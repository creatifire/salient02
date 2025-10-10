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


class AgentInstanceInfo(BaseModel):
    """Information about a single agent instance."""
    instance_slug: str = Field(..., description="Agent instance identifier slug")
    agent_type: str = Field(..., description="Type of agent (e.g., simple_chat, sales_agent)")
    display_name: str = Field(..., description="Human-readable display name")
    last_used_at: Optional[str] = Field(None, description="ISO8601 timestamp of last usage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "instance_slug": "simple_chat1",
                "agent_type": "simple_chat",
                "display_name": "Simple Chat 1",
                "last_used_at": "2025-10-10T12:34:56Z"
            }
        }


class AgentListResponse(BaseModel):
    """Response model for agent instance listing endpoint."""
    account: str = Field(..., description="Account slug")
    instances: List[AgentInstanceInfo] = Field(..., description="List of active agent instances")
    count: int = Field(..., description="Number of instances returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "account": "default_account",
                "instances": [
                    {
                        "instance_slug": "simple_chat1",
                        "agent_type": "simple_chat",
                        "display_name": "Simple Chat 1",
                        "last_used_at": "2025-10-10T12:34:56Z"
                    },
                    {
                        "instance_slug": "simple_chat2",
                        "agent_type": "simple_chat",
                        "display_name": "Simple Chat 2",
                        "last_used_at": "2025-10-10T11:20:30Z"
                    }
                ],
                "count": 2
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
# AGENT INSTANCE LISTING ENDPOINT
# ============================================================================

@router.get("/{account_slug}/agents", response_model=AgentListResponse)
async def list_agents_endpoint(
    account_slug: str = Path(..., description="Account identifier slug")
) -> AgentListResponse:
    """
    List all active agent instances for an account.
    
    Returns metadata about all active agent instances configured for the
    specified account. Useful for UI dropdowns, agent selection interfaces,
    and programmatic discovery of available agents.
    
    Args:
        account_slug: Account identifier from URL path
        
    Returns:
        AgentListResponse with list of active agent instances
        
    Raises:
        HTTPException: 404 if account not found or has no instances
        HTTPException: 500 for unexpected errors
        
    Example:
        GET /accounts/default_account/agents
        -> {
            "account": "default_account",
            "instances": [
                {
                    "instance_slug": "simple_chat1",
                    "agent_type": "simple_chat",
                    "display_name": "Simple Chat 1",
                    "last_used_at": "2025-10-10T12:34:56Z"
                },
                {
                    "instance_slug": "simple_chat2",
                    "agent_type": "simple_chat",
                    "display_name": "Simple Chat 2",
                    "last_used_at": null
                }
            ],
            "count": 2
        }
    """
    logger.info({
        "event": "list_agents_request",
        "account": account_slug
    })
    
    try:
        # Load instance metadata from database
        instances_metadata = await list_account_instances(account_slug)
        
        if not instances_metadata:
            logger.warning(f"No instances found for account: {account_slug}")
            raise HTTPException(
                status_code=404,
                detail=f"No agent instances found for account '{account_slug}'"
            )
        
        # Format instance data for response
        instances = [
            AgentInstanceInfo(
                instance_slug=inst["instance_slug"],
                agent_type=inst["agent_type"],
                display_name=inst["display_name"],
                last_used_at=inst["last_used_at"].isoformat() if inst.get("last_used_at") else None
            )
            for inst in instances_metadata
        ]
        
        logger.info({
            "event": "list_agents_success",
            "account": account_slug,
            "instance_count": len(instances)
        })
        
        return AgentListResponse(
            account=account_slug,
            instances=instances,
            count=len(instances)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except ValueError as e:
        # ValueError from list_account_instances means invalid/nonexistent account
        logger.warning(f"Invalid account: {account_slug} - {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_slug}' not found"
        )
    except Exception as e:
        logger.error({
            "event": "list_agents_error",
            "account": account_slug,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agent instances: {str(e)}"
        )


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


# ============================================================================
# STREAMING ENDPOINT (SSE)
# ============================================================================

@router.get("/{account_slug}/agents/{instance_slug}/stream")
async def stream_endpoint(
    request: Request,
    message: str = Query(..., description="User message to send to agent", min_length=1),
    account_slug: str = Path(..., description="Account identifier slug"),
    instance_slug: str = Path(..., description="Agent instance identifier slug")
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    
    Streams agent responses in real-time as they're generated, providing
    a better user experience for longer responses.
    
    SSE Event Format:
        - event: message, data: <text chunk>
        - event: done, data: ""
        - event: error, data: {"message": "<error>"}
    
    Flow:
    1. Load agent instance (DB + config file)
    2. Get/create session with account/instance context
    3. Load conversation history
    4. Route to streaming agent based on agent_type
    5. Yield SSE events as chunks arrive
    6. Save messages and track costs after completion
    7. Return completion event
    
    Args:
        request: FastAPI request object (for session middleware)
        message: User message from query parameter
        account_slug: Account identifier from URL
        instance_slug: Agent instance identifier from URL
        
    Returns:
        StreamingResponse with SSE events
        
    Raises:
        HTTPException 404: Account or instance not found
        HTTPException 400: Invalid agent type or bad request
        HTTPException 500: Internal server error
        
    Example:
        GET /accounts/default_account/agents/simple_chat1/stream?message=Hello
        
        -> event: message\ndata: Hello\n\n
        -> event: message\ndata: ! How can\n\n
        -> event: message\ndata:  I help you?\n\n
        -> event: done\ndata: \n\n
    """
    from fastapi.responses import StreamingResponse
    import json
    
    logger.info({
        "event": "stream_request",
        "account": account_slug,
        "instance": instance_slug,
        "message_preview": message[:100] + "..." if len(message) > 100 else message
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
        logger.error("No session available for stream request")
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
    # STEP 4: STREAMING GENERATOR FUNCTION
    # ========================================================================
    
    async def event_generator():
        """Generate SSE events from agent stream."""
        agent_type = instance.agent_type
        
        try:
            if agent_type == "simple_chat":
                # Import streaming function
                from ..agents.simple_chat import simple_chat_stream
                
                # Stream events from agent
                async for event in simple_chat_stream(
                    message=message,
                    session_id=str(session.id),
                    agent_instance_id=instance.id,
                    message_history=message_history,
                    instance_config=instance.config
                ):
                    # Format as SSE
                    event_type = event.get("event", "message")
                    event_data = event.get("data", "")
                    
                    # SSE format: "event: <type>\ndata: <data>\n\n"
                    yield f"event: {event_type}\ndata: {event_data}\n\n"
                
            # Future agent types can be added here:
            # elif agent_type == "sales_agent":
            #     from ..agents.sales_agent import sales_agent_stream
            #     async for event in sales_agent_stream(...):
            #         yield f"event: {event['event']}\ndata: {event['data']}\n\n"
            
            else:
                logger.error({
                    "event": "unknown_agent_type",
                    "agent_type": agent_type,
                    "instance": instance_slug
                })
                error_data = json.dumps({"message": f"Unknown agent type: {agent_type}"})
                yield f"event: error\ndata: {error_data}\n\n"
                
        except Exception as e:
            logger.error({
                "event": "streaming_exception",
                "session_id": str(session.id),
                "agent_type": agent_type,
                "error": str(e),
                "error_type": type(e).__name__
            })
            error_data = json.dumps({"message": f"Streaming failed: {str(e)}"})
            yield f"event: error\ndata: {error_data}\n\n"
    
    # ========================================================================
    # STEP 5: RETURN STREAMING RESPONSE
    # ========================================================================
    
    logger.info({
        "event": "stream_initiated",
        "session_id": str(session.id),
        "account": account_slug,
        "instance": instance_slug
    })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/{account_slug}/agents/{instance_slug}/history")
async def history_endpoint(
    request: Request,
    account_slug: str = Path(..., description="Account identifier slug"),
    instance_slug: str = Path(..., description="Agent instance identifier slug")
):
    """
    Get chat history for the current session, filtered by agent instance.
    
    Multi-tenant aware history endpoint that ensures messages are isolated
    by both session AND agent instance. This prevents cross-contamination
    when the same session cookie is used across multiple agent instances.
    
    Args:
        request: FastAPI request object (provides session context)
        account_slug: Account identifier from URL path
        instance_slug: Agent instance identifier from URL path
        
    Returns:
        JSONResponse with session_id and formatted messages array
        
    Raises:
        HTTPException: 401 if no session found
        HTTPException: 404 if account/instance not found
        HTTPException: 500 for unexpected errors
        
    Example Response:
        {
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "account": "default_account",
            "agent_instance": "simple_chat1",
            "messages": [
                {
                    "message_id": "msg-uuid",
                    "role": "user",
                    "content": "Hello",
                    "raw_content": "Hello",
                    "timestamp": "2025-10-10T12:00:00Z"
                },
                {
                    "message_id": "msg-uuid-2",
                    "role": "bot",
                    "content": "<p>Hi there!</p>",
                    "raw_content": "Hi there!",
                    "timestamp": "2025-10-10T12:00:01Z"
                }
            ],
            "count": 2
        }
    """
    logger.info({
        "event": "history_request",
        "account": account_slug,
        "instance": instance_slug
    })
    
    try:
        # ====================================================================
        # STEP 1: VALIDATE SESSION
        # ====================================================================
        session = get_current_session(request)
        if not session:
            logger.warning({
                "event": "history_no_session",
                "account": account_slug,
                "instance": instance_slug
            })
            raise HTTPException(
                status_code=401,
                detail="No session found. Please send a message first."
            )
        
        # ====================================================================
        # STEP 2: LOAD AND VALIDATE AGENT INSTANCE
        # ====================================================================
        instance_metadata = await load_account_agent_instance(
            account_slug, instance_slug
        )
        
        if not instance_metadata:
            logger.warning(f"Instance not found: {account_slug}/{instance_slug}")
            raise HTTPException(
                status_code=404,
                detail=f"Agent instance '{instance_slug}' not found for account '{account_slug}'"
            )
        
        instance = instance_metadata["instance"]
        
        # ====================================================================
        # STEP 3: LOAD HISTORY FILTERED BY SESSION + AGENT INSTANCE
        # ====================================================================
        from sqlalchemy import desc, select, and_
        from app.models.message import Message
        from app.services.database_service import get_database_service
        
        # Get configurable history limit
        from app.config import load_config
        config = load_config()
        chat_config = config.get("chat", {})
        history_limit = chat_config.get("history_limit", 50)
        
        db_service = get_database_service()
        async with db_service.get_session() as db_session:
            # Query messages filtered by BOTH session_id AND agent_instance_id
            stmt = (
                select(Message)
                .where(
                    and_(
                        Message.session_id == session.id,
                        Message.agent_instance_id == instance.id  # Multi-tenant isolation
                    )
                )
                .order_by(desc(Message.created_at))
                .limit(history_limit)
            )
            
            result = await db_session.execute(stmt)
            messages = result.scalars().all()
            
            # Reverse to chronological order (oldest first)
            messages = list(reversed(messages))
        
        # ====================================================================
        # STEP 4: FORMAT MESSAGES FOR FRONTEND
        # ====================================================================
        formatted_messages = []
        for msg in messages:
            # Skip system messages in UI history
            if msg.role == "system":
                continue
            
            # Map roles for frontend: human -> user, assistant -> bot
            display_role = "user" if msg.role == "human" else "bot"
            
            # For bot messages, render markdown if enabled
            content = msg.content
            raw_content = msg.content
            
            if display_role == "bot":
                # Bot messages: render markdown to HTML
                allow_html = config.get("ui", {}).get("allow_basic_html", True)
                if allow_html:
                    try:
                        import markdown
                        content = markdown.markdown(
                            msg.content,
                            extensions=['nl2br', 'fenced_code']
                        )
                    except Exception as e:
                        logger.warning(f"Markdown rendering failed: {e}")
                        content = msg.content
            
            formatted_messages.append({
                "message_id": str(msg.id),
                "role": display_role,
                "content": content,
                "raw_content": raw_content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            })
        
        logger.info({
            "event": "history_loaded",
            "session_id": str(session.id),
            "account": account_slug,
            "instance": instance_slug,
            "message_count": len(formatted_messages)
        })
        
        return JSONResponse({
            "session_id": str(session.id),
            "account": account_slug,
            "agent_instance": instance_slug,
            "messages": formatted_messages,
            "count": len(formatted_messages)
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error({
            "event": "history_error",
            "account": account_slug,
            "instance": instance_slug,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load chat history: {str(e)}"
        )

