#!/usr/bin/env python3
"""
Approach 8: Enhanced structured output approach based on user's sample code
Enhanced with the critical "usage": {"include": true} parameter for OpenRouter cost tracking.
"""

import os
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Enhanced Pydantic Models with OpenRouter Cost Data ---
class UsageData(BaseModel):
    """
    Model for the usage statistics of an API call with OpenRouter cost data.
    """
    completion_tokens: int = Field(..., description="Number of tokens generated in the completion.")
    prompt_tokens: int = Field(..., description="Number of tokens in the user's prompt.")
    total_tokens: int = Field(..., description="Total number of tokens used (prompt + completion).")
    cost: Optional[float] = Field(None, description="OpenRouter cost for this request")
    cost_details: Optional[dict] = Field(None, description="Detailed cost breakdown from OpenRouter")
    is_byok: Optional[bool] = Field(None, description="Whether this is a bring-your-own-key request")

class AgentResponse(BaseModel):
    """
    Model for the overall agent response, including the generated content and usage data.
    """
    output: str = Field(..., description="The generated text content from the LLM.")
    usage: UsageData = Field(..., description="The token usage data for the request.")

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print('='*70)

async def test_structured_output_approach():
    """Test the structured output approach with OpenRouter cost tracking."""
    
    print_section("APPROACH 8: STRUCTURED OUTPUT + COST TRACKING")
    
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("❌ OPENROUTER_API_KEY environment variable is not set.")
        return False
    
    print(f"✅ API Key: {openrouter_api_key[:10]}...")

    try:
        # Method 1: Try the basic approach from the sample
        print(f"\n🔬 Method 1: Basic structured output approach")
        
        agent = Agent(
            model="deepseek/deepseek-chat-v3.1",
            output_type=AgentResponse,
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        print("✅ Agent created with structured output")

        prompt = "Respond with exactly: 'Structured output test'"
        result = await agent.run(prompt=prompt)
        print(f"✅ Response received: '{result.output.output}'")
        print(f"📊 Usage: {result.output.usage}")
        
        if result.output.usage.cost and result.output.usage.cost > 0:
            print(f"💰 SUCCESS: Cost data found: ${result.output.usage.cost}")
            return True
        else:
            print(f"❌ Method 1: No cost data in structured output")
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    try:
        # Method 2: Try with model settings to inject usage parameter
        print(f"\n🔬 Method 2: Structured output + usage parameter injection")
        
        # This is where we need to figure out how to inject the usage parameter
        # Let's try different approaches
        
        # Approach 2a: Try with model_settings in agent.run()
        try:
            agent2 = Agent(
                model="deepseek/deepseek-chat-v3.1", 
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key
            )
            
            result2 = await agent2.run(
                "Respond with exactly: 'Method 2a test'",
                model_settings={"usage": {"include": True}}
            )
            print(f"✅ Method 2a worked: '{result2.output}'")
            
            # Check if we can access usage somehow
            usage = result2.usage()
            print(f"📊 Pydantic AI usage: {usage}")
            
            # Check for cost in usage details
            if hasattr(usage, 'cost'):
                print(f"💰 Cost found in usage: ${usage.cost}")
                return True
            elif hasattr(usage, 'details') and 'cost' in str(usage.details):
                print(f"💰 Cost found in details: {usage.details}")
                return True
            else:
                print(f"❌ Method 2a: No cost in standard usage")
                
        except Exception as e2a:
            print(f"❌ Method 2a failed: {e2a}")
        
        # Approach 2b: Try with extra_body
        try:
            result2b = await agent2.run(
                "Respond with exactly: 'Method 2b test'",
                model_settings={"extra_body": {"usage": {"include": True}}}
            )
            print(f"✅ Method 2b worked: '{result2b.output}'")
            
            usage2b = result2b.usage()
            print(f"📊 Usage with extra_body: {usage2b}")
            
            if hasattr(usage2b, 'cost') and usage2b.cost > 0:
                print(f"💰 SUCCESS: Method 2b found cost: ${usage2b.cost}")
                return True
            else:
                print(f"❌ Method 2b: No cost data")
                
        except Exception as e2b:
            print(f"❌ Method 2b failed: {e2b}")
    
    except Exception as e:
        print(f"❌ Method 2 setup failed: {e}")
    
    try:
        # Method 3: Combine with our working OpenAI SDK approach
        print(f"\n🔬 Method 3: Hybrid - OpenAI SDK call + Pydantic validation")
        
        from openai import AsyncOpenAI
        import json
        
        # Make the call with OpenAI SDK (we know this works for cost)
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        
        openai_response = await client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[{"role": "user", "content": "Respond with exactly: 'Hybrid method test'"}],
            max_tokens=50,
            extra_body={"usage": {"include": True}}
        )
        
        print(f"✅ OpenAI SDK call successful")
        content = openai_response.choices[0].message.content
        usage_raw = openai_response.usage
        
        # Create our structured data
        usage_data = UsageData(
            completion_tokens=usage_raw.completion_tokens,
            prompt_tokens=usage_raw.prompt_tokens,
            total_tokens=usage_raw.total_tokens,
            cost=getattr(usage_raw, 'cost', 0.0),
            cost_details=getattr(usage_raw, 'cost_details', {}),
            is_byok=getattr(usage_raw, 'is_byok', False)
        )
        
        response = AgentResponse(
            output=content,
            usage=usage_data
        )
        
        print(f"✅ Hybrid method response: '{response.output}'")
        print(f"💰 Hybrid cost data: ${response.usage.cost}")
        print(f"📊 Full usage: {response.usage}")
        
        if response.usage.cost > 0:
            print(f"🎯 SUCCESS: Hybrid method works!")
            print(f"  ✅ We get the OpenRouter cost data: ${response.usage.cost}")
            print(f"  ✅ We get structured Pydantic validation")
            print(f"  ✅ We can integrate this with Pydantic AI agents")
            return True
        
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    return False

