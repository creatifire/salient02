#!/usr/bin/env python3
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

"""
Test Data Cleanup Script

Safely delete test data created by test_data_integrity.py

Usage:
    python backend/tests/manual/cleanup_test_data.py              # Interactive with confirmation
    python backend/tests/manual/cleanup_test_data.py --dry-run    # Show what would be deleted
    python backend/tests/manual/cleanup_test_data.py --agent wyckoff/wyckoff_info_chat1  # Clean specific agent
    python backend/tests/manual/cleanup_test_data.py --all        # Skip confirmation (dangerous!)

Safety Features:
    - Confirmation prompt before deletion (unless --all flag)
    - Dry-run mode to preview deletions
    - Selective deletion by agent
    - Production environment check
    - Summary of deleted records

Note: This deletes data from sessions, messages, and llm_requests tables.
      Data is deleted in proper order (respecting foreign keys).
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import UUID

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_database_service
from app.models.session import Session as DBSession
from app.models.message import Message
from app.models.llm_request import LLMRequest


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def is_production_environment() -> bool:
    """Check if we're in a production environment"""
    # Check for production indicators
    env = os.getenv('ENVIRONMENT', '').lower()
    db_url = os.getenv('DATABASE_URL', '')
    
    production_indicators = [
        'prod' in env,
        'production' in env,
        'prod' in db_url.lower(),
        'production' in db_url.lower()
    ]
    
    return any(production_indicators)


async def get_test_data_stats(
    db: AsyncSession,
    agent_filter: Optional[str] = None,
    time_window_minutes: int = 60
) -> Dict[str, Any]:
    """Get statistics about test data to be deleted"""
    cutoff_time = datetime.now(UTC) - timedelta(minutes=time_window_minutes)
    
    # Build session query
    session_query = select(DBSession).where(
        DBSession.created_at > cutoff_time
    )
    
    if agent_filter:
        session_query = session_query.where(
            DBSession.agent_instance_slug == agent_filter
        )
    
    # Get sessions
    result = await db.execute(session_query)
    sessions = result.scalars().all()
    session_ids = [session.id for session in sessions]
    
    if not session_ids:
        return {
            "sessions": 0,
            "messages": 0,
            "llm_requests": 0,
            "session_ids": [],
            "agents": []
        }
    
    # Count messages
    stmt = select(func.count(Message.id)).where(
        Message.session_id.in_(session_ids)
    )
    result = await db.execute(stmt)
    message_count = result.scalar()
    
    # Count LLM requests
    stmt = select(func.count(LLMRequest.id)).where(
        LLMRequest.session_id.in_(session_ids)
    )
    result = await db.execute(stmt)
    llm_request_count = result.scalar()
    
    # Get unique agents
    agents = list(set(session.agent_instance_slug for session in sessions if session.agent_instance_slug))
    
    return {
        "sessions": len(sessions),
        "messages": message_count,
        "llm_requests": llm_request_count,
        "session_ids": session_ids,
        "agents": sorted(agents)
    }


async def delete_test_data(
    db: AsyncSession,
    session_ids: List[UUID],
    dry_run: bool = False
) -> Dict[str, int]:
    """Delete test data in proper order (respecting foreign keys)"""
    deleted_counts = {
        "messages": 0,
        "llm_requests": 0,
        "sessions": 0
    }
    
    if not session_ids:
        return deleted_counts
    
    if dry_run:
        print(f"{Colors.YELLOW}DRY-RUN MODE: No data will be deleted{Colors.RESET}")
        return deleted_counts
    
    # Delete in order: messages, llm_requests, sessions
    # (Messages have FK to llm_requests, but llm_request_id is nullable)
    
    # 1. Delete messages
    stmt = delete(Message).where(Message.session_id.in_(session_ids))
    result = await db.execute(stmt)
    deleted_counts["messages"] = result.rowcount
    
    # 2. Delete LLM requests
    stmt = delete(LLMRequest).where(LLMRequest.session_id.in_(session_ids))
    result = await db.execute(stmt)
    deleted_counts["llm_requests"] = result.rowcount
    
    # 3. Delete sessions
    stmt = delete(DBSession).where(DBSession.id.in_(session_ids))
    result = await db.execute(stmt)
    deleted_counts["sessions"] = result.rowcount
    
    # Commit the transaction
    await db.commit()
    
    return deleted_counts


