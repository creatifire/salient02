# Epic 0010 - Website Content Ingestion

> Goal: Implement comprehensive website content ingestion pipeline to convert WordPress XML dumps and Astro websites to markdown, then index the content into Pinecone vector database for RAG-powered sales agent responses.

## Scope & Approach

### Content Ingestion Pipeline
- **WordPress XML Processing**: Parse WordPress export XML and convert to structured markdown
- **Astro Website Extraction**: Extract content from Astro pages and convert to markdown
- **Markdown Standardization**: Normalize content format for consistent vector database indexing
- **Vector Database Indexing**: Chunk and embed content for semantic search in Pinecone
- **Content Management**: Track, version, and update ingested content

### Target Content Types (Priority Order)
1. **Astro Website Content** (Phase 1 Priority)
   - Product pages, service descriptions, company information
   - Blog posts, technical documentation, FAQ content
   - Navigation structure and content relationships

2. **WordPress Content** (Phase 2 Priority)
   - Legacy blog posts and archived content
   - WordPress-specific custom post types
   - Historical content and documentation

## Features & Requirements

### [ ] 0010-001 - FEATURE - Astro Website Content Extraction (Phase 1 Priority)

#### [ ] 0010-001-001 - TASK - Astro Page Analysis & Extraction
- [ ] 0010-001-001-01 - CHUNK - Astro project scanner
  - SUB-TASKS:
    - Scan Astro project structure for content pages
    - Parse .astro files to extract content sections
    - Handle component-based content and dynamic imports
    - Extract frontmatter and page metadata
    - Identify content vs layout components
    - Acceptance: All Astro pages identified and content extracted

- [ ] 0010-001-001-02 - CHUNK - Content aggregation and structuring
  - SUB-TASKS:
    - Combine page content with component-based content
    - Resolve dynamic content and build-time variables
    - Extract navigation structure and page relationships
    - Preserve content hierarchy and site organization
    - Add page metadata (URL, title, description)
    - Acceptance: Complete site content structured for conversion

#### [ ] 0010-001-002 - TASK - Astro to Markdown Processing
- [ ] 0010-001-002-01 - CHUNK - Astro content converter
  - SUB-TASKS:
    - Convert Astro component content to markdown format
    - Handle JSX/TSX content blocks and dynamic content
    - Preserve markdown frontmatter and metadata
    - Convert component props to readable content
    - Add page context and navigation information
    - Acceptance: Astro content converted to structured markdown

### [ ] 0010-002 - FEATURE - WordPress Content Processing (Phase 2 Priority)

#### [ ] 0010-002-001 - TASK - XML Parsing & Structure Analysis
- [ ] 0010-002-001-01 - CHUNK - WordPress XML parser
  - SUB-TASKS:
    - Create WordPress XML export parser using ElementTree or lxml
    - Extract posts, pages, categories, tags, and custom fields
    - Handle WordPress-specific content structures (shortcodes, blocks)
    - Parse featured images and attachment metadata
    - Extract author information and publication dates
    - Acceptance: Complete WordPress site content extracted to structured data

- [ ] 0010-002-001-02 - CHUNK - Content filtering and validation
  - SUB-TASKS:
    - Filter published vs draft content based on post status
    - Exclude admin-only content and internal documentation
    - Validate content completeness and data integrity
    - Handle missing or corrupted content gracefully
    - Add content categorization based on post types and taxonomies
    - Acceptance: Only relevant, complete content proceeds to conversion

#### [ ] 0010-002-002 - TASK - WordPress to Markdown Conversion
- [ ] 0010-002-002-01 - CHUNK - HTML to Markdown converter
  - SUB-TASKS:
    - Convert WordPress HTML content to clean markdown
    - Handle WordPress shortcodes and custom block structures
    - Preserve formatting (headings, lists, links, images)
    - Convert tables, code blocks, and embedded media
    - Add frontmatter with metadata (title, date, categories, tags)
    - Acceptance: WordPress content converted to properly formatted markdown

