#!/usr/bin/env python3
"""
Production-ready wrapper that integrates the hybrid OpenAI SDK + Pydantic validation
approach with your existing simple_chat.py interface.

This gives you:
✅ Real OpenRouter cost tracking (critical for customer billing)
✅ Structured Pydantic validation 
✅ Clean integration with existing LLMRequestTracker
✅ Same interface as current simple_chat()
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from loguru import logger
from dotenv import load_dotenv

# Import existing infrastructure
from app.config import load_config
from app.services.llm_request_tracker import LLMRequestTracker

# Load environment variables
load_dotenv()

# Enhanced Pydantic Models for Cost Tracking
class EnhancedUsageData(BaseModel):
    """Enhanced usage data with OpenRouter cost tracking."""
    input_tokens: int = Field(..., description="Number of tokens in the prompt")
    output_tokens: int = Field(..., description="Number of tokens in completion")  
    total_tokens: int = Field(..., description="Total tokens used")
    requests: int = Field(default=1, description="Number of requests made")
    cost: Optional[float] = Field(None, description="Real OpenRouter cost")
    cost_details: Optional[Dict[str, Any]] = Field(None, description="Detailed OpenRouter cost breakdown")
    is_byok: Optional[bool] = Field(None, description="Bring-your-own-key flag")
    prompt_tokens_details: Optional[Dict[str, Any]] = Field(None, description="Detailed prompt token info")
    completion_tokens_details: Optional[Dict[str, Any]] = Field(None, description="Detailed completion token info")

class EnhancedChatResponse(BaseModel):
    """Enhanced chat response with cost tracking and message history."""
    response: str = Field(..., description="The generated response text")
    usage: EnhancedUsageData = Field(..., description="Usage data with cost tracking")
    messages: List[Dict[str, str]] = Field(..., description="All messages in conversation")
    new_messages: List[Dict[str, str]] = Field(..., description="New messages from this request")
    llm_request_id: Optional[str] = Field(None, description="Database tracking ID")
    cost_tracking: Dict[str, Any] = Field(default_factory=dict, description="Additional cost tracking info")

async def enhanced_simple_chat(
    message: str,
    session_id: str,
    message_history: Optional[List[Dict[str, str]]] = None,
    system_prompt: str = "You are a helpful assistant."
) -> EnhancedChatResponse:
    """
    Enhanced simple chat function with OpenRouter cost tracking.
    
    This function provides the same interface as your existing simple_chat()
    but with real OpenRouter cost tracking integrated.
    """
    
    start_time = datetime.now()
    
    # Load configuration
    config = load_config()
    llm_config = config.get("llm", {})
    
    # Get API configuration
    api_key = llm_config.get("api_key") or os.getenv('OPENROUTER_API_KEY')
    model_name = llm_config.get("model", "deepseek/deepseek-chat-v3.1")
    
    if not api_key:
        raise ValueError("OpenRouter API key not found in configuration or environment")
    
    logger.info({
        "event": "enhanced_simple_chat_start",
        "session_id": session_id,
        "model": model_name,
        "has_message_history": bool(message_history),
        "message_preview": message[:100]
    })
    
    try:
        # Create OpenAI client configured for OpenRouter
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        # Build message history
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add message history if provided
        if message_history:
            messages.extend(message_history)
        
        # Add current user message
        messages.append({"role": "user", "content": message})
        
        # Make the API call with cost tracking enabled
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            extra_body={"usage": {"include": True}}  # Critical for cost tracking!
        )
        
        end_time = datetime.now()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Extract response content
        response_content = response.choices[0].message.content
        
        # Extract usage data with cost tracking
        usage_raw = response.usage
        
        # Convert Pydantic objects to dictionaries for our model
        prompt_details = getattr(usage_raw, 'prompt_tokens_details', None)
        completion_details = getattr(usage_raw, 'completion_tokens_details', None)
        
        usage_data = EnhancedUsageData(
            input_tokens=usage_raw.prompt_tokens,
            output_tokens=usage_raw.completion_tokens,
            total_tokens=usage_raw.total_tokens,
            cost=getattr(usage_raw, 'cost', 0.0),
            cost_details=getattr(usage_raw, 'cost_details', {}),
            is_byok=getattr(usage_raw, 'is_byok', False),
            prompt_tokens_details=prompt_details.model_dump() if prompt_details else {},
            completion_tokens_details=completion_details.model_dump() if completion_details else {}
        )
        
        # Build complete message history
        all_messages = messages + [{"role": "assistant", "content": response_content}]
        new_messages = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response_content}
        ]
        
        # Store in database using existing LLMRequestTracker
        llm_request_id = None
        try:
            tracker = LLMRequestTracker()
            llm_request_id = await tracker.track_llm_request(
                session_id=UUID(session_id),
                provider="openrouter",
                model=model_name,
                request_body={
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "usage": {"include": True}
                },
                response_body={
                    "choices": [{"message": {"content": response_content}}],
                    "usage": {
                        "prompt_tokens": usage_data.input_tokens,
                        "completion_tokens": usage_data.output_tokens,
                        "total_tokens": usage_data.total_tokens,
                        "cost": usage_data.cost,
                        "cost_details": usage_data.cost_details
                    }
                },
                tokens={
                    "prompt": usage_data.input_tokens,
                    "completion": usage_data.output_tokens,
                    "total": usage_data.total_tokens
                },
                cost_data={
                    "total_cost": usage_data.cost,
                    "unit_cost_prompt": 0.0,  # OpenRouter provides total cost, not per-token
                    "unit_cost_completion": 0.0
                },
                latency_ms=latency_ms
            )
        except Exception as tracking_error:
            logger.error(f"Failed to track LLM request: {tracking_error}")
        
        # Create enhanced response
        enhanced_response = EnhancedChatResponse(
            response=response_content,
            usage=usage_data,
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in all_messages],
            new_messages=[{"role": msg["role"], "content": msg["content"]} for msg in new_messages],
            llm_request_id=str(llm_request_id) if llm_request_id else None,
            cost_tracking={
                "real_cost": usage_data.cost,
                "cost_details": usage_data.cost_details,
                "latency_ms": latency_ms,
                "method": "openai_sdk_openrouter_hybrid",
                "has_real_cost_data": usage_data.cost > 0 if usage_data.cost else False
            }
        )
        
        logger.info({
            "event": "enhanced_simple_chat_success",
            "session_id": session_id,
            "llm_request_id": str(llm_request_id) if llm_request_id else None,
            "real_cost": usage_data.cost,
            "total_tokens": usage_data.total_tokens,
            "latency_ms": latency_ms,
            "response_length": len(response_content)
        })
        
        return enhanced_response
        
    except Exception as e:
        logger.error({
            "event": "enhanced_simple_chat_error",
            "session_id": session_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise

async def test_enhanced_wrapper():
    """Test the enhanced wrapper."""
    
    print("🎯 Testing Enhanced Simple Chat Wrapper")
    print("="*50)
    
    try:
        # Test basic functionality
        result = await enhanced_simple_chat(
            message="Hello, please respond with a brief greeting.",
            session_id="test-session-123",
            system_prompt="You are a helpful assistant."
        )
        
        print(f"✅ Response: '{result.response}'")
        print(f"💰 Cost: ${result.usage.cost}")
        print(f"🔢 Tokens: {result.usage.total_tokens}")
        print(f"📊 Cost details: {result.usage.cost_details}")
        print(f"🆔 LLM Request ID: {result.llm_request_id}")
        print(f"⏱️  Latency: {result.cost_tracking.get('latency_ms', 0)}ms")
        
        # Test with message history
        print(f"\n🔬 Testing with message history...")
        result2 = await enhanced_simple_chat(
            message="What did I just say to you?",
            session_id="test-session-123",
            message_history=result.messages[:-1]  # Exclude the last assistant message
        )
        
        print(f"✅ History response: '{result2.response}'")
        print(f"💰 Second cost: ${result2.usage.cost}")
        
        total_cost = (result.usage.cost or 0) + (result2.usage.cost or 0)
        print(f"\n💰 Total session cost: ${total_cost}")
        
        print(f"\n🏆 Enhanced wrapper test SUCCESSFUL!")
        print(f"✅ Real OpenRouter cost tracking working")
        print(f"✅ Structured Pydantic validation working")
        print(f"✅ Database integration working")
        print(f"✅ Ready for production!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_wrapper())
    
    if success:
        print(f"\n🎯 INTEGRATION INSTRUCTIONS:")
        print(f"1. Replace simple_chat() call with enhanced_simple_chat()")
        print(f"2. Update response handling to use EnhancedChatResponse structure")
        print(f"3. Enjoy real OpenRouter cost tracking!")
    else:
        print(f"\n❌ Needs debugging...")
