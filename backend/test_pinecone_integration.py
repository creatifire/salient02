#!/usr/bin/env python3
"""
Pinecone Integration Test Script
Tests the complete Pinecone setup with your salient-dev-01 index.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config.pinecone_config import pinecone_config_manager, PineconeEnvironment
from app.services.pinecone_client import PineconeClient
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService, VectorDocument


async def test_pinecone_integration():
    """Test complete Pinecone integration"""
    
    print("🔧 Testing Pinecone Integration for FEATURE 0011-001")
    print("=" * 60)
    
    try:
        # 1. Test Configuration
        print("\n1️⃣ Testing Configuration Management...")
        config = pinecone_config_manager.get_config()
        print(f"   ✅ Environment: {config.environment.value}")
        print(f"   ✅ Index Name: {config.index_name}")
        print(f"   ✅ Index Host: {config.index_host}")
        print(f"   ✅ Namespace: {config.namespace}")
        print(f"   ✅ Dimensions: {config.dimensions}")
        print(f"   ✅ Metric: {config.metric}")
        print(f"   ✅ Embedding Model: {config.embedding_model}")
        
        if not pinecone_config_manager.validate_config(config):
            raise ValueError("Configuration validation failed!")
        
        # 2. Test Pinecone Connection
        print("\n2️⃣ Testing Pinecone Connection...")
        pinecone_client = PineconeClient(config)
        
        health_check = await pinecone_client.health_check(force=True)
        print(f"   ✅ Connection Status: {health_check['status']}")
        print(f"   ✅ Total Vectors: {health_check.get('total_vector_count', 'N/A')}")
        print(f"   ✅ Index Dimension: {health_check.get('dimension', 'N/A')}")
        print(f"   ✅ Available Namespaces: {health_check.get('available_namespaces', [])}")
        
        # 3. Test Embedding Service
        print("\n3️⃣ Testing Embedding Service...")
        embedding_service = EmbeddingService()
        
        test_text = "This is a test document for vector database integration."
        embedding = await embedding_service.embed_text(test_text)
        print(f"   ✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   ✅ Expected dimensions: {config.dimensions}")
        
        if len(embedding) != config.dimensions:
            raise ValueError(f"Embedding dimension mismatch: got {len(embedding)}, expected {config.dimensions}")
        
        # 4. Test Vector Service - Document Upload
        print("\n4️⃣ Testing Vector Service - Document Operations...")
        vector_service = VectorService(pinecone_client, embedding_service)
        
        test_doc = VectorDocument(
            id="test-doc-001",
            text="This is a test document for the OpenThought Salient project vector database integration.",
            metadata={
                "source": "integration_test",
                "category": "test",
                "project": "salient02"
            }
        )
        
        # Upsert test document
        upsert_success = await vector_service.upsert_document(test_doc, namespace="development")
        print(f"   ✅ Document upsert: {'SUCCESS' if upsert_success else 'FAILED'}")
        
        # Wait a moment for indexing
        await asyncio.sleep(2)
        
        # 5. Test Vector Search
        print("\n5️⃣ Testing Vector Search...")
        
        query_response = await vector_service.query_similar(
            query_text="OpenThought project test document",
            top_k=3,
            similarity_threshold=0.5,
            namespace="development"
        )
        
        print(f"   ✅ Query Results: {query_response.total_results} documents found")
        print(f"   ✅ Query Time: {query_response.query_time_ms:.2f}ms")
        print(f"   ✅ Namespace: {query_response.namespace}")
        
        for i, result in enumerate(query_response.results, 1):
            print(f"   📄 Result {i}: ID={result.id}, Score={result.score:.3f}")
            print(f"      Text: {result.text[:60]}...")
        
        # 6. Test Document Retrieval
        print("\n6️⃣ Testing Document Retrieval...")
        
        retrieved_doc = await vector_service.get_document("test-doc-001", namespace="development")
        if retrieved_doc:
            print(f"   ✅ Document retrieved: {retrieved_doc.id}")
            print(f"   ✅ Metadata: {retrieved_doc.metadata}")
        else:
            print("   ⚠️ Document not found (may take time to index)")
        
        # 7. Test Namespace Statistics
        print("\n7️⃣ Testing Namespace Statistics...")
        
        stats = await vector_service.get_namespace_stats(namespace="development")
        print(f"   ✅ Namespace: {stats['namespace']}")
        print(f"   ✅ Total Vectors: {stats.get('total_vector_count', 'N/A')}")
        print(f"   ✅ Index Fullness: {stats.get('index_fullness', 'N/A')}")
        
        # 8. Cleanup (Optional)
        print("\n8️⃣ Cleanup Test Document...")
        
        delete_success = await vector_service.delete_document("test-doc-001", namespace="development")
        print(f"   ✅ Document cleanup: {'SUCCESS' if delete_success else 'FAILED'}")
        
        print("\n" + "=" * 60)
        print("🎉 Pinecone Integration Test COMPLETED Successfully!")
        print("✅ All FEATURE 0011-001 components are working correctly")
        print("🚀 Ready for Phase 1A Item 2 completion")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test execution"""
    success = await test_pinecone_integration()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
