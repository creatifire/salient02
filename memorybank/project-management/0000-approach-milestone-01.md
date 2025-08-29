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

## API Endpoint Evolution Summary

| Phase | Primary Endpoints | Agent Types | Strategy |
|-------|------------------|-------------|----------|
| **Phase 1** | `POST /agents/simple-chat/chat`<br/>`POST /chat` (legacy) | Simple Chat | Parallel development |
| **Phase 2** | `POST /agents/simple-chat/chat`<br/>`POST /agents/sales/chat`<br/>`POST /chat` (legacy) | Simple Chat<br/>Sales | Two agent types |
| **Phase 3** | `POST /accounts/{slug}/agents/{type}/chat`<br/>`POST /agents/{type}/chat` (compat) | Simple Chat<br/>Sales | Multi-account |
| **Phase 4** | `POST /accounts/{slug}/chat` (router)<br/>`POST /accounts/{slug}/agents/{type}/chat` | Simple Chat<br/>Sales<br/>Digital Expert | Multi-agent routing |

## Milestone 1: Sales Agent with RAG & CRM Integration

**Objective**: Deliver a working sales agent with one CRM integration, website content knowledge, and full chat memory functionality.

### **Focused Requirements (Reduced Scope)**
1. **Page Source Tracking**: Track which website page initiated each conversation
2. **Website Content RAG**: Ingest and index website content for accurate product responses
3. **Customer Profile Capture**: Collect contact information during conversations
4. **Conversation Summaries**: Generate and send summaries to customers and sales team
5. **Appointment Scheduling**: Enable booking of sales appointments
6. **CRM Integration**: Zoho CRM integration (primary choice for Milestone 1)

### **Epic Dependencies & Status Analysis**
- **✅ 0004-001/002/003/004** (Foundation): **COMPLETED** - Database, sessions, message persistence
- **🔄 0004-006** (Profile Data Collection): **READY** - Foundation for customer capture
- **🔄 0004-012** (Conversation Hierarchy): **READY** - Required for summaries  
- **🔄 0008** (Sales Agent): **REVISED** - Focused on milestone 1 requirements
- **✅ 0010** (Content Ingestion): **NEW EPIC** - Astro to Pinecone (Phase 1 priority)
- **✅ 0011/012/013** (Infrastructure): **NEW EPICS** - RAG, Email, Scheduling

### **Critical Missing Components ✅ Now Addressed**
1. ✅ **RAG Integration Service**: Epic 0011 - Vector Database Integration
2. ✅ **Email Service Integration**: Epic 0012 - Outbound Email (Mailgun)
3. ✅ **Calendar API Integration**: Epic 0013 - Scheduling (Nylas/Calendly)
4. 🔄 **Referrer Tracking**: Session middleware enhancement (add to 0008)

### **Phase 1: Complete Simple Chat Agent (Single Instance)**
*Deliver a fully functional simple chat agent with multi-tool capabilities using config file-based setup*

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
*Build specialized sales agent with RAG capabilities, business tools, and complete sales workflow*

#### **API Endpoints (Phase 2)**
**Active Endpoints:**
```
# Legacy (Continue Working)
POST /chat                           # Existing chat functionality
GET /events/stream                   # Existing SSE streaming

# Agent Endpoints (Both Active)
POST /agents/simple-chat/chat        # Simple chat agent (from Phase 1)
GET /agents/simple-chat/stream       # Simple chat agent SSE

POST /agents/sales/chat              # Sales agent (new in Phase 2)
GET /agents/sales/stream             # Sales agent SSE
```

**Strategy:**
- **Two Agent Types**: Simple chat and sales agents both available
- **Agent Selection**: Frontend specifies which agent to use in endpoint URL
- **Backward Compatibility**: Legacy `/chat` continues as fallback option
- **Demo Migration**: Demo pages updated to use appropriate agent endpoints

#### **Sales-Specific Infrastructure**
- ❌ **0010** (Website Content Ingestion) **NOT STARTED** - *Astro content pipeline feeding Pinecone*
- ❌ **0004-006** (Profile Data Collection) **NOT STARTED** - *Customer profile capture for sales agent*

#### **Complete Sales Agent (Epic 0008)**
- ❌ **0008-001** (Sales Agent Framework) **NOT STARTED** - *Specialized sales agent built on Simple Chat Agent foundation*
- ❌ **0008-002** (Sales Agent Intelligence) **NOT STARTED** - *Sales-specific knowledge and customer intelligence with RAG*
- ❌ **0008-003** (Sales Agent Business Tools) **NOT STARTED** - *CRM, email, and scheduling capabilities*
- ❌ **0008-004** (Sales Agent Optimization) **NOT STARTED** - *Performance and accuracy tuning*

#### **Business Tool Infrastructure**
- ❌ **0012** (Outbound Email Integration) **NOT STARTED** - *Mailgun infrastructure for agent*
- ❌ **0013** (Scheduling Integration) **NOT STARTED** - *Nylas/Calendly infrastructure for agent*

### **Phase 3: Multi-Account Architecture**
*Implement database-driven multi-account support with agent instances*

#### **API Endpoints (Phase 3)**
**Active Endpoints:**
```
# Legacy (Deprecated)
POST /chat                           # Redirects to /accounts/default/chat
GET /events/stream                   # Redirects to default account

# Agent Endpoints (Backward Compatible)
POST /agents/simple-chat/chat        # Maps to /accounts/default/agents/simple-chat/chat
POST /agents/sales/chat              # Maps to /accounts/default/agents/sales/chat

# Multi-Account Endpoints (New)
POST /accounts/{account-slug}/agents/{agent-type}/chat
GET /accounts/{account-slug}/agents/{agent-type}/stream
GET /accounts/{account-slug}/agents  # Agent discovery per account
```

