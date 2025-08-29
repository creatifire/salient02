# Tactical Development Approach
> Strategic recommendations for prioritizing and executing remaining work across Epics 0003 and 0004

## Executive Summary

Based on comprehensive analysis of remaining work in Epic 0003 (Website & HTMX Chatbot) and Epic 0004 (Chat Memory & Persistence), this document provides tactical recommendations for development prioritization and execution strategy.

**Current State**: ~45% project completion with Epic 0004 foundational work completed (session management, database setup, message persistence)
**Critical Path**: Fix frontend inconsistencies → Complete conversation hierarchy → Expand widget ecosystem

## Milestone 1 Implementation Plan

### Decisions (confirmed)
- Agent configs live in YAML under `backend/config/agent_configs/` for Phase 1-2; will move into DB in Phase 3.
- Vector DB: Pinecone-first for RAG; reassess `pgvector` as a budget option in Milestone 2.
- First CRM integration: Zoho.
- Per-agent thresholds/models are configurable in YAML (e.g., `model_settings`, `memory.auto_summary_threshold`).
- Widget scope: keep existing Shadow DOM widget; defer Preact/React widgets until the end of Milestone 1.
- Deployment target: Backend on Render, frontend on a CDN (Cloudflare/Netlify/Vercel) with cross-origin session + CORS support (see production cross-origin plan).

### Pinecone sharding plan (Phase 1-2 note)
- We will shard a single organization’s Pinecone project across clients using namespaces on a shared index for Standard and Professional plans. Storage quotas differ by tier; isolation is enforced by namespace.
- For Enterprise, we will provision a dedicated Pinecone instance/indexes per account.
- Open question (to decide during Phase 2): whether to segment multiple shared indexes by cohort versus a single shared index per environment.


## Milestone 1: Sales Agent with RAG & CRM Integration

**Objective**: Deliver a working sales agent with one CRM integration, website content knowledge, and full chat memory functionality.

### **Phase 1: Complete Simple Chat Agent (Single Instance)**
*Deliver a fully functional simple chat agent with multi-tool capabilities using config file-based setup*

Priority order (Phase 1)
1. 0005-001: Pydantic AI framework setup (install, base module, DI)
2. 0017-001: Simple Chat Agent foundation + 0017-004: agent YAML (`simple_chat.yaml`)
3. 0017-005: FastAPI integration & streaming for agent endpoints
4. 0011: Vector DB (Pinecone) minimal integration + 0010: website content pipeline
5. 0017-002: Core tools (vector search, conversation management)
6. 0017-003: External tools (web search, CrossFeed MCP)
7. 0004-005: LLM request tracking (cost/usage)

#### **API Endpoints (Phase 1)**
**Active Endpoints:**
```
# Legacy (Continue Working)
POST /chat                           # Existing chat functionality
GET /events/stream                   # Existing SSE streaming
GET /                               # Main chat page

# New Agent Endpoints (Phase 1)
POST /agents/simple-chat/chat        # Simple chat agent
GET /agents/simple-chat/stream       # Agent-specific SSE
```

**Strategy:**
- **Parallel Development**: Both legacy and agent endpoints active simultaneously
- **Zero Disruption**: Existing `/chat` continues working unchanged during development
- **Session Compatibility**: Shared session management and chat history between endpoints
- **Testing**: Demo pages gradually migrate to `/agents/simple-chat/chat` for validation
- **Detailed Plan**: See [agent-endpoint-transition.md](../design/agent-endpoint-transition.md)

#### **Infrastructure (Completed)**
- ✅ **0004-004-002-05** (Frontend chat history loading) **COMPLETED**
- ✅ **0004-004-002-06/07/08** (Markdown formatting consistency) **COMPLETED** - 06✅, 07✅, 08✅ affects all 5 integration strategies
- ✅ **0004-004-002-10** (Chat Widget History Loading) **COMPLETED** - widget conversation continuity
- ✅ **0004-004-003** (Enhanced Session Information Display) **COMPLETED** - operational visibility
- ✅ **0004-001** (Development Environment & Database Setup) **COMPLETED**
- ✅ **0004-002** (Database Setup & Migrations) **COMPLETED**
- ✅ **0004-003** (Session Management & Resumption) **COMPLETED**
- ✅ **0004-004** (Message Persistence & Chat History) **COMPLETED**

#### **Pydantic AI Framework (Single Account)**
- ❌ **0005-001** (Pydantic AI Framework Setup) **READY TO START** - *Core framework, simplified for single account*
- ❌ **0004-012** (Conversation Hierarchy & Management) **NOT STARTED** - *Agent conversation memory*
- ❌ **0004-013** (Agent Context Management) **NOT STARTED** - *Agent memory and context integration*

#### **Vector Database Infrastructure**
- ❌ **0011** (Vector Database Integration - Pinecone) **NOT STARTED** - *Foundational RAG infrastructure for simple chat agent*

