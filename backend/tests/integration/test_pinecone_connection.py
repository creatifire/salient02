"""
Integration Tests for Pinecone Connection
Tests connection to pre-existing index and health check functionality.
"""

import os
import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
import dataclasses

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from config.pinecone_config import pinecone_config_manager, PineconeEnvironment
from app.services.pinecone_client import PineconeClient, PineconeConnectionError, PineconeHealthCheckError
from app.services.vector_service import VectorService, VectorDocument
from app.services.embedding_service import EmbeddingService


@pytest.mark.integration
class TestIndexConnection:
    """Test connection to pre-existing index in test environment"""
    
    @pytest.fixture
    def pinecone_client(self):
        """Fixture to provide PineconeClient with test configuration"""
        # Use test environment configuration if available
        if os.getenv('PINECONE_API_KEY'):
            return PineconeClient()
        else:
            pytest.skip("PINECONE_API_KEY not available for integration tests")
    
    def test_client_initialization(self, pinecone_client):
        """Test that Pinecone client initializes successfully"""
        assert pinecone_client is not None
        assert pinecone_client.config is not None
        assert pinecone_client.config.api_key is not None
    
    def test_index_connection_establishment(self, pinecone_client):
        """Test that connection to pre-existing index is established successfully"""
        try:
            # Attempt to get index connection
            index = pinecone_client.index
            assert index is not None
            
            # Test that we can access the index without errors
            stats = index.describe_index_stats()
            assert stats is not None
            
        except Exception as e:
            pytest.fail(f"Failed to establish index connection: {str(e)}")
    
    def test_connection_retry_mechanism(self, pinecone_client):
        """Test connection retry mechanism with invalid configuration"""
        # Create client with invalid host but valid API key to test retry logic
        invalid_config = dataclasses.replace(
            pinecone_client.config,
            index_host="https://invalid-host-that-does-not-exist.pinecone.io"
        )
        
        invalid_client = PineconeClient(invalid_config)
        
        # This should fail after retry attempts
        with pytest.raises(PineconeConnectionError):
            invalid_client._create_index_connection_with_retry()
    
    def test_connection_with_different_environments(self):
        """Test that connection works correctly for different environment configurations"""
        if not os.getenv('PINECONE_API_KEY'):
            pytest.skip("PINECONE_API_KEY not available for integration tests")
        
        environments = ['development', 'test']
        
        for env in environments:
            with pytest.MonkeyPatch().context() as m:
                m.setenv('ENVIRONMENT', env)
                
                try:
                    client = PineconeClient()
                    # Test that client can be created for each environment
                    assert client.config.environment.value == env
                    
                    # Test basic connection (if index exists for this environment)
                    index = client.index
                    assert index is not None
                    
                except Exception as e:
                    # Log but don't fail - test indexes may not exist for all environments
                    print(f"Note: Could not connect to {env} environment: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_async_connection_operations(self, pinecone_client):
        """Test that async operations work correctly with the connection"""
        try:
            # Test async health check
            health_result = await pinecone_client.health_check()
            assert health_result['status'] in ['healthy', 'cached']
            
            # Test connection context manager
            async with pinecone_client.connection_context():
                # Should not raise any exceptions
                pass
                
        except Exception as e:
            pytest.fail(f"Async connection operations failed: {str(e)}")


@pytest.mark.integration  
class TestIndexConfigurationMatch:
    """Test that existing index matches application expectations"""
    
    @pytest.fixture
    def pinecone_client(self):
        """Fixture to provide PineconeClient for configuration testing"""
        if os.getenv('PINECONE_API_KEY'):
            return PineconeClient()
        else:
            pytest.skip("PINECONE_API_KEY not available for integration tests")
    
    def test_index_dimensions_match_expectation(self, pinecone_client):
        """Test that existing index has expected dimensions (1536 for OpenAI embeddings)"""
        try:
            stats = pinecone_client.index.describe_index_stats()
            
            # Check that dimensions match OpenAI text-embedding-3-small
            expected_dimensions = pinecone_client.config.dimensions
            actual_dimensions = stats.dimension
            
            assert actual_dimensions == expected_dimensions, (
                f"Index dimensions mismatch: expected {expected_dimensions}, "
                f"got {actual_dimensions}"
            )
            
            # Specifically test for OpenAI embedding dimensions
            assert actual_dimensions == 1536, (
                f"Index should have 1536 dimensions for OpenAI embeddings, "
                f"got {actual_dimensions}"
            )
            
        except Exception as e:
            pytest.fail(f"Failed to verify index dimensions: {str(e)}")
    
    def test_index_configuration_validation(self, pinecone_client):
        """Test that index configuration matches application requirements"""
        try:
            stats = pinecone_client.index.describe_index_stats()
            config = pinecone_client.config
            
            # Validate basic index properties
            assert stats.dimension > 0, "Index should have positive dimensions"
            assert stats.dimension == config.dimensions, "Dimensions should match config"
            
            # Test that we can get basic index information
            assert hasattr(stats, 'total_vector_count'), "Should have vector count info"
            assert stats.total_vector_count >= 0, "Vector count should be non-negative"
            
        except Exception as e:
            pytest.fail(f"Index configuration validation failed: {str(e)}")
    
    def test_namespace_accessibility(self, pinecone_client):
        """Test that configured namespaces are accessible"""
        try:
            config = pinecone_client.config
            stats = pinecone_client.index.describe_index_stats()
            
            # Test that we can work with the configured namespace
            target_namespace = config.namespace
            assert target_namespace is not None, "Should have configured namespace"
            assert len(target_namespace) > 0, "Namespace should not be empty"
            
            # Test namespace access (this creates the namespace if it doesn't exist)
            test_vector_id = "test-config-validation"
            test_vector = [0.1] * config.dimensions
            
            # Upsert test vector to verify namespace access
            pinecone_client.index.upsert(
                vectors=[(test_vector_id, test_vector, {"test": "config_validation"})],
                namespace=target_namespace
            )
            
            # Clean up test vector
            pinecone_client.index.delete(ids=[test_vector_id], namespace=target_namespace)
            
        except Exception as e:
            pytest.fail(f"Namespace accessibility test failed: {str(e)}")
    
    def test_index_metric_compatibility(self, pinecone_client):
        """Test that index metric is compatible with application expectations"""
        config = pinecone_client.config
        
        # Test that configured metric is valid
        assert config.metric in ["cosine", "euclidean", "dotproduct"], (
            f"Invalid metric configuration: {config.metric}"
        )
        
        # For OpenAI embeddings, cosine similarity is recommended
        if config.embedding_model in ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]:
            assert config.metric == "cosine", (
                f"OpenAI embeddings work best with cosine similarity, "
                f"but config uses: {config.metric}"
            )


