# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Manual test script for Directory Service Full-Text Search (FTS).

Tests all three search modes:
- substring: Backward compatible partial match
- exact: Exact name match
- fts: Full-text search with ranking

Usage:
    cd backend
    python tests/manual/test_directory_fts.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.database import get_database_service
from app.services.directory_service import DirectoryService
from sqlalchemy import select
from app.models.directory import DirectoryList
from uuid import UUID


async def main():
    """Test all three search modes with Wyckoff doctors data."""
    
    print("=" * 80)
    print("Directory Service FTS Test")
    print("=" * 80)
    
    # Initialize database
    db = get_database_service()
    await db.initialize()
    
    # Get Wyckoff account ID and doctors list
    wyckoff_account_id = UUID('481d3e72-c0f5-47dd-8d6e-291c5a44a5c7')
    
    async with db.get_session() as session:
        # Get doctors list ID
        result = await session.execute(
            select(DirectoryList.id).where(
                DirectoryList.account_id == wyckoff_account_id,
                DirectoryList.list_name == 'doctors'
            )
        )
        doctors_list_id = result.scalar_one()
        
        print(f"\n✅ Using Wyckoff account: {wyckoff_account_id}")
        print(f"✅ Doctors list ID: {doctors_list_id}\n")
        
        # Test 1: Substring search (default - backward compatible)
        print("-" * 80)
        print("TEST 1: Substring Search (default)")
        print("-" * 80)
        entries = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query="cardio",
            search_mode="substring"
        )
        print(f"Query: 'cardio' (substring)")
        print(f"Results: {len(entries)} entries")
        for entry in entries[:3]:
            print(f"  - {entry.name}")
            print(f"    Dept: {entry.entry_data.get('department')}, "
                  f"Spec: {entry.entry_data.get('specialty')}")
        
        # Test 2: Exact match search
        print("\n" + "-" * 80)
        print("TEST 2: Exact Match Search")
        print("-" * 80)
        if entries:
            exact_name = entries[0].name
            exact_entries = await DirectoryService.search(
                session=session,
                accessible_list_ids=[doctors_list_id],
                name_query=exact_name,
                search_mode="exact"
            )
            print(f"Query: '{exact_name}' (exact)")
            print(f"Results: {len(exact_entries)} entries")
            for entry in exact_entries:
                print(f"  - {entry.name}")
        
        # Test 3: FTS with single word
        print("\n" + "-" * 80)
        print("TEST 3: Full-Text Search - Single Word")
        print("-" * 80)
        fts_entries = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query="surgery",
            search_mode="fts",
            limit=5
        )
        print(f"Query: 'surgery' (fts)")
        print(f"Results: {len(fts_entries)} entries (ranked by relevance)")
        for entry in fts_entries:
            print(f"  - {entry.name}")
            print(f"    Dept: {entry.entry_data.get('department')}, "
                  f"Spec: {entry.entry_data.get('specialty')}")
        
        # Test 4: FTS with multiple words
        print("\n" + "-" * 80)
        print("TEST 4: Full-Text Search - Multiple Words")
        print("-" * 80)
        fts_multi = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query="plastic surgery",
            search_mode="fts",
            limit=5
        )
        print(f"Query: 'plastic surgery' (fts)")
        print(f"Results: {len(fts_multi)} entries (ranked by relevance)")
        for entry in fts_multi:
            print(f"  - {entry.name}")
            print(f"    Dept: {entry.entry_data.get('department')}, "
                  f"Spec: {entry.entry_data.get('specialty')}")
        
        # Test 5: FTS with word variations (stemming)
        print("\n" + "-" * 80)
        print("TEST 5: Full-Text Search - Word Variations (Stemming)")
        print("-" * 80)
        fts_stem = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query="surgeons",  # Plural should match "surgeon", "surgery"
            search_mode="fts",
            limit=5
        )
        print(f"Query: 'surgeons' (fts - should match 'surgeon', 'surgery')")
        print(f"Results: {len(fts_stem)} entries")
        for entry in fts_stem:
            print(f"  - {entry.name}")
            print(f"    Dept: {entry.entry_data.get('department')}, "
                  f"Spec: {entry.entry_data.get('specialty')}")
        
        # Test 6: FTS with combined filters
        print("\n" + "-" * 80)
        print("TEST 6: Full-Text Search + Combined Filters")
        print("-" * 80)
        fts_combined = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query="medicine",
            tags=["Spanish"],
            search_mode="fts",
            limit=5
        )
        print(f"Query: 'medicine' (fts) + tags: ['Spanish']")
        print(f"Results: {len(fts_combined)} entries")
        for entry in fts_combined:
            print(f"  - {entry.name}")
            print(f"    Dept: {entry.entry_data.get('department')}, "
                  f"Tags: {entry.tags}")
        
        # Test 7: FTS with department filter
        print("\n" + "-" * 80)
        print("TEST 7: Full-Text Search + JSONB Filter")
        print("-" * 80)
        fts_jsonb = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query="doctor",
            jsonb_filters={"department": "Pediatrics"},
            search_mode="fts",
            limit=5
        )
        print(f"Query: 'doctor' (fts) + department: 'Pediatrics'")
        print(f"Results: {len(fts_jsonb)} entries")
        for entry in fts_jsonb:
            print(f"  - {entry.name}")
            print(f"    Dept: {entry.entry_data.get('department')}, "
                  f"Spec: {entry.entry_data.get('specialty')}")
        
        # Test 8: Empty query handling
        print("\n" + "-" * 80)
        print("TEST 8: Empty Query Handling")
        print("-" * 80)
        empty_entries = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query=None,
            search_mode="fts",
            limit=5
        )
        print(f"Query: None (should return any entries)")
        print(f"Results: {len(empty_entries)} entries")
        
        # Test 9: Backward compatibility (no search_mode specified)
        print("\n" + "-" * 80)
        print("TEST 9: Backward Compatibility (default substring)")
        print("-" * 80)
        default_entries = await DirectoryService.search(
            session=session,
            accessible_list_ids=[doctors_list_id],
            name_query="smith"
            # search_mode not specified - should default to "substring"
        )
        print(f"Query: 'smith' (no search_mode - defaults to substring)")
        print(f"Results: {len(default_entries)} entries")
        for entry in default_entries[:3]:
            print(f"  - {entry.name}")
        
        print("\n" + "=" * 80)
        print("✅ All tests completed successfully!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

