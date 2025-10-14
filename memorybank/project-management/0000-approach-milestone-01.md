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
  - [ ] 0022-001-005 - Cost Tracking & Observability ⏸️ **DEFERRED**
    - [ ] 0022-001-005-01 - LLM request tracker updates (denormalized columns for fast billing queries)
    - [ ] 0022-001-005-02 - Link LLM requests to messages (1:many FK for cost attribution and debugging)
  - [ ] 0022-001-006 - Testing & Validation ⏸️ **DEFERRED**
  - [ ] 0022-001-007 - Simple Admin UI (Optional) ⏸️ **DEFERRED**
- [ ] 0022-002 - Authentication & Authorization ⏸️ **DEFERRED**

### **Priority 3: Vector Search Tool** 📋
**Epic 0017-005 - Vector Search Tool with Multi-Client Demo Architecture**

**Why Priority 3**: Demonstrates vector search capabilities through realistic client demo sites with proper multi-tenant account separation. Showcases Epic 0022's multi-tenant architecture in a sales-ready format.

- [ ] 0017-005-001 - Multi-Client Demo Site Architecture
  - Separate accounts per client (agrofresh, wyckoff, default_account)
  - Move existing pages to `/agrofresh/`, create `/wyckoff/` pages, keep `/demo/` unchanged
  - Client-specific layouts, components, footers with widget configuration
  - 8 Wyckoff Hospital pages showcasing doctor profile search

- [ ] 0017-005-002 - Vector Search Tool Implementation
  - Core InfoBot functionality - answers questions using knowledge base via @agent.tool

### **Priority 4: Profile Fields Configuration & Database Schema** 📋
- [ ] 0017-006-001 - Profile Fields YAML Configuration
- [ ] 0017-006-002 - Migrate Profiles Table to JSONB

### **Priority 5: Profile Capture Tool** 📋
- [ ] 0017-007-001 - Profile Capture Agent Tool
  - Conversational capture of email/phone using @agent.tool

### **Priority 6: Email Summary Tool with Mailgun** 📋
- [ ] 0017-008-001 - Mailgun Integration
- [ ] 0017-008-002 - Email Summary Agent Tool
  - Completes user workflow: chat → capture → email summary

### **Priority 6A: Multi-Provider Infrastructure** 📋
- [ ] 0022-001-002-01 - Provider factory and base infrastructure
- [ ] 0022-001-002-02 - Config schema and validation
- [ ] 0022-001-002-03 - Update simple_chat agent to use factory
- [ ] 0022-001-002-04 - Update test instance configs (4th agent: acme/simple_chat2 with Together.ai + different model family)
- [ ] 0022-001-002-05 - Provider-specific cost tracking
- [ ] 0022-001-002-06 - Integration testing and validation
  - **Rationale**: OpenRouter randomly switches LLMs which can cause glitches; Together.ai provides consistency
  - **Test Strategy**: 4th agent (acme/simple_chat2) uses Together.ai with different model family (e.g., Llama vs Kimi/GPT/Qwen)
  - **Regression Testing**: All unit/integration/manual tests must pass after implementation

### **Priority 7: Profile Search Tool** 📋 🎯 **DEMO FEATURE**
**Epic 0023 - Generic Profile Search for LLM Agents**

**Why Priority 7**: Enables agents to search professional profiles (doctors, nurses, sales reps, consultants) via natural language queries. Demonstrates real-world tool usage with structured data. Positioned after email tool to complete core workflow tools first.

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

**Note**: Simple Chat Agent is now called "InfoBot" - information sharing bot (NO web search included)

**Phase 1 MVP Complete**: Priorities 3 through 7 complete the InfoBot MVP: vector search, profile capture, email summaries, multi-provider support, and profile search.

---

## PHASE 2: Enhanced Functionality

Optional enhancements that extend InfoBot capabilities beyond core MVP.

### **Priority 8: Email Capture & Consent** ⚠️ **DEPRECATED**
- [ ] 0017-009-001 - Email Collection System
- [ ] 0017-009-002 - Consent and preferences management
  - **Status**: DEPRECATED - Superseded by Priority 5 (Profile Capture Tool)
  - Originally: UI-based alternative to conversational capture
  - Decision: Profile Capture Tool (Priority 5) will handle email/phone collection conversationally
  - Action: Revisit only if Profile Capture Tool doesn't cover this use case