- [ ] 0010-002-002-02 - CHUNK - Content enhancement and cleanup
  - SUB-TASKS:
    - Clean up WordPress-specific HTML artifacts
    - Normalize heading structures and content hierarchy
    - Add semantic metadata for better search relevance
    - Extract and preserve internal linking structures
    - Handle media references and image alt text
    - Acceptance: Markdown content is clean, semantic, and search-optimized

### [ ] 0010-003 - FEATURE - Markdown Processing & Standardization

#### [ ] 0010-003-001 - TASK - Content Normalization
- [ ] 0010-003-001-01 - CHUNK - Markdown standardization
  - SUB-TASKS:
    - Standardize markdown formatting across content sources
    - Normalize heading levels and content structure
    - Clean up inconsistent spacing and formatting
    - Validate markdown syntax and fix common issues
    - Add consistent metadata structure across all content
    - Acceptance: All content follows consistent markdown standards

- [ ] 0010-003-001-02 - CHUNK - Content enrichment
  - SUB-TASKS:
    - Add semantic tags and content categorization
    - Extract key phrases and topics for better searchability
    - Generate content summaries and abstracts
    - Add cross-references and internal linking metadata
    - Create content quality scores and relevance ratings
    - Acceptance: Content enhanced with semantic metadata for optimal search

#### [ ] 0010-003-002 - TASK - Content Chunking & Preparation
- [ ] 0010-003-002-01 - CHUNK - Intelligent content chunking
  - SUB-TASKS:
    - Split content into semantically meaningful chunks
    - Respect natural boundaries (sections, paragraphs, topics)
    - Maintain context and continuity across chunks
    - Add chunk metadata and relationship tracking
    - Optimize chunk size for vector embedding (500-1500 tokens)
    - Acceptance: Content optimally chunked for vector database indexing

### [ ] 0010-004 - FEATURE - Vector Database Integration

#### [ ] 0010-004-001 - TASK - Pinecone Setup & Configuration
- [ ] 0010-004-001-01 - CHUNK - Pinecone index management
  - SUB-TASKS:
    - Create dedicated Pinecone index for sales content
    - Configure index dimensions and similarity metrics
    - Set up namespace strategy for content organization
    - Implement index monitoring and health checks
    - Add backup and recovery procedures
    - Acceptance: Pinecone index ready for content ingestion

- [ ] 0010-004-001-02 - CHUNK - Embedding generation pipeline
  - SUB-TASKS:
    - Integrate with OpenAI or similar embedding API
    - Generate embeddings for all content chunks
    - Handle rate limiting and batch processing
    - Add embedding quality validation
    - Implement retry logic for failed embeddings
    - Acceptance: All content chunks have high-quality embeddings

#### [ ] 0010-004-002 - TASK - Content Indexing & Storage
- [ ] 0010-004-002-01 - CHUNK - Vector database population
  - SUB-TASKS:
    - Upload embeddings and metadata to Pinecone
    - Implement batch uploading for efficiency
    - Add content versioning and update tracking
    - Create content categorization within vector space
    - Implement duplicate detection and deduplication
    - Acceptance: All website content indexed and searchable in Pinecone

- [ ] 0010-004-002-02 - CHUNK - Search optimization and validation
  - SUB-TASKS:
    - Test search quality and relevance scoring
    - Optimize similarity thresholds and ranking
    - Add query preprocessing and enhancement
    - Implement search result filtering and post-processing
    - Create search analytics and performance monitoring
    - Acceptance: Vector search returns highly relevant, accurate results

### [ ] 0010-005 - FEATURE - Content Management & Updates

#### [ ] 0010-005-001 - TASK - Content Tracking & Versioning
- [ ] 0010-005-001-01 - CHUNK - Content inventory system
  - SUB-TASKS:
    - Track all ingested content with unique identifiers
    - Monitor content freshness and update dates
    - Implement content change detection
    - Add content source attribution and lineage
    - Create content quality and completeness metrics
    - Acceptance: Complete visibility into ingested content status