def confirm_deletion(stats: Dict[str, Any], skip_confirmation: bool = False) -> bool:
    """Ask user to confirm deletion"""
    if skip_confirmation:
        return True
    
    print()
    print(f"{Colors.BOLD}{Colors.YELLOW}⚠️  WARNING: About to delete test data{Colors.RESET}")
    print()
    print(f"  {Colors.CYAN}Sessions:{Colors.RESET}      {stats['sessions']}")
    print(f"  {Colors.CYAN}Messages:{Colors.RESET}      {stats['messages']}")
    print(f"  {Colors.CYAN}LLM Requests:{Colors.RESET}  {stats['llm_requests']}")
    
    if stats['agents']:
        print()
        print(f"  {Colors.CYAN}Affected agents:{Colors.RESET}")
        for agent in stats['agents']:
            print(f"    - {agent}")
    
    print()
    response = input(f"{Colors.YELLOW}Are you sure you want to delete this data? [y/N]: {Colors.RESET}")
    
    return response.lower() in ['y', 'yes']


async def main():
    """Main cleanup execution"""
    parser = argparse.ArgumentParser(
        description="Test Data Cleanup Script"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--agent',
        type=str,
        help='Clean specific agent data only (e.g., wyckoff/wyckoff_info_chat1)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Skip confirmation, delete immediately (dangerous!)'
    )
    parser.add_argument(
        '--time-window',
        type=int,
        default=60,
        help='Time window in minutes for data to delete (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Safety check: prevent accidental production deletion
    if is_production_environment() and not args.dry_run:
        print(f"{Colors.RED}{Colors.BOLD}ERROR: Production environment detected!{Colors.RESET}")
        print(f"{Colors.RED}This script should not be run in production.{Colors.RESET}")
        print(f"{Colors.YELLOW}Use --dry-run to see what would be deleted.{Colors.RESET}")
        sys.exit(1)
    
    print()
    print(f"{Colors.BOLD}{'═' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}  TEST DATA CLEANUP SCRIPT{Colors.RESET}")
    print(f"{Colors.BOLD}{'═' * 80}{Colors.RESET}")
    print()
    
    if args.dry_run:
        print(f"{Colors.YELLOW}🔍 DRY-RUN MODE: No data will be deleted{Colors.RESET}")
    
    if args.agent:
        print(f"{Colors.CYAN}🎯 Agent filter: {args.agent}{Colors.RESET}")
    
    print(f"{Colors.CYAN}⏱️  Time window: Last {args.time_window} minutes{Colors.RESET}")
    print()
    
    # Initialize and get database service
    db_service = get_database_service()
    try:
        await db_service.initialize()
    except Exception as e:
        print(f"{Colors.RED}Error initializing database: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)
    
    # Get test data statistics
    async with db_service.get_session() as db:
        stats = await get_test_data_stats(
            db,
            agent_filter=args.agent,
            time_window_minutes=args.time_window
        )
        
        if stats["sessions"] == 0:
            print(f"{Colors.GREEN}✅ No test data found to delete{Colors.RESET}")
            print()
            return
        
        # Show stats
        print(f"{Colors.BOLD}Data to be deleted:{Colors.RESET}")
        print()
        print(f"  {Colors.CYAN}Sessions:{Colors.RESET}      {stats['sessions']:>6}")
        print(f"  {Colors.CYAN}Messages:{Colors.RESET}      {stats['messages']:>6}")
        print(f"  {Colors.CYAN}LLM Requests:{Colors.RESET}  {stats['llm_requests']:>6}")
        
        if stats['agents']:
            print()
            print(f"  {Colors.CYAN}Affected agents:{Colors.RESET}")
            for agent in stats['agents']:
                print(f"    {Colors.BLUE}•{Colors.RESET} {agent}")
        
        print()
        
        # Dry-run mode: just show stats and exit
        if args.dry_run:
            print(f"{Colors.GREEN}✓ Dry-run complete (no data deleted){Colors.RESET}")
            print()
            return
        
        # Confirm deletion
        if not confirm_deletion(stats, skip_confirmation=args.all):
            print()
            print(f"{Colors.YELLOW}❌ Deletion cancelled{Colors.RESET}")
            print()
            return
        
        # Delete data
        print()
        print(f"{Colors.CYAN}Deleting data...{Colors.RESET}")
        
        deleted_counts = await delete_test_data(db, stats["session_ids"], dry_run=False)
        
        # Show results
        print()
        print(f"{Colors.BOLD}{'═' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}  DELETION SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{'═' * 80}{Colors.RESET}")
        print()
        print(f"  {Colors.GREEN}✓{Colors.RESET} Sessions deleted:      {deleted_counts['sessions']:>6}")
        print(f"  {Colors.GREEN}✓{Colors.RESET} Messages deleted:      {deleted_counts['messages']:>6}")
        print(f"  {Colors.GREEN}✓{Colors.RESET} LLM Requests deleted:  {deleted_counts['llm_requests']:>6}")
        print()
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Cleanup complete!{Colors.RESET}")
        print()


if __name__ == "__main__":
    asyncio.run(main())

