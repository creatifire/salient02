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

##### Configuration

```yaml
# Agent config
tools:
  vector_search:
    filters:
      enabled: true
      default_filters:               # Applied to all queries
        source_type: ["page", "post"]
        published: true
      allowed_filter_fields:         # Fields LLM can filter on
        - source_type
        - categories
        - tags
        - updated_at
        - author
        - language
```

##### Implementation Plan

**Phase 1: Tool Parameter Support**

Add `metadata_filter` parameter to `vector_search` tool:

```python
# backend/app/agents/tools/vector_tools.py

async def vector_search(
    ctx: RunContext[SessionDependencies],
    query: str,
    max_results: Optional[int] = None,
    metadata_filter: Optional[Dict[str, Any]] = None  # NEW
) -> str:
    """
    Search with optional metadata filtering.
    
    Args:
        metadata_filter: Pinecone-compatible filter dict
            Examples:
                {"source_type": "page"}
                {"categories": {"$in": ["Healthcare", "Emergency"]}}
                {"updated_at": {"$gte": "2024-01-01"}}
                {"$and": [
                    {"source_type": "page"},
                    {"published": True},
                    {"updated_at": {"$gte": "2024-01-01"}}
                ]}
    """
    # Merge with default filters from config
    vector_config = ctx.deps.agent_config.get("tools", {}).get("vector_search", {})
    default_filters = vector_config.get("filters", {}).get("default_filters", {})
    
    # Combine: default AND user-provided
    combined_filter = {}
    if default_filters and metadata_filter:
        combined_filter = {
            "$and": [default_filters, metadata_filter]
        }
    else:
        combined_filter = metadata_filter or default_filters or None
    
    # Pass to vector service
    response = await vector_service.query_similar(
        query_text=query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        namespace=pinecone_config.namespace,
        metadata_filter=combined_filter  # NEW
    )
```

**Phase 2: System Prompt Guidance**

Update agent system prompts to teach LLMs when/how to use filters:

```markdown
## Metadata Filtering

You can filter search results by metadata:

**Available Filters:**
- `source_type`: Content type (page, post, product, doc)
- `categories`: Content categories (list)
- `tags`: Content tags (list)
- `updated_at`: Last update date (ISO8601)
- `language`: Content language (en, es, fr)

**Examples:**
- Recent pages only: `metadata_filter={"source_type": "page", "updated_at": {"$gte": "2024-01-01"}}`
- Emergency category: `metadata_filter={"categories": {"$in": ["Emergency", "Healthcare"]}}`
- Spanish content: `metadata_filter={"language": "es"}`

**When to use filters:**
- User asks for recent content: filter by `updated_at`
- User specifies category: filter by `categories`
- User wants specific content type: filter by `source_type`
```

**Phase 3: Validation & Security**

```python
# Validate filter fields against allowed list
allowed_fields = vector_config.get("filters", {}).get("allowed_filter_fields", [])

if metadata_filter:
    for field in extract_filter_fields(metadata_filter):
        if field not in allowed_fields:
            return f"Metadata filtering on '{field}' is not allowed. Available: {allowed_fields}"
```

##### Pinecone Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equals | `{"source_type": {"$eq": "page"}}` |
| `$ne` | Not equals | `{"source_type": {"$ne": "draft"}}` |
| `$in` | In list | `{"categories": {"$in": ["Emergency", "Healthcare"]}}` |
| `$nin` | Not in list | `{"tags": {"$nin": ["archived", "deleted"]}}` |
| `$gt` | Greater than | `{"updated_at": {"$gt": "2024-01-01"}}` |
| `$gte` | Greater or equal | `{"priority": {"$gte": 5}}` |
| `$lt` | Less than | `{"word_count": {"$lt": 1000}}` |
| `$lte` | Less or equal | `{"read_time": {"$lte": 5}}` |
| `$and` | Logical AND | `{"$and": [{"published": True}, {"source_type": "page"}]}` |
| `$or` | Logical OR | `{"$or": [{"language": "en"}, {"language": "es"}]}` |

##### Use Cases

