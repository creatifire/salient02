import sys
import os
from pathlib import Path

# Add backend to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import json
from uuid import UUID
from sqlalchemy import select
from app.agents.tools.directory_tools import get_available_directories, search_directory
from app.database import get_database_service
from app.models.account import Account
from pydantic_ai.models.test import TestModel
from pydantic_ai import RunContext
import yaml

class MockDeps:
    def __init__(self, account_id, agent_config):
        self.account_id = account_id
        self.agent_config = agent_config

async def get_wyckoff_account_id() -> UUID:
    """Query database for Wyckoff account UUID."""
    db_service = get_database_service()
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        result = await session.execute(
            select(Account).where(Account.slug == "wyckoff")
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise ValueError("Wyckoff account not found in database")
        
        return account.id

async def test_direct_search():
    """Test search_directory tool directly with new JSON output"""
    
    # Initialize database
    db_service = get_database_service()
    await db_service.initialize()
    
    # Get Wyckoff account UUID
    account_id = await get_wyckoff_account_id()
    print(f"Using Wyckoff account ID: {account_id}\n")
    
    # Load Wyckoff config
    config_path = Path(__file__).parent.parent.parent / "config" / "agent_configs" / "wyckoff" / "wyckoff_info_chat1" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create mock context
    ctx = RunContext(
        deps=MockDeps(
            account_id=account_id,
            agent_config=config
        ),
        model=TestModel(),
        usage=None,
        prompt='test'
    )
    
    print("=" * 80)
    print("TEST 1: Get Available Directories")
    print("=" * 80)
    result1 = await get_available_directories(ctx)
    dirs_json = json.loads(result1)
    print(json.dumps(dirs_json, indent=2))
    print()
    
    print("=" * 80)
    print("TEST 2: Search Cardiologists (doctors)")
    print("=" * 80)
    result2 = await search_directory(ctx, list_name="doctors", filters={"specialty": "Cardiology"})
    doctors_json = json.loads(result2)
    print(json.dumps(doctors_json, indent=2))
    
    # Show field coverage
    if doctors_json['total'] > 0:
        first_entry = doctors_json['entries'][0]
        print(f"\n✅ Entry type: {first_entry.get('entry_type', 'MISSING')}")
        print(f"✅ Fields returned: {', '.join(first_entry.keys())}")
        
        # Check for key medical_professional fields
        expected_fields = ['name', 'entry_type', 'department', 'specialty', 'phone', 'email', 'location']
        present = [f for f in expected_fields if f in first_entry]
        missing = [f for f in expected_fields if f not in first_entry]
        print(f"✅ Expected fields present: {', '.join(present)}")
        if missing:
            print(f"⚠️  Expected fields missing: {', '.join(missing)}")
    print()
    
    print("=" * 80)
    print("TEST 3: Search by name (doctors)")
    print("=" * 80)
    result3 = await search_directory(ctx, list_name="doctors", query="Smith")
    search_json = json.loads(result3)
    print(f"Found {search_json['total']} results for 'Smith'")
    if search_json['total'] > 0:
        print(json.dumps(search_json['entries'][0], indent=2))
        print(f"\n✅ Query search working: {search_json['total']} results found")

if __name__ == "__main__":
    asyncio.run(test_direct_search())
