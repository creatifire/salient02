<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Tactical Development Approach - Streamlined
> **Last Updated**: October 11, 2025
> Sequential development approach focused on incremental enhancement and systematic scaling

## Executive Summary

**Current State**: ~70% project completion with core agent implementation complete:
- ✅ Epic 0004 (Chat Memory & Persistence) - Session management, database, message persistence
- ✅ Feature 0005-001 (Pydantic AI Framework) - Agent infrastructure ready  
- ✅ Feature 0011-001 (Vector Database Setup) - Pinecone integration working
- ✅ Feature 0017-003 (Core Agent Implementation) - Pydantic AI agent with conversation loading, cost tracking

- [ Note: Look for documents as a whole or sections of documents that can be used to provide context to LLMs (beyond Vector Databases) ]

**Approach**: Linear progression through priority items organized into phases, with manageable chunks and automated testing documented in epic files.

---

# PHASE 1: MVP Core Functionality

## 🎯 DEVELOPMENT PRIORITIES

### **Priority 0: Cleanup Overengineered Code** ✅
- [x] 0017-001-001 - Pre-Cleanup Safety & Documentation
- [x] 0017-001-002 - Update Test Files  
- [x] 0017-001-003 - Remove Overengineered Components
- [x] 0017-001-004 - Verify Clean Foundation

### **Priority 1: Legacy Agent Switch** ✅  
- [x] 0017-002-001 - Configuration-driven endpoint registration


### **Priority 2: Simple Chat Agent Implementation** ✅
- [x] 0017-003-001 - Direct Pydantic AI Agent Implementation
- [x] 0017-003-002 - Conversation History Integration  
- [x] 0017-003-003 - FastAPI Endpoint Integration
- [x] 0017-003-004 - LLM Request Tracking & Cost Management
- [x] 0017-003-005 - Agent Conversation Loading

### **Priority 2A: Configuration Cascade & Consistency** ✅
- [x] 0017-004-001 - Configuration Parameter Standardization
- [x] 0017-004-002 - Agent-First Configuration Cascade
- [x] 0017-004-003 - Extend Configuration Cascade to Additional Parameters
  - [x] 0017-004-003-01 - Model settings cascade implementation
  - [x] 0017-004-003-02 - Tool configuration cascade

### **Priority 2B: Multi-Tenant Account-Instance Architecture** ✅ **COMPLETE**
**Epic 0022 - Foundational Infrastructure for Pydantic AI Migration**

**Why Priority 2B**: All endpoints must use Pydantic AI (core architecture principle). Epic 0022 provides the multi-tenant infrastructure to properly migrate ALL endpoints to Pydantic AI without breaking existing functionality.

**Status**: Production-ready multi-tenant architecture complete. Core features implemented and tested. Optional enhancements (iframe embedding, advanced observability, admin UI) deferred to focus on MVP delivery.

- [x] 0022-001 - Core Multi-Tenancy Infrastructure ✅
  - [x] 0022-001-001 - Database & Configuration Infrastructure ✅
    - [x] 0022-001-001-01 - Test instance configuration files ✅
    - [x] 0022-001-001-02 - Multi-tenant database schema migration ✅
    - [x] 0022-001-001-03 - Agent instance loader implementation ✅
    - [x] 0022-001-001-04 - Instance discovery and listing ✅
  - [x] 0022-001-002 - Multi-Provider Infrastructure (Logfire complete, rest deferred to after Priority 6) ✅
    - [x] 0022-001-002-00 - Logfire observability integration ✅
    - Chunks 01-06 (Provider factory, Together.ai) - DEFERRED to after Priority 6
  - [x] 0022-001-003 - API Endpoints ✅ **COMPLETE**
    - [x] 0022-001-003-01 - Account agents router setup ✅
    - [x] 0022-001-003-01a - Session context migration (nullable fields) ✅
    - [x] 0022-001-003-02 - Non-streaming chat endpoint ✅
    - [x] 0022-001-003-03 - Streaming chat endpoint ✅
    - [x] 0022-001-003-04 - Instance listing endpoint ✅
  - [x] 0022-001-004 - Frontend Widget Migration ✅ **COMPLETE**
    - [x] 0022-001-004-01 - Astro/Preact components ✅ **PRODUCTION READY**
    - [ ] 0022-001-004-02 - Create iframe embedding option (NEW, non-breaking) ⏸️ **DEFERRED**
    - [ ] 0022-001-004-03 - Multi-tenant showcase demo (educational) ⏸️ **DEFERRED**
  - [ ] 0022-001-005 - Cost Tracking & Observability ⏸️ **MOVED TO PRIORITY 3**
    - [x] 0022-001-005-01 - LLM request tracker updates (denormalized columns for fast billing queries) ✅ **DONE in Priority 3**
    - [x] 0022-001-005-02 - Link LLM requests to messages (1:many FK for cost attribution and debugging) ✅ **DONE in Priority 3**
  - [ ] 0022-001-006 - Testing & Validation ⏸️ **DEFERRED**
  - [ ] 0022-001-007 - Simple Admin UI (Optional) ⏸️ **DEFERRED**
- [ ] 0022-002 - Authentication & Authorization ⏸️ **DEFERRED**

### **Priority 3: Data Model Cleanup & Cost Attribution** ✅ **COMPLETE** (4/4 complete)
**Completed to enable accurate billing and debugging**

- [x] 0022-001-005-01 - Populate denormalized fields in LLM requests (BUG-0017-005) ✅
  - Update `llm_request_tracker.py` to populate: account_id, account_slug, agent_instance_slug, agent_type, completion_status
  - Enables fast billing queries without JOINs across 3 tables
  - **Status**: ✅ FIXED 2025-10-18 - Database verified: 100% field population, 0 NULL values
  - **Verification**: 5/5 recent records have all denormalized fields populated correctly
  - See: [bugs-0017.md](bugs-0017.md) for implementation details and verification
  
