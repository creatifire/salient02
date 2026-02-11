"""
Investigation 001 - Tool Calling Behavior
Phase 2D: Real Wyckoff Tools with Real LLM

Tests discovery pattern with:
- Real production tools from directory_tools.py
- Actual Wyckoff database data
- Real SessionDependencies structure
- Gemini 2.5 Flash via Pydantic AI Gateway
"""
import sys
import os
import asyncio
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pydantic_ai import Agent
from pydantic_ai.messages import ToolCallPart
from dotenv import load_dotenv
from sqlalchemy import select

# Import real production tools
from app.agents.tools.directory_tools import get_available_directories, search_directory
from app.agents.base.dependencies import SessionDependencies
from app.database import get_database_service
from app.models.account import Account

# Load environment variables
load_dotenv()


# ==============================================================================
# SETUP: Load Wyckoff Configuration and Account Data
# ==============================================================================

async def load_wyckoff_config() -> Dict[str, Any]:
    """Load real Wyckoff agent configuration from config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "agent_configs" / "wyckoff" / "wyckoff_info_chat1" / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Wyckoff config not found at {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ Loaded Wyckoff config from {config_path}")
    return config


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
        
        print(f"✅ Found Wyckoff account: {account.id}")
        return account.id


@dataclass
class MockSessionDependencies:
    """
    Mock SessionDependencies for testing.
    
    Provides the same structure as production SessionDependencies
    but allows us to control account_id and agent_config.
    """
    account_id: UUID
    agent_config: Dict[str, Any]
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    
    def __getattr__(self, name):
        """Handle any additional attributes gracefully."""
        return None


def get_tool_call_order(result) -> list[str]:
    """Extract the order of tool calls from messages."""
    tool_calls = []
    for msg in result.all_messages():
        for part in msg.parts:
            if isinstance(part, ToolCallPart):
                tool_calls.append(part.tool_name)
    return tool_calls


# ==============================================================================
# PHASE 2D: TEST WITH REAL WYCKOFF TOOLS AND DATA
# ==============================================================================

async def phase2d_test_with_llm(
    test_num: int,
    query: str,
    expected_directory: str,
    expected_result_contains: str,
    account_id: UUID,
    agent_config: Dict[str, Any]
):
    """Test a single query with real LLM and real Wyckoff tools."""
    print("\n" + "="*70)
    print(f"PHASE 2D - TEST {test_num}: {expected_directory.upper()} Directory")
    print("="*70)
    
    # Setup model using Pydantic AI Gateway
    model = "gateway/google-vertex:gemini-2.5-flash"
    
    # Get API key from environment
    api_key = os.getenv('PYDANTIC_AI_GATEWAY_API_KEY')
    if not api_key:
        raise ValueError("PYDANTIC_AI_GATEWAY_API_KEY not found in environment")
    
    # Create mock dependencies matching production structure
    mock_deps = MockSessionDependencies(
        account_id=account_id,
        agent_config=agent_config
    )
    
    # Create agent with real tools
    system_prompt_text = (
        "You are a helpful assistant for Wyckoff Hospital. You have access to tools.\n\n"
        "CRITICAL: ALWAYS follow this pattern:\n"
        "1. Call get_available_directories() FIRST to see what directories are available\n"
        "2. Review the metadata and choose the appropriate directory\n"
        "3. Call search_directory(list_name, query) with the chosen directory\n\n"
        "DO NOT skip step 1. You MUST call get_available_directories() before search_directory()."
    )
    
    agent = Agent(
        model,
        deps_type=MockSessionDependencies,
        tools=[get_available_directories, search_directory],
        system_prompt=system_prompt_text
    )
    
    print(f"\n📋 FULL PROMPT SENT TO LLM:")
    print(f"\n--- SYSTEM PROMPT ---")
    print(system_prompt_text)
    print(f"\n--- USER QUERY ---")
    print(f"{query}")
    print(f"--- END PROMPT ---\n")
    
    # Run query with mock dependencies
    result = await agent.run(query, deps=mock_deps)
    
    # Extract tool calls and their results
    tool_order = get_tool_call_order(result)
    
    print(f"\n🔧 TOOLS CALLED:")
    if tool_order:
        for i, tool in enumerate(tool_order, 1):
            print(f"   {i}. {tool}()")
    else:
        print("   ❌ No tools called")
    
    # Print detailed tool call arguments and results
    print(f"\n🔍 DETAILED TOOL CALLS AND RESULTS:")
    from pydantic_ai.messages import ModelRequest, ModelResponse, ToolReturnPart
    
    for msg in result.all_messages():
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    print(f"\n   📤 Tool Called: {part.tool_name}")
                    if hasattr(part, 'args'):
                        print(f"      Args: {part.args}")
        elif isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    print(f"\n   📥 Tool Result ({part.tool_name}):")
                    result_str = str(part.content)
                    if len(result_str) > 800:
                        print(f"      {result_str[:800]}...")
                    else:
                        print(f"      {result_str}")
    
    # Check if correct pattern followed
    correct_pattern = tool_order[0:2] == ['get_available_directories', 'search_directory'] if len(tool_order) >= 2 else False
    pattern_status = "✅ CORRECT" if correct_pattern else "❌ WRONG"
    print(f"\n   Discovery pattern: {pattern_status}")
    if not correct_pattern:
        print(f"   Expected: get_available_directories → search_directory")
        print(f"   Got: {' → '.join(tool_order) if tool_order else 'None'}")
    
    # Get the actual response
    response_text = result.output if hasattr(result, 'output') else str(result)
    
    print(f"\n💬 LLM RESPONSE:")
    print(f"   {response_text[:400]}{'...' if len(response_text) > 400 else ''}")
    
    # Check if expected directory was used
    directory_used = None
    for msg in result.all_messages():
        for part in msg.parts:
            if isinstance(part, ToolCallPart) and part.tool_name == 'search_directory':
                # Extract directory name from args
                if hasattr(part, 'args') and 'list_name' in part.args:
                    directory_used = part.args['list_name']
                    break
    
    if directory_used:
        directory_correct = directory_used == expected_directory
        directory_status = "✅ CORRECT" if directory_correct else "❌ WRONG"
        print(f"\n   Directory selected: {directory_used} {directory_status}")
        if not directory_correct:
            print(f"   Expected: {expected_directory}")
    
    # Check if expected result is in response
    result_found = expected_result_contains.lower() in response_text.lower()
    result_status = "✅ FOUND" if result_found else "❌ NOT FOUND"
    print(f"   Expected result '{expected_result_contains}': {result_status}")
    
    # Count extra tool calls
    extra_calls = len(tool_order) - 2 if len(tool_order) > 2 else 0
    if extra_calls > 0:
        print(f"\n   ⚠️  Extra tool calls: {extra_calls} (acceptable if < 2)")
    
    return correct_pattern and directory_correct


async def run_phase2d():
    """Run all Phase 2D tests with real Wyckoff tools."""
    print("\n" + "="*70)
    print("PHASE 2D: REAL WYCKOFF TOOLS WITH REAL LLM")
    print("="*70)
    print("\nModel: gateway/google-vertex:gemini-2.5-flash")
    print("Tools: Real production tools from directory_tools.py")
    print("Data: Real Wyckoff database (doctors, phone_directory)")
    print("\nNote: This will make actual API calls and database queries")
    
    # Check for API key
    api_key = os.getenv('PYDANTIC_AI_GATEWAY_API_KEY')
    if not api_key:
        print("\n❌ ERROR: PYDANTIC_AI_GATEWAY_API_KEY not found in environment")
        print("   Please set your Pydantic AI Gateway API key to run Phase 2D")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Load Wyckoff configuration and account
    try:
        agent_config = await load_wyckoff_config()
        account_id = await get_wyckoff_account_id()
    except Exception as e:
        print(f"\n❌ ERROR loading Wyckoff data: {e}")
        return False
    
    # Define test cases based on real Wyckoff data
    test_cases = [
        (1, "I need a cardiologist", "doctors", "Timothy Akojenu", "Cardiology"),
        (2, "What's the cardiology department phone number?", "contact_information", "718-963-2000", "Cardiology dept"),
        (3, "Find Dr. Premila Bhat", "doctors", "Premila Bhat", "Dr. Bhat"),
        (4, "What's the emergency room number?", "contact_information", "718-963-7272", "Emergency"),
        (5, "Find a gastroenterology doctor", "doctors", "Raghav Bansal", "Gastroenterology"),
    ]
    
    results = {}
    
    for test_num, query, expected_dir, expected_result, test_label in test_cases:
        try:
            passed = await phase2d_test_with_llm(
                test_num, query, expected_dir, expected_result,
                account_id, agent_config
            )
            results[f"Test {test_num} ({test_label})"] = passed
        except Exception as e:
            print(f"\n❌ ERROR in test {test_num}: {e}")
            import traceback
            traceback.print_exc()
            results[f"Test {test_num} ({test_label})"] = False
    
    print("\n" + "="*70)
    print("PHASE 2D SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    correct_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n{'✅' if all_passed else '⚠️'} Tests passed: {correct_count}/{total_count}")
    
    if all_passed:
        print("\n✅ SUCCESS! Real Wyckoff tools work with discovery pattern!")
        print("   → Production tools validated")
        print("   → Database queries working")
        print("   → Ready for deployment")
    else:
        print("\n⚠️  Some tests failed - review results above")
    
    return all_passed


if __name__ == '__main__':
    success = asyncio.run(run_phase2d())
    exit(0 if success else 1)

