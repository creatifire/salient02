#!/usr/bin/env python3
"""
Direct OpenRouter API test script to verify cost data availability.

This script bypasses Pydantic AI and calls OpenRouter directly to confirm
that OpenRouter does provide cost data in its responses.
"""

import asyncio
import os
import sys
import json
import httpx
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

async def test_direct_openrouter():
    """Test direct OpenRouter API call to verify cost data."""
    
    print_section("DIRECT OPENROUTER API COST DATA TEST")
    
    # Get API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test configuration
    model_name = "deepseek/deepseek-chat-v3.1"
    test_message = "Hello! Please respond with exactly 'Direct API test response.'"
    
    print(f"📝 Model: {model_name}")
    print(f"📝 Test message: '{test_message}'")
    
    # Prepare OpenRouter API request
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-repo/openthought-salient02",
        "X-Title": "OpenThought Salient02 Cost Test"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": test_message}
        ],
        "max_tokens": 50,
        "temperature": 0.1,
        "usage": {
            "include": True
        }
    }
    
    print_section("MAKING DIRECT OPENROUTER API CALL")
    print("⏳ Calling OpenRouter API directly...")
    print(f"🔗 URL: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
        
        print(f"✅ HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        # Parse response
        response_data = response.json()
        
        print_section("INSPECTING OPENROUTER RESPONSE")
        
        # 1. Full response structure
        print("📊 RESPONSE STRUCTURE:")
        print(f"  - Keys: {list(response_data.keys())}")
        
        # 2. Usage data
        if 'usage' in response_data:
            usage = response_data['usage']
            print(f"\n📊 USAGE DATA:")
            print(f"  - Type: {type(usage)}")
            print(f"  - Keys: {list(usage.keys()) if isinstance(usage, dict) else 'Not a dict'}")
            
            if isinstance(usage, dict):
                for key, value in usage.items():
                    print(f"  - {key}: {value}")
                
                # Check for cost field
                if 'cost' in usage:
                    cost = usage['cost']
                    print(f"\n🎯 COST FOUND: ${cost}")
                    print(f"   Type: {type(cost)}")
                    print(f"   Value: {cost}")
                else:
                    print(f"\n❌ No 'cost' field in usage data")
        else:
            print(f"\n❌ No 'usage' key in response")
        
        # 3. Message content
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
                print(f"\n📤 Response content: '{content}'")
        
        # 4. Full raw response (truncated)
        print(f"\n📊 FULL RAW RESPONSE:")
        raw_json = json.dumps(response_data, indent=2)
        if len(raw_json) > 1000:
            print(f"{raw_json[:1000]}...")
            print(f"   (truncated, full response is {len(raw_json)} characters)")
        else:
            print(raw_json)
        
        print_section("COST DATA ASSESSMENT")
        
        # Final cost extraction test
        cost_found = False
        cost_value = 0.0
        
        if 'usage' in response_data:
            usage = response_data['usage']
            if isinstance(usage, dict) and 'cost' in usage:
                cost_value = usage['cost']
                cost_found = True
        
        if cost_found:
            print(f"✅ COST DATA SUCCESSFULLY EXTRACTED!")
            print(f"   Direct OpenRouter cost: ${cost_value}")
            print(f"   OpenRouter DOES provide cost data")
            print(f"   Problem: Pydantic AI doesn't preserve this data")
        else:
            print(f"❌ COST DATA NOT FOUND")
            print(f"   Either OpenRouter doesn't provide cost data")
            print(f"   Or it's in a different location than expected")
        
        print_section("RECOMMENDATION")
        
        if cost_found:
            print("🎯 SOLUTION APPROACH:")
            print("   1. Pydantic AI abstracts away cost data")
            print("   2. Need hybrid approach: Pydantic AI for features + direct API for costs")
            print("   3. Or: Use alternative LLM library that preserves raw responses")
            print("   4. Or: Patch Pydantic AI to preserve raw response data")
        else:
            print("⚠️ INVESTIGATION NEEDED:")
            print("   - Check OpenRouter documentation for cost data location")
            print("   - Verify API key permissions for cost data access")
            print("   - Test with different models or request parameters")
        
    except Exception as e:
        print(f"❌ Direct API call failed: {e}")
        import traceback
        traceback.print_exc()
    
    print_section("TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_direct_openrouter())
