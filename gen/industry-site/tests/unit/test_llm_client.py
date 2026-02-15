"""
Unit tests for LLMClient class.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from lib.llm.client import LLMClient
from lib.errors.exceptions import LLMError, LLMRetryExhausted


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    with patch('lib.llm.client.OpenAI') as mock:
        yield mock


@pytest.fixture
def llm_client(mock_openai_client):
    """Create an LLMClient instance with mocked OpenAI."""
    return LLMClient(
        api_key="test-api-key",
        default_model="anthropic/claude-haiku-4.5"
    )


@pytest.mark.unit
def test_client_initialization(mock_openai_client):
    """Test that LLMClient initializes correctly."""
    client = LLMClient(
        api_key="test-key",
        base_url="https://test.api.com",
        default_model="test-model",
        max_retries=5,
        timeout=120
    )
    
    # Verify OpenAI client was initialized with correct params
    mock_openai_client.assert_called_once_with(
        base_url="https://test.api.com",
        api_key="test-key",
        timeout=120
    )
    
    # Verify client attributes
    assert client.default_model == "test-model"
    assert client.max_retries == 5
    assert client.call_count == 0
    assert client.total_tokens == 0


@pytest.mark.unit
def test_generate_text_mocked(llm_client, mock_openai_client):
    """Test generate_text with mocked API response."""
    # Setup mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Hello! How can I help you?"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 8
    mock_response.usage.total_tokens = 18
    mock_response.model = "anthropic/claude-haiku-4.5"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Call generate_text
    result = llm_client.generate_text("Say hello")
    
    # Verify response
    assert result == "Hello! How can I help you?"
    
    # Verify API was called correctly
    llm_client.client.chat.completions.create.assert_called_once()
    call_args = llm_client.client.chat.completions.create.call_args
    
    assert call_args.kwargs['model'] == "anthropic/claude-haiku-4.5"
    assert len(call_args.kwargs['messages']) == 1
    assert call_args.kwargs['messages'][0]['role'] == 'user'
    assert call_args.kwargs['messages'][0]['content'] == 'Say hello'


@pytest.mark.unit
def test_chat_with_messages(llm_client, mock_openai_client):
    """Test chat method processes messages correctly."""
    # Setup mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "I understand your question."
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.completion_tokens = 10
    mock_response.usage.total_tokens = 30
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Call chat with multiple messages
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Question?"}
    ]
    
    result = llm_client.chat(messages)
    
    # Verify response structure
    assert result['content'] == "I understand your question."
    assert result['tool_calls'] is None
    assert result['usage']['total_tokens'] == 30
    assert result['model'] == "test-model"
    assert result['finish_reason'] == "stop"


@pytest.mark.unit
def test_usage_tracking(llm_client, mock_openai_client):
    """Test that usage statistics are tracked correctly."""
    # Setup mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Make first call
    llm_client.generate_text("Test 1")
    
    stats1 = llm_client.get_usage_stats()
    assert stats1['call_count'] == 1
    assert stats1['total_tokens'] == 15
    
    # Make second call
    llm_client.generate_text("Test 2")
    
    stats2 = llm_client.get_usage_stats()
    assert stats2['call_count'] == 2
    assert stats2['total_tokens'] == 30  # 15 + 15


@pytest.mark.unit
def test_reset_stats(llm_client):
    """Test that usage statistics can be reset."""
    # Manually set some stats
    llm_client.call_count = 10
    llm_client.total_tokens = 1000
    
    # Reset
    llm_client.reset_stats()
    
    # Verify reset
    stats = llm_client.get_usage_stats()
    assert stats['call_count'] == 0
    assert stats['total_tokens'] == 0


@pytest.mark.unit
def test_retry_on_api_error(llm_client, mock_openai_client):
    """Test that retry logic is invoked on API errors."""
    # Setup mock to fail twice then succeed
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Success after retry"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "test-model"
    
    call_count = []
    
    def side_effect(*args, **kwargs):
        call_count.append(1)
        if len(call_count) < 3:
            raise Exception("Temporary API error")
        return mock_response
    
    llm_client.client.chat.completions.create = Mock(side_effect=side_effect)
    
    # Should succeed after retries
    result = llm_client.generate_text("Test")
    
    assert result == "Success after retry"
    assert len(call_count) == 3  # Failed twice, succeeded on third


@pytest.mark.unit
def test_tool_calling_response(llm_client, mock_openai_client):
    """Test that tool calling responses are handled correctly."""
    # Setup mock response with tool calls
    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "search_products"
    mock_tool_call.function.arguments = '{"query": "laptops"}'
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    mock_response.choices[0].finish_reason = "tool_calls"
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 70
    mock_response.model = "anthropic/claude-sonnet-4.5"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Call with tools
    tools = [{"type": "function", "function": {"name": "search_products"}}]
    result = llm_client.chat(
        [{"role": "user", "content": "Find laptops"}],
        tools=tools
    )
    
    # Verify tool calls in response
    assert result['tool_calls'] is not None
    assert len(result['tool_calls']) == 1
    assert result['tool_calls'][0]['id'] == "call_123"
    assert result['tool_calls'][0]['function'] == "search_products"
    assert result['tool_calls'][0]['arguments'] == '{"query": "laptops"}'
    assert result['finish_reason'] == "tool_calls"


@pytest.mark.unit
def test_no_model_raises_error(llm_client):
    """Test that missing model raises ValueError."""
    # Create client without default model
    client = LLMClient(api_key="test-key", default_model=None)
    
    with pytest.raises(ValueError) as exc_info:
        client.chat([{"role": "user", "content": "test"}])
    
    assert "No model specified" in str(exc_info.value)


@pytest.mark.unit
def test_model_override(llm_client, mock_openai_client):
    """Test that model parameter overrides default model."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "different-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Call with different model
    llm_client.chat(
        [{"role": "user", "content": "test"}],
        model="different-model"
    )
    
    # Verify the override model was used
    call_args = llm_client.client.chat.completions.create.call_args
    assert call_args.kwargs['model'] == "different-model"


