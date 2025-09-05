"""
Unit Tests for Vector Service Implementation
Tests VectorService class behavior for RAG operations.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import dataclasses

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.vector_service import (
    VectorService, 
    VectorDocument, 
    VectorQueryResult, 
    VectorQueryResponse,
    get_vector_service
)
from app.services.pinecone_client import PineconeClient
from app.services.embedding_service import EmbeddingService


class TestServiceInitialization:
    """Test VectorService instantiation with proper configuration"""
    
    def test_vector_service_initialization_default(self):
        """Test VectorService initializes with default dependencies"""
        service = VectorService()
        
        assert service is not None
        assert service.pinecone_client is not None
        assert service.embedding_service is not None
    
    def test_vector_service_initialization_with_custom_dependencies(self):
        """Test VectorService initializes with custom dependencies"""
        mock_pinecone = Mock(spec=PineconeClient)
        mock_embedding = Mock(spec=EmbeddingService)
        
        service = VectorService(
            pinecone_client=mock_pinecone,
            embedding_service=mock_embedding
        )
        
        assert service.pinecone_client is mock_pinecone
        assert service.embedding_service is mock_embedding
    
    def test_vector_service_singleton_pattern(self):
        """Test that get_vector_service returns consistent instance"""
        service1 = get_vector_service()
        service2 = get_vector_service()
        
        assert service1 is service2  # Should be same instance
    
    def test_vector_document_creation(self):
        """Test VectorDocument dataclass creation and validation"""
        doc = VectorDocument(
            id="test-doc-123",
            text="This is a test document for RAG.",
            metadata={
                "source": "test_source",
                "category": "product",
                "timestamp": "2024-01-01"
            }
        )
        
        assert doc.id == "test-doc-123"
        assert "test document" in doc.text
        assert doc.metadata["source"] == "test_source"
        assert doc.embedding is None  # Should start as None
        assert doc.namespace is None  # Should start as None


class TestQueryOperations:
    """Test similarity search with various parameters (top_k, threshold)"""
    
    @pytest.fixture
    def mock_vector_service(self):
        """Fixture providing VectorService with mocked dependencies"""
        mock_pinecone = Mock(spec=PineconeClient)
        mock_embedding = Mock(spec=EmbeddingService)
        
        return VectorService(
            pinecone_client=mock_pinecone,
            embedding_service=mock_embedding
        )
    
    @pytest.mark.asyncio
    async def test_query_similar_basic_functionality(self, mock_vector_service):
        """Test basic similarity query with default parameters"""
        # Mock embedding generation
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1, 0.2, 0.3] * 512  # 1536 dimensions
        )
        
        # Mock Pinecone query response
        mock_response = Mock()
        mock_response.matches = [
            Mock(
                id="doc1",
                score=0.95,
                metadata={"text": "Test document 1", "category": "product"}
            ),
            Mock(
                id="doc2", 
                score=0.87,
                metadata={"text": "Test document 2", "category": "support"}
            )
        ]
        
        mock_vector_service.pinecone_client.index.query = Mock(return_value=mock_response)
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        # Test query
        result = await mock_vector_service.query_similar(
            query_text="test query",
            top_k=5,
            similarity_threshold=0.7
        )
        
        # Verify results
        assert isinstance(result, VectorQueryResponse)
        assert result.total_results == 2
        assert len(result.results) == 2
        assert result.results[0].score == 0.95
        assert result.results[1].score == 0.87
        assert result.namespace == "development"
        
        # Verify embedding service was called
        mock_vector_service.embedding_service.embed_text.assert_called_once_with("test query")
        
        # Verify Pinecone query was called with correct parameters
        mock_vector_service.pinecone_client.index.query.assert_called_once()
        call_args = mock_vector_service.pinecone_client.index.query.call_args
        assert call_args[1]['top_k'] == 5
        assert call_args[1]['namespace'] == "development"
    
    @pytest.mark.asyncio
    async def test_query_similar_with_threshold_filtering(self, mock_vector_service):
        """Test similarity threshold filtering works correctly"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1] * 1536
        )
        
        # Mock response with varied scores
        mock_response = Mock()
        mock_response.matches = [
            Mock(id="high", score=0.95, metadata={"text": "High relevance"}),
            Mock(id="medium", score=0.75, metadata={"text": "Medium relevance"}),
            Mock(id="low", score=0.45, metadata={"text": "Low relevance"})
        ]
        
        mock_vector_service.pinecone_client.index.query = Mock(return_value=mock_response)
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        # Test with threshold 0.7 - should filter out low score
        result = await mock_vector_service.query_similar(
            query_text="test query",
            similarity_threshold=0.7
        )
        
        assert result.total_results == 2  # Only high and medium should pass
        assert all(r.score >= 0.7 for r in result.results)
        assert result.results[0].id == "high"
        assert result.results[1].id == "medium"
    
    @pytest.mark.asyncio 
    async def test_query_similar_with_metadata_filter(self, mock_vector_service):
        """Test query with metadata filtering"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1] * 1536
        )
        
        mock_response = Mock()
        mock_response.matches = [
            Mock(id="doc1", score=0.9, metadata={"text": "Product doc", "category": "product"})
        ]
        
        mock_vector_service.pinecone_client.index.query = Mock(return_value=mock_response)
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")  
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        metadata_filter = {"category": {"$eq": "product"}}
        
        await mock_vector_service.query_similar(
            query_text="test query",
            metadata_filter=metadata_filter
        )
        
        # Verify metadata filter was passed to Pinecone
        call_args = mock_vector_service.pinecone_client.index.query.call_args
        assert call_args[1]['filter'] == metadata_filter
    
    @pytest.mark.asyncio
    async def test_query_similar_custom_namespace(self, mock_vector_service):
        """Test query with custom namespace parameter"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1] * 1536
        )
        
        mock_response = Mock()
        mock_response.matches = []
        
        mock_vector_service.pinecone_client.index.query = Mock(return_value=mock_response)
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        custom_namespace = "test-namespace"
        
        result = await mock_vector_service.query_similar(
            query_text="test query",
            namespace=custom_namespace
        )
        
        assert result.namespace == custom_namespace
        call_args = mock_vector_service.pinecone_client.index.query.call_args
        assert call_args[1]['namespace'] == custom_namespace


