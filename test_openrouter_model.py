#!/usr/bin/env python3
"""
Test script for OpenRouterModel cost tracking implementation.
"""

import asyncio
import sys
import uuid

async def test_simple_chat():
    from app.agents.simple_chat import simple_chat
    
    # Generate a test session ID
    session_id = str(uuid.uuid4())
    print(f"🧪 Testing OpenRouterModel with session: {session_id[:8]}...")
    
    try:
        # Test the agent
        result = await simple_chat("What model are you and what is 2+2?", session_id)
        
        print("✅ Chat execution successful!")
        print(f"Response preview: {result['response'][:100]}...")
        print(f"Method: {result['cost_tracking']['method']}")
        print(f"Cost found: {result['cost_tracking']['cost_found']}")
        print(f"Real cost: ${result['cost_tracking']['real_cost']}")
        print(f"Usage: {result['usage'].input_tokens} input, {result['usage'].output_tokens} output")
        
        # Test cost tracking specifically
        if result['cost_tracking']['real_cost'] > 0:
            print("🎯 SUCCESS: Real cost data extracted!")
        else:
            print("⚠️  WARNING: No cost data found")
            
        return result
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_simple_chat())
