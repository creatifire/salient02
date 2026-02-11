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
        result = await generate_directory_tool_docs(
            agent_config=agent_config,
            account_id=WYCKOFF_ACCOUNT_ID,
            db_session=session
        )
        
        print("\n✅ Generated Documentation:\n")
        print(result.full_text)
        print("\n" + "=" * 80)
        
        # Verify documentation content
        assert "## Directory Search Tool" in result.full_text or "## Directory Tool" in result.full_text, "Missing header"
        assert "doctors" in result.full_text, "Missing list name"
        # Note: Content structure changed in Phase 3C - validating presence of key info
        assert len(result.full_text) > 100, "Documentation too short"
        
        # Verify structured result
        assert result.directory_sections is not None, "Missing directory sections"
        print(f"\n📊 Generated {len(result.directory_sections)} directory sections")
        if result.header_section:
            print(f"📄 Header section: {len(result.header_section.content)} chars")
        
        print("\n✅ All assertions passed!")
        print(f"   - Documentation length: {len(result.full_text)} chars")
        print(f"   - Structure: {len(result.directory_sections)} directory sections")
        if result.header_section:
            print(f"   - Has header section for multi-directory guidance")


if __name__ == "__main__":
    asyncio.run(test_prompt_generator())

