#!/usr/bin/env python3
"""
Test Runner for Agent Conversation Loading Tests - TASK 0017-003-005

Quick script to run all tests related to agent conversation loading functionality.
Includes both unit tests and integration tests with proper reporting.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests():
    """Run all agent conversation loading tests."""
    print("🧪 Running Agent Conversation Loading Tests - TASK 0017-003-005")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    test_commands = [
        {
            "name": "Unit Tests - Agent Session Service",
            "command": ["python", "-m", "pytest", "tests/unit/test_agent_session.py", "-v", "--tb=short"],
            "description": "CHUNK 0017-003-005-01 & 03: Tests load_agent_conversation() and get_session_stats() functions"
        },
        {
            "name": "Unit Tests - Simple Chat Agent Integration",
            "command": ["python", "-m", "pytest", "tests/unit/test_simple_chat_agent.py", "-v", "--tb=short"],
            "description": "CHUNK 0017-003-005-02: Tests simple_chat() history loading integration"
        },
        {
            "name": "Integration Tests - Full Workflow",
            "command": ["python", "-m", "pytest", "tests/integration/test_agent_conversation_loading.py", "-v", "--tb=short", "-m", "integration"],
            "description": "All chunks: Complete cross-endpoint conversation workflow testing"
        },
        {
            "name": "All Agent Conversation Tests",
            "command": ["python", "-m", "pytest", "tests/unit/test_agent_session.py", "tests/unit/test_simple_chat_agent.py", "tests/integration/test_agent_conversation_loading.py", "-v", "--cov=app.services.agent_session", "--cov=app.agents.simple_chat", "--cov-report=term-missing"],
            "description": "Complete test suite with coverage report"
        }
    ]
    
    results = {}
    
    for test_config in test_commands:
        print(f"\n🔄 {test_config['name']}")
        print(f"   {test_config['description']}")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                test_config['command'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"✅ {test_config['name']} - PASSED")
                results[test_config['name']] = "PASSED"
            else:
                print(f"❌ {test_config['name']} - FAILED")
                print("STDOUT:", result.stdout[-500:] if result.stdout else "No output")
                print("STDERR:", result.stderr[-500:] if result.stderr else "No errors")
                results[test_config['name']] = "FAILED"
                
        except Exception as e:
            print(f"💥 {test_config['name']} - ERROR: {e}")
            results[test_config['name']] = "ERROR"
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, status in results.items():
        status_emoji = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "ERROR": "💥"
        }.get(status, "❓")
        
        print(f"{status_emoji} {test_name}: {status}")
    
    # Overall result
    failed_tests = [name for name, status in results.items() if status != "PASSED"]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test suite(s) failed: {', '.join(failed_tests)}")
        return 1
    else:
        print(f"\n🎉 All {len(results)} test suites passed!")
        return 0


def run_quick_unit_tests():
    """Run only unit tests for quick feedback."""
    print("🚀 Quick Unit Tests - Agent Conversation Loading")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            "python", "-m", "pytest", 
            "tests/unit/test_agent_session.py",
            "tests/unit/test_simple_chat_agent.py",
            "-v", "--tb=line"
        ], check=False)
        
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        exit_code = run_quick_unit_tests()
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
