"""
Pinecone Configuration Management
Handles environment-specific Pinecone configuration and validation.
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class PineconeEnvironment(Enum):
    """Pinecone deployment environments"""
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class PineconeConfig:
    """Pinecone configuration settings"""
    api_key: str
    index_name: str
    index_host: str
    namespace: str
    dimensions: int
    metric: str
    embedding_model: str
    environment: PineconeEnvironment
    
    # Connection settings
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    max_requests_per_minute: int = 100
    batch_size: int = 100


class PineconeConfigManager:
    """Manages Pinecone configuration across environments"""
    
    def __init__(self):
        self.current_env = self._detect_environment()
    
    def _detect_environment(self) -> PineconeEnvironment:
        """Detect current environment from environment variables"""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        try:
            return PineconeEnvironment(env_name)
        except ValueError:
            # Default to development for unknown environments
            return PineconeEnvironment.DEVELOPMENT
    
    def get_config(self) -> PineconeConfig:
        """Get Pinecone configuration for current environment"""
        base_config = self._get_base_config()
        
        # Environment-specific overrides
        if self.current_env == PineconeEnvironment.DEVELOPMENT:
            return self._apply_development_config(base_config)
        elif self.current_env == PineconeEnvironment.TEST:
            return self._apply_test_config(base_config)
        elif self.current_env == PineconeEnvironment.STAGING:
            return self._apply_staging_config(base_config)
        elif self.current_env == PineconeEnvironment.PRODUCTION:
            return self._apply_production_config(base_config)
        else:
            return base_config
    
    def _get_base_config(self) -> PineconeConfig:
        """Get base configuration from environment variables"""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        return PineconeConfig(
            api_key=api_key,
            index_name=os.getenv("PINECONE_INDEX_NAME", "salient-dev-01"),
            index_host=os.getenv("PINECONE_INDEX_HOST", "https://salient-dev-01-e1nildl.svc.aped-4627-b74a.pinecone.io"),
            namespace=os.getenv("PINECONE_NAMESPACE", "development"),
            dimensions=int(os.getenv("PINECONE_DIMENSIONS", "1536")),
            metric=os.getenv("PINECONE_METRIC", "cosine"),
            embedding_model=os.getenv("PINECONE_EMBEDDING_MODEL", "text-embedding-3-small"),
            environment=self.current_env
        )
    
    def _apply_development_config(self, config: PineconeConfig) -> PineconeConfig:
        """Apply development-specific configuration"""
        config.namespace = "development"
        config.timeout = 10  # Shorter timeout for dev
        config.retry_attempts = 2  # Fewer retries for dev
        return config
    
    def _apply_test_config(self, config: PineconeConfig) -> PineconeConfig:
        """Apply test-specific configuration"""
        config.namespace = "test"
        config.index_name = f"{config.index_name}-test"
        config.timeout = 5  # Very short timeout for tests
        config.retry_attempts = 1  # No retries for tests
        return config
    
    def _apply_staging_config(self, config: PineconeConfig) -> PineconeConfig:
        """Apply staging-specific configuration"""
        config.namespace = "staging"
        config.index_name = f"{config.index_name}-staging"
        return config
    
    def _apply_production_config(self, config: PineconeConfig) -> PineconeConfig:
        """Apply production-specific configuration"""
        config.namespace = "production"
        config.index_name = f"{config.index_name}-prod"
        config.timeout = 60  # Longer timeout for production
        config.retry_attempts = 5  # More retries for production
        config.max_requests_per_minute = 500  # Higher rate limit for production
        return config
    
    def validate_config(self, config: PineconeConfig) -> bool:
        """Validate Pinecone configuration"""
        required_fields = [
            config.api_key,
            config.index_name,
            config.index_host,
            config.namespace
        ]
        
        if not all(required_fields):
            return False
        
        if config.dimensions <= 0:
            return False
        
        if config.metric not in ["cosine", "euclidean", "dotproduct"]:
            return False
        
        return True
    
    def get_namespace_for_account(self, account_id: Optional[str] = None) -> str:
        """Get namespace for account (Phase 3 multi-tenancy preparation)"""
        if self.current_env == PineconeEnvironment.PRODUCTION and account_id:
            return f"account-{account_id}"
        else:
            # Use environment-specific namespace for dev/test/staging
            return self.get_config().namespace


# Global configuration manager instance
pinecone_config_manager = PineconeConfigManager()
