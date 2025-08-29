# Epic 0005 - Multi-Agent Support

> Goal: Implement multi-account and multi-agent infrastructure supporting four agent types (simple-chat, sales, simple-research, deep-research) with account-scoped routing, agent instance management, and intelligent query routing within accounts.

**Framework**: Built on Pydantic AI with database-driven agent instance management, supporting multiple agent instances per account with different configurations, vector databases, and tool access.

## Scope & Approach

### Four Agent Types Supported
- **Simple Chat Agent (0017)**: Multi-tool foundation with vector search, web search, CrossFeed MCP, conversation management
- **Sales Agent (0008)**: CRM integration, product recommendations, lead qualification, scheduling
- **Simple Research Agent (0015)**: Web search, document intelligence, research synthesis, smart bookmarking
- **Deep Research Agent (0016)**: Advanced multi-step investigation, hypothesis formation, evidence validation
- **Digital Expert Agent (0009)**: Persona-based expert with content ingestion, knowledge extraction, persona modeling, and cited responses (see [0009-digital-expert-agent.md](0009-digital-expert-agent.md))

### Multi-Account Infrastructure
- **Account Isolation**: Complete data separation between accounts with account-scoped endpoints
- **Agent Instance Management**: Multiple instances per agent type per account with unique configurations
- **Vector Database Policy**: Subscription-based routing — Budget accounts use pgvector; Standard and Professional use shared Pinecone (namespaces/shared index; main difference is allowed storage volume); Enterprise accounts get a dedicated Pinecone instance. Level of sharing for Standard/Professional to be finalized (namespace strategy vs segmented shared indexes).
- **Resource Management**: Subscription-tier based limits and feature access control

### Intelligent Query Routing
- **Router Agent**: Intent classification to route queries to appropriate agent instances within an account
- **Context Preservation**: Maintain conversation context and enable agent handoffs when needed
- **Fallback Handling**: Graceful degradation when specialist agents are unavailable

## Multi-Account Agent Architecture

### Agent Instance Model
Each account can provision multiple instances of the four supported agent types:

```
Account: "Acme Healthcare Corp"
├── simple-chat-instances:
│   ├── general-support (shared knowledge base)
│   └── product-specialist (product-specific vector DB)
├── sales-agent-instances:
│   ├── human-health (Salesforce + FDA content)
│   └── animal-health (HubSpot + veterinary content)  
├── research-agent-instances:
│   ├── clinical-research (PubMed + clinical trials)
│   └── regulatory-research (FDA docs + compliance)
└── deep-research-instances:
    └── competitive-analysis (market research + patents)
```

### Configuration Differentiation
Same agent type, different configurations per instance:
- **Vector Database**: Different content libraries (Pinecone namespaces/indexes)
- **Search Engines**: Different providers (Exa for academic, Tavily for general)
- **MCP Servers**: Different tool access (basic CRM vs advanced pricing)
- **System Prompts**: Instance-specific domain expertise and tone

### Multi-Account Data Isolation
Complete separation achieved through:
- **Database Schema**: All tables include `account_id` FK (defined in [datamodel.md](../architecture/datamodel.md))
- **Vector Databases**: Account-tier routing (pgvector → Pinecone namespace → dedicated)
- **Agent Instances**: Account-scoped with unique `(account_id, instance_name)` combinations
- **Resource Limits**: Subscription-tier based agent limits and feature access

### Primary Architectural Question: Endpoint Strategy
**How should we structure API endpoints for multi-account, multi-agent, multi-instance architecture?**

Path scheme and slug mapping:
- Phase 1 (single app, single-account, one instance per agent type):
  - `/agents/{agent-name-slug}/chat` and `/agents/{agent-name-slug}/stream`
  - `{agent-name-slug}` maps internally to the concrete agent implementation and its YAML configuration (e.g., `simple-chat` → Simple Chat using `simple_chat.yaml`).
- Phase 3+ (multi-account):
  - `/accounts/{account-slug}/agents/{agent-name-slug}/chat`
  - `{agent-name-slug}` continues to map to the agent + configuration bound to that account’s instance.

