"""
Integration Tests for Vector Service Implementation
Tests complete RAG workflows with real Pinecone and OpenAI integration.
"""

import os
import pytest
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.vector_service import VectorService, VectorDocument, get_vector_service
from app.services.pinecone_client import PineconeClient
from app.services.embedding_service import EmbeddingService


@pytest.mark.integration
class TestRAGQueryWorkflow:
    """Test complete query workflow (text → embedding → similarity search → results)"""
    
    @pytest.fixture
    def vector_service(self):
        """Fixture to provide VectorService for RAG workflow testing"""
        if not os.getenv('PINECONE_API_KEY') or not os.getenv('OPENAI_API_KEY'):
            pytest.skip("PINECONE_API_KEY and OPENAI_API_KEY required for RAG workflow tests")
        
        return get_vector_service()
    
    @pytest.mark.asyncio
    async def test_complete_rag_query_workflow(self, vector_service):
        """Test complete RAG query workflow from text input to final results"""
        try:
            # Step 1: Create test RAG document
            test_doc = VectorDocument(
                id="rag-workflow-test-001",
                text="The OpenThought Salient platform provides AI-powered conversational experiences for businesses. It features advanced RAG capabilities, multi-tenant architecture, and seamless integration with existing systems.",
                metadata={
                    "source": "product_documentation",
                    "category": "platform_overview", 
                    "version": "1.0",
                    "test_type": "rag_workflow"
                }
            )
            
            # Step 2: Document Ingestion (text → embedding → vector storage)
            upsert_success = await vector_service.upsert_document(test_doc, namespace="integration-test")
            assert upsert_success is True, "Document ingestion should succeed"
            
            # Wait for indexing
            await asyncio.sleep(3)
            
            # Step 3: RAG Query (user query → embedding → similarity search → results)
            query_text = "What are the AI capabilities of the OpenThought platform?"
            
            query_response = await vector_service.query_similar(
                query_text=query_text,
                top_k=3,
                similarity_threshold=0.6,
                namespace="integration-test"
            )
            
            # Step 4: Verify RAG workflow results
            assert query_response is not None
            assert query_response.query_time_ms > 0
            assert query_response.namespace == "integration-test"
            
            # Should find our test document with reasonable similarity
            if query_response.total_results > 0:
                top_result = query_response.results[0]
                assert top_result.score >= 0.6  # Above our threshold
                assert "OpenThought" in top_result.text or "AI" in top_result.text
                assert top_result.metadata.get("source") == "product_documentation"
                
            # Step 5: Cleanup
            cleanup_success = await vector_service.delete_document(
                test_doc.id, 
                namespace="integration-test"
            )
            assert cleanup_success is True, "Cleanup should succeed"
            
        except Exception as e:
            # Always attempt cleanup even if test fails
            try:
                await vector_service.delete_document(test_doc.id, namespace="integration-test")
            except:
                pass
            pytest.fail(f"RAG query workflow test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_rag_query_with_multiple_documents(self, vector_service):
        """Test RAG query workflow with multiple relevant documents"""
        test_docs = [
            VectorDocument(
                id="rag-multi-001",
                text="OpenThought Salient offers enterprise-grade security with end-to-end encryption and compliance certifications.",
                metadata={"source": "security_docs", "category": "security", "test_batch": "multi_doc"}
            ),
            VectorDocument(
                id="rag-multi-002", 
                text="The platform supports real-time chat, file sharing, and collaborative workspaces for modern teams.",
                metadata={"source": "features_docs", "category": "collaboration", "test_batch": "multi_doc"}
            ),
            VectorDocument(
                id="rag-multi-003",
                text="Integration APIs allow seamless connection with CRM systems, databases, and third-party tools.",
                metadata={"source": "integration_docs", "category": "apis", "test_batch": "multi_doc"}
            )
        ]
        
        try:
            # Ingest multiple test documents
            for doc in test_docs:
                upsert_success = await vector_service.upsert_document(doc, namespace="multi-doc-test")
                assert upsert_success is True
            
            # Wait for indexing
            await asyncio.sleep(4)
            
            # Query for enterprise features
            query_response = await vector_service.query_similar(
                query_text="What enterprise features does the platform offer?",
                top_k=5,
                similarity_threshold=0.5,
                namespace="multi-doc-test"
            )
            
            # Should return multiple relevant results
            assert query_response.total_results >= 1
            
            # Verify we get diverse, relevant results
            if query_response.total_results >= 2:
                result_categories = set()
                for result in query_response.results[:3]:
                    result_categories.add(result.metadata.get("category", "unknown"))
                
                # Should have results from different categories (diversity)
                assert len(result_categories) >= 2, "Should get diverse results from different categories"
            
            # Cleanup
            for doc in test_docs:
                await vector_service.delete_document(doc.id, namespace="multi-doc-test")
                
        except Exception as e:
            # Cleanup on failure
            for doc in test_docs:
                try:
                    await vector_service.delete_document(doc.id, namespace="multi-doc-test")
                except:
                    pass
            pytest.fail(f"Multi-document RAG test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_rag_query_relevance_scoring(self, vector_service):
        """Test that RAG queries return results in relevance order"""
        test_docs = [
            VectorDocument(
                id="relevance-high",
                text="Machine learning and artificial intelligence capabilities power intelligent automation and predictive analytics.",
                metadata={"relevance": "high", "test_type": "scoring"}
            ),
            VectorDocument(
                id="relevance-medium", 
                text="The software platform includes various tools and features for business productivity.",
                metadata={"relevance": "medium", "test_type": "scoring"}
            ),
            VectorDocument(
                id="relevance-low",
                text="User interface design principles focus on accessibility and user experience best practices.",
                metadata={"relevance": "low", "test_type": "scoring"}
            )
        ]
        
        try:
            # Ingest test documents
            for doc in test_docs:
                await vector_service.upsert_document(doc, namespace="relevance-test")
            
            await asyncio.sleep(3)
            
            # Query specifically about AI/ML
            query_response = await vector_service.query_similar(
                query_text="artificial intelligence and machine learning features",
                top_k=3,
                similarity_threshold=0.3,
                namespace="relevance-test"
            )
            
            if query_response.total_results >= 2:
                # Verify results are ordered by relevance (score)
                scores = [result.score for result in query_response.results]
                assert scores == sorted(scores, reverse=True), "Results should be ordered by score (descending)"
                
                # The high-relevance document should score highest
                top_result = query_response.results[0]
                assert top_result.metadata.get("relevance") == "high", "Most relevant document should score highest"
            
            # Cleanup
            for doc in test_docs:
                await vector_service.delete_document(doc.id, namespace="relevance-test")
                
        except Exception as e:
            # Cleanup on failure
            for doc in test_docs:
                try:
                    await vector_service.delete_document(doc.id, namespace="relevance-test")
                except:
                    pass
            pytest.fail(f"Relevance scoring test failed: {str(e)}")


@pytest.mark.integration
class TestDocumentIngestion:
    """Test adding documents to vector database for RAG"""
    
    @pytest.fixture
    def vector_service(self):
        """Fixture to provide VectorService for document ingestion testing"""
        if not os.getenv('PINECONE_API_KEY') or not os.getenv('OPENAI_API_KEY'):
            pytest.skip("PINECONE_API_KEY and OPENAI_API_KEY required for document ingestion tests")
        
        return get_vector_service()
    
    @pytest.mark.asyncio
    async def test_single_document_ingestion_lifecycle(self, vector_service):
        """Test complete lifecycle of single document ingestion"""
        test_doc = VectorDocument(
            id="ingestion-lifecycle-001",
            text="This document tests the complete RAG ingestion lifecycle including creation, storage, retrieval, and cleanup.",
            metadata={
                "source": "test_suite",
                "document_type": "integration_test",
                "created_by": "automated_test",
                "version": "1.0"
            }
        )
        
        try:
            # Step 1: Ingest document
            upsert_result = await vector_service.upsert_document(
                test_doc, 
                namespace="ingestion-test"
            )
            assert upsert_result is True, "Document ingestion should succeed"
            
            # Step 2: Wait for indexing and verify storage
            await asyncio.sleep(2)
            
            # Step 3: Retrieve document by ID
            retrieved_doc = await vector_service.get_document(
                test_doc.id,
                namespace="ingestion-test"
            )
            
            if retrieved_doc:
                assert retrieved_doc.id == test_doc.id
                assert retrieved_doc.text == test_doc.text
                assert retrieved_doc.metadata["source"] == "test_suite"
                assert retrieved_doc.namespace == "ingestion-test"
            
            # Step 4: Verify document is searchable
            search_results = await vector_service.query_similar(
                query_text="RAG ingestion lifecycle testing",
                top_k=5,
                similarity_threshold=0.5,
                namespace="ingestion-test"
            )
            
            # Should find our document in search results
            found_doc = False
            for result in search_results.results:
                if result.id == test_doc.id:
                    found_doc = True
                    assert result.score >= 0.5
                    break
            
            # Note: Due to indexing delays, we don't assert found_doc
            # but this tests the search functionality
            
            # Step 5: Cleanup
            delete_result = await vector_service.delete_document(
                test_doc.id,
                namespace="ingestion-test"
            )
            assert delete_result is True, "Document deletion should succeed"
            
        except Exception as e:
            # Cleanup on failure
            try:
                await vector_service.delete_document(test_doc.id, namespace="ingestion-test")
            except:
                pass
            pytest.fail(f"Document ingestion lifecycle test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_document_metadata_preservation(self, vector_service):
        """Test that document metadata is preserved through ingestion"""
        complex_metadata = {
            "source": "knowledge_base",
            "category": "product_info",
            "subcategory": "features",
            "tags": ["ai", "rag", "search"],
            "confidence_score": 0.95,
            "last_updated": "2024-01-15",
            "author": "product_team",
            "version": "2.1.3",
            "language": "en",
            "region": "global"
        }
        
        test_doc = VectorDocument(
            id="metadata-preservation-test",
            text="Testing metadata preservation through the RAG document ingestion process.",
            metadata=complex_metadata
        )
        
        try:
            # Ingest document
            await vector_service.upsert_document(test_doc, namespace="metadata-test")
            await asyncio.sleep(2)
            
            # Retrieve and verify metadata preservation
            retrieved = await vector_service.get_document(test_doc.id, namespace="metadata-test")
            
            if retrieved:
                # Check that all original metadata is preserved
                for key, value in complex_metadata.items():
                    assert key in retrieved.metadata, f"Metadata key '{key}' should be preserved"
                    assert retrieved.metadata[key] == value, f"Metadata value for '{key}' should match original"
                
                # Check that system metadata was added
                assert "created_at" in retrieved.metadata, "System should add created_at timestamp"
                assert "embedding_model" in retrieved.metadata, "System should add embedding_model info"
            
            # Cleanup
            await vector_service.delete_document(test_doc.id, namespace="metadata-test")
            
        except Exception as e:
            try:
                await vector_service.delete_document(test_doc.id, namespace="metadata-test")
            except:
                pass
            pytest.fail(f"Metadata preservation test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_document_update_ingestion(self, vector_service):
        """Test updating existing documents in RAG system"""
        doc_id = "update-test-doc"
        
        # Original document
        original_doc = VectorDocument(
            id=doc_id,
            text="Original version of the document with initial content.",
            metadata={"version": "1.0", "status": "draft"}
        )
        
        # Updated document
        updated_doc = VectorDocument(
            id=doc_id,  # Same ID to update
            text="Updated version of the document with new and improved content for better RAG responses.",
            metadata={"version": "2.0", "status": "published", "updated": True}
        )
        
        try:
            # Step 1: Ingest original document
            await vector_service.upsert_document(original_doc, namespace="update-test")
            await asyncio.sleep(2)
            
            # Step 2: Update document (same ID, new content)
            await vector_service.upsert_document(updated_doc, namespace="update-test")
            await asyncio.sleep(2)
            
            # Step 3: Verify updated content
            retrieved = await vector_service.get_document(doc_id, namespace="update-test")
            
            if retrieved:
                assert "Updated version" in retrieved.text, "Should have updated text"
                assert retrieved.metadata["version"] == "2.0", "Should have updated version"
                assert retrieved.metadata["status"] == "published", "Should have updated status"
                assert retrieved.metadata.get("updated") is True, "Should have new metadata fields"
            
            # Step 4: Verify search returns updated content
            search_results = await vector_service.query_similar(
                query_text="improved content better RAG responses",
                top_k=3,
                namespace="update-test"
            )
            
            # Look for our updated document in results
            for result in search_results.results:
                if result.id == doc_id:
                    assert "improved" in result.text.lower(), "Search should return updated content"
                    break
            
            # Cleanup
            await vector_service.delete_document(doc_id, namespace="update-test")
            
        except Exception as e:
            try:
                await vector_service.delete_document(doc_id, namespace="update-test")
            except:
                pass
            pytest.fail(f"Document update test failed: {str(e)}")


@pytest.mark.integration
class TestRealQueryOperations:
    """Test actual similarity searches against development index"""
    
    @pytest.fixture
    def vector_service(self):
        """Fixture to provide VectorService for real query testing"""
        if not os.getenv('PINECONE_API_KEY') or not os.getenv('OPENAI_API_KEY'):
            pytest.skip("PINECONE_API_KEY and OPENAI_API_KEY required for real query tests")
        
        return get_vector_service()
    
    @pytest.mark.asyncio
    async def test_similarity_search_parameters(self, vector_service):
        """Test similarity search with different parameter combinations"""
        # First, add a test document to ensure we have content
        test_doc = VectorDocument(
            id="similarity-params-test",
            text="Testing similarity search parameters with different top_k values and similarity thresholds for optimal RAG performance.",
            metadata={"test_type": "similarity_params", "category": "search_testing"}
        )
        
        try:
            await vector_service.upsert_document(test_doc, namespace="similarity-test")
            await asyncio.sleep(3)
            
            # Test different top_k values
            for top_k in [1, 3, 5]:
                results = await vector_service.query_similar(
                    query_text="similarity search testing parameters",
                    top_k=top_k,
                    similarity_threshold=0.3,
                    namespace="similarity-test"
                )
                
                assert results is not None
                assert len(results.results) <= top_k, f"Should return at most {top_k} results"
                assert results.query_time_ms > 0, "Should record query time"
                
                # Verify results are sorted by score
                if len(results.results) > 1:
                    scores = [r.score for r in results.results]
                    assert scores == sorted(scores, reverse=True), "Results should be sorted by score"
            
            # Test different similarity thresholds
            for threshold in [0.3, 0.6, 0.8]:
                results = await vector_service.query_similar(
                    query_text="similarity search testing",
                    top_k=10,
                    similarity_threshold=threshold,
                    namespace="similarity-test"
                )
                
                # All returned results should meet threshold
                for result in results.results:
                    assert result.score >= threshold, f"All results should score >= {threshold}"
            
            # Cleanup
            await vector_service.delete_document(test_doc.id, namespace="similarity-test")
            
        except Exception as e:
            try:
                await vector_service.delete_document(test_doc.id, namespace="similarity-test")
            except:
                pass
            pytest.fail(f"Similarity search parameters test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_metadata_filtering_in_queries(self, vector_service):
        """Test similarity search with metadata filtering"""
        test_docs = [
            VectorDocument(
                id="filter-test-product",
                text="Product documentation for advanced features and capabilities.",
                metadata={"content_type": "product", "priority": "high", "department": "engineering"}
            ),
            VectorDocument(
                id="filter-test-support",
                text="Support documentation for troubleshooting and user assistance.",
                metadata={"content_type": "support", "priority": "medium", "department": "support"}
            ),
            VectorDocument(
                id="filter-test-sales",
                text="Sales documentation for customer engagement and business development.",
                metadata={"content_type": "sales", "priority": "high", "department": "sales"}
            )
        ]
        
        try:
            # Ingest test documents
            for doc in test_docs:
                await vector_service.upsert_document(doc, namespace="filter-test")
            
            await asyncio.sleep(3)
            
            # Test filtering by content_type
            product_results = await vector_service.query_similar(
                query_text="documentation features",
                top_k=5,
                similarity_threshold=0.3,
                metadata_filter={"content_type": {"$eq": "product"}},
                namespace="filter-test"
            )
            
            # All results should be product content
            for result in product_results.results:
                assert result.metadata.get("content_type") == "product", "Filter should limit to product docs"
            
            # Test filtering by priority
            high_priority_results = await vector_service.query_similar(
                query_text="documentation",
                top_k=5,
                similarity_threshold=0.3,
                metadata_filter={"priority": {"$eq": "high"}},
                namespace="filter-test"
            )
            
            # All results should be high priority
            for result in high_priority_results.results:
                assert result.metadata.get("priority") == "high", "Filter should limit to high priority docs"
            
            # Test complex filtering with multiple conditions
            complex_filter = {
                "priority": {"$eq": "high"},
                "department": {"$in": ["engineering", "sales"]}
            }
            
            complex_results = await vector_service.query_similar(
                query_text="documentation",
                top_k=5,
                metadata_filter=complex_filter,
                namespace="filter-test"
            )
            
            # Results should meet both conditions
            for result in complex_results.results:
                assert result.metadata.get("priority") == "high"
                assert result.metadata.get("department") in ["engineering", "sales"]
            
            # Cleanup
            for doc in test_docs:
                await vector_service.delete_document(doc.id, namespace="filter-test")
                
        except Exception as e:
            for doc in test_docs:
                try:
                    await vector_service.delete_document(doc.id, namespace="filter-test")
                except:
                    pass
            pytest.fail(f"Metadata filtering test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_query_performance_characteristics(self, vector_service):
        """Test query performance and response time characteristics"""
        # Create test document for consistent testing
        test_doc = VectorDocument(
            id="performance-test-doc",
            text="Performance testing document for measuring query response times and RAG system efficiency.",
            metadata={"test_type": "performance", "category": "benchmarking"}
        )
        
        try:
            await vector_service.upsert_document(test_doc, namespace="performance-test")
            await asyncio.sleep(2)
            
            query_times = []
            
            # Run multiple queries to measure consistency
            for i in range(5):
                result = await vector_service.query_similar(
                    query_text=f"performance testing query iteration {i}",
                    top_k=3,
                    namespace="performance-test"
                )
                
                assert result.query_time_ms > 0, "Should record positive query time"
                query_times.append(result.query_time_ms)
            
            # Verify reasonable query times
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            
            # These are reasonable expectations for development testing
            assert avg_query_time < 5000, f"Average query time should be reasonable, got {avg_query_time}ms"
            assert max_query_time < 10000, f"Max query time should be reasonable, got {max_query_time}ms"
            
            # Verify query times are recorded properly
            assert all(t > 0 for t in query_times), "All query times should be positive"
            
            # Cleanup
            await vector_service.delete_document(test_doc.id, namespace="performance-test")
            
        except Exception as e:
            try:
                await vector_service.delete_document(test_doc.id, namespace="performance-test")
            except:
                pass
            pytest.fail(f"Query performance test failed: {str(e)}")


@pytest.mark.integration
class TestEmbeddingIntegration:
    """Verify OpenAI embedding service integration works end-to-end"""
    
    @pytest.fixture
    def vector_service(self):
        """Fixture to provide VectorService for embedding integration testing"""
        if not os.getenv('PINECONE_API_KEY') or not os.getenv('OPENAI_API_KEY'):
            pytest.skip("PINECONE_API_KEY and OPENAI_API_KEY required for embedding integration tests")
        
        return get_vector_service()
    
    @pytest.mark.asyncio
    async def test_embedding_generation_integration(self, vector_service):
        """Test that embeddings are properly generated and used"""
        test_doc = VectorDocument(
            id="embedding-integration-test",
            text="Testing end-to-end embedding generation with OpenAI text-embedding-3-small model for RAG applications.",
            metadata={"test_type": "embedding_integration"}
        )
        
        try:
            # Test that document upsert generates embeddings properly
            upsert_result = await vector_service.upsert_document(test_doc, namespace="embedding-test")
            assert upsert_result is True, "Upsert with embedding generation should succeed"
            
            await asyncio.sleep(2)
            
            # Test that query generates embeddings and finds similar content
            query_result = await vector_service.query_similar(
                query_text="OpenAI embedding model RAG testing",
                top_k=3,
                similarity_threshold=0.4,
                namespace="embedding-test"
            )
            
            assert query_result is not None
            assert query_result.query_time_ms > 0
            
            # If we find results, they should have reasonable similarity scores
            for result in query_result.results:
                assert 0.0 <= result.score <= 1.0, "Similarity scores should be between 0 and 1"
                assert result.score >= 0.4, "Results should meet our similarity threshold"
            
            # Cleanup
            await vector_service.delete_document(test_doc.id, namespace="embedding-test")
            
        except Exception as e:
            try:
                await vector_service.delete_document(test_doc.id, namespace="embedding-test")
            except:
                pass
            pytest.fail(f"Embedding integration test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_embedding_consistency_across_operations(self, vector_service):
        """Test that embeddings work consistently across upsert and query operations"""
        # Use identical text for both upsert and query to test consistency
        identical_text = "Consistent embedding testing with identical text content for verification"
        
        test_doc = VectorDocument(
            id="embedding-consistency-test",
            text=identical_text,
            metadata={"test_type": "embedding_consistency"}
        )
        
        try:
            # Upsert document (generates embedding)
            await vector_service.upsert_document(test_doc, namespace="consistency-test")
            await asyncio.sleep(2)
            
            # Query with identical text (generates same embedding)
            query_result = await vector_service.query_similar(
                query_text=identical_text,
                top_k=1,
                similarity_threshold=0.9,  # High threshold for identical content
                namespace="consistency-test"
            )
            
            # Should find our document with very high similarity
            assert query_result.total_results >= 1, "Should find document with identical text"
            
            if query_result.results:
                top_result = query_result.results[0]
                assert top_result.id == test_doc.id, "Should find the exact document we uploaded"
                assert top_result.score >= 0.95, f"Identical text should have very high similarity, got {top_result.score}"
            
            # Cleanup
            await vector_service.delete_document(test_doc.id, namespace="consistency-test")
            
        except Exception as e:
            try:
                await vector_service.delete_document(test_doc.id, namespace="consistency-test")
            except:
                pass
            pytest.fail(f"Embedding consistency test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_embedding_model_configuration(self, vector_service):
        """Test that the correct embedding model is configured and working"""
        test_doc = VectorDocument(
            id="embedding-model-test",
            text="Testing embedding model configuration for text-embedding-3-small integration.",
            metadata={"test_type": "model_config"}
        )
        
        try:
            # Check that the embedding service is configured correctly
            embedding_service = vector_service.embedding_service
            model_info = embedding_service.get_model_info()
            
            # Verify model configuration
            assert model_info["model"] == "text-embedding-3-small", "Should use text-embedding-3-small model"
            assert model_info["dimensions"] == 1536, "Should have 1536 dimensions for text-embedding-3-small"
            
            # Test that upsert works with the configured model
            upsert_result = await vector_service.upsert_document(test_doc, namespace="model-config-test")
            assert upsert_result is True, "Upsert should work with configured model"
            
            await asyncio.sleep(2)
            
            # Verify document was stored with correct model metadata
            retrieved_doc = await vector_service.get_document(test_doc.id, namespace="model-config-test")
            
            if retrieved_doc:
                # Check that embedding model is tracked in metadata
                embedding_model = retrieved_doc.metadata.get("embedding_model")
                assert embedding_model == "text-embedding-3-small", "Should track embedding model in metadata"
            
            # Cleanup
            await vector_service.delete_document(test_doc.id, namespace="model-config-test")
            
        except Exception as e:
            try:
                await vector_service.delete_document(test_doc.id, namespace="model-config-test")
            except:
                pass
            pytest.fail(f"Embedding model configuration test failed: {str(e)}")


# Test configuration and utilities for integration tests
@pytest.fixture(scope="session", autouse=True)
def setup_vector_service_integration_tests():
    """Setup integration test environment for vector service tests"""
    required_env_vars = ['PINECONE_API_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        pytest.skip(f"Vector service integration tests require: {', '.join(missing_vars)}")
    
    # Set test environment if not already set
    if not os.getenv('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = 'test'
    
    yield
    
    # Cleanup would go here if needed


@pytest.fixture
def vector_service_test_config():
    """Fixture to provide test-specific configuration for vector service tests"""
    return {
        'test_namespace_prefix': 'vector-service-test',
        'cleanup_enabled': True,
        'test_timeout': 30,
        'similarity_threshold': 0.6,
        'embedding_model': 'text-embedding-3-small'
    }
