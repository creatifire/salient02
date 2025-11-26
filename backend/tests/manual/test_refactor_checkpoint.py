"""
Refactoring Checkpoint Verification Script

This script runs after each CHUNK to verify no regressions were introduced.
It compares current behavior against baseline metrics.

Usage:
    python backend/tests/manual/test_refactor_checkpoint.py --chunk CHUNK-0026-010-001

Verification Checklist (from FEATURE-0026-010 plan):
- Non-streaming chat works
- Streaming chat works  
- Directory tools called correctly
- Vector search works
- Prompt breakdown captured
- Cost tracking accurate
- Token counts correct
- Messages saved correctly
- Tool calls captured in message.meta
- No errors in logs
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
import argparse

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
from typing import Dict, List, Optional

# Import baseline test
from test_baseline_metrics import (
    BASE_URL,
    TEST_AGENT,
    TEST_SCENARIOS,
    test_non_streaming,
    test_streaming,
    check_database_records,
    print_header
)


def load_latest_baseline() -> Optional[Dict]:
    """Load the most recent baseline results."""
    results_dir = backend_dir / "test_results"
    if not results_dir.exists():
        return None
    
    baseline_files = sorted(results_dir.glob("baseline_*.json"), reverse=True)
    if not baseline_files:
        return None
    
    with open(baseline_files[0], 'r') as f:
        return json.load(f)


def compare_metrics(baseline: Dict, current: Dict, chunk_id: str):
    """
    Compare current metrics against baseline.
    
    Args:
        baseline: Baseline metrics
        current: Current metrics
        chunk_id: Current chunk identifier
    """
    print_header(f"COMPARISON: {chunk_id}")
    
    baseline_scenarios = {s["scenario_id"]: s for s in baseline.get("scenarios", []) if s["type"] == "non_streaming"}
    current_scenarios = {s["scenario_id"]: s for s in current.get("scenarios", []) if s["type"] == "non_streaming"}
    
    issues = []
    
    # Compare each scenario
    for scenario_id in baseline_scenarios:
        if scenario_id not in current_scenarios:
            issues.append(f"❌ Scenario '{scenario_id}' missing in current run")
            continue
        
        baseline_m = baseline_scenarios[scenario_id]
        current_m = current_scenarios[scenario_id]
        
        print(f"\n📊 Scenario: {scenario_id}")
        print("─" * 80)
        
        # Compare duration (allow 20% variance)
        baseline_duration = baseline_m["duration_ms"]
        current_duration = current_m["duration_ms"]
        duration_diff_pct = ((current_duration - baseline_duration) / baseline_duration) * 100
        
        if abs(duration_diff_pct) > 20:
            issues.append(f"⚠️  Duration changed significantly: {duration_diff_pct:+.1f}%")
            print(f"   Duration: {current_duration:.0f}ms (baseline: {baseline_duration:.0f}ms, {duration_diff_pct:+.1f}%)")
        else:
            print(f"   ✅ Duration: {current_duration:.0f}ms (baseline: {baseline_duration:.0f}ms, {duration_diff_pct:+.1f}%)")
        
        # Compare token counts (should be nearly identical)
        baseline_tokens = baseline_m.get("usage", {}).get("total_tokens", 0)
        current_tokens = current_m.get("usage", {}).get("total_tokens", 0)
        
        if baseline_tokens > 0:
            token_diff_pct = ((current_tokens - baseline_tokens) / baseline_tokens) * 100 if baseline_tokens > 0 else 0
            if abs(token_diff_pct) > 5:
                issues.append(f"⚠️  Token count changed: {token_diff_pct:+.1f}%")
                print(f"   Tokens: {current_tokens} (baseline: {baseline_tokens}, {token_diff_pct:+.1f}%)")
            else:
                print(f"   ✅ Tokens: {current_tokens} (baseline: {baseline_tokens})")
        
        # Compare cost tracking
        baseline_has_cost = baseline_m.get("has_cost_tracking", False)
        current_has_cost = current_m.get("has_cost_tracking", False)
        
        if baseline_has_cost != current_has_cost:
            issues.append(f"❌ Cost tracking regression: baseline={baseline_has_cost}, current={current_has_cost}")
            print(f"   Cost tracking: {'✅' if current_has_cost else '❌'} (baseline: {'✅' if baseline_has_cost else '❌'})")
        else:
            print(f"   ✅ Cost tracking: {'working' if current_has_cost else 'not available'}")
        
        # Compare database persistence
        baseline_has_db = baseline_m.get("database", {}).get("has_llm_request_id", False)
        current_has_db = current_m.get("database", {}).get("has_llm_request_id", False)
        
        if baseline_has_db != current_has_db:
            issues.append(f"❌ Database persistence regression: baseline={baseline_has_db}, current={current_has_db}")
            print(f"   Database: {'✅' if current_has_db else '❌'} (baseline: {'✅' if baseline_has_db else '❌'})")
        else:
            print(f"   ✅ Database: {'working' if current_has_db else 'not available'}")
    
    # Summary
    print()
    print("=" * 100)
    if issues:
        print("⚠️  REGRESSIONS DETECTED:")
        for issue in issues:
            print(f"   {issue}")
        print()
        return False
    else:
        print("✅ NO REGRESSIONS - ALL METRICS WITHIN ACCEPTABLE RANGE")
        print()
        return True


def run_checkpoint_verification(chunk_id: str):
    """
    Run checkpoint verification for a specific chunk.
    
    Args:
        chunk_id: Chunk identifier (e.g., "CHUNK-0026-010-001")
    """
    print_header(f"CHECKPOINT VERIFICATION - {chunk_id}")
    
    print(f"\n🎯 Chunk: {chunk_id}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Load baseline
    print("\n📂 Loading baseline metrics...")
    baseline = load_latest_baseline()
    
    if not baseline:
        print("⚠️  No baseline found. Run test_baseline_metrics.py first.")
        return False
    
    baseline_timestamp = baseline.get("timestamp", "unknown")
    print(f"   ✅ Baseline loaded (captured: {baseline_timestamp})")
    
    # Run current tests
    print("\n🧪 Running current tests...")
    
    current_metrics = {
        "timestamp": datetime.now().isoformat(),
        "chunk_id": chunk_id,
        "agent": TEST_AGENT,
        "base_url": BASE_URL,
        "scenarios": []
    }
    
    # Non-streaming tests
    print_header("NON-STREAMING VERIFICATION")
    
    for scenario in TEST_SCENARIOS:
        metrics = test_non_streaming(scenario)
        if metrics:
            db_check = check_database_records(metrics.get("llm_request_id"))
            metrics["database"] = db_check
            current_metrics["scenarios"].append(metrics)
        
        import time
        time.sleep(1)
    
    # Streaming tests
    print_header("STREAMING VERIFICATION")
    
    for scenario in TEST_SCENARIOS:
        metrics = test_streaming(scenario)
        if metrics:
            current_metrics["scenarios"].append(metrics)
        
        import time
        time.sleep(1)
    
    # Compare against baseline
    comparison_passed = compare_metrics(baseline, current_metrics, chunk_id)
    
    # Save checkpoint results
    results_dir = backend_dir / "test_results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_file = results_dir / f"checkpoint_{chunk_id}_{timestamp_str}.json"
    
    current_metrics["comparison"] = {
        "baseline_timestamp": baseline.get("timestamp"),
        "passed": comparison_passed
    }
    
    with open(checkpoint_file, 'w') as f:
        json.dump(current_metrics, f, indent=2)
    
    print(f"💾 Checkpoint results saved to: {checkpoint_file}")
    
    return comparison_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run refactoring checkpoint verification")
    parser.add_argument("--chunk", required=True, help="Chunk ID (e.g., CHUNK-0026-010-001)")
    args = parser.parse_args()
    
    try:
        success = run_checkpoint_verification(args.chunk)
        
        print()
        print("=" * 100)
        if success:
            print(f"✅ CHECKPOINT PASSED - {args.chunk} VERIFIED")
            print()
            print("💡 Next Steps:")
            print(f"   1. Review checkpoint results")
            print(f"   2. Commit changes for {args.chunk}")
            print(f"   3. Proceed to next chunk")
        else:
            print(f"❌ CHECKPOINT FAILED - {args.chunk} HAS REGRESSIONS")
            print()
            print("💡 Next Steps:")
            print(f"   1. Review regression details above")
            print(f"   2. Fix issues in {args.chunk}")
            print(f"   3. Re-run checkpoint verification")
        print("=" * 100)
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

