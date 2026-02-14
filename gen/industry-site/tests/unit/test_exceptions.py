"""
Unit tests for error handling and exceptions.
"""

import pytest
from lib.errors.exceptions import (
    SiteGenError,
    ConfigError,
    ConfigValidationError,
    StateError,
    LLMError,
    LLMRetryExhausted,
    ResearchError,
    ValidationError,
    SchemaValidationError,
    LinkValidationError,
    DataConsistencyError,
    GenerationError
)
from lib.errors.handlers import (
    handle_errors,
    format_error_message,
    log_error,
    validate_and_raise
)


@pytest.mark.unit
def test_exception_hierarchy():
    """Test that all exceptions inherit from SiteGenError."""
    # Test direct children
    assert issubclass(ConfigError, SiteGenError)
    assert issubclass(StateError, SiteGenError)
    assert issubclass(LLMError, SiteGenError)
    assert issubclass(ResearchError, SiteGenError)
    assert issubclass(ValidationError, SiteGenError)
    assert issubclass(GenerationError, SiteGenError)
    
    # Test grandchildren
    assert issubclass(ConfigValidationError, ConfigError)
    assert issubclass(ConfigValidationError, SiteGenError)
    
    assert issubclass(LLMRetryExhausted, LLMError)
    assert issubclass(LLMRetryExhausted, SiteGenError)
    
    assert issubclass(SchemaValidationError, ValidationError)
    assert issubclass(LinkValidationError, ValidationError)
    assert issubclass(DataConsistencyError, ValidationError)


@pytest.mark.unit
def test_config_error_raised():
    """Test that ConfigError can be raised and caught."""
    with pytest.raises(ConfigError) as exc_info:
        raise ConfigError("Test config error")
    
    assert "Test config error" in str(exc_info.value)
    
    # Can also be caught as SiteGenError
    with pytest.raises(SiteGenError):
        raise ConfigError("Another test")


@pytest.mark.unit
def test_validation_error_message():
    """Test that ConfigValidationError has clear message."""
    error_message = "Configuration validation failed: missing required field 'api_key'"
    
    with pytest.raises(ConfigValidationError) as exc_info:
        raise ConfigValidationError(error_message)
    
    assert error_message in str(exc_info.value)
    assert "validation" in str(exc_info.value).lower()


@pytest.mark.unit
def test_llm_error_types():
    """Test that LLMError and LLMRetryExhausted work correctly."""
    # Test LLMError
    with pytest.raises(LLMError) as exc_info:
        raise LLMError("API request failed")
    
    assert "API request failed" in str(exc_info.value)
    
    # Test LLMRetryExhausted
    with pytest.raises(LLMRetryExhausted) as exc_info:
        raise LLMRetryExhausted("All 3 retry attempts failed")
    
    assert "retry" in str(exc_info.value).lower()
    
    # LLMRetryExhausted can be caught as LLMError
    with pytest.raises(LLMError):
        raise LLMRetryExhausted("Retries exhausted")


@pytest.mark.unit
def test_handle_errors_decorator_catches_sitegen_error():
    """Test that handle_errors decorator catches SiteGenError."""
    @handle_errors(reraise=False, default_return='handled')
    def failing_function():
        raise ConfigError("Test error")
    
    result = failing_function()
    assert result == 'handled'


@pytest.mark.unit
def test_handle_errors_decorator_reraises():
    """Test that handle_errors decorator reraises when configured."""
    @handle_errors(reraise=True)
    def failing_function():
        raise ConfigError("Should be reraised")
    
    with pytest.raises(ConfigError) as exc_info:
        failing_function()
    
    assert "Should be reraised" in str(exc_info.value)


