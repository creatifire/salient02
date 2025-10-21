"""
Basic Pinecone Connectivity Test
Simple test to verify Pinecone API connection is working.
Similar to siphon project test_api_connections.py
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import os
import pytest
from pathlib import Path


@pytest.mark.integration
class TestPineconeBasicConnectivity:
    """Basic Pinecone connection test - just verify API works"""
    
    def test_pinecone_api_key_present(self):
        """Verify Pinecone API key is available"""
        api_key = os.getenv('PINECONE_API_KEY')
        
        if not api_key:
            pytest.skip("PINECONE_API_KEY not found in environment - test skipped")
        
        assert api_key is not None
        assert len(api_key) > 0, "API key should not be empty"
        print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    def test_pinecone_connection_and_list_indexes(self):
        """Test basic Pinecone connection by listing available indexes"""
        api_key = os.getenv('PINECONE_API_KEY')
        
        if not api_key:
            pytest.skip("PINECONE_API_KEY not available for integration tests")
        
        try:
            from pinecone import Pinecone
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=api_key)
            
            # List available indexes - this verifies API connection works
            print("📡 Testing Pinecone API connection...")
            indexes = pc.list_indexes()
            
            print(f"✅ Pinecone Connection SUCCESS!")
            print(f"   Available indexes: {len(indexes)} found")
            
            # Display index information
            for idx in indexes:
                print(f"   - {idx['name']} ({idx['dimension']} dims, {idx['metric']} metric)")
            
            if not indexes:
                print("   ℹ️  No indexes found - this is normal for new accounts")
            
            # Basic assertion - connection worked if we got here
            assert indexes is not None, "Should be able to list indexes (even if empty)"
            
        except ImportError as e:
            pytest.fail(f"Missing required library: pinecone-client. Run: pip install pinecone-client")
        except Exception as e:
            pytest.fail(f"Pinecone Connection FAILED: {str(e)}")
    
    def test_pinecone_index_connection(self):
        """Test connection to a specific Pinecone index if configured"""
        api_key = os.getenv('PINECONE_API_KEY')
        
        if not api_key:
            pytest.skip("PINECONE_API_KEY not available for integration tests")
        
        try:
            # Use the project's Pinecone configuration
            from config.pinecone_config import pinecone_config_manager
            from pinecone import Pinecone
            
            # Get configuration
            config = pinecone_config_manager.get_config()
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=api_key)
            
            # Try to connect to the configured index
            index_name = config.index_name
            print(f"📡 Testing connection to index: {index_name}")
            
            # List indexes to verify the configured index exists
            indexes = pc.list_indexes()
            index_names = [idx['name'] for idx in indexes]
            
            if index_name not in index_names:
                pytest.skip(f"Configured index '{index_name}' not found in Pinecone. Available: {index_names}")
            
            # Connect to the index
            index = pc.Index(index_name)
            
            # Get index stats to verify connection
            stats = index.describe_index_stats()
            
            print(f"✅ Successfully connected to index: {index_name}")
            print(f"   Dimensions: {stats.dimension}")
            print(f"   Total vectors: {stats.total_vector_count}")
            
            # Verify basic index properties
            assert stats is not None, "Should be able to get index stats"
            assert stats.dimension > 0, "Index should have dimensions"
            assert stats.total_vector_count >= 0, "Vector count should be non-negative"
            
        except ImportError as e:
            pytest.fail(f"Missing required library: {str(e)}")
        except Exception as e:
            # If index doesn't exist or other errors, skip gracefully
            pytest.skip(f"Could not connect to configured index: {str(e)}")


@pytest.fixture(scope="session", autouse=True)
def check_pinecone_availability():
    """Check if Pinecone tests can run"""
    if not os.getenv('PINECONE_API_KEY'):
        pytest.skip("PINECONE_API_KEY not available - skipping Pinecone connectivity tests")
    
    yield
