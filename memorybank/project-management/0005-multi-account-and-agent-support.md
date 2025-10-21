<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Epic 0005 - Multi-Agent Support
> **Last Updated**: September 04, 2025

> Goal: Implement multi-account and multi-agent infrastructure supporting four agent types (simple-chat, sales, simple-research, deep-research) with account-scoped routing, agent instance management, and intelligent query routing within accounts.

**Framework**: Built on Pydantic AI with database-driven agent instance management, supporting multiple agent instances per account with different configurations, vector databases, and tool access.

## Scope & Approach

### Five Agent Types Supported
See agent type list in [architecture/code-organization.md](../architecture/code-organization.md) (simple-chat, sales, simple-research, deep-research, digital-expert). Details for Digital Expert live in [0009-digital-expert-agent.md](0009-digital-expert-agent.md).

### Multi-Account Infrastructure (essentials for 0005-001)
- **Vector Database Policy**: Subscription-based routing — Budget accounts use pgvector; Standard and Professional use shared Pinecone (namespaces/shared index; main difference is allowed storage volume); Enterprise accounts get a dedicated Pinecone instance. Level of sharing for Standard/Professional to be finalized (namespace strategy vs segmented shared indexes).

<!-- Non-essential routing and deep multi-account details removed for 0005-001 scope -->

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
See summary in [architecture/code-organization.md](../architecture/code-organization.md). This epic focuses on implementing 0005-001 first.

## References
- Architecture and code structure: [architecture/code-organization.md](../architecture/code-organization.md)
- Agent configuration schema: [architecture/agent-configuration.md](../architecture/agent-configuration.md)
- API gateway, config storage, Redis: see `architecture/*.md` docs

<!-- Deep schema, MCP, and scaling examples removed; see architecture docs if needed -->

---

## Implementation Plan

### FEATURE 0005-001 - Pydantic AI Framework Setup
> Establish core Pydantic AI infrastructure and base agent classes for multi-account support

#### TASK 0005-001-001 - Core Framework Installation & Configuration ✅ COMPLETE
- [x] 0005-001-001-01 - CHUNK - Install Pydantic AI dependencies
  - Install `pydantic-ai` package and core dependencies
  - Configure project requirements and version constraints
  - Verify compatibility with existing FastAPI infrastructure
  - **Acceptance**: Pydantic AI imports successfully, no dependency conflicts

#### 0005-001-001-01 - AUTOMATED-TESTS - Pydantic AI Dependencies
**Unit Tests** (`backend/tests/unit/test_pydantic_ai_setup.py`):
- **Import Validation**: Verify pydantic-ai imports successfully with version ≥0.8.1
- **FastAPI Compatibility**: Confirm Agent class works alongside FastAPI without conflicts
- **Core Dependencies**: Check all required packages (pydantic, fastapi, asyncio) are available
- **Version Constraints**: Validate minimum versions meet requirements (pydantic ≥2.0.0, fastapi ≥0.100.0)

- [x] 0005-001-001-02 - CHUNK - Base agent module structure
  - Create `backend/app/agents/` module hierarchy following code-organization.md
  - Implement base agent class with account-aware dependency injection
  - Define shared types and multi-account dependency patterns
  - **Acceptance**: Base agent class supports account isolation

#### 0005-001-001-02 - AUTOMATED-TESTS - Base Agent Module Structure
**Unit Tests** (`backend/tests/unit/test_agent_base_structure.py`):
- **Module Import Validation**: Verify all base agent classes import without errors
  - BaseAgent, BaseDependencies, AccountScopedDependencies, SessionDependencies
- **Agent Instantiation**: Confirm BaseAgent can be created with proper dependency types
- **Dependency Injection**: Test account-aware dependency injection patterns work correctly
- **Shared Type Definitions**: Validate core types (AgentResponse, ToolResult, AgentConfig) function properly

**Integration Tests**:
- **Account Isolation Support**: Verify different account contexts remain properly isolated

- [x] 0005-001-001-03 - CHUNK - Multi-account configuration integration + Agent Selection
  - Implement agent template loading from `backend/config/agent_configs/` directory
  - Add agent selection mechanism from app.yaml (`agents.default_agent`, `routes` configuration)
  - Create route-based agent selection logic and configuration validation
  - Add agent instance configuration loading from database (Phase 3 preparation)
  - Create configuration validation and schema enforcement for both app-level and agent-level configs
  - **Acceptance**: Agent selection works via app.yaml routing AND agent configurations load with account context

