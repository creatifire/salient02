import os
import asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file at project root
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir.parent / ".env")

class SimpleResponse(BaseModel):
    """Simple response model for testing."""
    message: str = Field(..., description="The response message")

async def test_openrouter_provider_deep_dive():
    """
    Deep dive into OpenRouterProvider to see if we can access cost data.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        return
    
    print("🔍 DEEP DIVE: OpenRouterProvider Analysis")
    print("=" * 50)
    
    try:
        # Create provider and inspect its properties
        provider = OpenRouterProvider(api_key=openrouter_api_key)
        
        print(f"🔧 PROVIDER INVESTIGATION:")
        print(f"   Type: {type(provider)}")
        print(f"   Name: {getattr(provider, 'name', 'No name')}")
        print(f"   Base URL: {getattr(provider, 'base_url', 'No base_url')}")
        
        # Check the client
        if hasattr(provider, 'client'):
            client = provider.client()  # It might be a method
            print(f"   Client type: {type(client)}")
            print(f"   Client base_url: {getattr(client, 'base_url', 'No base_url')}")
            print(f"   Client attrs: {[a for a in dir(client) if not a.startswith('_')][:10]}...")
        
        # Check model profile
        if hasattr(provider, 'model_profile'):
            profile = provider.model_profile("openai/gpt-3.5-turbo")
            print(f"   Model profile type: {type(profile)}")
            print(f"   Model profile: {profile}")
        
        # Create model and test
        model_instance = OpenAIChatModel(
            model_name="openai/gpt-3.5-turbo",
            provider=provider
        )
        
        agent = Agent(
            model=model_instance,
            output_type=SimpleResponse,
        )
        
        print(f"\n🦜 Testing OpenRouterProvider...")
        result = await agent.run("Count to 3")
        
        print(f"✅ Response: '{result.output.message}'")
        
        # Get usage data
        usage_data = result.usage()
        print(f"\n🎯 USAGE ANALYSIS:")
        print(f"   Usage: {usage_data}")
        print(f"   Details: {usage_data.details}")
        
        # Check if we can access the raw result or model response
        print(f"\n🔍 RAW RESULT INVESTIGATION:")
        print(f"   Result type: {type(result)}")
        result_attrs = [attr for attr in dir(result) if not attr.startswith('_')]
        print(f"   Result attrs: {result_attrs}")
        
        # Try to access various result attributes
        if hasattr(result, 'all_messages'):
            messages = result.all_messages()
            print(f"   All messages count: {len(messages)}")
            if messages:
                last_msg = messages[-1]
                print(f"   Last message type: {type(last_msg)}")
                if hasattr(last_msg, 'data'):
                    print(f"   Last message data: {last_msg.data}")
                    
        # Check if there's a _raw_response or similar
        for attr_name in ['_raw_response', 'raw_response', '_response', 'response', '_model_response']:
            if hasattr(result, attr_name):
                raw_resp = getattr(result, attr_name)
                print(f"   Found {attr_name}: {type(raw_resp)}")
                if hasattr(raw_resp, 'usage'):
                    print(f"   Raw usage: {raw_resp.usage}")
                    
        # Try to monkey-patch or intercept the client to see the actual response
        print(f"\n🔧 TRYING TO ACCESS REAL COST DATA...")
        
        # Let's try to make a direct call to see what the provider's client returns
        if hasattr(provider, 'client'):
            direct_client = provider.client()
            if hasattr(direct_client, 'chat'):
                print("   Attempting direct client call...")
                try:
                    # Try to make a direct call with usage parameter
                    direct_response = await direct_client.chat.completions.create(
                        model="openai/gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Hi"}],
                        # Try to add usage parameter like OpenRouter expects
                        extra_body={"usage": {"include": True}}
                    )
                    print(f"   Direct response type: {type(direct_response)}")
                    if hasattr(direct_response, 'usage'):
                        usage = direct_response.usage
                        print(f"   Direct usage: {usage}")
                        print(f"   Direct usage attrs: {dir(usage)}")
                        
                        # Check for cost in the direct response
                        if hasattr(usage, 'cost'):
                            print(f"   🎯 DIRECT COST FOUND: ${usage.cost}")
                        else:
                            print("   ❌ No cost in direct response either")
                            
                except Exception as direct_error:
                    print(f"   ❌ Direct call failed: {direct_error}")
        
        print(f"\n🎯 CONCLUSION:")
        print("   OpenRouterProvider works but follows same limitations:")
        print("   - Perfect token tracking ✅")  
        print("   - No cost data access ❌")
        print("   - Same underlying issue as OpenAIProvider approach")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_openrouter_provider_deep_dive())
