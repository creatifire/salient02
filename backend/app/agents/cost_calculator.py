"""
Cost tracking and calculation utilities for LLM requests.

This module consolidates cost calculation logic using genai-prices with fallback
pricing, and provides unified LLM request tracking for both streaming and non-streaming.

Extracted from BUG-0017-009 refactoring.
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from typing import Dict, Tuple, Optional, Any
from decimal import Decimal
from uuid import UUID
from pathlib import Path
import yaml
import logfire


def calculate_streaming_costs(
    usage_data: Any,
    requested_model: str,
    session_id: str
) -> Tuple[float, float, float]:
    """
    Calculate costs for LLM usage with genai-prices + fallback pricing.
    
    Attempts to calculate costs using the genai-prices library. If the model
    is not found, falls back to config/fallback_pricing.yaml. Logs all cost
    calculations with method attribution.
    
    Args:
        usage_data: Usage data object from Pydantic AI result
        requested_model: Full model identifier (may include provider prefix)
        session_id: Session ID for logging context
        
    Returns:
        Tuple of (prompt_cost, completion_cost, total_cost) in USD
        Returns (0.0, 0.0, 0.0) if calculation fails
        
    Example:
        >>> costs = calculate_streaming_costs(result.usage(), "google/gemini-2.5-flash", "session-123")
        >>> prompt_cost, completion_cost, total_cost = costs
    """
    prompt_cost = 0.0
    completion_cost = 0.0
    total_cost = 0.0
    
    try:
        from genai_prices import calc_price
        
        # Strip provider prefix (e.g., "google/gemini-2.5-flash" → "gemini-2.5-flash")
        # genai-prices expects models without provider prefix
        model_for_pricing = requested_model.split('/')[-1] if '/' in requested_model else requested_model
        
        price = calc_price(
            usage=usage_data,
            model_ref=model_for_pricing,
            provider_id="openrouter"
        )
        
        # Extract individual costs
        prompt_cost = float(price.input_price)
        completion_cost = float(price.output_price)
        total_cost = float(price.total_price)
        
        logfire.info(
            'agent.cost_calculated',
            session_id=session_id,
            model=requested_model,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            method="genai-prices"
        )
        
    except LookupError as e:
        # Model not in genai-prices database - use fallback pricing from config
        prompt_cost, completion_cost, total_cost = _calculate_fallback_costs(
            usage_data, requested_model, session_id, str(e)
        )
        
    except Exception as e:
        logfire.warn(
            'agent.cost_calculation_failed',
            session_id=session_id,
            model=requested_model,
            error=str(e),
            error_type=type(e).__name__,
            fallback="zero_cost"
        )
    
    return prompt_cost, completion_cost, total_cost


def _calculate_fallback_costs(
    usage_data: Any,
    requested_model: str,
    session_id: str,
    lookup_error: str
) -> Tuple[float, float, float]:
    """
    Calculate costs using fallback pricing configuration.
    
    Loads pricing from config/fallback_pricing.yaml and calculates costs
    based on per-million-token rates.
    
    Args:
        usage_data: Usage data object from Pydantic AI result
        requested_model: Full model identifier
        session_id: Session ID for logging
        lookup_error: Original lookup error message
        
    Returns:
        Tuple of (prompt_cost, completion_cost, total_cost) in USD
        Returns (0.0, 0.0, 0.0) if fallback pricing not available
    """
    # Load fallback pricing from config file
    config_dir = Path(__file__).parent.parent.parent / "config"
    fallback_pricing_path = config_dir / "fallback_pricing.yaml"
    
    fallback_pricing_models = {}
    if fallback_pricing_path.exists():
        with open(fallback_pricing_path, 'r') as f:
            fallback_config = yaml.safe_load(f)
            fallback_pricing_models = fallback_config.get('models', {})
    
    if requested_model in fallback_pricing_models:
        pricing = fallback_pricing_models[requested_model]
        
        # Extract token counts from usage data
        prompt_tokens = usage_data.request_tokens if hasattr(usage_data, 'request_tokens') else 0
        completion_tokens = usage_data.response_tokens if hasattr(usage_data, 'response_tokens') else 0
        
        # Calculate costs based on per-million-token rates
        prompt_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
        completion_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
        total_cost = prompt_cost + completion_cost
        
        logfire.info(
            'agent.cost_calculated',
            session_id=session_id,
            model=requested_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            method="fallback_pricing",
            source=pricing.get("source", "unknown"),
            config_file=str(fallback_pricing_path)
        )
        
        return prompt_cost, completion_cost, total_cost
    else:
        logfire.warn(
            'agent.cost_calculation_failed',
            session_id=session_id,
            model=requested_model,
            error=f"Model not in genai-prices or fallback pricing: {lookup_error}",
            error_type="LookupError",
            fallback="zero_cost",
            suggestion=f"Add model to {fallback_pricing_path}"
        )
        
        return 0.0, 0.0, 0.0


def extract_costs_from_provider_details(
    result: Any,
    requested_model: str
) -> Tuple[float, float, float]:
    """
    Extract cost information from provider details if available.
    
    Some providers return cost information in the response. This function
    extracts that information if present.
    
    Args:
        result: Pydantic AI result object
        requested_model: Model identifier for logging
        
    Returns:
        Tuple of (prompt_cost, completion_cost, total_cost) in USD
        Returns (0.0, 0.0, 0.0) if provider details unavailable
    """
    try:
        new_messages = result.new_messages()
        if new_messages:
            latest_message = new_messages[-1]
            if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
                provider_details = latest_message.provider_details
                
                # Extract costs if available in provider details
                if 'cost' in provider_details:
                    cost_info = provider_details['cost']
                    return (
                        float(cost_info.get('prompt_cost', 0.0)),
                        float(cost_info.get('completion_cost', 0.0)),
                        float(cost_info.get('total_cost', 0.0))
                    )
    except Exception as e:
        logfire.debug(
            'agent.provider_cost_extraction_failed',
            model=requested_model,
            error=str(e)
        )
    
    return 0.0, 0.0, 0.0


async def track_chat_request(
    tracker: Any,
    session_id: str,
    tracking_model: str,
    requested_model: str,
    request_messages: list,
    model_settings: dict,
    response_body: dict,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    prompt_cost: float,
    completion_cost: float,
    total_cost: float,
    latency_ms: int,
    agent_instance_id: Optional[UUID],
    account_id: Optional[UUID],
    account_slug: Optional[str],
    agent_instance_slug: Optional[str],
    agent_type: Optional[str],
    is_streaming: bool = False
) -> Optional[UUID]:
    """
    Track LLM request with unified interface for streaming and non-streaming.
    
    Consolidates LLM request tracking logic that was duplicated between
    simple_chat() and simple_chat_stream() functions.
    
    Args:
        tracker: LLMRequestTracker instance
        session_id: Session ID
        tracking_model: Model name for tracking (may differ from requested_model)
        requested_model: Original model identifier requested
        request_messages: List of messages in the request
        model_settings: Model configuration (temperature, max_tokens)
        response_body: Full response body with usage and provider details
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens  
        total_tokens: Total tokens (prompt + completion)
        prompt_cost: Cost for prompt tokens in USD
        completion_cost: Cost for completion tokens in USD
        total_cost: Total cost in USD
        latency_ms: Request latency in milliseconds
        agent_instance_id: Agent instance UUID (multi-tenant)
        account_id: Account UUID (multi-tenant)
        account_slug: Account slug (multi-tenant)
        agent_instance_slug: Agent instance slug (multi-tenant)
        agent_type: Agent type identifier
        is_streaming: Whether this is a streaming request
        
    Returns:
        LLM request UUID if tracking succeeded, None otherwise
    """
    try:
        # Build request body
        request_body = {
            "messages": request_messages,
            "model": requested_model,
            "temperature": model_settings.get("temperature"),
            "max_tokens": model_settings.get("max_tokens")
        }
        
        if is_streaming:
            request_body["stream"] = True
        
        # Track the request
        llm_request_id = await tracker.track_llm_request(
            session_id=session_id,
            model=tracking_model,
            request_body=request_body,
            response_body=response_body,
            tokens={
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            cost_data={
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "total_cost": Decimal(str(total_cost))
            },
            latency_ms=latency_ms,
            agent_instance_id=agent_instance_id,
            # Denormalized fields for fast billing queries (no JOINs)
            account_id=account_id,
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug,
            agent_type=agent_type,
            completion_status="complete"
        )
        
        logfire.info(
            'agent.llm_tracked',
            session_id=session_id,
            llm_request_id=str(llm_request_id) if llm_request_id else None,
            model=tracking_model,
            streaming=is_streaming
        )
        
        return llm_request_id
        
    except Exception as e:
        logfire.error(
            'agent.llm_tracking_failed',
            session_id=session_id,
            error=str(e),
            error_type=type(e).__name__
        )
        return None

