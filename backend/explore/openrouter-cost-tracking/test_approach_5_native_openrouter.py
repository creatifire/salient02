#!/usr/bin/env python3
"""
Approach 5: Test Pydantic AI's native OpenRouter provider
Based on research suggesting Pydantic AI has native OpenRouter support
with built-in cost tracking capabilities.

This would be the IDEAL solution if it exists:
✅ Full Pydantic AI capabilities (agents, graphs, validation)
✅ Native OpenRouter cost tracking
✅ Official support (not custom hacking)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic_ai import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print('='*70)

async def test_native_openrouter_provider():
    """Test if Pydantic AI has native OpenRouter provider with cost tracking."""
    
    print_section("APPROACH 5: PYDANTIC AI NATIVE OPENROUTER PROVIDER")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    # Test 1: Check if OpenRouterProvider exists
    print("\n🔍 Checking for native OpenRouter provider...")
    try:
        from pydantic_ai.providers.openrouter import OpenRouterProvider
        print("✅ Found pydantic_ai.providers.openrouter.OpenRouterProvider!")
        
        # Try to initialize it
        provider = OpenRouterProvider(api_key=api_key)
        print("✅ OpenRouterProvider initialized successfully")
        
        # Import OpenAI model 
        from pydantic_ai.models.openai import OpenAIModel
        
        # Create model with OpenRouter provider
        model = OpenAIModel('deepseek/deepseek-chat-v3.1', provider=provider)
        print("✅ Model configured with OpenRouterProvider")
        
        # Create agent
        agent = Agent(model)
        print("✅ Agent created with OpenRouter provider")
        
        return await test_cost_tracking_with_native_provider(agent)
        
    except ImportError as e:
        print(f"❌ OpenRouterProvider not found: {e}")
        print("   Pydantic AI may not have native OpenRouter support")
        
    # Test 2: Check if OpenAIModel + OpenRouter + usage parameter works
    print("\n🔍 Testing OpenAIModel with OpenRouter endpoint + usage parameter...")
    try:
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider
        
        # Configure for OpenRouter
        provider = OpenAIProvider(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        model = OpenAIModel('deepseek/deepseek-chat-v3.1', provider=provider)
        agent = Agent(model)
        
        print("✅ Agent configured with OpenRouter endpoint")
        
        return await test_cost_tracking_with_usage_parameter(agent)
        
    except Exception as e:
        print(f"❌ OpenRouter endpoint configuration failed: {e}")
        return False

async def test_cost_tracking_with_native_provider(agent):
    """Test cost tracking with native OpenRouter provider."""
    
    print("\n💰 Testing cost tracking with native OpenRouter provider")
    
    try:
        # Test basic agent call
        result = await agent.run("Hello, respond with exactly: 'Native provider test'")
        print(f"✅ Agent response: '{result.output}'")
        
        # Check for usage data
        usage = result.usage()
        print(f"📊 Usage data: {usage}")
        
        # Check if cost data is included
        if hasattr(usage, 'cost'):
            cost = getattr(usage, 'cost')
            print(f"💰 Cost found: ${cost}")
            return True
        else:
            print("❌ No cost data in usage")
            
        # Check for cost in usage details
        if hasattr(usage, 'details'):
            details = getattr(usage, 'details', {})
            if 'cost' in details:
                cost = details['cost']
                print(f"💰 Cost found in details: ${cost}")
                return True
                
        print("❌ No cost data found in native provider")
        return False
        
    except Exception as e:
        print(f"❌ Native provider test failed: {e}")
        return False

async def test_cost_tracking_with_usage_parameter(agent):
    """Test if we can pass usage parameter to agent.run()."""
    
    print("\n💰 Testing cost tracking with usage parameter")
    
    try:
        # Test Method 1: usage parameter in agent.run()
        print("🔬 Method 1: agent.run() with usage parameter")
        try:
            result = await agent.run(
                "Hello, respond with exactly: 'Usage parameter test'",
                usage={'include': True}
            )
            print(f"✅ Method 1 worked: '{result.output}'")
            
            usage = result.usage()
            print(f"📊 Usage: {usage}")
            
            # Check for cost data
            cost_attrs = [attr for attr in dir(usage) if 'cost' in attr.lower()]
            if cost_attrs:
                print(f"💰 Cost attributes found: {cost_attrs}")
                for attr in cost_attrs:
                    value = getattr(usage, attr)
                    print(f"  {attr}: {value}")
                    if isinstance(value, (int, float)) and value > 0:
                        print(f"✅ SUCCESS: Real cost data found: ${value}")
                        return True
            
            print("❌ Method 1: No cost data despite usage parameter")
            
        except Exception as e:
            print(f"❌ Method 1 failed: {e}")
        
        # Test Method 2: Basic call without usage parameter
        print("\n🔬 Method 2: Basic call (check if cost is automatic)")
        result2 = await agent.run("Hello, respond with exactly: 'Basic test'")
        usage2 = result2.usage()
        
        print(f"📊 Basic usage: {usage2}")
        
        # Check all attributes for cost-related data
        usage_attrs = [attr for attr in dir(usage2) if not attr.startswith('_')]
        print(f"📋 All usage attributes: {usage_attrs}")
        
        for attr in usage_attrs:
            try:
                value = getattr(usage2, attr)
                if 'cost' in attr.lower() or (isinstance(value, (int, float)) and value > 0 and 'token' not in attr.lower()):
                    print(f"💰 Potential cost field {attr}: {value}")
            except:
                pass
        
        print("❌ Method 2: No cost data found")
        return False
        
    except Exception as e:
        print(f"❌ Usage parameter test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing Pydantic AI's NATIVE OpenRouter support!")
    
    success = asyncio.run(test_native_openrouter_provider())
    print(f"\n🎯 APPROACH 5 RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print(f"\n🏆 IDEAL SOLUTION FOUND:")
        print(f"✅ Native Pydantic AI OpenRouter support")
        print(f"✅ Built-in cost tracking")
        print(f"✅ All agent capabilities preserved")
        print(f"✅ Official support (no custom code needed)")
    else:
        print(f"\n⚠️  Native OpenRouter support not available")
        print(f"   Will need custom provider approach")