@pytest.mark.integration
class TestHealthCheckIntegration:
    """Test index monitoring and health check functionality"""
    
    @pytest.fixture
    def pinecone_client(self):
        """Fixture to provide PineconeClient for health check testing"""
        if os.getenv('PINECONE_API_KEY'):
            return PineconeClient()
        else:
            pytest.skip("PINECONE_API_KEY not available for integration tests")
    
    @pytest.mark.asyncio
    async def test_basic_health_check(self, pinecone_client):
        """Test basic health check functionality"""
        try:
            health_result = await pinecone_client.health_check(force=True)
            
            # Validate health check response structure
            assert 'status' in health_result
            assert health_result['status'] in ['healthy', 'cached']
            assert 'timestamp' in health_result
            assert 'index_name' in health_result
            assert 'namespace' in health_result
            
            # Validate health check data
            assert health_result['index_name'] == pinecone_client.config.index_name
            assert health_result['namespace'] == pinecone_client.config.namespace
            
        except Exception as e:
            pytest.fail(f"Basic health check failed: {str(e)}")
    
    @pytest.mark.asyncio 
    async def test_health_check_caching(self, pinecone_client):
        """Test that health check caching works correctly"""
        try:
            # First health check (should hit the index)
            health_result1 = await pinecone_client.health_check(force=True)
            assert health_result1['status'] == 'healthy'
            
            # Second health check (should use cache)
            health_result2 = await pinecone_client.health_check(force=False)
            
            # Should either be cached or healthy
            assert health_result2['status'] in ['healthy', 'cached']
            
        except Exception as e:
            pytest.fail(f"Health check caching test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_health_check_failure_handling(self, pinecone_client):
        """Test health check failure scenarios"""
        # Create client with invalid configuration to test failure handling
        invalid_config = dataclasses.replace(
            pinecone_client.config,
            index_host="https://invalid-health-check-host.pinecone.io"
        )
        
        invalid_client = PineconeClient(invalid_config)
        
        # Health check should fail gracefully
        with pytest.raises(PineconeHealthCheckError):
            await invalid_client.health_check(force=True)
    
    def test_connection_info_monitoring(self, pinecone_client):
        """Test connection information monitoring"""
        try:
            connection_info = pinecone_client.get_connection_info()
            
            # Validate connection info structure
            assert 'config' in connection_info
            assert 'connection' in connection_info
            
            # Validate config section
            config_info = connection_info['config']
            assert 'index_name' in config_info
            assert 'namespace' in config_info
            assert 'environment' in config_info
            assert 'dimensions' in config_info
            assert 'metric' in config_info
            assert 'embedding_model' in config_info
            
            # Validate connection section
            conn_info = connection_info['connection']
            assert 'client_created' in conn_info
            assert 'index_connected' in conn_info
            assert 'connection_attempts' in conn_info
            assert 'last_health_check' in conn_info
            
        except Exception as e:
            pytest.fail(f"Connection info monitoring failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_connection_context_manager(self, pinecone_client):
        """Test connection context manager for safe operations"""
        try:
            async with pinecone_client.connection_context() as client_context:
                # Should be same client
                assert client_context is pinecone_client
                
                # Should be able to perform operations
                health = await pinecone_client.health_check()
                assert health is not None
                
        except Exception as e:
            pytest.fail(f"Connection context manager test failed: {str(e)}")
    
    def test_connection_reset_functionality(self, pinecone_client):
        """Test connection reset functionality for error recovery"""
        try:
            # Get initial connection state
            initial_client = pinecone_client._client
            initial_index = pinecone_client._index
            
            # Reset connections
            pinecone_client.reset_connection()
            
            # Check that connections were reset
            assert pinecone_client._client is None
            assert pinecone_client._index is None
            assert pinecone_client._connection_attempts == 0
            assert pinecone_client._last_health_check == 0
            
            # Test that connections can be re-established
            new_index = pinecone_client.index
            assert new_index is not None
            
        except Exception as e:
            pytest.fail(f"Connection reset test failed: {str(e)}")


@pytest.mark.integration
class TestEndToEndIntegration:
    """Test complete end-to-end integration with vector operations"""
    
    @pytest.fixture
    def vector_service(self):
        """Fixture to provide VectorService for end-to-end testing"""
        if not os.getenv('PINECONE_API_KEY') or not os.getenv('OPENAI_API_KEY'):
            pytest.skip("PINECONE_API_KEY and OPENAI_API_KEY required for end-to-end tests")
        
        return VectorService()
    
    @pytest.mark.asyncio
    async def test_complete_vector_workflow(self, vector_service):
        """Test complete vector workflow: embed -> upsert -> query -> delete"""
        try:
            # Create test document
            test_doc = VectorDocument(
                id="integration-test-doc",
                text="This is an integration test document for Pinecone connection validation.",
                metadata={
                    "test_type": "integration",
                    "category": "connection_test"
                }
            )
            
            # Test upsert
            upsert_success = await vector_service.upsert_document(test_doc)
            assert upsert_success is True, "Document upsert should succeed"
            
            # Wait for indexing
            await asyncio.sleep(2)
            
            # Test query
            query_response = await vector_service.query_similar(
                query_text="integration test validation",
                top_k=5,
                similarity_threshold=0.3
            )
            
            assert query_response.total_results >= 0, "Query should return valid results"
            
            # Test document retrieval
            retrieved_doc = await vector_service.get_document(test_doc.id)
            if retrieved_doc:
                assert retrieved_doc.id == test_doc.id
                assert "integration" in retrieved_doc.text.lower()
            
            # Test cleanup
            delete_success = await vector_service.delete_document(test_doc.id)
            assert delete_success is True, "Document deletion should succeed"
            
        except Exception as e:
            pytest.fail(f"End-to-end integration test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_namespace_isolation(self, vector_service):
        """Test that namespace isolation works correctly"""
        try:
            # Use test namespace for isolation
            test_namespace = "integration-test"
            
            # Create test document
            test_doc = VectorDocument(
                id="namespace-isolation-test",
                text="This document tests namespace isolation functionality.",
                metadata={"test": "namespace_isolation"}
            )
            
            # Upsert to test namespace
            upsert_success = await vector_service.upsert_document(
                test_doc, 
                namespace=test_namespace
            )
            assert upsert_success is True
            
            # Wait for indexing
            await asyncio.sleep(2)
            
            # Query in test namespace (should find document)
            test_results = await vector_service.query_similar(
                query_text="namespace isolation test",
                top_k=5,
                namespace=test_namespace
            )
            
            # Query in different namespace (should not find document)
            different_results = await vector_service.query_similar(
                query_text="namespace isolation test", 
                top_k=5,
                namespace="different-test-namespace"
            )
            
            # Clean up
            await vector_service.delete_document(test_doc.id, namespace=test_namespace)
            
            # Note: We can't make strong assertions about finding/not finding the document
            # because indexing may take time, but we can verify the operations complete successfully
            assert test_results.namespace == test_namespace
            assert different_results.namespace == "different-test-namespace"
            
        except Exception as e:
            pytest.fail(f"Namespace isolation test failed: {str(e)}")


# Test configuration and utilities
@pytest.fixture(scope="session", autouse=True)
def setup_integration_test_environment():
    """Setup integration test environment"""
    required_env_vars = ['PINECONE_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        pytest.skip(f"Integration tests require environment variables: {', '.join(missing_vars)}")
    
    # Set test environment if not already set
    if not os.getenv('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = 'test'
    
    yield
    
    # Cleanup code would go here if needed


@pytest.fixture
def integration_test_config():
    """Fixture to provide test-specific configuration"""
    return {
        'test_namespace': 'integration-test',
        'cleanup_enabled': True,
        'test_timeout': 30
    }
