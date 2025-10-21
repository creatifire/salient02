"""
Embedding Service
Handles text embedding generation using OpenAI's embedding models.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import asyncio
import logging
import os
from typing import List, Optional
from dataclasses import dataclass

import openai
from openai import AsyncOpenAI


logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service"""
    model: str
    api_key: str
    dimensions: int
    max_tokens: int = 8192
    batch_size: int = 100
    timeout: int = 30


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI models.
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or self._get_default_config()
        self.client = AsyncOpenAI(api_key=self.config.api_key)
    
    def _get_default_config(self) -> EmbeddingConfig:
        """Get default embedding configuration from environment"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Use environment variables or sensible defaults for embedding
        # Don't depend on Pinecone config - embedding service is independent
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
        
        return EmbeddingConfig(
            model=model,
            api_key=api_key,
            dimensions=dimensions
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Truncate text if too long
            if len(text) > self.config.max_tokens * 4:  # Rough character estimate
                text = text[:self.config.max_tokens * 4]
                logger.warning(f"Text truncated to {self.config.max_tokens * 4} characters for embedding")
            
            response = await self.client.embeddings.create(
                model=self.config.model,
                input=text,
                dimensions=self.config.dimensions
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding for text of length {len(text)} using model {self.config.model}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        total_texts = len(texts)
        batch_size = self.config.batch_size
        all_embeddings = []
        
        logger.info(f"Generating embeddings for {total_texts} texts with batch size {batch_size}")
        
        # Process in batches
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (total_texts + batch_size - 1) // batch_size
            
            logger.info(f"Processing embedding batch {batch_number}/{total_batches} ({len(batch)} texts)")
            
            try:
                # Truncate texts if too long
                processed_batch = []
                for text in batch:
                    if len(text) > self.config.max_tokens * 4:
                        text = text[:self.config.max_tokens * 4]
                        logger.warning(f"Text truncated to {self.config.max_tokens * 4} characters for embedding")
                    processed_batch.append(text)
                
                response = await self.client.embeddings.create(
                    model=self.config.model,
                    input=processed_batch,
                    dimensions=self.config.dimensions
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"Successfully generated embeddings for batch {batch_number}")
                
                # Small delay to respect rate limits
                if batch_number < total_batches:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {batch_number}: {str(e)}")
                # For now, raise the exception - could implement retry logic here
                raise
        
        logger.info(f"Successfully generated embeddings for all {total_texts} texts")
        return all_embeddings
    
    def get_model_info(self) -> dict:
        """Get information about the current embedding model"""
        return {
            "model": self.config.model,
            "dimensions": self.config.dimensions,
            "max_tokens": self.config.max_tokens,
            "batch_size": self.config.batch_size
        }


# Global embedding service instance (lazy initialization)
# Only created when actually needed (not at module import time)
_embedding_service: Optional[EmbeddingService] = None


def get_default_embedding_service() -> EmbeddingService:
    """
    Get or create the default global embedding service (lazy initialization).
    Only initializes when first accessed, not at module import time.
    This allows agent-specific services to be created without requiring
    global Pinecone configuration.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_embedding_service() -> EmbeddingService:
    """Dependency injection helper (for backwards compatibility)"""
    return get_default_embedding_service()


async def get_embedding_service_async() -> EmbeddingService:
    """Async dependency injection helper for FastAPI"""
    return get_default_embedding_service()
