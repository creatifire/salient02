# Epic 0011 - Vector Database Integration

> Goal: Implement comprehensive vector database integration for RAG-powered chat responses, including semantic search, content retrieval, and intelligent response generation using ingested website content.

**Milestone 1**: Pinecone integration for premium vector storage  
**Milestone 2**: PostgreSQL pgvector extension for cost-effective entry-tier storage

## Scope & Approach

### Vector Database Capabilities
- **Pinecone Integration** (Milestone 1): Full API integration with Pinecone vector database
- **PostgreSQL pgvector** (Milestone 2): Cost-effective vector storage using PostgreSQL extension
- **Semantic Search**: High-quality similarity search for relevant content retrieval
- **RAG Pipeline**: Complete retrieval-augmented generation workflow
- **Chat Integration**: Seamless integration with existing chat endpoints
- **Performance Optimization**: Efficient querying and response generation
- **Hybrid Architecture**: Support for multiple vector storage backends

### Target Use Cases
- **Product Inquiries**: Accurate responses using website product information
- **Technical Support**: Context-aware answers from documentation and guides
- **Sales Conversations**: Informed responses using company and product content
- **FAQ Handling**: Automatic responses using ingested FAQ content
- **Content Discovery**: Help users find relevant information through natural language

## Features & Requirements

### ✅ 0011-001 - FEATURE - Pinecone Setup & Configuration [COMPLETED]

#### ✅ 0011-001-001 - TASK - Pinecone Infrastructure Setup [COMPLETED]
- ✅ 0011-001-001-01 - CHUNK - Pinecone account and index configuration [COMPLETED]
  - **CONFIRMED CONFIGURATION**:
    - **Project**: openthought-dev
    - **Index**: salient-dev-01 
    - **Host**: https://salient-dev-01-e1nildl.svc.aped-4627-b74a.pinecone.io
    - **Dimensions**: 1536 (text-embedding-3-small)
    - **Metric**: cosine
    - **Namespace**: development (dev), test (testing), account-{id} (production)
  - SUB-TASKS:
    - ✅ Pinecone account and API key setup (COMPLETED)
    - ✅ Development index creation (COMPLETED) 
    - ✅ Configuration in agent_configs/simple_chat.yaml (COMPLETED)
    - ✅ Environment-based configuration management (COMPLETED)
    - ✅ Namespace strategy implementation (COMPLETED)
    - ✅ Index monitoring and health checks (COMPLETED)
    - ✅ Acceptance: Pinecone indexes ready for content ingestion and querying (VERIFIED)

#### 0011-001-001-01 - AUTOMATED-TESTS - Pinecone Index Configuration
**Unit Tests** (`backend/tests/unit/test_pinecone_infrastructure.py`):
- **API Key Validation**: Test API key loading from environment and configuration validation
- **Index Configuration Validation**: Verify application validates existing index dimensions (1536) and cosine similarity
- **Environment Setup**: Test dev/staging/prod index configuration switching
- **Namespace Strategy**: Validate namespace selection and organization logic

**Integration Tests** (`backend/tests/integration/test_pinecone_connection.py`):
- **Index Connection**: Test connection to pre-existing index in test environment
- **Index Configuration Match**: Verify existing index matches application expectations
- **Health Check Integration**: Verify index monitoring and health check functionality

- ✅ 0011-001-001-02 - CHUNK - Connection and authentication management [COMPLETED]
  - SUB-TASKS:
    - ✅ Secure API key storage and environment configuration (COMPLETED)
    - ✅ Connection pooling and retry logic with exponential backoff (COMPLETED)
    - ✅ Environment-based configuration (dev/staging/prod) (COMPLETED)
    - ✅ Connection health monitoring and alerting (COMPLETED)
    - ✅ Rate limiting and quota management (COMPLETED)
    - ✅ Acceptance: Reliable, secure connection to Pinecone with proper monitoring (VERIFIED)

#### 0011-001-001-02 - AUTOMATED-TESTS - Connection & Authentication Management
**Unit Tests** (`backend/tests/unit/test_pinecone_connection.py`):
- **Secure API Key Storage**: Test API key encryption, rotation, and secure retrieval
- **Connection Pooling**: Verify connection pool creation, reuse, and cleanup
- **Environment Configuration**: Test configuration switching between dev/staging/prod environments
- **Rate Limiting Logic**: Validate rate limiting and backoff strategy implementation
- **Error Handling**: Test connection failure scenarios and retry mechanisms