### **Priority 9: Periodic Summarization** 📋
- [ ] 0017-010-001 - Context Window Management System
  - Token counting and threshold monitoring
  - Conversation summarization engine
  - Automatic summarization triggers

### **Priority 10: OTP Authentication** 📋
- [ ] 0017-011-001 - OTP Authentication System
  - Twilio Verify integration
  - Session upgrade and account creation
  - Cross-device session persistence

---

## PHASE 3: Multi-Agent Platform

### **Priority 11: Multi-Client Widget Foundation** ✅ **DONE**
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

### **Priority 12: Agent Type Plumbing** ✅ **3/4 SUPERSEDED by Epic 0022**
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

### **Priority 13: Sales Agent Addition** 📋
- [ ] 0008-001-001 - Sales agent foundation with business tools
- [ ] 0008-001-002 - RAG integration with business knowledge
- [ ] 0008-001-003 - Email integration (Mailgun)
- [ ] 0008-001-004 - Scheduling integration (Nylas/Calendly)
- [ ] 0008-001-005 - Profile data collection and lead qualification

### **Priority 14: React and Vue Chat Widgets** 📋
- [ ] 0003-002-001 - React Widget Component with TypeScript
- [ ] 0003-002-002 - Vue 3 Widget Component with Composition API
- [ ] 0003-002-003 - NPM Package Distribution (@salient/widget-react, @salient/widget-vue)

### **Priority 15: Advanced Widget Features** 📋
- [ ] 0003-003-001 - Iframe Adapter for security isolation
- [ ] 0003-003-002 - API-Only Mode for mobile integration
- [ ] 0003-003-003 - Advanced Theming with CSS variables
- [ ] 0003-003-004 - Widget Analytics and performance monitoring

**Current Status**: Priority 2B complete ✅ - Multi-tenant architecture production ready, moving to Priority 3 (Vector Search Tool)

**Progress Summary (Priority 2B - Epic 0022):**
- ✅ Database & Configuration Infrastructure (4/4 chunks complete)
- ✅ Multi-Provider Infrastructure (Logfire complete, verified working; multi-provider deferred to Priority 6A)
- ✅ API Endpoints (5/5 chunks complete) - All endpoints fully functional (non-streaming chat, streaming chat, instance listing)
- ✅ Frontend Widget Migration (1/1 production chunk complete) - Core Astro/Preact components PRODUCTION READY
  - ✅ Multi-tenant endpoints working (chat, stream, history)
  - ✅ All critical bugs fixed (CORS, sessions, markdown, SSE, cost tracking)
  - ✅ Debug logging infrastructure added
  - ⏸️ iframe embedding and showcase demo deferred (educational features, not blocking MVP)
- ⏸️ Cost Tracking & Observability deferred (optimization features, core tracking already functional)
- ⏸️ Testing & Validation deferred (core functionality tested, comprehensive suite deferred)
- ⏸️ Simple Admin UI deferred (optional feature)

**Next Steps (Phase 1 MVP):**
1. ✅ **Priority 2B: Epic 0022 (Multi-Tenant Architecture)** - COMPLETE
   - Production-ready multi-tenant infrastructure with Pydantic AI agents
   - Working endpoints, widget integration, cost tracking, and observability
2. **Priority 3: 0017-005 (Vector Search Tool)** 🎯 **NEXT** - Core InfoBot value
   - Multi-client demo site architecture with separate accounts
   - Vector search tool implementation with Pydantic AI
3. Priority 4: 0017-006 (Profile Fields Config & JSONB Migration)
4. Priority 5: 0017-007 (Profile Capture Tool)
5. Priority 6: 0017-008 (Email Summary with Mailgun)
6. **Priority 6A: Multi-Provider Infrastructure** - Together.ai integration for LLM consistency
7. **Priority 7: Epic 0023 (Profile Search Tool)** - Generic profile search for natural language queries
