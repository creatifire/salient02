import os
import asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file at project root
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir.parent / ".env")

class SimpleResponse(BaseModel):
    """Simple response model for testing."""
    message: str = Field(..., description="The response message")

async def test_pydantic_ai_together():
    """
    Test Pydantic AI with Together.ai to see if we can get usage data.
    """
    together_api_key = os.getenv("TOGETHER_API_KEY")
    
    if not together_api_key:
        print("❌ TOGETHER_API_KEY not found in environment variables")
        return
    
    print("🦜 Testing Pydantic AI + Together.ai Integration")
    print("=" * 55)
    
    try:
        # Configure Pydantic AI for Together.ai
        provider = OpenAIProvider(
            base_url="https://api.together.xyz/v1",
            api_key=together_api_key
        )
        
        model_instance = OpenAIChatModel(
            model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            provider=provider
        )
        
        agent = Agent(
            model=model_instance,
            output_type=SimpleResponse,
        )
        
        # Run the agent
        result = await agent.run("Say hello in exactly 3 words")
        
        print("✅ Pydantic AI + Together.ai works!")
        print(f"📝 Response: '{result.output.message}'")
        
        # Check usage data (discovered that usage is a method!)
        usage_data = result.usage()
        print(f"\n🎯 USAGE DATA FOUND!")
        print(f"📊 Usage type: {type(usage_data)}")
        print(f"📊 Usage: {usage_data}")
        
        # Check token fields
        print(f"✅ Prompt tokens: {usage_data.input_tokens}")
        print(f"✅ Completion tokens: {usage_data.output_tokens}")
        print(f"✅ Total tokens: {usage_data.total_tokens}")
        
        # Check for cost data
        if hasattr(usage_data, 'details') and usage_data.details:
            print(f"📋 Details: {usage_data.details}")
            if 'cost' in usage_data.details:
                print(f"💰 Cost found: {usage_data.details['cost']}")
            else:
                print("❌ No cost in details")
        else:
            print("❌ No details field or empty details")
            
        # Check for any cost-related attributes
        cost_attrs = [attr for attr in dir(usage_data) if 'cost' in attr.lower()]
        if cost_attrs:
            print(f"💰 Cost-related attributes: {cost_attrs}")
        else:
            print("❌ No cost-related attributes found")
        
        print(f"\n🎯 CONCLUSION: Together.ai + Pydantic AI = Great token data, no cost data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_pydantic_ai_together())
