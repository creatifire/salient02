"""
Unit Tests for Pinecone Infrastructure Configuration
Tests configuration validation, environment setup, and namespace strategy.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import os
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import dataclasses

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from config.pinecone_config import (
    PineconeConfigManager, 
    PineconeConfig, 
    PineconeEnvironment,
    pinecone_config_manager
)


class TestAPIKeyValidation:
    """Test API key loading from environment and configuration validation"""
    
    def test_api_key_loading_from_environment(self):
        """Test API key is properly loaded from environment variables"""
        test_api_key = "pc-test-api-key-12345"
        
        with patch.dict(os.environ, {'PINECONE_API_KEY': test_api_key}):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.api_key == test_api_key
            assert config_manager.validate_config(config) is True
    
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            config_manager = PineconeConfigManager()
            
            with pytest.raises(ValueError, match="PINECONE_API_KEY environment variable is required"):
                config_manager.get_config()
    
    def test_empty_api_key_validation_fails(self):
        """Test that empty API key fails validation"""
        config = PineconeConfig(
            api_key="",
            index_name="test-index",
            index_host="test-host",
            namespace="test",
            dimensions=1536,
            metric="cosine",
            embedding_model="text-embedding-3-small",
            environment=PineconeEnvironment.DEVELOPMENT
        )
        
        config_manager = PineconeConfigManager()
        assert config_manager.validate_config(config) is False
    
    def test_none_api_key_validation_fails(self):
        """Test that None API key fails validation"""
        config = PineconeConfig(
            api_key=None,
            index_name="test-index",
            index_host="test-host",
            namespace="test",
            dimensions=1536,
            metric="cosine",
            embedding_model="text-embedding-3-small",
            environment=PineconeEnvironment.DEVELOPMENT
        )
        
        config_manager = PineconeConfigManager()
        assert config_manager.validate_config(config) is False


class TestIndexConfigurationValidation:
    """Test application validates existing index dimensions and cosine similarity"""
    
    def test_valid_index_configuration(self):
        """Test that valid index configuration passes validation"""
        config = PineconeConfig(
            api_key="test-key",
            index_name="test-index",
            index_host="test-host",
            namespace="test",
            dimensions=1536,
            metric="cosine",
            embedding_model="text-embedding-3-small",
            environment=PineconeEnvironment.DEVELOPMENT
        )
        
        config_manager = PineconeConfigManager()
        assert config_manager.validate_config(config) is True
    
    def test_invalid_dimensions_fails_validation(self):
        """Test that invalid dimensions (<=0) fail validation"""
        config = PineconeConfig(
            api_key="test-key",
            index_name="test-index",
            index_host="test-host",
            namespace="test",
            dimensions=0,  # Invalid
            metric="cosine",
            embedding_model="text-embedding-3-small",
            environment=PineconeEnvironment.DEVELOPMENT
        )
        
        config_manager = PineconeConfigManager()
        assert config_manager.validate_config(config) is False
        
        config.dimensions = -100  # Also invalid
        assert config_manager.validate_config(config) is False
    
    def test_valid_similarity_metrics(self):
        """Test that all valid similarity metrics pass validation"""
        valid_metrics = ["cosine", "euclidean", "dotproduct"]
        
        config_manager = PineconeConfigManager()
        
        for metric in valid_metrics:
            config = PineconeConfig(
                api_key="test-key",
                index_name="test-index",
                index_host="test-host",
                namespace="test",
                dimensions=1536,
                metric=metric,
                embedding_model="text-embedding-3-small",
                environment=PineconeEnvironment.DEVELOPMENT
            )
            
            assert config_manager.validate_config(config) is True, f"Metric {metric} should be valid"
    
    def test_invalid_similarity_metric_fails_validation(self):
        """Test that invalid similarity metrics fail validation"""
        invalid_metrics = ["invalid", "manhattan", "hamming", ""]
        
        config_manager = PineconeConfigManager()
        
        for metric in invalid_metrics:
            config = PineconeConfig(
                api_key="test-key",
                index_name="test-index",
                index_host="test-host",
                namespace="test",
                dimensions=1536,
                metric=metric,
                embedding_model="text-embedding-3-small",
                environment=PineconeEnvironment.DEVELOPMENT
            )
            
            assert config_manager.validate_config(config) is False, f"Metric {metric} should be invalid"
    
    def test_openai_embedding_dimensions_validation(self):
        """Test that OpenAI embedding dimensions (1536) are correctly validated"""
        config = PineconeConfig(
            api_key="test-key",
            index_name="test-index",
            index_host="test-host",
            namespace="test",
            dimensions=1536,  # OpenAI text-embedding-3-small dimensions
            metric="cosine",
            embedding_model="text-embedding-3-small",
            environment=PineconeEnvironment.DEVELOPMENT
        )
        
        config_manager = PineconeConfigManager()
        assert config_manager.validate_config(config) is True
        assert config.dimensions == 1536
        assert config.embedding_model == "text-embedding-3-small"


class TestEnvironmentSetup:
    """Test dev/staging/prod index configuration switching"""
    
    def test_development_environment_configuration(self):
        """Test development environment specific configuration"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development', 'PINECONE_API_KEY': 'test-key'}):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.environment == PineconeEnvironment.DEVELOPMENT
            assert config.namespace == "development"
            assert config.timeout == 10  # Shorter timeout for dev
            assert config.retry_attempts == 2  # Fewer retries for dev
    
    def test_test_environment_configuration(self):
        """Test test environment specific configuration"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'test', 
            'PINECONE_API_KEY': 'test-key',
            'PINECONE_INDEX_NAME': 'base-index'
        }):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.environment == PineconeEnvironment.TEST
            assert config.namespace == "test"
            assert config.index_name == "base-index-test"  # Test suffix added
            assert config.timeout == 5  # Very short timeout for tests
            assert config.retry_attempts == 1  # No retries for tests
    
    def test_staging_environment_configuration(self):
        """Test staging environment specific configuration"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'staging', 
            'PINECONE_API_KEY': 'test-key',
            'PINECONE_INDEX_NAME': 'base-index'
        }):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.environment == PineconeEnvironment.STAGING
            assert config.namespace == "staging"
            assert config.index_name == "base-index-staging"  # Staging suffix added
    
    def test_production_environment_configuration(self):
        """Test production environment specific configuration"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production', 
            'PINECONE_API_KEY': 'test-key',
            'PINECONE_INDEX_NAME': 'base-index'
        }):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.environment == PineconeEnvironment.PRODUCTION
            assert config.namespace == "production"
            assert config.index_name == "base-index-prod"  # Production suffix added
            assert config.timeout == 60  # Longer timeout for production
            assert config.retry_attempts == 5  # More retries for production
            assert config.max_requests_per_minute == 500  # Higher rate limit
    
    def test_unknown_environment_defaults_to_development(self):
        """Test that unknown environment defaults to development"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'unknown', 'PINECONE_API_KEY': 'test-key'}):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.environment == PineconeEnvironment.DEVELOPMENT
            assert config.namespace == "development"
    
    def test_missing_environment_defaults_to_development(self):
        """Test that missing environment variable defaults to development"""
        with patch.dict(os.environ, {'PINECONE_API_KEY': 'test-key'}, clear=True):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.environment == PineconeEnvironment.DEVELOPMENT
            assert config.namespace == "development"


