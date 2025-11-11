"""
Phase 3 prompt generation tests.

Tests generate_directory_tool_docs with single and multiple directories.
"""

import asyncio
import sys
from uuid import UUID

# Add backend to path
sys.path.insert(0, 'backend')


async def test_single_directory_prompt():
    """Test prompt generation with single directory (doctors only)."""
    print("\n" + "="*60)
    print("Test: Single Directory Prompt Generation")
    print("="*60)
    
    from app.database import get_database_service
    from app.agents.tools.prompt_generator import generate_directory_tool_docs
    
    db = get_database_service()
    await db.initialize()
    
    async with db.get_session() as session:
        config = {
            "tools": {
                "directory": {
                    "accessible_lists": ["doctors"]
                }
            }
        }
        wyckoff_id = UUID("481d3e72-c0f5-47dd-8d6e-291c5a44a5c7")
        
        docs = await generate_directory_tool_docs(config, wyckoff_id, session)
        
        print(f"\n📄 Generated docs length: {len(docs)} characters\n")
        print("="*60)
        print(docs)
        print("="*60)
        
        # Validation
        assert docs != "", "❌ Docs should not be empty"
        assert "doctors" in docs.lower(), "❌ Should mention 'doctors'"
        assert "Directory Tool" in docs, "❌ Should have 'Directory Tool' heading"
        assert "multiple directories" not in docs.lower(), "❌ Should NOT mention multiple directories for single directory"
        assert "Medical Term Mappings" in docs, "❌ Should have medical term mappings"
        assert "formal" in docs.lower(), "❌ Should use formal terms"
        
        print("\n✅ Single directory prompt: ALL CHECKS PASSED\n")
        return docs


async def test_multi_directory_prompt():
    """Test prompt generation with multiple directories (doctors + phone_directory)."""
    print("\n" + "="*60)
    print("Test: Multi-Directory Prompt Generation")
    print("="*60)
    
    from app.database import get_database_service
    from app.agents.tools.prompt_generator import generate_directory_tool_docs
    
    db = get_database_service()
    await db.initialize()
    
    async with db.get_session() as session:
        config = {
            "tools": {
                "directory": {
                    "accessible_lists": ["doctors", "phone_directory"]
                }
            }
        }
        wyckoff_id = UUID("481d3e72-c0f5-47dd-8d6e-291c5a44a5c7")
        
        docs = await generate_directory_tool_docs(config, wyckoff_id, session)
        
        print(f"\n📄 Generated docs length: {len(docs)} characters\n")
        print("="*60)
        print(docs)
        print("="*60)
        
        # Validation
        assert docs != "", "❌ Docs should not be empty"
        assert "doctors" in docs.lower(), "❌ Should mention 'doctors'"
        assert "phone_directory" in docs.lower(), "❌ Should mention 'phone_directory'"
        assert "Directory Tool" in docs, "❌ Should have 'Directory Tool' heading"
        assert "multiple directories" in docs.lower(), "❌ Should mention multiple directories"
        assert "Choose the appropriate directory" in docs or "Choose" in docs, "❌ Should have directory selection guidance"
        assert "Use for" in docs, "❌ Should have 'Use for' guidance"
        assert "Example queries" in docs, "❌ Should have example queries"
        
        # Check for directory_purpose content
        assert "Medical professionals" in docs or "medical professionals" in docs, "❌ Should describe doctors directory"
        assert "phone numbers" in docs.lower(), "❌ Should describe phone_directory"
        
        print("\n✅ Multi-directory prompt: ALL CHECKS PASSED\n")
        return docs


async def main():
    """Run all prompt generation tests."""
    try:
        single_dir_docs = await test_single_directory_prompt()
        multi_dir_docs = await test_multi_directory_prompt()
        
        # Compare content focus
        print("\n" + "="*60)
        print("COMPARISON")
        print("="*60)
        print(f"Single directory docs: {len(single_dir_docs)} chars")
        print(f"Multi-directory docs:  {len(multi_dir_docs)} chars")
        print(f"Difference:            {len(multi_dir_docs) - len(single_dir_docs)} chars")
        print("\n✅ Single-directory: Detailed search strategy (medical term mappings)")
        print("✅ Multi-directory: Directory selection guide (which directory to use)")
        print("\nBoth approaches are correct - they optimize for different scenarios:")
        
        print("\n" + "="*60)
        print("SUMMARY: ALL PROMPT GENERATION TESTS PASSED ✅")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

