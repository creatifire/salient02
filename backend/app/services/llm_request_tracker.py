"""
LLM Request Tracker service for comprehensive cost management and usage tracking.

This service provides centralized tracking of all LLM requests across agent types,
capturing detailed information for billing, performance monitoring, and debugging.

Key Features:
- Token usage tracking from Pydantic AI result objects
- Cost calculation and storage for billing analysis  
- Performance metrics (latency) for monitoring
- Request/response sanitization for privacy
- Error handling for billable vs non-billable failures
- Integration with existing database and session management

Architecture:
The LLMRequestTracker follows the established service pattern used by MessageService
and SessionService, providing both a service class and a wrapper function for
easy integration with agent functions.

Usage:
    # Direct service usage
    tracker = LLMRequestTracker()
    llm_request_id = await tracker.track_llm_request(...)
    
    # Wrapper function for agent calls
    result, llm_request_id = await track_llm_call(
        agent.run, session_id, message, deps=session_deps
    )

Dependencies:
- LLMRequest model for database persistence
- DatabaseService for async session management  
- Pydantic AI for usage data extraction
- UUID and datetime for request identification and timing
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



from typing import Dict, Any, Optional, Tuple
from uuid import UUID
import uuid
from datetime import datetime, UTC

from loguru import logger

from ..models.llm_request import LLMRequest
from ..database import get_database_service


class LLMRequestTracker:
    """Shared service for tracking all LLM requests across agent types."""
    
    def __init__(self):
        """Initialize tracker with default account and agent IDs for Phase 1."""
        # Default account and agent for Phase 1 (single account)
        self.DEFAULT_ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000000001")
        self.DEFAULT_AGENT_INSTANCE_ID = UUID("00000000-0000-0000-0000-000000000002")
    
    async def track_llm_request(
        self,
        session_id: UUID,
        provider: str,
        model: str,
        request_body: Dict[str, Any],
        response_body: Dict[str, Any],
        tokens: Dict[str, int],  # {"prompt": 150, "completion": 75, "total": 225}
        cost_data: Dict[str, float],  # OpenRouter actuals: unit costs + computed total
        latency_ms: int,
        # Denormalized fields for fast billing queries (no JOINs needed)
        account_id: UUID,
        account_slug: str,
        agent_instance_slug: str,
        agent_type: str,
        # Optional parameters (with defaults)
        agent_instance_id: Optional[UUID] = None,
        completion_status: str = "complete",
        error_metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Track a complete LLM request with all billing and performance data.
        
        Args:
            session_id: The chat session this request belongs to
            provider: LLM provider identifier (e.g., "openrouter")
            model: Model identifier (e.g., "deepseek/deepseek-chat-v3.1")
            request_body: Sanitized request payload for debugging
            response_body: Response metadata including headers and usage stats
            tokens: Token usage breakdown from Pydantic AI
            cost_data: Cost information from OpenRouter or computed
            latency_ms: Request duration in milliseconds
            agent_instance_id: Optional agent identifier for multi-agent tracking
            account_id: Account UUID (denormalized for fast billing queries)
            account_slug: Account slug (denormalized for fast billing queries)
            agent_instance_slug: Agent instance slug (denormalized for fast billing queries)
            agent_type: Agent type identifier (denormalized for fast billing queries)
            completion_status: Status of LLM request completion (default: "complete")
                Values: "complete", "partial", "error", "timeout"
            error_metadata: Error information for failed requests
            
        Returns:
            UUID: The llm_request.id for linking with messages
            
        Raises:
            Exception: If database operations fail (logged but not re-raised)
        """
        
        # Use defaults for Phase 1 (single account)
        agent_id = agent_instance_id or self.DEFAULT_AGENT_INSTANCE_ID
        
        # Store full request/response bodies for debugging
        # TODO: Add sanitization option via config flag for production
        final_request = request_body.copy() if request_body else {}
        final_response = response_body.copy() if response_body else {}
        
        # Add error metadata if present
        if error_metadata:
            final_response["error_metadata"] = error_metadata
        
        # Create LLM request record
        llm_request = LLMRequest(
            session_id=session_id,
            agent_instance_id=agent_instance_id,  # Multi-tenant: track which agent made the request
            provider=provider,
            model=model,
            request_body=final_request,
            response_body=final_response,
            prompt_tokens=tokens.get("prompt", 0),
            completion_tokens=tokens.get("completion", 0),
            total_tokens=tokens.get("total", 0),
            prompt_cost=cost_data.get("prompt_cost", 0.0),
            completion_cost=cost_data.get("completion_cost", 0.0),
            total_cost=cost_data.get("total_cost", 0.0),
            latency_ms=latency_ms,
            # Denormalized fields for fast billing queries
            account_id=account_id,
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug,
            agent_type=agent_type,
            completion_status=completion_status,
            created_at=datetime.now(UTC)
        )
        
        # Save to database using existing database service pattern
        db_service = get_database_service()
        try:
            async with db_service.get_session() as session:
                session.add(llm_request)
                await session.commit()
                await session.refresh(llm_request)
        except Exception as e:
            logger.error({
                "event": "llm_request_tracking_failed",
                "session_id": str(session_id),
                "provider": provider,
                "model": model,
                "error": str(e),
                "error_type": type(e).__name__
            })
            # Don't re-raise - tracking failures shouldn't block agent responses
            # Return a placeholder UUID for consistency
            return uuid.uuid4()
        
        # Log successful tracking for monitoring
        logger.info({
            "event": "llm_request_tracked",
            "session_id": str(session_id),
            "agent_instance_id": str(agent_id),
            "provider": provider,
            "model": model,
            "total_tokens": tokens.get("total", 0),
            "computed_cost": cost_data.get("total_cost", 0.0),
            "latency_ms": latency_ms,
            "llm_request_id": str(llm_request.id),
            # Denormalized attribution for debugging
            "account_slug": account_slug,
            "agent_instance_slug": agent_instance_slug,
            "agent_type": agent_type,
            "completion_status": completion_status
        })
        
        return llm_request.id
    
    def _sanitize_request_body(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize request body by removing sensitive data while preserving structure.
        
        Args:
            request_body: Original request payload
            
        Returns:
            Dict: Sanitized request with content redacted but structure preserved
        """
        if not request_body:
            return {"sanitized": True, "reason": "empty_request"}
        
        # For now, use simplified sanitization
        # In production, this would intelligently redact PII while preserving structure
        sanitized = {
            "messages_count": len(request_body.get("messages", [])),
            "temperature": request_body.get("temperature"),
            "max_tokens": request_body.get("max_tokens"),
            "model": request_body.get("model"),
            "sanitized": True
        }
        
        return sanitized
    
    def _sanitize_response_body(self, response_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize response body by removing sensitive content while preserving metadata.
        
        Args:
            response_body: Original response payload
            
        Returns:
            Dict: Sanitized response with content redacted but metadata preserved
        """
        if not response_body:
            return {"sanitized": True, "reason": "empty_response"}
        
        # Preserve important metadata while redacting content
        sanitized = {
            "model": response_body.get("model"),
            "usage": response_body.get("usage"),
            "headers": {
                "x-ratelimit-remaining": response_body.get("headers", {}).get("x-ratelimit-remaining"),
                "x-ratelimit-limit": response_body.get("headers", {}).get("x-ratelimit-limit")
            },
            "sanitized": True
        }
        
        # Remove None values
        return {k: v for k, v in sanitized.items() if v is not None}


# Wrapper function for all agents
async def track_llm_call(
    agent_function,
    session_id: UUID,
    *args,
    **kwargs
) -> Tuple[Any, UUID]:
    """
    Wrapper function that tracks any LLM agent call with comprehensive monitoring.
    
    This function wraps any agent function call to automatically track token usage,
    costs, performance metrics, and error conditions for billing and monitoring.
    
    Args:
        agent_function: The agent function to call (e.g., agent.run)
        session_id: Session UUID for tracking and billing
        *args: Positional arguments to pass to the agent function
        **kwargs: Keyword arguments to pass to the agent function
        
    Returns:
        Tuple[Any, UUID]: (agent_result, llm_request_id)
        
    Usage:
        result, llm_request_id = await track_llm_call(
            agent.run, session_id, message, deps=session_deps
        )
        
    Error Handling:
        - Non-billable errors: Re-raised without tracking
        - Billable errors: Tracked with error metadata then re-raised
        - Tracking failures: Logged but don't block agent responses
    """
    tracker = LLMRequestTracker()
    start_time = datetime.utcnow()
    
    try:
        # Make the actual LLM call
        from loguru import logger
        logger.info("WRAPPER DEBUG: Starting agent function call")
        result = await agent_function(*args, **kwargs)
        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        logger.info(f"WRAPPER DEBUG: Agent call completed in {latency_ms}ms")
        
        # Extract tracking data from result (Pydantic AI provides usage info)
        usage_data = result.usage() if hasattr(result, 'usage') else {}
        logger.info(f"WRAPPER DEBUG: Usage data extracted: {usage_data}")
        
        # Build token usage dictionary
        tokens = {
            "prompt": usage_data.get("input_tokens", 0),  # Pydantic AI uses input_tokens
            "completion": usage_data.get("output_tokens", 0),  # Pydantic AI uses output_tokens  
            "total": usage_data.get("total_tokens", 0)
        }
        logger.info(f"WRAPPER DEBUG: Token data built: {tokens}")
        
        # Extract cost data from usage (OpenRouter provides actual costs)
        cost_data = {
            "unit_cost_prompt": 0.0,  # Will be enhanced when OpenRouter cost data available
            "unit_cost_completion": 0.0,
            "total_cost": 0.0
        }
        
        # Build request/response data for tracking
        request_data = {
            "messages": "redacted",  # Simplified for now
            "model": kwargs.get("model", "unknown"),
            "temperature": kwargs.get("temperature"),
            "max_tokens": kwargs.get("max_tokens")
        }
        
        response_data = {
            "model": usage_data.get("model", "unknown"),
            "usage": usage_data
        }
        
        # Track the successful request
        logger.info(f"WRAPPER DEBUG: Calling tracker.track_llm_request with session_id={session_id}")
        llm_request_id = await tracker.track_llm_request(
            session_id=session_id,
            provider="openrouter",  # Will be configurable later
            model=usage_data.get("model", "unknown"),
            request_body=request_data,
            response_body=response_data,
            tokens=tokens,
            cost_data=cost_data,
            latency_ms=latency_ms
        )
        logger.info(f"WRAPPER DEBUG: LLM request tracked successfully: {llm_request_id}")
        
        return result, llm_request_id
        
    except Exception as e:
        # Calculate latency for failed requests
        from loguru import logger
        logger.error(f"WRAPPER DEBUG: Exception caught in track_llm_call: {e}")
        logger.error(f"WRAPPER DEBUG: Exception type: {type(e)}")
        import traceback
        logger.error(f"WRAPPER DEBUG: Full traceback: {traceback.format_exc()}")
        
        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Determine if error is billable (consumed tokens/resources)
        error_metadata = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "billable": _is_billable_error(e)
        }
        
        # Track error if billable (consumed resources)
        if error_metadata["billable"]:
            await tracker.track_llm_request(
                session_id=session_id,
                provider="openrouter",
                model="unknown",
                request_body={"error": "failed_request"},
                response_body={"error": str(e)},
                tokens={"prompt": 0, "completion": 0, "total": 0},  # May be updated if partial
                cost_data={"total_cost": 0.0},
                latency_ms=latency_ms,
                error_metadata=error_metadata
            )
        
        # Re-raise the exception - tracking shouldn't suppress errors
        raise


def _is_billable_error(error: Exception) -> bool:
    """
    Determine if an error represents a billable LLM request failure.
    
    Args:
        error: The exception that occurred
        
    Returns:
        bool: True if the error likely consumed tokens/resources
    """
    error_str = str(error).lower()
    
    # These errors typically indicate the request reached the LLM and consumed tokens
    billable_indicators = [
        "timeout",           # Request timed out after reaching LLM
        "rate_limit",        # Hit rate limits (implies successful connection)
        "content_filter",    # Content was filtered (after processing)
        "context_length",    # Context too long (after tokenization)
        "insufficient_quota" # Quota exceeded (implies usage was tracked)
    ]
    
    return any(indicator in error_str for indicator in billable_indicators)


# Global service instance (singleton pattern)
_llm_request_tracker: Optional[LLMRequestTracker] = None


def get_llm_request_tracker() -> LLMRequestTracker:
    """
    Get the global LLM request tracker instance using singleton pattern.
    
    Returns:
        LLMRequestTracker: The global tracker instance
    """
    global _llm_request_tracker
    if _llm_request_tracker is None:
        _llm_request_tracker = LLMRequestTracker()
    return _llm_request_tracker