### Option 1: Account-Scoped Agent Endpoints (Recommended)
```
POST /accounts/{account-id}/agents/{agent-id}/chat
POST /accounts/123/agents/sales-agent-enterprise/chat
POST /accounts/456/agents/digital-expert-startup/chat

// Agent discovery per account
GET /accounts/{account-id}/agents
GET /accounts/{account-id}/agentic-workflows  // Admin-level templates

// Agent instance management
POST /accounts/{account-id}/agents            // Create from template
PUT /accounts/{account-id}/agents/{agent-id}  // Update configuration
DELETE /accounts/{account-id}/agents/{agent-id}
```

**Pros:**
- ✅ **Perfect account isolation**: Account-based resource boundaries
- ✅ **Clear billing model**: Easy to track usage per account
- ✅ **Scalable architecture**: Aligns with Render's multi-service scaling
- ✅ **Agent-specific optimization**: Each agent can have custom configurations
- ✅ **Security**: Account-level permissions and access control

**Cons:**
- ❌ **More complex frontend**: Must manage account context
- ❌ **Agent discovery overhead**: Requires separate calls to list agents
- ❌ **Cross-agent workflows**: Harder to implement agent handoffs

### Option 2: Template-Based Configuration Management
```
// Database-stored agent templates
agent_templates:
  sales_agent:
    workflow_class: "SalesAgentWorkflow"
    pricing_tiers:
      startup: { tools: ["basic_crm"], vector_db: "pgvector" }
      enterprise: { tools: ["advanced_crm", "pricing"], vector_db: "pinecone_dedicated" }
  
  digital_expert:
    workflow_class: "DigitalExpertWorkflow"
    pricing_tiers:
      standard: { vector_db: "pinecone_namespace" }
      premium: { vector_db: "pinecone_dedicated", tools: ["advanced_nlp"] }

// Account agent instance creation
POST /accounts/{account-id}/agents
{
  "template": "sales_agent",
  "tier": "enterprise",
  "config_overrides": {
    "crm_integration": "salesforce",
    "vector_namespace": "account-123-sales"
  }
}
```

**Pros:**
- ✅ **Template reusability**: Same workflow, different configurations
- ✅ **Tiered pricing**: Easy to implement different feature levels
- ✅ **Database configuration**: Hot-reloadable, admin-friendly
- ✅ **Account isolation**: Complete data and resource separation

**Cons:**
- ❌ **Configuration complexity**: More moving parts to manage
- ❌ **Template versioning**: Need to handle template updates gracefully

### Option 3: Vector Database Strategy (Critical Decision)
```
// Multi-tier vector database architecture

Entry Tier (Budget / Cost-optimized):
├── PostgreSQL + pgvector
├── Shared infrastructure
└── Basic agent templates

Standard Tier (Shared Pinecone):
├── Pinecone (shared index with namespaces)
├── account-123-sales-agent (namespace)
├── account-123-digital-expert (namespace)
└── Storage quota: standard

Professional Tier (Shared Pinecone, larger quota):
├── Pinecone (shared index with namespaces)
├── Same isolation via namespaces
└── Storage quota: professional (larger volume)

Enterprise Tier (Dedicated resources):
├── Dedicated Pinecone instance/indexes
├── Custom MCP server instances
├── Enhanced tool access
└── Dedicated Render services
```

**Multi-Tenant Vector DB Options:**
- **Pinecone Namespaces**: Perfect for shared hosting with complete data isolation
- **Dedicated Indexes**: Premium accounts get their own Pinecone indexes
- **pgvector**: Entry-level PostgreSQL extension for smaller workloads
- **Hybrid**: Mix of pgvector (entry) → Pinecone namespace (standard) → Dedicated index (premium)

## Questions for Architectural Decision

### 1. **Agent Discovery & Capabilities**
- How should clients discover available agents and their capabilities?
  - ✅ Phase 1: Static list of five agent types (simple-chat, sales, simple-research, deep-research, digital-expert), one instance each, defined via YAML config files.
- Should agent capabilities be static (config) or dynamic (runtime discovery)?
  - ✅ Phase 1: Static via configuration files; dynamic discovery deferred to Phase 3 (DB-backed templates/instances).
- How do we handle agent availability and fallback strategies?
  - ✅ Phase 1: If a requested agent is unavailable, fallback to Simple Chat agent.

