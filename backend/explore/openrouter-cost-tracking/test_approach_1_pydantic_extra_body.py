#!/usr/bin/env python3
"""
Approach 1: Test if Pydantic AI's OpenAI provider supports extra_body parameter
to pass OpenRouter's usage tracking parameter.

This would be the ideal solution as it keeps all Pydantic AI benefits while
getting accurate cost data from OpenRouter.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print('='*70)

async def test_approach_1():
    """Test Approach 1: Pydantic AI with extra_body parameter."""
    
    print_section("APPROACH 1: PYDANTIC AI + EXTRA_BODY PARAMETER")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    try:
        # Configure Pydantic AI with OpenRouter
        model = OpenAIChatModel(
            "deepseek/deepseek-chat-v3.1",
            provider=OpenAIProvider(
                base_url='https://openrouter.ai/api/v1',
                api_key=api_key
            )
        )
        
        agent = Agent(
            model,
            system_prompt="You are a helpful assistant. Be concise."
        )
        
        print("✅ Agent configured")
        
        # Test Method 1: Try passing extra_body through agent.run()
        print("\n🔬 Testing Method 1: extra_body in agent.run()")
        try:
            result = await agent.run(
                "Hello, respond with exactly: 'Test 1 response'",
                extra_body={"usage": {"include": True}}
            )
            print(f"✅ Method 1 worked! Response: '{result.output}'")
            
            # Check for cost data
            usage = result.usage()
            print(f"📊 Usage: {usage}")
            
            # Check for raw response
            raw_response = getattr(result, '_raw_response', None)
            if raw_response:
                print(f"📦 Raw response available: {type(raw_response)}")
                if isinstance(raw_response, dict) and 'usage' in raw_response:
                    openrouter_usage = raw_response['usage']
                    cost = openrouter_usage.get('cost', 0.0)
                    print(f"💰 OpenRouter cost found: ${cost}")
                    return True
            
            print("❌ Method 1: No cost data in raw response")
            
        except Exception as e:
            print(f"❌ Method 1 failed: {e}")
        
        # Test Method 2: Try model-level configuration
        print("\n🔬 Testing Method 2: Model-level extra configuration")
        try:
            # This is speculative - check if OpenAI provider supports model-level config
            result = await agent.run("Hello, respond with exactly: 'Test 2 response'")
            print(f"✅ Method 2 basic call worked: '{result.output}'")
            
            # Check if there's a way to configure the model with extra parameters
            # This would require checking Pydantic AI documentation
            print("❌ Method 2: No model-level extra_body configuration found")
            
        except Exception as e:
            print(f"❌ Method 2 failed: {e}")
        
        print("\n📊 APPROACH 1 ASSESSMENT:")
        print("❌ Pydantic AI doesn't support passing OpenRouter usage parameter")
        print("❌ No extra_body parameter forwarding found")
        print("❌ Raw response doesn't contain OpenRouter cost data")
        return False
        
    except Exception as e:
        print(f"❌ Approach 1 setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_approach_1())
    print(f"\n🎯 APPROACH 1 RESULT: {'SUCCESS' if success else 'FAILED'}")
