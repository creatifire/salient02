#!/usr/bin/env python3
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

"""
Test script to verify instance loader retrieves different LLM settings
for each configured agent instance.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path (go up 2 levels: manual/ -> tests/ -> backend/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.instance_loader import load_agent_instance
from app.database import initialize_database


async def test_config_loading():
    """Test that each instance loads with its configured LLM model."""
    
    # Initialize database connection
    print("🔌 Initializing database connection...")
    await initialize_database()
    print("✅ Database initialized\n")
    
    print("🧪 Testing Agent Instance Configuration Loading")
    print("=" * 70)
    
    # Test instances to check
    test_instances = [
        ("default_account", "simple_chat1"),
        ("default_account", "simple_chat2"),
        ("acme", "acme_chat1"),
    ]
    
    results = []
    
    for account_slug, instance_slug in test_instances:
        print(f"\n📋 Loading: {account_slug}/{instance_slug}")
        print("-" * 70)
        
        try:
            # Load the instance
            instance = await load_agent_instance(account_slug, instance_slug)
            
            # Extract model settings
            model_settings = instance.config.get("model_settings", {})
            model = model_settings.get("model", "NOT FOUND")
            temperature = model_settings.get("temperature", "NOT FOUND")
            max_tokens = model_settings.get("max_tokens", "NOT FOUND")
            
            # Extract context settings
            context_settings = instance.config.get("context_management", {})
            history_limit = context_settings.get("history_limit", "NOT FOUND")
            
            # Extract tool settings
            tools = instance.config.get("tools", {})
            vector_search = tools.get("vector_search", {})
            pinecone_namespace = vector_search.get("pinecone", {}).get("namespace", "NOT FOUND")
            
            print(f"✅ Instance loaded successfully!")
            print(f"   Account: {instance.account_slug}")
            print(f"   Instance: {instance.instance_slug}")
            print(f"   Display Name: {instance.display_name}")
            print(f"   Agent Type: {instance.agent_type}")
            print(f"\n   🤖 Model Settings:")
            print(f"      Model: {model}")
            print(f"      Temperature: {temperature}")
            print(f"      Max Tokens: {max_tokens}")
            print(f"\n   📚 Context Settings:")
            print(f"      History Limit: {history_limit}")
            print(f"\n   🔍 Vector Settings:")
            print(f"      Pinecone Namespace: {pinecone_namespace}")
            
            results.append({
                "account": account_slug,
                "instance": instance_slug,
                "model": model,
                "temperature": temperature,
                "history_limit": history_limit,
                "namespace": pinecone_namespace,
                "status": "✅ SUCCESS"
            })
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            results.append({
                "account": account_slug,
                "instance": instance_slug,
                "model": "FAILED",
                "temperature": "FAILED",
                "history_limit": "FAILED",
                "namespace": "FAILED",
                "status": f"❌ ERROR: {str(e)}"
            })
    
    # Summary table
    print("\n" + "=" * 70)
    print("📊 CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"\n{'Account':<20} {'Instance':<15} {'Model':<40} {'Temp':<6} {'History'}")
    print("-" * 105)
    
    for result in results:
        account = result['account'][:19]
        instance = result['instance'][:14]
        model = result['model'][:39] if isinstance(result['model'], str) else str(result['model'])
        temp = str(result['temperature'])[:5]
        history = str(result['history_limit'])[:7]
        
        print(f"{account:<20} {instance:<15} {model:<40} {temp:<6} {history}")
    
    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 70)
    
    # Verify differentiation
    models = [r['model'] for r in results if r['model'] != "FAILED"]
    temps = [r['temperature'] for r in results if r['temperature'] != "FAILED"]
    namespaces = [r['namespace'] for r in results if r['namespace'] != "FAILED"]
    
    print(f"\n🔍 Differentiation Check:")
    print(f"   Unique Models: {len(set(models))} / {len(models)} - {'✅ PASS' if len(set(models)) == 3 else '❌ FAIL'}")
    print(f"   Temperature Variation: {set(temps)} - {'✅ PASS' if 0.5 in temps else '❌ FAIL'}")
    print(f"   Namespace Isolation: {set(namespaces)} - {'✅ PASS' if 'acme' in namespaces else '❌ FAIL'}")
    
    # Check for errors
    errors = [r for r in results if "ERROR" in r['status']]
    if errors:
        print(f"\n❌ {len(errors)} ERRORS DETECTED")
        return False
    else:
        print(f"\n✅ ALL CONFIGURATIONS LOADED SUCCESSFULLY")
        return True


if __name__ == "__main__":
    success = asyncio.run(test_config_loading())
    sys.exit(0 if success else 1)

