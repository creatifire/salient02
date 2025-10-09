"""
Check what Qwen models are available on OpenRouter.

This script queries the OpenRouter API to list available Qwen models
and helps verify the correct model IDs to use in config files.

Usage:
    python backend/tests/manual/check_openrouter_models.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
import json
from dotenv import load_dotenv

# Load environment variables
env_path = backend_dir.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")


def list_openrouter_models():
    """
    Fetch and display available models from OpenRouter API.
    """
    print()
    print("=" * 100)
    print("OPENROUTER AVAILABLE MODELS")
    print("=" * 100)
    print()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("💡 Make sure your .env file has OPENROUTER_API_KEY set")
        return False
    
    print("🔑 API Key found")
    print("🌐 Fetching models from OpenRouter...")
    print()
    
    try:
        response = httpx.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Salient AI"
            },
            timeout=10.0
        )
        
        if response.status_code != 200:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        models = data.get("data", [])
        
        # Filter for Qwen models
        qwen_models = [m for m in models if "qwen" in m["id"].lower()]
        
        print("=" * 100)
        print(f"QWEN MODELS FOUND: {len(qwen_models)}")
        print("=" * 100)
        print()
        
        if not qwen_models:
            print("❌ No Qwen models found!")
            print("💡 This might indicate an API issue or the models are not available")
            return False
        
        # Print Qwen models
        print(f"{'Model ID':<60} {'Context':<15} {'Pricing (per 1M tokens)'}")
        print("─" * 100)
        
        for model in sorted(qwen_models, key=lambda x: x["id"]):
            model_id = model["id"]
            context = f"{model.get('context_length', 'N/A'):,}" if model.get('context_length') else "N/A"
            
            pricing = model.get("pricing", {})
            prompt_price = pricing.get("prompt", "N/A")
            completion_price = pricing.get("completion", "N/A")
            
            if prompt_price != "N/A":
                prompt_price = f"${float(prompt_price) * 1_000_000:.2f}"
            if completion_price != "N/A":
                completion_price = f"${float(completion_price) * 1_000_000:.2f}"
            
            price_str = f"{prompt_price} / {completion_price}"
            
            print(f"{model_id:<60} {context:<15} {price_str}")
        
        print()
        print("=" * 100)
        print()
        
        # Check for the specific model in the config
        configured_model = "qwen/qwen3-vl-235b-a22b-instruct"
        print(f"🔍 Checking configured model: {configured_model}")
        
        found = any(m["id"] == configured_model for m in models)
        if found:
            print(f"✅ Model found in OpenRouter catalog")
        else:
            print(f"❌ Model NOT found in OpenRouter catalog")
            print(f"💡 This is why acme/acme_chat1 is calling the wrong LLM!")
            print()
            print("Suggested alternatives:")
            for model in qwen_models[:5]:  # Show first 5
                print(f"  - {model['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = list_openrouter_models()
    sys.exit(0 if success else 1)

