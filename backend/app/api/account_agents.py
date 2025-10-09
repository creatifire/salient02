"""
Multi-tenant Account-Agent Instance Router.

This module provides RESTful endpoints for interacting with agent instances
within the multi-tenant account-agent-instance architecture.

URL Structure:
    /accounts/{account_slug}/agents/{instance_slug}/*

Key Features:
- Account-scoped agent instances with isolation
- Dynamic agent loading from database + config files
- Session management with account/instance attribution
- Cost tracking per account/instance
- Support for multiple agent types (simple_chat, sales_agent, etc.)

Endpoints:
- GET  /accounts/{account}/agents - List agent instances for an account
- POST /accounts/{account}/agents/{instance}/chat - Non-streaming chat
- GET  /accounts/{account}/agents/{instance}/stream - Streaming chat (SSE)
- GET  /accounts/{account}/agents/health - Health check for router

Dependencies:
- instance_loader: Load agent instances from DB + config files
- SimpleSessionMiddleware: Session management with account/instance context
- MessageService: Message persistence with agent_instance_id attribution
- LLMRequestTracker: Cost tracking with account/instance attribution
"""

from fastapi import APIRouter, Request, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..agents.instance_loader import load_agent_instance, list_account_instances
from ..middleware.simple_session_middleware import get_current_session
from ..database import get_database_service
from ..services.message_service import get_message_service

