"""
Pinecone Client Service
Manages Pinecone connections, health checks, and retry logic.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from contextlib import asynccontextmanager

from pinecone import Pinecone
try:
    from pinecone.exceptions import PineconeException
except ImportError:
    # Fallback for different pinecone versions
    PineconeException = Exception

import sys
from pathlib import Path

# Add backend directory to path for config imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from config.pinecone_config import pinecone_config_manager, PineconeConfig


logger = logging.getLogger(__name__)


class PineconeConnectionError(Exception):
    """Raised when Pinecone connection fails"""
    pass


class PineconeHealthCheckError(Exception):
    """Raised when Pinecone health check fails"""
    pass


class PineconeClient:
    """
    Pinecone client with connection management, retry logic, and health monitoring.
    """
    
    def __init__(self, config: Optional[PineconeConfig] = None):
        self.config = config or pinecone_config_manager.get_config()
        self._client: Optional[Pinecone] = None
        self._index: Optional[Any] = None
        self._connection_pool: Dict[str, Any] = {}
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
        self._connection_attempts = 0
        self._max_connection_attempts = self.config.retry_attempts
        
        # Validate configuration
        if not pinecone_config_manager.validate_config(self.config):
            raise ValueError(f"Invalid Pinecone configuration for environment: {self.config.environment}")
    
    @classmethod
    def create_from_agent_config(cls, agent_config):
        """
        Factory method to create PineconeClient from AgentPineconeConfig.
        
        Args:
            agent_config: AgentPineconeConfig instance from agent's config.yaml
            
        Returns:
            PineconeClient configured for the specific agent
        """
        from config.pinecone_config import PineconeConfig, PineconeEnvironment
        
        # Convert AgentPineconeConfig to PineconeConfig
        pinecone_config = PineconeConfig(
            api_key=agent_config.api_key,
            index_name=agent_config.index_name,
            index_host=agent_config.index_host,
            namespace=agent_config.namespace,
            dimensions=agent_config.dimensions,
            metric="cosine",  # Default metric
            embedding_model=agent_config.embedding_model,
            environment=PineconeEnvironment.DEVELOPMENT  # Will be overridden by env detection
        )
        
        return cls(config=pinecone_config)
    
    @property
    def client(self) -> Pinecone:
        """Get or create Pinecone client with connection retry"""
        if self._client is None:
            self._client = self._create_client_with_retry()
        return self._client
    
    @property
    def index(self) -> Any:
        """Get or create Pinecone index connection with retry"""
        if self._index is None:
            self._index = self._create_index_connection_with_retry()
        return self._index
    
    def _create_client_with_retry(self) -> Pinecone:
        """Create Pinecone client with retry logic"""
        for attempt in range(self._max_connection_attempts):
            try:
                logger.info(f"Creating Pinecone client (attempt {attempt + 1}/{self._max_connection_attempts})")
                
                client = Pinecone(
                    api_key=self.config.api_key,
                    # Additional configuration could be added here
                )
                
                logger.info("Pinecone client created successfully")
                self._connection_attempts = 0
                return client
                
            except Exception as e:
                self._connection_attempts += 1
                logger.warning(
                    f"Failed to create Pinecone client (attempt {attempt + 1}): {str(e)}"
                )
                
                if attempt < self._max_connection_attempts - 1:
                    sleep_time = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    raise PineconeConnectionError(
                        f"Failed to create Pinecone client after {self._max_connection_attempts} attempts: {str(e)}"
                    )
    
    def _create_index_connection_with_retry(self) -> Any:
        """Create Pinecone index connection with retry logic"""
        for attempt in range(self._max_connection_attempts):
            try:
                logger.info(f"Creating index connection (attempt {attempt + 1}/{self._max_connection_attempts})")
                
                # Remove https:// prefix if present - Pinecone client handles this
                host = self.config.index_host
                if host.startswith("https://"):
                    host = host[8:]
                
                index = self.client.Index(host=host)
                
                logger.info(f"Index connection created successfully for host: {host}")
                return index
                
            except Exception as e:
                logger.warning(
                    f"Failed to create index connection (attempt {attempt + 1}): {str(e)}"
                )
                
                if attempt < self._max_connection_attempts - 1:
                    sleep_time = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    raise PineconeConnectionError(
                        f"Failed to create index connection after {self._max_connection_attempts} attempts: {str(e)}"
                    )
    
    async def health_check(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform Pinecone health check with caching.
        
        Args:
            force: Force health check even if cached result is available
            
        Returns:
            Dict with health check results
        """
        current_time = time.time()
        
        # Use cached result if recent and not forced
        if not force and (current_time - self._last_health_check) < self._health_check_interval:
            return {"status": "cached", "message": "Using cached health check result"}
        
        try:
            logger.info("Performing Pinecone health check...")
            
            # Test basic index stats call
            stats = self.index.describe_index_stats()
            
            # Test basic namespace operation
            namespaces = list(stats.namespaces.keys()) if hasattr(stats, 'namespaces') and stats.namespaces else []
            
            health_info = {
                "status": "healthy",
                "timestamp": current_time,
                "index_name": self.config.index_name,
                "namespace": self.config.namespace,
                "available_namespaces": namespaces,
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": getattr(stats, 'index_fullness', 0),
                "connection_attempts": self._connection_attempts
            }
            
            self._last_health_check = current_time
            logger.info("Pinecone health check passed")
            
            return health_info
            
        except Exception as e:
            logger.error(f"Pinecone health check failed: {str(e)}")
            raise PineconeHealthCheckError(f"Health check failed: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test Pinecone connection without throwing exceptions"""
        try:
            await self.health_check(force=True)
            return True
        except Exception:
            return False
    
    def get_namespace(self, account_id: Optional[str] = None) -> str:
        """Get appropriate namespace for current environment and account"""
        return pinecone_config_manager.get_namespace_for_account(account_id)
    
    def reset_connection(self):
        """Reset client and index connections (useful for error recovery)"""
        logger.info("Resetting Pinecone connections...")
        self._client = None
        self._index = None
        self._connection_attempts = 0
        self._last_health_check = 0
    
    @asynccontextmanager
    async def connection_context(self):
        """Context manager for safe Pinecone operations with cleanup"""
        try:
            yield self
        except Exception as e:
            logger.error(f"Error in Pinecone operation: {str(e)}")
            # Reset connection on certain error types
            if isinstance(e, (PineconeConnectionError, PineconeException)):
                self.reset_connection()
            raise
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information for monitoring/debugging"""
        return {
            "config": {
                "index_name": self.config.index_name,
                "namespace": self.config.namespace,
                "environment": self.config.environment.value,
                "dimensions": self.config.dimensions,
                "metric": self.config.metric,
                "embedding_model": self.config.embedding_model
            },
            "connection": {
                "client_created": self._client is not None,
                "index_connected": self._index is not None,
                "connection_attempts": self._connection_attempts,
                "last_health_check": self._last_health_check
            }
        }


# Global Pinecone client instance (lazy initialization)
# Only created when actually needed (not at module import time)
_pinecone_client: Optional[PineconeClient] = None


def get_default_pinecone_client() -> PineconeClient:
    """
    Get or create the default global Pinecone client (lazy initialization).
    Only initializes when first accessed, not at module import time.
    This allows agent-specific clients to be created without requiring
    global PINECONE_API_KEY environment variable.
    """
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient()
    return _pinecone_client


async def get_pinecone_client() -> PineconeClient:
    """Dependency injection helper for FastAPI"""
    return get_default_pinecone_client()