@pytest.mark.unit
def test_handle_errors_decorator_wraps_unexpected():
    """Test that unexpected errors are wrapped in SiteGenError."""
    @handle_errors(reraise=True)
    def unexpected_error():
        raise ValueError("Unexpected value error")
    
    with pytest.raises(SiteGenError) as exc_info:
        unexpected_error()
    
    assert "Unexpected error" in str(exc_info.value)
    assert "unexpected_error" in str(exc_info.value)


@pytest.mark.unit
def test_handle_errors_decorator_returns_value():
    """Test that decorator returns function value when no error."""
    @handle_errors(reraise=True)
    def successful_function():
        return "success"
    
    result = successful_function()
    assert result == "success"


@pytest.mark.unit
def test_format_error_message_without_context():
    """Test formatting error message without context."""
    error = ConfigError("Test error message")
    formatted = format_error_message(error)
    
    assert "ConfigError" in formatted
    assert "Test error message" in formatted


@pytest.mark.unit
def test_format_error_message_with_context():
    """Test formatting error message with context."""
    error = ConfigError("Config file not found")
    context = {
        'file_path': '/path/to/config.yaml',
        'function': 'load_config'
    }
    
    formatted = format_error_message(error, context)
    
    assert "ConfigError" in formatted
    assert "Config file not found" in formatted
    assert "Context:" in formatted
    assert "file_path" in formatted
    assert "/path/to/config.yaml" in formatted
    assert "function" in formatted
    assert "load_config" in formatted


@pytest.mark.unit
def test_validate_and_raise_passes_on_true():
    """Test that validate_and_raise does nothing when condition is True."""
    # Should not raise
    validate_and_raise(True, ConfigError, "Should not raise")
    
    # Should not raise with context
    validate_and_raise(
        True,
        ConfigError,
        "Should not raise",
        file='config.yaml'
    )


@pytest.mark.unit
def test_validate_and_raise_raises_on_false():
    """Test that validate_and_raise raises error when condition is False."""
    with pytest.raises(ConfigError) as exc_info:
        validate_and_raise(False, ConfigError, "Condition failed")
    
    assert "Condition failed" in str(exc_info.value)


@pytest.mark.unit
def test_validate_and_raise_with_context():
    """Test that validate_and_raise logs context."""
    with pytest.raises(ValidationError):
        validate_and_raise(
            False,
            ValidationError,
            "Validation failed",
            field='api_key',
            expected='string',
            got='None'
        )


@pytest.mark.unit
def test_all_exception_types_instantiable():
    """Test that all exception types can be instantiated."""
    exceptions = [
        SiteGenError,
        ConfigError,
        ConfigValidationError,
        StateError,
        LLMError,
        LLMRetryExhausted,
        ResearchError,
        ValidationError,
        SchemaValidationError,
        LinkValidationError,
        DataConsistencyError,
        GenerationError
    ]
    
    for exc_class in exceptions:
        # Should be able to create instance
        exc = exc_class("Test message")
        assert isinstance(exc, Exception)
        assert isinstance(exc, SiteGenError)
        assert "Test message" in str(exc)


@pytest.mark.unit
def test_exception_messages_preserved():
    """Test that exception messages are preserved correctly."""
    test_message = "This is a detailed error message with context"
    
    error = ConfigValidationError(test_message)
    assert str(error) == test_message
    
    # Test with formatting
    formatted_message = f"Error in file {'/path/to/file'}: {test_message}"
    error = LLMError(formatted_message)
    assert str(error) == formatted_message


@pytest.mark.unit
def test_nested_exception_catching():
    """Test that nested exceptions can be caught at different levels."""
    # Catch at specific level
    try:
        raise ConfigValidationError("Validation failed")
    except ConfigValidationError as e:
        assert "Validation failed" in str(e)
    
    # Catch at parent level
    try:
        raise ConfigValidationError("Validation failed")
    except ConfigError as e:
        assert "Validation failed" in str(e)
    
    # Catch at base level
    try:
        raise ConfigValidationError("Validation failed")
    except SiteGenError as e:
        assert "Validation failed" in str(e)
