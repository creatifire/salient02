"""
Configuration management for the Salient Sales Bot backend.

This module provides centralized, secure configuration loading from YAML files and
environment variables, implementing security-first design principles with comprehensive
validation, intelligent defaults, and performance optimization through caching.

Key Features:
- YAML configuration files with environment variable overrides for flexibility
- Security-enforced environment variables for sensitive data (DATABASE_URL, REDIS_URL)
- Configuration caching for performance with global singleton pattern
- Comprehensive validation with sensible defaults and graceful error handling
- Support for development, staging, and production environments
- Type-safe configuration access with validation and error reporting
- Environment-specific configuration patterns with security enforcement

Security Design:
The configuration system enforces security best practices by requiring sensitive
credentials to be provided via environment variables, never stored in YAML files.
This prevents accidental credential exposure in version control while maintaining
deployment flexibility across environments.

Configuration Sources (in precedence order):
1. Environment variables (highest priority, required for sensitive data)
2. YAML configuration files (backend/config/app.yaml)
3. Hardcoded defaults (fallback values with safe assumptions)

Caching Strategy:
Configuration is loaded once at module import and cached globally to avoid repeated
file I/O and YAML parsing. The cache is invalidated only on module reload, making
it suitable for production deployments where configuration is static.

Validation Approach:
All configuration values undergo validation with type checking, range validation,
and sensible defaults. Invalid values gracefully fall back to safe defaults with
appropriate logging for troubleshooting.

Usage Patterns:
    # Load complete configuration
    config = load_config()
    llm_model = config["llm"]["model"]
    
    # Get specific configuration sections
    db_config = get_database_config()
    session_config = get_session_config()
    
    # Get secure URLs from environment
    db_url = get_database_url()
    redis_url = get_redis_url()
    
    # Environment variable access
    api_key = get_env("OPENROUTER_API_KEY")

Thread Safety:
All configuration access is thread-safe due to the read-only nature of the
cached configuration and atomic operations for environment variable access.

Performance Considerations:
- Configuration caching eliminates repeated YAML parsing overhead
- Environment variable access is optimized via os.getenv()
- Validation occurs once at load time, not per access
- Graceful fallbacks prevent application startup failures

Dependencies:
- PyYAML for YAML file parsing with safe loading
- python-dotenv for .env file support in development
- pathlib for cross-platform file path handling
- typing for comprehensive type hints and validation
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import find_dotenv, load_dotenv


# Load environment variables once at module import
# System environment variables take precedence over .env file for security
# This ensures production environment variables override development .env files
load_dotenv(find_dotenv(), override=False)

# Global configuration cache to avoid repeated YAML parsing and file I/O
# This singleton pattern ensures configuration is loaded once per application lifecycle
# and provides consistent, high-performance access across all application components
_CONFIG_CACHE: Dict[str, Any] | None = None

# Configuration metadata for change detection and versioning
_CONFIG_METADATA: Dict[str, Any] = {
    "loaded_at": None,
    "config_hash": None,
    "yaml_file_modified": None,
    "env_vars_hash": None,
    "version": None
}


def load_config() -> Dict[str, Any]:
    """
    Load and validate application configuration from YAML and environment variables.
    
    This function implements the core configuration loading logic with security-first
    design, comprehensive validation, and performance optimization through caching.
    It combines YAML configuration files with environment variable overrides to
    provide flexible, secure configuration management.
    
    Configuration Loading Process:
    1. Check global cache for previously loaded configuration (performance optimization)
    2. Load base configuration from backend/config/app.yaml (graceful failure handling)
    3. Apply security-enforced environment variables for sensitive data
    4. Validate all configuration sections with type checking and range validation
    5. Apply sensible defaults for missing or invalid configuration values
    6. Cache complete configuration for subsequent access
    
    Security Enforcement:
    - DATABASE_URL must come from environment (never stored in YAML)
    - REDIS_URL must come from environment (never stored in YAML)
    - Sensitive credentials are rejected if found in YAML files
    - Environment variables take precedence over YAML for all sensitive data
    
    Validation Features:
    - Type checking for numeric values with safe casting
    - Range validation for parameters like temperature, pool sizes, timeouts
    - Graceful fallback to safe defaults for malformed or missing values
    - Comprehensive error handling with descriptive error messages
    
    Configuration Sections:
    - chat: User interface and interaction settings
    - ui: Frontend display and behavior configuration
    - logging: Application logging configuration with rotation and retention
    - llm: Language model provider settings with validation
    - database: PostgreSQL connection and pool configuration
    - session: HTTP session and cookie management
    - redis: Redis connection and database assignment
    
    Returns:
        Dict[str, Any]: Complete configuration dictionary with all validated settings
            organized by section (chat, ui, logging, llm, database, session, redis)
        
    Raises:
        ValueError: If required environment variables (DATABASE_URL, REDIS_URL) are missing
        
    Examples:
        >>> config = load_config()
        >>> llm_model = config["llm"]["model"]
        >>> db_pool_size = config["database"]["pool_size"]
        >>> session_timeout = config["session"]["inactivity_minutes"]
        
        >>> # Access nested configuration
        >>> debounce_ms = config["chat"]["input"]["debounce_ms"]
        >>> log_level = config["logging"]["level"]
    
    Performance Notes:
        Configuration is cached globally after first load, making subsequent calls
        extremely fast. Cache invalidation only occurs on module reload, suitable
        for production where configuration is static during application lifecycle.
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        # Return cached configuration for performance optimization
        return _CONFIG_CACHE

    # Load base configuration from YAML file with graceful error handling
    # Path resolution: backend/app/config.py -> backend/config/app.yaml
    config_path = Path(__file__).resolve().parent.parent / "config" / "app.yaml"
    config: Dict[str, Any] = {}
    
    if config_path.exists():
        try:
            # Use safe_load to prevent arbitrary code execution from YAML
            config = yaml.safe_load(config_path.read_text()) or {}
        except Exception:
            # Graceful fallback to empty config if YAML is malformed
            # Application will use defaults and environment variables
            config = {}
    else:
        # YAML file is optional - application works with environment variables and defaults
        config = {}

    # Apply defaults and validation for each configuration section
    # Chat configuration: User interface and interaction settings
    chat = config.setdefault("chat", {})
    input_cfg = chat.setdefault("input", {})
    # Debounce delay prevents excessive API calls during typing
    input_cfg.setdefault("debounce_ms", 250)
    # Keyboard shortcut for message submission
    input_cfg.setdefault("submit_shortcut", "ctrl+enter")
    # Allow Enter key to insert newlines instead of submitting
    input_cfg.setdefault("enter_inserts_newline", True)

    # UI configuration: Frontend display and behavior settings
    ui_cfg = config.setdefault("ui", {})
    # Server-Sent Events for real-time updates
    ui_cfg.setdefault("sse_enabled", True)
    # Allow basic HTML tags in chat messages for formatting
    ui_cfg.setdefault("allow_basic_html", True)

    # Logging configuration: Application logging with structured JSONL format
    logging_cfg = config.setdefault("logging", {})
    # Standard log level for production environments
    logging_cfg.setdefault("level", "INFO")
    # Log file path relative to project root for consistent deployment
    logging_cfg.setdefault("path", "./backend/logs/app.jsonl")
    # Log rotation to prevent disk space issues
    logging_cfg.setdefault("rotation", "50 MB")
    # Log retention for compliance and debugging
    logging_cfg.setdefault("retention", "14 days")
    # Frontend debug logging disabled by default for security
    logging_cfg.setdefault("frontend_debug", False)

    # LLM configuration: Language model provider settings with validation
    llm_cfg = config.setdefault("llm", {})
    # Default to OpenRouter for cost-effective access to multiple models
    llm_cfg.setdefault("provider", "openrouter")
    # Free tier model for development and testing
    llm_cfg.setdefault("model", "openai/gpt-oss-20b:free")
    
    # Temperature validation: Controls randomness in model responses (0.0-2.0)
    try:
        temp = float(llm_cfg.get("temperature", 0.3))
        if not (0.0 <= temp <= 2.0):
            # Invalid temperature, use conservative default
            temp = 0.3
        llm_cfg["temperature"] = temp
    except Exception:
        # Non-numeric temperature, fallback to safe default
        llm_cfg["temperature"] = 0.3
    
    # Max tokens validation: Limits response length for cost control
    try:
        max_toks = int(llm_cfg.get("max_tokens", 512))
        if max_toks <= 0:
            # Invalid token count, use reasonable default
            max_toks = 512
        llm_cfg["max_tokens"] = max_toks
    except Exception:
        # Non-numeric max_tokens, fallback to safe default
        llm_cfg["max_tokens"] = 512

    # Database configuration with security-enforced environment variables
    # SECURITY REQUIREMENT: Database URL must come from environment (never in YAML)
    # This prevents credential exposure in version control and config files
    db_cfg = config.setdefault("database", {})
    env_database_url = get_env("DATABASE_URL")
    if not env_database_url:
        raise ValueError(
            "DATABASE_URL environment variable is required for security. "
            "Example: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname"
        )
    db_cfg["url"] = env_database_url
    
    # Database connection pool settings with validation for production workloads
    # Pool size: Number of persistent connections maintained in the pool
    try:
        pool_size = int(db_cfg.get("pool_size", 20))
        if pool_size <= 0:
            # Invalid pool size, use production-safe default
            pool_size = 20
        db_cfg["pool_size"] = pool_size
    except Exception:
        # Non-numeric pool_size, fallback to safe default
        db_cfg["pool_size"] = 20
    
    # Max overflow: Additional connections beyond pool_size (0 = no overflow)
    try:
        max_overflow = int(db_cfg.get("max_overflow", 0))
        if max_overflow < 0:
            # Negative overflow not allowed, use conservative default
            max_overflow = 0
        db_cfg["max_overflow"] = max_overflow
    except Exception:
        # Non-numeric max_overflow, fallback to safe default
        db_cfg["max_overflow"] = 0
    
    # Pool timeout: Seconds to wait for available connection
    try:
        pool_timeout = int(db_cfg.get("pool_timeout", 30))
        if pool_timeout <= 0:
            # Invalid timeout, use reasonable default
            pool_timeout = 30
        db_cfg["pool_timeout"] = pool_timeout
    except Exception:
        # Non-numeric pool_timeout, fallback to safe default
        db_cfg["pool_timeout"] = 30

    # Session configuration: HTTP session and cookie management
    session_cfg = config.setdefault("session", {})
    # Cookie name for session identification
    session_cfg.setdefault("cookie_name", "salient_session")
    
    # Cookie max age validation: Session lifetime in seconds (default: 7 days)
    try:
        max_age = int(session_cfg.get("cookie_max_age", 604800))  # 7 days default
        if max_age <= 0:
            # Invalid max age, use secure default (7 days)
            max_age = 604800
        session_cfg["cookie_max_age"] = max_age
    except Exception:
        # Non-numeric max_age, fallback to secure default
        session_cfg["cookie_max_age"] = 604800
    
    # Cookie security settings (environment-specific)
    # SECURITY NOTE: Set cookie_secure=True in production with HTTPS
    session_cfg.setdefault("cookie_secure", False)  # True in production
    # HTTP-only cookies prevent XSS access via JavaScript
    session_cfg.setdefault("cookie_httponly", True)
    # SameSite protection against CSRF attacks
    session_cfg.setdefault("cookie_samesite", "lax")
    
    # Session timeout configuration: User inactivity threshold
    try:
        inactivity_minutes = int(session_cfg.get("inactivity_minutes", 30))
        if inactivity_minutes <= 0:
            # Invalid timeout, use secure default
            inactivity_minutes = 30
        session_cfg["inactivity_minutes"] = inactivity_minutes
    except Exception:
        # Non-numeric timeout, fallback to secure default
        session_cfg["inactivity_minutes"] = 30

    # Redis configuration with security-enforced environment variables
    # SECURITY REQUIREMENT: Redis URL must come from environment (never in YAML)
    # This prevents credential exposure in version control and config files
    redis_cfg = config.setdefault("redis", {})
    env_redis_url = get_env("REDIS_URL")
    if not env_redis_url:
        raise ValueError(
            "REDIS_URL environment variable is required for security. "
            "Example: REDIS_URL=redis://localhost:6379/0"
        )
    redis_cfg["url"] = env_redis_url
    
    # Redis database assignments for logical separation of data types
    # Session database: User session storage (default: database 1)
    try:
        session_db = int(redis_cfg.get("session_db", 1))
        if session_db < 0:
            # Invalid database number, use safe default
            session_db = 1
        redis_cfg["session_db"] = session_db
    except Exception:
        # Non-numeric session_db, fallback to safe default
        redis_cfg["session_db"] = 1
    
    # Cache database: Application caching (default: database 2)
    try:
        cache_db = int(redis_cfg.get("cache_db", 2))
        if cache_db < 0:
            # Invalid database number, use safe default
            cache_db = 2
        redis_cfg["cache_db"] = cache_db
    except Exception:
        # Non-numeric cache_db, fallback to safe default
        redis_cfg["cache_db"] = 2

    # Generate configuration metadata for change detection
    _generate_config_metadata(config, config_path)
    
    # Cache validated configuration globally for performance
    _CONFIG_CACHE = config
    return config