**1. Time-Based Filtering**
```python
# Only show content updated in last 6 months
vector_search(
    query="latest products",
    metadata_filter={
        "updated_at": {"$gte": "2024-04-30"}
    }
)
```

**2. Content Type Filtering**
```python
# Search only published pages (exclude drafts, products)
vector_search(
    query="services overview",
    metadata_filter={
        "source_type": "page",
        "published": True
    }
)
```

**3. Multi-Category Filtering**
```python
# Search emergency and pediatric healthcare content
vector_search(
    query="emergency pediatric care",
    metadata_filter={
        "categories": {"$in": ["Emergency", "Pediatrics"]},
        "source_type": "page"
    }
)
```

**4. Language-Specific Search**
```python
# Search Spanish content only
vector_search(
    query="servicios de emergencia",
    metadata_filter={
        "language": "es"
    }
)
```

##### Benefits

- **Precision:** Filter out irrelevant content types
- **Freshness:** Exclude outdated content
- **Personalization:** Filter by user language preference
- **Performance:** Smaller candidate set = faster queries
- **Compliance:** Exclude unpublished/draft content from search

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

#### 7. **Alternate Chunking Strategies** (Priority: Medium)

**Current:** Fixed-size semantic chunking (500-1000 tokens, 100-200 overlap)  
**Future:** Adaptive chunking based on content type and structure

##### Chunking Strategy Comparison

| Strategy | Description | Pros | Cons | Best For |
|----------|-------------|------|------|----------|
| **Fixed-Size** (Current) | Split at N tokens with M overlap | Simple, predictable, works for any content | Breaks semantic boundaries, may split mid-sentence | General-purpose, mixed content |
| **Sentence-Based** | Split at sentence boundaries | Preserves complete thoughts, grammatically correct | Variable chunk sizes, may be too small/large | Narrative content, blog posts |
| **Paragraph-Based** | Split at paragraph boundaries | Preserves topical coherence, natural breaks | Highly variable sizes, some paragraphs too long | Well-structured articles, documentation |
| **Semantic Sectioning** | Split by headings/sections (H1, H2, H3) | Preserves document structure, topically coherent | Only works with structured content, variable sizes | Documentation, technical guides |
| **Sliding Window** | Overlapping windows of N tokens | Better context continuity, handles queries spanning boundaries | More vectors (higher cost), redundancy | Reference lookup, code documentation |
| **Recursive Hierarchical** | Chunk at multiple levels (doc → section → paragraph) | Preserves context at multiple scales, better retrieval | Complex implementation, requires hierarchy | Long documents, books, manuals |
| **Content-Aware** | Split by content type (lists, tables, code blocks) | Preserves structure, better formatting | Requires content parsing, type detection | Technical docs, API references |

##### Implementation Example: Adaptive Chunking

```python
# backend/app/services/chunking_service.py

class AdaptiveChunker:
    """Content-aware chunking based on document type and structure."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strategies = {
            "fixed": FixedSizeChunker(config),
            "semantic": SemanticChunker(config),
            "hierarchical": HierarchicalChunker(config),
            "content_aware": ContentAwareChunker(config)
        }
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Select and apply optimal chunking strategy."""
        # Detect content type
        content_type = self._detect_content_type(document)
        
        # Select strategy
        if content_type == "api_doc":
            strategy = self.strategies["content_aware"]
        elif content_type == "manual":
            strategy = self.strategies["hierarchical"]
        elif content_type == "blog":
            strategy = self.strategies["semantic"]
        else:
            strategy = self.strategies["fixed"]
        
        return strategy.chunk(document)
```

##### Configuration per Content Type

```yaml
# projects/wyckoff/config.yaml

chunking:
  strategies:
    website_pages:
      strategy: "semantic"        # Paragraph-based semantic chunking
      chunk_size: 800
      chunk_overlap: 150
      min_chunk_size: 200
    
    blog_posts:
      strategy: "semantic"
      chunk_size: 1000
      chunk_overlap: 200
      min_chunk_size: 300
    
    documentation:
      strategy: "hierarchical"    # Split by headings
      max_section_size: 1500
      min_section_size: 300
      preserve_headings: true
    
    product_descriptions:
      strategy: "content_aware"   # Preserve lists, tables
      chunk_size: 600
      preserve_structure: true
```

