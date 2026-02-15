"""
Unit tests for retry logic with exponential backoff.
"""

import pytest
import time
from lib.llm.retry import exponential_backoff, calculate_delay, should_retry
from lib.errors.exceptions import LLMRetryExhausted


@pytest.mark.unit
def test_retry_succeeds_on_first_attempt():
    """Test that no retry occurs if function succeeds on first attempt."""
    call_count = []
    
    @exponential_backoff(max_retries=3, base_delay=0.1)
    def successful_func():
        call_count.append(1)
        return "success"
    
    result = successful_func()
    
    assert result == "success"
    assert len(call_count) == 1  # Called only once


@pytest.mark.unit
def test_retry_succeeds_after_failures():
    """Test that function retries until success."""
    attempts = []
    
    @exponential_backoff(max_retries=3, base_delay=0.1)
    def flaky_func():
        attempts.append(1)
        if len(attempts) < 3:
            raise Exception("Temporary failure")
        return "success"
    
    result = flaky_func()
    
    assert result == "success"
    assert len(attempts) == 3  # Failed twice, succeeded on third


@pytest.mark.unit
def test_exponential_backoff_delays():
    """Test that delays follow exponential backoff pattern."""
    start_time = time.time()
    attempts = []
    
    @exponential_backoff(max_retries=2, base_delay=0.1, exponential_base=2.0)
    def delayed_func():
        attempts.append(time.time())
        if len(attempts) < 3:
            raise Exception("Not yet")
        return "done"
    
    delayed_func()
    
    # Verify delays between attempts
    # Attempt 1 -> wait 0.1s -> Attempt 2 -> wait 0.2s -> Attempt 3
    assert len(attempts) == 3
    
    delay1 = attempts[1] - attempts[0]
    delay2 = attempts[2] - attempts[1]
    
    # Allow some tolerance for timing
    assert 0.08 <= delay1 <= 0.15  # ~0.1s
    assert 0.18 <= delay2 <= 0.25  # ~0.2s
    
    # Second delay should be roughly twice the first
    assert 1.8 <= (delay2 / delay1) <= 2.2


@pytest.mark.unit
def test_max_retries_exhausted():
    """Test that LLMRetryExhausted is raised after max retries."""
    call_count = []
    
    @exponential_backoff(max_retries=2, base_delay=0.05)
    def always_fails():
        call_count.append(1)
        raise Exception("Always fails")
    
    with pytest.raises(LLMRetryExhausted) as exc_info:
        always_fails()
    
    # Verify exception message
    assert "Failed after 3 attempts" in str(exc_info.value)
    assert "Always fails" in str(exc_info.value)
    
    # Verify it tried the correct number of times
    assert len(call_count) == 3  # Initial + 2 retries


@pytest.mark.unit
def test_retry_with_custom_params():
    """Test that custom retry parameters work correctly."""
    attempts = []
    
    @exponential_backoff(
        max_retries=1,
        base_delay=0.2,
        max_delay=10.0,
        exponential_base=3.0
    )
    def custom_func():
        attempts.append(time.time())
        if len(attempts) < 2:
            raise Exception("Fail once")
        return "worked"
    
    result = custom_func()
    
    assert result == "worked"
    assert len(attempts) == 2
    
    # Verify delay matches custom base_delay
    delay = attempts[1] - attempts[0]
    assert 0.18 <= delay <= 0.25  # ~0.2s


@pytest.mark.unit
def test_max_delay_cap():
    """Test that delay is capped at max_delay."""
    # With base=1, exponential_base=2, attempt 10 would be 1024s
    # But max_delay=5 should cap it
    delay = calculate_delay(attempt=10, base_delay=1.0, max_delay=5.0, exponential_base=2.0)
    
    assert delay == 5.0


@pytest.mark.unit
def test_calculate_delay_progression():
    """Test that calculate_delay produces correct exponential progression."""
    delays = [
        calculate_delay(0, base_delay=1.0, exponential_base=2.0),
        calculate_delay(1, base_delay=1.0, exponential_base=2.0),
        calculate_delay(2, base_delay=1.0, exponential_base=2.0),
        calculate_delay(3, base_delay=1.0, exponential_base=2.0)
    ]
    
    assert delays == [1.0, 2.0, 4.0, 8.0]


