"""
Manual Test Script for Agent Instance Listing Endpoint.

Tests the GET /accounts/{account}/agents endpoint for retrieving agent instance metadata.

Usage:
    python backend/tests/manual/test_list_endpoint.py

Features:
    - Tests all configured accounts (default_account, acme)
    - Verifies response format and required fields
    - Tests error handling for invalid accounts
    - Validates instance data completeness
    - Summary table for quick verification
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"

# Account configurations to test
TEST_ACCOUNTS = [
    {
        "account": "default_account",
        "expected_instances": ["simple_chat1", "simple_chat2"],
        "expected_count": 2
    },
    {
        "account": "acme",
        "expected_instances": ["acme_chat1"],
        "expected_count": 1
    }
]

# Test cases
TEST_CASES = {
    "valid_accounts": TEST_ACCOUNTS,
    "invalid_account": "nonexistent_account_12345"
}


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_list_endpoint(base_url: str, account: str) -> Optional[Dict]:
    """
    Test GET /accounts/{account}/agents endpoint.
    
    Args:
        base_url: Base URL of the API server
        account: Account slug to test
        
    Returns:
        Dict with test results, or None if request fails
    """
    url = f"{base_url}/accounts/{account}/agents"
    
    try:
        response = requests.get(url, timeout=30)
        
        # Parse response
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"error": "Invalid JSON response", "text": response.text[:200]}
        
        return {
            "account": account,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_data": data,
            "error": None if response.status_code == 200 else data.get("detail", "Unknown error")
        }
        
    except requests.exceptions.ConnectionError as e:
        return {
            "account": account,
            "status_code": None,
            "success": False,
            "response_data": None,
            "error": f"Connection refused: {str(e)}"
        }
    except Exception as e:
        return {
            "account": account,
            "status_code": None,
            "success": False,
            "response_data": None,
            "error": f"Request failed: {str(e)}"
        }


def validate_response_structure(data: Dict) -> tuple[bool, List[str]]:
    """
    Validate the structure of a list response.
    
    Args:
        data: Response data dictionary
        
    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []
    
    # Check required top-level fields
    required_fields = ["account", "instances", "count"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
    
    # Validate instances array
    if "instances" in data:
        if not isinstance(data["instances"], list):
            errors.append("'instances' should be an array")
        else:
            # Validate each instance
            required_instance_fields = ["instance_slug", "agent_type", "display_name", "last_used_at"]
            for idx, instance in enumerate(data["instances"]):
                if not isinstance(instance, dict):
                    errors.append(f"Instance {idx} is not an object")
                    continue
                
                for field in required_instance_fields:
                    if field not in instance:
                        errors.append(f"Instance {idx} missing field: '{field}'")
    
    # Validate count matches array length
    if "count" in data and "instances" in data and isinstance(data["instances"], list):
        if data["count"] != len(data["instances"]):
            errors.append(f"Count mismatch: count={data['count']}, array_length={len(data['instances'])}")
    
    return (len(errors) == 0, errors)


def validate_expected_instances(data: Dict, expected_instances: List[str]) -> tuple[bool, List[str]]:
    """
    Validate that expected instances are present.
    
    Args:
        data: Response data dictionary
        expected_instances: List of expected instance slugs
        
    Returns:
        Tuple of (all_found, missing_instances)
    """
    if "instances" not in data:
        return (False, expected_instances)
    
    actual_slugs = [inst["instance_slug"] for inst in data["instances"] if isinstance(inst, dict)]
    missing = [slug for slug in expected_instances if slug not in actual_slugs]
    
    return (len(missing) == 0, missing)


# ============================================================================
# SUMMARY REPORTING
# ============================================================================

def print_result_summary(results: List[Dict]):
    """Print summary table of test results."""
    
    print("\n" + "="*100)
    print("AGENT INSTANCE LISTING ENDPOINT TEST RESULTS")
    print("="*100)
    
    # Calculate column widths
    col_account = max(20, max([len(r["account"]) for r in results] + [len("Account")]))
    col_status = 8
    col_count = 8
    col_instances = 40
    col_result = 10
    
    # Header
    header = (
        f"{'Account':<{col_account}} | "
        f"{'Status':<{col_status}} | "
        f"{'Count':<{col_count}} | "
        f"{'Instances':<{col_instances}} | "
        f"{'Result':<{col_result}}"
    )
    print(header)
    print("-" * len(header))
    
    # Results
    for result in results:
        account = result["account"]
        status_code = result.get("status_code", "N/A")
        status_str = str(status_code) if status_code else "CONN_ERR"
        
        # Extract instance info
        data = result.get("response_data", {})
        if isinstance(data, dict):
            count = data.get("count", 0)
            instances = data.get("instances", [])
            instance_slugs = [inst.get("instance_slug", "?") for inst in instances if isinstance(inst, dict)]
            instances_str = ", ".join(instance_slugs) if instance_slugs else "N/A"
        else:
            count = 0
            instances_str = "N/A"
        
        # Determine result
        if result["success"]:
            validation_result = result.get("validation_result", {})
            if validation_result.get("structure_valid") and validation_result.get("instances_complete"):
                result_str = "✅ PASS"
            else:
                result_str = "⚠️  WARN"
        else:
            result_str = "❌ FAIL"
        
        # Print row
        print(
            f"{account:<{col_account}} | "
            f"{status_str:<{col_status}} | "
            f"{count:<{col_count}} | "
            f"{instances_str[:col_instances]:<{col_instances}} | "
            f"{result_str:<{col_result}}"
        )
    
    print("="*100)
    
    # Overall summary
    passed = sum(1 for r in results if r["success"] and r.get("validation_result", {}).get("structure_valid") and r.get("validation_result", {}).get("instances_complete"))
    failed = len(results) - passed
    
    print(f"\nTotal: {len(results)} tests | ✅ Passed: {passed} | ❌ Failed: {failed}")
    print("\n")


def print_detailed_errors(results: List[Dict]):
    """Print detailed error information."""
    
    has_errors = any(not r["success"] or not r.get("validation_result", {}).get("structure_valid") or not r.get("validation_result", {}).get("instances_complete") for r in results)
    
    if not has_errors:
        print("✅ All tests passed with no errors!")
        return
    
    print("\n" + "="*100)
    print("DETAILED ERROR INFORMATION")
    print("="*100 + "\n")
    
    for result in results:
        if not result["success"]:
            print(f"❌ {result['account']}")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print()
        else:
            validation = result.get("validation_result", {})
            if not validation.get("structure_valid"):
                print(f"⚠️  {result['account']} - Structure validation failed")
                for error in validation.get("structure_errors", []):
                    print(f"   • {error}")
                print()
            if not validation.get("instances_complete"):
                print(f"⚠️  {result['account']} - Missing expected instances")
                for missing in validation.get("missing_instances", []):
                    print(f"   • Missing: {missing}")
                print()


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    """Run all manual tests for the list endpoint."""
    
    print("\n" + "="*100)
    print("STARTING MANUAL TESTS: Agent Instance Listing Endpoint")
    print("="*100)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = []
    
    # Test 1: Valid accounts
    print("Test 1: Valid Accounts")
    print("-" * 50)
    
    for account_config in TEST_CASES["valid_accounts"]:
        account = account_config["account"]
        expected_instances = account_config["expected_instances"]
        expected_count = account_config["expected_count"]
        
        print(f"\n  Testing: {account}")
        print(f"  Expected instances: {', '.join(expected_instances)}")
        
        result = test_list_endpoint(BASE_URL, account)
        
        if result and result["success"]:
            # Validate response structure
            structure_valid, structure_errors = validate_response_structure(result["response_data"])
            
            # Validate expected instances
            instances_complete, missing_instances = validate_expected_instances(
                result["response_data"], 
                expected_instances
            )
            
            result["validation_result"] = {
                "structure_valid": structure_valid,
                "structure_errors": structure_errors,
                "instances_complete": instances_complete,
                "missing_instances": missing_instances
            }
            
            if structure_valid and instances_complete:
                print(f"  ✅ Status: {result['status_code']} OK")
                print(f"  ✅ Found {result['response_data']['count']} instances")
                print(f"  ✅ All expected instances present")
            else:
                print(f"  ⚠️  Status: {result['status_code']} with validation issues")
                if not structure_valid:
                    print(f"  ⚠️  Structure errors: {len(structure_errors)}")
                if not instances_complete:
                    print(f"  ⚠️  Missing instances: {missing_instances}")
        else:
            print(f"  ❌ Request failed: {result.get('error', 'Unknown error')}")
            result["validation_result"] = {
                "structure_valid": False,
                "structure_errors": ["Request failed"],
                "instances_complete": False,
                "missing_instances": expected_instances
            }
        
        results.append(result)
    
    # Test 2: Invalid account (should return 404)
    print("\n\nTest 2: Invalid Account (Error Handling)")
    print("-" * 50)
    
    invalid_account = TEST_CASES["invalid_account"]
    print(f"\n  Testing: {invalid_account} (should return 404)")
    
    result = test_list_endpoint(BASE_URL, invalid_account)
    
    if result:
        expected_404 = result["status_code"] == 404
        result["success"] = expected_404  # For invalid account, success means getting 404
        result["validation_result"] = {
            "structure_valid": expected_404,
            "structure_errors": [] if expected_404 else ["Expected 404, got {result['status_code']}"],
            "instances_complete": expected_404,
            "missing_instances": []
        }
        
        if expected_404:
            print(f"  ✅ Status: 404 (correctly rejected invalid account)")
        else:
            print(f"  ❌ Status: {result['status_code']} (expected 404)")
    else:
        print(f"  ❌ Request failed")
        result = {
            "account": invalid_account,
            "status_code": None,
            "success": False,
            "response_data": None,
            "error": "Request failed",
            "validation_result": {
                "structure_valid": False,
                "structure_errors": ["Request failed"],
                "instances_complete": False,
                "missing_instances": []
            }
        }
    
    results.append(result)
    
    # Print summaries
    print_result_summary(results)
    print_detailed_errors(results)
    
    # Exit with appropriate code
    all_passed = all(
        r["success"] and 
        r.get("validation_result", {}).get("structure_valid") and 
        r.get("validation_result", {}).get("instances_complete") 
        for r in results
    )
    
    exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