##### Pros & Cons Analysis

**Fixed-Size Chunking (Current)**
- ✅ **Pros:** 
  - Simple to implement
  - Predictable chunk count (cost estimation)
  - Works for any content type
  - Fast processing
- ❌ **Cons:**
  - Breaks semantic boundaries (sentence mid-split)
  - May split critical information (lists, tables)
  - Requires manual overlap tuning
  - Doesn't leverage document structure

**Semantic Sectioning**
- ✅ **Pros:**
  - Preserves topical coherence
  - Natural boundaries (headings, paragraphs)
  - Better retrieval relevance
  - Respects document structure
- ❌ **Cons:**
  - Requires well-structured content
  - Variable chunk sizes (token limit issues)
  - Doesn't work for unstructured text
  - May produce very large/small chunks

**Hierarchical Chunking**
- ✅ **Pros:**
  - Multi-scale context (doc → section → chunk)
  - Better for "navigating" long documents
  - Preserves relationships between sections
  - Enables hierarchical retrieval
- ❌ **Cons:**
  - Complex implementation
  - Requires parsing document hierarchy
  - Higher storage costs (redundant chunks)
  - Query complexity (which level to search?)

**Content-Aware Chunking**
- ✅ **Pros:**
  - Preserves special structures (code, tables, lists)
  - Better formatting in results
  - Type-specific optimization
  - Higher quality retrieval
- ❌ **Cons:**
  - Requires content type detection
  - More complex parsing logic
  - Type-specific tuning needed
  - Slower processing

##### Recommendation

**Phase 1:** Implement **Semantic Sectioning** for structured content (docs, manuals)
- Split by H1/H2/H3 headings
- Fallback to paragraph-based for unstructured sections
- Validate chunk sizes (200-1500 tokens)

**Phase 2:** Add **Content-Aware Chunking** for special content
- Detect and preserve code blocks (markdown fenced code)
- Preserve tables (HTML tables, markdown tables)
- Keep lists intact (ordered/unordered)

**Phase 3:** Implement **Hierarchical Chunking** for long documents
- Store parent-child relationships in metadata
- Enable "zoom in/out" retrieval
- Better context for follow-up questions

#### 8. **Cost Tracking for Vector Operations** (Priority: High)

**Current:** No cost tracking for embeddings or Pinecone operations  
**Future:** Comprehensive tracking like LLM cost tracking

##### Architecture

```python
# backend/app/models/vector_request.py

class VectorRequest(Base):
    """Track vector database operations for billing and monitoring."""
    __tablename__ = "vector_requests"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    account_id = Column(UUID, ForeignKey("accounts.id"), nullable=False)
    
    # Operation details
    operation_type = Column(String, nullable=False)  # "query" | "upsert" | "delete"
    index_name = Column(String, nullable=False)
    namespace = Column(String, nullable=True)
    
    # Query operations
    query_text = Column(Text, nullable=True)
    top_k = Column(Integer, nullable=True)
    similarity_threshold = Column(Float, nullable=True)
    metadata_filter = Column(JSONB, nullable=True)
    results_count = Column(Integer, nullable=True)
    
    # Upsert operations
    vectors_upserted = Column(Integer, nullable=True)
    
    # Embedding operations
    embedding_model = Column(String, nullable=False)
    embedding_provider = Column(String, nullable=False)  # "openai" | "cohere" | "azure"
    embedding_tokens = Column(Integer, nullable=True)
    embedding_cost_usd = Column(Float, nullable=True)
    
    # Pinecone operations
    pinecone_read_units = Column(Integer, nullable=True)
    pinecone_write_units = Column(Integer, nullable=True)
    pinecone_storage_vectors = Column(Integer, nullable=True)
    pinecone_cost_usd = Column(Float, nullable=True)
    
    # Performance
    embedding_latency_ms = Column(Float, nullable=True)
    pinecone_latency_ms = Column(Float, nullable=True)
    total_latency_ms = Column(Float, nullable=True)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

##### Cost Calculation

```python
# backend/app/services/vector_cost_tracker.py

