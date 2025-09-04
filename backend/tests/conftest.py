"""
Shared pytest fixtures and configuration for the backend test suite.
"""
import pytest
import asyncio
from unittest.mock import MagicMock
from typing import Dict, Any


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    return MagicMock()


@pytest.fixture
def sample_account_context():
    """Sample account context for testing."""
    return {
        "account_id": "test-account-123",
        "subscription_tier": "standard",
        "namespace": "test-namespace"
    }


@pytest.fixture
def sample_vector_config():
    """Sample vector database configuration."""
    return {
        "provider": "pinecone",
        "index_name": "test-index",
        "namespace": "test-namespace",
        "api_key": "test-api-key"
    }


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test-session-123",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }


# Test markers configuration
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
