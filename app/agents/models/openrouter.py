ts"""
OpenRouter-specific model implementation with cost tracking.

Extends OpenAIChatModel to extract OpenRouter-specific data including
cost information from responses and store it in vendor_details.

Based on pydantic-ai Issue #1849: "Store OpenRouter provider metadata in ModelResponse vendor details"
"""

from typing import Any, Dict

from openai.types.chat import ChatCompletion
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.openai import OpenAIChatModel


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
                # Initialize vendor_details if it doesn't exist
                if model_response.provider_details is None:
                    # Create a new vendor_details dict
                    vendor_details = openrouter_data
                else:
                    # Merge with existing vendor_details
                    vendor_details = dict(model_response.provider_details)
                    vendor_details.update(openrouter_data)
                
                # Update the model response with OpenRouter data
                model_response = model_response.model_copy(
                    update={'provider_details': vendor_details}
                )
        
        return model_response
