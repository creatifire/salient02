"""
Local models for agent implementations.

This module contains custom model classes that extend or customize
the behavior of base Pydantic AI models for specific providers.
"""

from .openrouter import OpenRouterModel

__all__ = ['OpenRouterModel']