### 2. **Context & State Management**
- How do we maintain conversation context when switching between agents?
- Should agents share conversation history or maintain separate contexts?
- How do we handle agent-specific context (e.g., customer service case ID)?

### 3. **Tool Access & Security**
- Should tool access be agent-specific or user/session-specific?
- How do we prevent agents from accessing unauthorized tools or data?
- Should tool calling be logged/audited per agent or per conversation?

### 4. **Performance & Scaling**
- Should each agent type have dedicated infrastructure resources?
- How do we handle different latency requirements (fast chat vs. deep analysis)?
- Should we implement agent-specific caching strategies?

### 5. **Monitoring & Analytics**
- How granular should agent performance monitoring be?
- Should we track agent handoff patterns and success rates?
- How do we measure agent effectiveness and user satisfaction per agent type?

### 6. **Version Management**
- How do we handle agent updates and backward compatibility?
- Should agents have independent version lifecycles?
- How do we coordinate updates across dependent agents?

### 7. **Configuration Management**
- Should each agent have its own dedicated YAML configuration file complementary to app.yaml?
  - ✅ Yes. One config file per agent type under `backend/config/agent_configs/` (e.g., `simple_chat.yaml`).
- How do we balance centralized configuration (app.yaml) vs. agent-specific configuration files?
  - ✅ Global behavior in `app.yaml`; agent-specific behavior in per-agent YAML files.
- Should agent configurations be hot-reloadable or require deployment restarts?
  - ✅ Phase 1: Restart to pick up changes. Phase 3+: DB-backed configs with hot reload via cache invalidation.
- How do we handle configuration inheritance and overrides between global and agent-specific settings?
  - ✅ Phase 1: No inheritance; explicit values per agent YAML. Phase 3+: consider template/instance inheritance in DB.
- Should agent configurations be versioned independently or tied to application versions?
  - ✅ Phase 1: Tied to application releases. Phase 3+: introduce template/instance versioning.

## Proposed Investigation Plan

### Phase 1: Requirements Analysis
- **Stakeholder Interviews**: Understand different agent use cases and requirements
- **Use Case Mapping**: Document specific workflows and tool requirements per agent type
- **Performance Requirements**: Define latency, throughput, and accuracy requirements
- **Integration Analysis**: Assess frontend and external system integration needs

### Phase 2: Prototype & Validation
- **Simple Multi-Agent POC**: Implement 2-3 basic agents with different approaches
- **Endpoint Pattern Testing**: Try both unified and dedicated endpoint patterns
- **Context Handoff Testing**: Validate conversation continuity across agent switches
- **Performance Benchmarking**: Measure latency and resource usage patterns

### Phase 3: Architecture Decision
- **Trade-off Analysis**: Document pros/cons of each approach with real data
- **Stakeholder Review**: Present findings and get feedback on preferred approach
- **Technical Decision**: Choose endpoint strategy with clear rationale
- **Migration Plan**: If changing from current approach, plan transition strategy

## Recommended Starting Point

### Immediate Recommendation: **Hybrid Approach**

Start with **Option 3 (Hybrid)** for these reasons:

1. **Evolutionary Path**: Begin with unified endpoint, add specialized as needed
2. **Flexibility**: Supports both simple and complex use cases
3. **Risk Mitigation**: Can fall back to single approach if hybrid proves too complex
4. **User Choice**: Different clients can choose appropriate level of complexity

### Implementation Sequence:
1. **Phase 1**: Implement unified `/chat` endpoint with basic agent routing
2. **Phase 2**: Add agent discovery endpoints (`GET /agents`)
3. **Phase 3**: Implement specialized agent endpoints (`POST /agents/{id}/chat`)
4. **Phase 4**: Add advanced routing and handoff capabilities

### Success Metrics:
- **Developer Experience**: Easy to integrate for simple use cases
- **Flexibility**: Supports advanced agent-specific workflows
- **Performance**: Meets latency requirements for all agent types
- **Maintainability**: Clear separation of concerns and monitoring

## Research Questions for Further Investigation

### Technical Architecture
1. **Agent Registry**: Should we implement a dynamic agent registry service?
2. **Load Balancing**: How do we distribute load across multiple instances of the same agent?
3. **Circuit Breakers**: How do we handle agent failures and implement fallbacks?
4. **Streaming**: Should all agents support streaming responses or only specific ones?
5. **Configuration Architecture**: Should agents have dedicated config files (e.g., `agents/sales-agent.yaml`) vs. centralized in `app.yaml`?

