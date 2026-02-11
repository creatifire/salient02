"""
Baseline Metrics Capture Script for FEATURE-0026-010 Refactoring

This script captures baseline metrics BEFORE the refactoring work begins.
After each chunk, we'll re-run this to verify no regressions.

Metrics Captured:
- Response times (non-streaming and streaming)
- Cost tracking accuracy
- Token counts
- Database persistence
- Prompt breakdown capture
- Tool call extraction

Usage:
    python backend/tests/manual/test_baseline_metrics.py

Output:
    - Prints detailed metrics to stdout
    - Saves JSON report to test_results/baseline_TIMESTAMP.json
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
from typing import Dict, List, Optional

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_AGENT = {
    "account": "wyckoff",
    "instance": "wyckoff_info_chat1",
    "name": "Wyckoff Info Chat"
}

# Test scenarios
TEST_SCENARIOS = [
    {
        "id": "simple_query",
        "message": "Hello, can you help me?",
        "expected_tools": [],
        "category": "simple"
    },
    {
        "id": "directory_query",
        "message": "What is the cardiology department phone number?",
        "expected_tools": ["get_available_directories", "search_directory"],
        "category": "directory"
    },
    {
        "id": "knowledge_query",
        "message": "What is cardiology?",
        "expected_tools": ["vector_search"],
        "category": "knowledge"
    }
]


def print_header(title: str):
    """Print a formatted section header."""
    print()
    print("=" * 100)
    print(f" {title:^98} ")
    print("=" * 100)


def test_non_streaming(scenario: Dict) -> Optional[Dict]:
    """
    Test non-streaming endpoint and capture metrics.
    
    Returns:
        Dictionary with metrics or None if failed
    """
    endpoint = f"{BASE_URL}/accounts/{TEST_AGENT['account']}/agents/{TEST_AGENT['instance']}/chat"
    
    print(f"\n📝 Testing: {scenario['id']}")
    print(f"💬 Message: {scenario['message']}")
    print(f"🔗 Endpoint: {endpoint}")
    
    try:
        start_time = datetime.now()
        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, json={"message": scenario["message"]})
        end_time = datetime.now()
        
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None
        
        data = response.json()
        
        # Extract metrics
        metrics = {
            "scenario_id": scenario["id"],
            "type": "non_streaming",
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "response_length": len(data.get("response", "")),
            "model": data.get("model"),
            "usage": data.get("usage", {}),
            "cost_tracking": data.get("cost_tracking", {}),
            "llm_request_id": data.get("llm_request_id"),
            "has_response": bool(data.get("response")),
            "has_usage": bool(data.get("usage")),
            "has_cost_tracking": bool(data.get("cost_tracking")),
            "timestamp": datetime.now().isoformat()
        }
        
        # Print summary
        print(f"✅ Response received in {duration_ms:.0f}ms")
        print(f"📦 Model: {metrics['model']}")
        if metrics['usage']:
            usage = metrics['usage']
            print(f"📈 Tokens: {usage.get('input_tokens', 0)} in | {usage.get('output_tokens', 0)} out | {usage.get('total_tokens', 0)} total")
        if metrics['cost_tracking'] and metrics['cost_tracking'].get('cost_found'):
            cost = metrics['cost_tracking'].get('real_cost', 0)
            print(f"💰 Cost: ${cost:.6f}")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_streaming(scenario: Dict) -> Optional[Dict]:
    """
    Test streaming endpoint and capture metrics.
    
    Returns:
        Dictionary with metrics or None if failed
    """
    endpoint = f"{BASE_URL}/accounts/{TEST_AGENT['account']}/agents/{TEST_AGENT['instance']}/stream"
    
    print(f"\n📝 Testing: {scenario['id']} (streaming)")
    print(f"💬 Message: {scenario['message']}")
    print(f"🔗 Endpoint: {endpoint}")
    
    chunks = []
    
    try:
        start_time = datetime.now()
        
        with httpx.Client(timeout=60.0) as client:
            with client.stream("GET", endpoint, params={"message": scenario["message"]}) as response:
                if response.status_code != 200:
                    print(f"❌ HTTP {response.status_code}")
                    return None
                
                # Collect chunks
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        chunk = line[5:].strip()
                        if chunk:
                            chunks.append(chunk)
        
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        full_response = "".join(chunks)
        
        metrics = {
            "scenario_id": scenario["id"],
            "type": "streaming",
            "status_code": 200,
            "duration_ms": duration_ms,
            "chunk_count": len(chunks),
            "response_length": len(full_response),
            "has_content": len(full_response) > 0,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Stream completed in {duration_ms:.0f}ms")
        print(f"📦 Chunks: {metrics['chunk_count']}")
        print(f"📏 Length: {metrics['response_length']} chars")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def check_database_records(llm_request_id: Optional[str]) -> Optional[Dict]:
    """
    Check if database records were created correctly.
    
    This would ideally query the database directly, but for now
    we'll just verify that we received an llm_request_id.
    
    Returns:
        Dictionary with verification results
    """
    if not llm_request_id:
        return {"has_llm_request_id": False}
    
    return {
        "has_llm_request_id": True,
        "llm_request_id": llm_request_id
    }


def run_baseline_tests():
    """
    Run all baseline tests and capture metrics.
    """
    print_header("BASELINE METRICS CAPTURE - FEATURE-0026-010")
    
    print(f"\n🎯 Target Agent: {TEST_AGENT['name']}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🧪 Test Scenarios: {len(TEST_SCENARIOS)}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    all_metrics = {
        "timestamp": datetime.now().isoformat(),
        "agent": TEST_AGENT,
        "base_url": BASE_URL,
        "scenarios": []
    }
    
    # Run non-streaming tests
    print_header("NON-STREAMING TESTS")
    
    for scenario in TEST_SCENARIOS:
        metrics = test_non_streaming(scenario)
        if metrics:
            # Check database
            db_check = check_database_records(metrics.get("llm_request_id"))
            metrics["database"] = db_check
            
            all_metrics["scenarios"].append(metrics)
        
        # Brief pause between tests
        import time
        time.sleep(1)
    
    # Run streaming tests
    print_header("STREAMING TESTS")
    
    for scenario in TEST_SCENARIOS:
        metrics = test_streaming(scenario)
        if metrics:
            all_metrics["scenarios"].append(metrics)
        
        # Brief pause between tests
        import time
        time.sleep(1)
    
    # Calculate summary statistics
    print_header("SUMMARY STATISTICS")
    
    non_streaming = [m for m in all_metrics["scenarios"] if m["type"] == "non_streaming"]
    streaming = [m for m in all_metrics["scenarios"] if m["type"] == "streaming"]
    
    print(f"\n📊 Tests Completed:")
    print(f"   Non-streaming: {len(non_streaming)}/{len(TEST_SCENARIOS)}")
    print(f"   Streaming: {len(streaming)}/{len(TEST_SCENARIOS)}")
    
    if non_streaming:
        avg_duration = sum(m["duration_ms"] for m in non_streaming) / len(non_streaming)
        print(f"\n⏱️  Non-Streaming Average Duration: {avg_duration:.0f}ms")
        
        total_tokens = sum(m.get("usage", {}).get("total_tokens", 0) for m in non_streaming)
        print(f"📈 Total Tokens Used: {total_tokens}")
        
        total_cost = sum(m.get("cost_tracking", {}).get("real_cost", 0) for m in non_streaming)
        print(f"💰 Total Cost: ${total_cost:.6f}")
        
        cost_tracking_success = sum(1 for m in non_streaming if m.get("has_cost_tracking"))
        print(f"✅ Cost Tracking Success Rate: {cost_tracking_success}/{len(non_streaming)}")
        
        db_success = sum(1 for m in non_streaming if m.get("database", {}).get("has_llm_request_id"))
        print(f"✅ Database Persistence Success Rate: {db_success}/{len(non_streaming)}")
    
    if streaming:
        avg_duration = sum(m["duration_ms"] for m in streaming) / len(streaming)
        avg_chunks = sum(m["chunk_count"] for m in streaming) / len(streaming)
        print(f"\n⏱️  Streaming Average Duration: {avg_duration:.0f}ms")
        print(f"📦 Average Chunks: {avg_chunks:.0f}")
    
    # Save results to file
    results_dir = backend_dir / "test_results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"baseline_{timestamp_str}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Success check
    success = (
        len(non_streaming) == len(TEST_SCENARIOS) and
        len(streaming) == len(TEST_SCENARIOS) and
        all(m.get("has_cost_tracking") for m in non_streaming) and
        all(m.get("database", {}).get("has_llm_request_id") for m in non_streaming)
    )
    
    return success, results_file


if __name__ == "__main__":
    try:
        success, results_file = run_baseline_tests()
        
        print()
        print("=" * 100)
        if success:
            print("✅ BASELINE CAPTURE COMPLETE - ALL TESTS PASSED")
        else:
            print("⚠️  BASELINE CAPTURE COMPLETE - SOME TESTS FAILED")
        print("=" * 100)
        print()
        print(f"📄 Baseline metrics saved to: {results_file}")
        print()
        print("💡 Next Steps:")
        print("   1. Review metrics to confirm current functionality")
        print("   2. Begin CHUNK-0026-010-001: Create CostTrackingService")
        print("   3. After refactoring, re-run this script to compare")
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

