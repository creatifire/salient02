# Tactical Development Approach - Streamlined
> Sequential development approach focused on incremental enhancement and systematic scaling

## Executive Summary

**Current State**: ~60% project completion with foundational infrastructure complete:
- ✅ Epic 0004 (Chat Memory & Persistence) - Session management, database, message persistence
- ✅ Feature 0005-001 (Pydantic AI Framework) - Agent infrastructure ready  
- ✅ Feature 0011-001 (Vector Database Setup) - Pinecone integration working

**Approach**: Linear progression through 9 priority items with manageable chunks, manual verification checkpoints, and automated testing documented in epic files.

---

## 🎯 DEVELOPMENT PRIORITIES (Sequential Order)

### ✅ **Phase 0: Cleanup Overengineered Code** (COMPLETED)
**Epic Reference**: [0017-simple-chat-agent.md](0017-simple-chat-agent.md) - Phase 0
**Status**: ✅ **COMPLETED** - All 5 tasks finished successfully

**Summary**: Removed 950+ lines of overengineered agent code to create clean foundation:
- SimpleChatAgent wrapper (305 lines) → DELETED
- Factory system (389 lines) → DELETED  
- ChatResponse model (209 lines) → DELETED
- 15 failing agent tests → Fixed (reduced to 4 infrastructure failures)
- All legacy functionality preserved and working

**Foundation Ready**: Clean codebase with SessionDependencies, config loading, and all infrastructure intact. Ready for simple Pydantic AI implementation.

---

### **Priority 1: Legacy Agent Switch** 🔄
**Epic Reference**: [0017-simple-chat-agent.md](0017-simple-chat-agent.md) - TASK 0017-001
**Goal**: Add configuration switch to enable/disable legacy chat endpoint

**Implementation:**
- Add `legacy.enabled: true/false` to `backend/config/app.yaml`
- Update FastAPI routing to conditionally register legacy `/chat` endpoint
- Maintain backward compatibility during development

**Detailed Implementation**: See TASK 0017-001 in [0017-simple-chat-agent.md](0017-simple-chat-agent.md) for complete acceptance criteria, automated tests, and technical specifications.

**Chunk Size**: ~0.5 day (as refined in TASK 0017-001)
**Manual Verification**: Toggle switch, confirm legacy endpoint enables/disables correctly
**Dependencies**: Phase 0 complete ✅
**Status**: 🚀 **Ready to start** (Phase 0 cleanup completed)

---

### **Priority 2: Simple Chat Agent Implementation** 🤖
**Epic Reference**: [0017-simple-chat-agent.md](0017-simple-chat-agent.md)
**Goal**: Implement enhanced chat agent with vector search and web search capabilities

**Key Features:**
- Pydantic AI agent following official documentation patterns (~45 lines)
- Full legacy feature parity (session handling, message persistence, logging, error handling)
- Integrated vector search using existing Pinecone setup (0+ indexes supported)
- Exa search engine integration (with search engine enable/disable switch)
- Both SSE streaming and all-in-one shot responses
- Account-based routing structure: `<account_id>/<agent_id>/chat` (starting with "default" account)

**Configuration Structure:**
```
backend/config/
└── <account_id>_configs/           # Start with "default_configs/"
    └── agent_<name>/
        └── agent_config.yaml       # Specifies agent type, LLM, search engine enabled/disabled, vector indexes
```

**Endpoints:**
```
POST /default/simple-chat/chat      # Enhanced chat with tools
GET /default/simple-chat/stream     # SSE streaming  
```

**Task Breakdown** (Sequential Implementation):
1. **TASK 0017-002** (~1 day): Direct Pydantic AI Agent Implementation - Core agent with YAML configuration
2. **TASK 0017-003** (~0.5 day): Conversation History Integration - Pydantic AI native message history
3. **TASK 0017-004** (~1.5 days): LLM Request Tracking & Cost Management - Comprehensive billing tracking
4. **TASK 0017-005** (~1 day): Legacy Session Compatibility - Seamless session bridging
5. **TASK 0017-006** (~1.5 days): FastAPI Endpoint Integration - Account-based routing with legacy parity
6. **TASK 0017-007** (~1 day): Vector Search Tool - @agent.tool for vector database queries  
7. **TASK 0017-008** (~1 day): Web Search Tool (Exa Integration) - @agent.tool for web search

