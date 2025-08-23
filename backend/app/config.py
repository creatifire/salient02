"""
Configuration management for the Salient Sales Bot backend.

This module provides centralized configuration loading from YAML files and
environment variables, with validation, defaults, and security-first design.

Key Features:
- YAML configuration with environment variable overrides
- Security-enforced environment variables for sensitive data
- Configuration caching for performance
- Comprehensive validation with sensible defaults
- Support for development, staging, and production environments

Usage:
    config = load_config()
    db_url = get_database_url()
    session_config = get_session_config()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import os

import yaml
from dotenv import load_dotenv, find_dotenv


# Load environment variables once at module import
# System environment takes precedence over .env file for security
load_dotenv(find_dotenv(), override=False)

# Global configuration cache to avoid repeated YAML parsing
_CONFIG_CACHE: Dict[str, Any] | None = None


def load_config() -> Dict[str, Any]:
    """
    Load and validate application configuration from YAML and environment.
    
    Loads configuration from backend/config/app.yaml with environment variable
    overrides for sensitive data. Provides comprehensive validation and defaults
    to ensure the application can start safely.
    
    Returns:
        Complete configuration dictionary with all validated settings
        
    Raises:
        ValueError: If required environment variables are missing
        
    Example:
        >>> config = load_config()
        >>> llm_model = config["llm"]["model"]
        >>> db_pool_size = config["database"]["pool_size"]
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    # Load base configuration from YAML file
    config_path = Path(__file__).resolve().parent.parent / "config" / "app.yaml"
    config: Dict[str, Any] = {}
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text()) or {}
        except Exception:
            # Graceful fallback to empty config if YAML is malformed
            config = {}

    # Apply defaults and validation for each configuration section
    chat = config.setdefault("chat", {})
    input_cfg = chat.setdefault("input", {})
    input_cfg.setdefault("debounce_ms", 250)
    input_cfg.setdefault("submit_shortcut", "ctrl+enter")
    input_cfg.setdefault("enter_inserts_newline", True)

    # UI defaults
    ui_cfg = config.setdefault("ui", {})
    ui_cfg.setdefault("sse_enabled", True)
    ui_cfg.setdefault("allow_basic_html", True)

    # Logging defaults
    logging_cfg = config.setdefault("logging", {})
    logging_cfg.setdefault("level", "INFO")
    logging_cfg.setdefault("path", "./backend/logs/app.jsonl")
    logging_cfg.setdefault("rotation", "50 MB")
    logging_cfg.setdefault("retention", "14 days")
    logging_cfg.setdefault("frontend_debug", False)

    # LLM defaults with basic validation
    llm_cfg = config.setdefault("llm", {})
    llm_cfg.setdefault("provider", "openrouter")
    llm_cfg.setdefault("model", "openai/gpt-oss-20b:free")
    try:
        temp = float(llm_cfg.get("temperature", 0.3))
        if not (0.0 <= temp <= 2.0):
            temp = 0.3
        llm_cfg["temperature"] = temp
    except Exception:
        llm_cfg["temperature"] = 0.3
    try:
        max_toks = int(llm_cfg.get("max_tokens", 512))
        if max_toks <= 0:
            max_toks = 512
        llm_cfg["max_tokens"] = max_toks
    except Exception:
        llm_cfg["max_tokens"] = 512

    # Database configuration with security-enforced environment variables
    # Database URL must come from environment for security (never in YAML)
    db_cfg = config.setdefault("database", {})
    env_database_url = get_env("DATABASE_URL")
    if not env_database_url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Example: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname"
        )
    db_cfg["url"] = env_database_url
    
    # Database connection pool settings
    try:
        pool_size = int(db_cfg.get("pool_size", 20))
        if pool_size <= 0:
            pool_size = 20
        db_cfg["pool_size"] = pool_size
    except Exception:
        db_cfg["pool_size"] = 20
    
    try:
        max_overflow = int(db_cfg.get("max_overflow", 0))
        if max_overflow < 0:
            max_overflow = 0
        db_cfg["max_overflow"] = max_overflow
    except Exception:
        db_cfg["max_overflow"] = 0
        
    try:
        pool_timeout = int(db_cfg.get("pool_timeout", 30))
        if pool_timeout <= 0:
            pool_timeout = 30
        db_cfg["pool_timeout"] = pool_timeout
    except Exception:
        db_cfg["pool_timeout"] = 30

    # Session configuration
    session_cfg = config.setdefault("session", {})
    session_cfg.setdefault("cookie_name", "salient_session")
    try:
        max_age = int(session_cfg.get("cookie_max_age", 604800))  # 7 days default
        if max_age <= 0:
            max_age = 604800
        session_cfg["cookie_max_age"] = max_age
    except Exception:
        session_cfg["cookie_max_age"] = 604800
    
    session_cfg.setdefault("cookie_secure", False)  # True in production
    session_cfg.setdefault("cookie_httponly", True)
    session_cfg.setdefault("cookie_samesite", "lax")

    # Redis configuration with security-enforced environment variables  
    # Redis URL must come from environment for security (never in YAML)
    redis_cfg = config.setdefault("redis", {})
    env_redis_url = get_env("REDIS_URL")
    if not env_redis_url:
        raise ValueError(
            "REDIS_URL environment variable is required. "
            "Example: REDIS_URL=redis://localhost:6379/0"
        )
    redis_cfg["url"] = env_redis_url
    
    try:
        session_db = int(redis_cfg.get("session_db", 1))
        if session_db < 0:
            session_db = 1
        redis_cfg["session_db"] = session_db
    except Exception:
        redis_cfg["session_db"] = 1
        
    try:
        cache_db = int(redis_cfg.get("cache_db", 2))
        if cache_db < 0:
            cache_db = 2
        redis_cfg["cache_db"] = cache_db
    except Exception:
        redis_cfg["cache_db"] = 2

    _CONFIG_CACHE = config
    return config