class VectorCostTracker:
    """Track and calculate costs for vector operations."""
    
    # Embedding costs (per 1M tokens)
    EMBEDDING_COSTS = {
        "openai/text-embedding-3-small": 0.02,
        "openai/text-embedding-3-large": 0.13,
        "openai/text-embedding-ada-002": 0.10,
        "cohere/embed-english-v3.0": 0.10,
        "cohere/embed-multilingual-v3.0": 0.10,
    }
    
    # Pinecone costs (serverless)
    PINECONE_READ_COST = 0.0018 / 1000   # per operation
    PINECONE_WRITE_COST = 0.045 / 1000   # per operation
    PINECONE_STORAGE_COST = 0.25 / 1_000_000  # per vector per month
    
    async def track_query(
        self,
        session_id: UUID,
        account_id: UUID,
        query_text: str,
        embedding_tokens: int,
        embedding_model: str,
        embedding_latency_ms: float,
        pinecone_latency_ms: float,
        results_count: int,
        index_name: str,
        namespace: str,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Track a vector query operation."""
        
        # Calculate costs
        embedding_cost = self._calculate_embedding_cost(
            embedding_model, embedding_tokens
        )
        pinecone_cost = self.PINECONE_READ_COST  # 1 read operation
        total_cost = embedding_cost + pinecone_cost
        
        # Create tracking record
        vector_request = VectorRequest(
            session_id=session_id,
            account_id=account_id,
            operation_type="query",
            query_text=query_text,
            embedding_model=embedding_model,
            embedding_provider=embedding_model.split("/")[0],
            embedding_tokens=embedding_tokens,
            embedding_cost_usd=embedding_cost,
            pinecone_read_units=1,
            pinecone_cost_usd=pinecone_cost,
            embedding_latency_ms=embedding_latency_ms,
            pinecone_latency_ms=pinecone_latency_ms,
            total_latency_ms=embedding_latency_ms + pinecone_latency_ms,
            results_count=results_count,
            index_name=index_name,
            namespace=namespace,
            success=success,
            error_message=error_message
        )
        
        # Save to database
        async with get_db_session() as session:
            session.add(vector_request)
            await session.commit()
        
        # Log to Logfire
        logfire.info(
            "vector_operation_tracked",
            operation="query",
            session_id=str(session_id),
            account_id=str(account_id),
            embedding_tokens=embedding_tokens,
            embedding_cost_usd=embedding_cost,
            pinecone_cost_usd=pinecone_cost,
            total_cost_usd=total_cost,
            latency_ms=embedding_latency_ms + pinecone_latency_ms,
            results_count=results_count
        )
```

##### Integration with Vector Service

```python
# backend/app/services/vector_service.py (modified)

async def query_similar(
    self,
    query_text: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
    namespace: Optional[str] = None,
    metadata_filter: Optional[Dict[str, Any]] = None,
    session_id: Optional[UUID] = None,  # NEW
    account_id: Optional[UUID] = None   # NEW
) -> VectorQueryResponse:
    """Query with cost tracking."""
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Generate embedding (track time and tokens)
        embed_start = asyncio.get_event_loop().time()
        query_embedding = await self.embedding_service.embed_text(query_text)
        embedding_latency_ms = (asyncio.get_event_loop().time() - embed_start) * 1000
        
        # Estimate tokens
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        embedding_tokens = len(encoding.encode(query_text))
        
        # Query Pinecone (track time)
        pinecone_start = asyncio.get_event_loop().time()
        async with self.pinecone_client.connection_context():
            response = self.pinecone_client.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace,
                filter=metadata_filter
            )
        pinecone_latency_ms = (asyncio.get_event_loop().time() - pinecone_start) * 1000
        
        # Process results...
        results = [...]
        
        # Track costs (non-blocking)
        if session_id and account_id:
            asyncio.create_task(
                vector_cost_tracker.track_query(
                    session_id=session_id,
                    account_id=account_id,
                    query_text=query_text,
                    embedding_tokens=embedding_tokens,
                    embedding_model=self.pinecone_client.config.embedding_model,
                    embedding_latency_ms=embedding_latency_ms,
                    pinecone_latency_ms=pinecone_latency_ms,
                    results_count=len(results),
                    index_name=self.pinecone_client.config.index_name,
                    namespace=namespace or "__default__",
                    success=True
                )
            )
        
        return VectorQueryResponse(...)
        
    except Exception as e:
        # Track failed query
        if session_id and account_id:
            asyncio.create_task(
                vector_cost_tracker.track_query(
                    session_id=session_id,
                    account_id=account_id,
                    query_text=query_text,
                    embedding_tokens=0,
                    embedding_model=self.pinecone_client.config.embedding_model,
                    embedding_latency_ms=0,
                    pinecone_latency_ms=0,
                    results_count=0,
                    index_name=self.pinecone_client.config.index_name,
                    namespace=namespace or "__default__",
                    success=False,
                    error_message=str(e)
                )
            )
        raise
```

##### Cost Analytics Dashboard

**Example Queries:**

```sql
-- Total vector costs per account (last 30 days)
SELECT 
    a.name AS account_name,
    COUNT(*) AS total_queries,
    SUM(vr.embedding_cost_usd) AS embedding_costs,
    SUM(vr.pinecone_cost_usd) AS pinecone_costs,
    SUM(vr.embedding_cost_usd + vr.pinecone_cost_usd) AS total_costs,
    AVG(vr.total_latency_ms) AS avg_latency_ms
FROM vector_requests vr
JOIN accounts a ON vr.account_id = a.id
WHERE vr.created_at > NOW() - INTERVAL '30 days'
GROUP BY a.id, a.name
ORDER BY total_costs DESC;

-- Most expensive queries (by embedding tokens)
SELECT 
    query_text,
    embedding_tokens,
    embedding_cost_usd,
    results_count,
    total_latency_ms,
    created_at
FROM vector_requests
WHERE operation_type = 'query'
ORDER BY embedding_cost_usd DESC
LIMIT 20;

-- Failed query analysis
SELECT 
    error_message,
    COUNT(*) AS failure_count,
    AVG(total_latency_ms) AS avg_latency_ms
FROM vector_requests
WHERE success = FALSE
GROUP BY error_message
ORDER BY failure_count DESC;
```

##### Benefits

- **Billing Transparency:** Track exact costs per account/session
- **Cost Attribution:** Link vector costs to specific users/conversations
- **Performance Monitoring:** Identify slow queries, optimize indexes
- **Usage Analytics:** Understand query patterns, popular content
- **Budget Alerts:** Notify when costs exceed thresholds
- **ROI Analysis:** Compare vector search costs vs. value delivered

#### 9. **Disaster Recovery & Backup** (Priority: Medium)

**Current:** No automated backup or disaster recovery plan  
**Future:** Automated backups, point-in-time recovery, cross-region replication

##### Backup Strategy

**1. Index Snapshots (Export to S3)**

```python
# backend/scripts/backup_pinecone_index.py

import boto3
from pinecone import Pinecone
import asyncio
from datetime import datetime

async def backup_index_to_s3(
    index_name: str,
    namespace: str,
    s3_bucket: str,
    s3_prefix: str
):
    """Export Pinecone index to S3 for disaster recovery."""
    
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(index_name)
    s3 = boto3.client('s3')
    
    # Fetch all vectors in namespace
    vectors = []
    async for ids in index.list(namespace=namespace):
        # Fetch vectors in batches
        batch = index.fetch(ids=ids, namespace=namespace)
        vectors.extend(batch.vectors.values())
    
    # Create backup file
    backup_data = {
        "index_name": index_name,
        "namespace": namespace,
        "backup_timestamp": datetime.utcnow().isoformat(),
        "vector_count": len(vectors),
        "vectors": [
            {
                "id": v.id,
                "values": v.values,
                "metadata": v.metadata
            }
            for v in vectors
        ]
    }
    
    # Upload to S3
    backup_key = f"{s3_prefix}/{index_name}/{namespace}/{datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')}.json"
    s3.put_object(
        Bucket=s3_bucket,
        Key=backup_key,
        Body=json.dumps(backup_data),
        ServerSideEncryption='AES256'
    )
    
    print(f"Backup completed: s3://{s3_bucket}/{backup_key}")
    print(f"Vectors backed up: {len(vectors)}")
```

**2. Automated Daily Backups (Cron Job)**

```bash
# Crontab entry
0 2 * * * cd /app && python backend/scripts/backup_pinecone_index.py --index wyckoff-poc-01 --namespace __default__ >> /var/log/pinecone-backup.log 2>&1
```

**3. Point-in-Time Recovery**

```python
# Restore from S3 backup
async def restore_index_from_s3(
    s3_bucket: str,
    backup_key: str,
    target_index: str,
    target_namespace: str
):
    """Restore Pinecone index from S3 backup."""
    
    s3 = boto3.client('s3')
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(target_index)
    
    # Download backup
    backup_obj = s3.get_object(Bucket=s3_bucket, Key=backup_key)
    backup_data = json.loads(backup_obj['Body'].read())
    
    # Upsert vectors in batches
    vectors = backup_data['vectors']
    batch_size = 100
    
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch, namespace=target_namespace)
    
    print(f"Restore completed: {len(vectors)} vectors")
```

##### Cross-Region Replication

**Setup Secondary Index for Disaster Recovery**

```python
# Create replica index in different region
pc.create_index(
    name="wyckoff-poc-01-replica",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-west-2"  # Different region from primary (us-east-1)
    )
)

# Sync primary → replica (run periodically)
async def sync_indexes(primary_index: str, replica_index: str):
    """Sync primary index to replica for disaster recovery."""
    primary = pc.Index(primary_index)
    replica = pc.Index(replica_index)
    
    # Fetch all IDs from primary
    for ids in primary.list():
        # Fetch vectors
        vectors = primary.fetch(ids=ids)
        
        # Upsert to replica
        replica.upsert(vectors=[
            {
                "id": v.id,
                "values": v.values,
                "metadata": v.metadata
            }
            for v in vectors.vectors.values()
        ])
```

##### Failover Procedure

**1. Detect Primary Index Failure**

```python
# Health check
async def check_index_health(index_name: str) -> bool:
    """Check if index is healthy and responsive."""
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        return True
    except Exception as e:
        logger.error(f"Index {index_name} health check failed: {e}")
        return False
```

**2. Automatic Failover to Replica**

```python
# Agent config with failover
pinecone:
  index_name: "wyckoff-poc-01"
  failover_index: "wyckoff-poc-01-replica"  # NEW
  health_check_interval: 60  # seconds

# Service layer
async def get_index_with_failover(config):
    """Get index with automatic failover."""
    primary_healthy = await check_index_health(config.index_name)
    
    if primary_healthy:
        return pc.Index(config.index_name)
    else:
        logger.warn(f"Primary index {config.index_name} unhealthy, failing over to replica")
        return pc.Index(config.failover_index)
```

##### Recovery Time Objectives (RTO/RPO)

| Scenario | Recovery Time (RTO) | Data Loss (RPO) | Method |
|----------|---------------------|-----------------|--------|
| Index corruption | < 1 hour | < 24 hours | Restore from S3 backup |
| Region failure | < 5 minutes | < 1 hour | Failover to replica index |
| Accidental deletion | < 2 hours | 0 (soft delete) | Restore from backup + replay |
| Complete account loss | < 4 hours | < 24 hours | Restore all indexes from S3 |

#### 10. **Serverless to Pod-Based Migration** (Priority: Low)

**Current:** Serverless indexes (auto-scaling, pay-per-use)  
**Future:** Pod-based indexes for high-volume, predictable workloads

##### When to Migrate

**Stay on Serverless if:**
- < 100k queries per month
- Variable/unpredictable load
- Cost-sensitive (pay only for what you use)
- Rapid scaling needed
- Multiple small indexes

**Migrate to Pods if:**
- > 500k queries per month
- Predictable, high-volume traffic
- Latency-critical (< 50ms p99)
- Large indexes (> 1M vectors)
- Cost optimization at scale (fixed cost vs. per-query)

##### Cost Comparison

**Serverless:** $0.0018 per 1k reads + $0.25 per 1M vectors/month

| Monthly Queries | Storage (1M vectors) | Serverless Cost | Pod Cost (p1.x1) | Savings |
|-----------------|----------------------|-----------------|------------------|---------|
| 100k | $0.25 | $0.43 | $70 | -$69.57 (serverless cheaper) |
| 500k | $0.25 | $1.15 | $70 | -$68.85 (serverless cheaper) |
| 1M | $0.25 | $2.05 | $70 | -$67.95 (serverless cheaper) |
| 10M | $0.25 | $18.25 | $70 | **+$51.75 (pods cheaper)** |
| 50M | $0.25 | $90.25 | $70 | **+$20.25 (pods cheaper)** |

**Break-Even Point:** ~4-5M queries per month

##### Migration Process

**Phase 1: Create Pod-Based Index**

```python
from pinecone import Pinecone, PodSpec

pc = Pinecone(api_key="...")
pc.create_index(
    name="wyckoff-pod-01",
    dimension=1536,
    metric="cosine",
    spec=PodSpec(
        environment="us-east-1-aws",  # Must match region
        pod_type="p1.x1",             # 1 pod, 100k vectors, 20 QPS
        pods=2,                        # Scale to 2 pods = 40 QPS
        replicas=1,                    # 1 replica for HA
        shards=1                       # 1 shard
    )
)
```

**Phase 2: Migrate Data (Zero-Downtime)**

```python
async def migrate_serverless_to_pod(
    source_index: str,
    target_index: str,
    namespace: str
):
    """Migrate data from serverless to pod-based index."""
    
    source = pc.Index(source_index)
    target = pc.Index(target_index)
    
    # Fetch all vectors from source
    total_migrated = 0
    batch_size = 100
    
    for ids in source.list(namespace=namespace):
        # Fetch vectors
        vectors = source.fetch(ids=ids, namespace=namespace)
        
        # Upsert to target in batches
        batch = []
        for vector_id, vector in vectors.vectors.items():
            batch.append({
                "id": vector_id,
                "values": vector.values,
                "metadata": vector.metadata
            })
            
            if len(batch) >= batch_size:
                target.upsert(vectors=batch, namespace=namespace)
                total_migrated += len(batch)
                batch = []
        
        # Upsert remaining
        if batch:
            target.upsert(vectors=batch, namespace=namespace)
            total_migrated += len(batch)
    
    print(f"Migration complete: {total_migrated} vectors migrated")
```

**Phase 3: Parallel Running (Validation)**

```python
# Run both indexes in parallel for validation
async def dual_query(query_text: str):
    """Query both serverless and pod indexes, compare results."""
    
    serverless_result = await query_index("wyckoff-poc-01", query_text)
    pod_result = await query_index("wyckoff-pod-01", query_text)
    
    # Compare results
    if serverless_result.results != pod_result.results:
        logger.warn("Result mismatch between serverless and pod!")
    
    # Log latency comparison
    logger.info(
        "latency_comparison",
        serverless_ms=serverless_result.query_time_ms,
        pod_ms=pod_result.query_time_ms
    )
    
    return serverless_result  # Still serve from serverless during validation
```

**Phase 4: Cutover**

```yaml
# Update agent config to use pod-based index
tools:
  vector_search:
    pinecone:
      index_name: "wyckoff-pod-01"  # Switch from wyckoff-poc-01
```

**Phase 5: Decommission Serverless**

```python
# After 7 days of stable pod operation, delete serverless index
pc.delete_index("wyckoff-poc-01")
```

##### Pod Sizing Guide

| Pod Type | Capacity | QPS | Latency (p99) | Cost/Month | Use Case |
|----------|----------|-----|---------------|------------|----------|
| p1.x1 | 100k vectors | 20 | < 100ms | $70 | Small production |
| p1.x2 | 200k vectors | 40 | < 75ms | $140 | Medium production |
| p1.x4 | 400k vectors | 80 | < 50ms | $280 | High-volume production |
| p1.x8 | 800k vectors | 160 | < 30ms | $560 | Enterprise, low-latency |

**Scaling:**
- Horizontal: Add more pods (2x pods = 2x QPS)
- Replicas: Add replicas for HA and read scaling
- Shards: Add shards for > 1M vectors per pod

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

