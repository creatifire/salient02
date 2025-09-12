#!/usr/bin/env python3
"""
Debug script to understand the OpenRouterProvider architecture
and find the correct method to override for cost tracking.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv

load_dotenv()

def debug_provider_methods():
    """Debug the OpenRouterProvider to understand its architecture."""
    
    print("🔍 DEBUGGING OPENROUTER PROVIDER ARCHITECTURE")
    print("="*60)
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    # Create provider instance
    provider = OpenRouterProvider(api_key=api_key)
    
    # Inspect all methods
    print(f"\n📋 All OpenRouterProvider methods:")
    methods = [method for method in dir(provider) if not method.startswith('__')]
    for method in sorted(methods):
        print(f"  - {method}")
    
    # Check class hierarchy 
    print(f"\n🏗️ Class hierarchy:")
    mro = type(provider).__mro__
    for i, cls in enumerate(mro):
        print(f"  {i}: {cls.__name__} ({cls.__module__})")
    
    # Check if it has specific HTTP methods
    http_methods = ['request', 'request_json', 'make_request', '_request', '_make_request', 'post', '_post']
    print(f"\n🌐 HTTP-related methods:")
    for method in http_methods:
        if hasattr(provider, method):
            method_obj = getattr(provider, method)
            print(f"  ✅ {method}: {type(method_obj)} - {method_obj}")
        else:
            print(f"  ❌ {method}: Not found")
    
    # Check the parent class methods
    print(f"\n👨‍👩‍👧‍👦 Parent class methods:")
    if hasattr(provider, '__class__'):
        parent_classes = provider.__class__.__bases__
        for parent in parent_classes:
            print(f"  Parent: {parent.__name__}")
            parent_methods = [m for m in dir(parent) if not m.startswith('__')]
            for method in parent_methods:
                if 'request' in method.lower() or 'http' in method.lower():
                    print(f"    🌐 {method}")
    
    # Try to understand the request flow
    print(f"\n🔄 Looking for request flow methods:")
    potential_methods = [
        'chat_completions_request',
        'completions',  
        'complete',
        'stream_request',
        'async_request'
    ]
    
    for method in potential_methods:
        if hasattr(provider, method):
            print(f"  ✅ Found: {method}")
        else:
            print(f"  ❌ Not found: {method}")

if __name__ == "__main__":
    debug_provider_methods()
