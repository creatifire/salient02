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
**Status**: ✅ **COMPLETED** (Legacy endpoints conditionally registered based on config)

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

**Task Breakdown** (Sequential Implementation - **CORRECTED ORDER**):
1. **TASK 0017-002** (~1 day): Direct Pydantic AI Agent Implementation - Core agent with YAML configuration
2. **TASK 0017-003** (~0.5 day): Conversation History Integration - Pydantic AI native message history  
3. **TASK 0017-004** (~1.5 days): **FastAPI Endpoint Integration** - ⬆️ **MOVED UP** for testability
4. **TASK 0017-005** (~1.5 days): **LLM Request Tracking & Cost Management** - ⬇️ **MOVED DOWN** (testable via endpoint)
5. **TASK 0017-006** (~1 day): **Legacy Session Compatibility** - ⬇️ **MOVED DOWN** (testable via endpoints)  
6. **TASK 0017-007** (~1 day): Vector Search Tool - @agent.tool for vector database queries  
7. **TASK 0017-008** (~1 day): Web Search Tool (Exa Integration) - @agent.tool for web search

**🔄 Sequencing Rationale**: 
- **FastAPI Endpoint moved to TASK 0017-004** (from 0017-006) to provide testable interface early
- **LLM Tracking and Session Compatibility** moved after endpoint integration for proper testing workflow
- **Each task can now be manually verified** immediately upon completion using previous tasks as foundation

**Manual Verification** (Sequential Checkpoints): 
- **TASK 0017-002**: ✅ **COMPLETED** - Agent responds to basic queries with YAML configuration
- **TASK 0017-003**: ✅ **COMPLETED** - Multi-turn conversations maintain context & history ordering fixed  
- **TASK 0017-004**: ✅ **COMPLETED** - `/agents/simple-chat/chat` endpoint accessible via curl with session handling
- **TASK 0017-005**: 🔄 **NEXT** - LLM cost records appear in database with accurate token counts
- **TASK 0017-006**: 📋 **PLANNED** - Session bridging: start on `/chat`, continue on `/agents/simple-chat/chat`
- **TASK 0017-007**: 📋 **PLANNED** - Vector search returns relevant results via agent queries
- **TASK 0017-008**: 📋 **PLANNED** - Web search works when enabled and returns current information

**Detailed Implementation**: See TASK 0017-002 through TASK 0017-008 in [0017-simple-chat-agent.md](0017-simple-chat-agent.md) for complete acceptance criteria, automated tests, and technical specifications
**Dependencies**: Priority 1 complete ✅
**Status**: 🔄 **IN PROGRESS** - Tasks 0017-002, 0017-003, 0017-004 completed ✅
**Next**: TASK 0017-005 (LLM Request Tracking & Cost Management)

---

### **Priority 3: Multi-Client Widget Foundation** 🎨
**Epic Reference**: [0003-website-htmx-chatbot.md](0003-website-htmx-chatbot.md)  
**Architecture Reference**: **[Chat Widget Architecture](../architecture/chat-widget-architecture.md)** ⭐

**Goal**: Implement widget foundation supporting Shadow DOM, Preact, and HTMX UI clients with integration examples

**Backend Foundation**: ✅ **READY** (Priority 2 completed with CORS, session bridging, `/agents/simple-chat/chat` endpoint)

**Multi-Client Architecture** (detailed in [chat-widget-architecture.md](../architecture/chat-widget-architecture.md)):
- **Shadow DOM**: Universal embedding for any website (`<script>` tag integration)
- **Preact Islands**: Native Astro integration (`<SalientWidget client:load />`)
- **HTMX Integration**: Enhanced HTMX examples for server-side rendered sites
- **Foundation**: 90% shared SalientCore + 10% client-specific adaptations

**Implementation Strategy:**
1. **Shadow DOM Widget** (~1.5 days): Universal embedding with `<script src="cdn.salient.ai/widget.js" data-agent="simple-chat">` 
2. **Preact Islands Integration** (~1 day): Native Astro + Preact components with simple chat agent
3. **HTMX UI Examples** (~0.5 day): Enhanced HTMX patterns and integration documentation for server-side sites

