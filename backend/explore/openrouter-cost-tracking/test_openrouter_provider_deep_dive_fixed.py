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

async def test_openrouter_provider_complete_investigation():
    """
    Complete investigation of OpenRouterProvider and direct client access.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        return
    
    print("🔍 COMPLETE INVESTIGATION: OpenRouterProvider vs Direct Client")
    print("=" * 65)
    
    try:
        # Create provider and inspect its properties
        provider = OpenRouterProvider(api_key=openrouter_api_key)
        
        print(f"🔧 PROVIDER DETAILS:")
        print(f"   Type: {type(provider)}")
        print(f"   Name: {provider.name}")
        print(f"   Base URL: {provider.base_url}")
        
        # Access client directly (it's a property, not a method)
        client = provider.client
        print(f"   Client type: {type(client)}")
        print(f"   Client base_url: {client.base_url}")
        
        # Test with Pydantic AI first
        print(f"\n🦜 TESTING WITH PYDANTIC AI:")
        print("-" * 35)
        
        model_instance = OpenAIChatModel(
            model_name="openai/gpt-3.5-turbo",
            provider=provider
        )
        
        agent = Agent(
            model=model_instance,
            output_type=SimpleResponse,
        )
        
        result = await agent.run("Say hi")
        usage_data = result.usage()
        
        print(f"✅ Pydantic AI Response: '{result.output.message}'")
        print(f"📊 Pydantic AI Usage: {usage_data}")
        print(f"📋 Details: {usage_data.details}")
        
        # Now test direct client access
        print(f"\n🔧 TESTING DIRECT CLIENT ACCESS:")
        print("-" * 40)
        
        # Make direct call without usage parameter
        print("   Testing direct call WITHOUT usage parameter...")
        direct_response_1 = await client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}],
        )
        
        print(f"   Direct response type: {type(direct_response_1)}")
        print(f"   Direct response usage: {direct_response_1.usage}")
        
        # Check for cost in direct response
        if hasattr(direct_response_1.usage, 'cost'):
            print(f"   💰 Direct cost (no param): ${direct_response_1.usage.cost}")
        else:
            print("   ❌ No cost in direct response (no param)")
            
        # Make direct call WITH usage parameter
        print("\n   Testing direct call WITH usage parameter...")
        try:
            direct_response_2 = await client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say hello again"}],
                extra_body={"usage": {"include": True}}  # The magic parameter!
            )
            
            print(f"   Direct response with usage: {direct_response_2.usage}")
            
            # Check for cost with usage parameter
            if hasattr(direct_response_2.usage, 'cost'):
                print(f"   🎯 BREAKTHROUGH: Direct cost (with param): ${direct_response_2.usage.cost}")
                print("   ✅ SUCCESS: Direct client + usage param = Real OpenRouter cost!")
            else:
                print("   ❌ Still no cost even with usage parameter")
                # Print all usage attributes to see what's available
                usage_attrs = [attr for attr in dir(direct_response_2.usage) if not attr.startswith('_')]
                print(f"   Available usage attrs: {usage_attrs}")
                
                # Try to convert to dict to see raw data
                try:
                    usage_dict = direct_response_2.usage.model_dump()
                    print(f"   Usage as dict: {usage_dict}")
                except:
                    print("   Could not convert usage to dict")
                    
        except Exception as usage_error:
            print(f"   ❌ Direct call with usage parameter failed: {usage_error}")
            
        # Final comparison
        print(f"\n🎯 FINAL COMPARISON:")
        print("-" * 25)
        print("✅ Pydantic AI + OpenRouterProvider:")
        print(f"   - Works perfectly: No validation errors")
        print(f"   - Token data: {usage_data.total_tokens} tokens")
        print(f"   - Cost data: {'❌ Missing' if 'cost' not in str(usage_data.details) else '✅ Available'}")
        
        print("🔧 Direct Client Access:")
        print(f"   - Raw API access: Available")
        print(f"   - Usage parameter: Supported")
        print(f"   - Cost data: {'✅ Available' if hasattr(direct_response_2.usage, 'cost') else '❌ Missing'}")
        
        print(f"\n🏆 CONCLUSION:")
        print("   OpenRouterProvider exists and works, but has same limitations")
        print("   Direct client access might provide cost data with usage parameter")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_openrouter_provider_complete_investigation())
