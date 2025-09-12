import os
import asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file at project root
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir.parent / ".env")

class SimpleResponse(BaseModel):
    """Simple response model for testing."""
    message: str = Field(..., description="The response message")

async def test_openrouter_provider():
    """
    Test Pydantic AI with dedicated OpenRouterProvider to see if it handles cost data.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        return
    
    print("🔍 Testing Pydantic AI with OpenRouterProvider")
    print("=" * 55)
    
    try:
        # Try to import OpenRouterProvider
        try:
            from pydantic_ai.providers.openrouter import OpenRouterProvider
            print("✅ OpenRouterProvider import successful!")
        except ImportError as e:
            print(f"❌ Cannot import OpenRouterProvider: {e}")
            print("   This provider might not exist in the current version")
            return
            
        # Configure Pydantic AI with OpenRouterProvider
        provider = OpenRouterProvider(api_key=openrouter_api_key)
        
        model_instance = OpenAIChatModel(
            model_name="deepseek/deepseek-chat-v3.1",  # Use known working model
            provider=provider
        )
        
        agent = Agent(
            model=model_instance,
            output_type=SimpleResponse,
        )
        
        print("🦜 Running agent with OpenRouterProvider...")
        
        # Run the agent
        result = await agent.run("Say hello in exactly 4 words")
        
        print("✅ Pydantic AI + OpenRouterProvider works!")
        print(f"📝 Response: '{result.output.message}'")
        
        # Check usage data (call the method)
        usage_data = result.usage()
        print(f"\n🎯 USAGE DATA:")
        print(f"📊 Usage type: {type(usage_data)}")
        print(f"📊 Usage: {usage_data}")
        
        # Check token fields
        print(f"✅ Prompt tokens: {usage_data.input_tokens}")
        print(f"✅ Completion tokens: {usage_data.output_tokens}")
        print(f"✅ Total tokens: {usage_data.total_tokens}")
        
        # Check for cost data in details
        print(f"\n💰 COST DATA INVESTIGATION:")
        if hasattr(usage_data, 'details') and usage_data.details:
            print(f"📋 Details found: {usage_data.details}")
            if 'cost' in usage_data.details:
                print(f"🎯 BREAKTHROUGH: Cost found: ${usage_data.details['cost']:.6f}")
                print("✅ SUCCESS: OpenRouterProvider provides real cost data!")
            else:
                print("❌ No 'cost' key in details")
                print(f"   Available keys: {list(usage_data.details.keys())}")
        else:
            print("❌ No details field or empty details")
            
        # Check for any cost-related attributes directly
        cost_attrs = [attr for attr in dir(usage_data) if 'cost' in attr.lower() and not attr.startswith('_')]
        if cost_attrs:
            print(f"💰 Cost-related attributes found: {cost_attrs}")
            for attr in cost_attrs:
                value = getattr(usage_data, attr, None)
                print(f"   {attr}: {value}")
        else:
            print("❌ No cost-related attributes found")
            
        # Check if OpenRouterProvider adds any special behavior
        print(f"\n🔧 PROVIDER ANALYSIS:")
        print(f"   Provider type: {type(provider)}")
        provider_attrs = [attr for attr in dir(provider) if not attr.startswith('_')]
        print(f"   Provider attributes: {provider_attrs}")
        
        print(f"\n🎯 CONCLUSION:")
        if hasattr(usage_data, 'details') and usage_data.details and 'cost' in usage_data.details:
            print("🏆 BREAKTHROUGH: OpenRouterProvider successfully provides real cost data!")
        else:
            print("❌ OpenRouterProvider still doesn't provide cost data")
            print("   Same limitation as OpenAIProvider with custom base_url")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_openrouter_provider())