class TestNamespaceStrategy:
    """Test namespace selection and organization logic"""
    
    def test_default_namespace_selection(self):
        """Test default namespace selection for each environment"""
        test_cases = [
            (PineconeEnvironment.DEVELOPMENT, "development"),
            (PineconeEnvironment.TEST, "test"),
            (PineconeEnvironment.STAGING, "staging"),
            (PineconeEnvironment.PRODUCTION, "production")
        ]
        
        for environment, expected_namespace in test_cases:
            with patch.dict(os.environ, {
                'ENVIRONMENT': environment.value, 
                'PINECONE_API_KEY': 'test-key'
            }):
                config_manager = PineconeConfigManager()
                config = config_manager.get_config()
                
                assert config.namespace == expected_namespace
    
    def test_account_specific_namespace_for_production(self):
        """Test account-specific namespace generation for production multi-tenancy"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production', 'PINECONE_API_KEY': 'test-key'}):
            config_manager = PineconeConfigManager()
            
            # Test account-specific namespace
            account_namespace = config_manager.get_namespace_for_account("account-12345")
            assert account_namespace == "account-account-12345"
            
            # Test different account
            account_namespace = config_manager.get_namespace_for_account("user-67890")
            assert account_namespace == "account-user-67890"
    
    def test_account_namespace_fallback_for_non_production(self):
        """Test that non-production environments fall back to environment namespace"""
        environments = ['development', 'test', 'staging']
        
        for env in environments:
            with patch.dict(os.environ, {'ENVIRONMENT': env, 'PINECONE_API_KEY': 'test-key'}):
                config_manager = PineconeConfigManager()
                
                # Should ignore account_id and use environment namespace
                account_namespace = config_manager.get_namespace_for_account("account-12345")
                assert account_namespace == env
    
    def test_namespace_without_account_id(self):
        """Test namespace selection when no account_id is provided"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production', 'PINECONE_API_KEY': 'test-key'}):
            config_manager = PineconeConfigManager()
            
            # Should use default production namespace
            namespace = config_manager.get_namespace_for_account(None)
            assert namespace == "production"
            
            # Should also work with empty string
            namespace = config_manager.get_namespace_for_account("")
            assert namespace == "production"
    
    def test_namespace_organization_logic(self):
        """Test namespace organization follows predictable patterns"""
        # Development: use 'development'
        # Test: use 'test' 
        # Staging: use 'staging'
        # Production: use 'production' or 'account-{account_id}'
        
        with patch.dict(os.environ, {'PINECONE_API_KEY': 'test-key'}):
            config_manager = PineconeConfigManager()
            
            # Test consistent namespace generation
            for _ in range(5):  # Test multiple times to ensure consistency
                dev_namespace = config_manager.get_namespace_for_account("test-account")
                assert dev_namespace == "development"  # Default environment is development
                
        # Test explicit test environment
        with patch.dict(os.environ, {'PINECONE_API_KEY': 'test-key', 'ENVIRONMENT': 'test'}):
            config_manager = PineconeConfigManager()
            
            for _ in range(3):  # Test multiple times to ensure consistency
                test_namespace = config_manager.get_namespace_for_account("test-account") 
                assert test_namespace == "test"  # Should use 'test' when ENVIRONMENT=test
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'production', 'PINECONE_API_KEY': 'test-key'}):
            config_manager = PineconeConfigManager()
            
            # Test consistent account namespace generation
            for _ in range(5):
                prod_namespace = config_manager.get_namespace_for_account("test-account")
                assert prod_namespace == "account-test-account"