@pytest.mark.unit
def test_generate_text_with_system_prompt(llm_client, mock_openai_client):
    """Test generate_text includes system prompt when provided."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Call with system prompt
    llm_client.generate_text(
        "User question",
        system_prompt="You are an expert"
    )
    
    # Verify messages include system prompt
    call_args = llm_client.client.chat.completions.create.call_args
    messages = call_args.kwargs['messages']
    
    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[0]['content'] == 'You are an expert'
    assert messages[1]['role'] == 'user'
    assert messages[1]['content'] == 'User question'


@pytest.mark.unit
def test_temperature_parameter(llm_client, mock_openai_client):
    """Test that temperature parameter is passed correctly."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Call with custom temperature
    llm_client.chat(
        [{"role": "user", "content": "test"}],
        temperature=0.3
    )
    
    call_args = llm_client.client.chat.completions.create.call_args
    assert call_args.kwargs['temperature'] == 0.3


@pytest.mark.unit
def test_max_tokens_parameter(llm_client, mock_openai_client):
    """Test that max_tokens parameter is passed correctly."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Call with max_tokens
    llm_client.chat(
        [{"role": "user", "content": "test"}],
        max_tokens=500
    )
    
    call_args = llm_client.client.chat.completions.create.call_args
    assert call_args.kwargs['max_tokens'] == 500


@pytest.mark.unit
def test_exception_wrapped_in_llm_error(llm_client, mock_openai_client):
    """Test that exceptions are wrapped in LLMError."""
    # Setup mock to always fail
    llm_client.client.chat.completions.create = Mock(
        side_effect=Exception("API error")
    )
    
    # Should raise LLMError (after retries exhausted)
    with pytest.raises((LLMError, LLMRetryExhausted)):
        llm_client.generate_text("test")


@pytest.mark.unit
def test_multiple_tool_calls(llm_client, mock_openai_client):
    """Test handling multiple tool calls in response."""
    # Setup mock response with multiple tool calls
    mock_tool_call_1 = Mock()
    mock_tool_call_1.id = "call_1"
    mock_tool_call_1.function.name = "search"
    mock_tool_call_1.function.arguments = '{"q": "test"}'
    
    mock_tool_call_2 = Mock()
    mock_tool_call_2.id = "call_2"
    mock_tool_call_2.function.name = "filter"
    mock_tool_call_2.function.arguments = '{"category": "tech"}'
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.tool_calls = [mock_tool_call_1, mock_tool_call_2]
    mock_response.choices[0].finish_reason = "tool_calls"
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 70
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = llm_client.chat([{"role": "user", "content": "test"}])
    
    # Verify multiple tool calls
    assert len(result['tool_calls']) == 2
    assert result['tool_calls'][0]['function'] == "search"
    assert result['tool_calls'][1]['function'] == "filter"


@pytest.mark.unit
def test_response_structure(llm_client, mock_openai_client):
    """Test that response has correct structure."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test content"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    result = llm_client.chat([{"role": "user", "content": "test"}])
    
    # Verify all expected keys present
    assert 'content' in result
    assert 'tool_calls' in result
    assert 'usage' in result
    assert 'model' in result
    assert 'finish_reason' in result
    
    # Verify usage structure
    assert 'prompt_tokens' in result['usage']
    assert 'completion_tokens' in result['usage']
    assert 'total_tokens' in result['usage']


@pytest.mark.unit
def test_call_count_increments(llm_client, mock_openai_client):
    """Test that call count increments with each call."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.model = "test-model"
    
    llm_client.client.chat.completions.create = Mock(return_value=mock_response)
    
    assert llm_client.call_count == 0
    
    llm_client.generate_text("Test 1")
    assert llm_client.call_count == 1
    
    llm_client.generate_text("Test 2")
    assert llm_client.call_count == 2
    
    llm_client.chat([{"role": "user", "content": "Test 3"}])
    assert llm_client.call_count == 3
