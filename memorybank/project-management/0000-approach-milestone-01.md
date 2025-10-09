# Tactical Development Approach - Streamlined
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

### **Priority 2B: Multi-Tenant Account-Instance Architecture** 🚧 🎯 **IN PROGRESS**
**Epic 0022 - Foundational Infrastructure for Pydantic AI Migration**

**Why Priority 2B**: All endpoints must use Pydantic AI (core architecture principle). Current legacy endpoints use direct OpenRouter calls. Epic 0022 provides the multi-tenant infrastructure to properly migrate ALL endpoints to Pydantic AI without breaking existing functionality.

- [ ] 0022-001 - Phase 1a: Core Multi-Tenancy Infrastructure
  - [x] 0022-001-001 - Database & Configuration Infrastructure ✅
    - [x] 0022-001-001-01 - Test instance configuration files ✅
    - [x] 0022-001-001-02 - Multi-tenant database schema migration ✅
    - [x] 0022-001-001-03 - Agent instance loader implementation ✅
    - [x] 0022-001-001-04 - Instance discovery and listing ✅
  - [x] 0022-001-002 - Multi-Provider Infrastructure (Logfire complete, rest optional) ✅
    - [x] 0022-001-002-00 - Logfire observability integration ✅
    - Chunks 01-06 (Provider factory, Together.ai) - DEFERRED (optional, not required)
  - [ ] 0022-001-003 - API Endpoints (3/4 complete) 🚧
    - [x] 0022-001-003-01 - Account agents router setup ✅
    - [x] 0022-001-003-01a - Session context migration (nullable fields) ✅
    - [x] 0022-001-003-02 - Non-streaming chat endpoint ✅
    - [ ] 0022-001-003-03 - Streaming chat endpoint 🎯 **NEXT**
    - [ ] 0022-001-003-04 - Instance listing endpoint
  - [ ] 0022-001-004 - Frontend Widget Migration (Astro/Preact components, embedded widgets, demo pages)
  - [ ] 0022-001-005 - Cost Tracking & Observability
  - [ ] 0022-001-006 - Testing & Validation
  - [ ] 0022-001-007 - Simple Admin UI (Optional)
- [ ] 0022-002 - Phase 1b: Authentication & Authorization (Deferred - when needed)

### **Priority 3: Vector Search Tool** 📋
- [ ] 0017-005-001 - Vector Search Tool Implementation
  - Core InfoBot functionality - answers questions using knowledge base

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

**Note**: Simple Chat Agent is now called "InfoBot" - information sharing bot (NO web search included)

**Phase 1 MVP Complete**: Priorities 3 through 6 complete the InfoBot MVP: vector search, profile capture, and email summaries.

---

## PHASE 2: Enhanced Functionality

Optional enhancements that extend InfoBot capabilities beyond core MVP.

### **Priority 7: Email Capture & Consent (Optional)** 📋
- [ ] 0017-009-001 - Email Collection System
- [ ] 0017-009-002 - Consent and preferences management
  - UI-based alternative to conversational capture
  - May be superseded by Profile Capture Tool - review during implementation

### **Priority 8: Periodic Summarization** 📋
- [ ] 0017-010-001 - Context Window Management System
  - Token counting and threshold monitoring
  - Conversation summarization engine
  - Automatic summarization triggers

### **Priority 9: OTP Authentication** 📋
- [ ] 0017-011-001 - OTP Authentication System
  - Twilio Verify integration
  - Session upgrade and account creation
  - Cross-device session persistence

---

## PHASE 3: Multi-Agent Platform

### **Priority 10: Multi-Client Widget Foundation** 📋
- [ ] 0003-001-001 - Shadow DOM Widget
- [ ] 0003-001-002 - Preact Islands Integration  
- [ ] 0003-001-003 - HTMX UI Examples

### **Priority 11: Agent Type Plumbing** 📋
**Note**: Epic 0022 replaces old multi-account/multi-instance epics with unified architecture
- [ ] 0005-002-001 - Agent type registration and discovery system
- [ ] 0005-002-002 - Configuration validation for different agent types
- [ ] 0005-002-003 - Routing enhancement for multiple agent types
- [ ] 0005-002-004 - Health checks and status monitoring

### **Priority 12: Sales Agent Addition** 📋
- [ ] 0008-001-001 - Sales agent foundation with business tools
- [ ] 0008-001-002 - RAG integration with business knowledge
- [ ] 0008-001-003 - Email integration (Mailgun)
- [ ] 0008-001-004 - Scheduling integration (Nylas/Calendly)
- [ ] 0008-001-005 - Profile data collection and lead qualification

### **Priority 13: React and Vue Chat Widgets** 📋
- [ ] 0003-002-001 - React Widget Component with TypeScript
- [ ] 0003-002-002 - Vue 3 Widget Component with Composition API
- [ ] 0003-002-003 - NPM Package Distribution (@salient/widget-react, @salient/widget-vue)

### **Priority 14: Advanced Widget Features** 📋
- [ ] 0003-003-001 - Iframe Adapter for security isolation
- [ ] 0003-003-002 - API-Only Mode for mobile integration
- [ ] 0003-003-003 - Advanced Theming with CSS variables
- [ ] 0003-003-004 - Widget Analytics and performance monitoring

**Current Status**: Priority 2B in progress 🚧 - Multi-tenant chat endpoint complete ✅, Logfire verified ✅

**Progress Summary (Priority 2B - Epic 0022):**
- ✅ Database & Configuration Infrastructure (4/4 chunks)
- ✅ Multi-Provider Infrastructure (Logfire complete, verified working)
- 🚧 API Endpoints (3/4 chunks) - Non-streaming chat endpoint fully functional
- 📋 Frontend Widget Migration (not started)
- 📋 Testing & Validation (not started)

**Next Steps (Phase 1 MVP):**
1. **Priority 2B: Epic 0022 (Multi-Tenant Architecture)** 🎯 - IN PROGRESS
   - Complete remaining API endpoints (streaming + listing)
   - Frontend widget migration
   - Integration testing
2. **Priority 3: 0017-005 (Vector Search Tool)** - Core InfoBot value
3. Priority 4: 0017-006 (Profile Fields Config & JSONB Migration)
4. Priority 5: 0017-007 (Profile Capture Tool)
5. Priority 6: 0017-008 (Email Summary with Mailgun)
