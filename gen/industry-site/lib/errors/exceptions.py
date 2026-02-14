"""Error handling and custom exceptions."""

class SiteGenError(Exception):
    """Base exception for site generator."""
    pass

class ConfigError(SiteGenError):
    """Configuration-related errors."""
    pass

class ConfigValidationError(ConfigError):
    """Config validation failed."""
    pass

class StateError(SiteGenError):
    """State management errors."""
    pass

class LLMError(SiteGenError):
    """LLM API errors."""
    pass

class LLMRetryExhausted(LLMError):
    """All LLM retry attempts failed."""
    pass

class ResearchError(SiteGenError):
    """Research/scraping errors."""
    pass

class ValidationError(SiteGenError):
    """Validation errors."""
    pass

class SchemaValidationError(ValidationError):
    """Schema validation failed."""
    pass

class LinkValidationError(ValidationError):
    """Link validation failed."""
    pass

class DataConsistencyError(ValidationError):
    """Data consistency check failed."""
    pass

class GenerationError(SiteGenError):
    """Content generation errors."""
    pass
