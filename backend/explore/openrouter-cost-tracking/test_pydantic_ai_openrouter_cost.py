#!/usr/bin/env python3
"""
Standalone test script to verify Pydantic AI + OpenRouter cost tracking.

This script tests in isolation whether we can extract OpenRouter cost data
through Pydantic AI without the complexity of the full application.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Pydantic AI imports
try:
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
except ImportError as e:
    print(f"❌ Failed to import Pydantic AI: {e}")
    print("Install with: pip install pydantic-ai")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

async def test_pydantic_ai_openrouter():
    """Test Pydantic AI with OpenRouter and inspect all response data."""
    
    print_section("PYDANTIC AI + OPENROUTER COST TRACKING TEST")
    
    # Get API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("Set it in .env file or environment variables")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test configuration
    model_name = "deepseek/deepseek-chat-v3.1"  # Use a low-cost model for testing
    test_message = "Hello! Please respond with exactly 'Test response for cost tracking.'"
    
    print(f"📝 Model: {model_name}")
    print(f"📝 Test message: '{test_message}'")
    
    # Configure Pydantic AI with OpenRouter
    try:
        print_section("CONFIGURING PYDANTIC AI AGENT")
        
        model = OpenAIChatModel(
            model_name,
            provider=OpenAIProvider(
                base_url='https://openrouter.ai/api/v1',
                api_key=api_key
            )
        )
        
        agent = Agent(
            model,
            system_prompt="You are a helpful assistant. Respond concisely and exactly as requested."
        )
        
        print("✅ Agent configured successfully")
        
    except Exception as e:
        print(f"❌ Failed to configure agent: {e}")
        return
    
    # Make the LLM call
    try:
        print_section("MAKING LLM CALL")
        print("⏳ Calling OpenRouter via Pydantic AI...")
        
        # Try multiple approaches to pass usage parameter through Pydantic AI
        try:
            # Method 1: Direct usage parameter
            result = await agent.run(test_message, usage={"include": True})
            print("✅ Method 1 (direct usage param) worked!")
        except Exception as e1:
            print(f"❌ Method 1 failed: {e1}")
            try:
                # Method 2: Extra body parameter (common in OpenAI SDK)
                result = await agent.run(test_message, extra_body={"usage": {"include": True}})
                print("✅ Method 2 (extra_body) worked!")
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                try:
                    # Method 3: Standard call without usage tracking
                    result = await agent.run(test_message)
                    print("✅ Method 3 (standard call) worked - but no cost data expected")
                except Exception as e3:
                    print(f"❌ All methods failed: {e3}")
                    raise e3
        
        print("✅ LLM call completed")
        print(f"📤 Response: '{result.output}'")
        
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return
    
    # Inspect all response data
    print_section("INSPECTING RESPONSE DATA")
    
    # 1. Basic result attributes
    print("📊 BASIC RESULT ATTRIBUTES:")
    print(f"  - Type: {type(result)}")
    print(f"  - Output: '{result.output}'")
    print(f"  - Has usage: {hasattr(result, 'usage')}")
    
    # 2. Usage data
    if hasattr(result, 'usage'):
        usage = result.usage()
        print(f"\n📊 USAGE DATA:")
        print(f"  - Type: {type(usage)}")
        print(f"  - Input tokens: {getattr(usage, 'input_tokens', 'N/A')}")
        print(f"  - Output tokens: {getattr(usage, 'output_tokens', 'N/A')}")
        print(f"  - Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")
        print(f"  - Requests: {getattr(usage, 'requests', 'N/A')}")
        print(f"  - Details: {getattr(usage, 'details', 'N/A')}")
        
        # Check for any cost-related attributes
        usage_attrs = [attr for attr in dir(usage) if not attr.startswith('_')]
        cost_attrs = [attr for attr in usage_attrs if 'cost' in attr.lower()]
        if cost_attrs:
            print(f"  - Cost-related attrs: {cost_attrs}")
        else:
            print("  - No cost-related attributes found")
    
    # 3. Raw response data
    print(f"\n📊 RAW RESPONSE DATA:")
    print(f"  - Has _raw_response: {hasattr(result, '_raw_response')}")
    
    if hasattr(result, '_raw_response'):
        raw_response = getattr(result, '_raw_response')
        print(f"  - Raw response type: {type(raw_response)}")
        print(f"  - Raw response value: {raw_response}")
        
        if isinstance(raw_response, dict):
            print(f"  - Raw response keys: {list(raw_response.keys())}")
            
            # Check for usage in raw response
            if 'usage' in raw_response:
                raw_usage = raw_response['usage']
                print(f"  - Raw usage: {raw_usage}")
                
                # Look for cost field
                if isinstance(raw_usage, dict) and 'cost' in raw_usage:
                    cost = raw_usage['cost']
                    print(f"  - 🎯 FOUND COST: ${cost}")
                else:
                    print("  - ❌ No 'cost' field in raw usage")
            else:
                print("  - ❌ No 'usage' key in raw response")
        else:
            print("  - ❌ Raw response is not a dictionary")
    else:
        print("  - ❌ No _raw_response attribute")
    
    # 4. All result attributes
    print(f"\n📊 ALL RESULT ATTRIBUTES:")
    all_attrs = [attr for attr in dir(result) if not attr.startswith('__')]
    for attr in all_attrs:
        try:
            value = getattr(result, attr)
            if callable(value):
                print(f"  - {attr}(): {type(value)} (method)")
            else:
                print(f"  - {attr}: {type(value)} = {str(value)[:100]}...")
        except Exception as e:
            print(f"  - {attr}: Error accessing - {e}")
    
    # 5. Final assessment
    print_section("COST TRACKING ASSESSMENT")
    
    # Try to extract cost data using all possible methods
    cost_found = False
    cost_value = 0.0
    cost_source = None
    
    # Method 1: _raw_response.usage.cost
    if hasattr(result, '_raw_response'):
        raw_response = getattr(result, '_raw_response')
        if isinstance(raw_response, dict) and 'usage' in raw_response:
            raw_usage = raw_response['usage']
            if isinstance(raw_usage, dict) and 'cost' in raw_usage:
                cost_value = raw_usage['cost']
                cost_source = "_raw_response.usage.cost"
                cost_found = True
    
    # Method 2: Check usage object for any cost attributes
    if not cost_found and hasattr(result, 'usage'):
        usage = result.usage()
        for attr in dir(usage):
            if 'cost' in attr.lower() and not attr.startswith('_'):
                try:
                    cost_value = getattr(usage, attr)
                    cost_source = f"usage.{attr}"
                    cost_found = True
                    break
                except:
                    pass
    
    if cost_found:
        print(f"✅ COST DATA FOUND!")
        print(f"   Source: {cost_source}")
        print(f"   Cost: ${cost_value}")
        print(f"   Ready for customer billing: YES")
    else:
        print(f"❌ NO COST DATA FOUND")
        print(f"   Pydantic AI is not preserving OpenRouter cost data")
        print(f"   Need alternative approach for customer billing")
    
    print_section("TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_pydantic_ai_openrouter())
