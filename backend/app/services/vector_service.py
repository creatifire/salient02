"""
Vector Database Service
Handles document ingestion, querying, and vector operations with Pinecone.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, UTC
import logfire

try:
    from pinecone.exceptions import PineconeException
except ImportError:
    # Fallback for different pinecone versions
    PineconeException = Exception

from backend.app.services.pinecone_client import PineconeClient, get_pinecone_client
from backend.app.services.embedding_service import get_embedding_service, EmbeddingService


logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Document for vector storage"""
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    namespace: Optional[str] = None


@dataclass
class VectorQueryResult:
    """Result from vector similarity search"""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]
    namespace: str


@dataclass
class VectorQueryResponse:
    """Complete response from vector query"""
    results: List[VectorQueryResult]
    total_results: int
    query_time_ms: float
    namespace: str


class VectorService:
    """
    Service for vector database operations including document ingestion and querying.
    """
    
    def __init__(
        self, 
        pinecone_client: Optional[PineconeClient] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        from backend.app.services.pinecone_client import pinecone_client as default_pinecone_client
        from backend.app.services.embedding_service import embedding_service as default_embedding_service
        
        self.pinecone_client = pinecone_client or default_pinecone_client
        self.embedding_service = embedding_service or default_embedding_service
    
    async def upsert_document(
        self, 
        document: VectorDocument,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Upsert a single document into the vector database.
        
        Args:
            document: Document to upsert
            namespace: Override namespace (defaults to configured namespace)
            
        Returns:
            Success status
        """
        try:
            # Generate embedding if not provided
            if document.embedding is None:
                document.embedding = await self.embedding_service.embed_text(document.text)
            
            # Determine namespace
            target_namespace = namespace or document.namespace or self.pinecone_client.get_namespace()
            
            # Prepare vector for upsert
            vector_data = {
                "id": document.id,
                "values": document.embedding,
                "metadata": {
                    **document.metadata,
                    "text": document.text,
                    "created_at": datetime.now(UTC).isoformat(),
                    "embedding_model": self.pinecone_client.config.embedding_model
                }
            }
            
            # Upsert to Pinecone
            async with self.pinecone_client.connection_context():
                self.pinecone_client.index.upsert(
                    vectors=[vector_data],
                    namespace=target_namespace
                )
            
            logger.info(f"Successfully upserted document {document.id} to namespace {target_namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert document {document.id}: {str(e)}")
            return False
    
    async def upsert_documents_batch(
        self, 
        documents: List[VectorDocument],
        namespace: Optional[str] = None,
        batch_size: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Upsert multiple documents in batches.
        
        Args:
            documents: List of documents to upsert
            namespace: Override namespace
            batch_size: Batch size (defaults to config batch_size)
            
        Returns:
            Tuple of (successful_count, total_count)
        """
        batch_size = batch_size or self.pinecone_client.config.batch_size
        total_documents = len(documents)
        successful_count = 0
        
        logger.info(f"Starting batch upsert of {total_documents} documents with batch size {batch_size}")
        
        # Process in batches
        for i in range(0, total_documents, batch_size):
            batch = documents[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (total_documents + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_number}/{total_batches} ({len(batch)} documents)")
            
            try:
                # Generate embeddings for batch
                texts = [doc.text for doc in batch if doc.embedding is None]
                if texts:
                    embeddings = await self.embedding_service.embed_texts(texts)
                    embedding_index = 0
                    for doc in batch:
                        if doc.embedding is None:
                            doc.embedding = embeddings[embedding_index]
                            embedding_index += 1
                
                # Determine namespace
                target_namespace = namespace or self.pinecone_client.get_namespace()
                
                # Prepare vectors for batch upsert
                vectors = []
                for doc in batch:
                    vectors.append({
                        "id": doc.id,
                        "values": doc.embedding,
                        "metadata": {
                            **doc.metadata,
                            "text": doc.text,
                            "created_at": datetime.now(UTC).isoformat(),
                            "embedding_model": self.pinecone_client.config.embedding_model
                        }
                    })
                
                # Batch upsert to Pinecone
                async with self.pinecone_client.connection_context():
                    self.pinecone_client.index.upsert(
                        vectors=vectors,
                        namespace=target_namespace
                    )
                
                successful_count += len(batch)
                logger.info(f"Successfully upserted batch {batch_number} to namespace {target_namespace}")
                
            except Exception as e:
                logger.error(f"Failed to upsert batch {batch_number}: {str(e)}")
                # Continue with next batch rather than failing entirely
        
        logger.info(f"Batch upsert completed: {successful_count}/{total_documents} documents successful")
        return successful_count, total_documents
    
    async def query_similar(
        self,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        namespace: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> VectorQueryResponse:
        """
        Query for similar documents using text similarity.
        
        Args:
            query_text: Text to search for similar documents
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            namespace: Target namespace
            metadata_filter: Pinecone metadata filter
            include_metadata: Include metadata in results
            
        Returns:
            Query response with results
        """
        start_time = asyncio.get_event_loop().time()
        target_namespace = namespace or self.pinecone_client.get_namespace()
        
        # Logfire span for entire vector search operation
        with logfire.span(
            'pinecone.query',
            query_text=query_text[:100],  # Truncate for readability
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            namespace=target_namespace,
            metadata_filter=metadata_filter
        ) as span:
            try:
                # Generate query embedding with nested span
                with logfire.span('pinecone.embedding', query_length=len(query_text)):
                    query_embedding = await self.embedding_service.embed_text(query_text)
                    span.set_attribute('embedding_dimensions', len(query_embedding))
                
                # Query Pinecone with nested span
                with logfire.span(
                    'pinecone.search',
                    index_name=self.pinecone_client.config.index_name if hasattr(self.pinecone_client, 'config') else 'unknown'
                ):
                    async with self.pinecone_client.connection_context():
                        response = self.pinecone_client.index.query(
                            vector=query_embedding,
                            top_k=top_k,
                            include_values=False,
                            include_metadata=include_metadata,
                            namespace=target_namespace,
                            filter=metadata_filter
                        )
                    
                    # Log raw response stats
                    span.set_attribute('raw_matches_count', len(response.matches))
                
                # Process results
                results = []
                for match in response.matches:
                    # Apply similarity threshold
                    if match.score >= similarity_threshold:
                        result = VectorQueryResult(
                            id=match.id,
                            text=match.metadata.get("text", "") if match.metadata else "",
                            score=match.score,
                            metadata=match.metadata or {},
                            namespace=target_namespace
                        )
                        results.append(result)
                
                query_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Log response details to Logfire span
                span.set_attribute('results_count', len(results))
                span.set_attribute('filtered_count', len(response.matches) - len(results))
                span.set_attribute('query_time_ms', query_time_ms)
                if results:
                    span.set_attribute('top_score', results[0].score)
                    span.set_attribute('lowest_score', results[-1].score)
                    # Capture preview of results (first 3 IDs and scores)
                    span.set_attribute('results_preview', [
                        {'id': r.id, 'score': round(r.score, 3)} 
                        for r in results[:3]
                    ])
                
                logger.info(
                    f"Vector query completed: {len(results)} results above threshold {similarity_threshold} "
                    f"in {query_time_ms:.2f}ms for namespace {target_namespace}"
                )
                
                return VectorQueryResponse(
                    results=results,
                    total_results=len(results),
                    query_time_ms=query_time_ms,
                    namespace=target_namespace
                )
                
            except Exception as e:
                logger.error(f"Vector query failed: {str(e)}")
                query_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Log error to Logfire span
                span.set_attribute('error', str(e))
                span.set_attribute('error_type', type(e).__name__)
                span.set_attribute('query_time_ms', query_time_ms)
                
                return VectorQueryResponse(
                    results=[],
                    total_results=0,
                    query_time_ms=query_time_ms,
                    namespace=namespace or "unknown"
                )
    
    async def delete_document(
        self, 
        document_id: str,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Delete a document from the vector database.
        
        Args:
            document_id: ID of document to delete
            namespace: Target namespace
            
        Returns:
            Success status
        """
        try:
            target_namespace = namespace or self.pinecone_client.get_namespace()
            
            async with self.pinecone_client.connection_context():
                self.pinecone_client.index.delete(
                    ids=[document_id],
                    namespace=target_namespace
                )
            
            logger.info(f"Successfully deleted document {document_id} from namespace {target_namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
    
    async def delete_namespace(self, namespace: str) -> bool:
        """
        Delete all documents in a namespace.
        
        Args:
            namespace: Namespace to clear
            
        Returns:
            Success status
        """
        try:
            async with self.pinecone_client.connection_context():
                self.pinecone_client.index.delete(
                    delete_all=True,
                    namespace=namespace
                )
            
            logger.info(f"Successfully cleared namespace {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear namespace {namespace}: {str(e)}")
            return False
    
    async def get_document(
        self, 
        document_id: str,
        namespace: Optional[str] = None
    ) -> Optional[VectorQueryResult]:
        """
        Fetch a specific document by ID.
        
        Args:
            document_id: Document ID to fetch
            namespace: Target namespace
            
        Returns:
            Document if found, None otherwise
        """
        try:
            target_namespace = namespace or self.pinecone_client.get_namespace()
            
            async with self.pinecone_client.connection_context():
                response = self.pinecone_client.index.fetch(
                    ids=[document_id],
                    namespace=target_namespace
                )
            
            if document_id in response.vectors:
                vector = response.vectors[document_id]
                return VectorQueryResult(
                    id=document_id,
                    text=vector.metadata.get("text", "") if vector.metadata else "",
                    score=1.0,  # Perfect match since we're fetching by ID
                    metadata=vector.metadata or {},
                    namespace=target_namespace
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch document {document_id}: {str(e)}")
            return None
    
    async def get_namespace_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a namespace.
        
        Args:
            namespace: Target namespace
            
        Returns:
            Namespace statistics
        """
        try:
            target_namespace = namespace or self.pinecone_client.get_namespace()
            
            async with self.pinecone_client.connection_context():
                stats = self.pinecone_client.index.describe_index_stats()
            
            namespace_stats = {
                "namespace": target_namespace,
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": getattr(stats, 'index_fullness', 0)
            }
            
            # Add namespace-specific stats if available
            if hasattr(stats, 'namespaces') and stats.namespaces:
                if target_namespace in stats.namespaces:
                    ns_info = stats.namespaces[target_namespace]
                    namespace_stats.update({
                        "namespace_vector_count": ns_info.vector_count
                    })
            
            return namespace_stats
            
        except Exception as e:
            logger.error(f"Failed to get namespace stats for {namespace}: {str(e)}")
            return {"namespace": target_namespace, "error": str(e)}


# Global vector service instance (will be initialized when first imported)  
vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Dependency injection helper for FastAPI"""
    global vector_service
    if vector_service is None:
        vector_service = VectorService()
    return vector_service


async def get_vector_service_async() -> VectorService:
    """Async dependency injection helper for FastAPI"""
    return get_vector_service()
