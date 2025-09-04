"""
Sample test data fixtures for pytest tests.
"""
import pytest


@pytest.fixture
def sample_chat_session():
    """Sample chat session data for testing."""
    return {
        "session_id": "test-session-123",
        "messages": [
            {
                "id": 1,
                "role": "user", 
                "content": "Hello, how are you?",
                "timestamp": "2024-01-01T12:00:00Z"
            },
            {
                "id": 2,
                "role": "assistant",
                "content": "Hi there! I'm doing well, thank you for asking. How can I help you today?",
                "timestamp": "2024-01-01T12:00:01Z"
            }
        ],
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:01Z"
    }


@pytest.fixture
def mock_vector_results():
    """Mock vector search results for testing."""
    return [
        {
            "id": "doc-1",
            "score": 0.95,
            "text": "Sample relevant content about AI agents and their capabilities",
            "metadata": {
                "source": "docs/ai-agents.md",
                "type": "documentation",
                "section": "introduction"
            }
        },
        {
            "id": "doc-2", 
            "score": 0.87,
            "text": "Related information about Pydantic AI framework usage",
            "metadata": {
                "source": "docs/pydantic-ai.md", 
                "type": "documentation",
                "section": "usage"
            }
        },
        {
            "id": "doc-3",
            "score": 0.78,
            "text": "Additional context about agent configuration and setup",
            "metadata": {
                "source": "docs/config.md",
                "type": "documentation", 
                "section": "configuration"
            }
        }
    ]


@pytest.fixture
def sample_agent_response():
    """Sample agent response structure for testing."""
    return {
        "content": "Based on the documentation, AI agents are software systems that can perform tasks autonomously using various tools and capabilities.",
        "citations": [
            {
                "source": "docs/ai-agents.md",
                "text": "Sample relevant content about AI agents and their capabilities",
                "score": 0.95
            }
        ],
        "metadata": {
            "agent_type": "simple_chat",
            "model_used": "openai:gpt-4o",
            "tokens_used": 156,
            "response_time_ms": 1250
        }
    }


@pytest.fixture  
def sample_tool_result():
    """Sample tool execution result for testing."""
    return {
        "tool_name": "vector_search",
        "success": True,
        "data": [
            {
                "id": "doc-1",
                "relevance_score": 0.95,
                "content": "Relevant content found"
            }
        ],
        "execution_time_ms": 340,
        "metadata": {
            "query": "AI agents capabilities",
            "results_count": 3,
            "search_namespace": "default"
        }
    }