**Integration Tests** (`backend/tests/integration/test_pinecone_connection.py`):
- **Live Connection**: Test actual connection to Pinecone test environment
- **Health Monitoring**: Verify connection health checks and alerting functionality
- **Performance Testing**: Test connection pool performance under load

#### [ ] 0011-001-002 - TASK - Vector Database Service Layer
- ✅ 0011-001-002-01 - CHUNK - Pinecone service implementation [COMPLETED]
  - SUB-TASKS:
    - ✅ Created `backend/app/services/vector_service.py` (COMPLETED)
    - ✅ Implemented query, upsert, delete, and fetch operations (COMPLETED)
    - ✅ Added namespace management and content categorization (COMPLETED)
    - ✅ Created batch operations for efficient bulk processing (COMPLETED)
    - ✅ Added comprehensive error handling and logging (COMPLETED)
    - ✅ Acceptance: Complete Pinecone API wrapper with all essential operations (VERIFIED)

#### 0011-001-002-01 - AUTOMATED-TESTS - Vector Service Implementation
**Unit Tests** (`backend/tests/unit/test_vector_service.py`):
- **Service Initialization**: Test VectorService instantiation with proper configuration
- **CRUD Operations**: Verify query, upsert, delete, and fetch method signatures and validation
- **Namespace Management**: Test namespace creation, switching, and isolation logic
- **Batch Operations**: Validate batch processing logic for bulk operations
- **Error Handling**: Test error scenarios, logging, and exception handling
- **Input Validation**: Verify proper validation of vectors, metadata, and parameters

**Integration Tests** (`backend/tests/integration/test_vector_service.py`):
- **End-to-End Operations**: Test complete CRUD workflows with real Pinecone test index
- **Performance Validation**: Verify query response times meet requirements (<500ms)
- **Batch Processing**: Test bulk operations with large datasets
- **Namespace Isolation**: Ensure namespace separation works correctly with real data

### [ ] 0011-002 - FEATURE - Embedding Generation & Management

#### [ ] 0011-002-001 - TASK - Embedding Service Integration
- [ ] 0011-002-001-01 - CHUNK - OpenAI embedding integration
  - SUB-TASKS:
    - Integrate with OpenAI text-embedding-3-small API
    - Implement batch embedding generation for efficiency
    - Add embedding caching to avoid duplicate API calls
    - Create embedding quality validation and error handling
    - Add cost tracking for embedding generation
    - Acceptance: Reliable, cost-effective embedding generation service

- [ ] 0011-002-001-02 - CHUNK - Embedding optimization and caching
  - SUB-TASKS:
    - Implement embedding cache using Redis or database
    - Add embedding versioning for model updates
    - Create embedding quality metrics and monitoring
    - Implement embedding refresh strategies for updated content
    - Add embedding deduplication and consistency checks
    - Acceptance: Optimized embedding pipeline with intelligent caching

#### [ ] 0011-002-002 - TASK - Query Processing & Enhancement
- [ ] 0011-002-002-01 - CHUNK - Query preprocessing and optimization
  - SUB-TASKS:
    - Implement query cleaning and normalization
    - Add query expansion and enhancement techniques
    - Create query intent detection and categorization
    - Implement query rewriting for better search results
    - Add query history and analytics for optimization
    - Acceptance: Enhanced query processing for improved search relevance

### [ ] 0011-003 - FEATURE - Semantic Search & Retrieval

#### [ ] 0011-003-001 - TASK - Search Implementation
- [ ] 0011-003-001-01 - CHUNK - Similarity search with filtering
  - SUB-TASKS:
    - Implement semantic similarity search with configurable thresholds
    - Add metadata filtering for content type and category
    - Create multi-stage search with re-ranking
    - Implement search result scoring and relevance calculation
    - Add search result diversity and deduplication
    - Acceptance: High-quality search results with proper relevance scoring

- [ ] 0011-003-001-02 - CHUNK - Context-aware retrieval
  - SUB-TASKS:
    - Implement conversation context integration for search
    - Add user profile and session-based personalization
    - Create adaptive search based on conversation history
    - Implement temporal relevance for time-sensitive content
    - Add domain-specific search optimization
    - Acceptance: Context-aware search that improves with conversation depth

