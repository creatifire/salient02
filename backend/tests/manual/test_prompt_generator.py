"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

"""
Test prompt generator for directory tools.

Verifies:
1. Prompt generator loads agent config
2. Queries database for list metadata
3. Loads schema files
4. Generates formatted markdown documentation
"""

import asyncio
from uuid import UUID
from app.database import get_database_service
from app.agents.tools.prompt_generator import generate_directory_tool_docs

# Wyckoff account and agent IDs
WYCKOFF_ACCOUNT_ID = UUID('481d3e72-c0f5-47dd-8d6e-291c5a44a5c7')


async def test_prompt_generator():
    """Test prompt generator with Wyckoff doctors list."""
    db = get_database_service()
    await db.initialize()
    
    async with db.get_session() as session:
        # Simulate agent config
        agent_config = {
            "tools": {
                "directory": {
                    "enabled": True,
                    "accessible_lists": ["doctors"],
                    "max_results": 5
                }
            }
        }
        
        print("=" * 80)
        print("TEST: Prompt Generator - Wyckoff Doctors List")
        print("=" * 80)
        
        # Generate documentation
        docs = await generate_directory_tool_docs(
            agent_config=agent_config,
            account_id=WYCKOFF_ACCOUNT_ID,
            db_session=session
        )
        
        print("\n✅ Generated Documentation:\n")
        print(docs)
        print("\n" + "=" * 80)
        
        # Verify documentation content
        assert "## Directory Search Tool" in docs, "Missing header"
        assert "doctors (medical_professional)" in docs, "Missing list name"
        assert "**Entries**:" in docs, "Missing entry count"
        assert "**Tags**:" in docs, "Missing tags documentation"
        assert "**Searchable Filters**:" in docs, "Missing searchable fields"
        assert "department" in docs, "Missing department field"
        assert "specialty" in docs, "Missing specialty field"
        assert "gender" in docs, "Missing gender field"
        assert "**Query Examples**:" in docs, "Missing query examples"
        assert "search_directory" in docs, "Missing tool function name"
        assert "filters=" in docs, "Missing filters parameter"
        
        print("\n✅ All assertions passed!")
        print(f"   - Documentation length: {len(docs)} chars")
        print(f"   - Contains required sections: header, list info, tags, filters, examples")
        print(f"   - Uses new filters dict syntax")


if __name__ == "__main__":
    asyncio.run(test_prompt_generator())

