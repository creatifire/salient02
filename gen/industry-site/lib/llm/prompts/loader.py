"""
Prompt management system for external prompt storage and loading.

This module provides utilities for loading prompts from external Markdown files
with variable substitution support.
"""

from pathlib import Path
from typing import Dict, Any, Optional


PROMPTS_DIR = Path(__file__).parent


def load_prompt(category: str, name: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Load prompt from file with variable substitution.
    
    Args:
        category: Prompt category (research, generation, analysis, validation, system)
        name: Prompt filename without .md extension
        variables: Dict of variables to substitute using {var} syntax
        
    Returns:
        Formatted prompt string
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        KeyError: If required variable missing
        
    Example:
        >>> prompt = load_prompt('generation', 'product_names', {
        ...     'count': 100,
        ...     'industry': 'agtech',
        ...     'company_name': 'AgriTech Solutions',
        ...     'real_products': 'Tractor\\nHarvester\\nDrone',
        ...     'categories': 'Equipment\\nSoftware\\nServices'
        ... })
    """
    prompt_path = PROMPTS_DIR / category / f"{name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    prompt_template = prompt_path.read_text(encoding='utf-8')
    
    if variables:
        try:
            return prompt_template.format(**variables)
        except KeyError as e:
            raise KeyError(f"Missing required variable in prompt: {e}")
    
    return prompt_template


def load_system_prompt(role: str) -> str:
    """
    Load system prompt for specific role.
    
    Args:
        role: Role name (researcher, generator, analyst)
        
    Returns:
        System prompt string
        
    Raises:
        FileNotFoundError: If system prompt file doesn't exist
        
    Example:
        >>> system = load_system_prompt('generator')
    """
    return load_prompt('system', role)
