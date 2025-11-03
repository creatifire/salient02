"""
OpenRouter-specific model implementation with cost tracking.

Extends OpenAIChatModel to extract OpenRouter-specific data including
cost information from responses and store it in vendor_details.

Based on pydantic-ai Issue #1849: "Store OpenRouter provider metadata in ModelResponse vendor details"
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



from typing import Any, Dict
import os

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider


class OpenRouterAsyncClient(AsyncOpenAI):
    """
    Custom AsyncOpenAI client configured for OpenRouter.
    
    The actual usage tracking injection is handled by the factory function
    create_openrouter_provider_with_cost_tracking() which patches the
    chat.completions.create method.
    """
    
    def __init__(self, **kwargs):
        # Ensure OpenRouter base_url is set
        if 'base_url' not in kwargs:
            kwargs['base_url'] = 'https://openrouter.ai/api/v1'
        super().__init__(**kwargs)


def create_openrouter_provider_with_cost_tracking(api_key: str = None) -> OpenRouterProvider:
    """
    Create OpenRouterProvider with automatic cost tracking enabled.
    
    Uses a custom AsyncOpenAI client that always includes usage tracking
    parameters in requests to OpenRouter.
    
    Args:
        api_key: OpenRouter API key (uses env OPENROUTER_API_KEY if not provided)
        
    Returns:
        OpenRouterProvider configured for cost tracking
    """
    if not api_key:
        api_key = os.getenv('OPENROUTER_API_KEY')
        
    if not api_key:
        raise ValueError("OpenRouter API key required")
    
    # Create custom client with automatic usage tracking
    custom_client = OpenRouterAsyncClient(api_key=api_key)
    
    # Patch the chat completions create method
    original_create = custom_client.chat.completions.create
    
    async def create_with_usage(**kwargs):
        # Always include usage tracking
        extra_body = kwargs.get('extra_body') or {}
        if not isinstance(extra_body, dict):
            extra_body = {}
        extra_body.setdefault('usage', {})['include'] = True
        kwargs['extra_body'] = extra_body
        
        return await original_create(**kwargs)
    
    custom_client.chat.completions.create = create_with_usage
    
    # Create provider with custom client
    return OpenRouterProvider(openai_client=custom_client)


class OpenRouterModel(OpenAIChatModel):
    """
    OpenRouter-specific model that extracts cost and provider metadata.
    
    Extends OpenAIChatModel to capture OpenRouter-specific response data:
    - cost: The actual cost charged by OpenRouter
    - provider: The upstream provider used by OpenRouter (if available)
    - Any other OpenRouter-specific metadata
    
    Cost data is stored in ModelResponse.vendor_details for easy access.
    """
    
    def _process_response(self, response: ChatCompletion | str) -> ModelResponse:
        """
        Process OpenRouter response and extract cost/provider metadata.
        
        Calls the parent OpenAI processing then adds OpenRouter-specific
        data to the vendor_details field of the response.
        
        Args:
            response: OpenRouter API response (OpenAI-compatible format)
            
        Returns:
            ModelResponse with OpenRouter cost data in vendor_details
        """
        # First, process with standard OpenAI logic
        model_response = super()._process_response(response)
        
        # Extract OpenRouter-specific data if available
        if isinstance(response, ChatCompletion) and response.usage:
            openrouter_data = {}
            
            # Extract cost information (the main goal!)
            if hasattr(response.usage, 'cost') and response.usage.cost is not None:
                openrouter_data['cost'] = float(response.usage.cost)
            
            # Extract provider information if available
            if hasattr(response, 'provider') and response.provider:
                openrouter_data['provider'] = response.provider
            
            # Extract any other OpenRouter-specific fields
            if hasattr(response.usage, 'cost_details'):
                openrouter_data['cost_details'] = response.usage.cost_details
                
            # Store in vendor_details if we found any OpenRouter data
            if openrouter_data:
                # Initialize or update provider_details directly
                if model_response.provider_details is None:
                    # Set new provider_details dict
                    model_response.provider_details = openrouter_data
                else:
                    # Merge with existing provider_details
                    model_response.provider_details.update(openrouter_data)
        
        return model_response