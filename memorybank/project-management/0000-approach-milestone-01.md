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
    - [ ] 0022-001-005-02 - Link LLM requests to messages (1:many FK for cost attribution and debugging) → Now Priority 3
  - [ ] 0022-001-006 - Testing & Validation ⏸️ **DEFERRED**
  - [ ] 0022-001-007 - Simple Admin UI (Optional) ⏸️ **DEFERRED**
- [ ] 0022-002 - Authentication & Authorization ⏸️ **DEFERRED**

### **Priority 3: Data Model Cleanup & Cost Attribution** 🚧 **IN PROGRESS** (2/4 complete)
**Doing this to enable accurate billing and debugging**

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

- [ ] 0022-001-005-03 - Add agent_instance_slug to sessions table (fast analytics)
  - Add denormalized `agent_instance_slug` (TEXT, nullable, indexed) to sessions table
  - Enables fast session analytics without JOINs to agent_instances table
  - Follows same denormalization pattern as llm_requests table
  - See: [Epic 0022-001-005-03](0022-multi-tenant-architecture.md#0022-001-005-03) for detailed implementation plan

- [ ] 0017-005-003 - Multi-Agent Data Integrity Verification Script
  - Create comprehensive manual test script: `backend/tests/manual/test_data_integrity.py`
  - **Purpose**: Verify all database tables are populated correctly after Priority 3 changes
  - **Scope**: Test all agent instances (5 agents across 3 accounts: agrofresh, wyckoff, default_account, acme)
  - **Verification**: For each agent, send test chat request and verify:
    - Sessions table: account_id, agent_instance_id, agent_instance_slug populated
    - Messages table: session_id, llm_request_id FK populated, role/content correct
    - LLM_requests table: account_id, account_slug, agent_instance_slug, agent_type, completion_status populated
    - Costs tracked: prompt_cost, completion_cost, total_cost non-zero
  - **Configuration**: YAML config file specifying test prompts per agent (e.g., "What products do you offer?" for AgroFresh)
  - **Implementation Options** (3 approaches to consider):
    1. **Sequential Database Queries** (Recommended for MVP):
       - Direct SQLAlchemy queries after each HTTP request
       - Simple, debuggable, no external dependencies
       - Prints summary table with pass/fail per agent
       - Pros: Fast to implement, easy to understand
       - Cons: Slower execution (sequential), requires running server
    2. **LLM-Assisted Verification** (Intelligent validation):
       - Uses LLM to generate test prompts and verify response quality
       - Validates data relationships are semantically correct
       - Can catch logical errors (e.g., Wyckoff agent answering AgroFresh questions)
       - Pros: Smart validation, catches semantic issues
       - Cons: Costs money, slower, adds complexity
    3. **Pytest Parametrized Suite** (Production-ready):
       - Uses `@pytest.mark.parametrize` to test all agents
       - Parallel execution with `pytest-xdist`
       - Proper fixtures, setup/teardown, CI/CD integration
       - Pros: Professional, parallel, reusable in CI pipeline
       - Cons: More complex, pytest overhead, harder to read output
  - **Recommendation**: Start with Option 1 (Sequential), evolve to Option 3 (Pytest) for CI/CD
  - **Output**: Summary table showing pass/fail for each agent + data integrity checks
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

- [ ] 0003-010 - Chat Widget Maximize/Minimize Toggle 🎯 **NEXT**
  - Add maximize/minimize functionality to Shadow DOM chat widget
  - Two states: minimized (default) and maximized (fills ~90% of viewport)
  - Maximized positioning: 25px from top, 50px from left, preserves bottom-right anchor
  - Features: Toggle button, smooth CSS transitions (~300ms), localStorage persistence, keyboard shortcuts (Alt+M)
  - Accessibility: ARIA labels, focus management, ESC key handling (minimize → close)
  - Mobile: Full-screen overlay for screens <768px
  - Implementation: Update `web/public/widget/chat-widget.js`
  - Configuration: Add `defaultMaximized` and `enableMaximize` options
  - See: [Epic 0003-010](0003-website-htmx-chatbot.md#0003-010) for detailed 8-task breakdown (Toggle Button, Layout, Sizing, Transitions, State Persistence, Accessibility, Cross-Framework, Testing)

### **Priority 5: Profile Search Tool** 📋 🎯 **DEMO FEATURE**
**Epic 0023 - Generic Profile Search for LLM Agents**

**Why Priority 5**: Enables agents to search professional profiles (doctors, nurses, sales reps, consultants) via natural language queries. Demonstrates real-world tool usage with structured data. Complements vector search (Priority 4) by adding structured profile queries.

**Dependencies**: Requires `accounts` and `agent_instances` tables from Epic 0022 (already complete in Priority 2B).

- [ ] 0023-001 - Core Profile Infrastructure
  - [ ] 0023-001-001 - Database Schema Design & Migration (profile_lists, profiles, agent_profile_lists with UUIDs)
  - [ ] 0023-001-002 - CSV Import & Data Seeding (doctors_profile.csv → PostgreSQL)
  - [ ] 0023-001-003 - Profile Service (CRUD Operations with SQLAlchemy)
- [ ] 0023-002 - Profile Search Tool (Pydantic AI)
  - [ ] 0023-002-001 - Pydantic AI Tool Implementation (@agent.tool decorator with agent-level access control)
  - [ ] 0023-002-002 - Tool Integration & Testing (manual + automated tests)
- [ ] 0023-003 - Semantic Search Enhancement (Pinecone) - DEFERRED to post-demo

**Architecture Highlights**:
- Multi-list support per account (e.g., doctors, nurses, sales_east, sales_west)
- Agent-level access control (agents can access one or more profile lists)
- Hybrid schema: Core columns + JSONB for type-specific fields
- PostgreSQL structured queries (Phase 1), Pinecone semantic search (Phase 2 - deferred)

**Initial Use Case**: Hospital doctor profiles (320 records)
**Demo Query**: "Find me a Spanish-speaking cardiologist"

### **Priority 6: Profile Fields Configuration & Database Schema** 📋
- [ ] 0017-006-001 - Profile Fields YAML Configuration
- [ ] 0017-006-002 - Migrate Profiles Table to JSONB

### **Priority 7: Profile Capture Tool** 📋
- [ ] 0017-007-001 - Profile Capture Agent Tool
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

**Phase 1 MVP Complete**: Priorities 3 through 9 complete the InfoBot MVP: vector search, chat widget enhancements, profile search, profile fields, profile capture, email summaries, and multi-provider support.

---

## PHASE 2: Enhanced Functionality

Optional enhancements that extend InfoBot capabilities beyond core MVP.

### **Priority 10: Email Capture & Consent** ⚠️ **DEPRECATED**
- [ ] 0017-009-001 - Email Collection System
- [ ] 0017-009-002 - Consent and preferences management
  - **Status**: DEPRECATED - Superseded by Priority 7 (Profile Capture Tool)
  - Originally: UI-based alternative to conversational capture
  - Decision: Profile Capture Tool (Priority 7) will handle email/phone collection conversationally
  - Action: Revisit only if Profile Capture Tool doesn't cover this use case

### **Priority 11: Periodic Summarization** 📋
- [ ] 0017-010-001 - Context Window Management System
  - Token counting and threshold monitoring
  - Conversation summarization engine
  - Automatic summarization triggers

### **Priority 12: OTP Authentication** 📋
- [ ] 0017-011-001 - OTP Authentication System
  - Twilio Verify integration
  - Session upgrade and account creation
  - Cross-device session persistence

---

## PHASE 3: Multi-Agent Platform

### **Priority 13: Multi-Client Widget Foundation** ✅ **DONE**
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

### **Priority 14: Agent Type Plumbing** ✅ **3/4 SUPERSEDED by Epic 0022**
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

### **Priority 15: Sales Agent Addition** 📋
- [ ] 0008-001-001 - Sales agent foundation with business tools
- [ ] 0008-001-002 - RAG integration with business knowledge
- [ ] 0008-001-003 - Email integration (Mailgun)
- [ ] 0008-001-004 - Scheduling integration (Nylas/Calendly)
- [ ] 0008-001-005 - Profile data collection and lead qualification

### **Priority 16: React and Vue Chat Widgets** 📋
- [ ] 0003-002-001 - React Widget Component with TypeScript
- [ ] 0003-002-002 - Vue 3 Widget Component with Composition API
- [ ] 0003-002-003 - NPM Package Distribution (@salient/widget-react, @salient/widget-vue)

### **Priority 17: Advanced Widget Features** 📋
- [ ] 0003-003-001 - Iframe Adapter for security isolation
- [ ] 0003-003-002 - API-Only Mode for mobile integration
- [ ] 0003-003-003 - Advanced Theming with CSS variables
- [ ] 0003-003-004 - Widget Analytics and performance monitoring

**Current Status**: Priority 3 in progress 🎯 - Data model cleanup and cost attribution

**Progress Summary:**
- ✅ **Priority 2B - Epic 0022 (Multi-Tenant Architecture)**: COMPLETE
  - Production-ready multi-tenant infrastructure
  - Working endpoints, widget integration, cost tracking
  - All critical bugs fixed (CORS, sessions, markdown, SSE)
  
- 🚧 **Priority 3 - Data Model Cleanup**: IN PROGRESS (3/5 complete)
  - ✅ 0022-001-005-01: Populate denormalized fields in llm_requests (BUG-0017-005) ✅ **DONE**
    - Database verified: 100% field population, 0 NULL values, fast billing queries working
  - ✅ 0022-001-005-02: Link llm_requests to messages (1:many FK) ✅ **DONE**
    - Migration created, models updated, 1:many FK established, agent integration complete
  - ✅ BUG-0017-006: Pinecone multi-project API key support ✅ **DONE** (config + lazy singleton initialization)
  - 📋 0022-001-005-03: Add agent_instance_slug to sessions table (fast analytics) - **NEXT**
  - 📋 0017-005-003: Multi-Agent Data Integrity Verification Script - remaining
  
- 🚧 **Priority 4 - Vector Search Tool & Chat Widget**: IN PROGRESS
  - ✅ Multi-Client Demo Site Architecture (3/3 chunks complete)
  - ✅ Vector Search Tool Implementation (3/3 chunks complete)
  - ✅ Bug Fixes (4/5 complete) - See [bugs-0017.md](bugs-0017.md)
    - ✅ BUG-0017-001: Zero chunks streaming - FIXED 2025-10-15
    - ✅ BUG-0017-002: Missing model pricing - FIXED 2025-10-15
    - ✅ BUG-0017-003: Vapid sessions with NULL IDs - FIXED 2025-10-18
    - ✅ BUG-0017-005: Missing denormalized fields - FIXED 2025-10-18
    - ⏸️ BUG-0017-004: Duplicate user messages on retry - WON'T FIX
  - 📋 0003-010: Chat Widget Maximize/Minimize Toggle - NEXT

**Previous Milestone (Priority 2B - Epic 0022):** ✅ COMPLETE
- Production-ready multi-tenant architecture with Pydantic AI agents
- Working endpoints, widget integration, cost tracking, and observability
- All critical bugs fixed (CORS, sessions, markdown, SSE, cost tracking)

**Next Steps (Phase 1 MVP):**
1. 🚧 **Priority 3: Data Model Cleanup & Cost Attribution** - IN PROGRESS (3/5 complete)
   - ✅ 0022-001-005-01: Denormalized fields in llm_requests (BUG-0017-005) - DONE
   - ✅ 0022-001-005-02: Link llm_requests to messages (1:many FK) - DONE
   - ✅ BUG-0017-006: Pinecone multi-project API key support - DONE (config + lazy singleton)
   - 📋 0022-001-005-03: Add agent_instance_slug to sessions table (fast analytics) - **NEXT**
   - 📋 0017-005-003: Multi-Agent Data Integrity Verification Script
2. 📋 **Priority 4: 0017-005 (Vector Search Tool)** - After Priority 3
   - ✅ Multi-client demo site architecture (complete)
   - ✅ Vector search tool implementation with Pydantic AI (complete)
   - ✅ Bug fixes (4/5 fixed, 1 won't fix)
   - 📋 Chat widget maximize/minimize (Epic 0003-010) - NEXT after Priority 3
3. **Priority 5: Epic 0023 (Profile Search Tool)** - Generic profile search for natural language queries
4. Priority 6: 0017-006 (Profile Fields Config & JSONB Migration)
5. Priority 7: 0017-007 (Profile Capture Tool)
6. Priority 8: 0017-008 (Email Summary with Mailgun)
7. **Priority 9: Multi-Provider Infrastructure** - Together.ai integration for LLM consistency
