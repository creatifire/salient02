<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Vector Query Tool - Architecture & Configuration

**Status:** Production  
**Last Updated:** 2025-10-30  
**Related:** [Code Organization](./code-organization.md), [Pinecone Connectivity](./pinecone-connectivity.md), [Simple Chat Agent Design](./simple-chat-agent-design.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Multi-Tenancy Model](#multi-tenancy-model)
4. [Data Loading Workflow](#data-loading-workflow)
5. [Query Processing](#query-processing)
6. [Configuration](#configuration)
7. [Adding New Content Sources](#adding-new-content-sources)
8. [Performance Characteristics](#performance-characteristics)
9. [Future Enhancements](#future-enhancements)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The **Vector Query Tool** enables Pydantic AI agents to perform semantic search across knowledge bases stored in Pinecone vector databases. It transforms natural language queries into vector embeddings and retrieves the most relevant content based on semantic similarity.

### Purpose

Agents use vector search to:
- Ground responses in actual organization content (websites, documentation, knowledge bases)
- Provide accurate, up-to-date information about products, services, and policies
- Avoid hallucination by retrieving factual information before responding
- Scale from small businesses to large enterprises with consistent performance

### Key Design Principles

1. **Multi-Tenant Architecture**: Each account gets its own Pinecone index for data isolation
2. **Namespace-Based Access**: Agent instances access specific namespaces within their account's index
3. **Semantic Search**: Uses vector embeddings (not keyword matching) for understanding user intent
4. **Retrieval-Augmented Generation (RAG)**: Combines vector search with LLM generation for accurate, contextual responses
5. **Schema-Free Flexibility**: No predefined schema - works with any content type (websites, docs, PDFs, etc.)

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PYDANTIC AI AGENT                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  vector_search(query, max_results)                    │   │
│  │  - Tool registered via @agent.tool decorator         │   │
│  │  - Accessible to LLM for any semantic search need    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    VECTOR TOOLS LAYER                        │
│  File: backend/app/agents/tools/vector_tools.py             │
│                                                              │
│  • Validates agent has vector search enabled                │
│  • Loads Pinecone configuration from agent config           │
│  • Manages PineconeClient connection pool (cached)          │
│  • Formats results for LLM consumption                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   VECTOR SERVICE LAYER                       │
│  File: backend/app/services/vector_service.py               │
│                                                              │
│  VectorService:                                              │
│  • query_similar(query_text, top_k, threshold, namespace)  │
│  • upsert_document(document, namespace)                    │
│  • upsert_documents_batch(documents, namespace)            │
│  • delete_document(id, namespace)                          │
│  • get_namespace_stats(namespace)                          │
│                                                              │
│  Uses:                                                       │
│  • EmbeddingService - generates query embeddings           │
│  • PineconeClient - manages Pinecone API connections       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   PINECONE INFRASTRUCTURE                    │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │  Account: wyckoff  │  │ Account: agrofresh │            │
│  │  Index: wyckoff-01 │  │ Index: agrofresh-01│            │
│  │                    │  │                    │            │
│  │  Namespaces:       │  │  Namespaces:       │            │
│  │  • __default__     │  │  • website         │            │
│  │  • products        │  │  • products        │            │
│  │  • docs            │  │  • manuals         │            │
│  └────────────────────┘  └────────────────────┘            │
│                                                              │
│  Vector Dimensions: 1536 (text-embedding-3-small)          │
│  Similarity Metric: cosine                                  │
│  Cloud: AWS us-east-1                                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: Query Execution

1. **LLM Tool Call**: Agent decides to use `vector_search(query="What products do you offer?")`
2. **Configuration Load**: Tool loads agent's Pinecone config (index, namespace, API key)
3. **Embedding Generation**: Query text → vector embedding via OpenAI `text-embedding-3-small`
4. **Pinecone Query**: Search index/namespace for top K most similar vectors
5. **Threshold Filtering**: Keep only results above similarity threshold (e.g., 0.7)
6. **Result Formatting**: Format results with text, scores, metadata for LLM
7. **LLM Response**: Agent uses retrieved context to formulate accurate answer

---

## Multi-Tenancy Model

### Isolation Strategy

**Account Level → Pinecone Index**
- Each account (wyckoff, agrofresh, prepexcellence) gets a dedicated Pinecone index
- Complete data isolation - no risk of cross-account data leakage
- Independent scaling and configuration per account

**Agent Instance Level → Namespace**
- Agent instances access specific namespaces within their account's index
- Example: `wyckoff/wyckoff_info_chat1` → `wyckoff-poc-01` index, `__default__` namespace
- Future: Support multiple namespaces per agent for federated search

### Configuration Hierarchy

```yaml
# Agent Config: backend/config/agent_configs/<account>/<instance>/config.yaml

tools:
  vector_search:
    enabled: true
    max_results: 5                    # Number of results to return
    similarity_threshold: 0.7         # Minimum similarity score (0-1)
    pinecone:
      index_name: "wyckoff-poc-01"    # Account-specific index
      namespace: "__default__"         # Agent instance namespace
      api_key_env: "PINECONE_API_KEY_OPENTHOUGHT"  # API key env var
    embedding:
      model: "text-embedding-3-small" # OpenAI embedding model
      dimensions: 1536                # Vector dimensions
```

---

## Data Loading Workflow

Content is loaded into Pinecone vector databases using **Siphon Projects** - a separate suite of ETL (Extract, Transform, Load) tools.

### Siphon Project: `siphon-wp-xml-to-md-vdb`

**Location:** `/Users/arifsufi/Documents/GitHub/OpenThought/siphon/siphon-wp-xml-to-md-vdb`

**Purpose:** Convert WordPress XML exports to vector embeddings in Pinecone

### Pipeline Stages

#### 1. Extract & Convert to Markdown

**Tool:** `shell/convert_xml_to_md.sh`

```bash
# Convert WordPress XML to Markdown files
./shell/convert_xml_to_md.sh --project wyckoff

# Features:
# - Uses wordpress-export-to-markdown Node.js tool
# - Single markdown files per post (no folders)
# - Date prefixes for chronological sorting
# - Rich frontmatter metadata (title, date, categories, tags, excerpt)
# - No image downloads (focuses on text content)
```

**Input:** `projects/wyckoff/source/*.xml` (WordPress XML export)  
**Output:** `projects/wyckoff/markdown/*.md` (Markdown files with frontmatter)

**Sample Output:**
```markdown
---
title: "Welcome to Wyckoff Hospital"
date: 2024-10-15
categories: [Healthcare, Services]
tags: [hospital, emergency, pediatrics]
type: page
slug: welcome
---

Wyckoff Heights Medical Center is a 350-bed community hospital...
```

#### 2. Chunk Markdown Content

**Tool:** `python/markdown_to_pinecone.py`

**Chunking Strategy:**
- Uses LangChain `RecursiveCharacterTextSplitter`
- Semantic chunking (preserves sentence/paragraph boundaries)
- Chunk size: ~500-1000 tokens (configurable)
- Overlap: 100-200 tokens for context continuity
- Token validation for embedding model limits (8191 tokens for `text-embedding-3-small`)

**Chunk Metadata:**
```json
{
  "source_title": "Welcome to Wyckoff Hospital",
  "source_type": "page",
  "source_file": "2024-10-15-welcome.md",
  "original_url": "https://wyckoffhospital.org/welcome",
  "categories": ["Healthcare", "Services"],
  "tags": ["hospital", "emergency", "pediatrics"],
  "chunk_index": 0,
  "chunk_content": "...",
  "token_count": 487
}
```

#### 3. Generate Embeddings

**Model:** OpenAI `text-embedding-3-small`  
**Dimensions:** 1536  
**Batch Size:** 100 chunks per API call

```python
# Batch embedding generation
embeddings = openai.embeddings.create(
    model="text-embedding-3-small",
    input=[chunk1_text, chunk2_text, ...],  # Up to 100 chunks
    dimensions=1536
)
```

**Features:**
- Batch processing for efficiency (reduces API calls)
- Automatic retry logic for transient failures
- Token usage tracking and logging
- Rate limiting compliance

#### 4. Upsert to Pinecone

**Batch Size:** 100 vectors per upsert  
**Namespace:** Configured per project (e.g., `__default__`, `website`, `products`)

```python
# Upsert vector batch
index.upsert(
    vectors=[
        {
            "id": "wyckoff-page-123-chunk-0",
            "values": [0.023, -0.154, ...],  # 1536-dim embedding
            "metadata": {
                "text": "Wyckoff Heights Medical Center is...",
                "source_title": "Welcome to Wyckoff Hospital",
                "source_type": "page",
                "original_url": "https://wyckoffhospital.org/welcome",
                "created_at": "2025-10-30T12:00:00Z",
                "embedding_model": "text-embedding-3-small"
            }
        },
        # ... up to 100 vectors
    ],
    namespace="__default__"
)
```

### Running the Pipeline

```bash
# Step 1: Convert XML to Markdown
cd /Users/arifsufi/Documents/GitHub/OpenThought/siphon/siphon-wp-xml-to-md-vdb
./shell/convert_xml_to_md.sh --project wyckoff

# Step 2: Generate embeddings and load to Pinecone
python python/markdown_to_pinecone.py --project wyckoff

# Optional: Dry-run to preview without uploading
python python/markdown_to_pinecone.py --project wyckoff --dry-run --samples 3
```

---

## Query Processing

### Query Embedding

When an agent calls `vector_search(query="What emergency services do you provide?")`:

1. **Query Text → Embedding**
   ```python
   query_embedding = await embedding_service.embed_text(query_text)
   # Returns: [0.012, -0.089, ..., 0.034]  # 1536 dimensions
   ```

2. **Pinecone Query**
   ```python
   response = index.query(
       vector=query_embedding,
       top_k=5,                          # Return top 5 results
       include_metadata=True,            # Include metadata in results
       namespace="__default__",          # Target namespace
       filter=None                       # Optional metadata filters
   )
   ```

3. **Similarity Scoring**
   - Pinecone returns results with cosine similarity scores (0-1)
   - 1.0 = identical vectors
   - 0.7-0.9 = very similar
   - 0.5-0.7 = somewhat similar
   - < 0.5 = not very similar

4. **Threshold Filtering**
   ```python
   # Only return results above similarity threshold
   results = [
       match for match in response.matches 
       if match.score >= similarity_threshold  # e.g., 0.7
   ]
   ```

### Result Formatting

Results are formatted for LLM consumption:

```
Found 3 relevant result(s) in knowledge base:

1. Wyckoff Heights Medical Center offers 24/7 emergency services including trauma care, pediatric emergency, cardiac care, and stroke treatment. Our Level II Trauma Center is equipped with state-of-the-art facilities...
   Relevance Score: 0.892
   Details: title: Emergency Services, type: page, url: https://wyckoffhospital.org/emergency

2. Our Emergency Department provides rapid assessment and treatment for life-threatening conditions. We have specialized teams for cardiac emergencies, stroke response, and pediatric care...
   Relevance Score: 0.847
   Details: title: Emergency Department Overview, type: page

3. Emergency care includes advanced diagnostic imaging, laboratory services, and direct admission to specialized units when needed. Average wait time is monitored to ensure timely care...
   Relevance Score: 0.781
   Details: title: Emergency Care Services, type: page
```

### Configuration Cascade

Query parameters follow a cascade (LLM → Agent → Global):

```python
# 1. LLM Parameter (highest priority)
vector_search(query="...", max_results=10)

# 2. Agent Config
tools:
  vector_search:
    max_results: 5
    similarity_threshold: 0.7

# 3. Global Config (backend/config/app.yaml)
vector:
  search:
    max_results: 5
    similarity_threshold: 0.7

# 4. Code Default (lowest priority)
top_k = max_results or agent_config_value or global_config_value or 5
```

---

## Configuration

### Agent-Level Configuration

**File:** `backend/config/agent_configs/<account>/<instance>/config.yaml`

```yaml
tools:
  vector_search:
    enabled: true                     # Enable/disable vector search for this agent
    max_results: 5                    # Number of results to return (default: 5)
    similarity_threshold: 0.7         # Minimum similarity score 0-1 (default: 0.7)
    
    pinecone:
      index_name: "wyckoff-poc-01"    # REQUIRED: Pinecone index name
      namespace: "__default__"         # REQUIRED: Namespace within index
      api_key_env: "PINECONE_API_KEY_OPENTHOUGHT"  # Environment variable for API key
      # index_host: "https://..."     # OPTIONAL: Explicit index host (auto-discovered if omitted)
    
    embedding:
      model: "text-embedding-3-small" # OpenAI embedding model
      dimensions: 1536                # Vector dimensions (must match index)
```

### Global Configuration

**File:** `backend/config/app.yaml`

```yaml
vector:
  search:
    max_results: 5                    # Default max results
    similarity_threshold: 0.7         # Default similarity threshold
```

### Environment Variables

**File:** `.env`

```bash
# Pinecone API Key (per project/organization)
PINECONE_API_KEY_OPENTHOUGHT="pc-..."

# OpenAI API Key (for embeddings)
OPENAI_API_KEY="sk-..."
```

### Current Implementations

| Account | Agent Instance | Index Name | Namespace | Content Type |
|---------|---------------|------------|-----------|--------------|
| wyckoff | wyckoff_info_chat1 | wyckoff-poc-01 | __default__ | Hospital website (WordPress) |
| agrofresh | agro_info_chat1 | agrofresh-01 | website | Company website content |
| prepexcellence | prepexcel_info_chat1 | prepexcellence-01 | website | Test prep website content |

---

## Adding New Content Sources

### Prerequisites

1. **Pinecone Index**: Create index for the account (if doesn't exist)
2. **Namespace**: Choose namespace within index (e.g., `website`, `products`, `docs`)
3. **Content**: Prepare content source (WordPress XML, PDF docs, website HTML, etc.)
4. **Siphon Project**: Use existing siphon or create new one for your content type

### Step-by-Step Process

#### 1. Create Pinecone Index (One-Time per Account)

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="...")
pc.create_index(
    name="newaccount-01",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)
```

#### 2. Set Up Siphon Project

**For WordPress content:**

```bash
# Navigate to siphon project
cd /Users/arifsufi/Documents/GitHub/OpenThought/siphon/siphon-wp-xml-to-md-vdb

# Create project directory
cp -r projects/template projects/newaccount

# Edit configuration
nano projects/newaccount/config.yaml
```

**Sample config:**
```yaml
# projects/newaccount/config.yaml
project:
  name: "newaccount"
  description: "New Account website content"

pinecone:
  index: "newaccount-01"
  namespace: "website"
  metric: "cosine"
  cloud: "aws"
  region: "us-east-1"

embedding:
  model: "text-embedding-3-small"
  dimensions: 1536
  batch_size: 100

chunking:
  enabled: true
  chunk_size: 1000      # Target tokens per chunk
  chunk_overlap: 200    # Overlap tokens for context
  min_chunk_size: 100   # Minimum chunk size
```

#### 3. Run Data Pipeline

```bash
# Step 1: Convert source content to markdown
./shell/convert_xml_to_md.sh --project newaccount

# Step 2: Generate embeddings and load to Pinecone
python python/markdown_to_pinecone.py --project newaccount

# Verify results
python python/markdown_to_pinecone.py --project newaccount --dry-run --samples 3
```

#### 4. Configure Agent

**File:** `backend/config/agent_configs/newaccount/instance1/config.yaml`

```yaml
tools:
  vector_search:
    enabled: true
    max_results: 5
    similarity_threshold: 0.7
    pinecone:
      index_name: "newaccount-01"
      namespace: "website"
      api_key_env: "PINECONE_API_KEY_OPENTHOUGHT"
    embedding:
      model: "text-embedding-3-small"
      dimensions: 1536
```

#### 5. Update Agent System Prompt

**File:** `backend/config/agent_configs/newaccount/instance1/system_prompt.md`

```markdown
## Your Search Tool: Vector Search

You have access to a **vector search tool** that searches the organization's knowledge base:
- Website content and product information
- Service descriptions and policies
- Contact information and FAQs

**CRITICAL: ALWAYS USE vector_search TOOL FIRST**

Examples:
- "What products do you offer?" → CALL vector_search("products offerings")
- "What are your hours?" → CALL vector_search("business hours contact information")
- "Tell me about your services" → CALL vector_search("services capabilities")
```

#### 6. Test the Agent

```bash
# Start the backend server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Test via API or web interface
curl -X POST "http://localhost:8000/accounts/newaccount/agents/instance1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What products do you offer?"}'
```

---

## Performance Characteristics

### Query Latency

**Typical Query Times:**
- **Embedding Generation:** 100-300ms (OpenAI API call)
- **Pinecone Query:** 50-150ms (vector similarity search)
- **Total Vector Search:** 150-450ms

**Example from Logfire:**
```
22:56:14.685 chat openai/gpt-5-mini (3.1s)
22:56:14.686   pinecone.query (1.2s)
22:56:14.686     pinecone.embedding (0.7s)
22:56:14.686     pinecone.search (0.5s)
```

### Embedding Costs

**OpenAI `text-embedding-3-small`:**
- Cost: $0.02 per 1M tokens
- Query: ~100-300 tokens → $0.000002-$0.000006 per query
- Batch 1000 chunks: ~500k tokens → $0.01

### Pinecone Costs

**Serverless Plan:**
- Storage: $0.25 per 1M vectors per month
- Reads: $0.0018 per 1000 operations
- Writes: $0.045 per 1000 operations

**Example:** 10k vectors, 10k queries/month
- Storage: 10k × $0.25 / 1M = $0.0025/month
- Reads: 10k × $0.0018 / 1k = $0.018/month
- **Total:** ~$0.02/month + query time compute

### Scalability

**Single Index Limits:**
- **Vectors:** 100M+ vectors per index (Pinecone serverless)
- **Namespaces:** Unlimited namespaces per index
- **Queries:** 100+ QPS (queries per second) per index

**Multi-Index Strategy:**
- Each account gets dedicated index
- Scales horizontally with account growth
- No cross-account performance impact

---

## Future Enhancements

### Roadmap: Planned Features

#### 1. **Multiple Namespace Support** (Priority: High)

**Current:** Agent instance → 1 namespace  
**Future:** Agent instance → N namespaces (federated search)

```yaml
tools:
  vector_search:
    enabled: true
    pinecone:
      index_name: "wyckoff-poc-01"
      namespaces:                    # Multiple namespaces
        - "website"
        - "products"
        - "documentation"
      search_strategy: "parallel"    # Search all in parallel, merge results
```

**Benefits:**
- Search across multiple content types simultaneously
- Organize content by source (website, docs, products)
- Better relevance through content-type filtering

#### 2. **Metadata Filtering** (Priority: High)

**Current:** No metadata filtering  
**Future:** Rich metadata filtering for precision

```yaml
tools:
  vector_search:
    filters:
      enabled: true
      default_filters:               # Applied to all queries
        source_type: ["page", "post"]
        published: true
```

**Agent Tool Call:**
```python
vector_search(
    query="emergency services",
    metadata_filter={
        "source_type": "page",
        "categories": {"$in": ["Healthcare", "Emergency"]},
        "updated_at": {"$gte": "2024-01-01"}
    }
)
```

**Benefits:**
- Filter by content type, date, category, author
- Exclude outdated content
- Target specific content sections

#### 3. **Hybrid Search** (Priority: Medium)

**Current:** Pure vector search (semantic only)  
**Future:** Hybrid semantic + keyword search

```python
# Combine vector similarity with BM25 keyword scoring
response = hybrid_search(
    query="emergency room wait times",
    alpha=0.7,  # 70% vector, 30% keyword
    top_k=10
)
```

**Benefits:**
- Better recall for exact-match queries (phone numbers, names, codes)
- Semantic understanding + keyword precision
- Configurable weighting per agent

#### 4. **Reranking** (Priority: Medium)

**Current:** Rank by cosine similarity only  
**Future:** Two-stage retrieval + reranking

```python
# Stage 1: Retrieve top 20 candidates (fast, broad recall)
candidates = vector_search(query, top_k=20, threshold=0.6)

# Stage 2: Rerank with cross-encoder (slow, high precision)
reranked = reranker.rerank(query, candidates, top_k=5)
```

**Reranking Models:**
- Cohere Rerank API
- Cross-encoder models (e.g., `ms-marco-MiniLM`)
- Custom fine-tuned rerankers

**Benefits:**
- Higher precision for top results
- Better relevance for ambiguous queries
- Improved user satisfaction

#### 5. **Query Expansion** (Priority: Low)

**Current:** Search with user query as-is  
**Future:** Expand query with synonyms, related terms

```python
# Original query
"thyroid doctor"

# Expanded queries (parallel search + merge)
queries = [
    "thyroid doctor",
    "endocrinologist",
    "endocrine specialist",
    "hormone specialist"
]
```

**Methods:**
- LLM-based query expansion
- Medical/domain-specific ontologies
- User feedback loop

#### 6. **Caching** (Priority: Low)

**Current:** No caching  
**Future:** Cache frequently asked queries

```python
# Cache query embeddings + results for N minutes
cache_key = hash(query_text)
if cache_key in cache and not cache_expired:
    return cache[cache_key]
```

**Benefits:**
- Reduce OpenAI API costs
- Lower Pinecone query costs
- Faster response times

### Research Ideas: Long-Term

#### 1. **Multi-Modal Search**

**Vision:** Search across text, images, audio, video

```python
vector_search(
    query="Show me the hospital lobby",
    modalities=["text", "image"],  # Search text + image embeddings
    top_k=5
)
```

**Use Cases:**
- Product catalogs with images
- Video tutorials + transcripts
- Medical imaging + reports

**Models:**
- CLIP (text + image embeddings in same space)
- Whisper + embeddings (audio → text → embeddings)

#### 2. **Self-Learning Systems**

**Vision:** Automatically improve search from user interactions

```python
# Track query → result → user feedback
feedback = {
    "query": "emergency services",
    "result_id": "wyckoff-page-123",
    "clicked": True,
    "helpful": True,
    "timestamp": "2025-10-30T12:00:00Z"
}

# Periodically retrain/fine-tune embeddings
embedding_model = fine_tune(
    base_model="text-embedding-3-small",
    feedback_data=feedback_history
)
```

**Benefits:**
- Continuous improvement without manual tuning
- Domain-specific optimization
- Personalization per account

#### 3. **Real-Time Indexing**

**Current:** Batch indexing via siphon (manual trigger)  
**Future:** Real-time indexing as content changes

```python
# Webhook from WordPress → index immediately
@app.post("/webhooks/content-update")
async def handle_content_update(payload):
    # Extract new/updated content
    content = extract_content(payload)
    
    # Generate embedding
    embedding = await embedding_service.embed_text(content.text)
    
    # Upsert to Pinecone immediately
    await vector_service.upsert_document(
        VectorDocument(
            id=content.id,
            text=content.text,
            embedding=embedding,
            metadata=content.metadata,
            namespace="website"
        )
    )
```

**Benefits:**
- Always up-to-date content
- No manual pipeline re-runs
- Immediate content availability

#### 4. **Privacy-Preserving Search**

**Vision:** Search without exposing sensitive data

**Techniques:**
- **Federated Learning:** Train on distributed data without centralization
- **Differential Privacy:** Add noise to embeddings to protect individual records
- **Homomorphic Encryption:** Search encrypted vectors

**Use Cases:**
- HIPAA compliance (medical records)
- Financial data (PCI-DSS)
- Legal documents (attorney-client privilege)

#### 5. **AI-Optimized Indexing**

**Vision:** Use AI to optimize index structure for faster search

**Current:** Flat index (brute-force similarity search)

**Future:**
- **HNSW (Hierarchical Navigable Small World)**: Graph-based approximate nearest neighbor
- **Product Quantization**: Compress vectors for faster search
- **Learned Indexes**: Train neural networks to predict vector locations

**Benefits:**
- Lower query latency (10x faster)
- Reduced memory usage (4x compression)
- Scale to 1B+ vectors per index

---

## Troubleshooting

### Common Issues

#### 1. "Vector search is not enabled for this agent"

**Cause:** Agent config has `vector_search.enabled: false` or missing

**Fix:**
```yaml
# backend/config/agent_configs/<account>/<instance>/config.yaml
tools:
  vector_search:
    enabled: true  # Set to true
```

#### 2. "Vector search configuration error"

**Cause:** Missing Pinecone config (index, namespace, API key)

**Fix:** Ensure all required fields are present:
```yaml
tools:
  vector_search:
    pinecone:
      index_name: "wyckoff-poc-01"    # REQUIRED
      namespace: "__default__"         # REQUIRED
      api_key_env: "PINECONE_API_KEY_OPENTHOUGHT"  # REQUIRED
```

**Verify API key in `.env`:**
```bash
echo $PINECONE_API_KEY_OPENTHOUGHT
# Should output: pc-...
```

#### 3. "No relevant information found in knowledge base"

**Causes:**
1. Query too specific / no matching content
2. Similarity threshold too high
3. Wrong namespace
4. Index is empty

**Debugging:**

**Check namespace stats:**
```python
stats = await vector_service.get_namespace_stats(namespace="__default__")
print(stats)
# Output: {"namespace": "__default__", "namespace_vector_count": 1234}
```

**Lower threshold temporarily:**
```yaml
tools:
  vector_search:
    similarity_threshold: 0.4  # Lower from 0.7 to 0.4
```

**Check Logfire logs:**
```
22:56:14.686 pinecone.query
  query_text: "emergency services"
  top_k: 5
  similarity_threshold: 0.7
  namespace: "__default__"
  results_count: 0         # No results above threshold!
  filtered_count: 3        # 3 results were filtered out
```

#### 4. "Vector search encountered an error"

**Causes:**
1. Pinecone API error (network, auth, quota)
2. OpenAI embedding API error
3. Index/namespace doesn't exist

**Check Logfire:**
```
22:56:14.686 pinecone.query
  error: "Index 'wyckoff-poc-01' not found"
  error_type: "NotFoundException"
```

**Fix:** Verify index exists:
```python
from pinecone import Pinecone
pc = Pinecone(api_key="...")
print(pc.list_indexes())
```

#### 5. Slow Query Performance (>2s)

**Causes:**
1. Large `top_k` (>50)
2. Complex metadata filters
3. High Pinecone load

**Optimizations:**
- Reduce `top_k` to 5-10
- Use simpler metadata filters
- Cache frequent queries
- Upgrade Pinecone plan (if serverless)

**Benchmark queries:**
```python
import time
start = time.time()
response = await vector_service.query_similar(query, top_k=5)
print(f"Query time: {(time.time() - start) * 1000:.2f}ms")
```

---

## Related Documentation

- **[Pinecone Connectivity](./pinecone-connectivity.md)** - Pinecone client setup and connection pooling
- **[Simple Chat Agent Design](./simple-chat-agent-design.md)** - Agent architecture and tool registration
- **[Code Organization](./code-organization.md)** - Project structure and module organization
- **[LLM Tool Calling Performance](./llm-tool-calling-performance.md)** - Tool execution benchmarks

---

## References

### External Links

- **Pinecone Documentation**: https://docs.pinecone.io/
- **OpenAI Embeddings Guide**: https://platform.openai.com/docs/guides/embeddings
- **LangChain Text Splitters**: https://python.langchain.com/docs/modules/data_connection/document_transformers/
- **Vector Search Trends 2025**: https://nextbrick.com/future-trends-in-vector-search-whats-next/
- **Hybrid Search Guide**: https://www.pinecone.io/learn/hybrid-search/

### Internal Projects

- **Siphon Project:** `/Users/arifsufi/Documents/GitHub/OpenThought/siphon/`
  - `siphon-wp-xml-to-md-vdb/` - WordPress to Pinecone pipeline

### Code References

- **Vector Tools:** `backend/app/agents/tools/vector_tools.py`
- **Vector Service:** `backend/app/services/vector_service.py`
- **Embedding Service:** `backend/app/services/embedding_service.py`
- **Pinecone Client:** `backend/app/services/pinecone_client.py`
- **Agent Pinecone Config:** `backend/app/services/agent_pinecone_config.py`

---

**Document Version:** 1.0  
**Last Reviewed:** 2025-10-30  
**Next Review:** 2025-12-01