- [ ] 0010-005-001-02 - CHUNK - Update and refresh pipeline
  - SUB-TASKS:
    - Implement incremental content updates
    - Add automated re-ingestion for changed content
    - Handle content deletions and removals
    - Update vector embeddings for modified content
    - Maintain search index consistency during updates
    - Acceptance: Content stays current with minimal manual intervention

## Technical Architecture

### Content Processing Pipeline
```
WordPress XML / Astro Source → Parser → Content Extractor → Markdown Converter
                                                                    ↓
Vector Database (Pinecone) ← Embedding Generator ← Chunker ← Markdown Standardizer
```

### Database Schema Extensions
```sql
-- Content source tracking
content_sources:
  id (GUID, PK)
  source_type (VARCHAR) -- wordpress, astro
  source_url (VARCHAR)
  source_path (VARCHAR)
  last_ingested_at (TIMESTAMP)
  content_hash (VARCHAR) -- for change detection
  metadata (JSONB)

-- Ingested content tracking
ingested_content:
  id (GUID, PK)
  source_id (GUID, FK → content_sources.id)
  content_type (VARCHAR) -- page, post, product, faq
  title (VARCHAR)
  slug (VARCHAR)
  original_url (VARCHAR)
  markdown_content (TEXT)
  embedding_id (VARCHAR) -- Pinecone vector ID
  chunk_count (INTEGER)
  created_at (TIMESTAMP)
  updated_at (TIMESTAMP)

-- Content chunks for vector database
content_chunks:
  id (GUID, PK)
  content_id (GUID, FK → ingested_content.id)
  chunk_index (INTEGER)
  chunk_text (TEXT)
  embedding_id (VARCHAR) -- Pinecone vector ID
  token_count (INTEGER)
  metadata (JSONB)
```

### Configuration Schema (app.yaml)
```yaml
content_ingestion:
  wordpress:
    enabled: true
    xml_upload_path: "/uploads/wordpress"
    content_filters:
      - published_only: true
      - exclude_drafts: true
      - min_content_length: 100
  
  astro:
    enabled: true
    project_path: "./web"
    include_patterns:
      - "src/pages/**/*.astro"
      - "src/content/**/*.md"
    exclude_patterns:
      - "src/pages/demo/**"
      - "src/pages/dev/**"
  
  processing:
    chunk_size: 1000  # tokens
    chunk_overlap: 200  # tokens
    embedding_model: "text-embedding-3-small"
    quality_threshold: 0.5
  
  pinecone:
    index_name: "sales-content"
    namespace: "website"
    dimension: 1536
    metric: "cosine"
    batch_size: 100
```

### Integration Points
- **WordPress**: XML export file processing
- **Astro Projects**: Direct file system scanning and parsing  
- **OpenAI API**: Text embedding generation
- **Pinecone**: Vector storage and similarity search
- **Sales Agent**: Content retrieval for RAG responses

### Dependencies
- **0008**: Sales Agent (consumes ingested content for RAG)
- **Basic Vector DB Setup**: Pinecone account and API configuration
- **Embedding Service**: OpenAI or compatible embedding API

### Performance Considerations
- **Batch Processing**: Handle large content volumes efficiently
- **Rate Limiting**: Respect API limits for embedding generation
- **Chunking Strategy**: Optimize for both storage and retrieval
- **Caching**: Cache embeddings and processed content
- **Monitoring**: Track ingestion performance and quality

## Success Criteria
1. **WordPress Processing**: 100% of WordPress XML content successfully converted to markdown
2. **Astro Extraction**: All Astro pages and content accurately extracted and converted
3. **Vector Indexing**: All content chunked, embedded, and indexed in Pinecone
4. **Search Quality**: Vector search returns relevant, accurate results for sales queries
5. **Content Coverage**: Complete website content available for sales agent responses
6. **Update Pipeline**: Incremental updates work correctly for content changes
7. **Performance**: Large content volumes processed efficiently within reasonable time limits

This epic creates the content foundation necessary for the sales agent to provide accurate, website-sourced responses, enabling truly informed sales conversations.
