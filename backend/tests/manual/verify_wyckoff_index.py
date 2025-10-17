#!/usr/bin/env python3
"""
Verify Wyckoff Pinecone Index Connectivity and Content
Checks that the wyckoff-poc-01 index is accessible and contains WordPress content.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Backend directory for config files
backend_dir = Path(__file__).parent.parent.parent

from backend.app.services.agent_pinecone_config import load_agent_pinecone_config
from backend.app.services.pinecone_client import PineconeClient
from backend.app.services.vector_service import VectorService
import yaml


async def verify_index():
    """Verify Pinecone index connectivity and sample query."""
    print("=" * 80)
    print("WYCKOFF PINECONE INDEX VERIFICATION")
    print("=" * 80)
    
    try:
        # Load wyckoff agent config
        config_path = backend_dir / "config" / "agent_configs" / "wyckoff" / "wyckoff_info_chat1" / "config.yaml"
        print(f"\n📄 Loading agent config from: {config_path}")
        
        with open(config_path) as f:
            agent_config = yaml.safe_load(f)
        
        # Load Pinecone config
        print("\n🔧 Loading Pinecone configuration...")
        pinecone_config = load_agent_pinecone_config(agent_config)
        
        if not pinecone_config:
            print("❌ ERROR: Vector search not enabled or config missing")
            return False
        
        print(f"✅ Pinecone config loaded:")
        print(f"   - Index: {pinecone_config.index_name}")
        print(f"   - Namespace: {pinecone_config.namespace}")
        print(f"   - Host: {pinecone_config.index_host}")
        print(f"   - Embedding model: {pinecone_config.embedding_model}")
        print(f"   - Dimensions: {pinecone_config.dimensions}")
        
        # Create Pinecone client
        print("\n🔌 Connecting to Pinecone...")
        pinecone_client = PineconeClient.create_from_agent_config(pinecone_config)
        
        # Check index stats
        print("\n📊 Fetching index statistics...")
        stats = pinecone_client.index.describe_index_stats()
        
        print(f"✅ Index statistics:")
        print(f"   - Total vectors: {stats.total_vector_count:,}")
        print(f"   - Dimension: {stats.dimension}")
        if hasattr(stats, 'namespaces') and stats.namespaces:
            print(f"   - Namespaces: {list(stats.namespaces.keys())}")
            if pinecone_config.namespace in stats.namespaces:
                ns_stats = stats.namespaces[pinecone_config.namespace]
                print(f"   - Vectors in {pinecone_config.namespace}: {ns_stats.vector_count:,}")
        
        # Sample query to verify connectivity
        print("\n🔍 Testing sample query...")
        vector_service = VectorService(pinecone_client=pinecone_client)
        
        test_queries = [
            "cardiology services",
            "emergency department",
            "visiting hours"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            results = await vector_service.query_similar(
                query_text=query,
                top_k=3,
                similarity_threshold=0.5,  # Lower threshold for testing
                namespace=pinecone_config.namespace
            )
            
            print(f"   Results: {results.total_results} found (threshold: 0.5)")
            print(f"   Query time: {results.query_time_ms:.2f}ms")
            
            if results.results:
                for i, result in enumerate(results.results[:2], 1):  # Show top 2
                    print(f"   {i}. Score: {result.score:.3f}")
                    print(f"      Text: {result.text[:100]}...")
                    if result.metadata:
                        metadata_filtered = {k: v for k, v in result.metadata.items() 
                                            if k not in ["text", "created_at", "embedding_model"]}
                        if metadata_filtered:
                            print(f"      Metadata: {metadata_filtered}")
            else:
                print("   ⚠️  No results found (index may be empty)")
        
        print("\n" + "=" * 80)
        print("✅ VERIFICATION COMPLETE - Index is accessible and queryable")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during verification:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(verify_index())
    sys.exit(0 if result else 1)

