"""
FastAPI router for agent endpoints.

This module provides RESTful endpoints for interacting with AI agents,
with comprehensive session handling, message persistence, and error handling.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from loguru import logger
from typing import Optional, List

from app.agents.simple_chat import simple_chat
from app.middleware.simple_session_middleware import get_current_session
from app.services.message_service import get_message_service
from app.config import load_config
from pydantic_ai.messages import ModelMessage

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    message_history: Optional[List[ModelMessage]] = None

@router.post("/agents/simple-chat/chat", response_class=PlainTextResponse)
async def simple_chat_endpoint(
    chat_request: ChatRequest, 
    request: Request
) -> PlainTextResponse:
    """
    Simple chat endpoint with comprehensive legacy feature integration.
    
    Integrates:
    - Session handling from legacy implementation
    - Message persistence before/after LLM call
    - Configuration loading from app.yaml
    - Comprehensive logging
    - Error handling with graceful degradation
    - Input validation and security
    """
    
    # 1. SESSION HANDLING - Extract and validate session
    session = get_current_session(request)
    if not session:
        logger.error("No session available for simple chat request")
        return PlainTextResponse("Session error", status_code=500)
    
    # 2. INPUT VALIDATION & SECURITY
    message = str(chat_request.message or "").strip()
    if not message:
        logger.warning(f"Empty message from session {session.id}")
        return PlainTextResponse("", status_code=400)
    
    # 3. CONFIGURATION LOADING
    config = load_config()
    llm_config = config.get("llm", {})
    
    # 4. COMPREHENSIVE LOGGING - Request
    logger.info({
        "event": "simple_chat_request",
        "path": "/agents/simple-chat/chat",
        "session_id": str(session.id),
        "session_key": session.session_key[:8] + "..." if session.session_key else None,
        "message_preview": message[:100] + "..." if len(message) > 100 else message,
        "model": f"{llm_config.get('provider', 'openrouter')}:{llm_config.get('model', 'deepseek/deepseek-chat-v3.1')}",
        "temperature": llm_config.get("temperature", 0.3),
        "max_tokens": llm_config.get("max_tokens", 1024)
    })
    
    # 5. MESSAGE PERSISTENCE - Before LLM call
    message_service = get_message_service()
    user_message_id = None
    
    try:
        user_message_id = await message_service.save_message(
            session_id=session.id,
            role="human",
            content=message,
            metadata={"source": "simple_chat", "agent_type": "simple_chat"}
        )
        logger.info({
            "event": "user_message_saved",
            "session_id": str(session.id),
            "message_id": str(user_message_id),
            "content_length": len(message)
        })
    except Exception as e:
        # ERROR HANDLING - Database failures don't block chat
        logger.error({
            "event": "user_message_save_failed",
            "session_id": str(session.id),
            "error": str(e),
            "error_type": type(e).__name__
        })
    
    try:
        # 6. PYDANTIC AI AGENT CALL - Simple and clean
        result = await simple_chat(
            message=message, 
            session_id=str(session.id),
            message_history=chat_request.message_history
        )
        
        # 7. MESSAGE PERSISTENCE - After LLM completion
        try:
            # Prepare metadata with JSON-serializable usage data
            usage_data = result.get('usage', {})
            if hasattr(usage_data, '__dict__'):
                # Convert Pydantic models to dict for JSON serialization
                usage_data = usage_data.__dict__
            elif hasattr(usage_data, 'dict'):
                # Use Pydantic .dict() method if available
                usage_data = usage_data.dict()
            
            assistant_message_id = await message_service.save_message(
                session_id=session.id,
                role="assistant",
                content=result['response'],
                metadata={
                    "source": "simple_chat",
                    "agent_type": "simple_chat",
                    "user_message_id": str(user_message_id) if user_message_id else None,
                    "usage": usage_data
                }
            )
            
            # 8. COMPREHENSIVE LOGGING - Success
            logger.info({
                "event": "assistant_message_saved",
                "session_id": str(session.id),
                "message_id": str(assistant_message_id),
                "user_message_id": str(user_message_id) if user_message_id else None,
                "content_length": len(result['response']),
                "usage": result.get('usage', {}),
                "agent_type": "simple_chat"
            })
        except Exception as e:
            # ERROR HANDLING - Database failures don't block response
            logger.error({
                "event": "assistant_message_save_failed",
                "session_id": str(session.id),
                "user_message_id": str(user_message_id) if user_message_id else None,
                "error": str(e),
                "error_type": type(e).__name__
            })
        
        # Return plain text response like legacy implementation
        return PlainTextResponse(result['response'])
        
    except Exception as e:
        # ERROR HANDLING & GRACEFUL DEGRADATION - LLM failures
        logger.error({
            "event": "simple_chat_agent_failed",
            "session_id": str(session.id),
            "user_message_id": str(user_message_id) if user_message_id else None,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return PlainTextResponse("Sorry, I'm having trouble responding right now.", status_code=500)
