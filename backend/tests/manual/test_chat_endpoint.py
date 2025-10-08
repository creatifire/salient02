"""
Manual test for the multi-tenant chat endpoint.

This script tests the /accounts/{account}/agents/{instance}/chat endpoint
by sending a real request and printing the response.

Prerequisites:
- FastAPI server must be running (uvicorn app.main:app --reload)
- Database must be initialized with seed data
- OpenRouter API key must be configured in .env

Usage:
    python backend/tests/manual/test_chat_endpoint.py

Expected behavior:
- Endpoint responds with 200 status
- Response contains 'response', 'usage', and 'model' fields
- LLM responds with information about itself and cutoff date
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


def test_simple_chat_endpoint():
    """
    Test the default_account/simple_chat1 endpoint.
    
    Sends a question about the LLM's identity and cutoff date,
    then prints the full response for manual verification.
    """
    print("=" * 80)
    print("MANUAL TEST: Multi-Tenant Chat Endpoint")
    print("=" * 80)
    print()
    
    # Configuration
    base_url = "http://localhost:8000"
    account = "default_account"
    agent_instance = "simple_chat1"
    endpoint = f"{base_url}/accounts/{account}/agents/{agent_instance}/chat"
    
    # Test message
    message = "What LLM are you and what is your knowledge cutoff date?"
    
    print(f"📍 Endpoint: {endpoint}")
    print(f"💬 Message: {message}")
    print()
    
    # Send request
    print("⏳ Sending request...")
    start_time = datetime.now()
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                endpoint,
                json={"message": message}
            )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Response received in {duration:.2f}s")
        print()
        
        # Print status
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        # Parse and print response
        if response.status_code == 200:
            data = response.json()
            
            print("=" * 80)
            print("RESPONSE DATA")
            print("=" * 80)
            print()
            
            # Print LLM response
            if "response" in data:
                print("🤖 LLM Response:")
                print("-" * 80)
                print(data["response"])
                print("-" * 80)
                print()
            
            # Print model information
            if "model" in data:
                print(f"📦 Model: {data['model']}")
                print()
            
            # Print usage statistics
            if "usage" in data and data["usage"]:
                print("📈 Token Usage:")
                usage = data["usage"]
                for key, value in usage.items():
                    print(f"  - {key}: {value}")
                print()
            
            # Print full JSON for debugging
            print("=" * 80)
            print("FULL JSON RESPONSE")
            print("=" * 80)
            print(json.dumps(data, indent=2))
            print()
            
            # Verify expected fields
            print("=" * 80)
            print("VALIDATION")
            print("=" * 80)
            required_fields = ["response", "usage", "model"]
            all_present = True
            for field in required_fields:
                present = field in data
                status = "✅" if present else "❌"
                print(f"{status} '{field}' field present: {present}")
                if not present:
                    all_present = False
            
            print()
            if all_present:
                print("✅ All required fields present")
            else:
                print("❌ Some required fields missing")
            
            return True
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print()
            print("Response body:")
            print(response.text)
            return False
            
    except httpx.ConnectError as e:
        print(f"❌ Connection error: {e}")
        print()
        print("💡 Make sure the FastAPI server is running:")
        print("   cd backend && uvicorn app.main:app --reload")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = test_simple_chat_endpoint()
    print()
    print("=" * 80)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("=" * 80)
    print()
    
    sys.exit(0 if success else 1)

