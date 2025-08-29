# Epic 0005 - Multi-Agent Support

> Goal: Implement multi-account and multi-agent infrastructure supporting four agent types (simple-chat, sales, simple-research, deep-research) with account-scoped routing, agent instance management, and intelligent query routing within accounts.

**Framework**: Built on Pydantic AI with database-driven agent instance management, supporting multiple agent instances per account with different configurations, vector databases, and tool access.

## Scope & Approach

### Five Agent Types Supported
See agent type list in [architecture/code-organization.md](../architecture/code-organization.md) (simple-chat, sales, simple-research, deep-research, digital-expert). Details for Digital Expert live in [0009-digital-expert-agent.md](0009-digital-expert-agent.md).

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

See the database schema and isolation model in [architecture/datamodel.md](../architecture/datamodel.md). Per-account isolation is enforced across API, storage, and vector DB (per the Vector DB Policy above).

### Primary Architectural Question: Endpoint Strategy
**How should we structure API endpoints for multi-account, multi-agent, multi-instance architecture?**

Path scheme and slug mapping:
- Phase 1 (single app, single-account, one instance per agent type):
  - `/agents/{agent-name-slug}/chat` and `/agents/{agent-name-slug}/stream`
  - `{agent-name-slug}` maps internally to the concrete agent implementation and its YAML configuration (e.g., `simple-chat` → Simple Chat using `simple_chat.yaml`).
- Phase 3+ (multi-account):
  - `/accounts/{account-slug}/agents/{agent-name-slug}/chat`
  - `{agent-name-slug}` continues to map to the agent + configuration bound to that account’s instance.

Legacy terminology:
- “legacy-agent” refers to the existing pre–pydantic-ai implementation behind `POST /chat` and `GET /events/stream`.

### Endpoint & Configuration Options
Endpoint patterns and configuration templates are summarized in [architecture/code-organization.md](../architecture/code-organization.md). This epic focuses on implementing 0005-001/002/003; option trade-offs are tracked in architecture docs.

## Open items (trackers)
- Standard/Professional Pinecone sharing model: finalize single shared index vs segmented shared indexes (Phase 2 decision).

## References
- Architecture and code structure: [architecture/code-organization.md](../architecture/code-organization.md)
- Data model and account isolation: [architecture/datamodel.md](../architecture/datamodel.md)
- Agent configuration schema: [architecture/agent-configuration.md](../architecture/agent-configuration.md)

## Research Questions for Further Investigation

### Technical Architecture

#### 1) API Gateway (Kong) policies
See [architecture/api-gateway-kong-policies.md](../architecture/api-gateway-kong-policies.md).

#### 2) Agent configuration storage (files → database)
See [architecture/agent-configuration-storage.md](../architecture/agent-configuration-storage.md).

#### 3) Redis usage policy
See [architecture/redis-usage-policy.md](../architecture/redis-usage-policy.md).

## Database Schema

Multi-account and multi-agent database schema is defined in [architecture/datamodel.md](../architecture/datamodel.md), including:

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
