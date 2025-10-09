"""
Manual test for the multi-tenant chat endpoint.

This script tests the /accounts/{account}/agents/{instance}/chat endpoint
by sending requests to all 3 configured agent instances and comparing responses.

Tests:
1. default_account/simple_chat1 (Kimi by Moonshot AI)
2. default_account/simple_chat2 (GPT OSS)
3. acme/acme_chat1 (Qwen VL)

Prerequisites:
- FastAPI server must be running (uvicorn app.main:app --reload)
- Database must be initialized with seed data
- OpenRouter API key must be configured in .env

Usage:
    python backend/tests/manual/test_chat_endpoint.py

Expected behavior:
- All endpoints respond with 200 status
- Each response contains 'response', 'usage', and 'model' fields
- Different LLMs provide different responses to the same question,
  identifying themselves and their knowledge cutoff dates correctly
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
import json
from datetime import datetime
from typing import Dict, Optional


# Define test configurations for all 3 agent instances
AGENT_INSTANCES = [
    {
        "account": "default_account",
        "instance": "simple_chat1",
        "name": "Simple Chat 1",
        "expected_model": "moonshotai/kimi"
    },
    {
        "account": "default_account",
        "instance": "simple_chat2",
        "name": "Simple Chat 2",
        "expected_model": "openai/gpt-oss"
    },
    {
        "account": "acme",
        "instance": "acme_chat1",
        "name": "ACME Chat 1",
        "expected_model": "qwen/qwen3"
    }
]


def test_endpoint(base_url: str, account: str, instance: str, message: str) -> Optional[Dict]:
    """
    Send a request to a specific endpoint and return the parsed response.
    
    Args:
        base_url: Base URL of the API server
        account: Account slug
        instance: Agent instance slug
        message: Message to send
        
    Returns:
        Dictionary with response data, or None if request failed
    """
    endpoint = f"{base_url}/accounts/{account}/agents/{instance}/chat"
    
    try:
        start_time = datetime.now()
        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, json={"message": message})
        duration = (end_time := datetime.now()) - start_time
        
        if response.status_code == 200:
            data = response.json()
            data["_meta"] = {
                "duration": duration.total_seconds(),
                "status_code": response.status_code,
                "endpoint": endpoint
            }
            return data
        else:
            return {
                "_meta": {
                    "duration": duration.total_seconds(),
                    "status_code": response.status_code,
                    "endpoint": endpoint,
                    "error": response.text
                }
            }
    except Exception as e:
        return {
            "_meta": {
                "endpoint": endpoint,
                "error": str(e)
            }
        }


def print_response_summary(config: Dict, result: Optional[Dict], index: int, total: int):
    """
    Print a nicely formatted summary of a single endpoint test.
    
    Args:
        config: Agent instance configuration
        result: Response data from the endpoint
        index: Current test number (1-based)
        total: Total number of tests
    """
    print()
    print("=" * 100)
    print(f"TEST {index}/{total}: {config['name']}")
    print(f"Account: {config['account']} | Instance: {config['instance']}")
    print("=" * 100)
    
    if not result or "_meta" not in result:
        print("❌ FAILED: No response received")
        return False
    
    meta = result["_meta"]
    endpoint = meta.get("endpoint", "unknown")
    
    # Print endpoint and timing
    print(f"\n📍 Endpoint: {endpoint}")
    if "duration" in meta:
        print(f"⏱️  Duration: {meta['duration']:.2f}s")
    
    # Check for errors
    if "error" in meta:
        print(f"\n❌ ERROR: {meta['error']}")
        if "status_code" in meta:
            print(f"📊 Status Code: {meta['status_code']}")
        return False
    
    # Success case - print response details
    status_code = meta.get("status_code", "unknown")
    print(f"📊 Status Code: {status_code}")
    
    # Print LLM response (truncated if too long)
    if "response" in result:
        llm_response = result["response"]
        print(f"\n🤖 LLM Response:")
        print("─" * 100)
        # Truncate long responses for readability
        if len(llm_response) > 300:
            print(llm_response[:300] + "...")
        else:
            print(llm_response)
        print("─" * 100)
    
    # Print model and usage in a compact format
    print()
    if "model" in result:
        print(f"📦 Model: {result['model']}")
    
    if "usage" in result and result["usage"]:
        usage = result["usage"]
        print(f"📈 Tokens: {usage.get('input_tokens', 0)} in | {usage.get('output_tokens', 0)} out | {usage.get('total_tokens', 0)} total")
        if "requests" in usage:
            print(f"📊 Requests: {usage['requests']}")
    
    if "cost_tracking" in result and result["cost_tracking"]:
        cost = result["cost_tracking"]
        if cost.get("cost_found"):
            real_cost = cost.get("real_cost", 0)
            print(f"💰 Cost: ${real_cost:.6f}")
    
    # Validation
    required_fields = ["response", "usage", "model"]
    missing = [f for f in required_fields if f not in result]
    
    if not missing:
        print(f"\n✅ All required fields present")
        return True
    else:
        print(f"\n⚠️  Missing fields: {', '.join(missing)}")
        return False


def run_all_tests():
    """
    Test all configured agent endpoints with the same question.
    """
    print()
    print("=" * 100)
    print(" " * 30 + "MULTI-TENANT CHAT ENDPOINT TEST")
    print("=" * 100)
    
    base_url = "http://localhost:8000"
    message = "What LLM are you and what is your knowledge cutoff date?"
    
    print(f"\n📝 Test Message: {message}")
    print(f"🌐 Base URL: {base_url}")
    print(f"🔢 Testing {len(AGENT_INSTANCES)} agent instances...")
    
    # Run tests for all endpoints
    results = []
    for i, config in enumerate(AGENT_INSTANCES, 1):
        result = test_endpoint(base_url, config["account"], config["instance"], message)
        results.append((config, result))
        success = print_response_summary(config, result, i, len(AGENT_INSTANCES))
        
        # Brief pause between requests to avoid rate limiting
        if i < len(AGENT_INSTANCES):
            import time
            time.sleep(0.5)
    
    # Print summary comparison
    print()
    print("=" * 100)
    print(" " * 40 + "SUMMARY COMPARISON")
    print("=" * 100)
    print()
    
    # Table header
    print(f"{'Agent Instance':<30} {'LLM Identified':<20} {'Tokens':<12} {'Cost':<12} {'Status'}")
    print("─" * 100)
    
    # Expected LLM indicators for each instance
    llm_indicators = {
        "default_account/simple_chat1": ["Kimi", "April 2025"],
        "default_account/simple_chat2": ["ChatGPT", "GPT", "June 2024"],
        "acme/acme_chat1": ["Qwen", "October 2024"]
    }
    
    all_passed = True
    for config, result in results:
        agent_name = f"{config['account']}/{config['instance']}"
        
        if result and "_meta" in result and "error" not in result["_meta"]:
            model = result.get("model", "unknown")
            usage = result.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            cost_tracking = result.get("cost_tracking", {})
            cost = cost_tracking.get("real_cost", 0) if cost_tracking.get("cost_found") else 0
            response_text = result.get("response", "")
            
            # VALIDATE: Check for LLM indicators in response text
            expected_indicators = llm_indicators.get(agent_name, [])
            found_indicators = [ind for ind in expected_indicators if ind in response_text]
            llm_identified_str = "✅" if len(found_indicators) >= 1 else "❌"
            llm_name_display = found_indicators[0] if found_indicators else "Unknown"
            
            # VALIDATE: Check if the returned model matches the expected model
            expected_model = config.get("expected_model", "")
            model_correct = expected_model.lower() in model.lower() if expected_model else True
            
            # VALIDATE: Check if all required fields are present
            required_fields = ["response", "usage", "model"]
            all_fields_present = all(f in result for f in required_fields)
            
            # VALIDATE: Check if we got actual content
            has_content = bool(response_text.strip())
            
            # VALIDATE: Check if LLM identified itself
            has_llm_match = len(found_indicators) >= 1
            
            # Determine status based on validations
            if model_correct and all_fields_present and has_content and has_llm_match:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
                all_passed = False
                # Add failure reason
                reasons = []
                if not model_correct:
                    reasons.append(f"wrong_model")
                if not all_fields_present:
                    reasons.append("missing_fields")
                if not has_content:
                    reasons.append("no_content")
                if not has_llm_match:
                    reasons.append("llm_not_identified")
                status += f" ({', '.join(reasons)})"
        else:
            llm_identified_str = "❌"
            llm_name_display = "N/A"
            total_tokens = 0
            cost = 0
            status = "❌ FAIL (no_response)"
            all_passed = False
        
        print(f"{agent_name:<30} {llm_identified_str} {llm_name_display:<17} {total_tokens:<12} ${cost:<11.6f} {status}")
    
    print()
    print("=" * 100)
    
    return all_passed


if __name__ == "__main__":
    try:
        success = run_all_tests()
        
        print()
        if success:
            print("✅ ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
        print()
        
        sys.exit(0 if success else 1)
        
    except httpx.ConnectError:
        print()
        print("=" * 100)
        print("❌ CONNECTION ERROR")
        print("=" * 100)
        print()
        print("💡 Make sure the FastAPI server is running:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")
        print()
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 100)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("=" * 100)
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