class TestDocumentUpsert:
    """Test single document insertion for RAG content"""
    
    @pytest.fixture
    def mock_vector_service(self):
        """Fixture providing VectorService with mocked dependencies"""
        mock_pinecone = Mock(spec=PineconeClient)
        mock_embedding = Mock(spec=EmbeddingService)
        
        return VectorService(
            pinecone_client=mock_pinecone,
            embedding_service=mock_embedding
        )
    
    @pytest.mark.asyncio
    async def test_upsert_document_without_embedding(self, mock_vector_service):
        """Test upserting document without pre-computed embedding"""
        # Mock embedding generation
        test_embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_vector_service.embedding_service.embed_text = AsyncMock(return_value=test_embedding)
        
        # Mock Pinecone operations
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        mock_vector_service.pinecone_client.index.upsert = Mock()
        # Mock config attribute
        mock_config = Mock()
        mock_config.embedding_model = "text-embedding-3-small"
        mock_vector_service.pinecone_client.config = mock_config
        
        test_doc = VectorDocument(
            id="rag-doc-001",
            text="This document contains product information for RAG responses.",
            metadata={
                "source": "product_catalog",
                "category": "electronics",
                "last_updated": "2024-01-01"
            }
        )
        
        # Test upsert
        result = await mock_vector_service.upsert_document(test_doc)
        
        assert result is True
        
        # Verify embedding was generated
        mock_vector_service.embedding_service.embed_text.assert_called_once_with(test_doc.text)
        
        # Verify Pinecone upsert was called correctly
        mock_vector_service.pinecone_client.index.upsert.assert_called_once()
        upsert_call = mock_vector_service.pinecone_client.index.upsert.call_args
        
        vectors = upsert_call[1]['vectors']
        assert len(vectors) == 1
        
        vector_data = vectors[0]
        assert vector_data['id'] == "rag-doc-001"
        assert vector_data['values'] == test_embedding
        assert vector_data['metadata']['text'] == test_doc.text
        assert vector_data['metadata']['source'] == "product_catalog"
        assert vector_data['metadata']['embedding_model'] == "text-embedding-3-small"
        assert 'created_at' in vector_data['metadata']
        
        assert upsert_call[1]['namespace'] == "development"
    
    @pytest.mark.asyncio
    async def test_upsert_document_with_pre_computed_embedding(self, mock_vector_service):
        """Test upserting document with existing embedding"""
        pre_computed_embedding = [0.5, 0.6, 0.7] * 512
        
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        mock_vector_service.pinecone_client.index.upsert = Mock()
        # Mock config attribute
        mock_config = Mock()
        mock_config.embedding_model = "text-embedding-3-small"
        mock_vector_service.pinecone_client.config = mock_config
        
        test_doc = VectorDocument(
            id="pre-embedded-doc",
            text="This document already has an embedding.",
            metadata={"source": "batch_processed"},
            embedding=pre_computed_embedding
        )
        
        result = await mock_vector_service.upsert_document(test_doc)
        
        assert result is True
        
        # Verify embedding service was NOT called (already had embedding)
        mock_vector_service.embedding_service.embed_text.assert_not_called()
        
        # Verify correct embedding was used
        upsert_call = mock_vector_service.pinecone_client.index.upsert.call_args
        vector_data = upsert_call[1]['vectors'][0]
        assert vector_data['values'] == pre_computed_embedding
    
    @pytest.mark.asyncio
    async def test_upsert_document_custom_namespace(self, mock_vector_service):
        """Test upserting document to custom namespace"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(return_value=[0.1] * 1536)
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        mock_vector_service.pinecone_client.index.upsert = Mock()
        # Mock config attribute
        mock_config = Mock()
        mock_config.embedding_model = "text-embedding-3-small"
        mock_vector_service.pinecone_client.config = mock_config
        
        test_doc = VectorDocument(
            id="custom-ns-doc",
            text="Document for custom namespace",
            metadata={"type": "test"}
        )
        
        custom_namespace = "product-docs"
        
        await mock_vector_service.upsert_document(test_doc, namespace=custom_namespace)
        
        upsert_call = mock_vector_service.pinecone_client.index.upsert.call_args
        assert upsert_call[1]['namespace'] == custom_namespace


class TestDocumentRetrieval:
    """Test fetching specific documents by ID"""
    
    @pytest.fixture
    def mock_vector_service(self):
        """Fixture providing VectorService with mocked dependencies"""
        mock_pinecone = Mock(spec=PineconeClient)
        mock_embedding = Mock(spec=EmbeddingService)
        
        return VectorService(
            pinecone_client=mock_pinecone,
            embedding_service=mock_embedding
        )
    
    @pytest.mark.asyncio
    async def test_get_document_exists(self, mock_vector_service):
        """Test retrieving document that exists"""
        # Mock Pinecone fetch response
        mock_response = Mock()
        mock_response.vectors = {
            "doc-123": Mock(
                metadata={
                    "text": "Retrieved RAG document content",
                    "source": "knowledge_base",
                    "category": "support"
                }
            )
        }
        
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        mock_vector_service.pinecone_client.index.fetch = Mock(return_value=mock_response)
        
        result = await mock_vector_service.get_document("doc-123")
        
        assert result is not None
        assert isinstance(result, VectorQueryResult)
        assert result.id == "doc-123"
        assert result.text == "Retrieved RAG document content"
        assert result.score == 1.0  # Perfect match for direct fetch
        assert result.metadata["source"] == "knowledge_base"
        assert result.namespace == "development"
        
        # Verify fetch call
        mock_vector_service.pinecone_client.index.fetch.assert_called_once_with(
            ids=["doc-123"],
            namespace="development"
        )
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, mock_vector_service):
        """Test retrieving document that doesn't exist"""
        # Mock empty response
        mock_response = Mock()
        mock_response.vectors = {}  # Empty dict means not found
        
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        mock_vector_service.pinecone_client.index.fetch = Mock(return_value=mock_response)
        
        result = await mock_vector_service.get_document("nonexistent-doc")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_document_custom_namespace(self, mock_vector_service):
        """Test retrieving document from custom namespace"""
        mock_response = Mock()
        mock_response.vectors = {
            "ns-doc": Mock(metadata={"text": "Namespace doc", "category": "test"})
        }
        
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        mock_vector_service.pinecone_client.index.fetch = Mock(return_value=mock_response)
        
        custom_namespace = "support-docs"
        
        result = await mock_vector_service.get_document("ns-doc", namespace=custom_namespace)
        
        assert result is not None
        assert result.namespace == custom_namespace
        
        # Verify correct namespace was used
        fetch_call = mock_vector_service.pinecone_client.index.fetch.call_args
        assert fetch_call[1]['namespace'] == custom_namespace