#### **Complete Simple Chat Agent (Epic 0017)**
- ❌ **0017-001** (Simple Chat Agent Foundation) **READY TO START** - *Basic Pydantic AI agent with dependency injection*
- ❌ **0017-002** (Core Agent Tools) **NOT STARTED** - *Vector search and conversation management tools*
- ❌ **0017-003** (External Integration Tools) **NOT STARTED** - *Web search and CrossFeed MCP integration*
- ❌ **0017-004** (Agent Configuration) **NOT STARTED** - *Config file-based agent setup (no database)*
- ❌ **0017-005** (FastAPI Integration & Streaming) **NOT STARTED** - *SSE streaming and performance optimization*
- ❌ **0004-005** (LLM Request Tracking) **NOT STARTED** - *Cost monitoring for agent operations*

### **Phase 2: Complete Sales Agent (Two Agent Types)**
*Specialized sales agent with RAG and business tools; see priority list above for ordering.*

Priority order (Phase 2)
1. 0008-001: Sales Agent framework (built on Simple Chat base)
2. 0004-006: Profile data collection (fields + capture flows)
3. 0010: Website content ingestion (if not fully completed in Phase 1)
4. 0008-002: Sales intelligence (RAG, retrieval policies)
5. 0012: Outbound email integration (Mailgun)
6. 0013: Scheduling integration (Nylas/Calendly)
7. 0008-003: Business tools & UX integration
8. 0008-004: Optimization & tuning

### **Phase 3: Multi-Account Architecture**
*Database-driven multi-account support; defer details to 0005.*

Priority order (Phase 3)
1. 0005-002-001: Account-scoped endpoint structure and auth
2. 0005-002-001: Agent instance discovery and health
3. 0005-002-001: Request routing to instances (loading/caching)
4. 0005-002-002: Instance provisioning and configuration updates
5. 0005-001-002 (deferred): Agent factory, vector routing by tier, resource limits

### **Phase 4: Multi-Agent Routing & Intelligence**
*Router agent and delegation; details deferred to 0005 and 0009.*

Priority order (Phase 4)
1. 0005-003-001-01: Intent classification router
2. 0005-003-001-02: Instance selection within type
3. 0005-003-001-03: Context handoff & continuity
4. 0005-003-002-01: Unified chat endpoint using router
5. 0005-003-002-02: Router performance & fallbacks

### **Phase 5: Widget Ecosystem & UX Enhancement**
*Complete widget ecosystem and user experience enhancements*

Priority order (Phase 5)
1. 0003-003-002: Preact widget component
2. 0003-003-003: React widget component
3. 0003-010: Widget maximize/minimize toggle
4. 0004-010: Chat UI copy functionality (ensure parity across surfaces)

#### **Widget Ecosystem Enhancement**
- ❌ **0003-003-002** (Preact Chat Widget Component) **NOT STARTED** - enables React ecosystem integration
- ❌ **0003-003-003** (React Chat Widget Component) **NOT STARTED** - completes widget trio
- ❌ **0004-010** (Chat UI Copy Functionality) **NOT STARTED** - enhanced user experience
- ❌ **0003-010** (Chat Widget Maximize/Minimize Toggle) **NOT STARTED** - widget UX enhancement

### **Phase 6: Production Readiness & Technical Excellence**
*Deployment hardening, upgrades, code quality, testing.*

Priority order (Phase 6)
1. 0004-011: Session security hardening
2. 0003-009/008: HTMX 2.0.6 upgrade
3. 0004-007: Code organization & maintainability
4. 0004-008: Testing & validation (comprehensive coverage)
5. 0004-009-002: Code quality tools setup (black/ruff/mypy)
6. Performance monitoring & integration testing

### **Phase 7: Analytics & Conversation Insights**
*Add lightweight analytics and summary capabilities to improve attribution and follow‑ups.*

Priority order (Phase 7)
1. Page Source Tracking: record the originating website page for each session/conversation to attribute queries and tailor responses.
2. Conversation Summaries: generate concise summaries of completed conversations and deliver them to customers and the sales team.
3. Referrer Tracking: capture and persist HTTP referrers and campaign parameters (e.g., UTM) for analytics and routing.

## Risk Assessment & Mitigation

### 🚨 **High-Risk Items**
| Item | Risk | Mitigation |
|------|------|------------|
| **0004-012 Conversation Hierarchy** | Complex database migration | Staged rollout, rollback plan, extensive testing |
| **HTMX 2.0.6 Upgrade** | Breaking changes | Parallel implementation, feature flags |
| **Security Hardening** | Production impact | Staging environment testing, gradual rollout |

### ⚠️ **Medium-Risk Items**
| Item | Risk | Mitigation |
|------|------|------------|
| **Widget Components** | Framework compatibility | Extensive browser testing, fallback strategies |
| **Markdown Consistency** | Cross-platform differences | Standardized library versions, comprehensive testing |

## Success gates
- Foundations complete (0004-001/002/003/004)
- Simple Chat Agent functional with vector search and streaming
- Sales Agent functional with CRM, email, scheduling
- Conversation hierarchy introduced