**Widget Client Options:**
- **Shadow DOM** (Universal): `<script src="cdn.salient.ai/widget.js" data-agent="simple-chat">` - Works on any website
- **Preact Islands** (Astro): `<SalientWidget agent="simple-chat" client:load />` - Native integration
- **HTMX Integration**: Enhanced patterns for `hx-post="/agents/simple-chat/chat"` with streaming examples

**Technical Foundation:**
- **API Integration**: `/agents/simple-chat/chat` endpoint ready for widget consumption
- **Session Compatibility**: Cross-origin session sharing working (`localhost:4321` ↔ `localhost:8000`)
- **Configuration-Driven**: Widget behavior controlled via `simple_chat.yaml`
- **Framework Alignment**: Leverages existing Astro + Preact Islands architecture

**Manual Verification**:
- Preact Islands widget works in Astro pages (`<SalientWidget>`) ✓
- Shadow DOM widget embeds universally via script tag ✓
- 90% shared components proven with simple chat specialization ✓
- Session continuity between legacy and Preact widgets ✓
- Configuration-driven agent selection functional ✓
- Performance meets/exceeds legacy HTMX implementation ✓

**Dependencies**: Priority 2 complete ✅
**Status**: 📋 **READY** (Backend foundation complete)

---

### **Priority 4: Agent Type Plumbing** ⚙️
**Epic Reference**: [0005-multi-account-and-agent-support.md](0005-multi-account-and-agent-support.md) 
**Goal**: Complete infrastructure for multiple agent types with instance discovery

**Implementation:**
- Agent type registration and discovery system
- Configuration validation for different agent types  
- Routing enhancement for multiple agent types under same account
- Health checks and status monitoring for agent instances

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

**Manual Verification**: Multiple agent instances per account work independently
**Dependencies**: Priority 6 complete
**Status**: 📋 Planned

---

### **Priority 8: React and Vue Chat Widgets** ⚛️
**Epic Reference**: [0003-website-htmx-chatbot.md](0003-website-htmx-chatbot.md)  
**Architecture Reference**: **[Chat Widget Architecture](../architecture/chat-widget-architecture.md)** ⭐

**Goal**: Create dedicated React and Vue chat widget components for modern framework ecosystems

**Implementation Strategy:**
1. **React Widget Component** (~1.5 days): Native React component with hooks, context providers, and TypeScript support
2. **Vue 3 Widget Component** (~1.5 days): Composition API widget with reactive props and Vue ecosystem integration
3. **NPM Package Distribution** (~0.5 day): Publish `@salient/widget-react` and `@salient/widget-vue` packages

**React Integration:**
```tsx
// React Component with Hooks
import { SalientWidget } from '@salient/widget-react'

function App() {
  return (
    <SalientWidget 
      agent="simple-chat"
      endpoint="/agents/simple-chat/chat"
      theme="modern"
      onMessageReceived={(msg) => console.log(msg)}
    />
  )
}
```

**Vue 3 Integration:**
```vue
<!-- Vue 3 Composition API -->
<template>
  <SalientWidget 
    :agent="'simple-chat'"
    :endpoint="'/agents/simple-chat/chat'"
    :theme="'modern'"
    @message-received="handleMessage"
  />
</template>

<script setup>
import { SalientWidget } from '@salient/widget-vue'

const handleMessage = (msg) => console.log(msg)
</script>
```

**Manual Verification**: React and Vue applications can integrate Salient widgets with framework-native patterns
**Dependencies**: Priority 7 complete
**Status**: 📋 Planned

---

### **Priority 9: Advanced Widget Features** 🎨
**Epic Reference**: [0003-website-htmx-chatbot.md](0003-website-htmx-chatbot.md)  
**Architecture Reference**: **[Chat Widget Architecture](../architecture/chat-widget-architecture.md)** ⭐

**Goal**: Enhanced widget ecosystem with advanced deployment options

