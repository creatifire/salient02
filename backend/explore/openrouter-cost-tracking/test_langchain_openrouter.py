#!/usr/bin/env python3
"""
Quick test: LangChain + OpenRouter cost tracking accuracy
vs our proven OpenAI SDK approach.
"""

import asyncio
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

async def test_langchain_vs_custom():
    """Compare LangChain cost tracking vs our custom solution."""
    
    print("🔍 LANGCHAIN vs CUSTOM SOLUTION COST TRACKING")
    print("="*60)
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ No API key")
        return
    
    test_message = "What is the capital of France? Be concise."
    
    # Method 1: Our proven custom approach
    print("\n💰 METHOD 1: Our Custom OpenAI SDK Approach")
    print("-" * 40)
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[{"role": "user", "content": test_message}],
            extra_body={"usage": {"include": True}}
        )
        
        custom_cost = getattr(response.usage, 'cost', 0.0)
        custom_tokens = response.usage.total_tokens
        custom_response = response.choices[0].message.content
        
        print(f"✅ Custom Response: '{custom_response}'")
        print(f"💵 Custom Cost: ${custom_cost}")
        print(f"🔢 Custom Tokens: {custom_tokens}")
        
    except Exception as e:
        print(f"❌ Custom approach failed: {e}")
        return
    
    # Method 2: LangChain approach
    print(f"\n🦜 METHOD 2: LangChain + OpenRouter")
    print("-" * 40)
    
    try:
        # Test if LangChain is available
        from langchain_openai import ChatOpenAI
        from langchain_community.callbacks.manager import get_openai_callback
        print("✅ LangChain available")
        
        # Setup LangChain with OpenRouter
        llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model="deepseek/deepseek-chat-v3.1"
        )
        
        # Make the call with cost tracking
        with get_openai_callback() as cb:
            langchain_response = await llm.ainvoke(test_message)
            langchain_cost = cb.total_cost
            langchain_tokens = cb.total_tokens
        
        print(f"✅ LangChain Response: '{langchain_response.content}'")
        print(f"💵 LangChain Cost: ${langchain_cost}")
        print(f"🔢 LangChain Tokens: {langchain_tokens}")
        
        # Compare accuracy
        print(f"\n📊 COMPARISON:")
        print(f"Custom Cost:    ${custom_cost}")
        print(f"LangChain Cost: ${langchain_cost}")
        
        if custom_cost > 0 and langchain_cost > 0:
            accuracy = (langchain_cost / custom_cost) * 100
            print(f"LangChain Accuracy: {accuracy:.1f}%")
            
            if accuracy > 95:
                print(f"🎯 EXCELLENT: LangChain cost tracking is highly accurate!")
                return "langchain_excellent"
            elif accuracy > 85:
                print(f"✅ GOOD: LangChain cost tracking is good enough")
                return "langchain_good"
            else:
                print(f"⚠️  MODERATE: Significant difference in cost tracking")
                return "langchain_moderate"
        else:
            print(f"❌ One of the methods didn't return cost data")
            return "inconclusive"
            
    except Exception as e:
        print(f"❌ LangChain approach failed: {e}")
        print(f"   This might be due to missing dependencies")
        return "langchain_failed"

async def show_langchain_complex_example():
    """Show what complex agents look like in LangChain."""
    
    print(f"\n🚀 LANGCHAIN COMPLEX AGENT EXAMPLE")
    print("="*40)
    
    example_code = '''
# LangChain Complex Agent Example
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.callbacks import get_openai_callback

# Define custom tools
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Your web search implementation
    return f"Search results for: {query}"

@tool 
def calculate(expression: str) -> float:
    """Perform mathematical calculations."""
    try:
        return eval(expression)  # Be careful with eval in production!
    except:
        return "Invalid expression"

# Setup LLM with OpenRouter
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="deepseek/deepseek-chat-v3.1"
)

# Create agent with tools
tools = [search_web, calculate]
agent = create_react_agent(llm, tools)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Execute with cost tracking
with get_openai_callback() as cb:
    result = agent_executor.invoke({
        "input": "Search for the population of Tokyo, then calculate the population density if the area is 2,194 km²"
    })
    
    print(f"Result: {result}")
    print(f"Total cost: ${cb.total_cost}")
    print(f"Total tokens: {cb.total_tokens}")
'''
    
    print("📝 This is what you get with LangChain:")
    print("✅ Multi-step reasoning (ReAct pattern)")
    print("✅ Tool calling and custom functions") 
    print("✅ Built-in cost tracking")
    print("✅ Error handling and retries")
    print("✅ Memory and conversation state")
    print("✅ Production-ready agent execution")
    print()
    print("🎯 Perfect for your complex agent needs!")

if __name__ == "__main__":
    result = asyncio.run(test_langchain_vs_custom())
    
    print(f"\n🎯 FINAL RECOMMENDATION:")
    
    if result == "langchain_excellent":
        print("🏆 USE LANGCHAIN!")
        print("   ✅ Excellent cost tracking accuracy")
        print("   ✅ All complex agent capabilities")
        print("   ✅ Best of both worlds!")
        
    elif result == "langchain_good": 
        print("✅ LANGCHAIN IS GOOD!")
        print("   ✅ Good enough cost tracking for most use cases")
        print("   ✅ Excellent complex agent capabilities")
        print("   💡 Consider hybrid approach for critical billing")
        
    elif result == "langchain_failed":
        print("🔧 INSTALL LANGCHAIN TO TEST:")
        print("   pip install langchain langchain-openai")
        print("   Then run this test again")
        
    else:
        print("🤔 HYBRID APPROACH RECOMMENDED:")
        print("   ✅ Use our custom solution for simple agents (perfect costs)")
        print("   ✅ Use LangChain for complex agents (good enough costs)")
    
    asyncio.run(show_langchain_complex_example())