class TestInputValidation:
    """Verify proper validation of query text, document content, metadata"""
    
    def test_vector_document_validation_valid_inputs(self):
        """Test VectorDocument creation with valid inputs"""
        doc = VectorDocument(
            id="valid-doc-123",
            text="Valid document content for RAG system.",
            metadata={
                "source": "documentation",
                "confidence": 0.95,
                "tags": ["product", "support"]
            }
        )
        
        assert doc.id == "valid-doc-123"
        assert len(doc.text) > 0
        assert isinstance(doc.metadata, dict)
        assert "source" in doc.metadata
    
    def test_vector_document_validation_edge_cases(self):
        """Test VectorDocument creation with edge case inputs"""
        # Empty text should still create valid document
        doc_empty_text = VectorDocument(
            id="empty-text",
            text="",
            metadata={}
        )
        assert doc_empty_text.text == ""
        
        # Large metadata should work
        large_metadata = {f"key_{i}": f"value_{i}" for i in range(100)}
        doc_large_meta = VectorDocument(
            id="large-meta",
            text="Document with large metadata",
            metadata=large_metadata
        )
        assert len(doc_large_meta.metadata) == 100
    
    def test_vector_query_result_validation(self):
        """Test VectorQueryResult creation and validation"""
        result = VectorQueryResult(
            id="result-123",
            text="Query result content",
            score=0.85,
            metadata={"relevance": "high"},
            namespace="test"
        )
        
        assert result.id == "result-123"
        assert 0.0 <= result.score <= 1.0
        assert result.namespace == "test"
    
    def test_vector_query_response_validation(self):
        """Test VectorQueryResponse creation and validation"""
        results = [
            VectorQueryResult(
                id="r1",
                text="Result 1", 
                score=0.9,
                metadata={},
                namespace="test"
            ),
            VectorQueryResult(
                id="r2",
                text="Result 2",
                score=0.8, 
                metadata={},
                namespace="test"
            )
        ]
        
        response = VectorQueryResponse(
            results=results,
            total_results=2,
            query_time_ms=150.5,
            namespace="test"
        )
        
        assert len(response.results) == 2
        assert response.total_results == 2
        assert response.query_time_ms > 0
        assert response.namespace == "test"