### Business Logic
1. **Agent Specialization**: What's the optimal level of agent specialization vs. generalization?
2. **User Experience**: Should users be aware of agent switching or should it be transparent?
3. **Training Data**: How do we manage training data and fine-tuning per agent type?
4. **Cost Optimization**: How do we balance cost vs. capability across different agent types?

### Integration Patterns
1. **Tool Orchestration**: Should agents orchestrate tools directly or through a separate service?
2. **External APIs**: How do we handle rate limiting and authentication for agent tool calls?
3. **Database Access**: Should agents have direct database access or go through APIs?
4. **Event Streaming**: Should agent actions generate events for analytics and monitoring?

## Database Schema

Multi-account and multi-agent database schema is defined in [architecture/datamodel.md](../architecture/datamodel.md), including:
- `accounts`: Multi-account support with subscription tiers
- `agent_instances`: Account-scoped agent instances with configuration overrides  
- `agent_templates`: Template definitions for the four agent types
- `mcp_servers`: MCP server registry with account restrictions
- `vector_db_configs`: Per-instance vector database configurations

### Infrastructure Strategy (Render-Based)
```yaml
# render.yaml for multi-account agent platform
services:
  - type: web
    name: agent-platform-api
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    scaling:
      minInstances: 2
      maxInstances: 20
      targetCPUPercent: 70
    envVars:
      - key: DATABASE_URL
        from: render-postgres:platform-db
      - key: PINECONE_API_KEY
        from: render-secret:pinecone-key

  - type: backgroundWorker
    name: agent-orchestrator
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python -m app.workers.agent_orchestrator"
    instances: 3

  - type: postgres
    name: platform-db
    plan: standard-2gb
    
  - type: redis
    name: platform-cache
    plan: starter
```

### Configuration Management Strategy
**Database-Stored Configuration** with caching:
- **Agent Templates**: Stored in `agent_templates` table
- **Instance Configs**: Stored in `agent_instances` table  
- **Runtime Caching**: Redis cache for frequently accessed configs
- **Hot Reloading**: Configuration changes take effect immediately
- **Version Control**: Template versioning for backward compatibility

### Vector Database Multi-Tenancy
```python
# Pinecone namespace strategy
def get_vector_config(account_id: str, agent_instance_id: str):
    config = db.get_vector_config(account_id, agent_instance_id)
    
    if config.type == "pinecone_namespace":
        # Shared index with namespace isolation
        namespace = f"account-{account_id}-{agent_instance_id}"
        return PineconeConfig(
            index_name="shared-multi-account",
            namespace=namespace
        )
    elif config.type == "pinecone_dedicated":
        # Dedicated index for premium accounts
        return PineconeConfig(
            index_name=f"dedicated-{account_id}",
            namespace="default"
        )
    elif config.type == "pgvector":
        # Entry-tier PostgreSQL vector storage
        return PgVectorConfig(
            table_name=f"vectors_account_{account_id}_{agent_instance_id}"
        )
```

### MCP Server Integration
```python
# Stateless MCP servers can be shared
async def call_mcp_server(
    server_config: MCPServerConfig,
    account_id: str,
    agent_instance_id: str,
    action: str,
    **kwargs
):
    headers = {"Authorization": f"Bearer {server_config.api_token}"}
    
    if not server_config.is_stateless:
        # Add account context for stateful servers
        headers["X-Account-ID"] = account_id
        headers["X-Agent-Instance-ID"] = agent_instance_id
    
    response = await httpx.post(
        f"{server_config.endpoint_url}/{action}",
        headers=headers,
        json=kwargs
    )
    return response.json()
```

### Scaling Strategy
- **Entry/Standard Tiers**: Shared Render services with database-level account isolation
- **Premium Tiers**: Dedicated Render services for complete infrastructure isolation
- **Auto-scaling**: Render's built-in scaling based on CPU/memory usage
- **Database Scaling**: PostgreSQL read replicas for improved performance
- **Cache Layer**: Redis for configuration and session caching

