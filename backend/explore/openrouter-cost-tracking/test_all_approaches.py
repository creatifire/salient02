#!/usr/bin/env python3
"""
Comprehensive test of all cost tracking approaches.

This script tests all three approaches and provides a final recommendation
for implementing OpenRouter cost tracking in our application.
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

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"🔬 {title}")
    print('='*80)

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'-'*60}")
    print(f"📋 {title}")
    print('-'*60)

async def main():
    """Run all approach tests and provide recommendations."""
    
    print_header("OPENROUTER COST TRACKING - COMPREHENSIVE SOLUTION TEST")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("Please set the API key and run again.")
        return
    
    print(f"✅ OpenRouter API Key: {api_key[:10]}...")
    
    results = {}
    
    # Test Approach 1: Pydantic AI with extra_body
    print_section("APPROACH 1: PYDANTIC AI + EXTRA_BODY")
    try:
        from test_approach_1_pydantic_extra_body import test_approach_1
        results['approach_1'] = await test_approach_1()
    except Exception as e:
        print(f"❌ Approach 1 test failed to run: {e}")
        results['approach_1'] = False
    
    # Test Approach 2: OpenAI SDK Direct  
    print_section("APPROACH 2: OPENAI SDK DIRECT")
    try:
        from test_approach_2_openai_sdk_direct import test_approach_2
        results['approach_2'] = await test_approach_2()
    except Exception as e:
        print(f"❌ Approach 2 test failed to run: {e}")
        results['approach_2'] = False
    
    # Test Approach 3: Our OpenRouter Client
    print_section("APPROACH 3: FIXED OPENROUTER_CLIENT.PY")
    try:
        from test_approach_3_openrouter_client import test_approach_3
        results['approach_3'] = await test_approach_3()
    except Exception as e:
        print(f"❌ Approach 3 test failed to run: {e}")
        results['approach_3'] = False
    
    # Analysis and Recommendations
    print_header("ANALYSIS AND RECOMMENDATIONS")
    
    successful_approaches = [k for k, v in results.items() if v]
    failed_approaches = [k for k, v in results.items() if not v]
    
    print(f"📊 TEST RESULTS:")
    for approach, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  - {approach.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    
    if results.get('approach_1'):
        print("🏆 RECOMMENDED: Use Approach 1 (Pydantic AI + extra_body)")
        print("   ✅ Keeps all Pydantic AI benefits")
        print("   ✅ Gets real OpenRouter cost data")
        print("   ✅ Single API call")
        recommendation = "approach_1"
        
    elif results.get('approach_2'):
        print("🥈 RECOMMENDED: Use Approach 2 (OpenAI SDK Direct)")  
        print("   ✅ Reliable cost data access")
        print("   ✅ Full control over API request")
        print("   ⚠️  Loses Pydantic AI advanced features")
        recommendation = "approach_2"
        
    elif results.get('approach_3'):
        print("🥉 RECOMMENDED: Use Approach 3 (Fixed OpenRouter Client)")
        print("   ✅ Guaranteed cost tracking")
        print("   ✅ Custom implementation under our control")
        print("   ⚠️  Simpler than Pydantic AI or OpenAI SDK")
        recommendation = "approach_3"
        
    else:
        print("❌ NO WORKING SOLUTION FOUND")
        print("   All approaches failed to retrieve cost data")
        print("   Need to investigate OpenRouter API or account settings")
        recommendation = "investigate"
    
    # Implementation guidance
    if recommendation != "investigate":
        print(f"\n🔧 IMPLEMENTATION NEXT STEPS:")
        
        if recommendation == "approach_1":
            print("1. Update simple_chat.py to use extra_body parameter")
            print("2. Test cost tracking in development")
            print("3. Validate database storage of real costs")
            
        elif recommendation == "approach_2":
            print("1. Replace Pydantic AI agent.run() with OpenAI SDK call")
            print("2. Configure client with OpenRouter endpoint")
            print("3. Pass usage parameter in extra_body")
            print("4. Handle response format changes in application")
            
        elif recommendation == "approach_3":
            print("1. Replace Pydantic AI call with openrouter_client.chat_completion_with_usage()")
            print("2. Update message handling to work with simpler response format")
            print("3. Ensure conversation history integration still works")
        
        print(f"\n4. Test with real API key")
        print(f"5. Verify costs appear correctly in llm_requests table")
        print(f"6. Commit the working solution")
    
    print_header("COMPREHENSIVE TEST COMPLETE")
    
    return recommendation

if __name__ == "__main__":
    recommendation = asyncio.run(main())
    print(f"\n🎯 FINAL RECOMMENDATION: {recommendation.upper()}")
    
    if recommendation != "investigate":
        print("✅ Ready to implement the working solution!")
