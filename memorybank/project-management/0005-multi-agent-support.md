# Epic 0005 - Multi-Agent Support

> Goal: Implement Pydantic AI-based multi-agent infrastructure with intelligent routing, tool calling, and specialized agent endpoints to support different agent types with distinct capabilities and workflows.

**Framework**: Built on Pydantic AI for type-safe agent development with dependency injection, structured output, and tool orchestration.

## Scope & Approach

### Multi-Agent Architecture
- **Specialized Agents**: Different agents with distinct capabilities, tools, and knowledge domains
- **Intelligent Routing**: Automatic agent selection based on query intent and context
- **Tool Integration**: Agent-specific tool calling and workflow orchestration
- **Context Preservation**: Maintain conversation context across agent handoffs

## Core Architectural Questions

### Multi-Dimensional Agent Architecture
The system must handle two distinct dimensions:

#### 1. **Agent Types (Agentic Workflows)**
Different agent workflows implemented in pydantic.ai:
- **Sales Agent**: CRM integration, lead qualification, pricing
- **Digital Expert**: Content ingestion, persona modeling, knowledge extraction
- **Support Agent**: Ticket management, knowledge base queries
- **Research Agent**: Document analysis, competitive intelligence

#### 2. **Agent Instances (Configuration Variants)**
Same workflow configured differently for specific use cases:
- **Vector Database**: Different Pinecone namespaces or dedicated indexes
- **MCP Servers**: Different tools and API access levels
- **Tool Restrictions**: Account-specific permissions and capabilities
- **Pricing Tiers**: Different feature sets and usage limits

### Multi-Tenant Account Architecture
```
Account → Agent Template Selection → Instance Configuration → Deployed Agent
├── account-123/sales-agent-enterprise    (Dedicated Pinecone index)
├── account-123/digital-expert-ceo        (Specialized content corpus)
└── account-456/sales-agent-startup       (Shared Pinecone namespace)
```

### Primary Architectural Question: Endpoint Strategy
**How should we structure API endpoints for multi-account, multi-agent, multi-instance architecture?**

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

Entry Tier (Cost-optimized):
├── PostgreSQL + pgvector
├── Shared infrastructure
└── Basic agent templates

Standard Tier (Namespace isolation):
├── Pinecone with namespaces
├── account-123-sales-agent
├── account-123-digital-expert
└── Shared Pinecone index

Premium Tier (Dedicated resources):
├── Dedicated Pinecone indexes
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
- Should agent capabilities be static (config) or dynamic (runtime discovery)?
- How do we handle agent availability and fallback strategies?

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
- How do we balance centralized configuration (app.yaml) vs. agent-specific configuration files?
- Should agent configurations be hot-reloadable or require deployment restarts?
- How do we handle configuration inheritance and overrides between global and agent-specific settings?
- Should agent configurations be versioned independently or tied to application versions?

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

## Recommended Technical Architecture

### Database Schema (PostgreSQL Primary)
```sql
-- Account management
accounts:
  id (GUID, PK)
  name (VARCHAR)
  tier (VARCHAR) -- entry, standard, premium
  created_at (TIMESTAMP)
  billing_settings (JSONB)

-- Agent template definitions
agent_templates:
  id (GUID, PK)
  name (VARCHAR) -- sales_agent, digital_expert
  workflow_class (VARCHAR) -- pydantic.ai class reference
  description (TEXT)
  version (VARCHAR)
  config_schema (JSONB) -- JSON schema for validation
  pricing_tiers (JSONB) -- tier-specific configurations

-- Account-specific agent instances
agent_instances:
  id (GUID, PK)
  account_id (GUID, FK → accounts.id)
  template_id (GUID, FK → agent_templates.id)
  name (VARCHAR) -- user-friendly name
  tier (VARCHAR)
  configuration (JSONB) -- instance-specific config
  vector_db_config (JSONB) -- Pinecone namespace or pgvector settings
  mcp_server_configs (JSONB) -- MCP server assignments and tokens
  status (VARCHAR) -- active, suspended, configuring
  created_at (TIMESTAMP)
  updated_at (TIMESTAMP)

-- MCP server registrations
mcp_servers:
  id (GUID, PK)
  name (VARCHAR)
  type (VARCHAR) -- crm, pricing, content_analysis
  endpoint_url (VARCHAR)
  is_stateless (BOOLEAN)
  supported_tools (VARCHAR[])
  account_restrictions (JSONB) -- which accounts can access

-- Vector database configurations
vector_db_configs:
  id (GUID, PK)
  account_id (GUID, FK → accounts.id)
  agent_instance_id (GUID, FK → agent_instances.id)
  type (VARCHAR) -- pinecone_namespace, pinecone_dedicated, pgvector
  connection_details (JSONB, encrypted)
  namespace (VARCHAR) -- for Pinecone
  index_name (VARCHAR) -- for dedicated indexes
```

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
> Establish core Pydantic AI infrastructure and base agent classes

#### TASK 0005-001-001 - Core Framework Installation & Configuration
- [ ] 0005-001-001-01 - CHUNK - Install Pydantic AI dependencies
  - Install `pydantic-ai` package and core dependencies
  - Configure project requirements and version constraints
  - Verify compatibility with existing FastAPI infrastructure
  - **Acceptance**: Pydantic AI imports successfully, no dependency conflicts