class TestErrorHandling:
    """Test error scenarios (invalid embeddings, connection failures)"""
    
    @pytest.fixture
    def mock_vector_service(self):
        """Fixture providing VectorService with mocked dependencies"""
        mock_pinecone = Mock(spec=PineconeClient)
        mock_embedding = Mock(spec=EmbeddingService)
        
        return VectorService(
            pinecone_client=mock_pinecone,
            embedding_service=mock_embedding
        )
    
    @pytest.mark.asyncio
    async def test_upsert_document_embedding_failure(self, mock_vector_service):
        """Test upsert when embedding generation fails"""
        # Mock embedding service to raise exception
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            side_effect=Exception("OpenAI API error")
        )
        
        test_doc = VectorDocument(
            id="failing-doc",
            text="Document that will fail embedding",
            metadata={"source": "test"}
        )
        
        result = await mock_vector_service.upsert_document(test_doc)
        
        assert result is False  # Should return False on failure
    
    @pytest.mark.asyncio
    async def test_upsert_document_pinecone_failure(self, mock_vector_service):
        """Test upsert when Pinecone operation fails"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1] * 1536
        )
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock config attribute
        mock_config = Mock()
        mock_config.embedding_model = "test-model"
        mock_vector_service.pinecone_client.config = mock_config
        
        # Mock Pinecone connection_context to raise exception
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=Exception("Pinecone connection error"))
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        test_doc = VectorDocument(
            id="pinecone-fail-doc",
            text="Document that will fail Pinecone upsert",
            metadata={}
        )
        
        result = await mock_vector_service.upsert_document(test_doc)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_query_similar_embedding_failure(self, mock_vector_service):
        """Test query when embedding generation fails"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            side_effect=Exception("Embedding service unavailable")
        )
        
        result = await mock_vector_service.query_similar("failing query")
        
        assert isinstance(result, VectorQueryResponse)
        assert result.total_results == 0
        assert len(result.results) == 0
        assert result.query_time_ms > 0  # Should still record time
    
    @pytest.mark.asyncio
    async def test_query_similar_pinecone_failure(self, mock_vector_service):
        """Test query when Pinecone operation fails"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1] * 1536
        )
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        
        # Mock Pinecone connection_context to raise exception during query
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=Exception("Pinecone query failed"))
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        result = await mock_vector_service.query_similar("query with pinecone failure")
        
        assert isinstance(result, VectorQueryResponse)
        assert result.total_results == 0
        assert len(result.results) == 0
    
    @pytest.mark.asyncio
    async def test_get_document_failure(self, mock_vector_service):
        """Test document retrieval failure handling"""
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        
        # Mock Pinecone connection_context to raise exception during fetch
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=Exception("Fetch operation failed"))
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        result = await mock_vector_service.get_document("error-doc")
        
        assert result is None  # Should return None on failure


class TestLoguruIntegration:
    """Verify RAG operations are properly logged with appropriate levels"""
    
    @pytest.fixture
    def mock_vector_service(self):
        """Fixture providing VectorService with mocked dependencies"""
        mock_pinecone = Mock(spec=PineconeClient)
        mock_embedding = Mock(spec=EmbeddingService)
        
        return VectorService(
            pinecone_client=mock_pinecone,
            embedding_service=mock_embedding
        )
    
    @pytest.mark.asyncio
    @patch('app.services.vector_service.logger')
    async def test_upsert_document_logging(self, mock_logger, mock_vector_service):
        """Test that document upsert operations are properly logged"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1] * 1536
        )
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        mock_vector_service.pinecone_client.index.upsert = Mock()
        # Mock config attribute
        mock_config = Mock()
        mock_config.embedding_model = "test-model"
        mock_vector_service.pinecone_client.config = mock_config
        
        test_doc = VectorDocument(
            id="logged-doc",
            text="Document for logging test",
            metadata={"source": "test"}
        )
        
        await mock_vector_service.upsert_document(test_doc)
        
        # Verify info level logging was called for successful upsert
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Successfully upserted document logged-doc" in call for call in log_calls)
    
    @pytest.mark.asyncio
    @patch('app.services.vector_service.logger')
    async def test_upsert_document_error_logging(self, mock_logger, mock_vector_service):
        """Test that upsert errors are properly logged"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            side_effect=Exception("Test embedding error")
        )
        
        test_doc = VectorDocument(
            id="error-doc",
            text="Document that will cause error",
            metadata={}
        )
        
        await mock_vector_service.upsert_document(test_doc)
        
        # Verify error level logging was called
        mock_logger.error.assert_called()
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        assert any("Failed to upsert document error-doc" in call for call in error_calls)
    
    @pytest.mark.asyncio
    @patch('app.services.vector_service.logger')
    async def test_query_similar_logging(self, mock_logger, mock_vector_service):
        """Test that query operations are properly logged"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            return_value=[0.1] * 1536
        )
        
        mock_response = Mock()
        mock_response.matches = [
            Mock(id="result1", score=0.9, metadata={"text": "Result 1"})
        ]
        
        mock_vector_service.pinecone_client.index.query = Mock(return_value=mock_response)
        mock_vector_service.pinecone_client.get_namespace = Mock(return_value="development")
        # Mock connection_context as an async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock()
        mock_context.__aexit__ = AsyncMock()
        mock_vector_service.pinecone_client.connection_context = Mock(return_value=mock_context)
        
        await mock_vector_service.query_similar("test query for logging")
        
        # Verify info level logging for successful query
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        query_logs = [call for call in log_calls if "Vector query completed" in call]
        assert len(query_logs) > 0
    
    @pytest.mark.asyncio
    @patch('app.services.vector_service.logger')  
    async def test_query_similar_error_logging(self, mock_logger, mock_vector_service):
        """Test that query errors are properly logged"""
        mock_vector_service.embedding_service.embed_text = AsyncMock(
            side_effect=Exception("Query embedding failed")
        )
        
        await mock_vector_service.query_similar("failing query")
        
        # Verify error level logging was called
        mock_logger.error.assert_called()
        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
        assert any("Vector query failed" in call for call in error_calls)
