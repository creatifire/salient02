"""
Investigation 001 - Tool Calling Behavior
Phase 2E: Multi-Turn Conversation Test

Tests whether tools continue working across multiple conversation turns
when message_history is provided (like production does).

Key difference from Phase 2D:
- Phase 2D: Single-turn queries (WORKS)
- Phase 2E: Multi-turn with message_history (Testing if this FAILS like production)
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
from pydantic_ai.messages import ToolCallPart, ModelRequest, ModelResponse
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


def analyze_message_history(message_history):
    """Analyze message history structure."""
    print(f"\n📊 MESSAGE HISTORY ANALYSIS:")
    print(f"   Total messages: {len(message_history)}")
    
    for i, msg in enumerate(message_history, 1):
        msg_type = type(msg).__name__
        print(f"\n   Message {i}: {msg_type}")
        
        if hasattr(msg, 'parts'):
            print(f"      Parts count: {len(msg.parts)}")
            for j, part in enumerate(msg.parts, 1):
                part_type = type(part).__name__
                print(f"         Part {j}: {part_type}")
                
                if isinstance(part, ToolCallPart):
                    print(f"            Tool: {part.tool_name}")
                    if hasattr(part, 'args'):
                        print(f"            Args: {part.args}")


def get_tool_call_order(result) -> list[str]:
    """Extract the order of tool calls from messages."""
    tool_calls = []
    for msg in result.all_messages():
        for part in msg.parts:
            if isinstance(part, ToolCallPart):
                tool_calls.append(part.tool_name)
    return tool_calls


# ==============================================================================
# PHASE 2E: MULTI-TURN CONVERSATION TEST
# ==============================================================================

async def run_multiturn_test():
    """Test multi-turn conversation with message_history."""
    print("\n" + "="*80)
    print("PHASE 2E: MULTI-TURN CONVERSATION TEST")
    print("="*80)
    print("\nGoal: Reproduce production behavior where tools stop working after turn 1")
    print("Method: Call agent.run() multiple times, passing message_history like production does")
    print("\nModel: gateway/google-vertex:gemini-2.5-flash")
    print("Tools: Real production tools from directory_tools.py")
    
    # Check for API key
    api_key = os.getenv('PYDANTIC_AI_GATEWAY_API_KEY')
    if not api_key:
        print("\n❌ ERROR: PYDANTIC_AI_GATEWAY_API_KEY not found in environment")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Load Wyckoff configuration and account
    try:
        agent_config = await load_wyckoff_config()
        account_id = await get_wyckoff_account_id()
    except Exception as e:
        print(f"\n❌ ERROR loading Wyckoff data: {e}")
        return False
    
    # Setup model using Pydantic AI Gateway
    model = "gateway/google-vertex:gemini-2.5-flash"
    
    # Create mock dependencies matching production structure
    mock_deps = MockSessionDependencies(
        account_id=account_id,
        agent_config=agent_config
    )
    
    # Create agent with real tools and system prompt
    system_prompt_text = (
        "You are Alex, a helpful assistant for Wyckoff Hospital. You have access to tools.\n\n"
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
    
    # ===========================================================================
    # TURN 1: First query (should work like Phase 2D)
    # ===========================================================================
    
    print("\n" + "="*80)
    print("TURN 1: First query (baseline)")
    print("="*80)
    
    query1 = "What's the cardiology department phone number?"
    print(f"\n👤 USER: {query1}")
    print(f"\n🔧 Calling agent.run() WITHOUT message_history (fresh start)")
    
    result1 = await agent.run(query1, deps=mock_deps)
    
    # Analyze turn 1 results
    tool_order1 = get_tool_call_order(result1)
    response1 = result1.output if hasattr(result1, 'output') else str(result1)
    
    print(f"\n🔧 TOOLS CALLED (Turn 1):")
    if tool_order1:
        for i, tool in enumerate(tool_order1, 1):
            print(f"   {i}. {tool}()")
    else:
        print("   ❌ No tools called")
    
    print(f"\n💬 LLM RESPONSE (Turn 1):")
    print(f"   {response1[:300]}{'...' if len(response1) > 300 else ''}")
    
    # Check if cardiology number found
    cardiology_found = "718-963-2000" in response1
    print(f"\n   Cardiology number (718-963-2000): {'✅ FOUND' if cardiology_found else '❌ NOT FOUND'}")
    
    # ===========================================================================
    # EXTRACT MESSAGE HISTORY (This is what production does)
    # ===========================================================================
    
    print("\n" + "="*80)
    print("EXTRACTING MESSAGE HISTORY")
    print("="*80)
    print("\n📝 Extracting message_history from result1.all_messages()")
    print("   This simulates how production loads history from database")
    
    message_history = result1.all_messages()
    analyze_message_history(message_history)
    
    # ===========================================================================
    # TURN 2: Second query WITH message_history (test if this breaks)
    # ===========================================================================
    
    print("\n" + "="*80)
    print("TURN 2: Second query WITH message_history")
    print("="*80)
    print("\n⚠️  CRITICAL: Now passing message_history like production does")
    
    query2 = "What about the emergency room?"
    print(f"\n👤 USER: {query2}")
    print(f"\n🔧 Calling agent.run() WITH message_history={len(message_history)} messages")
    
    result2 = await agent.run(
        query2, 
        deps=mock_deps,
        message_history=message_history  # <-- KEY: Pass history like production
    )
    
    # Analyze turn 2 results
    tool_order2 = get_tool_call_order(result2)
    response2 = result2.output if hasattr(result2, 'output') else str(result2)
    
    print(f"\n🔧 TOOLS CALLED (Turn 2):")
    if tool_order2:
        for i, tool in enumerate(tool_order2, 1):
            print(f"   {i}. {tool}()")
    else:
        print("   ❌ No tools called")
    
    print(f"\n💬 LLM RESPONSE (Turn 2):")
    print(f"   {response2[:300]}{'...' if len(response2) > 300 else ''}")
    
    # Check if emergency room number found
    emergency_found = "718-963-7272" in response2
    print(f"\n   Emergency room number (718-963-7272): {'✅ FOUND' if emergency_found else '❌ NOT FOUND'}")
    
    # ===========================================================================
    # TURN 3: Third query to see if pattern continues
    # ===========================================================================
    
    print("\n" + "="*80)
    print("TURN 3: Third query (extended test)")
    print("="*80)
    
    # Update message history with turn 2
    message_history = result2.all_messages()
    print(f"\n📝 Updated message_history: {len(message_history)} messages")
    
    query3 = "What's the number of the heart department?"
    print(f"\n👤 USER: {query3}")
    print(f"\n🔧 Calling agent.run() WITH message_history={len(message_history)} messages")
    
    result3 = await agent.run(
        query3, 
        deps=mock_deps,
        message_history=message_history
    )
    
    # Analyze turn 3 results
    tool_order3 = get_tool_call_order(result3)
    response3 = result3.output if hasattr(result3, 'output') else str(result3)
    
    print(f"\n🔧 TOOLS CALLED (Turn 3):")
    if tool_order3:
        for i, tool in enumerate(tool_order3, 1):
            print(f"   {i}. {tool}()")
    else:
        print("   ❌ No tools called")
    
    print(f"\n💬 LLM RESPONSE (Turn 3):")
    print(f"   {response3[:300]}{'...' if len(response3) > 300 else ''}")
    
    # Check if LLM refuses or uses tools
    refusal_indicators = [
        "cannot directly",
        "don't have access",
        "cannot access",
        "not able to",
        "unable to"
    ]
    refused = any(indicator in response3.lower() for indicator in refusal_indicators)
    print(f"\n   LLM refusal detected: {'❌ YES' if refused else '✅ NO'}")
    
    # ===========================================================================
    # SUMMARY
    # ===========================================================================
    
    print("\n" + "="*80)
    print("MULTI-TURN TEST SUMMARY")
    print("="*80)
    
    print(f"\n📊 TOOL CALLING ACROSS TURNS:")
    print(f"   Turn 1: {len(tool_order1)} tools called")
    print(f"   Turn 2: {len(tool_order2)} tools called")
    print(f"   Turn 3: {len(tool_order3)} tools called")
    
    tools_working_turn2 = len(tool_order2) > 0
    tools_working_turn3 = len(tool_order3) > 0
    
    if tools_working_turn2 and tools_working_turn3:
        print(f"\n✅ SUCCESS: Tools continue working in multi-turn conversations!")
        print(f"   → This means the production issue is NOT in message_history handling")
        print(f"   → Need to check production's load_conversation_history() implementation")
    elif not tools_working_turn2:
        print(f"\n❌ FAILURE: Tools stopped working on Turn 2!")
        print(f"   → This REPRODUCES the production bug")
        print(f"   → Problem is in how message_history affects Pydantic AI behavior")
    else:
        print(f"\n⚠️  PARTIAL: Tools worked on Turn 2 but failed on Turn 3")
        print(f"   → Tools degrade over multiple turns")
    
    print(f"\n📋 DETAILED BREAKDOWN:")
    print(f"   Turn 1 correct: {cardiology_found}")
    print(f"   Turn 2 correct: {emergency_found}")
    print(f"   Turn 3 refused: {refused}")
    
    return tools_working_turn2 and tools_working_turn3


if __name__ == '__main__':
    success = asyncio.run(run_multiturn_test())
    exit(0 if success else 1)