# Create router instance with prefix and tags
router = APIRouter(
    prefix="/accounts",
    tags=["multi-tenant", "agents"],
    responses={
        404: {"description": "Account or agent instance not found"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message to send to agent", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, can you help me with a question?"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Agent's response message")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage statistics")
    llm_request_id: Optional[str] = Field(None, description="LLM request tracking ID")
    cost_tracking: Optional[Dict[str, Any]] = Field(None, description="Cost tracking information")
    model: Optional[str] = Field(None, description="LLM model used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "I'd be happy to help! What would you like to know?",
                "usage": {
                    "input_tokens": 15,
                    "output_tokens": 12,
                    "total_tokens": 27
                },
                "llm_request_id": "550e8400-e29b-41d4-a716-446655440000",
                "model": "moonshotai/kimi-k2-0905"
            }
        }


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@router.get("/{account_slug}/agents/health")
async def health_check(
    account_slug: str = Path(..., description="Account identifier slug")
) -> JSONResponse:
    """
    Health check endpoint for multi-tenant agent router.
    
    Verifies:
    - Router is properly registered and accessible
    - Account parameter extraction works
    - Basic endpoint functionality
    
    Args:
        account_slug: Account identifier from URL path
        
    Returns:
        JSON response with health status and account context
        
    Example:
        GET /accounts/default_account/agents/health
        -> {"status": "healthy", "account": "default_account", "router": "account-agents"}
    """
    logger.debug(f"Health check for account: {account_slug}")
    
    return JSONResponse({
        "status": "healthy",
        "account": account_slug,
        "router": "account-agents",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /accounts/{account}/agents/health",
            "list": "GET /accounts/{account}/agents",
            "chat": "POST /accounts/{account}/agents/{instance}/chat",
            "stream": "GET /accounts/{account}/agents/{instance}/stream"
        }
    })


# ============================================================================
# CHAT ENDPOINT (NON-STREAMING)
# ============================================================================

@router.post("/{account_slug}/agents/{instance_slug}/chat")
async def chat_endpoint(
    chat_request: ChatRequest,
    request: Request,
    account_slug: str = Path(..., description="Account identifier slug"),
    instance_slug: str = Path(..., description="Agent instance identifier slug")
) -> JSONResponse:
    """
    Non-streaming chat endpoint for multi-tenant agent instances.
    
    Handles complete chat interactions with comprehensive session management,
    message persistence, cost tracking, and error handling.
    
    Flow:
    1. Load agent instance (DB + config file)
    2. Get/create session with account/instance context
    3. Load conversation history
    4. Route to appropriate agent based on agent_type
    5. Save user message and assistant response
    6. Track LLM request costs
    7. Return JSON response
    
    Args:
        chat_request: User message and optional parameters
        request: FastAPI request object (for session middleware)
        account_slug: Account identifier from URL
        instance_slug: Agent instance identifier from URL
        
    Returns:
        JSONResponse with agent response, usage stats, and tracking IDs
        
    Raises:
        HTTPException 404: Account or instance not found
        HTTPException 400: Invalid agent type or bad request
        HTTPException 500: Internal server error
        
    Example:
        POST /accounts/default_account/agents/simple_chat1/chat
        {"message": "Hello, can you help me?"}
        
        -> {
            "response": "Of course! What would you like help with?",
            "usage": {"input_tokens": 10, "output_tokens": 8, "total_tokens": 18},
            "llm_request_id": "550e8400-...",
            "model": "moonshotai/kimi-k2-0905"
        }
    """
    user_message = chat_request.message.strip()
    
    logger.info({
        "event": "chat_request",
        "account": account_slug,
        "instance": instance_slug,
        "message_preview": user_message[:100] + "..." if len(user_message) > 100 else user_message
    })
    
    # ========================================================================
    # STEP 1: LOAD AGENT INSTANCE
    # ========================================================================
    
    try:
        instance = await load_agent_instance(account_slug, instance_slug)
        logger.debug({
            "event": "instance_loaded",
            "instance_id": str(instance.id),
            "agent_type": instance.agent_type,
            "display_name": instance.display_name
        })
    except ValueError as e:
        # Account or instance not found
        logger.warning({
            "event": "instance_not_found",
            "account": account_slug,
            "instance": instance_slug,
            "error": str(e)
        })
        raise HTTPException(status_code=404, detail=f"Agent instance not found: {account_slug}/{instance_slug}")
    except Exception as e:
        logger.error({
            "event": "instance_load_failed",
            "account": account_slug,
            "instance": instance_slug,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail="Failed to load agent instance")
    
    # ========================================================================
    # STEP 2: GET/CREATE SESSION WITH CONTEXT UPDATE
    # ========================================================================
    
    session = get_current_session(request)
    if not session:
        logger.error("No session available for chat request")
        raise HTTPException(status_code=500, detail="Session error")
    
    logger.debug({
        "event": "session_retrieved",
        "session_id": str(session.id),
        "session_key": session.session_key[:8] + "..." if session.session_key else None,
        "account_id": str(session.account_id) if session.account_id else None
    })
    
    # Update session context if NULL (progressive context flow)
    if session.account_id is None:
        from sqlalchemy import update as sql_update
        from ..models import Session as SessionModel
        
        async with get_database_service().get_session() as db_session:
            await db_session.execute(
                sql_update(SessionModel)
                .where(SessionModel.id == session.id)
                .values(
                    account_id=instance.account_id,
                    account_slug=instance.account_slug,
                    agent_instance_id=instance.id
                )
            )
            await db_session.commit()
        
        logger.info({
            "event": "session_context_updated",
            "session_id": str(session.id),
            "account_id": str(instance.account_id),
            "agent_instance_id": str(instance.id)
        })
        
        # Update local session object for use in this request
        session.account_id = instance.account_id
        session.account_slug = instance.account_slug
        session.agent_instance_id = instance.id
    
    # ========================================================================
    # STEP 3: LOAD CONVERSATION HISTORY
    # ========================================================================
    
    # Get history_limit from instance config
    context_management = instance.config.get("context_management", {})
    history_limit = context_management.get("history_limit", 50)
    
    # Load conversation history for this session
    from ..services.agent_session import load_agent_conversation
    message_history = await load_agent_conversation(
        session_id=str(session.id),
        max_messages=history_limit
    )
    
    logger.debug({
        "event": "history_loaded",
        "session_id": str(session.id),
        "history_count": len(message_history),
        "history_limit": history_limit
    })
    
    # ========================================================================
    # STEP 4: ROUTE TO APPROPRIATE AGENT
    # ========================================================================
    
    agent_type = instance.agent_type
    
    try:
        if agent_type == "simple_chat":
            # Import and call simple_chat agent with pre-loaded history
            from ..agents.simple_chat import simple_chat
            
            result = await simple_chat(
                message=user_message,
                session_id=str(session.id),
                message_history=message_history,  # Pass pre-loaded history
                instance_config=instance.config  # Pass instance-specific config
            )
            
        # Future agent types can be added here:
        # elif agent_type == "sales_agent":
        #     from ..agents.sales_agent import sales_agent
        #     result = await sales_agent(
        #         message=user_message,
        #         session_id=str(session.id),
        #         message_history=message_history
        #     )
        
        else:
            logger.error({
                "event": "unknown_agent_type",
                "agent_type": agent_type,
                "instance": instance_slug
            })
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {agent_type}. Supported types: simple_chat"
            )
        
        logger.info({
            "event": "agent_response_generated",
            "session_id": str(session.id),
            "agent_type": agent_type,
            "response_length": len(result['response']),
            "llm_request_id": result.get('llm_request_id')
        })
        
        # NOTE: Messages and cost tracking are handled by the agent (simple_chat)
        # which uses Pydantic AI's native tracking and saves via MessageService
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error({
            "event": "agent_call_failed",
            "session_id": str(session.id),
            "agent_type": agent_type,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=500,
            detail=f"Agent processing failed: {str(e)}"
        )
    
    # ========================================================================
    # STEP 4: RETURN RESPONSE
    # ========================================================================
    
    # Format usage data for response
    usage = result.get('usage')
    usage_dict = None
    if usage:
        usage_dict = {
            "input_tokens": getattr(usage, 'input_tokens', 0),
            "output_tokens": getattr(usage, 'output_tokens', 0),
            "total_tokens": getattr(usage, 'total_tokens', 0),
            "requests": getattr(usage, 'requests', 1)
        }
    
    # Get model from instance config
    model_settings = instance.config.get("model_settings", {})
    model = model_settings.get("model", "unknown")
    
    response_data = {
        "response": result['response'],
        "usage": usage_dict,
        "llm_request_id": result.get('llm_request_id'),
        "cost_tracking": result.get('cost_tracking', {}),
        "model": model
    }
    
    logger.info({
        "event": "chat_response_complete",
        "session_id": str(session.id),
        "account": account_slug,
        "instance": instance_slug,
        "response_length": len(result['response']),
        "llm_request_id": result.get('llm_request_id')
    })
    
    return JSONResponse(response_data)