#### [ ] 0011-003-002 - TASK - Search Result Processing
- [ ] 0011-003-002-01 - CHUNK - Result ranking and selection
  - SUB-TASKS:
    - Implement advanced ranking algorithms beyond similarity
    - Add business logic for content prioritization
    - Create result clustering and grouping
    - Implement result explanation and citation tracking
    - Add A/B testing framework for ranking optimization
    - Acceptance: Intelligently ranked search results with clear attribution

### [ ] 0011-004 - FEATURE - RAG Pipeline Integration

#### [ ] 0011-004-001 - TASK - Chat Endpoint Enhancement
- [ ] 0011-004-001-01 - CHUNK - RAG integration in streaming endpoint
  - SUB-TASKS:
    - Enhance `GET /events/stream` to include vector search
    - Add retrieval step before LLM generation
    - Implement context injection into LLM prompts
    - Add citation tracking and source attribution
    - Maintain streaming performance with RAG overhead
    - Acceptance: Streaming chat with RAG-enhanced responses

- [ ] 0011-004-001-02 - CHUNK - RAG integration in POST endpoint
  - SUB-TASKS:
    - Enhance `POST /chat` to include vector search
    - Add retrieval step before LLM generation
    - Implement context injection into LLM prompts
    - Add citation tracking and source attribution
    - Ensure response format consistency
    - Acceptance: POST chat endpoint with RAG-enhanced responses

#### [ ] 0011-004-002 - TASK - Response Generation Enhancement
- [ ] 0011-004-002-01 - CHUNK - Context injection and prompt engineering
  - SUB-TASKS:
    - Design prompts for effective RAG context utilization
    - Implement dynamic context length management
    - Add source citation generation and formatting
    - Create response quality validation
    - Add fallback strategies for low-quality retrievals
    - Acceptance: High-quality RAG responses with proper citations

### [ ] 0011-005 - FEATURE - Performance & Monitoring

#### [ ] 0011-005-001 - TASK - Performance Optimization
- [ ] 0011-005-001-01 - CHUNK - Search performance optimization
  - SUB-TASKS:
    - Implement query result caching strategies
    - Add search latency monitoring and optimization
    - Create parallel processing for multiple retrievals
    - Implement search result precomputation for common queries
    - Add performance benchmarking and testing
    - Acceptance: Sub-second search performance for most queries

- [ ] 0011-005-001-02 - CHUNK - Monitoring and analytics
  - SUB-TASKS:
    - Add comprehensive search analytics and metrics
    - Implement search quality monitoring
    - Create RAG performance dashboards
    - Add user satisfaction tracking for RAG responses
    - Implement A/B testing for search improvements
    - Acceptance: Complete visibility into RAG performance and quality

## Technical Architecture

### RAG Pipeline Flow
```
User Query → Query Processing → Vector Search → Context Retrieval → LLM Generation → Response with Citations
                                      ↓
                               Pinecone Index ← Content Ingestion (Epic 0010)
```

### Database Schema Extensions
```sql
-- Vector search queries and results tracking
vector_queries:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  conversation_id (GUID, FK → conversations.id)
  query_text (TEXT)
  processed_query (TEXT)
  search_results_count (INTEGER)
  top_similarity_score (DECIMAL)
  latency_ms (INTEGER)
  created_at (TIMESTAMP)

-- Retrieved content tracking
retrieved_content:
  id (GUID, PK)
  query_id (GUID, FK → vector_queries.id)
  content_id (VARCHAR) -- Pinecone vector ID
  similarity_score (DECIMAL)
  rank_position (INTEGER)
  used_in_response (BOOLEAN)
  metadata (JSONB)

-- RAG response tracking
rag_responses:
  id (GUID, PK)
  query_id (GUID, FK → vector_queries.id)
  message_id (GUID, FK → messages.id)
  context_length (INTEGER)
  sources_count (INTEGER)
  response_quality_score (DECIMAL)
  user_feedback (VARCHAR) -- helpful, not_helpful, partially_helpful
  created_at (TIMESTAMP)
```