- [ ] 0005-001-001-02 - CHUNK - Base agent module structure
  - Create `backend/app/agents/` module hierarchy
  - Implement base agent class with common functionality
  - Define shared types and dependency injection patterns
  - **Acceptance**: Base agent class available for inheritance

- [ ] 0005-001-001-03 - CHUNK - Configuration integration
  - Extend `app.yaml` with agent configuration section
  - Implement agent configuration loading and validation
  - Add environment variable overrides for agent settings
  - **Acceptance**: Agent configurations load from YAML with env overrides

#### TASK 0005-001-002 - Agent Dependency Injection System
- [ ] 0005-001-002-01 - CHUNK - Core dependency classes
  - Implement `AgentDependencies` base class with account context
  - Add database connection, session, and configuration dependencies
  - Create dependency factory for agent instantiation
  - **Acceptance**: Agents receive properly injected dependencies

- [ ] 0005-001-002-02 - CHUNK - Vector database dependency integration
  - Implement vector database configuration dependency
  - Add Pinecone namespace/dedicated index routing
  - Create pgvector fallback for entry-tier accounts
  - **Acceptance**: Agents access appropriate vector database per account tier

- [ ] 0005-001-002-03 - CHUNK - MCP server dependency integration
  - Implement MCP server configuration dependency injection
  - Add account-specific MCP server routing and authentication
  - Create MCP client wrapper for agent tool integration
  - **Acceptance**: Agents access account-specific MCP servers

### FEATURE 0005-002 - Agent Template System
> Implement agent template management and instantiation

#### TASK 0005-002-001 - Agent Template Database Schema
- [ ] 0005-002-001-01 - CHUNK - Agent template database tables
  - Create `agent_templates` table with workflow definitions
  - Add `agent_instances` table for account-specific configurations
  - Implement `agent_tools` table for tool registry
  - **Acceptance**: Database schema supports agent templates and instances

- [ ] 0005-002-001-02 - CHUNK - Agent configuration models
  - Define Pydantic models for agent template configuration
  - Implement configuration validation and schema enforcement
  - Add pricing tier and feature flag support
  - **Acceptance**: Agent configurations validate correctly

#### TASK 0005-002-002 - Template Management API
- [ ] 0005-002-002-01 - CHUNK - Template CRUD operations
  - Implement template creation, reading, updating, deletion
  - Add template versioning and backward compatibility
  - Create template validation and testing framework
  - **Acceptance**: Agent templates managed through API

- [ ] 0005-002-002-02 - CHUNK - Instance provisioning system
  - Implement agent instance creation from templates
  - Add account-specific configuration override handling
  - Create instance lifecycle management (activate, suspend, delete)
  - **Acceptance**: Agent instances provisioned correctly per account

### FEATURE 0005-003 - Multi-Agent Routing & Delegation
> Implement intelligent agent routing and delegation capabilities

#### TASK 0005-003-001 - Router Agent Implementation
- [ ] 0005-003-001-01 - CHUNK - Intent classification router
  - Implement Pydantic AI router agent for intent detection
  - Add query classification and agent selection logic
  - Create fallback handling for ambiguous queries
  - **Acceptance**: Router correctly identifies appropriate specialist agents

- [ ] 0005-003-001-02 - CHUNK - Agent delegation framework
  - Implement agent-to-agent delegation using Pydantic AI
  - Add context preservation across agent handoffs
  - Create delegation tracking and conversation continuity
  - **Acceptance**: Agents delegate successfully with context preservation

#### TASK 0005-003-002 - Account-Scoped Agent Endpoints
- [ ] 0005-003-002-01 - CHUNK - Account-based routing
  - Implement `/accounts/{account-id}/agents/{agent-id}/chat` endpoints
  - Add account authentication and authorization middleware
  - Create agent discovery endpoints per account
  - **Acceptance**: Account-scoped agent endpoints functional

- [ ] 0005-003-002-02 - CHUNK - Agent session management
  - Implement agent-specific session handling
  - Add conversation tracking per agent instance
  - Create cross-agent conversation linking
  - **Acceptance**: Agent sessions managed independently with linking

### FEATURE 0005-004 - Tool Integration Framework
> Establish tool integration patterns for Pydantic AI agents

#### TASK 0005-004-001 - Base Tool Classes
- [ ] 0005-004-001-01 - CHUNK - Tool base class implementation
  - Create base tool class with common functionality
  - Implement tool authentication and error handling
  - Add tool usage tracking and rate limiting
  - **Acceptance**: Tools inherit common functionality consistently

- [ ] 0005-004-001-02 - CHUNK - MCP server tool integration
  - Implement MCP server tool wrapper for Pydantic AI
  - Add dynamic tool discovery from MCP servers
  - Create tool authentication and session management
  - **Acceptance**: MCP server tools available to agents

#### TASK 0005-004-002 - Tool Registry & Discovery
- [ ] 0005-004-002-01 - CHUNK - Dynamic tool registration
  - Implement runtime tool registration system
  - Add tool capability detection and metadata
  - Create tool availability checking per account/agent
  - **Acceptance**: Tools registered and discoverable dynamically

- [ ] 0005-004-002-02 - CHUNK - Tool security and permissions
  - Implement tool access control per account tier
  - Add tool usage auditing and logging
  - Create tool rate limiting and quota management
  - **Acceptance**: Tool access properly controlled and audited

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
