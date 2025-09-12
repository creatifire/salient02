#!/usr/bin/env python3
"""
Debug script to understand how OpenRouterProvider uses its client
and where HTTP requests are actually made.
"""

import os
import sys
from pathlib import Path
import asyncio

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()

async def debug_provider_client():
    """Debug the OpenRouterProvider's client and request flow."""
    
    print("🔍 DEBUGGING OPENROUTER PROVIDER CLIENT")
    print("="*50)
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    # Create provider instance
    provider = OpenRouterProvider(api_key=api_key)
    print(f"✅ Provider created")
    
    # Check the client property
    print(f"\n🔍 Inspecting provider.client:")
    try:
        client = provider.client
        print(f"  Type: {type(client)}")
        print(f"  Module: {type(client).__module__}")
        
        # Check client methods
        client_methods = [method for method in dir(client) if not method.startswith('__')]
        print(f"  Methods: {len(client_methods)}")
        
        # Look for HTTP-related methods on the client
        http_methods = [m for m in client_methods if any(term in m.lower() for term in ['request', 'post', 'get', 'http', 'call', 'completion'])]
        print(f"  HTTP methods: {http_methods}")
        
        # Check if it's an OpenAI client
        if hasattr(client, 'chat'):
            print(f"  ✅ Has chat attribute")
            chat = client.chat
            print(f"    Chat type: {type(chat)}")
            if hasattr(chat, 'completions'):
                print(f"    ✅ Has completions")
                completions = chat.completions
                print(f"      Completions type: {type(completions)}")
                completions_methods = [m for m in dir(completions) if not m.startswith('__')]
                print(f"      Completions methods: {completions_methods}")
        
    except Exception as e:
        print(f"❌ Error inspecting client: {e}")
    
    # Check the _client property (internal)
    print(f"\n🔍 Inspecting provider._client:")
    try:
        _client = provider._client
        print(f"  Type: {type(_client)}")
        print(f"  Module: {type(_client).__module__}")
        
        # Check if it has a request method we can override
        _client_methods = [method for method in dir(_client) if not method.startswith('__')]
        request_methods = [m for m in _client_methods if 'request' in m.lower()]
        print(f"  Request methods: {request_methods}")
        
    except Exception as e:
        print(f"❌ Error inspecting _client: {e}")
    
    # Try to trace where HTTP requests actually happen
    print(f"\n🔍 Tracing request flow:")
    try:
        # Create a model and agent to see the request flow
        model = OpenAIChatModel('deepseek/deepseek-chat-v3.1', provider=provider)
        agent = Agent(model, system_prompt="Test")
        
        print(f"  Model type: {type(model)}")
        model_methods = [m for m in dir(model) if not m.startswith('__')]
        request_model_methods = [m for m in model_methods if any(term in m.lower() for term in ['request', 'call', 'run', 'generate'])]
        print(f"  Model request methods: {request_model_methods}")
        
        # Check if we can intercept at the model level
        if hasattr(model, '_request'):
            print(f"  ✅ Model has _request method")
        if hasattr(model, 'request'):
            print(f"  ✅ Model has request method")
        if hasattr(model, '_call'):
            print(f"  ✅ Model has _call method")
            
    except Exception as e:
        print(f"❌ Error tracing request flow: {e}")

if __name__ == "__main__":
    asyncio.run(debug_provider_client())