### Configuration Schema (app.yaml)
```yaml
vector_database:
  pinecone:
    environment: "us-west1-gcp"
    index_name: "salient-content"
    dimension: 1536
    metric: "cosine"
    namespace: "sales_content"
  
  search:
    similarity_threshold: 0.7
    max_results: 5
    enable_reranking: true
    context_window_tokens: 8000
    
  rag:
    enabled: true
    fallback_to_normal_chat: true
    citation_format: "markdown"  # markdown, numbered, none
    max_context_length: 4000
    quality_threshold: 0.6
    
  embedding:
    provider: "openai"
    model: "text-embedding-3-small"
    batch_size: 100
    cache_embeddings: true
    
  performance:
    query_cache_ttl: 300  # seconds
    max_concurrent_searches: 10
    search_timeout_ms: 5000
```

### Integration Points
- **Epic 0010**: Content ingestion provides indexed content
- **Chat Endpoints**: Both streaming and POST endpoints enhanced
- **OpenAI API**: Embedding generation and LLM responses
- **Pinecone**: Vector storage and similarity search
- **Redis**: Query and embedding caching

### Dependencies
- **0010**: Website Content Ingestion (provides content to search)
- **0004-004-002**: Chat endpoint persistence (foundation for RAG enhancement)
- **OpenAI API**: Embedding and chat completion services
- **Pinecone Account**: Vector database service

### Performance Considerations
- **Search Latency**: Target sub-second search performance
- **Caching Strategy**: Multi-layer caching for queries and embeddings
- **Concurrent Searches**: Handle multiple simultaneous requests
- **Token Management**: Efficient context window utilization
- **Cost Optimization**: Balance search quality with embedding costs

## Success Criteria
1. **Search Quality**: 90%+ relevant results for product and service queries
2. **Response Enhancement**: RAG responses demonstrably more accurate than baseline
3. **Performance**: Sub-second search latency for 95% of queries
4. **Citation Accuracy**: All RAG responses include proper source attribution
5. **Integration Success**: Seamless integration with existing chat endpoints
6. **User Satisfaction**: Positive user feedback on response quality and helpfulness
7. **Cost Efficiency**: RAG enhancement maintains reasonable operational costs

---

## Milestone 2: PostgreSQL pgvector Integration

### [ ] 0011-006 - FEATURE - PostgreSQL pgvector Implementation
> Cost-effective vector storage using PostgreSQL pgvector extension for entry-tier accounts

#### [ ] 0011-006-001 - TASK - pgvector Setup & Configuration
- [ ] 0011-006-001-01 - CHUNK - PostgreSQL pgvector extension installation
  - SUB-TASKS:
    - Install and configure pgvector extension in PostgreSQL
    - Create vector tables and indexes for content storage
    - Set up vector similarity functions and operators
    - Configure optimal index parameters for performance
    - Add pgvector monitoring and health checks
    - Acceptance: pgvector extension ready for vector storage and queries

- [ ] 0011-006-001-02 - CHUNK - Hybrid vector storage architecture
  - SUB-TASKS:
    - Implement vector storage routing based on account tier
    - Create abstraction layer for Pinecone + pgvector backends
    - Add vector storage migration capabilities between backends
    - Implement cost-based storage tier recommendations
    - Add vector storage usage analytics and optimization
    - Acceptance: Seamless routing between Pinecone and pgvector based on account tier

#### [ ] 0011-006-002 - TASK - pgvector Performance Optimization
- [ ] 0011-006-002-01 - CHUNK - PostgreSQL vector query optimization
  - SUB-TASKS:
    - Optimize pgvector similarity search queries
    - Implement efficient indexing strategies (IVFFlat, HNSW)
    - Add query result caching for pgvector searches
    - Create batch processing for vector operations
    - Add performance monitoring and benchmarking
    - Acceptance: pgvector performance meets entry-tier requirements

### Configuration Schema Extensions
```yaml
vector_database:
  # Account-tier based storage routing
  storage_tiers:
    entry:
      provider: "pgvector"
      connection: "postgresql://..."
      index_type: "ivfflat"  # or hnsw
      max_vectors: 100000
    
    standard:
      provider: "pinecone"
      environment: "us-west1-gcp"
      namespace_based: true
      
    premium:
      provider: "pinecone"
      environment: "us-west1-gcp"
      dedicated_index: true

  # Automatic tier recommendations
  tier_optimization:
    enabled: true
    usage_threshold_upgrade: 50000  # vectors
    performance_threshold_upgrade: 2000  # ms average query time
    cost_optimization: true
```

This epic creates the intelligent content retrieval foundation that transforms the chat system from a general LLM to a knowledgeable domain expert using the company's own content, with flexible storage options for different account tiers.
