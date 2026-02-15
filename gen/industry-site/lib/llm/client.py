"""
LLM client for unified interaction with OpenRouter API.
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
import logging
from ..errors.exceptions import LLMError, LLMRetryExhausted
from .retry import exponential_backoff

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client with retry logic and logging.
    Supports both tool calling and text generation models.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenRouter API key
            base_url: API base URL (default: OpenRouter)
            default_model: Default model to use
            max_retries: Maximum retry attempts for failed calls
            timeout: Request timeout in seconds
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )
        self.default_model = default_model
        self.max_retries = max_retries
        self.call_count = 0
        self.total_tokens = 0
        
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make chat completion request with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (overrides default)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            tools: Tool definitions for function calling
            tool_choice: Tool selection strategy ('auto', 'none', or specific tool)
            
        Returns:
            Response dictionary with:
                - content: Generated text content
                - tool_calls: List of tool calls (if any)
                - usage: Token usage statistics
                - model: Model used
                - finish_reason: Completion reason
            
        Raises:
            LLMRetryExhausted: If all retries failed
            LLMError: For other API errors
            
        Example:
            >>> response = client.chat([
            ...     {"role": "system", "content": "You are helpful."},
            ...     {"role": "user", "content": "Hello!"}
            ... ])
            >>> print(response['content'])
        """
        model = model or self.default_model
        if not model:
            raise ValueError("No model specified and no default set")
        
        self.call_count += 1
        
        logger.info(
            f"LLM call #{self.call_count} starting: model={model}, "
            f"messages={len(messages)}, has_tools={tools is not None}"
        )
        
        @exponential_backoff(max_retries=self.max_retries)
        def _make_request():
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice=tool_choice
            )
        
        try:
            response = _make_request()
            
            result = {
                'content': response.choices[0].message.content,
                'tool_calls': None,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason
            }
            
            # Track total tokens
            self.total_tokens += result['usage']['total_tokens']
            
            # Handle tool calls if present
            if response.choices[0].message.tool_calls:
                result['tool_calls'] = [
                    {
                        'id': tc.id,
                        'function': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                    for tc in response.choices[0].message.tool_calls
                ]
            
            logger.info(
                f"LLM call #{self.call_count} success: "
                f"tokens={result['usage']['total_tokens']}, "
                f"finish_reason={result['finish_reason']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"LLM call #{self.call_count} failed: {type(e).__name__}: {str(e)}"
            )
            raise LLMError(f"LLM call failed: {str(e)}") from e
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt (convenience method).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use
            **kwargs: Additional arguments to chat()
            
        Returns:
            Generated text content
            
        Example:
            >>> text = client.generate_text(
            ...     "What is Python?",
            ...     system_prompt="You are a helpful assistant."
            ... )
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat(messages, model=model, **kwargs)
        return response['content']
    
    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with call_count and total_tokens
        """
        return {
            'call_count': self.call_count,
            'total_tokens': self.total_tokens
        }
    
    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self.call_count = 0
        self.total_tokens = 0
