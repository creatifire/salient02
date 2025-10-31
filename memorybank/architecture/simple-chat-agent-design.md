<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Simple Chat Agent Design

> **Last Updated**: January 31, 2025  
> **Template**: This document serves as a template for documenting future agent designs.  
> **Architecture**: Follows patterns defined in [agent-and-tool-design.md](agent-and-tool-design.md)

## Overview

Simple Chat Agent is a **concrete instantiation** of the four-layer architecture pattern. This document shows how the general patterns apply to a specific agent type.

**See**: [Agent and Tool Design Architecture](agent-and-tool-design.md) for architectural patterns and conventions.

---

## Architecture Instantiation

### Layer 1: Agent Definition

**File**: `backend/app/agents/simple_chat.py`

```python
from pydantic_ai import Agent
from ..base.dependencies import SessionDependencies
from ..tools.directory_tools import search_directory
from ..tools.vector_tools import vector_search

def create_simple_chat_agent(model_name: str, system_prompt: str) -> Agent:
    """Creates Simple Chat agent following architecture patterns."""
    agent = Agent(
        model=model_name,
        deps_type=SessionDependencies,  # Standard dependency injection
        system_prompt=system_prompt
    )
    
    # Register tools (Layer 2)
    agent.tool(search_directory)
    agent.tool(vector_search)
    
    return agent
```

**Follows**: [Layer 1: Agents](agent-and-tool-design.md#layer-1-agents-backendappagents) pattern

---

### Layer 2: Tools Used

**Tools**:
- `search_directory` - Directory search (doctors, services, etc.)
- `vector_search` - Knowledge base search (Pinecone)

**Location**: `backend/app/agents/tools/`

**Pattern**: Each tool extracts context from `RunContext[SessionDependencies]`, validates access, calls services, and formats results as strings.

**Follows**: [Layer 2: Tools](agent-and-tool-design.md#layer-2-tools-backendappagentstools) pattern

---

### Layer 3: Services Used

**Services**:
- `DirectoryService` - Directory search business logic
- `VectorService` - Vector database operations

**Location**: `backend/app/services/`

**Pattern**: Services accept explicit parameters (session, account_id), return structured data (models, lists).

**Follows**: [Layer 3: Services](agent-and-tool-design.md#layer-3-services-backendappservices) pattern

---

### Layer 4: Data Layer

- **Database**: PostgreSQL (SQLAlchemy models)
- **Vector DB**: Pinecone (via VectorService)

**Follows**: [Layer 4: Data Layer](agent-and-tool-design.md#architecture-layers)

---

## Configuration

**Config Location**: `backend/config/agent_configs/simple_chat/config.yaml`

```yaml
agent_type: "simple_chat"
name: "Simple Chat Assistant"

prompts:
  system_prompt_file: "./system_prompt.md"

model_settings:
  model: "moonshotai/kimi-k2-0905"
  temperature: 0.3
  max_tokens: 2000

context_management:
  history_limit: 50
  context_window_tokens: 8000

tools:
  directory:
    enabled: true
    accessible_lists: ["doctors", "services"]
  
  vector_search:
    enabled: true
    max_results: 5
```

**See**: [Configuration Reference](configuration-reference.md) for complete schema.

---

## Key Features

1. **Multi-Tool Support**: Directory search + vector search**
2. **Context Management**: Conversation history with summarization
3. **Cost Tracking**: Automatic LLM cost tracking via Pydantic AI
4. **Multi-Tenant**: Account-scoped data isolation

---

## Implementation Files

| Layer | File | Purpose |
|-------|------|---------|
| **Agent** | `backend/app/agents/simple_chat.py` | Agent definition and orchestration |
| **Tools** | `backend/app/agents/tools/directory_tools.py` | Directory search tool |
| **Tools** | `backend/app/agents/tools/vector_tools.py` | Vector search tool |
| **Services** | `backend/app/services/directory_service.py` | Directory business logic |
| **Services** | `backend/app/services/vector_service.py` | Vector database operations |
| **Config** | `backend/config/agent_configs/simple_chat/config.yaml` | Agent configuration |
| **Config** | `backend/config/agent_configs/simple_chat/system_prompt.md` | System prompt |

---

## Example Usage Flow

```
User: "What urologists do you have?"
  ↓
Agent (Layer 1): Receives message, loads history
  ↓
Tool (Layer 2): search_directory(ctx, list_name="doctors", filters={"specialty": "Urology"})
  ↓
Service (Layer 3): DirectoryService.search(session, accessible_list_ids, ...)
  ↓
Data (Layer 4): Query PostgreSQL → Format results → Return
  ↓
Tool: Format results as string → Return to agent
  ↓
Agent: Incorporate into response → Return to user
```

---

## Design Decisions

1. **Uses `SessionDependencies`**: Standard dependency injection pattern
2. **Session-Per-Operation**: Tools create independent database sessions (prevents concurrent errors)
3. **String Returns from Tools**: Tools format results for LLM consumption
4. **Structured Returns from Services**: Services return models/lists for reuse

---

## Template for Future Agents

When documenting new agents, follow this structure:

1. **Overview**: Brief description and link to architecture patterns
2. **Architecture Instantiation**: Show how each layer is implemented
3. **Configuration**: Agent-specific config schema
4. **Key Features**: What makes this agent unique
5. **Implementation Files**: List of relevant files by layer
6. **Example Flow**: Show end-to-end execution
7. **Design Decisions**: Agent-specific choices

---

## References

- **[Agent and Tool Design](agent-and-tool-design.md)** - Architectural patterns this agent follows
- **[Directory Search Tool](directory-search-tool.md)** - Directory tool details
- **[Vector Query Tool](vector-query-tool.md)** - Vector search details
- **[Configuration Reference](configuration-reference.md)** - Config schema
- **[Code Organization](code-organization.md)** - File structure

---

**Last Updated**: January 31, 2025  
**Template Version**: 1.0
