# Tactical Development Approach
> Strategic recommendations for prioritizing and executing remaining work across Epics 0003 and 0004

## Executive Summary

Based on comprehensive analysis of remaining work in Epic 0003 (Website & HTMX Chatbot) and Epic 0004 (Chat Memory & Persistence), this document provides tactical recommendations for development prioritization and execution strategy.

### **Recent Updates (Post-Memorybank Review)**
- **Work Order Optimization**: Moved Vector DB setup earlier (item #2) to unblock agent tools development
- **Parallel Streams**: Added concurrent work tracks to reduce overall timeline
- **Implementation Details**: Added Pydantic AI development patterns and testing strategy
- **Validation Framework**: Added incremental checkpoints and clear acceptance criteria

**Current State**: ~60% project completion with Epic 0004 foundational work completed (session management, database setup, message persistence) + ✅ Pydantic AI framework complete (FEATURE 0005-001) + ✅ Vector database setup complete (FEATURE 0011-001)
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

### **Phase 1: Complete Simple Chat Agent & Frontend Migration**
*Deliver a fully functional simple chat agent with multi-tool capabilities using config file-based setup, AND migrate frontend interfaces to use the new agent endpoints*

**Implementation Sequence**:
- **Phase 1A**: Build Pydantic AI agent (backend development)
- **Phase 1B**: Migrate frontends to use agent endpoints (frontend migration)
- **Result**: Both legacy and agent systems working, with frontends using agent endpoints

#### **Phase 1A: Agent Development** (Backend Focus)
*Detailed implementation breakdown provided in Phase 1A Implementation section below*

#### **Phase 1B: Frontend Migration** (After Agent Development)  
*Detailed implementation breakdown provided in Phase 1B Implementation section below*

### **Implementation Strategy Details**

#### **Pydantic AI Development Pattern**
```python
# Phase 1 Implementation Approach
@dataclass
class ChatDependencies:
    account_id: str  # "default" for Phase 1
    session_id: str
    db: DatabaseConn
    vector_config: VectorDBConfig

chat_agent = Agent(
    'openai:gpt-4o',
    deps_type=ChatDependencies,
    output_type=ChatResponse,
    system_prompt="..."
)

@chat_agent.tool
async def search_knowledge(ctx: RunContext[ChatDependencies], query: str) -> List[str]:
    return await vector_search(ctx.deps.vector_config, query)
```

#### **Agent Testing & Validation Strategy**
**Phase 1A Testing** (During Agent Development):
1. **Unit Testing**: Test agent tools individually using Pydantic AI's `TestModel`
2. **Integration Testing**: Test complete agent workflows with mock dependencies
3. **Agent Functionality**: Validate structured outputs and tool integration

**Phase 1B Testing** (During Frontend Migration):
4. **A/B Validation**: Compare agent responses vs legacy endpoint responses
5. **Progressive Migration**: Test each frontend component migration individually
6. **Session Compatibility**: Ensure seamless transition between legacy and agent endpoints

#### **Configuration System Implementation**
**Phase 1A Approach**: File-based configuration with database preparation + agent selection
- `backend/config/app.yaml` - Enhanced with agent selection settings
- `backend/config/agent_configs/simple_chat.yaml` - Agent template
- `backend/app/agents/config_loader.py` - YAML loading + validation + agent selection
- Database schema ready for Phase 3 transition to database-driven configs
- **Detailed Implementation**: See [0005-multi-account-and-agent-support.md](0005-multi-account-and-agent-support.md) **FEATURE 0005-001-001-03** (Multi-account configuration integration + Agent Selection) for complete app.yaml agent selection architecture and individual agent configuration patterns

**Enhanced app.yaml with Agent Selection**:
```yaml
# Added to backend/config/app.yaml
agents:
  default_agent: simple_chat           # Which agent to use by default
  available_agents:                    # List of available agent types
    - simple_chat
    - sales_agent                      # Available in Phase 2
  configs_directory: ./config/agent_configs/  # Agent YAML files location
  
# Route-specific agent assignments (optional)
routes:
  "/chat": simple_chat                 # Legacy endpoint uses simple_chat
  "/agents/simple-chat": simple_chat   # Explicit agent routing
  "/agents/sales": sales_agent         # Sales agent routing (Phase 2)
```

**Individual Agent Configuration Pattern**:
```yaml
# backend/config/agent_configs/simple_chat.yaml
agent_type: "simple_chat"
system_prompt: "You are a helpful AI assistant..."
tools:
  vector_search: 
    enabled: true
    max_results: 5
  web_search:
    enabled: true  
    provider: "exa"
model_settings:
  model: "openai:gpt-4o"
  temperature: 0.3
  max_tokens: 2000
```

#### **Risk Mitigation & Development Approach**
- **Early Vector DB Setup**: Ensures tool development isn't blocked
- **Parallel Development**: Reduces time to working agent
- **Legacy Compatibility**: Zero disruption during development
- **Incremental Testing**: Validate each component before integration

#### **API Endpoints (Phase 1A - Parallel Strategy)**
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
- **Frontend Migration**: Handled in Phase 1B after agent development is complete
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
- ✅ **0005-001-001** (Pydantic AI Framework Setup) **COMPLETED**


#### **Phase 1A Implementation Breakdown** (Detailed Work Items)

##### **Item 1: 0005-001 - Pydantic AI Framework Setup** ✅ COMPLETE
- Install pydantic-ai>=0.8.1 + dependencies (latest stable version)
- Create `backend/app/agents/base/` module structure
- Implement BaseAgent class with dependency injection patterns
- **Deliverable**: Base agent infrastructure ready for specific agent types

##### **Item 2: 0011-001 - Vector DB Minimal Setup** ✅ [COMPLETED]
- **Confirmed Configuration**: openthought-dev project, salient-dev-01 index
- **Index Details**: 1536 dimensions, cosine similarity, text-embedding-3-small model
- **Host**: https://salient-dev-01-e1nildl.svc.aped-4627-b74a.pinecone.io
- ✅ Pinecone account + development index setup (COMPLETED)
- ✅ Agent configuration in simple_chat.yaml (COMPLETED)
- ✅ Connection + namespace configuration implementation (COMPLETED)
- ✅ Basic vector search functionality (COMPLETED)
- ✅ Test data ingestion pipeline (COMPLETED & VERIFIED)
- ✅ **Integration Test**: All components verified working with live index
- **Deliverable**: Vector search working for agent tool testing
- **Critical**: Must complete before agent tools development

##### **Item 3: 0017-001 - Simple Chat Agent Foundation**
- Create simple_chat agent using BaseAgent patterns
- Basic system prompt and response structure
- Agent instantiation and dependency wiring
- **Deliverable**: Agent can respond to basic queries (no tools yet)

##### **Item 4: 0017-004 - Configuration System + Agent Selection**
- YAML config loading for agent templates from `agent_configs/` directory
- Agent selection mechanism from app.yaml (`agents.default_agent`, `routes`)
- Configuration validation using Pydantic for both app-level and agent-level configs
- Agent instance configuration merging and route-based agent selection
- **Deliverable**: Agent selection works via app.yaml + simple_chat.yaml loads and creates configured agent

##### **Stream A (Parallel): Endpoints + Content**
- **0017-005**: FastAPI agent endpoints with SSE streaming
- **0010-001**: Minimal website content ingestion for testing

##### **Stream B (Parallel): Agent Tools**  
- **0017-002**: Core tools (vector_search, conversation_management)
- **0017-003**: External tools (web_search, crossfeed_mcp)

#### **Phase 1B: Frontend Migration** (After Phase 1A Complete)
*Migrate all frontend interfaces from legacy endpoints to agent endpoints using parallel strategy*

##### **Item 1: Demo Page Migration & Testing**
- Update `web/src/pages/demo/htmx-chat.astro` to use `/agents/simple-chat/chat` *(updates 0003-007)*
- Update `web/public/htmx-chat.html` to use agent endpoints *(updates 0003-007)*
- Update iframe demo page integration *(updates 0003-002-002)*
- Test session compatibility between legacy and agent endpoints
- **Deliverable**: All demo pages successfully using agent endpoints
- **Epic References**: Updates completed features 0003-007, 0003-002-002
- **Dependencies**: Phase 1A Items 1-4 complete (agent endpoints functional)

##### **Item 2: A/B Quality Validation** *(NEW - Phase 1 Planning)*
- Create A/B testing framework comparing legacy vs agent responses
- Test identical queries on both endpoints with same session context
- Validate response quality, accuracy, and performance metrics
- Document any quality differences and optimization needs
- **Deliverable**: Agent response quality validated to meet/exceed legacy standards
- **Epic References**: NEW work - not covered in existing epics
- **Dependencies**: Demo page migration complete

##### **Item 3: Widget Integration & Testing** 
- Update `web/public/widget/chat-widget.js` to use agent endpoints *(updates 0003-003-001)*
- Test widget functionality across different embedding scenarios
- Validate cross-origin session handling for embedded widgets
- Test widget performance with agent endpoints vs legacy
- **Deliverable**: Chat widget fully functional with agent endpoints
- **Epic References**: Updates completed feature 0003-003-001 (Shadow DOM Widget)
- **Dependencies**: A/B validation complete

##### **Item 4: Progressive Frontend Rollout** *(NEW - Phase 1 Planning)*
- Migrate main chat interface (`backend/templates/index.html`) to use agent endpoints
- Update frontend routing to prefer agent endpoints over legacy
- Implement feature flags for quick rollback if needed
- Monitor performance and error rates during rollout
- **Deliverable**: All frontend interfaces using agent endpoints by default
- **Epic References**: NEW work - main interface migration not covered in existing epics
- **Dependencies**: Widget integration complete

##### **Item 5: Legacy Endpoint Deprecation Planning** *(PARTIALLY NEW - Phase 1 Planning)*
- Add deprecation warnings to legacy endpoints in headers/responses  
- Update documentation to recommend agent endpoints
- Monitor usage patterns and identify any remaining legacy usage
- Plan timeline for eventual legacy endpoint removal
- **Deliverable**: Legacy endpoints marked deprecated, usage monitoring active
- **Epic References**: Mentioned in agent-endpoint-transition.md but not detailed in existing epics
- **Dependencies**: Progressive rollout complete and stable

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
| **Agent Selection Configuration** | Breaking changes to config system | Gradual rollout with fallbacks, extensive validation |
| **HTMX 2.0.6 Upgrade** | Breaking changes | Parallel implementation, feature flags |
| **Security Hardening** | Production impact | Staging environment testing, gradual rollout |

### ⚠️ **Medium-Risk Items**
| Item | Risk | Mitigation |
|------|------|------------|
| **Widget Components** | Framework compatibility | Extensive browser testing, fallback strategies |
| **Markdown Consistency** | Cross-platform differences | Standardized library versions, comprehensive testing |

### **Phase 1 Success Gates & Validation**

#### **Phase 1A Validation Checkpoints** (Agent Development)
1. **After Item 1 (Framework)** ✅: Pydantic AI imports work, base agent class instantiates
2. **After Item 2 (Vector DB)**: Can search test vectors, basic retrieval working  
3. **After Item 3 (Agent Foundation)**: Agent responds to simple queries, no errors
4. **After Item 4 (Configuration)**: YAML config loads, agent configures correctly
5. **After Stream A (Endpoints)**: Agent accessible via API, SSE streaming works
6. **After Stream B (Tools)**: Agent uses tools correctly, structured responses

#### **Phase 1B Validation Checkpoints** (Frontend Migration)
7. **After Demo Migration**: Demo pages successfully using agent endpoints
8. **After A/B Testing**: Agent response quality validated vs legacy
9. **After Widget Integration**: Chat widget works with agent endpoints
10. **After Progressive Rollout**: All frontend components migrated successfully

#### **Final Phase 1 Acceptance Criteria** 
- ✅ **Agent Functionality**: Simple chat agent responds with structured outputs
- ✅ **Tool Integration**: Vector search tool returns relevant results
- ✅ **API Integration**: Agent accessible via `/agents/simple-chat/chat` endpoint
- ✅ **Session Compatibility**: Works with existing session management
- ✅ **Legacy Parallel**: Both legacy `/chat` and agent endpoints working
- ✅ **Configuration System**: YAML-driven agent configuration functional
- ✅ **Testing Coverage**: Unit tests for all agent components
- ✅ **Frontend Migration**: All demo pages and widgets using agent endpoints
- ✅ **Quality Validation**: A/B testing confirms agent quality meets/exceeds legacy

#### **Demo Validation Targets**
- **Technical Demo**: Agent answering questions using vector knowledge base
- **Performance Demo**: Response times comparable to legacy system (<2s)
- **Integration Demo**: Demo pages successfully using agent endpoints
- **A/B Comparison**: Agent vs legacy response quality assessment

## Milestone Success Gates
- **Phase 1 Complete**: Simple Chat Agent functional with vector search, streaming, AND all frontends migrated to use agent endpoints
- **Phase 2 Complete**: Sales Agent functional with CRM, email, scheduling  
- **Future Phases**: Multi-account architecture, conversation hierarchy, widget ecosystem