This epic will establish the foundation for a sophisticated, scalable, multi-account AI agent platform that can serve diverse customer segments while maintaining cost-effectiveness and operational simplicity.

---

## Implementation Plan

### FEATURE 0005-001 - Pydantic AI Framework Setup
> Establish core Pydantic AI infrastructure and base agent classes for multi-account support

#### TASK 0005-001-001 - Core Framework Installation & Configuration
- [ ] 0005-001-001-01 - CHUNK - Install Pydantic AI dependencies
  - Install `pydantic-ai` package and core dependencies
  - Configure project requirements and version constraints
  - Verify compatibility with existing FastAPI infrastructure
  - **Acceptance**: Pydantic AI imports successfully, no dependency conflicts

- [ ] 0005-001-001-02 - CHUNK - Base agent module structure
  - Create `backend/app/agents/` module hierarchy following code-organization.md
  - Implement base agent class with account-aware dependency injection
  - Define shared types and multi-account dependency patterns
  - **Acceptance**: Base agent class supports account isolation

- [ ] 0005-001-001-03 - CHUNK - Multi-account configuration integration
  - Implement agent template loading (filesystem initially, database eventually)
  - Add agent instance configuration loading from database
  - Create configuration validation and schema enforcement
  - **Acceptance**: Agent configurations load with account and instance context

#### TASK 0005-001-002 - Multi-Account Agent Factory (Deferred to Phase 3)
- [ ] 0005-001-002-01 - CHUNK - Agent factory implementation (Phase 3)
  - Implement AgentFactory with LRU caching for agent instances
  - Add account-scoped agent instance creation and management
  - Create agent template to instance configuration merging
  - **Acceptance**: Factory creates account-isolated agent instances with caching

- [ ] 0005-001-002-02 - CHUNK - Vector database routing (Phase 3)
  - Implement subscription policy routing: Budget → pgvector; Standard/Professional → Pinecone (namespace/dedicated)
  - Add account-specific vector database configuration loading
  - Create vector database connection pooling and management
  - **Acceptance**: Agent instances connect to appropriate vector database per account tier

- [ ] 0005-001-002-03 - CHUNK - Resource management and limits (Phase 3)
  - Implement subscription-tier based agent limits enforcement
  - Add resource usage tracking and quota management
  - Create agent instance lifecycle management (active/inactive/archived)
  - **Acceptance**: Account resource limits enforced correctly per subscription tier

### FEATURE 0005-002 - Account-Scoped Agent Endpoints
> Implement account-based routing and agent instance endpoints

#### TASK 0005-002-001 - Account-Based Routing Infrastructure
- [ ] 0005-002-001-01 - CHUNK - Account-scoped endpoint structure
  - Implement `/accounts/{account-slug}/chat/{agent-type}/{instance-name}` endpoints
  - Add account authentication and authorization middleware  
  - Create account resolution from slug to account ID
  - **Acceptance**: Account-scoped agent endpoints functional with proper isolation

- [ ] 0005-002-001-02 - CHUNK - Agent instance discovery
  - Implement `GET /accounts/{account-slug}/agents` endpoint for instance listing
  - Add agent instance metadata and capability reporting
  - Create agent instance status and health checking
  - **Acceptance**: Clients can discover available agent instances per account

- [ ] 0005-002-001-03 - CHUNK - Request routing to agent instances
  - Implement request routing from endpoint to appropriate agent instance
  - Add agent instance loading and caching integration
  - Create error handling for unavailable or misconfigured instances
  - **Acceptance**: Requests correctly routed to account-specific agent instances

#### TASK 0005-002-002 - Agent Instance Management API
- [ ] 0005-002-002-01 - CHUNK - Instance provisioning endpoints
  - Implement `POST /accounts/{account-slug}/agents` for instance creation
  - Add template selection and configuration override handling
  - Create instance validation and configuration merging
  - **Acceptance**: Agent instances can be provisioned through API per account

- [ ] 0005-002-002-02 - CHUNK - Instance configuration management
  - Implement `PUT /accounts/{account-slug}/agents/{instance-id}/config` for updates
  - Add configuration validation and hot-reloading
  - Create instance status management (activate/deactivate/archive)
  - **Acceptance**: Agent instance configurations can be updated without service restart

