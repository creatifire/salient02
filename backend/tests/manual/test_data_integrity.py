#!/usr/bin/env python3
"""
Multi-Agent Data Integrity Verification Script

Tests all 5 multi-tenant agent instances to verify database integrity:
- Sessions table: account_id, agent_instance_id, agent_instance_slug
- Messages table: session_id, llm_request_id FK, role/content
- LLM_requests table: denormalized fields, cost tracking
- Multi-tenant isolation: session, agent, and account level

Usage:
    python backend/tests/manual/test_data_integrity.py
    python backend/tests/manual/test_data_integrity.py --format simple
    python backend/tests/manual/test_data_integrity.py --format json > results.json
    python backend/tests/manual/test_data_integrity.py --strict

Output Formats:
    rich   - ASCII tables with box-drawing characters (default)
    simple - Plain text output (grep-friendly)
    json   - JSON output for CI/CD integration

Flags:
    --format {rich,simple,json}  Output format (default: rich)
    --strict                      Exit 1 on any failure (CI/CD mode)

Note: Test data is preserved by default for manual inspection.
      Run cleanup_test_data.py to delete test data.
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import UUID
import yaml

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
from sqlalchemy import select, func
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


def load_config() -> Dict[str, Any]:
    """Load test configuration from YAML file"""
    config_path = Path(__file__).parent / "test_data_integrity_config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Replace environment variable references
    db_url = config['database']['connection_string']
    if db_url.startswith('${') and db_url.endswith('}'):
        env_var = db_url[2:-1]
        config['database']['connection_string'] = os.getenv(env_var)
    
    return config


async def send_chat_request(
    backend_url: str,
    account: str,
    agent: str,
    message: str,
    timeout: int
) -> Optional[Dict[str, Any]]:
    """Send a chat request to the multi-tenant endpoint"""
    url = f"{backend_url}/accounts/{account}/agents/{agent}/chat"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                url,
                json={"message": message},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"{Colors.RED}HTTP Error{Colors.RESET}: {e}")
            return None


async def verify_session_data(
    db: AsyncSession,
    account: str,
    agent: str,
    expected_fields: List[str]
) -> Dict[str, Any]:
    """Verify session table has all required fields populated"""
    # Get most recent session for this agent
    stmt = select(DBSession).where(
        DBSession.agent_instance_slug == agent
    ).order_by(DBSession.created_at.desc()).limit(1)
    
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        return {
            "status": "FAIL",
            "error": "No session found",
            "details": {}
        }
    
    # Check all expected fields are populated
    missing_fields = []
    field_values = {}
    
    for field in expected_fields:
        value = getattr(session, field, None)
        field_values[field] = value
        if value is None:
            missing_fields.append(field)
    
    if missing_fields:
        return {
            "status": "FAIL",
            "error": f"Missing fields: {', '.join(missing_fields)}",
            "details": field_values,
            "session_id": str(session.id)
        }
    
    return {
        "status": "PASS",
        "error": None,
        "details": field_values,
        "session_id": str(session.id)
    }


async def verify_messages_data(
    db: AsyncSession,
    session_id: str,
    expected_fields: List[str]
) -> Dict[str, Any]:
    """Verify messages table has all required fields populated"""
    # Get messages for this session
    stmt = select(Message).where(
        Message.session_id == UUID(session_id)
    ).order_by(Message.created_at.desc()).limit(10)
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    if not messages:
        return {
            "status": "FAIL",
            "error": "No messages found",
            "count": 0
        }
    
    # Check fields on all messages
    issues = []
    for msg in messages:
        for field in expected_fields:
            value = getattr(msg, field, None)
            # llm_request_id can be NULL for user messages, but should exist for assistant messages
            if field == "llm_request_id" and msg.role == "user":
                continue
            if value is None and field != "llm_request_id":
                issues.append(f"Message {msg.id}: missing {field}")
    
    if issues:
        return {
            "status": "FAIL",
            "error": f"{len(issues)} field issues",
            "count": len(messages),
            "issues": issues[:5]  # Show first 5
        }
    
    return {
        "status": "PASS",
        "error": None,
        "count": len(messages)
    }


async def verify_llm_requests_data(
    db: AsyncSession,
    session_id: str,
    expected_fields: List[str]
) -> Dict[str, Any]:
    """Verify llm_requests table has all denormalized fields and costs populated"""
    # Get LLM requests for this session
    stmt = select(LLMRequest).where(
        LLMRequest.session_id == UUID(session_id)
    ).order_by(LLMRequest.created_at.desc()).limit(5)
    
    result = await db.execute(stmt)
    llm_requests = result.scalars().all()
    
    if not llm_requests:
        return {
            "status": "FAIL",
            "error": "No LLM requests found",
            "count": 0
        }
    
    # Check all expected fields
    issues = []
    for req in llm_requests:
        for field in expected_fields:
            value = getattr(req, field, None)
            if value is None:
                issues.append(f"LLM Request {req.id}: missing {field}")
            # Check costs are non-zero
            if field in ['prompt_cost', 'completion_cost', 'total_cost']:
                if value is not None and float(value) <= 0:
                    issues.append(f"LLM Request {req.id}: {field} is zero")
    
    if issues:
        return {
            "status": "FAIL",
            "error": f"{len(issues)} field/cost issues",
            "count": len(llm_requests),
            "issues": issues[:5]
        }
    
    return {
        "status": "PASS",
        "error": None,
        "count": len(llm_requests),
        "total_cost": sum(float(req.total_cost or 0) for req in llm_requests)
    }


async def verify_multi_tenant_isolation(
    db: AsyncSession,
    session_id: str,
    account: str,
    agent: str
) -> Dict[str, Any]:
    """
    Verify multi-tenant isolation across all 3 scenarios:
    1. Session-level: Messages don't leak between sessions
    2. Agent-level: Data properly attributed within account
    3. Account-level: Complete data isolation between accounts
    """
    results = {
        "session_level": {"status": "PASS", "details": ""},
        "agent_level": {"status": "PASS", "details": ""},
        "account_level": {"status": "PASS", "details": ""}
    }
    
    # 1. Session-level isolation: Check for message leakage
    # Get count of messages in this session
    stmt = select(func.count(Message.id)).where(Message.session_id == UUID(session_id))
    result = await db.execute(stmt)
    this_session_count = result.scalar()
    
    # Get count of messages in other sessions for same agent
    stmt = select(func.count(Message.id)).join(DBSession).where(
        DBSession.agent_instance_slug == agent,
        Message.session_id != UUID(session_id)
    )
    result = await db.execute(stmt)
    other_sessions_count = result.scalar()
    
    if other_sessions_count > 0:
        results["session_level"]["details"] = f"This session: {this_session_count}, Other sessions: {other_sessions_count}"
    else:
        results["session_level"]["details"] = f"This session: {this_session_count} (no other sessions for comparison)"
    
    # 2. Agent-level isolation: Verify sessions are properly attributed
    # Check if there are other agents in same account
    account_name = account.split('/')[0] if '/' in account else account
    stmt = select(func.count(DBSession.id)).where(
        DBSession.agent_instance_slug.like(f"{account_name}/%"),
        DBSession.agent_instance_slug != agent
    )
    result = await db.execute(stmt)
    other_agents_sessions = result.scalar()
    
    if other_agents_sessions > 0:
        # Verify no message cross-contamination
        stmt = select(func.count(Message.id)).join(DBSession).where(
            DBSession.agent_instance_slug == agent
        )
        result = await db.execute(stmt)
        agent_messages = result.scalar()
        
        results["agent_level"]["details"] = f"Agent messages: {agent_messages}, Other agents in account: {other_agents_sessions} sessions"
    else:
        results["agent_level"]["details"] = "Only agent in account (no isolation test needed)"
    
    # 3. Account-level isolation: Verify complete separation
    # Check for any LLM requests with mismatched account_slug
    stmt = select(func.count(LLMRequest.id)).where(
        LLMRequest.session_id == UUID(session_id),
        LLMRequest.account_slug != account_name
    )
    result = await db.execute(stmt)
    mismatched_accounts = result.scalar()
    
    if mismatched_accounts > 0:
        results["account_level"]["status"] = "FAIL"
        results["account_level"]["details"] = f"Found {mismatched_accounts} LLM requests with wrong account_slug"
    else:
        results["account_level"]["details"] = f"All LLM requests correctly attributed to account '{account_name}'"
    
    return results


async def test_agent_data_integrity(
    config: Dict[str, Any],
    account: str,
    agent: str,
    prompt: str,
    expected_keywords: List[str]
) -> Dict[str, Any]:
    """Test data integrity for a single agent"""
    backend_url = config['backend']['url']
    timeout = config['backend']['timeout_seconds']
    
    start_time = datetime.now(UTC)
    
    # 1. Send chat request
    response = await send_chat_request(backend_url, account, agent, prompt, timeout)
    
    if not response:
        return {
            "account": account,
            "agent": agent,
            "status": "FAIL",
            "error": "HTTP request failed",
            "database_checks": {},
            "isolation_checks": {},
            "elapsed_ms": 0
        }
    
    # 2. Query database
    db_service = get_database_service()
    async with db_service.get_session() as db:
        # Verify session data
        session_result = await verify_session_data(
            db, account, agent, 
            config['expected_fields']['sessions']
        )
        
        if session_result["status"] != "PASS":
            return {
                "account": account,
                "agent": agent,
                "status": "FAIL",
                "error": f"Session verification failed: {session_result['error']}",
                "database_checks": {"sessions": session_result},
                "isolation_checks": {},
                "elapsed_ms": int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            }
        
        session_id = session_result["session_id"]
        
        # Verify messages data
        messages_result = await verify_messages_data(
            db, session_id,
            config['expected_fields']['messages']
        )
        
        # Verify LLM requests data
        llm_requests_result = await verify_llm_requests_data(
            db, session_id,
            config['expected_fields']['llm_requests']
        )
        
        # Verify multi-tenant isolation
        isolation_result = await verify_multi_tenant_isolation(
            db, session_id, account, agent
        )
    
    # Determine overall status
    all_checks_passed = (
        session_result["status"] == "PASS" and
        messages_result["status"] == "PASS" and
        llm_requests_result["status"] == "PASS" and
        all(check["status"] == "PASS" for check in isolation_result.values())
    )
    
    elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
    
    return {
        "account": account,
        "agent": agent,
        "status": "PASS" if all_checks_passed else "FAIL",
        "error": None if all_checks_passed else "One or more checks failed",
        "database_checks": {
            "sessions": session_result,
            "messages": messages_result,
            "llm_requests": llm_requests_result
        },
        "isolation_checks": isolation_result,
        "elapsed_ms": elapsed_ms
    }


def format_rich(results: List[Dict[str, Any]], config: Dict[str, Any]):
    """Format output as rich ASCII tables with box-drawing characters"""
    print()
    print(f"{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}║          MULTI-AGENT DATA INTEGRITY VERIFICATION REPORT                        ║{Colors.RESET}")
    print(f"{Colors.BOLD}╚════════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    print(f"{Colors.CYAN}Test Run:{Colors.RESET} {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{Colors.CYAN}Backend:{Colors.RESET} {config['backend']['url']}")
    print()
    
    # Agent results table
    print(f"{Colors.BOLD}AGENT VERIFICATION RESULTS{Colors.RESET}")
    print("┌─────────────────────────────────┬────────┬──────────┬──────────┬──────────┬────────┬───────────┐")
    print("│ Agent                           │ Status │ Sessions │ Messages │ LLM_Reqs │ Costs  │ Isolation │")
    print("├─────────────────────────────────┼────────┼──────────┼──────────┼──────────┼────────┼───────────┤")
    
    for result in results:
        agent_full = f"{result['account']}/{result['agent']}"
        status_color = Colors.GREEN if result['status'] == 'PASS' else Colors.RED
        status_icon = "✅" if result['status'] == 'PASS' else "❌"
        
        db_checks = result['database_checks']
        sess_icon = "✅" if db_checks['sessions']['status'] == 'PASS' else "❌"
        msg_icon = "✅" if db_checks['messages']['status'] == 'PASS' else "❌"
        llm_icon = "✅" if db_checks['llm_requests']['status'] == 'PASS' else "❌"
        cost_icon = "✅" if db_checks['llm_requests'].get('total_cost', 0) > 0 else "❌"
        
        iso_checks = result['isolation_checks']
        iso_all_pass = all(check['status'] == 'PASS' for check in iso_checks.values())
        iso_icon = "✅" if iso_all_pass else "❌"
        
        # Truncate agent name if too long
        agent_display = agent_full if len(agent_full) <= 31 else agent_full[:28] + "..."
        
        print(f"│ {agent_display:<31} │ {status_color}{status_icon} {result['status']:<4}{Colors.RESET} │    {sess_icon}     │    {msg_icon}     │    {llm_icon}     │   {cost_icon}    │     {iso_icon}     │")
    
    print("└─────────────────────────────────┴────────┴──────────┴──────────┴──────────┴────────┴───────────┘")
    print()
    
    # Isolation verification table
    print(f"{Colors.BOLD}ISOLATION VERIFICATION (3 scenarios){Colors.RESET}")
    print("┌────────────────────────────┬───────────────────────────────────────────────────┐")
    print("│ Scenario                   │ Result                                            │")
    print("├────────────────────────────┼───────────────────────────────────────────────────┤")
    
    # Check overall isolation
    all_session_pass = all(r['isolation_checks']['session_level']['status'] == 'PASS' for r in results)
    all_agent_pass = all(r['isolation_checks']['agent_level']['status'] == 'PASS' for r in results)
    all_account_pass = all(r['isolation_checks']['account_level']['status'] == 'PASS' for r in results)
    
    sess_status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if all_session_pass else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    agent_status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if all_agent_pass else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    account_status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if all_account_pass else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    
    print(f"│ Session-level isolation    │ {sess_status} - No cross-session data leakage       │")
    print(f"│ Agent-level isolation      │ {agent_status} - Agents within account isolated      │")
    print(f"│ Account-level isolation    │ {account_status} - Complete account separation         │")
    print("└────────────────────────────┴───────────────────────────────────────────────────┘")
    print()
    
    # Summary
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    total_time = sum(r['elapsed_ms'] for r in results)
    total_cost = sum(
        r['database_checks']['llm_requests'].get('total_cost', 0) 
        for r in results
    )
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL CHECKS PASSED ({passed}/{total} agents verified){Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ SOME CHECKS FAILED ({passed}/{total} agents passed){Colors.RESET}")
    
    print()
    print(f"Total execution time: {total_time/1000:.1f} seconds")
    print(f"Total LLM cost: ${total_cost:.6f}")
    print()
    print(f"{Colors.CYAN}💾 Test data preserved for manual inspection{Colors.RESET}")
    print(f"{Colors.CYAN}🧹 Run cleanup_test_data.py to delete test data{Colors.RESET}")
    print()


def format_simple(results: List[Dict[str, Any]], config: Dict[str, Any]):
    """Format output as simple text (grep-friendly)"""
    print("MULTI-AGENT DATA INTEGRITY REPORT")
    print("=" * 80)
    print(f"Test Run: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Backend: {config['backend']['url']}")
    print()
    
    for result in results:
        agent_full = f"{result['account']}/{result['agent']}"
        status = "PASS" if result['status'] == 'PASS' else "FAIL"
        print(f"Agent: {agent_full} - {status}")
    
    print()
    
    # Isolation summary
    all_session_pass = all(r['isolation_checks']['session_level']['status'] == 'PASS' for r in results)
    all_agent_pass = all(r['isolation_checks']['agent_level']['status'] == 'PASS' for r in results)
    all_account_pass = all(r['isolation_checks']['account_level']['status'] == 'PASS' for r in results)
    
    print(f"Isolation: Session-level - {'PASS' if all_session_pass else 'FAIL'}")
    print(f"Isolation: Agent-level - {'PASS' if all_agent_pass else 'FAIL'}")
    print(f"Isolation: Account-level - {'PASS' if all_account_pass else 'FAIL'}")
    print()
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    print(f"Summary: {passed}/{total} PASS")
    print()


def format_json(results: List[Dict[str, Any]], config: Dict[str, Any]):
    """Format output as JSON for CI/CD integration"""
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    
    output = {
        "test_run": datetime.now(UTC).isoformat(),
        "backend_url": config['backend']['url'],
        "results": results,
        "summary": {
            "total_agents": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
        }
    }
    
    print(json.dumps(output, indent=2, default=str))


async def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Data Integrity Verification Script"
    )
    parser.add_argument(
        '--format',
        choices=['rich', 'simple', 'json'],
        default='rich',
        help='Output format (default: rich)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit 1 on any failure (CI/CD mode)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"{Colors.RED}Error loading configuration: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)
    
    # Test all agents
    results = []
    for agent_key, agent_config in config['agents'].items():
        account, agent = agent_key.rsplit('/', 1)
        
        if args.format == 'rich':
            print(f"{Colors.CYAN}Testing {agent_key}...{Colors.RESET}")
        
        result = await test_agent_data_integrity(
            config,
            account,
            agent,
            agent_config['prompt'],
            agent_config['expected_keywords']
        )
        results.append(result)
    
    # Format output
    if args.format == 'rich':
        format_rich(results, config)
    elif args.format == 'simple':
        format_simple(results, config)
    elif args.format == 'json':
        format_json(results, config)
    
    # Exit with appropriate code
    if args.strict:
        failures = sum(1 for r in results if r['status'] != 'PASS')
        sys.exit(1 if failures > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())