class TestConfigurationIntegration:
    """Test overall configuration integration and edge cases"""
    
    def test_global_config_manager_instance(self):
        """Test that global config manager instance works correctly"""
        with patch.dict(os.environ, {'PINECONE_API_KEY': 'test-key'}):
            config = pinecone_config_manager.get_config()
            
            assert config is not None
            assert config.api_key == "test-key"
            assert pinecone_config_manager.validate_config(config) is True
    
    def test_configuration_environment_override(self):
        """Test that environment variables properly override defaults"""
        env_overrides = {
            'PINECONE_API_KEY': 'custom-api-key',
            'PINECONE_INDEX_NAME': 'custom-index',
            'PINECONE_INDEX_HOST': 'custom-host.pinecone.io',
            'PINECONE_NAMESPACE': 'custom-namespace',
            'PINECONE_DIMENSIONS': '512',
            'PINECONE_METRIC': 'euclidean',
            'PINECONE_EMBEDDING_MODEL': 'text-embedding-ada-002',
            'ENVIRONMENT': 'development'  # Set environment to avoid overrides
        }
        
        with patch.dict(os.environ, env_overrides):
            config_manager = PineconeConfigManager()
            config = config_manager.get_config()
            
            assert config.api_key == 'custom-api-key'
            assert config.index_name == 'custom-index'
            assert config.index_host == 'custom-host.pinecone.io'
            # Note: namespace gets overridden by environment-specific configuration
            # In development environment, it will be 'development' regardless of PINECONE_NAMESPACE
            assert config.namespace == 'development'  # Environment override
            assert config.dimensions == 512
            assert config.metric == 'euclidean'
            assert config.embedding_model == 'text-embedding-ada-002'
    
    def test_configuration_validation_comprehensive(self):
        """Test comprehensive configuration validation"""
        # Valid configuration
        valid_config = PineconeConfig(
            api_key="valid-key",
            index_name="valid-index",
            index_host="valid-host.pinecone.io",
            namespace="valid-namespace",
            dimensions=1536,
            metric="cosine",
            embedding_model="text-embedding-3-small",
            environment=PineconeEnvironment.DEVELOPMENT
        )
        
        config_manager = PineconeConfigManager()
        assert config_manager.validate_config(valid_config) is True
        
        # Test each invalid configuration
        invalid_configs = [
            # Missing required fields
            dataclasses.replace(valid_config, api_key=None),
            dataclasses.replace(valid_config, index_name=""),
            dataclasses.replace(valid_config, index_host=None),
            dataclasses.replace(valid_config, namespace=""),
            # Invalid dimensions
            dataclasses.replace(valid_config, dimensions=0),
            dataclasses.replace(valid_config, dimensions=-1),
            # Invalid metric
            dataclasses.replace(valid_config, metric="invalid-metric"),
            dataclasses.replace(valid_config, metric=""),
        ]
        
        for invalid_config in invalid_configs:
            assert config_manager.validate_config(invalid_config) is False
