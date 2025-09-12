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

async def test_openrouter_provider_multiple_models():
    """
    Test Pydantic AI with OpenRouterProvider using different models to see which ones work.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        return
    
    print("🔍 Testing Pydantic AI with OpenRouterProvider - Multiple Models")
    print("=" * 65)
    
    # Try different models to see if any work with OpenRouterProvider
    models_to_test = [
        "openai/gpt-3.5-turbo",
        "anthropic/claude-3.5-sonnet",
        "meta-llama/llama-3.1-8b-instruct",
        "meta-llama/llama-3-8b-instruct",
        "deepseek/deepseek-chat",
    ]
    
    try:
        # Import OpenRouterProvider
        from pydantic_ai.providers.openrouter import OpenRouterProvider
        print("✅ OpenRouterProvider import successful!")
        
        provider = OpenRouterProvider(api_key=openrouter_api_key)
        print(f"✅ OpenRouterProvider created: {type(provider)}")
        
        for model_name in models_to_test:
            print(f"\n🧪 Testing model: {model_name}")
            print("-" * 40)
            
            try:
                model_instance = OpenAIChatModel(
                    model_name=model_name,
                    provider=provider
                )
                
                agent = Agent(
                    model=model_instance,
                    output_type=SimpleResponse,
                )
                
                print(f"🦜 Running agent with {model_name}...")
                
                # Run the agent with a simple prompt
                result = await agent.run("Hello")
                
                print(f"✅ SUCCESS: {model_name} works with OpenRouterProvider!")
                print(f"📝 Response: '{result.output.message}'")
                
                # Check usage data
                usage_data = result.usage()
                print(f"🎯 Usage: {usage_data}")
                print(f"📊 Tokens: {usage_data.input_tokens} + {usage_data.output_tokens} = {usage_data.total_tokens}")
                
                # Check for cost data
                if hasattr(usage_data, 'details') and usage_data.details:
                    print(f"📋 Details: {usage_data.details}")
                    if 'cost' in usage_data.details:
                        print(f"💰 BREAKTHROUGH: Cost found: ${usage_data.details['cost']:.6f}")
                        print("🏆 SUCCESS: OpenRouterProvider provides real cost data!")
                        return True  # Found working model with cost data
                else:
                    print("❌ No cost data in details")
                
                # Since we found a working model, let's do more investigation
                print(f"\n🔧 DETAILED ANALYSIS for {model_name}:")
                print(f"   Provider attrs: {[a for a in dir(provider) if not a.startswith('_')]}")
                print(f"   Usage attrs: {[a for a in dir(usage_data) if not a.startswith('_')]}")
                
                return True  # Found at least one working model
                
            except Exception as model_error:
                print(f"❌ Model {model_name} failed: {str(model_error)[:100]}...")
                continue
        
        print(f"\n❌ NO MODELS WORKED: All tested models failed with OpenRouterProvider")
        
    except ImportError as e:
        print(f"❌ Cannot import OpenRouterProvider: {e}")
        print("   This provider might not exist or might be in a different location")
    except Exception as e:
        print(f"❌ General error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

async def test_openrouter_provider_investigation():
    """
    Investigate what providers are available in pydantic_ai.
    """
    print("\n🔍 INVESTIGATING AVAILABLE PROVIDERS:")
    print("=" * 45)
    
    try:
        import pydantic_ai.providers
        print(f"✅ pydantic_ai.providers module found")
        
        # List all available providers
        provider_dir = dir(pydantic_ai.providers)
        providers = [item for item in provider_dir if not item.startswith('_')]
        print(f"📋 Available providers: {providers}")
        
        # Check if openrouter exists
        try:
            import pydantic_ai.providers.openrouter
            print("✅ pydantic_ai.providers.openrouter module exists")
            
            openrouter_dir = dir(pydantic_ai.providers.openrouter)
            openrouter_items = [item for item in openrouter_dir if not item.startswith('_')]
            print(f"📋 OpenRouter module contents: {openrouter_items}")
            
        except ImportError:
            print("❌ pydantic_ai.providers.openrouter does not exist")
            
    except ImportError as e:
        print(f"❌ Cannot import pydantic_ai.providers: {e}")

if __name__ == "__main__":
    asyncio.run(test_openrouter_provider_investigation())
    asyncio.run(test_openrouter_provider_multiple_models())
