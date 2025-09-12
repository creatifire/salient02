#!/usr/bin/env python3
"""
Approach 3: Use our existing openrouter_client.py which has been fixed
to include the "usage": {"include": true} parameter.

This is the most reliable approach as we have full control over the
implementation and know it works with OpenRouter's cost tracking.
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

async def test_approach_3():
    """Test Approach 3: Our fixed openrouter_client.py."""
    
    print_section("APPROACH 3: FIXED OPENROUTER_CLIENT.PY")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    try:
        # Import our fixed openrouter client
        from app.openrouter_client import chat_completion_with_usage
        print("✅ openrouter_client imported successfully")
        
        # Test the fixed client
        print("\n🔬 Testing chat_completion_with_usage()")
        result = await chat_completion_with_usage(
            message="Hello, respond with exactly: 'OpenRouter client test response'",
            model="deepseek/deepseek-chat-v3.1",
            temperature=0.7,
            max_tokens=50
        )
        
        print(f"✅ Response received")
        print(f"📝 Content: '{result['content']}'")
        print(f"📊 Usage: {result['usage']}")
        
        # Check for cost data
        usage_data = result.get('usage', {})
        cost = usage_data.get('cost', 0.0)
        prompt_tokens = usage_data.get('prompt_tokens', 0)
        completion_tokens = usage_data.get('completion_tokens', 0)
        total_tokens = usage_data.get('total_tokens', 0)
        
        print(f"\n💰 Cost Analysis:")
        print(f"  - Cost: ${cost}")
        print(f"  - Prompt tokens: {prompt_tokens}")
        print(f"  - Completion tokens: {completion_tokens}")
        print(f"  - Total tokens: {total_tokens}")
        
        # Assess results
        print(f"\n📊 APPROACH 3 ASSESSMENT:")
        if cost > 0:
            print(f"✅ SUCCESS: Real OpenRouter cost retrieved: ${cost}")
            print(f"✅ Single API call with accurate cost tracking")
            print(f"✅ Ready for production use")
            return True
        else:
            print(f"❌ FAILED: Cost is still {cost}")
            print(f"❌ Usage parameter may not be working correctly")
            return False
            
    except Exception as e:
        print(f"❌ Approach 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_comparison_with_direct_api():
    """Compare our client with direct API call to validate consistency."""
    
    print_section("VALIDATION: COMPARE WITH DIRECT API")
    
    try:
        import httpx
        import json
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            return
        
        # Direct API call
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek/deepseek-chat-v3.1",
            "messages": [{"role": "user", "content": "Hello, respond with exactly: 'Direct API validation'"}],
            "max_tokens": 50,
            "temperature": 0.7,
            "usage": {"include": True}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            direct_cost = data.get('usage', {}).get('cost', 0.0)
            print(f"🔗 Direct API cost: ${direct_cost}")
            
            # Test our client with same parameters
            from app.openrouter_client import chat_completion_with_usage
            result = await chat_completion_with_usage(
                message="Hello, respond with exactly: 'Client API validation'",
                model="deepseek/deepseek-chat-v3.1",
                temperature=0.7,
                max_tokens=50
            )
            
            client_cost = result.get('usage', {}).get('cost', 0.0)
            print(f"🔧 Client API cost: ${client_cost}")
            
            if direct_cost > 0 and client_cost > 0:
                print(f"✅ Both methods return real cost data")
                print(f"✅ Our client is working correctly")
            elif direct_cost > 0 and client_cost == 0:
                print(f"❌ Direct API works but our client doesn't")
            elif direct_cost == 0 and client_cost == 0:
                print(f"❌ Neither method returns cost data")
            else:
                print(f"⚠️  Inconsistent results")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")

if __name__ == "__main__":
    success = asyncio.run(test_approach_3())
    print(f"\n🎯 APPROACH 3 RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print("\n🔍 Running validation...")
        asyncio.run(test_comparison_with_direct_api())