**Strategy:**
- **Account Isolation**: Complete data separation between accounts
- **Backward Compatibility**: Phase 1-2 endpoints redirect to default account
- **Database-Driven**: Agent instances configured per account in database
- **Subscription Tiers**: Account-based resource limits and feature access

#### **Multi-Account Infrastructure**
- ❌ **0005-002** (Account-Scoped Agent Endpoints) **NOT STARTED** - *Account isolation and routing*
- ❌ **Agent Factory & Instance Management** **NOT STARTED** - *Database-driven agent instances*
- ❌ **Subscription Tiers & Resource Limits** **NOT STARTED** - *Account-based feature control*

### **Phase 4: Multi-Agent Routing & Intelligence**
*Implement router agent and intelligent delegation between agent types*

#### **API Endpoints (Phase 4)**
**Active Endpoints:**
```
# Multi-Account with Router (Primary)
POST /accounts/{account-slug}/chat   # Router selects best agent automatically
GET /accounts/{account-slug}/stream  # Unified streaming with agent handoffs

# Multi-Account Agent-Specific (Available)
POST /accounts/{account-slug}/agents/{agent-type}/chat
GET /accounts/{account-slug}/agents/{agent-type}/stream
GET /accounts/{account-slug}/agents  # Agent discovery and capabilities

# Legacy (Redirected)
POST /chat                           # → /accounts/default/chat (router)
POST /agents/{type}/chat             # → /accounts/default/agents/{type}/chat
```

**Strategy:**
- **Intelligent Routing**: Router agent automatically selects optimal agent type
- **Transparent Handoffs**: Context preserved when switching between agents
- **Client Choice**: Clients can still specify agent type or let router decide
- **Complete Compatibility**: All previous endpoint patterns supported via redirects

#### **Multi-Agent Routing**
- ❌ **0005-003** (Router Agent & Intent Classification) **NOT STARTED** - *Intelligent routing between simple chat and sales agents*
- ❌ **Agent Delegation Framework** **NOT STARTED** - *Context handoff and conversation continuity*
- ❌ **0009-001** (Digital Expert Agent Framework) **NOT STARTED** - *Third agent type for validation*

### **Phase 5: Widget Ecosystem & UX Enhancement**
*Complete widget ecosystem and user experience enhancements*

#### **Widget Ecosystem Enhancement**
- ❌ **0003-003-002** (Preact Chat Widget Component) **NOT STARTED** - enables React ecosystem integration
- ❌ **0003-003-003** (React Chat Widget Component) **NOT STARTED** - completes widget trio
- ❌ **0004-010** (Chat UI Copy Functionality) **NOT STARTED** - enhanced user experience
- ❌ **0003-010** (Chat Widget Maximize/Minimize Toggle) **NOT STARTED** - widget UX enhancement

### **Phase 6: Production Readiness & Technical Excellence**
*Production deployment and code quality*

- ❌ **0004-011** (Session Security Hardening) **NOT STARTED** - production security standards
- ❌ **0003-009/008** (HTMX 2.0.6 Upgrade) **NOT STARTED** - breaking changes require careful testing
- ❌ **0004-007** (Code Organization & Maintainability) **NOT STARTED** - clean architecture
- ❌ **0004-008** (Testing & Validation) **NOT STARTED** - comprehensive test coverage
- ❌ **0004-009-002** (Code Quality Tools Setup) **NOT STARTED** - automated quality enforcement
- Performance optimization and monitoring
- Complete integration testing

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

## Success Metrics & Gates

### **Sprint 1 Success Criteria (Current Status)**
- ✅ Demo pages load chat history correctly **COMPLETED**
- ✅ Markdown renders consistently across all 5 integration strategies **COMPLETED** (All 4 core strategies complete: Backend, Astro, Standalone, Widget - only 0004-004-002-09 cross-validation remaining)
- ❌ Documentation gaps closed **PENDING**

### **Phase 1 Success Criteria (Simple Chat Agent Foundation)**
- ✅ 0004-001: Development Environment & Database Setup **COMPLETED**
- ✅ 0004-002: Database schema and migrations **COMPLETED**
- ✅ 0004-003: Session management and middleware **COMPLETED** 
- ✅ 0004-004: Message persistence **COMPLETED**
- 🔄 0004-012: Conversation hierarchy and management **CRITICAL FOR AGENTS**
- 🔄 0011: Vector database integration (Pinecone) **READY FOR SIMPLE CHAT AGENT**

### **Milestone 1 Success Criteria (Two Working Agents)**
- 🔄 **Phase 1**: Complete Simple Chat Agent with multi-tool capabilities (vector search, web search, conversation management) **READY TO START**
- 🔄 **Phase 2**: Complete Sales Agent with RAG intelligence and business tools (CRM, email, scheduling) **PLANNED**
- 🔄 **Later Phases**: Multi-account architecture, router agent, and widget ecosystem **PLANNED**

#### **Technical Deliverables**
- 🔄 **Core Framework**: Pydantic AI agent framework with config file-based setup **READY TO START**
- 🔄 **Simple Chat Agent**: Complete multi-tool agent (Epic 0017) with vector search, web search, conversation management **READY TO START**
- 🔄 **Sales Agent**: Complete sales agent (Epic 0008) with RAG intelligence and business tools **PLANNED**
- 🔄 **RAG Infrastructure**: Pinecone integration and website content pipeline (Epics 0011, 0010) **PLANNED**
- 🔄 **Business Tools**: Email, scheduling, and CRM integration for sales agent (Epics 0012, 0013) **PLANNED**

This tactical approach balances immediate business needs with long-term technical health, providing a clear path forward for completing both epics while maintaining code quality and user experience standards.