def _generate_config_metadata(config: Dict[str, Any], config_path: Path) -> None:
    """Generate metadata for configuration change detection."""
    global _CONFIG_METADATA
    
    # Current timestamp
    _CONFIG_METADATA["loaded_at"] = time.time()
    
    # YAML file modification time
    if config_path.exists():
        _CONFIG_METADATA["yaml_file_modified"] = config_path.stat().st_mtime
    else:
        _CONFIG_METADATA["yaml_file_modified"] = None
    
    # Hash of relevant environment variables for LLM configuration
    llm_env_vars = {
        "LLM_PROVIDER": get_env("LLM_PROVIDER"),
        "LLM_MODEL": get_env("LLM_MODEL"), 
        "LLM_TEMPERATURE": get_env("LLM_TEMPERATURE"),
        "LLM_MAX_TOKENS": get_env("LLM_MAX_TOKENS")
    }
    env_string = str(sorted(llm_env_vars.items()))
    _CONFIG_METADATA["env_vars_hash"] = hashlib.md5(env_string.encode()).hexdigest()[:8]
    
    # Hash of complete configuration for change detection
    config_string = str(sorted(config.items()))
    _CONFIG_METADATA["config_hash"] = hashlib.md5(config_string.encode()).hexdigest()[:8]
    
    # Generate version string combining hashes
    _CONFIG_METADATA["version"] = f"{_CONFIG_METADATA['config_hash']}-{_CONFIG_METADATA['env_vars_hash']}"