#### 0005-001-001-03 - AUTOMATED-TESTS - Configuration Integration & Agent Selection
**Unit Tests** (`backend/tests/unit/test_agent_config_loader.py`):
- **Agent Template Loading**: Verify YAML agent configs load correctly from `agent_configs/` directory
  - Test config file parsing, agent type validation, tool configuration
- **Agent Selection from app.yaml**: Confirm agent selection mechanism works
  - Route-based selection (`/chat` → `simple_chat`, `/agents/sales` → `sales_agent`)
  - Default agent fallback for unknown routes
  - Available agents listing from configuration
- **Route-to-Agent Mapping**: Test route mapping logic and fallback behavior
- **Configuration Validation**: Verify schema enforcement for both valid and invalid configs
  - Required fields validation (`agent_type`, `name`)
  - Tool configuration structure validation

**Integration Tests**:
- **Account Context Integration**: Test config loading with account context (Phase 3 preparation)
- **Config Directory Scanning**: Verify automatic discovery of agent templates in filesystem

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

### FEATURE 0005-004 - Multi-Account Agent Factory (Phase 3)
> Implement agent factory with caching, vector database routing, and resource management for multi-account architecture

#### TASK 0005-004-001 - Agent Factory Implementation
- [ ] 0005-004-001-01 - CHUNK - Agent factory implementation
  - Implement AgentFactory with LRU caching for agent instances
  - Add account-scoped agent instance creation and management
  - Create agent template to instance configuration merging
  - **Acceptance**: Factory creates account-isolated agent instances with caching

- [ ] 0005-004-001-02 - CHUNK - Vector database routing
  - Implement subscription policy routing: Budget → pgvector; Standard/Professional → Pinecone (namespace/dedicated)
  - Add account-specific vector database configuration loading
  - Create vector database connection pooling and management
  - **Acceptance**: Agent instances connect to appropriate vector database per account tier

- [ ] 0005-004-001-03 - CHUNK - Resource management and limits
  - Implement subscription-tier based agent limits enforcement
  - Add resource usage tracking and quota management
  - Create agent instance lifecycle management (active/inactive/archived)
  - **Acceptance**: Account resource limits enforced correctly per subscription tier

---

## Configuration Architecture

### Enhanced app.yaml Structure (Phase 1)
```yaml
# Enhanced backend/config/app.yaml with agent selection
agents:
  default_agent: simple_chat           # Default agent for unspecified routes
  available_agents:                    # Available agent types (Phase 1: simple_chat only)
    - simple_chat
    - sales_agent                      # Available in Phase 2
  configs_directory: ./config/agent_configs/  # Directory for agent YAML templates

# Route-to-agent mapping (Phase 1)
routes:
  "/chat": simple_chat                 # Legacy endpoint uses simple_chat
  "/agents/simple-chat": simple_chat   # Explicit simple_chat routing
  "/agents/sales": sales_agent         # Sales agent routing (Phase 2+)

# Existing configuration sections continue unchanged
llm:
  provider: openrouter
  model: deepseek/deepseek-chat-v3.1
  # ... rest of existing config
```

### Agent Configuration Templates
```yaml
# backend/config/agent_configs/simple_chat.yaml
agent_type: "simple_chat"
name: "Simple Chat Agent"
description: "General-purpose conversational agent with RAG capabilities"

system_prompt: |
  You are a helpful AI assistant with access to knowledge base search and web search.
  Always provide accurate, helpful responses with proper citations.

model_settings:
  model: "openai:gpt-4o"  # Can override app.yaml default
  temperature: 0.3
  max_tokens: 2000

tools:
  vector_search:
    enabled: true
    max_results: 5
    similarity_threshold: 0.7
  web_search:
    enabled: true
    provider: "exa"
  conversation_management:
    enabled: true
    auto_summarize_threshold: 10

dependencies:
  vector_db_required: true
  session_required: true
  account_context: true  # Phase 3 preparation
```

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

<!-- Integration patterns and broad success criteria removed; focus remains on 0005-001 deliverables -->
