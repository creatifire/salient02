# Project Management Archive

> **Created**: January 12, 2025  
> **Last Updated**: January 12, 2025  
> This archive contains completed, superseded, and planning documentation from project development.

## Purpose

This folder preserves project management documents (epics, tasks, features) organized into three categories:
- **Completed**: Successfully finished epics from early project phases
- **Superseded**: Replaced by consolidated or improved approaches
- **Planning**: Ad-hoc planning documents, brainstorming, and demo implementations

These documents provide valuable historical context for understanding project evolution and architectural decisions.

## Archive Structure

```
archive/
├── README.md (this file)
├── completed/          # Successfully finished epics
├── superseded/         # Replaced by newer consolidated epics
└── planning/           # Ad-hoc planning, brainstorming, demos
```

---

## Archive Contents

### 📁 `completed/` - Successfully Finished Epics

Epics that were completed in early project phases and are no longer actively referenced in current development.

**Epic 0001 - Preliminary Design**
- **File**: `completed/0001-preliminary-design.md`
- **Date Completed**: Early 2025 (Phase 0)
- **Status**: Foundation work completed, informed later architecture
- **Content**: Initial design and architecture planning for the chat system
- **Value**: Historical context for early architectural decisions
- **Successor**: Design evolved into Epic 0004 (Chat Memory), Epic 0017 (Simple Chat), Epic 0022 (Multi-Tenant)

**Epic 0002 - Baseline Connectivity**
- **File**: `completed/0002-baseline-connectivity.md`
- **Date Completed**: Early 2025 (Phase 0)
- **Status**: Basic connectivity and infrastructure established
- **Content**: OpenRouter integration, FastAPI setup, basic request/response flow
- **Value**: Shows initial technical decisions and baseline implementation
- **Successor**: Evolved into Pydantic AI-based agent architecture

---

### 📁 `superseded/` - Replaced by Newer Consolidated Epics

Epics that were replaced by improved or consolidated approaches during active development.

**Epic 0017 - Simple Chat Agent (Original)**
- **File**: `superseded/0017-simple-chat-agent-old.md` (35KB, 734 lines)
- **Date Archived**: September 2025
- **Status**: Superseded by Epic 0022 (Multi-Tenant Architecture)
- **Reason**: Epic 0022 consolidated the multi-tenant architecture and simplified the implementation approach. The original Epic 0017 described a more complex, phase-based implementation that was streamlined in the actual development.
- **Key Changes**:
  - Original: Multi-phase agent factory, complex routing, registry system
  - New Approach: Explicit URL structure, hybrid DB + config files, no complex routing
  - Consolidation: Multi-tenant features integrated directly into Epic 0022
- **Value**: Shows the evolution from complex over-engineered approach to simple, explicit architecture
- **Lesson Learned**: Avoid premature abstraction - explicit URLs eliminated need for complex routing

---

### 📁 `planning/` - Ad-Hoc Planning & Brainstorming

Non-epic documents including brainstorming sessions, demo implementations, and exploratory planning.

**0004a - Integrated Plan (Brainstorming)**
- **File**: `planning/0004a-integrated-plan.md`
- **Type**: Ad-hoc planning document
- **Date Created**: Mid 2025
- **Status**: Brainstorming and high-level vision
- **Content**: System integration ideas across multiple layers:
  - OpenThought-level infrastructure provisioning
  - Customer-level chatbot configuration
  - Web presence strategies (Astro, WordPress, WooCommerce)
  - Content generation tools (SiteStory, AutoFAQtory)
- **Value**: Contains ideas that may inform future features and integrations
- **Note**: Not a formal epic - exploratory planning and system vision

**0004b - Demo: Retrieve and Summarize arXiv Articles**
- **File**: `planning/0004b-demo-retrive-summarize-arxiv-articles.md`
- **Type**: Demo/reference implementation
- **Date Created**: Mid 2025
- **Status**: Demo documentation with working code
- **Content**: 3-tier arXiv intelligence service architecture:
  - Tier 1: Free daily article retrieval and email digest
  - Tier 2: LLM-powered explainers with knowledge-level tuning
  - Tier 3: Premium multi-article synthesis with slide deck generation
  - Includes Python implementation using arxiv library