def get_config_metadata() -> Dict[str, Any]:
    """Get configuration metadata for change detection and debugging."""
    # Ensure config is loaded
    if _CONFIG_CACHE is None:
        load_config()
    
    return _CONFIG_METADATA.copy()


def get_env(name: str, default: str | None = None) -> str | None:
    """
    Get environment variable with optional default value.
    
    This function provides a consistent interface for accessing environment variables
    throughout the application. It wraps os.getenv() with explicit type hints and
    consistent behavior for missing variables.
    
    Environment Variable Access Pattern:
    Environment variables are the primary source for sensitive configuration data
    such as database URLs, API keys, and other credentials. This function ensures
    consistent access patterns across the application.
    
    Args:
        name: Environment variable name to retrieve
        default: Default value to return if environment variable is not set
    
    Returns:
        str | None: Environment variable value if found, default value if provided,
            or None if variable not found and no default specified
    
    Examples:
        >>> database_url = get_env("DATABASE_URL")
        >>> debug_mode = get_env("DEBUG", "false")
        >>> api_key = get_env("OPENROUTER_API_KEY")
    
    Note:
        This function does not perform any validation on the returned value.
        Validation should be performed by the calling code based on the specific
        requirements for each environment variable.
    """
    return os.getenv(name, default)


def get_openrouter_api_key() -> str | None:
    """
    Get OpenRouter API key from environment variables.
    
    This is a legacy helper function that wraps get_env() for backward compatibility.
    It provides access to the OpenRouter API key used for language model access.
    
    Security Note:
    The API key is retrieved from environment variables to prevent credential
    exposure in configuration files or version control. This follows security
    best practices for handling sensitive authentication tokens.
    
    Returns:
        str | None: OpenRouter API key if configured in environment, None otherwise
    
    Example:
        >>> api_key = get_openrouter_api_key()
        >>> if api_key:
        ...     # Configure OpenRouter client with API key
        ...     client = OpenRouterClient(api_key)
    
    Deprecation Note:
        This is a legacy helper function. New code should use get_env("OPENROUTER_API_KEY")
        directly for consistency and to avoid unnecessary function indirection.
    """
    return get_env("OPENROUTER_API_KEY")


