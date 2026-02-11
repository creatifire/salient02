"""
Test script to verify tools are registered correctly with Pydantic AI Agent.
This follows the exact pattern from Pydantic AI documentation.
"""
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

# Import the actual tool functions
import sys
sys.path.insert(0, '/Users/arifsufi/Documents/GitHub/OpenThought/salient02/backend')

from app.agents.tools.directory_tools import get_available_directories, search_directory
from app.agents.tools.vector_tools import vector_search
from app.agents.base.dependencies import SessionDependencies


def test_tool_registration():
    """Test that tools are properly registered with the agent."""
    
    # Create a test model to inspect tool registration
    test_model = TestModel()
    
    # Create tools list (same as our production code)
    tools_list = [get_available_directories, search_directory, vector_search]
    
    print(f"✅ Tools list created: {[t.__name__ for t in tools_list]}")
    
    # Create agent with tools (following Pydantic AI docs pattern)
    agent = Agent(
        test_model,
        deps_type=SessionDependencies,
        system_prompt="Test agent",
        tools=tools_list  # Direct function list - Method 1 from docs
    )
    
    print(f"✅ Agent created with model: {test_model}")
    
    # Run the agent to trigger tool registration
    result = agent.run_sync('What tools are available?')
    
    # Check what tools were registered
    function_tools = test_model.last_model_request_parameters.function_tools
    
    print(f"\n📊 RESULTS:")
    print(f"   Tools count: {len(function_tools) if function_tools else 0}")
    print(f"   Tool names: {[t.name for t in function_tools] if function_tools else 'None'}")
    
    if function_tools:
        print(f"\n✅ SUCCESS! Tools are being registered correctly!")
        for tool in function_tools:
            print(f"   - {tool.name}: {tool.description[:100]}...")
    else:
        print(f"\n❌ FAILURE! No tools were registered!")
    
    return function_tools


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING TOOL REGISTRATION (Pydantic AI Pattern)")
    print("=" * 60)
    
    try:
        tools = test_tool_registration()
        if tools:
            exit(0)  # Success
        else:
            exit(1)  # Failure
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

