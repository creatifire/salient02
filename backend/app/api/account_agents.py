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

from ..agents.instance_loader import load_agent_instance, list_account_instances
from ..middleware.simple_session_middleware import get_current_session
from ..database import get_database_service

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

