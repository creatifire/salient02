"""
Manual test for the multi-tenant streaming endpoint.

This script tests the /accounts/{account}/agents/{instance}/stream endpoint
by connecting to all 3 configured agent instances and displaying real-time SSE streams.

Tests:
1. default_account/simple_chat1 (Kimi by Moonshot AI)
2. default_account/simple_chat2 (GPT OSS)
3. acme/acme_chat1 (Qwen VL)

Prerequisites:
- FastAPI server must be running (uvicorn app.main:app --reload)
- Database must be initialized with seed data
- OpenRouter API key must be configured in .env

Usage:
    python backend/tests/manual/test_streaming_endpoint.py

Expected behavior:
- All endpoints stream text chunks in real-time
- Each stream ends with a "done" event
- Messages are saved to database after streaming completes
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
from typing import Dict, Optional, List
import time


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


def test_streaming_endpoint(base_url: str, account: str, instance: str, message: str) -> Optional[Dict]:
    """
    Connect to a streaming endpoint and collect all SSE events.
    
    Args:
        base_url: Base URL of the API server
        account: Account slug
        instance: Agent instance slug
        message: Message to send
        
    Returns:
        Dictionary with collected chunks and metadata, or None if request failed
    """
    endpoint = f"{base_url}/accounts/{account}/agents/{instance}/stream?message={message}"
    
    chunks = []
    events = []
    completion_status = "unknown"
    error_message = None
    
    print(f"\n🔗 Connecting to: {endpoint}")
    print("📡 Streaming chunks:")
    print("─" * 80)
    
    try:
        start_time = datetime.now()
        
        with httpx.Client(timeout=60.0) as client:
            with client.stream("GET", endpoint) as response:
                if response.status_code != 200:
                    return {
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code,
                        "endpoint": endpoint
                    }
                
                # Parse SSE events
                current_event = None
                for line in response.iter_lines():
                    if not line:
                        # Empty line resets state in SSE
                        continue
                    
                    # SSE format: "event: <type>" or "data: <content>"
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data = line[5:].strip()
                        
                        # Process based on current event type
                        if current_event == "message":
                            # Print chunk in real-time (without newline)
                            print(data, end="", flush=True)
                            chunks.append(data)
                            events.append({"event": current_event, "data": data})
                        elif current_event == "done":
                            completion_status = "complete"
                            print()  # New line after stream ends
                            events.append({"event": current_event, "data": data})
                        elif current_event == "error":
                            completion_status = "error"
                            try:
                                error_data = json.loads(data)
                                error_message = error_data.get("message", data)
                            except:
                                error_message = data
                            events.append({"event": current_event, "data": data})
                        elif current_event:
                            # Unknown event type, but still track it
                            events.append({"event": current_event, "data": data})
                        
                        current_event = None
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("─" * 80)
        
        # Collect full response
        full_response = "".join(chunks)
        
        return {
            "full_response": full_response,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "events": events,
            "completion_status": completion_status,
            "error_message": error_message,
            "duration": duration,
            "endpoint": endpoint,
            "status_code": 200
        }
        
    except Exception as e:
        print()
        print("─" * 80)
        return {
            "error": str(e),
            "endpoint": endpoint
        }


def print_stream_summary(config: Dict, result: Optional[Dict], index: int, total: int):
    """
    Print a nicely formatted summary of a streaming test.
    
    Args:
        config: Agent instance configuration
        result: Response data from the streaming endpoint
        index: Current test number (1-based)
        total: Total number of tests
    """
    print()
    print("=" * 100)
    print(f"TEST {index}/{total}: {config['name']}")
    print(f"Account: {config['account']} | Instance: {config['instance']}")
    print("=" * 100)
    
    if not result:
        print("❌ FAILED: No response received")
        return False
    
    # Check for errors
    if "error" in result:
        print(f"\n❌ ERROR: {result['error']}")
        if "status_code" in result:
            print(f"📊 Status Code: {result['status_code']}")
        return False
    
    # Success case - print streaming details
    print(f"\n⏱️  Duration: {result.get('duration', 0):.2f}s")
    print(f"📊 Status: {result.get('completion_status', 'unknown')}")
    print(f"📦 Chunks Received: {result.get('chunk_count', 0)}")
    print(f"📏 Response Length: {len(result.get('full_response', ''))} characters")
    
    # Print response preview (first 200 chars)
    full_response = result.get('full_response', '')
    if full_response:
        print(f"\n🤖 Response Preview:")
        print("─" * 100)
        preview = full_response[:200] + "..." if len(full_response) > 200 else full_response
        print(preview)
        print("─" * 100)
    
    # Debug: Show event summary
    events = result.get('events', [])
    event_counts = {}
    for event in events:
        event_type = event.get('event', 'unknown')
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    if event_counts:
        print(f"\n📊 Events received: ", end="")
        print(", ".join([f"{k}={v}" for k, v in event_counts.items()]))
    
    # Check for error message
    if result.get('error_message'):
        print(f"\n⚠️  Stream Error: {result['error_message']}")
        return False
    
    # Validation
    completion_status = result.get('completion_status')
    has_content = len(full_response) > 0
    has_chunks = result.get('chunk_count', 0) > 0
    
    if completion_status == "complete" and has_content and has_chunks:
        print(f"\n✅ Stream completed successfully")
        return True
    else:
        reasons = []
        if completion_status != "complete":
            reasons.append(f"status={completion_status}")
        if not has_content:
            reasons.append("no_content")
        if not has_chunks:
            reasons.append("no_chunks")
        print(f"\n⚠️  Stream incomplete: {', '.join(reasons)}")
        return False


def verify_database_persistence(base_url: str):
    """
    Verify that streaming messages were saved to the database.
    
    This is a simple check - in production you'd query the database directly.
    For now, we just wait a bit to allow async saves to complete.
    """
    print()
    print("=" * 100)
    print(" " * 35 + "DATABASE PERSISTENCE CHECK")
    print("=" * 100)
    print()
    print("⏳ Waiting 2 seconds for async database saves to complete...")
    time.sleep(2)
    print("✅ Messages should now be persisted to database")
    print()
    print("💡 To verify:")
    print("   1. Check the sessions table for new sessions")
    print("   2. Check the messages table for user and assistant messages")
    print("   3. Check the llm_requests table for cost tracking with completion_status='complete'")
    print()


def run_all_tests():
    """
    Test all configured streaming endpoints with the same question.
    """
    print()
    print("=" * 100)
    print(" " * 27 + "MULTI-TENANT STREAMING ENDPOINT TEST")
    print("=" * 100)
    
    base_url = "http://localhost:8000"
    message = "What LLM are you and what is your knowledge cutoff date?"
    
    print(f"\n📝 Test Message: {message}")
    print(f"🌐 Base URL: {base_url}")
    print(f"🔢 Testing {len(AGENT_INSTANCES)} agent instances with SSE streaming...")
    
    # Run tests for all endpoints
    results = []
    for i, config in enumerate(AGENT_INSTANCES, 1):
        result = test_streaming_endpoint(base_url, config["account"], config["instance"], message)
        results.append((config, result))
        success = print_stream_summary(config, result, i, len(AGENT_INSTANCES))
        
        # Brief pause between requests to avoid rate limiting
        if i < len(AGENT_INSTANCES):
            print()
            print("⏸️  Waiting 1 second before next test...")
            time.sleep(1)
    
    # Print summary comparison
    print()
    print("=" * 100)
    print(" " * 40 + "SUMMARY COMPARISON")
    print("=" * 100)
    print()
    
    # Table header
    print(f"{'Agent Instance':<30} {'LLM Identified':<20} {'Chunks':<10} {'Length':<10} {'Status'}")
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
        
        if result and "error" not in result:
            chunk_count = result.get("chunk_count", 0)
            response_length = len(result.get("full_response", ""))
            duration = result.get("duration", 0)
            completion_status = result.get("completion_status", "unknown")
            full_response = result.get("full_response", "")
            
            # Check for LLM indicators
            expected_indicators = llm_indicators.get(agent_name, [])
            found_indicators = [ind for ind in expected_indicators if ind in full_response]
            llm_identified = "✅" if len(found_indicators) >= 1 else "❌"
            llm_name = found_indicators[0] if found_indicators else "Unknown"
            
            # Determine status
            has_llm_match = len(found_indicators) >= 1
            has_content = chunk_count > 0 and response_length > 0
            is_complete = completion_status == "complete"
            
            if is_complete and has_content and has_llm_match:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
                all_passed = False
                # Add failure reason
                reasons = []
                if not is_complete:
                    reasons.append(f"status={completion_status}")
                if not has_content:
                    reasons.append("no_content")
                if not has_llm_match:
                    reasons.append("wrong_llm")
                status += f" ({', '.join(reasons)})"
        else:
            llm_identified = "❌"
            llm_name = "N/A"
            chunk_count = 0
            response_length = 0
            duration = 0
            status = "❌ FAIL (error)"
            all_passed = False
        
        print(f"{agent_name:<30} {llm_identified} {llm_name:<17} {chunk_count:<10} {response_length:<10} {status}")
    
    print()
    print("=" * 100)
    
    # Verify database persistence
    verify_database_persistence(base_url)
    
    return all_passed


if __name__ == "__main__":
    try:
        success = run_all_tests()
        
        print()
        if success:
            print("✅ ALL STREAMING TESTS PASSED")
        else:
            print("❌ SOME STREAMING TESTS FAILED")
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
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 100)
        print("⚠️  TEST INTERRUPTED BY USER")
        print("=" * 100)
        print()
        sys.exit(130)
    except Exception as e:
        print()
        print("=" * 100)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("=" * 100)
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