### FEATURE 0005-003 - Router Agent & Intent Classification
> Implement intelligent query routing to appropriate agent instances within accounts

#### TASK 0005-003-001 - Router Agent Implementation
- [ ] 0005-003-001-01 - CHUNK - Intent classification router
  - Implement Pydantic AI router agent for intent detection between the four agent types
  - Add query classification logic to route between simple-chat, sales, simple-research, deep-research
  - Create confidence scoring and fallback to simple-chat agent for ambiguous queries
  - **Acceptance**: Router correctly identifies appropriate agent type for user queries

- [ ] 0005-003-001-02 - CHUNK - Agent instance selection within type
  - Implement instance selection logic when multiple instances of same type exist
  - Add instance capability matching based on configuration (vector DB content, tools)
  - Create load balancing for instances with similar capabilities
  - **Acceptance**: Router selects optimal agent instance within the chosen agent type

- [ ] 0005-003-001-03 - CHUNK - Context handoff and conversation continuity
  - Implement conversation context preservation across agent switches
  - Add conversation metadata to track which agents handled which messages
  - Create conversation summary generation for agent handoffs
  - **Acceptance**: Context preserved when routing changes between agent instances

#### TASK 0005-003-002 - Router Integration with Account Endpoints
- [ ] 0005-003-002-01 - CHUNK - Unified chat endpoint with routing
  - Implement `/accounts/{account-slug}/chat` endpoint that uses router agent
  - Add automatic agent selection based on query intent and account available instances
  - Create transparent routing that doesn't require clients to specify agent type
  - **Acceptance**: Clients can chat without specifying agent type, router handles selection

- [ ] 0005-003-002-02 - CHUNK - Router performance optimization
  - Implement caching for frequently used routing decisions  
  - Add router agent performance monitoring and optimization
  - Create fallback mechanisms when router agent is unavailable
  - **Acceptance**: Router operates efficiently with sub-100ms decision time

---

## Technical Architecture

### Agent Module Structure
```
backend/app/agents/
├── __init__.py
├── base/
│   ├── __init__.py
│   ├── agent_base.py          # Base Pydantic AI agent class
│   ├── dependencies.py        # Common dependency injection
│   ├── tools_base.py          # Base tool classes
│   └── types.py              # Shared types and models
├── router/
│   ├── __init__.py
│   ├── intent_router.py       # Router agent implementation
│   └── delegation.py          # Agent delegation logic
├── sales/                     # Sales agent (Epic 0008)
├── digital_expert/            # Digital expert agent (Epic 0009)
└── shared/
    ├── __init__.py
    ├── mcp_client.py          # MCP server integration
    ├── vector_tools.py        # Vector database tools
    └── config_manager.py      # Agent configuration management
```

### Pydantic AI Integration Patterns
```python
# Base agent with dependency injection
@dataclass
class AgentDependencies:
    account_id: str
    db: DatabaseConn
    vector_config: VectorDBConfig
    mcp_servers: Dict[str, MCPServerConfig]
    pricing_tier: str

base_agent = Agent[AgentDependencies, BaseOutput](
    'openai:gpt-4o',
    deps_type=AgentDependencies,
    system_prompt="Base agent system prompt"
)

# Tool integration pattern
@base_agent.tool
async def vector_search(ctx: RunContext[AgentDependencies], query: str) -> List[str]:
    config = ctx.deps.vector_config
    # Route to appropriate vector database based on tier
    if ctx.deps.pricing_tier == "premium":
        return await pinecone_dedicated_search(config, query)
    else:
        return await pinecone_namespace_search(config, query)
```

## Success Criteria

### Phase 1: Foundation (Milestone 1)
- [ ] Base Pydantic AI agent framework operational
- [ ] Agent dependency injection system functional
- [ ] Basic agent template system implemented
- [ ] MCP server tool integration working

### Phase 2: Multi-Agent Capabilities
- [ ] Router agent with intent classification functional
- [ ] Agent delegation with context preservation working
- [ ] Account-scoped agent endpoints operational
- [ ] Tool registry and discovery system complete

### Phase 3: Production Readiness
- [ ] Agent security and access control implemented
- [ ] Performance monitoring and optimization complete
- [ ] Comprehensive testing and validation passed
- [ ] Documentation and deployment guides ready
