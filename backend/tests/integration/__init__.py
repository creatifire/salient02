"""
Integration Tests Package
Contains tests that require external services and test full system integration.
"""

# Integration test configuration
INTEGRATION_TEST_CONFIG = {
    "requires_pinecone": True,
    "requires_openai": True,
    "test_timeout": 60,  # seconds
    "cleanup_test_data": True
}