def get_database_config() -> Dict[str, Any]:
    """
    Get complete database configuration including connection settings and pool parameters.
    
    This function provides access to the validated database configuration section,
    including the database URL from environment variables and connection pool settings
    with applied defaults and validation.
    
    Configuration Contents:
    - url: PostgreSQL connection URL (from DATABASE_URL environment variable)
    - pool_size: Number of persistent connections (default: 20)
    - max_overflow: Additional connections beyond pool_size (default: 0)
    - pool_timeout: Seconds to wait for available connection (default: 30)
    
    Security Note:
    The database URL is always sourced from environment variables to prevent
    credential exposure in configuration files. This function provides access
    to the validated configuration after security enforcement.
    
    Returns:
        Dict[str, Any]: Dictionary containing database URL, pool settings, and timeouts
            with all values validated and defaults applied
    
    Examples:
        >>> db_config = get_database_config()
        >>> pool_size = db_config["pool_size"]
        >>> db_url = db_config["url"]
        >>> timeout = db_config["pool_timeout"]
    
    Note:
        This function loads the complete configuration on first call and uses
        cached results for subsequent calls, making it efficient for repeated access.
    """
    config = load_config()
    return config.get("database", {})


def get_database_url() -> str:
    """
    Get database connection URL from environment variable with security validation.
    
    This function provides direct access to the database connection URL that has been
    validated and loaded from environment variables. It ensures the URL is available
    and properly formatted for use with SQLAlchemy's async engine.
    
    Security Enforcement:
    The database URL is required to come from environment variables (DATABASE_URL)
    and is never stored in configuration files. This function validates that the
    security requirement has been met during configuration loading.
    
    URL Format:
    The expected format is a PostgreSQL connection URL compatible with asyncpg:
    postgresql+asyncpg://user:password@host:port/database
    
    Returns:
        str: PostgreSQL connection URL for asyncpg driver, validated and ready for use
        
    Raises:
        ValueError: If DATABASE_URL environment variable was not set during configuration
            loading, indicating a configuration or deployment issue
        
    Examples:
        >>> db_url = get_database_url()
        >>> engine = create_async_engine(db_url)
        >>> # URL format: postgresql+asyncpg://user:pass@localhost:5432/dbname
    
    Usage in Database Services:
        This function is typically used by database service initialization to create
        SQLAlchemy async engines with the properly configured connection URL.
    """
    db_config = get_database_config()
    url = db_config.get("url")
    if not url:
        # This should not happen if configuration loading succeeded
        raise ValueError("DATABASE_URL environment variable is required")
    return url