**Manual Verification**: 
- Agent responds to queries ✓
- Vector search returns relevant results ✓  
- Web search works when enabled ✓
- Streaming and regular responses both functional ✓
- Configuration changes apply without code changes ✓
- All conversations saved to database ✓

**Detailed Implementation**: See TASK 0017-002 through TASK 0017-008 in [0017-simple-chat-agent.md](0017-simple-chat-agent.md) for complete acceptance criteria, automated tests, and technical specifications
**Dependencies**: Priority 1 complete
**Status**: 📋 Ready to start after Priority 1

---

### **Priority 3: UI Migration to Simple Chat Agent** 🎨
**Epic Reference**: [0003-website-htmx-chatbot.md](0003-website-htmx-chatbot.md)
**Goal**: Migrate all user interfaces to use enhanced simple chat agent

**Migration Order:**
1. **Demo Page** (port 8000): `web/src/pages/demo/htmx-chat.astro` → `/default/simple-chat/chat`
2. **Chat Widget**: `web/public/widget/chat-widget.js` → enhanced agent endpoints
3. **HTMX Chat**: `web/public/htmx-chat.html` → agent integration  
4. **Iframe Integration**: Update iframe demos to use agent endpoints

**Chunk Breakdown:**
1. **Demo Page Migration** (~1 day): Update Astro page to use new endpoint
2. **Widget Update** (~1 day): Modify JavaScript widget for agent endpoints
3. **HTMX Integration** (~1 day): Update HTMX patterns for enhanced functionality
4. **Iframe Testing** (~0.5 day): Verify embedded scenarios work correctly

**Manual Verification**:
- All interfaces use simple chat agent ✓
- Enhanced features (search, vector query) accessible through UI ✓
- Session continuity maintained across interfaces ✓
- Performance comparable or better than legacy ✓

**Dependencies**: Priority 2 complete
**Status**: 📋 Planned

---

### **Priority 4: Agent Type Plumbing** ⚙️
**Epic Reference**: [0005-multi-account-and-agent-support.md](0005-multi-account-and-agent-support.md) 
**Goal**: Complete infrastructure for multiple agent types with instance discovery

**Implementation:**
- Agent type registration and discovery system
- Configuration validation for different agent types  
- Routing enhancement for multiple agent types under same account
- Health checks and status monitoring for agent instances

**Chunk Size**: ~2 days
**Manual Verification**: Can add new agent types without code changes, routing works correctly
**Dependencies**: Priority 3 complete
**Status**: 📋 Planned

---

### **Priority 5: Sales Agent Addition** 💼
**Epic Reference**: [0008-sales-agent.md](0008-sales-agent.md)
**Goal**: Specialized sales agent with business tools and CRM integration

**Key Features:**
- Built on simple chat foundation with sales-specific tools
- RAG integration with business/product knowledge
- Email integration (Mailgun) for outbound communication
- Scheduling integration (Nylas/Calendly) 
- Profile data collection and lead qualification

**Endpoints:**
```
POST /default/sales-agent/chat      # Sales-focused conversation
GET /default/sales-agent/stream     # Sales agent streaming
```

**Chunk Size**: ~5 days
**Manual Verification**: Sales-specific functionality works, integrations functional
**Dependencies**: Priority 4 complete  
**Status**: 📋 Planned

---

### **Priority 6: Multi-Account Support** 🏢
**Epic Reference**: [0005-multi-account-and-agent-support.md](0005-multi-account-and-agent-support.md) - Phase 3
**Goal**: Database-driven multi-account architecture with proper isolation

**Key Features:**
- Account authentication and authorization
- Account-scoped database isolation
- Per-account configuration and billing
- Account-specific vector database namespaces

**Routing Enhancement:**
```
POST /<actual_account_id>/<agent_id>/chat    # Account-specific agents
GET /<actual_account_id>/<agent_id>/stream   # Account-scoped streaming
```

**Chunk Size**: ~7 days
**Manual Verification**: Multiple accounts work independently, data isolation maintained
**Dependencies**: Priority 5 complete
**Status**: 📋 Planned

