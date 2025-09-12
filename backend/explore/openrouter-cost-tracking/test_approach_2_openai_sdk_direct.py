#!/usr/bin/env python3
"""
Approach 2: Use OpenAI SDK directly with OpenRouter endpoint
and usage parameter to get accurate cost data.

This bypasses Pydantic AI but gives us full control over the API request
and guaranteed access to OpenRouter's cost data.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print('='*70)

async def test_approach_2():
    """Test Approach 2: OpenAI SDK directly with OpenRouter."""
    
    print_section("APPROACH 2: OPENAI SDK DIRECT WITH OPENROUTER")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    try:
        # Try importing OpenAI SDK
        try:
            from openai import AsyncOpenAI
            print("✅ OpenAI SDK available")
        except ImportError:
            print("❌ OpenAI SDK not available, install with: pip install openai")
            return False
        
        # Configure OpenAI client for OpenRouter
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        print("✅ OpenAI client configured for OpenRouter")
        
        # Test basic call without usage tracking
        print("\n🔬 Testing without usage parameter")
        response_basic = await client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[
                {"role": "user", "content": "Hello, respond with exactly: 'Basic test response'"}
            ],
            max_tokens=50
        )
        
        print(f"✅ Basic response: '{response_basic.choices[0].message.content}'")
        print(f"📊 Basic usage: {response_basic.usage}")
        basic_cost = getattr(response_basic.usage, 'cost', None) if response_basic.usage else None
        print(f"💰 Basic cost: {basic_cost}")
        
        # Test call WITH usage tracking parameter
        print("\n🔬 Testing WITH usage parameter")
        response_with_usage = await client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[
                {"role": "user", "content": "Hello, respond with exactly: 'Usage tracking test response'"}
            ],
            max_tokens=50,
            extra_body={"usage": {"include": True}}  # This is the critical parameter
        )
        
        print(f"✅ Usage response: '{response_with_usage.choices[0].message.content}'")
        print(f"📊 Usage tracking: {response_with_usage.usage}")
        
        # Check for cost data
        usage_cost = getattr(response_with_usage.usage, 'cost', None) if response_with_usage.usage else None
        print(f"💰 Usage tracking cost: {usage_cost}")
        
        # Check raw response attributes
        print(f"\n🔍 Usage object attributes:")
        if response_with_usage.usage:
            usage_attrs = [attr for attr in dir(response_with_usage.usage) if not attr.startswith('_')]
            for attr in usage_attrs:
                try:
                    value = getattr(response_with_usage.usage, attr)
                    print(f"  - {attr}: {value}")
                except:
                    print(f"  - {attr}: <error accessing>")
        
        # Assess results
        print(f"\n📊 APPROACH 2 ASSESSMENT:")
        if usage_cost and usage_cost > 0:
            print(f"✅ SUCCESS: Got real cost data: ${usage_cost}")
            print(f"✅ OpenAI SDK + OpenRouter + usage parameter works")
            return True
        elif hasattr(response_with_usage.usage, 'cost'):
            print(f"⚠️  PARTIAL: Cost field exists but is {usage_cost}")
            print(f"⚠️  May need different parameter format")
            return False
        else:
            print(f"❌ FAILED: No cost field in response")
            print(f"❌ OpenAI SDK doesn't preserve OpenRouter cost data")
            return False
        
    except Exception as e:
        print(f"❌ Approach 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_approach_2())
    print(f"\n🎯 APPROACH 2 RESULT: {'SUCCESS' if success else 'FAILED'}")