def get_env(name: str, default: str | None = None) -> str | None:
    """
    Get environment variable with optional default.
    
    Args:
        name: Environment variable name
        default: Default value if variable not found
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(name, default)


def get_openrouter_api_key() -> str | None:
    """
    Get OpenRouter API key from environment variables.
    
    Returns:
        API key string or None if not configured
        
    Note:
        This is a legacy helper. New code should use get_env() directly.
    """
    return get_env("OPENROUTER_API_KEY")


def get_database_config() -> Dict[str, Any]:
    """
    Get complete database configuration including connection settings.
    
    Returns:
        Dictionary containing database URL, pool settings, and timeouts
        
    Example:
        >>> db_config = get_database_config()
        >>> pool_size = db_config["pool_size"]
        >>> db_url = db_config["url"]
    """
    config = load_config()
    return config.get("database", {})


def get_database_url() -> str:
    """
    Get database connection URL from environment variable.
    
    Returns:
        PostgreSQL connection URL for asyncpg
        
    Raises:
        ValueError: If DATABASE_URL environment variable is not set
        
    Example:
        >>> db_url = get_database_url()
        >>> engine = create_async_engine(db_url)
    """
    db_config = get_database_config()
    url = db_config.get("url")
    if not url:
        raise ValueError("DATABASE_URL environment variable is required")
    return url


def get_session_config() -> Dict[str, Any]:
    """
    Get HTTP session configuration for cookie management.
    
    Returns:
        Dictionary containing cookie settings for browser sessions
        
    Example:
        >>> session_config = get_session_config()
        >>> cookie_name = session_config["cookie_name"]
        >>> max_age = session_config["cookie_max_age"]
    """
    config = load_config()
    return config.get("session", {})


def get_redis_config() -> Dict[str, Any]:
    """
    Get Redis configuration for caching and session storage.
    
    Returns:
        Dictionary containing Redis URL and database assignments
        
    Example:
        >>> redis_config = get_redis_config()
        >>> session_db = redis_config["session_db"]
        >>> cache_db = redis_config["cache_db"]
    """
    config = load_config()
    return config.get("redis", {})


def get_redis_url() -> str:
    """
    Get Redis connection URL from environment variable.
    
    Returns:
        Redis connection URL for redis-py
        
    Raises:
        ValueError: If REDIS_URL environment variable is not set
        
    Example:
        >>> redis_url = get_redis_url()
        >>> redis_client = redis.from_url(redis_url)
    """
    redis_config = get_redis_config()
    url = redis_config.get("url")
    if not url:
        raise ValueError("REDIS_URL environment variable is required")
    return url