- [x] 0022-001-005-02 - Link LLM requests to messages (1:many FK) ✅
  - Add `llm_request_id` (nullable FK) to messages table
  - Enables cost attribution per message and debugging
  - **Status**: ✅ COMPLETE (2025-10-18) - Migration created, models updated, agent integration complete
  - **Verification**: 1:many relationship established, both user and assistant messages link to same LLM request
  - From: Epic 0022-001-005 (deferred from Priority 2B)

- [x] BUG-0017-006 - Pinecone multi-project API key support ✅ **FIXED 2025-10-19**
  - **Issue**: Wyckoff (openthought-dev project) and AgroFresh (Agrobot project) needed separate Pinecone API keys
  - **Fix Part 1**: Per-agent `api_key_env` config parameter (architecture already supported this)
  - **Fix Part 2**: Lazy singleton initialization to prevent module-level API key requirement
  - **Changes**: 
    - Config: Updated agent config.yaml files with project-specific env vars (PINECONE_API_KEY_OPENTHOUGHT, PINECONE_API_KEY_AGROBOT)
    - Code: Converted module-level singletons to lazy initialization (pinecone_client.py, embedding_service.py, vector_service.py)
  - **Testing**: ✅ Both agents' vector search works without global PINECONE_API_KEY
  - **Commits**: `3186ef5` (config), `30b50b9` (caching), `9984e99` (lazy init)
  - See: [bugs-0017.md](bugs-0017.md#bug-0017-006) for full details

- [x] 0022-001-005-03 - Add agent_instance_slug to sessions table (fast analytics) ✅ **COMPLETE 2025-10-20**
  - Add denormalized `agent_instance_slug` (TEXT, nullable, indexed) to sessions table
  - Enables fast session analytics without JOINs to agent_instances table
  - Follows same denormalization pattern as llm_requests table
  - **Implementation**: Migration `48d95232d581_add_agent_instance_slug_to_sessions.py` created and applied
  - **Testing**: Manual testing confirmed all agents populate agent_instance_slug correctly
  - See: [Epic 0022-001-005-03](0022-multi-tenant-architecture.md#0022-001-005-03) for detailed implementation plan

- [x] 0017-005-003 - Multi-Agent Data Integrity Verification Script ✅ **COMPLETE 2025-10-20**
  - Create comprehensive manual test script: `backend/tests/manual/test_data_integrity.py`
  - **Purpose**: Verify all database tables are populated correctly after Priority 3 changes
  - **Scope**: Test 5 multi-tenant agents only (excludes legacy non-multi-tenant endpoints - see BUG-0017-007)
    - agrofresh/agro_info_chat1, wyckoff/wyckoff_info_chat1, default_account/simple_chat1, default_account/simple_chat2, acme/acme_chat1
  - **Verification**: For each agent, send test chat request and verify:
    - Sessions table: account_id, agent_instance_id, agent_instance_slug populated
    - Messages table: session_id, llm_request_id FK populated, role/content correct
    - LLM_requests table: account_id, account_slug, agent_instance_slug, agent_type, completion_status populated
    - Costs tracked: prompt_cost, completion_cost, total_cost non-zero
    - **Multi-tenant isolation** (all 3 scenarios):
      - Session-level: Messages don't leak between sessions
      - Agent-level: Data properly attributed within account
      - Account-level: Complete data isolation between accounts
  - **Implementation**: ✅ Option 1 chosen - Sequential Database Queries
    - 3 output formats: `--format rich|simple|json` (rich default)
    - Data preserved by default for manual inspection
    - Separate cleanup script: `cleanup_test_data.py` with `--dry-run`, `--agent`, `--all` flags
    - Timing added to track LLM performance per agent
  - **Configuration**: YAML config file `test_data_integrity_config.yaml` specifying test prompts per agent
  - **Testing**: Manual testing confirmed all 5 agents PASS with proper isolation and cost tracking
  - **Files Created**:
    - `backend/tests/manual/test_data_integrity.py` (main test script)
    - `backend/tests/manual/cleanup_test_data.py` (cleanup script)
    - `backend/tests/manual/test_data_integrity_config.yaml` (test configuration)
  - **See**: [Epic 0017-005-003](0017-simple-chat-agent.md#0017-005-003) for detailed implementation plan

### **Priority 4: Vector Search Tool** ✅ **COMPLETE**
**Epic 0017-005 - Vector Search Tool with Multi-Client Demo Architecture**

**Why Priority 4**: Demonstrates vector search capabilities through realistic client demo sites with proper multi-tenant account separation. Showcases Epic 0022's multi-tenant architecture in a sales-ready format.

**Status**: Vector search tool fully implemented and tested. Wyckoff agent can now search hospital WordPress content via Pinecone. Multi-client demo sites (agrofresh, wyckoff) operational with distinct agent configurations.

- [x] 0017-005-001 - Multi-Client Demo Site Architecture ✅
  - [x] 0017-005-001-01 - Multi-client folder structure and layouts ✅
  - [x] 0017-005-001-02 - Wyckoff Hospital demo pages ✅
  - [x] 0017-005-001-03 - Agent configurations (agrofresh, wyckoff) ✅
  - **Status**: 3 accounts configured (agrofresh, wyckoff, default_account)
  - **Agents**: agrofresh/agro_info_chat1 (DeepSeek), wyckoff/wyckoff_info_chat1 (Qwen), acme/acme_chat1 (Mistral), default_account/simple_chat1 (Kimi), default_account/simple_chat2 (GPT-OSS)
  - **Bugs**: Tracked in [bugs-0017.md](bugs-0017.md) - 2/5 fixed, 3 remaining
  
- [x] 0017-005-002 - Vector Search Tool Implementation ✅
  - [x] 0017-005-002-01 - Per-agent Pinecone configuration loader ✅
  - [x] 0017-005-002-02 - Pydantic AI @agent.tool for vector search ✅
  - [x] 0017-005-002-03 - End-to-end testing with real Pinecone data ✅
  - Core InfoBot functionality - answers questions using knowledge base via @agent.tool
  - **Status**: All 3 chunks complete, test script passed (wyckoff-poc-01 index: 605 vectors, all queries successful)
  - **Commits**: da887ae, 379e59b, c0499d3, b77b6eb
  - **Testing**: backend/tests/manual/verify_wyckoff_index.py ✅ PASSED
  - **Dependencies**: Priority 3 complete (denormalized cost tracking helps with debugging)

- [x] 0003-010 - Chat Widget Maximize/Minimize Toggle ✅ **COMPLETE**
  - Add maximize/minimize functionality to Shadow DOM chat widget
  - Implementation: Size-based transitions (width/height) with bottom-right anchor preserved
  - Minimized: 480px height (fixed) | Maximized: calc(100vh - 97px)
  - Features: Toggle button (left side), smooth 500ms CSS transitions with cubic-bezier easing, localStorage persistence
  - Accessibility: ARIA labels, tab order, ESC key two-step (maximize→minimize→close)
  - Mobile: Force minimized on <768px, hide maximize button, auto-minimize on resize
  - SVG icons: chat-maximize.svg, chat-minimize.svg, chat-close.svg
  - Testing: Manual testing complete ✅ - smooth transitions, no regressions, seamless during SSE streaming
  - See: [Epic 0003-010](0003-website-htmx-chatbot.md#0003-010) for detailed implementation (8 tasks, 7 complete, 1 doc deferred)

### **Priority 5: Directory Search Tool** 📋 🎯 **DEMO FEATURE**
**Epic 0023 - Multi-Purpose Directory Service**

**Why Priority 5**: Generic directory service for searching structured entries (doctors, drugs, products, consultants, services) via natural language. Enables agents to answer specific queries about people, inventory, or resources. Demonstrates real-world tool usage with flexible data types.

**Dependencies**: Requires `accounts` and `agent_instances` tables from Epic 0022 (already complete in Priority 2B).

**Phase 1 - MVP (Complete ✅)**:
- [x] 0023-001 - Core Infrastructure ✅
  - [x] 0023-001-001 - Database Schema (directory_lists, directory_entries with UUIDs, GIN indexes) ✅
  - [x] 0023-001-002 - Schema Definitions (medical_professional.yaml) ✅
  - [x] 0023-001-003 - CSV Import (DirectoryImporter + seed script - 124 Wyckoff doctors) ✅
  - [x] 0023-001-004 - DirectoryService (SQLAlchemy queries with multi-tenant filtering) ✅
- [x] 0023-002 - Search Tool ✅
  - [x] 0023-002-001 - search_directory Pydantic AI tool (with explicit params) ✅
  - [x] 0023-002-002 - Wyckoff integration & testing (manual curl verified) ✅
- [x] 0023-008 - Multi-Tenant Dependencies ✅
  - [x] 0023-008-001 - SessionDependencies (account_id + db_session) ✅

**Phase 2 - Advanced Configurability (Planned)**:
- [x] 0017-005-004 - PrepExcellence Demo Site Implementation ✅ **COMPLETE**
  - [x] 0017-005-004-001 - Database and backend agent configuration ✅
  - [x] 0017-005-004-002 - Frontend folder structure and layouts ✅
  - [x] 0017-005-004-003 - Create PrepExcellence demo pages ✅
  - [x] 0017-005-004-004 - Demo selector integration and testing ✅
  - [x] 0017-005-004-005 - Vector search end-to-end testing ✅
  - **Purpose**: SAT/ACT/PSAT test prep demo site with Dr. Kaisar Alam
  - **Vector Search**: Enabled (prepexcellence-poc-01 index, __default__ namespace, PINECONE_API_KEY_OPENTHOUGHT)
  - **Model**: google/gemini-2.5-flash (excellent tool calling, educational content)
  - **Theme**: Purple/blue academic palette (#6A1B9A, #1976D2)
  - **Pages**: Homepage, About, Courses (Index, SAT, ACT, PSAT), Tutoring, Admissions, Contact (all complete)
  - **Status**: Backend ✅, Frontend Structure ✅, All Pages ✅, Demo Selector ✅, Vector Search ✅
  - **See**: [Epic 0017-005-004](0017-simple-chat-agent.md#0017-005-004) for detailed implementation plan

**Phase 2 - Search Quality & Scalability (Revised Priority Order)**:
- [x] 0023-007-002 - PostgreSQL Full-Text Search ✅ **COMPLETE**
  - Word-level matching, stemming, relevance ranking
  - **Result**: 0.68ms query time (143x faster than target)
  - **Status**: Complete - immediate search quality improvement delivered

- [x] 0023-004-001 - Schema-Driven Generic Filters ✅ **COMPLETE**
  - Replace explicit params with generic `filters` dict
  - Add `searchable_fields` to schema YAML files
  - Auto-generate system prompt from schemas
  - Enable zero-code addition of new directory types
  - **Value**: HIGH (unblocks scalability)
  - **Status**: All 5 chunks complete, extensive manual testing, SSE streaming fix included

**Priority 5A - Bug Fixes & Production Readiness** 🔧 **CRITICAL**
**Epic 0023 Bug Fixes + Critical Library Migrations**

**Why Priority 5A**: Address blocking bugs and critical migrations needed for production stability. These items prevent functionality (BUG-0023-002), impact scalability (BUG-0023-003), or use deprecated patterns that will break in future FastAPI versions.

**Priority Order** (ranked by impact and urgency):

1. **BUG-0023-002** (P1) - Configuration Cascade Path Error ✅ **COMPLETE**
   - **Problem**: Config loader uses wrong path, all agents fall back to global config
   - **Impact**: Directory service and multi-tenant agents can't load instance-specific configs
   - **Effort**: 1-2 hours ✅ **COMPLETE**
   - **Fix**: Update path construction in config loader from `agent_configs/{agent_type}/config.yaml` to `agent_configs/{account_slug}/{instance_slug}/config.yaml`
   - **Files**: `backend/app/agents/config_loader.py` ✅ **COMPLETE**
   - **Status**: ✅ **COMPLETE** - Manual testing passed (January 12, 2025)
   - **Commit**: `74ed4f9`
   - **See**: [bugs-0023.md](bugs-0023.md#bug-0023-002-configuration-cascade-path-error--complete)

2. **BUG-0023-003** (P2) - Connection Pool Sizing ✅ **COMPLETE**
   - **Problem**: `max_overflow=0` means no burst capacity, pool may exhaust under concurrent load
   - **Impact**: Connection pool exhaustion during traffic spikes
   - **Effort**: 15 minutes (single config change) ✅ **COMPLETE**
   - **Fix**: Add `max_overflow=10` to SQLAlchemy engine configuration ✅ **COMPLETE**
   - **Files**: Database engine initialization ✅ **COMPLETE**
   - **Status**: ✅ **COMPLETE** - Configuration updated (January 12, 2025)
   - **Commit**: `4de196e`
   - **See**: [bugs-0023.md](bugs-0023.md#bug-0023-003-connection-pool-sizing--complete) | [Connection Pool Configuration](../../analysis/critical-libraries-review.md#connection-pool-configuration-)

3. **FastAPI Lifespan Migration** ✅ **COMPLETE**
   - **Problem**: Using deprecated `@app.on_event()` pattern (will break in future FastAPI versions)
   - **Impact**: Future-proofing, prevents breaking changes
   - **Effort**: 2-4 hours (migrate startup/shutdown handlers) ✅ **COMPLETE**
   - **Fix**: Migrate from `@app.on_event("startup")`/`@app.on_event("shutdown")` to `lifespan()` context manager ✅ **COMPLETE**
   - **Files**: `backend/app/main.py` ✅ **COMPLETE**
   - **Status**: ✅ **COMPLETE** - Already migrated (uses `@asynccontextmanager` with `lifespan()`)
   - **See**: [Critical Libraries Review](../../analysis/critical-libraries-review.md#critical-patterns--1)

4. **SQLAlchemy selectinload() Migration** ✅ **COMPLETE**
   - **Problem**: N+1 queries when accessing relationships without eager loading
   - **Impact**: Performance degradation under load, database connection exhaustion
   - **Effort**: 4-8 hours (audit all relationship accesses, add selectinload()) ✅ **COMPLETE**
   - **Fix**: Add `selectinload()` for all relationship accesses in queries ✅ **COMPLETE**
   - **Files**: All service files with relationship queries (messages, sessions, accounts, etc.) ✅ **COMPLETE**
   - **Implementation**: Added selectinload() to Session, Message, DirectoryList, and DirectoryEntry queries across 7 files
   - **Status**: ✅ **COMPLETE** - All queries now use eager loading to prevent N+1 queries (January 12, 2025)
   - **Commit**: `c78799a`
   - **See**: [Critical Libraries Review](../../analysis/critical-libraries-review.md#critical-patterns--1)

5. **Pydantic AI RunContext Verification** ✅ **COMPLETE**
   - **Problem**: Verify all tools use `RunContext[DepsType]` pattern (may have inconsistencies)
   - **Impact**: Type safety, proper dependency injection, architecture compliance
   - **Effort**: 1-2 hours (audit all tools, fix any inconsistencies) ✅ **COMPLETE**
   - **Fix**: Review all `@agent.tool` functions, ensure first parameter is `RunContext[SessionDependencies]` ✅ **COMPLETE**
   - **Files**: `backend/app/agents/tools/*.py`, `backend/app/agents/simple_chat.py`, `backend/app/agents/base/agent_base.py` ✅ **COMPLETE**
   - **Implementation**: 
     - Verified `vector_search` uses `RunContext[SessionDependencies]` ✅
     - Verified `search_directory` uses `RunContext[SessionDependencies]` ✅
     - Fixed `tool_wrapper` in `agent_base.py` to use `RunContext[DepsType]` ✅
   - **Status**: ✅ **COMPLETE** - All tools now use correct RunContext pattern (January 12, 2025)
   - **Commit**: Pending
   - **See**: [Critical Libraries Review](../../analysis/critical-libraries-review.md#critical-patterns--1)

6. **Alembic Async Migration Verification** ✅ **COMPLETE**
   - **Problem**: Ensure all migrations use async engine patterns
   - **Impact**: Migration compatibility, prevents blocking migrations
   - **Effort**: 1-2 hours (review migration scripts, test async patterns) ✅ **COMPLETE**
   - **Fix**: Verify migrations use `async_engine_from_config()` and `connection.run_sync()` pattern ✅ **COMPLETE**
   - **Files**: `backend/migrations/env.py` and migration scripts ✅ **COMPLETE**
   - **Implementation**: 
     - Updated `run_async_migrations()` to use `async_engine_from_config()` (recommended pattern)
     - Verified all 8 migration scripts use sync `upgrade()`/`downgrade()` functions (correct pattern)
     - Confirmed `connection.run_sync(do_run_migrations)` pattern is properly implemented
     - Async detection via `+asyncpg` in database URL works correctly
   - **Status**: ✅ **COMPLETE** - All migrations use correct async patterns (January 12, 2025)
   - **Commit**: Pending
   - **See**: [Critical Libraries Review](../../analysis/critical-libraries-review.md#critical-patterns--1)

**Medium Priority** (can be addressed after Priority 5A):
- Pinecone Namespaces: Verify namespace isolation per account
- Logfire Instrumentation: Ensure all libraries instrumented
- Transaction Management: Verify all multi-step operations use transactions

**Status**: BUG-0023-002 ✅ COMPLETE, BUG-0023-003 ✅ COMPLETE, FastAPI Lifespan ✅ COMPLETE, SQLAlchemy selectinload() ✅ COMPLETE, Pydantic AI RunContext ✅ COMPLETE, Alembic Async ✅ COMPLETE - Priority 5A addresses critical bugs and migrations needed before production deployment.

**See**: 
- [bugs-0023.md](bugs-0023.md) for bug details
- [critical-libraries-review.md](../../analysis/critical-libraries-review.md) for migration patterns

---

- [ ] 0023-004-003 - Centralized Tool Registry (Optional)
  - Single source of truth for tool metadata
  - Automatic dependency validation
  - **Value**: MEDIUM (clean architecture)

- [ ] 0023-005-001 - Incremental CSV Updates (If Needed)
  - Support partial updates instead of delete-and-replace
  - Merge/replace/update modes
  - **Value**: LOW (only if data changes frequently)

**Deferred**:
- [ ] 0023-003 - Semantic Search (Pinecone) ⏸️ **DEFERRED**
  - [ ] 0023-003-001 - directory_embeddings table
  - [ ] 0023-003-002 - Embedding generation pipeline
  - [ ] 0023-003-003 - Hybrid search (exact + semantic)
  - **Value**: MEDIUM (FTS solves most needs)
  - **Status**: Re-evaluate after FTS - likely not needed

**Architecture Highlights**:
- Multi-list support per account (doctors, drugs, products, consultants, services)
- Agent-level access control via config YAML
- Flexible schema: Core columns + JSONB for type-specific fields
- Search strategy: Exact/substring (Phase 1) → FTS (Phase 2) → Semantic (Phase 3)

**Current Capabilities**:
- ✅ Wyckoff: 124 doctors, filter by specialty/gender/department, language tags
- ✅ Queries: "Find a female Spanish-speaking endocrinologist"
- ⏸️ Future: Pharmaceuticals, products, consultants (after 0023-004-001)

### **Priority 6: Profile Fields Configuration & Database Schema** 📋
- [ ] 0017-006-001 - Profile Fields YAML Configuration
- [ ] 0017-006-002 - Migrate Profiles Table to JSONB

### **Priority 7: Profile Capture Tool** 📋
**Epic 0017-012** (Renumbered from 0017-007)

- [ ] 0017-012-001 - Profile Capture Agent Tool
  - Conversational capture of email/phone using @agent.tool

### **Priority 8: Email Summary Tool with Mailgun** 📋
- [ ] 0017-008-001 - Mailgun Integration
- [ ] 0017-008-002 - Email Summary Agent Tool
  - Completes user workflow: chat → capture → email summary

### **Priority 9: Multi-Provider Infrastructure** 📋
- [ ] 0022-001-002-01 - Provider factory and base infrastructure
- [ ] 0022-001-002-02 - Config schema and validation
- [ ] 0022-001-002-03 - Update simple_chat agent to use factory
- [ ] 0022-001-002-04 - Update test instance configs (4th agent: acme/simple_chat2 with Together.ai + different model family)
- [ ] 0022-001-002-05 - Provider-specific cost tracking
- [ ] 0022-001-002-06 - Integration testing and validation
  - **Rationale**: OpenRouter randomly switches LLMs which can cause glitches; Together.ai provides consistency
  - **Test Strategy**: 4th agent (acme/simple_chat2) uses Together.ai with different model family (e.g., Llama vs Kimi/GPT/Qwen)
  - **Regression Testing**: All unit/integration/manual tests must pass after implementation

**Note**: Simple Chat Agent is now called "InfoBot" - information sharing bot (NO web search included)

**Phase 1 MVP Complete**: Priorities 3 through 10 complete the InfoBot MVP: vector search, chat widget enhancements, profile search, profile fields, profile capture, email summaries, multi-provider support, and per-agent session isolation.

### **Priority 10: Per-Agent Cookie Configuration** 📋 **PLANNED - Ready for Implementation**
**Epic 0017-007 - Per-Agent Session Management**

**Why Priority 10**: Implement backend-controlled per-agent cookie naming to ensure proper session isolation between agent instances. Currently all agents share a single session cookie, which can cause session conflicts when users interact with multiple agents.

**Status**: Comprehensive implementation plan complete with 5 chunks, 25 automated tests, and security considerations documented.

**Dependencies**: Requires multi-tenant architecture from Epic 0022 (complete in Priority 2B).

- [ ] 0017-007-001 - Backend Session Cookie Configuration 📋
  - [ ] 0017-007-001-001 - Add cookie configuration to agent config.yaml
  - [ ] 0017-007-001-002 - Update session middleware for per-agent cookies
  - [ ] 0017-007-001-003 - Update chat widget for per-agent cookies
  - [ ] 0017-007-001-004 - Database cleanup and migration
  - [ ] 0017-007-001-005 - End-to-end testing and documentation

**Key Features**:
- Cookie name format: `<account_slug>_<agent_instance_slug>_sk`
- Example: `prepexcellence_prepexcel_info_chat1_sk`
- Complete session isolation per agent instance
- **Breaking Change**: No backwards compatibility (acceptable - no production deployments)

**Security Enhancements**:
- UUID4 session ID validation
- HttpOnly, Secure, SameSite cookie attributes
- Session expiry cleanup
- CSRF protection guidance
- Rate limiting per session

**Testing**: 25 automated tests (unit, integration, widget, E2E)

**See**: [Epic 0017-007](0017-simple-chat-agent.md#0017-007) for detailed 5-chunk implementation plan

### **Priority 11: Logging Infrastructure Consolidation** 🎯 **IN PROGRESS**
**Epic 0017-013 - Complete Migration from Loguru to Logfire**

**Problem**: Mixed logging approaches (`loguru`, `logging`, `logfire`) create inconsistency and prevent full Logfire observability utilization.

**Solution**: Complete removal of loguru and standard logging, migrate all to Logfire with hierarchical event naming (`module.submodule.action`) and console + cloud output only (no local file logging).

**Status**: Phases 1-4 complete (15/21 files migrated), Phase 5 pending (6 files)

**See**: 
- [Logging Implementation Guide](../../architecture/logging-implementation.md) - Patterns, conventions, lessons learned
- [Epic 0017-013](0017-simple-chat-agent.md#0017-013) - Detailed implementation tracking

---

**Files Impacted** (21 total):

**✅ Migrated to Logfire** (Phases 1-4 complete):

**Phase 1: Core Agent & Tools** ✅
- [x] `backend/app/agents/simple_chat.py`
- [x] `backend/app/agents/tools/vector_tools.py`
- [x] `backend/app/services/vector_service.py`
- [x] `backend/app/agents/tools/directory_tools.py`

**Phase 2: Services** ✅
- [x] `backend/app/services/message_service.py`
- [x] `backend/app/services/session_service.py`
- [x] `backend/app/services/llm_request_tracker.py`
- [x] `backend/app/services/directory_service.py`
- [x] `backend/app/services/directory_importer.py`
- [x] `backend/app/services/agent_pinecone_config.py`
- [x] `backend/app/services/pinecone_client.py`
- [x] `backend/app/services/embedding_service.py`

**Phase 3: Middleware** ✅
- [x] `backend/app/middleware/simple_session_middleware.py`
- [x] `backend/app/middleware/session_middleware.py`

**Phase 4: API Routes** ✅
- [x] `backend/app/api/account_agents.py`
- [x] `backend/app/api/agents.py`

**⏳ Pending Migration** (Phase 5):
- [ ] `backend/app/main.py` - Remove `_setup_logger()` function entirely
- [ ] `backend/app/database.py`
- [ ] `backend/app/openrouter_client.py`
- [ ] `backend/app/agents/config_loader.py`
- [ ] `backend/app/agents/instance_loader.py`
- [ ] `backend/app/agents/cascade_monitor.py`

---

**Migration Strategy**: File-by-file migration with testing between each file

**Migration Pattern**:
```python
# BEFORE (loguru)
from loguru import logger
logger.info(f"Processing request for {session_id}")
logger.warning(f"Invalid account: {account_slug}")
logger.error(f"Failed to load: {error}")
logger.exception("Exception occurred")
logger.debug(f"Query result: {result}")

# BEFORE (logging)
import logging
logger = logging.getLogger(__name__)
logger.info("Processing request")

# AFTER (logfire)
import logfire

# Info/Warning/Error/Debug preserved with hierarchical event names
logfire.info('api.account.request', session_id=str(session_id))
logfire.warn('api.account.invalid', account_slug=account_slug)
logfire.error('service.load.failed', error=str(error))
logfire.exception('service.load.exception')  # Captures full traceback
logfire.debug('service.query.result', result_count=len(result))

# Dictionary logs converted to kwargs
# BEFORE: logger.info({"event": "chat_request", "account": account_slug})
# AFTER: logfire.info('api.chat.request', account=account_slug)
```

**Hierarchical Event Naming Convention**:
- Format: `{module}.{submodule}.{action}`
- Examples: `api.account.list`, `service.session.create`, `agent.tool.vector_search`, `middleware.session.retrieve`
- Benefits: Easy filtering in Logfire UI, clear component identification

**Exception Handling**:
- Use `logfire.exception('module.error.message')` for exceptions
- Within spans: `span.record_exception(e)` for handled exceptions
- Always include context (IDs, keys) as kwargs for debugging

---

**Implementation Plan**:

**✅ Phase 1: Core Agent & Tools** (COMPLETE - 4 files)
1. [x] `backend/app/agents/simple_chat.py`
2. [x] `backend/app/agents/tools/vector_tools.py`
3. [x] `backend/app/services/vector_service.py`
4. [x] `backend/app/agents/tools/directory_tools.py`

**✅ Phase 2: Services** (COMPLETE - 8 files)
5. [x] `backend/app/services/message_service.py`
6. [x] `backend/app/services/session_service.py`
7. [x] `backend/app/services/llm_request_tracker.py`
8. [x] `backend/app/services/directory_service.py`
9. [x] `backend/app/services/directory_importer.py`
10. [x] `backend/app/services/agent_pinecone_config.py`
11. [x] `backend/app/services/pinecone_client.py`
12. [x] `backend/app/services/embedding_service.py`

**✅ Phase 3: Middleware** (COMPLETE - 2 files)
13. [x] `backend/app/middleware/simple_session_middleware.py`
14. [x] `backend/app/middleware/session_middleware.py`

**✅ Phase 4: API Routes** (COMPLETE - 2 files)
15. [x] `backend/app/api/account_agents.py`
16. [x] `backend/app/api/agents.py`

**✅ Phase 5: Infrastructure & Cleanup** (COMPLETE - 6 files)
17. [x] `backend/app/main.py` - **Removed `_setup_logger()` function + migrated 41 logger calls**
18. [x] `backend/app/database.py` - Migrated 11 logger calls
19. [x] `backend/app/openrouter_client.py` - Migrated 13 logger calls
20. [x] `backend/app/agents/config_loader.py` - Migrated 6 logger calls (inline imports)
21. [x] `backend/app/agents/instance_loader.py` - Migrated 26 logger calls
22. [x] `backend/app/agents/cascade_monitor.py` - Migrated 7 logger calls

**Phase 6: Library Integrations & Final Cleanup** (IN PROGRESS)

**Logfire Library Integrations** (best practices):
- [x] 6.1 - Add HTTPX instrumentation (P1 - Critical) ✅
  - Added `logfire.instrument_httpx()` to `backend/app/main.py` (line 238)
  - Enables automatic tracing of all OpenRouter API calls via `openrouter_client.py`
  - **Impact**: Visibility into LLM API latency, errors, retries, request/response metadata
  - **Verification**: Check Logfire for HTTP request spans during chat interactions
  
- [x] 6.2 - Move Pydantic instrumentation to main.py (P2 - Consistency) ✅
  - Moved `logfire.instrument_pydantic()` from `backend/app/agents/simple_chat.py:44` to `backend/app/main.py:238`
  - Now instrumented with FastAPI, Pydantic AI, and HTTPX in central location
  - **Impact**: Consistent instrumentation pattern, guaranteed coverage of all Pydantic models
  - **Verification**: Verify Pydantic validation spans appear for all models
  
- [x] 6.3 - Verify SQLAlchemy async instrumentation (P3 - Investigation) ✅
  - Verified current implementation in `backend/app/database.py:211-217` is working optimally
  - Current approach: Access `sync_engine` attribute from async engine (standard SQLAlchemy pattern)
  - **Status**: ✅ Working correctly - SQL queries are being traced with full SQL statements, duration, and metadata
  - **Verification**: Logfire shows SQL spans (`SELECT salient_dev`, `INSERT salient_dev`, `UPDATE salient_dev`) with:
    - Full SQL statements (`db.statement` attribute)
    - Database system (`db.system: postgresql`)
    - Database name (`db.name: salient_dev`)
    - Query duration (0.6ms - 1.8ms range)
  - **Impact**: Full SQLAlchemy tracing working - no changes needed
  - **Findings**: The `sync_engine` wrapper approach is the recommended pattern for async SQLAlchemy engines. Logfire documentation confirms this is the correct approach.
  
- [x] 6.4 - Update logging-implementation.md (P4 - Documentation) ✅
  - Documented that HTTPX requires explicit `logfire.instrument_httpx()` call (not automatic)
  - Documented Pydantic instrumentation location (main.py, not per-agent)
  - Documented SQLAlchemy async instrumentation findings (sync_engine wrapper pattern)
  - Updated "Built-in Integrations" table with actual implementation status
  - Added SQLAlchemy Async Engine Instrumentation section with code examples
  - **Impact**: Documentation now reflects actual implementation patterns and best practices

**Dependency Cleanup**:
- [x] 6.5 - Remove loguru from dependencies ✅
  - Removed `loguru==0.7.3` from `requirements.txt`
  - Updated comments in `database.py`, `main.py`, and `tools_base.py` to reference Logfire instead
  - Verified no production code imports loguru (only explore/ test files still have it)
  - **Impact**: Cleaner dependencies, no unused logging library
  
- [x] 6.6 - Remove standard logging remnants ✅
  - Verified no `import logging` statements in production code (backend/app/)
  - Verified no `logging.getLogger()` or standard logging usage
  - All files use `import logfire` only
  - **Impact**: Clean codebase with single logging solution (Logfire)
  
- [x] 6.7 - Documentation audit ✅
  - Updated `project-brief.md` - Changed "phasing out loguru" to "migration complete"
  - Updated `code-organization.md` - Updated logs/ comment and Loguru references
  - Updated `endpoints.md` - Changed "Loguru" to "Logfire"
  - Updated `coding-standards-py.md` - Changed example from `loguru` to `logfire`
  - Updated `bugs-0017.md` - Marked Loguru migration as complete
  - Verified `logging-implementation.md` already uses Logfire patterns (complete)
  - **Impact**: All active documentation now reflects Logfire as the standard

**Progress**: 21/21 files complete (100%) ✅ | Phases 1-5 complete ✅, Phase 6 pending

**Verification**: Manual testing - verify console output + Logfire dashboard after each file

**Logfire Configuration** (keep as-is):
- Current `logfire.configure()` in `main.py` is sufficient
- No service_name/version needed for single-service app
- Console output handled automatically via fallback handler
- Cloud logging enabled when `LOGFIRE_TOKEN` environment variable is set
- Recommendation: Keep current configuration, it follows Logfire best practices

---

## PHASE 2: Enhanced Functionality

Optional enhancements that extend InfoBot capabilities beyond core MVP.

### **Priority 12: Email Capture & Consent** ⚠️ **DEPRECATED**
- [ ] 0017-009-001 - Email Collection System
- [ ] 0017-009-002 - Consent and preferences management
  - **Status**: DEPRECATED - Superseded by Priority 7 (Profile Capture Tool)
  - Originally: UI-based alternative to conversational capture
  - Decision: Profile Capture Tool (Priority 7) will handle email/phone collection conversationally
  - Action: Revisit only if Profile Capture Tool doesn't cover this use case

### **Priority 13: Periodic Summarization** 📋
- [ ] 0017-010-001 - Context Window Management System
  - Token counting and threshold monitoring
  - Conversation summarization engine
  - Automatic summarization triggers

### **Priority 14: OTP Authentication** 📋
- [ ] 0017-011-001 - OTP Authentication System
  - Twilio Verify integration
  - Session upgrade and account creation
  - Cross-device session persistence

---

## PHASE 3: Multi-Agent Platform

### **Priority 15: Multi-Client Widget Foundation** ✅ **DONE**
- [x] 0003-001-001 - Shadow DOM Widget ✅
  - Implementation: `web/public/widget/chat-widget.js`
  - Demo: `web/src/pages/demo/widget.astro`
  - Status: Production ready with multi-tenant endpoints
- [x] 0003-001-002 - Preact Islands Integration ✅
  - Implementation: Epic 0022-001-004-01 (Astro/Preact components)
  - Components: `simple-chat.astro`, `widget.astro` layouts
  - Status: Production ready, multi-tenant history/chat/stream working
- [x] 0003-001-003 - HTMX UI Examples ✅
  - Implementation: `web/public/htmx-chat.html`
  - Updated with multi-tenant endpoints
  - Status: Production ready

**Status**: All components complete and production ready. Three working implementations:
1. Shadow DOM widget (universal embedding)
2. Astro/Preact components (native integration)
3. HTMX standalone page (vanilla JS + SSE)

All migrated to multi-tenant architecture with explicit `/accounts/{account}/agents/{instance}/*` endpoints.

### **Priority 16: Agent Type Plumbing** ✅ **3/4 SUPERSEDED by Epic 0022**
**Note**: Epic 0022 replaces old multi-account/multi-instance epics with unified architecture

- [x] 0005-002-001 - Agent type registration and discovery system ✅ **SUPERSEDED**
  - Replaced by: Epic 0022-001-001-04 (Instance discovery and listing)
  - Implementation: `list_account_instances()` in `instance_loader.py`
  - Endpoint: `GET /accounts/{account}/agents` returns all instances with metadata

- [x] 0005-002-002 - Configuration validation for different agent types ✅ **SUPERSEDED**
  - Replaced by: Epic 0022-001-001-03 (Instance loader validation)
  - Implementation: Hybrid DB + config file validation in `load_agent_instance()`
  - Validates account existence, instance metadata, and YAML config loading

- [x] 0005-002-003 - Routing enhancement for multiple agent types ✅ **SUPERSEDED**
  - Replaced by: Epic 0022 explicit URL structure
  - Implementation: `/accounts/{account}/agents/{instance}/{action}`
  - No complex routing needed - URL directly specifies account and instance

- [ ] 0005-002-004 - Health checks and status monitoring 📋 **STILL NEEDED**
  - Not yet implemented
  - Future enhancement for production monitoring

### **Priority 17: Sales Agent Addition** 📋
- [ ] 0008-001-001 - Sales agent foundation with business tools
- [ ] 0008-001-002 - RAG integration with business knowledge
- [ ] 0008-001-003 - Email integration (Mailgun)
- [ ] 0008-001-004 - Scheduling integration (Nylas/Calendly)
- [ ] 0008-001-005 - Profile data collection and lead qualification

### **Priority 18: React and Vue Chat Widgets** 📋
- [ ] 0003-002-001 - React Widget Component with TypeScript
- [ ] 0003-002-002 - Vue 3 Widget Component with Composition API
- [ ] 0003-002-003 - NPM Package Distribution (@salient/widget-react, @salient/widget-vue)

### **Priority 19: Advanced Widget Features** 📋
- [ ] 0003-003-001 - Iframe Adapter for security isolation
- [ ] 0003-003-002 - API-Only Mode for mobile integration
- [ ] 0003-003-003 - Advanced Theming with CSS variables
- [ ] 0003-003-004 - Widget Analytics and performance monitoring

**Current Status**: Priority 3 complete ✅ - Data model cleanup and cost attribution finished

**Progress Summary:**
- ✅ **Priority 2B - Epic 0022 (Multi-Tenant Architecture)**: COMPLETE
  - Production-ready multi-tenant infrastructure
  - Working endpoints, widget integration, cost tracking
  - All critical bugs fixed (CORS, sessions, markdown, SSE)
  
- ✅ **Priority 3 - Data Model Cleanup**: COMPLETE (4/4 complete) ✅ **2025-10-20**
  - ✅ 0022-001-005-01: Populate denormalized fields in llm_requests (BUG-0017-005) ✅ **DONE**
    - Database verified: 100% field population, 0 NULL values, fast billing queries working
  - ✅ 0022-001-005-02: Link llm_requests to messages (1:many FK) ✅ **DONE**
    - Migration created, models updated, 1:many FK established, agent integration complete
  - ✅ BUG-0017-006: Pinecone multi-project API key support ✅ **DONE** (config + lazy singleton initialization)
  - ✅ 0022-001-005-03: Add agent_instance_slug to sessions table (fast analytics) ✅ **DONE**
    - Migration created, models updated, manual testing confirmed all agents populate correctly
  - ✅ 0017-005-003: Multi-Agent Data Integrity Verification Script ✅ **DONE**
    - Comprehensive test script with 3 output formats, cleanup script, all 5 agents verified
  
- ✅ **Priority 4 - Vector Search Tool & Chat Widget**: COMPLETE
  - ✅ Multi-Client Demo Site Architecture (3/3 chunks complete)
  - ✅ Vector Search Tool Implementation (3/3 chunks complete)
  - ✅ Bug Fixes (4/6 complete) - See [bugs-0017.md](bugs-0017.md)
    - ✅ BUG-0017-001: Zero chunks streaming - FIXED 2025-10-15
    - ✅ BUG-0017-002: Missing model pricing - FIXED 2025-10-15
    - ✅ BUG-0017-003: Vapid sessions with NULL IDs - FIXED 2025-10-18
    - ✅ BUG-0017-005: Missing denormalized fields - FIXED 2025-10-18
    - ⏸️ BUG-0017-004: Duplicate user messages on retry - WON'T FIX
    - 📋 BUG-0017-007: Legacy non-multi-tenant endpoints still active - PLANNED (P2)
  - ✅ 0003-010: Chat Widget Maximize/Minimize Toggle - COMPLETE (2025-10-28)

**Previous Milestone (Priority 2B - Epic 0022):** ✅ COMPLETE
- Production-ready multi-tenant architecture with Pydantic AI agents
- Working endpoints, widget integration, cost tracking, and observability
- All critical bugs fixed (CORS, sessions, markdown, SSE, cost tracking)

**Next Steps (Phase 1 MVP):**
1. ✅ **Priority 3: Data Model Cleanup & Cost Attribution** - COMPLETE (4/4 complete) ✅ **2025-10-20**
   - ✅ 0022-001-005-01: Denormalized fields in llm_requests (BUG-0017-005) - DONE
   - ✅ 0022-001-005-02: Link llm_requests to messages (1:many FK) - DONE
   - ✅ BUG-0017-006: Pinecone multi-project API key support - DONE (config + lazy singleton)
   - ✅ 0022-001-005-03: Add agent_instance_slug to sessions table (fast analytics) - DONE
   - ✅ 0017-005-003: Multi-Agent Data Integrity Verification Script - DONE
2. ✅ **Priority 4: Vector Search Tool & Chat Widget** - COMPLETE ✅ **2025-10-28**
   - ✅ Multi-client demo site architecture (complete)
   - ✅ Vector search tool implementation with Pydantic AI (complete)
   - ✅ Bug fixes (4/6 fixed, 1 won't fix, 1 planned for cleanup)
   - ✅ Chat widget maximize/minimize (Epic 0003-010) - COMPLETE
3. 📋 **Priority 5: Epic 0023 (Directory Search Tool)** - Generic directory search for natural language queries 🎯 **NEXT**
4. 📋 Priority 6: 0017-006 (Profile Fields Config & JSONB Migration)
5. 📋 Priority 7: 0017-012 (Profile Capture Tool)
6. 📋 Priority 8: 0017-008 (Email Summary with Mailgun)
7. 📋 Priority 9: Multi-Provider Infrastructure - Together.ai integration for LLM consistency
8. 📋 Priority 10: 0017-007 (Per-Agent Cookie Configuration) - Session isolation per agent instance
9. 📋 Priority 11: 0017-013 (Logfire Migration) - Consolidate all logging to Logfire for consistent observability
