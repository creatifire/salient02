"""
Quick test of the 3 problematic test cases from Phase 2D.

This script runs ONLY the failing tests with detailed logging
to see what the tools are actually returning.
"""
import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import and run only the problem tests
from tool_calling_wyckoff import (
    load_wyckoff_config,
    get_wyckoff_account_id,
    phase2d_test_with_llm
)
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run only the 3 problematic tests."""
    print("="*70)
    print("TESTING PROBLEM CASES - Tests 2, 3, 4")
    print("="*70)
    
    # Load config
    agent_config = await load_wyckoff_config()
    account_id = await get_wyckoff_account_id()
    
    # Test 2: Cardiology department phone
    print("\n" + "="*70)
    print("TEST 2: Cardiology Department Phone")
    print("="*70)
    await phase2d_test_with_llm(
        2,
        "What's the cardiology department phone number?",
        "phone_directory",
        "718-963-2000",
        account_id,
        agent_config
    )
    
    # Test 3: Find Dr. Premila Bhat
    print("\n" + "="*70)
    print("TEST 3: Find Dr. Premila Bhat")
    print("="*70)
    await phase2d_test_with_llm(
        3,
        "Find Dr. Premila Bhat",
        "doctors",
        "Premila Bhat",
        account_id,
        agent_config
    )
    
    # Test 4: Emergency room number
    print("\n" + "="*70)
    print("TEST 4: Emergency Room Number")
    print("="*70)
    await phase2d_test_with_llm(
        4,
        "What's the emergency room number?",
        "phone_directory",
        "718-963-7272",
        account_id,
        agent_config
    )


if __name__ == '__main__':
    asyncio.run(main())

