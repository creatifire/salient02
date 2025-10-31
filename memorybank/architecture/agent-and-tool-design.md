<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Agent and Tool Design Architecture

> **Last Updated**: January 31, 2025  
> **Related**: [code-organization.md](code-organization.md), [simple-chat-agent-design.md](simple-chat-agent-design.md)

## Overview

Four-layer architecture for Pydantic AI agents: Agents → Tools → Services → Data. Each layer has distinct responsibilities with clear boundaries.

## Architecture Layers

```
Agent Layer      →  Defines agents, registers tools, manages prompts
Tool Layer       →  Adapts services for LLM consumption (context → string)
Service Layer    →  Reusable business logic (parameters → structured data)
Data Layer       →  Models, external APIs (Pinecone, PostgreSQL)
```

## Layer 1: Agents (`backend/app/agents/`)

**Purpose**: Pydantic AI agent definitions and orchestration.

**Conventions**:
- One file per agent type (`simple_chat.py`, `sales.py`)
- Use `SessionDependencies` from `base.dependencies`
- Register tools with `agent.tool()`
- System prompts: static (config) or dynamic (functions)

**Example**:
```python
from pydantic_ai import Agent
from ..base.dependencies import SessionDependencies
from ..tools.directory_tools import search_directory

def create_agent(model_name: str, system_prompt: str) -> Agent:
    agent = Agent(model=model_name, deps_type=SessionDependencies, system_prompt=system_prompt)
    agent.tool(search_directory)
    return agent
```

---

## Layer 2: Tools (`backend/app/agents/tools/`)

**Purpose**: Adapt services for LLM consumption.

**Responsibilities**:
1. Extract context from `RunContext[SessionDependencies]`
2. Validate tool access via `agent_config`
3. Call services with extracted parameters
4. Format results as strings for LLM

**Required Pattern**:
```python
async def tool_name(
    ctx: RunContext[SessionDependencies],  # First parameter
    param1: str,
    filters: Optional[Dict[str, str]] = None,
) -> str:  # Always return string
    """Tool description for LLM."""
    
    # Extract context
    account_id = ctx.deps.account_id
    agent_config = ctx.deps.agent_config
    
    # Validate access
    if not agent_config.get("tools", {}).get("tool_name", {}).get("enabled"):
        return "Tool not enabled"
    
    # Create independent session (session-per-operation)
    db_service = get_database_service()
    async with db_service.get_session() as session:
        # Call service
        service = ServiceClass()
        results = await service.method(session, account_id, ...)
        
        # Format for LLM
        return format_results(results)
```

**Rules**:
- ✅ `RunContext[SessionDependencies]` as first parameter
- ✅ Always return `str`
- ✅ Create independent sessions per tool call
- ❌ Never use `ctx.deps.db_session` (removed in BUG-0023-001)

---

## Layer 3: Services (`backend/app/services/`)

**Purpose**: Reusable business logic, agent-agnostic.

**Pattern**:
```python
class ServiceClass:
    @staticmethod
    async def method_name(
        session: AsyncSession,  # First parameter
        account_id: UUID,      # Second parameter
        param1: str,
        filters: Optional[Dict] = None,
    ) -> List[Model] | Model | Dict:  # Structured data
        """Pure business logic - no agent context."""
        query = select(Model).where(...)
        result = await session.execute(query)
        return result.scalars().all()
```

**Rules**:
- ✅ No `RunContext` dependency
- ✅ `session: AsyncSession` as first parameter
- ✅ Return structured data (models, lists, dicts)
- ❌ Never import tools or agents
- ❌ Never return formatted strings

---

## Dependency Injection

All agents use `SessionDependencies`:

```python
@dataclass
class SessionDependencies:
    session_id: str
    agent_instance_id: Optional[int] = None
    account_id: Optional[UUID] = None
    agent_config: Optional[Dict[str, Any]] = None
    # db_session removed - tools create own sessions (BUG-0023-001)
```

---

## Quick Reference

### File Naming
- Agents: `{agent_type}.py` → `simple_chat.py`
- Tools: `{functionality}_tools.py` → `directory_tools.py`
- Services: `{domain}_service.py` → `directory_service.py`

### Import Patterns
- Tools → Services: `from ...services.directory_service import DirectoryService`
- Tools → Dependencies: `from ..base.dependencies import SessionDependencies`
- Services → Models: `from ..models.directory import DirectoryEntry`
- ❌ Services never import tools/agents

### Dependency Direction
```
Agents → Tools → Services → Models/External APIs
```
Dependencies flow down, never up.

---

## Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Business logic in tools | Tools call services |
| Services import tools | Services import only models |
| Shared `ctx.deps.db_session` | `async with get_db_session() as session:` |
| Services return strings | Services return structured data |
| Tools return structured data | Tools return formatted strings |

---

## Testing

| Layer | Approach |
|-------|----------|
| **Services** | Test independently with test DB sessions, mock external APIs |
| **Tools** | Mock `RunContext[SessionDependencies]`, verify formatting |
| **Agents** | Test creation/registration, mock dependencies |

---

## Library Verification

Verified against official documentation:

| Library | Status | Pattern |
|---------|--------|---------|
| **Pydantic AI** | ✅ Verified | `RunContext[DepsType]`, `@agent.tool`, `ctx.deps` |
| **SQLAlchemy** | ✅ Verified | `AsyncSession` context manager, session-per-operation, `selectinload()` |
| **Pinecone** | ⚠️ Functional | Uses sync client; consider `PineconeAsyncio` for future |
| **PostgreSQL** | ✅ Verified | Connection pooling via SQLAlchemy |
| **FastAPI** | ✅ Verified | Async endpoints, dependency injection, lifespan |

**References**: [Pydantic AI](https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md) | [SQLAlchemy AsyncIO](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | [Pinecone AsyncIO](https://github.com/pinecone-io/pinecone-python-client/blob/main/docs/asyncio.rst)

---

## References

- [code-organization.md](code-organization.md)
- [simple-chat-agent-design.md](simple-chat-agent-design.md)
- [directory-search-tool.md](directory-search-tool.md)
- [vector-query-tool.md](vector-query-tool.md)
- [bugs-0023.md](../project-management/bugs-0023.md#bug-0023-001)

---

**Last Updated**: January 31, 2025  
**Verified Against**: Pydantic AI, SQLAlchemy, Pinecone, FastAPI official documentation
