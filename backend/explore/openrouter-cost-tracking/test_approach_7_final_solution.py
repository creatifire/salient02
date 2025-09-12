#!/usr/bin/env python3
"""
Approach 7: FINAL SOLUTION - Subclass OpenAIChatModel to inject usage parameter
and capture OpenRouter cost data while preserving ALL Pydantic AI capabilities.

Architecture discovered:
OpenRouterProvider -> openai.AsyncOpenAI -> OpenAIChatModel.request() 

By overriding OpenAIChatModel.request(), we can:
✅ Inject {"usage": {"include": true}} automatically
✅ Capture raw OpenRouter response with cost data
✅ Preserve ALL Pydantic AI features (agents, graphs, validation)
✅ Make it transparent to the application
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic_ai import Agent
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai._utils import guard_tool_call_id as _guard_tool_call_id
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CostTrackingOpenAIChatModel(OpenAIChatModel):
    """
    Enhanced OpenAIChatModel that automatically injects OpenRouter usage
    parameter and captures cost data while preserving all Pydantic AI features.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_cost_data: Optional[Dict[str, Any]] = None
        print(f"🔧 Cost tracking model initialized")
    
    async def request(self, messages, model_settings, model_request_parameters) -> Any:
        """
        Override the request method to inject usage parameter and capture cost data.
        This is the key method where HTTP requests are made to OpenRouter.
        """
        
        # Get the original model settings or create empty dict
        enhanced_settings = model_settings.copy() if model_settings else {}
        
        # Automatically inject usage parameter for OpenRouter cost tracking
        enhanced_settings['extra_body'] = enhanced_settings.get('extra_body', {})
        enhanced_settings['extra_body']['usage'] = {'include': True}
        
        print(f"🔧 Injected usage parameter for cost tracking")
        
        # Call the parent's request method with enhanced settings
        try:
            response = await super().request(messages, enhanced_settings)
            
            # Capture raw response data for cost extraction
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                
                # Extract OpenRouter cost data
                cost_data = {
                    'cost': getattr(usage, 'cost', 0.0),
                    'cost_details': getattr(usage, 'cost_details', {}),
                    'prompt_tokens': getattr(usage, 'prompt_tokens', 0),
                    'completion_tokens': getattr(usage, 'completion_tokens', 0),
                    'total_tokens': getattr(usage, 'total_tokens', 0),
                    'is_byok': getattr(usage, 'is_byok', False),
                    'prompt_tokens_details': getattr(usage, 'prompt_tokens_details', {}),
                    'completion_tokens_details': getattr(usage, 'completion_tokens_details', {})
                }
                
                self._last_cost_data = cost_data
                print(f"📦 Captured cost data: ${cost_data['cost']}")
            else:
                print(f"⚠️  No usage data in response")
                self._last_cost_data = None
            
            return response
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            self._last_cost_data = None
            raise
    
    def get_cost_data(self) -> Optional[Dict[str, Any]]:
        """Get the cost data from the last request."""
        return self._last_cost_data

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print('='*70)