---

### **Priority 7: Multi-Instance Per Account Support** 🔀
**Goal**: Support multiple instances of same agent type with different configurations

**Key Features:**
- Same agent type, different configurations per instance
- Example: `sales_agent_1` → vector_db_1 + GPT-4, `sales_agent_2` → vector_db_2 + Claude-3
- Instance-specific routing and configuration management

**Configuration Example:**
```
backend/config/
└── account_123_configs/
    ├── agent_sales_1/
    │   └── agent_config.yaml       # → Pinecone index A, GPT-4
    ├── agent_sales_2/ 
    │   └── agent_config.yaml       # → Pinecone index B, Claude-3
    └── agent_simple_1/
        └── agent_config.yaml       # → Pinecone index C, web search enabled, Deepseek R1
```

**Routing:**
```
POST /account_123/sales_1/chat      # Sales agent instance 1
POST /account_123/sales_2/chat      # Sales agent instance 2  
POST /account_123/simple_1/chat     # Simple chat instance 1
```

**Chunk Size**: ~4 days
**Manual Verification**: Multiple agent instances per account work independently
**Dependencies**: Priority 6 complete
**Status**: 📋 Planned

---

### **Priority 8: Preact Chat Widget** ⚛️
**Epic Reference**: [0003-website-htmx-chatbot.md](0003-website-htmx-chatbot.md) - Feature 0003-003-002
**Goal**: React-ecosystem compatible widget component

**Implementation:**
- Preact-based widget for modern React/Preact applications
- Enhanced component lifecycle management
- Better TypeScript integration
- Improved bundle size optimization

**Chunk Size**: ~3 days
**Manual Verification**: Widget works in Preact/React applications
**Dependencies**: Priority 7 complete
**Status**: 📋 Planned

---

### **Priority 9: React Chat Widget** ⚛️
**Epic Reference**: [0003-website-htmx-chatbot.md](0003-website-htmx-chatbot.md) - Feature 0003-003-003
**Goal**: Native React widget component

**Implementation:**
- Full React component with hooks integration
- Complete ecosystem compatibility
- Advanced features (context providers, custom styling)
- Documentation and examples

**Chunk Size**: ~3 days  
**Manual Verification**: Widget works seamlessly in React applications
**Dependencies**: Priority 8 complete
**Status**: 📋 Planned

---

## ✅ SUCCESS CRITERIA

### **Milestone 1 Complete** (Priorities 1-3):
- Legacy chat can be toggled on/off via configuration
- Simple chat agent provides enhanced functionality (vector search, web search, streaming)
- All UIs successfully migrated to use enhanced agent
- Performance meets or exceeds legacy implementation

### **Milestone 2 Complete** (Priorities 4-5):
- Infrastructure supports multiple agent types
- Sales agent operational with CRM/email/scheduling integration
- Agent ecosystem proven and scalable

### **Milestone 3 Complete** (Priorities 6-7):
- Multi-account architecture fully functional
- Multiple agent instances per account supported
- Enterprise-ready scaling and isolation

### **Milestone 4 Complete** (Priorities 8-9):
- Complete widget ecosystem (Shadow DOM, Preact, React)
- Modern frontend framework integration
- Developer-friendly component library

---

## 📊 RISK MITIGATION

| **Risk** | **Mitigation** |
|----------|----------------|
| **Account routing complexity** | Start with "default" account structure, scale gradually |
| **Vector DB integration issues** | Pinecone setup already working and tested |
| **UI migration breaking changes** | Maintain legacy switch as fallback during transition |
| **Multi-account data isolation** | Implement and test isolation patterns early |
| **Performance degradation** | Benchmark each priority, maintain performance metrics |

---

## 📋 TRACKING APPROACH

- **Linear Progression**: Complete each priority before starting the next
- **Chunk-Based Development**: Break priorities into manageable 0.5-2 day chunks  
- **Manual Verification**: User verification required for each chunk before proceeding
- **Automated Testing**: Tests documented in respective epic files, implemented alongside features
- **Epic References**: Each priority maps to detailed planning in specific epic documents

**Phase 0 Complete ✅ - Ready to begin Priority 1: Legacy Agent Switch** 🚀