- **Value**: Pattern for document retrieval, LLM summarization, and tiered service models
- **Relevance**: Demonstrates concepts applicable to research agents (Epic 0015, 0016)
- **Note**: Demo implementation, not a formal epic

**Milestone 02 - WordPress & Multi-CRM Expansion (Deferred)**
- **File**: `planning/0000-approach-milestone-02.md`
- **Type**: Milestone planning document
- **Date Archived**: January 12, 2025
- **Status**: Deferred for future consideration
- **Content**: Sequential expansion plan post-Milestone 1:
  - Priority 1: WordPress content pipeline (XML processing, markdown conversion)
  - Priority 2: PostgreSQL pgvector for cost-effective vector storage
  - Priority 3: Salesforce CRM integration
  - Priority 4: CrossFeed MCP Server for cross-sell/upsell intelligence
  - Priority 5: HubSpot CRM integration
- **Associated Epics**: Epic 0010 (Website Content Ingestion), Epic 0014 (CrossFeed MCP)
- **Reason**: Focus shifted to completing Milestone 1 core features; multi-CRM expansion deferred
- **Value**: Complete roadmap for WordPress integration and enterprise CRM capabilities
- **Note**: May be revisited when Milestone 1 is fully complete

**Epic 0010 - Website Content Ingestion**
- **File**: `planning/0010-website-content-ingestion.md`
- **Type**: Epic (deferred)
- **Date Archived**: January 12, 2025
- **Status**: Planned for M2 Priority 1, now deferred
- **Content**: WordPress content processing pipeline:
  - WordPress XML export processing
  - Markdown conversion with metadata preservation
  - Advanced content handling (shortcodes, blocks, media)
  - Pinecone integration for vector search
- **Dependencies**: Epic 0011 (Vector Database) already completed
- **Reason**: Milestone 2 deferred; Astro content pipeline (Feature 0010-001) already working
- **Value**: Complete WordPress integration strategy for content-heavy sites
- **Note**: May be prioritized if client requires WordPress integration

**Epic 0014 - CrossFeed MCP Server**
- **File**: `planning/0014-crossfeed.md`
- **Type**: Epic (deferred)
- **Date Archived**: January 12, 2025
- **Status**: Planned for M2 Priority 4, now deferred
- **Content**: MCP server for sales intelligence:
  - Cross-sell opportunity identification
  - Upsell intelligence implementation
  - Product catalog integration
  - Competitive selling data
- **Dependencies**: Epic 0008 (Sales Agent)
- **Reason**: Milestone 2 deferred; focus on core chat and profile tools first
- **Value**: Advanced sales intelligence capabilities via MCP protocol
- **Note**: Synergies with Epic 1017 (Data as MCP Service) in backlog

## Current Project Management Documentation

For active project management documentation, see:

- **Development Approach**: `/memorybank/project-management/0000-approach-milestone-01.md`
- **Master Epic List**: `/memorybank/project-management/0000-epics.md`
- **Active Epics**: `/memorybank/project-management/00XX-*.md` (all numbered epic files)
- **Multi-Tenant Architecture**: `/memorybank/project-management/0022-multi-tenant-architecture.md` (current implementation)

## Related Archives

**Architecture Documentation Archive**: `/memorybank/archive/`
- Contains archived architecture and design documents (not epics)
- See `/memorybank/archive/README.md` for architecture archive contents

## When to Archive Project Management Documents

Epic or task files should be moved to this archive when:

1. **Superseded**: A new epic replaces or consolidates the old approach
2. **Completed**: Epic finished and implementation stable (optional - some teams prefer to keep completed epics in main folder)
3. **Approach Changed**: Fundamental shift in implementation strategy makes old planning obsolete
4. **Historical Reference Only**: Document no longer guides active development but provides valuable context

## Archive Guidelines

- **Don't Update**: Archived documents are historical snapshots - don't modify them
- **Cross-Reference**: Link from current epics to archived ones when relevant (e.g., "See archived Epic 0017 for original approach")
- **Preserve Context**: Keep commit history and file metadata intact
- **Update This README**: Add entries when archiving new documents

## Retrieval

If you need to reference archived epics:
1. Check current epics first - they may reference or incorporate archived content
2. Review this README for quick overview and supersession notes
3. Read archived files with historical context in mind
4. Consider whether archived approach has relevant ideas for current challenges

