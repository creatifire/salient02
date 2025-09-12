import os
import asyncio
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file at project root
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir.parent / ".env")

async def test_together_ai_api():
    """
    Test Together.ai API to see what usage/cost information they provide in responses.
    """
    together_api_key = os.getenv("TOGETHER_API_KEY")
    
    if not together_api_key:
        print("❌ TOGETHER_API_KEY not found in environment variables")
        print("Please add TOGETHER_API_KEY to your .env file")
        return
    
    print("🔧 Testing Together.ai API Response Structure")
    print("=" * 60)
    
    # Create client configured for Together.ai
    client = AsyncOpenAI(
        base_url="https://api.together.xyz/v1",
        api_key=together_api_key,
    )
    
    try:
        # Make a simple request
        response = await client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[
                {"role": "user", "content": "Say hello in exactly 5 words."}
            ],
            max_tokens=20,
            temperature=0.7,
        )
        
        print("✅ Successfully got response from Together.ai")
        print(f"📝 Response: '{response.choices[0].message.content}'")
        
        # Check if there's a usage object
        if hasattr(response, 'usage') and response.usage:
            print("\n🎯 USAGE OBJECT FOUND!")
            print("-" * 30)
            print(f"Usage object type: {type(response.usage)}")
            print(f"Usage object: {response.usage}")
            
            # Check individual fields
            if hasattr(response.usage, 'prompt_tokens'):
                print(f"✅ Prompt tokens: {response.usage.prompt_tokens}")
            if hasattr(response.usage, 'completion_tokens'):
                print(f"✅ Completion tokens: {response.usage.completion_tokens}")
            if hasattr(response.usage, 'total_tokens'):
                print(f"✅ Total tokens: {response.usage.total_tokens}")
            if hasattr(response.usage, 'cost'):
                print(f"💰 Cost: {response.usage.cost}")
            elif hasattr(response.usage, 'total_cost'):
                print(f"💰 Total cost: {response.usage.total_cost}")
            else:
                print("❌ No cost field found")
                
            # Print all available attributes
            print(f"📊 All usage attributes: {dir(response.usage)}")
        else:
            print("\n❌ NO USAGE OBJECT FOUND")
            
        # Print the raw response structure
        print(f"\n🔍 Raw response type: {type(response)}")
        print(f"🔍 Raw response attributes: {dir(response)}")
        
        # Try to convert to dict to see full structure
        try:
            response_dict = response.model_dump()
            print(f"\n📋 FULL RESPONSE STRUCTURE:")
            print(json.dumps(response_dict, indent=2, default=str))
        except Exception as e:
            print(f"❌ Could not convert response to dict: {e}")
            
    except Exception as e:
        print(f"❌ Error calling Together.ai API: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_together_ai_api())