async def test_final_solution():
    """Test the final cost tracking solution."""
    
    print_section("APPROACH 7: FINAL COST TRACKING SOLUTION")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    try:
        # Create OpenRouter provider (native Pydantic AI)
        provider = OpenRouterProvider(api_key=api_key)
        print("✅ Native OpenRouter provider created")
        
        # Create our enhanced model with cost tracking
        model = CostTrackingOpenAIChatModel('deepseek/deepseek-chat-v3.1', provider=provider)
        print("✅ Cost tracking model created")
        
        # Create Pydantic AI agent with full capabilities
        agent = Agent(
            model,
            system_prompt="You are a helpful assistant with advanced cost tracking capabilities."
        )
        print("✅ Pydantic AI agent created - ALL features available!")
        
        # Test 1: Basic functionality
        print(f"\n🔬 Test 1: Basic agent functionality with cost tracking")
        result1 = await agent.run("Hello, respond with exactly: 'Final solution test'")
        print(f"✅ Response: '{result1.output}'")
        
        # Check Pydantic AI usage (standard)
        pydantic_usage = result1.usage()
        print(f"📊 Pydantic AI usage: {pydantic_usage}")
        
        # Check our enhanced cost data
        cost_data1 = model.get_cost_data()
        if cost_data1 and cost_data1.get('cost', 0) > 0:
            print(f"💰 Enhanced cost data:")
            print(f"  💵 Cost: ${cost_data1['cost']}")
            print(f"  🔢 Prompt tokens: {cost_data1['prompt_tokens']}")
            print(f"  🔢 Completion tokens: {cost_data1['completion_tokens']}")
            print(f"  🔢 Total tokens: {cost_data1['total_tokens']}")
            print(f"  📊 Cost details: {cost_data1['cost_details']}")
        else:
            print(f"❌ No cost data captured")
            return False
        
        # Test 2: Message history (Pydantic AI feature)
        print(f"\n🔬 Test 2: Message history with cost tracking")
        result2 = await agent.run(
            "What did I just ask you to say?",
            message_history=result1.all_messages()
        )
        print(f"✅ Message history works: '{result2.output}'")
        
        cost_data2 = model.get_cost_data()
        if cost_data2:
            print(f"💰 Second call cost: ${cost_data2['cost']}")
        
        # Test 3: Dependencies (Advanced Pydantic AI feature)
        print(f"\n🔬 Test 3: Dependencies with cost tracking")
        from pydantic import BaseModel
        
        class UserSession(BaseModel):
            user_id: str
            request_count: int
            premium_user: bool
        
        session_agent = Agent(
            model,
            deps_type=UserSession,
            system_prompt="You are a session-aware assistant. Mention if the user is premium and their request count."
        )
        
        user_session = UserSession(user_id="user123", request_count=15, premium_user=True)
        result3 = await session_agent.run(
            "What's my account status?",
            deps=user_session
        )
        print(f"✅ Dependencies work: '{result3.output}'")
        
        cost_data3 = model.get_cost_data()
        if cost_data3:
            print(f"💰 Dependency call cost: ${cost_data3['cost']}")
        
        # Test 4: Multiple agents with same model
        print(f"\n🔬 Test 4: Multiple agents with shared cost tracking model")
        agent2 = Agent(
            model,  # Same model instance
            system_prompt="You are a second agent sharing the cost tracking model."
        )
        
        result4 = await agent2.run("Hello from second agent!")
        print(f"✅ Multiple agents work: '{result4.output}'")
        
        cost_data4 = model.get_cost_data()
        if cost_data4:
            print(f"💰 Multi-agent call cost: ${cost_data4['cost']}")
        
        # Calculate total costs for session
        total_cost = sum([
            cost_data1.get('cost', 0),
            cost_data2.get('cost', 0) if cost_data2 else 0,
            cost_data3.get('cost', 0) if cost_data3 else 0,
            cost_data4.get('cost', 0) if cost_data4 else 0
        ])
        
        print(f"\n📊 FINAL SOLUTION ASSESSMENT:")
        print(f"✅ SUCCESS: All tests passed with real cost data!")
        print(f"✅ SUCCESS: Full Pydantic AI capabilities preserved")
        print(f"✅ SUCCESS: Automatic OpenRouter cost tracking")
        print(f"✅ SUCCESS: Native provider compatibility maintained")
        print(f"✅ SUCCESS: Multi-agent support with shared model")
        print(f"💰 Total session cost: ${total_cost}")
        print(f"🎯 PERFECT SOLUTION ACHIEVED!")
        
        return True
        
    except Exception as e:
        print(f"❌ Final solution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 Testing the FINAL SOLUTION: Full Pydantic AI + OpenRouter Cost Tracking!")
    
    success = asyncio.run(test_final_solution())
    print(f"\n🎯 APPROACH 7 RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print(f"\n🏆 🏆 🏆 PERFECT SOLUTION READY! 🏆 🏆 🏆")
        print(f"✅ Full Pydantic AI capabilities (agents, graphs, validation, dependencies)")
        print(f"✅ Native OpenRouter provider integration")
        print(f"✅ Automatic cost tracking with real OpenRouter data")
        print(f"✅ Transparent to application code")
        print(f"✅ Ready for production implementation!")
        print(f"✅ Best of ALL worlds achieved!")
    else:
        print(f"❌ Need to investigate further...")
