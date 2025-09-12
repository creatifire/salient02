#!/usr/bin/env python3
"""
Side-by-side comparison: Pydantic AI v3 vs Our Custom Solution
"""

import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file at project root
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir.parent / ".env")

async def test_custom_solution():
    """Test our proven custom OpenAI SDK approach."""
    print("🔧 CUSTOM SOLUTION TEST")
    print("-" * 30)
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ No API key")
        return None
        
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[{
                "role": "user", 
                "content": "Generate a short, friendly message about the importance of being on time."
            }],
            extra_body={"usage": {"include": True}}  # 🔑 CRITICAL!
        )
        
        content = response.choices[0].message.content
        real_cost = getattr(response.usage, 'cost', 0.0)
        tokens = response.usage.total_tokens
        
        print(f"✅ Response: '{content[:50]}...'")
        print(f"💵 Real Cost: ${real_cost}")
        print(f"🔢 Tokens: {tokens}")
        print(f"📊 Has cost field: {hasattr(response.usage, 'cost')}")
        
        return real_cost
        
    except Exception as e:
        print(f"❌ Custom solution failed: {e}")
        return None

async def test_pydantic_ai_v3():
    """Test the user's v3 Pydantic AI approach."""
    print("\n🦜 PYDANTIC AI V3 TEST")
    print("-" * 30)
    
    # Import the function from v3 code
    import sys
    sys.path.append('.')
    
    try:
        from test_user_sample_code_v3 import retrieve_cost_data
        
        result = await retrieve_cost_data(
            prompt="Generate a short, friendly message about the importance of being on time.",
            model_name="deepseek/deepseek-chat-v3.1"
        )
        
        if result:
            print(f"✅ Response: '{result.output[:50]}...'")
            print(f"💵 Reported Cost: ${result.usage.cost}")
            print(f"🔢 Tokens: {result.usage.total_tokens}")
            print(f"📊 Has cost field: {result.usage.cost is not None}")
            return result.usage.cost
        else:
            print("❌ Pydantic AI v3 failed")
            return None
            
    except Exception as e:
        print(f"❌ Pydantic AI v3 failed: {e}")
        return None

async def main():
    """Compare both approaches side by side."""
    
    print("🔍 SIDE-BY-SIDE COST TRACKING COMPARISON")
    print("="*60)
    
    custom_cost = await test_custom_solution()
    pydantic_cost = await test_pydantic_ai_v3()
    
    print(f"\n📊 COMPARISON RESULTS:")
    print("-" * 30)
    print(f"Custom Solution Cost:   ${custom_cost}")
    print(f"Pydantic AI v3 Cost:    ${pydantic_cost}")
    
    if custom_cost and pydantic_cost:
        if abs(custom_cost - pydantic_cost) < 0.000001:  # Very close
            print("🎯 ACCURACY: Perfect match!")
            print("🚨 BREAKTHROUGH: Pydantic AI v3 might be getting real cost data!")
        else:
            difference = abs(custom_cost - pydantic_cost)
            print(f"⚠️  ACCURACY: Difference of ${difference}")
            if pydantic_cost == 0.0:
                print("❌ Pydantic AI has no cost data")
            else:
                accuracy = (min(custom_cost, pydantic_cost) / max(custom_cost, pydantic_cost)) * 100
                print(f"📈 Accuracy: {accuracy:.1f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if pydantic_cost and pydantic_cost > 0:
        print("🚨 NEED TO INVESTIGATE: Pydantic AI v3 is showing cost data!")
        print("❓ Is this real OpenRouter data or calculated elsewhere?")
    else:
        print("✅ CONFIRMED: Our custom solution is still the only working approach")

if __name__ == "__main__":
    asyncio.run(main())