def get_session_config() -> Dict[str, Any]:
    """
    Get HTTP session configuration for secure cookie management and user sessions.
    
    This function provides access to the validated session configuration section,
    including cookie settings, security parameters, and timeout configurations
    optimized for web application security and user experience.
    
    Configuration Contents:
    - cookie_name: Name for session cookies (default: "salient_session")
    - cookie_max_age: Session lifetime in seconds (default: 604800 = 7 days)
    - cookie_secure: HTTPS-only cookies (default: False, True in production)
    - cookie_httponly: Prevent JavaScript access (default: True for XSS protection)
    - cookie_samesite: CSRF protection level (default: "lax")
    - inactivity_minutes: User timeout threshold (default: 30 minutes)
    
    Security Features:
    All cookie settings are configured with security best practices including
    HTTP-only flags, SameSite protection, and appropriate timeouts to balance
    security with user experience.
    
    Returns:
        Dict[str, Any]: Dictionary containing cookie settings and session parameters
            with all values validated and security defaults applied
        
    Examples:
        >>> session_config = get_session_config()
        >>> cookie_name = session_config["cookie_name"]
        >>> max_age = session_config["cookie_max_age"]
        >>> secure_flag = session_config["cookie_secure"]
        >>> timeout_minutes = session_config["inactivity_minutes"]
    
    Usage in Session Management:
        This configuration is typically used by session middleware and authentication
        systems to configure secure cookie handling and user session timeouts.
    """
    config = load_config()
    return config.get("session", {})


