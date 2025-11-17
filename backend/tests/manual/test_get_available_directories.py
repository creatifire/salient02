"""
Manual test for get_available_directories() tool.

Tests the new dynamic directory discovery pattern (CHUNK-0026-3C-010-001).
"""

import asyncio
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_database_service
from app.agents.tools.directory_tools import get_available_directories
from pydantic_ai import RunContext
from app.agents.base.dependencies import SessionDependencies
from app.models.session import Session as ChatSession


async def test_get_available_directories():
    """Test the get_available_directories() tool."""
    print("\n" + "="*80)
    print("TEST: get_available_directories() - Dynamic Directory Discovery")
    print("="*80 + "\n")
    
    # Initialize database
    db_service = get_database_service()
    await db_service.initialize()
    
    # Setup: Get Wyckoff account ID and agent config
    async with db_service.get_session() as session:
        # Get a Wyckoff session to extract account_id
        from sqlalchemy import select
        result = await session.execute(
            select(ChatSession)
            .where(ChatSession.account_slug == 'wyckoff')
            .limit(1)
        )
        chat_session = result.scalar_one_or_none()
        
        if not chat_session:
            print("❌ No Wyckoff session found. Create one first.")
            return
        
        account_id = chat_session.account_id
        print(f"✅ Using account: wyckoff (ID: {account_id})\n")
        
        # Mock agent config with directory tools enabled
        agent_config = {
            "tools": {
                "directory": {
                    "enabled": True,
                    "accessible_lists": ["doctors", "phone_directory"]
                }
            }
        }
        
        # Create mock dependencies
        class MockDeps(SessionDependencies):
            def __init__(self, account_id, agent_config):
                self.account_id = account_id
                self.agent_config = agent_config
                self.session = type('obj', (object,), {'account_id': account_id})()
                self.db_session = None
        
        deps = MockDeps(account_id, agent_config)
        
        # Create mock RunContext
        class MockRunContext:
            def __init__(self, deps):
                self.deps = deps
        
        ctx = MockRunContext(deps)
        
        # Call the tool
        print("📞 Calling get_available_directories()...\n")
        result_json = await get_available_directories(ctx)
        
        # Parse and display results
        result = json.loads(result_json)
        
        print(f"✅ SUCCESS! Found {result['total_count']} directories\n")
        print("="*80)
        print("DIRECTORY METADATA:")
        print("="*80 + "\n")
        
        for i, directory in enumerate(result['directories'], 1):
            print(f"{i}. Directory: {directory['list_name']}")
            print(f"   Entry Type: {directory['entry_type']}")
            print(f"   Entry Count: {directory['entry_count']}")
            print(f"   Description: {directory['description']}")
            print(f"\n   Use Cases:")
            for use_case in directory['use_cases']:
                print(f"   - {use_case}")
            
            print(f"\n   Searchable Fields: {', '.join(directory['searchable_fields'])}")
            
            if directory['example_queries']:
                print(f"\n   Example Queries:")
                for query in directory['example_queries'][:3]:
                    print(f"   - \"{query}\"")
            
            if directory.get('not_for'):
                print(f"\n   Don't Use For:")
                for exclusion in directory['not_for']:
                    print(f"   - {exclusion}")
            
            print("\n" + "-"*80 + "\n")
        
        print("\n✅ TEST PASSED: Tool returned valid directory metadata\n")
        print("Next steps:")
        print("1. LLM can now call this tool to discover available directories")
        print("2. LLM reviews metadata to choose appropriate directory")
        print("3. LLM calls search_directory(list_name=...) with chosen directory")
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_get_available_directories())