@pytest.mark.unit
def test_calculate_delay_with_different_base():
    """Test calculate_delay with different exponential base."""
    delays = [
        calculate_delay(0, base_delay=1.0, exponential_base=3.0),
        calculate_delay(1, base_delay=1.0, exponential_base=3.0),
        calculate_delay(2, base_delay=1.0, exponential_base=3.0)
    ]
    
    assert delays == [1.0, 3.0, 9.0]


@pytest.mark.unit
def test_should_retry_all_exceptions():
    """Test should_retry returns True for all exceptions by default."""
    assert should_retry(Exception("test"))
    assert should_retry(ValueError("test"))
    assert should_retry(ConnectionError("test"))
    assert should_retry(KeyError("test"))


@pytest.mark.unit
def test_should_retry_specific_exceptions():
    """Test should_retry with specific exception types."""
    retryable = (ConnectionError, TimeoutError)
    
    # These should be retried
    assert should_retry(ConnectionError("test"), retryable)
    assert should_retry(TimeoutError("test"), retryable)
    
    # These should not be retried
    assert not should_retry(ValueError("test"), retryable)
    assert not should_retry(KeyError("test"), retryable)


@pytest.mark.unit
def test_retry_preserves_function_name():
    """Test that decorator preserves function name and docstring."""
    @exponential_backoff()
    def my_function():
        """My docstring"""
        return "result"
    
    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "My docstring"


@pytest.mark.unit
def test_retry_with_function_arguments():
    """Test that retry works with functions that take arguments."""
    call_args = []
    
    @exponential_backoff(max_retries=2, base_delay=0.05)
    def func_with_args(x, y, z=None):
        call_args.append((x, y, z))
        if len(call_args) < 2:
            raise Exception("Not yet")
        return x + y + (z or 0)
    
    result = func_with_args(1, 2, z=3)
    
    assert result == 6
    assert len(call_args) == 2
    assert all(args == (1, 2, 3) for args in call_args)


@pytest.mark.unit
def test_retry_with_kwargs():
    """Test that retry works with keyword arguments."""
    @exponential_backoff(max_retries=1, base_delay=0.05)
    def func_with_kwargs(**kwargs):
        if not hasattr(func_with_kwargs, 'called'):
            func_with_kwargs.called = True
            raise Exception("First call fails")
        return kwargs
    
    result = func_with_kwargs(name="test", value=42)
    
    assert result == {"name": "test", "value": 42}


@pytest.mark.unit
def test_zero_retries():
    """Test that max_retries=0 means no retries (fail immediately)."""
    call_count = []
    
    @exponential_backoff(max_retries=0, base_delay=0.05)
    def no_retry_func():
        call_count.append(1)
        raise Exception("Immediate failure")
    
    with pytest.raises(LLMRetryExhausted):
        no_retry_func()
    
    assert len(call_count) == 1  # Only one attempt


@pytest.mark.unit
def test_exception_chaining():
    """Test that original exception is preserved in exception chain."""
    @exponential_backoff(max_retries=1, base_delay=0.05)
    def failing_func():
        raise ValueError("Original error")
    
    with pytest.raises(LLMRetryExhausted) as exc_info:
        failing_func()
    
    # Verify exception chaining
    assert exc_info.value.__cause__.__class__ == ValueError
    assert "Original error" in str(exc_info.value.__cause__)


@pytest.mark.unit
def test_different_exception_types():
    """Test retry with different exception types."""
    exceptions = []
    
    @exponential_backoff(max_retries=2, base_delay=0.05)
    def multi_exception_func():
        attempt = len(exceptions)
        if attempt == 0:
            exc = ConnectionError("Connection failed")
        elif attempt == 1:
            exc = TimeoutError("Timeout")
        else:
            return "success"
        exceptions.append(exc)
        raise exc
    
    result = multi_exception_func()
    
    assert result == "success"
    assert len(exceptions) == 2
    assert isinstance(exceptions[0], ConnectionError)
    assert isinstance(exceptions[1], TimeoutError)