async def test_production_implementation():
    """Test how this would work in production with our agent system."""
    
    print_section("PRODUCTION IMPLEMENTATION TEST")
    
    try:
        # This shows how we could integrate the working hybrid approach
        # with our existing agent system
        
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            return False
        
        from openai import AsyncOpenAI
        
        async def enhanced_agent_call(prompt: str, system_prompt: str = "You are a helpful assistant."):
            """
            Enhanced agent call that gets both Pydantic AI features AND OpenRouter costs.
            """
            
            # Make the call with cost tracking
            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key
            )
            
            response = await client.chat.completions.create(
                model="deepseek/deepseek-chat-v3.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                extra_body={"usage": {"include": True}}
            )
            
            # Extract the data
            content = response.choices[0].message.content
            usage_raw = response.usage
            
            # Create structured response
            usage_data = UsageData(
                completion_tokens=usage_raw.completion_tokens,
                prompt_tokens=usage_raw.prompt_tokens, 
                total_tokens=usage_raw.total_tokens,
                cost=getattr(usage_raw, 'cost', 0.0),
                cost_details=getattr(usage_raw, 'cost_details', {}),
                is_byok=getattr(usage_raw, 'is_byok', False)
            )
            
            return AgentResponse(output=content, usage=usage_data)
        
        # Test the production function
        result = await enhanced_agent_call(
            "What is the capital of France?",
            "You are a geography expert."
        )
        
        print(f"✅ Production test successful:")
        print(f"  📝 Response: '{result.output}'")
        print(f"  💰 Cost: ${result.usage.cost}")
        print(f"  🔢 Tokens: {result.usage.total_tokens}")
        print(f"  📊 Details: {result.usage.cost_details}")
        
        return result.usage.cost > 0
        
    except Exception as e:
        print(f"❌ Production test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing structured output approach with OpenRouter cost tracking!")
    
    success = asyncio.run(test_structured_output_approach())
    print(f"\n🎯 APPROACH 8 RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print(f"\n🚀 Testing production implementation...")
        prod_success = asyncio.run(test_production_implementation())
        
        if prod_success:
            print(f"\n🏆 PRODUCTION-READY SOLUTION FOUND!")
            print(f"✅ Structured Pydantic output validation")
            print(f"✅ Real OpenRouter cost tracking")
            print(f"✅ Clean, maintainable code")
            print(f"✅ Ready for integration with our agent system!")