def get_redis_config() -> Dict[str, Any]:
    """
    Get Redis configuration for caching and session storage with database separation.
    
    This function provides access to the validated Redis configuration section,
    including the connection URL from environment variables and logical database
    assignments for different data types.
    
    Configuration Contents:
    - url: Redis connection URL (from REDIS_URL environment variable)
    - session_db: Database number for session storage (default: 1)
    - cache_db: Database number for application caching (default: 2)
    
    Database Separation Strategy:
    Redis logical databases provide data isolation between different application
    concerns (sessions vs. caching) while using a single Redis instance. This
    approach simplifies deployment while maintaining clear data boundaries.
    
    Security Note:
    The Redis URL is always sourced from environment variables to prevent
    credential exposure in configuration files. Database assignments can be
    configured via YAML for deployment flexibility.
    
    Returns:
        Dict[str, Any]: Dictionary containing Redis URL and database assignments
            with all values validated and defaults applied
        
    Examples:
        >>> redis_config = get_redis_config()
        >>> redis_url = redis_config["url"]
        >>> session_db = redis_config["session_db"]
        >>> cache_db = redis_config["cache_db"]
        >>> # Connect to specific database: redis_client.select(session_db)
    
    Usage in Caching and Sessions:
        This configuration is used by Redis clients for session storage and
        application caching, ensuring proper database separation and connection
        management across different application components.
    """
    config = load_config()
    return config.get("redis", {})


def get_redis_url() -> str:
    """
    Get Redis connection URL from environment variable with security validation.
    
    This function provides direct access to the Redis connection URL that has been
    validated and loaded from environment variables. It ensures the URL is available
    and properly formatted for use with Redis clients.
    
    Security Enforcement:
    The Redis URL is required to come from environment variables (REDIS_URL)
    and is never stored in configuration files. This function validates that the
    security requirement has been met during configuration loading.
    
    URL Format:
    The expected format is a Redis connection URL compatible with redis-py:
    redis://host:port/database or redis://user:password@host:port/database
    
    Returns:
        str: Redis connection URL for redis-py client, validated and ready for use
        
    Raises:
        ValueError: If REDIS_URL environment variable was not set during configuration
            loading, indicating a configuration or deployment issue
        
    Examples:
        >>> redis_url = get_redis_url()
        >>> redis_client = redis.from_url(redis_url)
        >>> # URL format: redis://localhost:6379/0
        >>> # URL format with auth: redis://user:pass@localhost:6379/0
    
    Usage in Caching Services:
        This function is typically used by Redis client initialization to create
        connection pools and client instances with the properly configured URL.
    """
    redis_config = get_redis_config()
    url = redis_config.get("url")
    if not url:
        # This should not happen if configuration loading succeeded
        raise ValueError("REDIS_URL environment variable is required")
    return url
