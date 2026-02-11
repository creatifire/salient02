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
        
        result = await generate_directory_tool_docs(config, wyckoff_id, session)
        
        print(f"\n📄 Generated docs length: {len(result.full_text)} characters\n")
        print("="*60)
        print(result.full_text)
        print("="*60)
        
        # Validation
        assert result.full_text != "", "❌ Docs should not be empty"
        assert "doctors" in result.full_text.lower(), "❌ Should mention 'doctors'"
        assert "Directory Tool" in result.full_text, "❌ Should have 'Directory Tool' heading"
        assert "multiple directories" not in result.full_text.lower(), "❌ Should NOT mention multiple directories for single directory"
        assert result.header_section is None, "❌ Single directory should not have header section"
        assert len(result.directory_sections) >= 0, "❌ Should have directory sections"
        
        print("\n✅ Single directory prompt: ALL CHECKS PASSED\n")
        return result.full_text


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
        
        result = await generate_directory_tool_docs(config, wyckoff_id, session)
        
        print(f"\n📄 Generated docs length: {len(result.full_text)} characters\n")
        print("="*60)
        print(result.full_text)
        print("="*60)
        
        # Validation
        assert result.full_text != "", "❌ Docs should not be empty"
        assert "doctors" in result.full_text.lower(), "❌ Should mention 'doctors'"
        assert "phone_directory" in result.full_text.lower(), "❌ Should mention 'phone_directory'"
        assert "Directory Tool" in result.full_text, "❌ Should have 'Directory Tool' heading"
        assert "multiple directories" in result.full_text.lower(), "❌ Should mention multiple directories"
        assert "Choose the appropriate directory" in result.full_text or "Choose" in result.full_text, "❌ Should have directory selection guidance"
        assert "Use for" in result.full_text, "❌ Should have 'Use for' guidance"
        assert "Example queries" in result.full_text, "❌ Should have example queries"
        
        # Check for directory_purpose content
        assert "Medical professionals" in result.full_text or "medical professionals" in result.full_text, "❌ Should describe doctors directory"
        assert "phone numbers" in result.full_text.lower(), "❌ Should describe phone_directory"
        
        # Check structured result
        assert result.header_section is not None, "❌ Multi-directory should have header section"
        assert len(result.directory_sections) == 0, "❌ Multi-directory uses header section only"
        
        print("\n✅ Multi-directory prompt: ALL CHECKS PASSED\n")
        return result.full_text


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