**Implementation:**
- **Iframe Adapter**: Sandboxed embedding for legacy systems requiring security isolation
- **API-Only Mode**: Headless widgets for mobile app integration
- **Advanced Theming**: CSS variables system for brand customization
- **Widget Analytics**: Usage metrics and performance monitoring

**Widget Distribution Matrix:**
```
Deployment     | Primary Use Case              | Integration Complexity
---------------|-------------------------------|----------------------
Shadow DOM     | Universal embedding          | Low (any website)
Preact Islands | Astro sites (native)         | Low (this project)
HTMX Patterns  | Server-side rendered sites   | Low (enhanced examples)
React Native   | React applications           | Medium (dedicated component)
Vue Native     | Vue 3 applications           | Medium (composition API)
Iframe         | Legacy security requirements | High (full isolation)
API-Only       | Mobile apps, custom UIs      | High (headless integration)
```

**Manual Verification**: All widget deployment options functional with agent specializations
**Dependencies**: Priority 8 complete
**Status**: 📋 Planned

---

## 🏗️ UI ARCHITECTURE DECISION

**Chat Widget Architecture**: Hybrid component-based approach documented in [chat-widget-architecture.md](../architecture/chat-widget-architecture.md)

**Key Benefits:**
- **Shared Foundation** (90% code reuse): Common chat functionality across all agent types
- **Agent-Specific Customization** (10% specialized): Tailored UI elements for different agents  
- **Legacy Compatibility**: Existing HTMX-based interface preserved during transition
- **Risk Mitigation**: Parallel development without disrupting proven functionality
- **Future Scalability**: Foundation ready for sales, support, and research agents

**Implementation**: Component architecture mirrors backend agent structure with seamless session bridging between legacy and enhanced agents.

---

## ✅ SUCCESS CRITERIA

### **Milestone 1 Complete** (Priorities 1-3):
- Legacy chat can be toggled on/off via configuration
- Simple chat agent provides enhanced functionality (vector search, web search, streaming)
- Multi-client widget foundation operational (Shadow DOM, Preact Islands, HTMX examples)
- Configuration-driven agent selection enables safe migration strategy
- Performance meets or exceeds legacy implementation
- Widget ecosystem proven with universal embedding + server-side integration

### **Milestone 2 Complete** (Priorities 4-5):
- Infrastructure supports multiple agent types with discovery system
- Sales agent operational with CRM/email/scheduling integration
- Agent ecosystem proven and scalable

### **Milestone 3 Complete** (Priorities 6-7):
- Multi-account architecture fully functional
- Multiple agent instances per account supported
- Enterprise-ready scaling and isolation

### **Milestone 4 Complete** (Priorities 8-9):
- React and Vue native chat widget components functional with TypeScript support
- Complete widget ecosystem (Shadow DOM, Preact, HTMX, React, Vue, Iframe, API-Only)
- Advanced features (theming, analytics, security isolation)
- NPM packages published (`@salient/widget-react`, `@salient/widget-vue`) and ecosystem integration proven

---

## 📊 RISK MITIGATION

| **Risk** | **Mitigation** |
|----------|----------------|
| **Account routing complexity** | Start with "default" account structure, scale gradually |
| **Vector DB integration issues** | Pinecone setup already working and tested |
| **UI migration breaking changes** | Hybrid widget architecture supports both legacy and enhanced agents simultaneously |
| **Multi-account data isolation** | Implement and test isolation patterns early |
| **Performance degradation** | Benchmark each priority, maintain performance metrics |

---

## 📋 TRACKING APPROACH

- **Linear Progression**: Complete each priority before starting the next
- **Chunk-Based Development**: Break priorities into manageable 0.5-2 day chunks  
- **Manual Verification**: User verification required for each chunk before proceeding
- **Automated Testing**: Tests documented in respective epic files, implemented alongside features
- **Epic References**: Each priority maps to detailed planning in specific epic documents

**Priority 1 Complete ✅ - Priority 2: Simple Chat Agent Implementation IN PROGRESS** 🔄  
**Completed**: TASK 0017-002 ✅, TASK 0017-003 ✅, TASK 0017-004 ✅  
**Next**: TASK 0017-005 (LLM Request Tracking & Cost Management) 🚀
