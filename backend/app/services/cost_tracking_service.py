"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import yaml
import logfire


class CostTrackingService:
    """
    Service for extracting and calculating LLM costs from Pydantic AI results.
    
    Handles both non-streaming (OpenRouter provider_details) and streaming 
    (genai-prices calculation) cost tracking patterns.
    """
    
    @staticmethod
    def extract_costs_from_result(
        result: Any,
        requested_model: str,
        session_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Extract costs from Pydantic AI result (non-streaming).
        
        For non-streaming responses, costs are extracted from OpenRouter's
        provider_details metadata which includes exact vendor costs.
        
        Args:
            result: Pydantic AI result object with usage() and new_messages()
            requested_model: Model string (e.g., "google/gemini-2.5-flash")
            session_id: Optional session ID for logging
            
        Returns:
            dict with keys: prompt_cost, completion_cost, total_cost (floats)
        """
        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0
        }
        
        # Get the latest message response with OpenRouter metadata
        new_messages = result.new_messages() if hasattr(result, 'new_messages') else None
        if not new_messages:
            return costs
        
        latest_message = new_messages[-1]  # Last message (assistant response)
        if not hasattr(latest_message, 'provider_details') or not latest_message.provider_details:
            return costs
        
        # DEBUG: Log provider_details for cost tracking verification
        logfire.info(
            'service.cost_tracking.provider_details_debug',
            provider_details=latest_message.provider_details,
            requested_model=requested_model,
            session_id=session_id
        )
        
        # Extract total cost
        vendor_cost = latest_message.provider_details.get('cost')
        if vendor_cost is not None:
            costs["total_cost"] = float(vendor_cost)
        
        # Extract detailed costs from cost_details
        cost_details = latest_message.provider_details.get('cost_details', {})
        if cost_details:
            costs["prompt_cost"] = float(cost_details.get('upstream_inference_prompt_cost', 0.0))
            costs["completion_cost"] = float(cost_details.get('upstream_inference_completions_cost', 0.0))
            
            logfire.info(
                'service.cost_tracking.openrouter_extracted',
                total_cost=costs["total_cost"],
                prompt_cost=costs["prompt_cost"],
                completion_cost=costs["completion_cost"],
                model=requested_model,
                session_id=session_id
            )
        
        return costs
    
    @staticmethod
    async def calculate_streaming_costs(
        usage_data: Any,
        requested_model: str,
        session_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate costs for streaming responses using genai-prices.
        
        Pydantic AI doesn't populate provider_details for streaming responses,
        so we use genai-prices to calculate costs from token usage.
        
        Falls back to config-based pricing if model not in genai-prices database.
        
        Args:
            usage_data: Usage data with input_tokens, output_tokens, total_tokens
            requested_model: Model string (e.g., "google/gemini-2.5-flash")
            session_id: Optional session ID for logging
            
        Returns:
            dict with keys: prompt_cost, completion_cost, total_cost (floats)
            
        Note:
            See memorybank/lessons-learned/pydantic-ai-streaming-cost-tracking.md
        """
        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0
        }
        
        if not usage_data:
            return costs
        
        prompt_tokens = getattr(usage_data, 'input_tokens', 0)
        completion_tokens = getattr(usage_data, 'output_tokens', 0)
        
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
            costs["prompt_cost"] = float(price.input_price)
            costs["completion_cost"] = float(price.output_price)
            costs["total_cost"] = float(price.total_price)
            
            logfire.info(
                'service.cost_tracking.genai_prices_calculated',
                session_id=session_id,
                model=requested_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                prompt_cost=costs["prompt_cost"],
                completion_cost=costs["completion_cost"],
                total_cost=costs["total_cost"],
                method="genai-prices"
            )
            
        except LookupError as e:
            # Model not in genai-prices database - use fallback pricing
            fallback_costs = CostTrackingService.get_fallback_pricing(
                requested_model,
                prompt_tokens,
                completion_tokens
            )
            
            if fallback_costs:
                costs = fallback_costs
                logfire.info(
                    'service.cost_tracking.fallback_pricing_used',
                    session_id=session_id,
                    model=requested_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    prompt_cost=costs["prompt_cost"],
                    completion_cost=costs["completion_cost"],
                    total_cost=costs["total_cost"],
                    method="fallback_pricing"
                )
            else:
                logfire.warn(
                    'service.cost_tracking.calculation_failed',
                    session_id=session_id,
                    model=requested_model,
                    error=f"Model not in genai-prices or fallback pricing: {e}",
                    error_type="LookupError",
                    fallback="zero_cost"
                )
        
        except Exception as e:
            logfire.warn(
                'service.cost_tracking.calculation_failed',
                session_id=session_id,
                model=requested_model,
                error=str(e),
                error_type=type(e).__name__,
                fallback="zero_cost"
            )
        
        return costs
    
    @staticmethod
    def get_fallback_pricing(
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Optional[Dict[str, float]]:
        """
        Load fallback pricing from YAML config for models not in genai-prices.
        
        Args:
            model: Full model string (e.g., "google/gemini-2.5-flash")
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            dict with cost data if model found in config, None otherwise
        """
        try:
            # Load fallback pricing from config file
            # This file is located at: backend/config/fallback_pricing.yaml
            config_dir = Path(__file__).parent.parent.parent / "config"
            fallback_pricing_path = config_dir / "fallback_pricing.yaml"
            
            if not fallback_pricing_path.exists():
                logfire.warn(
                    'service.cost_tracking.fallback_config_missing',
                    config_path=str(fallback_pricing_path)
                )
                return None
            
            with open(fallback_pricing_path, 'r') as f:
                fallback_config = yaml.safe_load(f)
                fallback_pricing_models = fallback_config.get('models', {})
            
            if model not in fallback_pricing_models:
                logfire.warn(
                    'service.cost_tracking.model_not_in_fallback',
                    model=model,
                    config_path=str(fallback_pricing_path),
                    suggestion=f"Add {model} to fallback_pricing.yaml"
                )
                return None
            
            pricing = fallback_pricing_models[model]
            prompt_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
            completion_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
            total_cost = prompt_cost + completion_cost
            
            return {
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "total_cost": total_cost,
                "source": pricing.get("source", "unknown"),
                "config_file": str(fallback_pricing_path)
            }
            
        except Exception as e:
            logfire.error(
                'service.cost_tracking.fallback_load_failed',
                model=model,
                error=str(e),
                error_type=type(e).__name__
            )
            return None

