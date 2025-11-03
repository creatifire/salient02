"""Simple test to verify filters dict works."""
import asyncio
from uuid import UUID
from app.database import get_database_service
from app.services.directory_service import DirectoryService
from app.models.directory import DirectoryList
from sqlalchemy import select

WYCKOFF_ACCOUNT_ID = UUID('481d3e72-c0f5-47dd-8d6e-291c5a44a5c7')

async def test():
    print("\n=== Testing Filters Dict ===")
    db = get_database_service()
    await db.initialize()
    print("✅ Database initialized")
    
    async with db.get_session() as session:
        # Get doctors list ID
        result = await session.execute(
            select(DirectoryList.id).where(
                DirectoryList.account_id == WYCKOFF_ACCOUNT_ID,
                DirectoryList.list_name == 'doctors'
            )
        )
        doctors_list_id = result.scalar_one()
        print(f"✅ Found doctors list: {doctors_list_id}")
        
        # Test filters dict
        print("\n🔍 Testing: filters={'specialty': 'Surgery', 'gender': 'female'}")
        entries = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            jsonb_filters={"specialty": "Surgery", "gender": "female"},
            search_mode="fts",
            limit=3
        )
        print(f"✅ Found {len(entries)} female surgeons:")
        for entry in entries:
            print(f"   - {entry.name}: {entry.entry_data.get('specialty')}, {entry.entry_data.get('gender')}")
        
        print("\n✅ FILTERS DICT WORKS!")

if __name__ == "__main__":
    asyncio.run(test())
