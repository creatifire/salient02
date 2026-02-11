"""
Ultra-simple test to verify tools are registered with Pydantic AI.
Uses TestModel with no dependencies.
"""
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


def simple_tool() -> str:
    """A simple test tool."""
    return "Tool works!"


def test_simple():
    """Test that a simple tool registers correctly."""
    test_model = TestModel()
    
    agent = Agent(
        test_model,
        tools=[simple_tool],  # Direct function list
        system_prompt="Test"
    )
    
    print(f"Agent created with tools: [simple_tool]")
    
    # Run to trigger registration
    result = agent.run_sync('test')
    
    # Check registration
    tools = test_model.last_model_request_parameters.function_tools
    
    if tools:
        print(f"✅ SUCCESS! {len(tools)} tool(s) registered:")
        for t in tools:
            print(f"   - {t.name}")
        return True
    else:
        print(f"❌ FAILURE! No tools registered")
        return False


if __name__ == '__main__':
    success = test_simple()
    exit(0 if success else 1)

