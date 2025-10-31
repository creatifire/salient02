<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Critical Libraries Review
> **Created**: January 12, 2025  
> **Source**: Context7 Documentation Review  
> **Purpose**: Comprehensive review of critical libraries used in Salient02 project with patterns, best practices, and recommendations

## Executive Summary

This document reviews the critical libraries used in the Salient02 project based on official documentation from Context7. The review focuses on:
- **Patterns** relevant to our architecture (Pydantic AI agents, FastAPI async endpoints, SQLAlchemy 2.0 async)
- **Best practices** for production use
- **Potential issues** and optimization opportunities
- **Migration paths** for deprecated patterns

## Critical Libraries Reviewed

1. **Pydantic AI** (`pydantic-ai==0.8.1`) - MANDATORY for all LLM interactions
2. **FastAPI** (`fastapi==0.116.1`) - Web framework
3. **SQLAlchemy** (`sqlalchemy==2.0.43`) - Database ORM
4. **Alembic** (`alembic==1.16.4`) - Database migrations
5. **Pydantic** (`pydantic==2.11.7`) - Data validation
6. **Pinecone** (`pinecone==7.3.0`) - Vector database
7. **Logfire** (`logfire==4.12.0`) - Logging/observability
8. **asyncpg** (`asyncpg==0.30.0`) - PostgreSQL async driver

---

## 1. Pydantic AI (`/pydantic/pydantic-ai`)

### Critical Patterns ✅

**Dependency Injection with RunContext:**
```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class SessionDependencies:
    session_id: str
    db: DatabaseConn
    config: AgentConfig

agent = Agent('openai:gpt-4o', deps_type=SessionDependencies)

@agent.tool
async def search_vector(ctx: RunContext[SessionDependencies], query: str) -> str:
    # Access dependencies via ctx.deps
    results = await ctx.deps.db.search(query)
    return results
```

**Key Points:**
- ✅ Use `RunContext[DepsType]` as first parameter for all tools
- ✅ Access dependencies via `ctx.deps` attribute
- ✅ Type-safe dependency injection (mypy support)
- ✅ Works with both sync and async dependencies

### Streaming Pattern ✅

**Agent Streaming Events:**
```python
async with agent.run_stream(prompt, deps=deps) as run:
    async for event in run.stream_text():
        # Handle streaming text chunks
        yield event
```

**Event Types:**
- `PartStartEvent` - New part starting
- `PartDeltaEvent` - Text/thinking/tool call deltas
- `FunctionToolCallEvent` - Tool invocation
- `FunctionToolResultEvent` - Tool result
- `FinalResultEvent` - Final output ready

**SSE Integration:**
- Use `run.stream_text()` for Server-Sent Events
- Event handlers via `event_stream_handler` parameter
- Supports nested streaming for complex workflows

### Best Practices ✅

1. **Tool Retries**: Use `@agent.tool(retries=2)` with `ModelRetry` for validation failures
2. **Structured Output**: Always use `output_type=PydanticModel` for validated responses
3. **Dynamic Instructions**: Use `@agent.instructions` decorator for context-aware prompts
4. **Tool Descriptions**: Docstrings become tool descriptions for LLM
5. **Dependency Sharing**: Pass `ctx.deps` to delegate agents for shared resources

### Potential Issues ⚠️

1. **Async Dependencies**: All async dependencies must use `async def` functions
2. **Sync Dependencies**: Use regular `def` functions, auto-executed in executor
3. **Tool Validation**: Pydantic validates tool arguments automatically
4. **Error Handling**: `ModelRetry` exceptions trigger agent retry logic

---

## 2. FastAPI (`/fastapi/fastapi`)

### Critical Patterns ✅

**Async Lifespan Management (REQUIRED):**
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_pool = await create_pool()
    app.state.db_pool = db_pool
    yield
    # Shutdown
    await db_pool.close()

app = FastAPI(lifespan=lifespan)
```

**Key Points:**
- ✅ **MUST** migrate from deprecated `@app.on_event()` to `lifespan` pattern
- ✅ Startup code before `yield`, shutdown after `yield`
- ✅ Use `app.state` for shared resources (not global variables)
- ✅ Graceful cleanup for connection pools, background tasks

**Dependency Injection with Yield:**
```python
async def get_db():
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)

@app.get("/items/")
async def read_items(db = Depends(get_db)):
    return await db.fetch("SELECT * FROM items")
```

### SSE Streaming ✅

**Server-Sent Events Pattern:**
```python
from fastapi.responses import StreamingResponse

@app.get("/stream")
async def stream_response():
    async def generate():
        async for chunk in agent.run_stream(...):
            yield f"data: {chunk}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Best Practices ✅

1. **Annotated Dependencies**: Use `Annotated[Type, Depends(func)]` for type safety
2. **Dependency Caching**: Use `use_cache=False` when fresh data needed
3. **Background Tasks**: Use `BackgroundTasks` for post-response work
4. **Error Handling**: HTTPException in dependencies propagates correctly

### Migration Requirements ⚠️

**CRITICAL**: Must migrate from deprecated patterns:
- ❌ `@app.on_event("startup")` → ✅ `lifespan()` context manager
- ❌ `@app.on_event("shutdown")` → ✅ `lifespan()` context manager
- ❌ Global variables → ✅ `app.state` for shared resources

---

## 3. SQLAlchemy 2.0 (`/websites/sqlalchemy_en_20`)

### Critical Patterns ✅

**Async Session with Eager Loading:**
```python
from sqlalchemy.orm import selectinload
from sqlalchemy import select

stmt = select(Session).options(
    selectinload(Session.messages),
    selectinload(Session.account)
)

result = await session.execute(stmt)
session_obj = result.scalars().first()

# Relationships already loaded - no N+1 queries
messages = session_obj.messages  # Already in memory
```

**Key Points:**
- ✅ **MUST** use `selectinload()` to prevent N+1 queries
- ✅ Use `select()` instead of deprecated `session.query()`
- ✅ Async session: `AsyncSession.execute()` not `session.query()`
- ✅ Relationship loading: `selectinload()` vs `joinedload()` vs `subqueryload()`

**Relationship Loading Strategies:**
- `selectinload()` - Separate SELECT IN query (best for collections)
- `joinedload()` - LEFT JOIN (good for single relationships)
- `subqueryload()` - Subquery (alternative for collections)
- `lazyload()` - Default lazy loading (causes N+1!)

### Best Practices ✅

1. **Prevent N+1**: Always use `selectinload()` for collections in loops
2. **Query Optimization**: Use `selectinload()` over `joinedload()` for many-to-many
3. **Async Patterns**: Use `await session.execute(select(...))` not `session.query()`
4. **Expire on Commit**: Set `expire_on_commit=False` for async sessions

### Potential Issues ⚠️

1. **N+1 Queries**: Accessing relationships without eager loading triggers lazy loads
2. **Async Attrs**: Use `await obj.awaitable_attrs.relationship` for lazy-loaded async relationships
3. **Transaction Management**: Use `async with session.begin()` for transactions
4. **Connection Pooling**: Configure pool size for async workloads
5. **Concurrent Operations**: Shared sessions cause "concurrent operations not permitted" errors

### Session-Per-Operation Pattern ✅ **CRITICAL**

**Problem**: Shared database sessions across concurrent operations (parallel tool calls) cause SQLAlchemy errors.

**Solution**: Each operation creates its own session. See [BUG-0023-001](../project-management/bugs-0023.md#bug-0023-001-sqlalchemy-concurrent-operations-error-complete) for full implementation.

```python
# ❌ BAD: Shared session causes concurrent operation errors
deps = SessionDependencies(db_session=session)  # ONE shared
result = await agent.run(prompt, deps=deps)
  ├─ Tool 1: uses ctx.deps.db_session  # CONFLICT
  └─ Tool 2: uses ctx.deps.db_session  # CONFLICT

# ✅ GOOD: Each operation creates independent session
@agent.tool
async def search_directory(ctx: RunContext[SessionDependencies], query: str) -> str:
    async with get_db_session() as session:  # Independent session
        return await service.search(session, query)
```

**Key Points:**
- ✅ **DO NOT** store `db_session` in `SessionDependencies` for tools
- ✅ Tools create own sessions via `get_db_session()` context manager
- ✅ Cost tracking creates own session (not shared)
- ✅ Eliminates concurrent operation errors while preserving parallel execution
- ✅ **Status**: ✅ Implemented and verified (see BUG-0023-001)

---

## 4. Alembic (`/sqlalchemy/alembic`)

### Critical Patterns ✅

**Async Migrations:**
```python
from sqlalchemy.ext.asyncio import async_engine_from_config

def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

**Key Points:**
- ✅ Use `async_engine_from_config()` for async migrations
- ✅ Use `connection.run_sync()` to run sync migration code
- ✅ Configure `target_metadata` for autogenerate
- ✅ Use `render_as_batch=True` for SQLite compatibility

### Best Practices ✅

1. **Autogenerate**: Always review generated migrations before applying
2. **Batch Mode**: Use batch mode for SQLite (via `render_as_batch`)
3. **Transaction Safety**: Use `context.begin_transaction()` for atomic migrations
4. **Multiple Engines**: Configure separate contexts for multiple databases

### Potential Issues ⚠️

1. **Async Support**: Requires `asyncpg` or `aiosqlite` driver
2. **Migration Review**: Autogenerate may miss complex changes
3. **Downgrade**: Always test downgrade paths
4. **Data Migrations**: Use `op.execute()` for custom SQL

---

## 5. Pydantic (`/pydantic/pydantic`)

### Critical Patterns ✅

**Model Validation:**
```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str

# Validation methods
user = User.model_validate({'id': 1, 'name': 'Alice'})
user = User.model_validate_json('{"id": 1, "name": "Alice"}')
user = User.model_validate_strings({'id': '1', 'name': 'Alice'})
```

**Key Points:**
- ✅ Use `model_validate()` for dict input
- ✅ Use `model_validate_json()` for JSON strings
- ✅ Use `model_validate_strings()` for string-coerced input
- ✅ `ValidationError` contains detailed error information

### Best Practices ✅

1. **Type Safety**: Leverage type hints for automatic validation
2. **Field Validators**: Use `@field_validator` for custom validation
3. **Model Validators**: Use `@model_validator` for cross-field validation
4. **Error Handling**: Catch `ValidationError` for user-friendly messages

---

## 6. Pinecone (`/pinecone-io/pinecone-python-client`)

### Critical Patterns ✅

**Query with Metadata Filtering:**
```python
from pinecone import Pinecone

pc = Pinecone(api_key="YOUR_API_KEY")
index = pc.Index(host="YOUR_INDEX_HOST")

query_response = index.query(
    namespace="account-namespace",
    vector=embedding_vector,
    top_k=10,
    include_metadata=True,
    filter={
        "account_id": {"$eq": account_id},
        "status": {"$in": ["active", "published"]}
    }
)
```

**Key Points:**
- ✅ Use `namespace` for multi-tenant isolation
- ✅ Metadata filtering supports operators: `$eq`, `$in`, `$gte`, `$lte`, etc.
- ✅ Use `include_metadata=True` for filtering results
- ✅ Batch operations: Use `upsert()` with list of vectors

### Best Practices ✅

1. **Namespace Isolation**: Use namespace per account for multi-tenancy
2. **Metadata Filtering**: Index frequently-filtered fields
3. **Batch Upserts**: Use batch operations for ingestion (100 vectors/batch)
4. **Query Optimization**: Set `top_k` appropriately (not too high)

### Potential Issues ⚠️

1. **Metadata Indexing**: Only indexed fields can be filtered efficiently
2. **Namespace Management**: Monitor namespace count limits
3. **Vector Dimensions**: Must match index dimension exactly
4. **Rate Limits**: Batch operations to respect API limits

---

## 7. Logfire (`/pydantic/logfire`)

### Critical Patterns ✅

**FastAPI Instrumentation:**
```python
import logfire

logfire.configure()
logfire.instrument_fastapi(app)
logfire.instrument_sqlalchemy(engine=engine)
logfire.instrument_pydantic_ai()
```

**Key Points:**
- ✅ Instrument FastAPI for request/response tracing
- ✅ Instrument SQLAlchemy for query tracing
- ✅ Instrument Pydantic AI for agent tracing
- ✅ Use `logfire.info()` for structured logging

### Best Practices ✅

1. **Early Configuration**: Configure Logfire before instrumenting libraries
2. **Structured Logging**: Use `logfire.info('event.name', key=value)` format
3. **Span Management**: Use `with logfire.span()` for custom tracing
4. **Error Handling**: Exceptions automatically captured in spans

### Potential Issues ⚠️

1. **Diagnostic Logging**: Keep `logfire.instrument_pydantic()` enabled - verbose logs reveal issues
2. **Performance**: Instrumentation adds minimal overhead
3. **Token Required**: Cloud dashboard requires LOGFIRE_TOKEN environment variable

---

## 8. asyncpg (`/magicstack/asyncpg`)

### Critical Patterns ✅

**Connection Pool Management:**
```python
import asyncpg

pool = await asyncpg.create_pool(
    database='postgres',
    user='postgres',
    min_size=10,
    max_size=20,
    max_queries=50000,
    max_inactive_connection_lifetime=300.0,
    command_timeout=60
)

async with pool.acquire() as connection:
    result = await connection.fetchval('SELECT COUNT(*) FROM users')
```

**Key Points:**
- ✅ Use connection pools for web applications
- ✅ Configure `min_size` and `max_size` for pool capacity
- ✅ Use `async with pool.acquire()` for connection management
- ✅ Pool can execute queries directly: `await pool.fetch()`

### Best Practices ✅

1. **Pool Configuration**: Set appropriate min/max sizes for workload
2. **Transaction Management**: Use `async with connection.transaction()` for atomic operations
3. **Query Execution**: Use parameterized queries (`$1`, `$2`) for safety
4. **Lifecycle Management**: Create pool at startup, close at shutdown

### Potential Issues ⚠️

1. **Connection Leaks**: Always use `async with` for connection acquisition
2. **Transaction Isolation**: Understand isolation levels for concurrent access
3. **Pool Sizing**: Too small causes waiting, too large wastes resources
4. **Max Overflow**: Must configure `max_overflow` for burst capacity (see [BUG-0023-003](../project-management/bugs-0023.md#bug-0023-003-connection-pool-sizing--p2))

### Connection Pool Configuration ✅

**SQLAlchemy Engine Configuration:**
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    database_url,
    pool_size=20,           # Base pool size
    max_overflow=10,        # Burst capacity (total: 30 connections)
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

**Key Points:**
- ✅ Set `max_overflow > 0` for burst capacity under concurrent load
- ✅ Use `pool_pre_ping=True` to detect stale connections
- ✅ Configure `pool_recycle` to prevent connection exhaustion
- ⚠️ **Without `max_overflow`**: Pool exhausts under concurrent load (see BUG-0023-003)

---

## Architecture-Specific Recommendations

### Multi-Tenant Pattern ✅

**Account Isolation:**
- **Pinecone**: Use namespace per account
- **PostgreSQL**: Use account_id in WHERE clauses
- **SQLAlchemy**: Use `with_loader_criteria()` for automatic filtering

### Agent Dependency Injection ✅

**SessionDependencies Pattern:**
```python
@dataclass
class SessionDependencies:
    session_id: str
    account_id: int
    account_slug: str
    # db_session removed - tools create own sessions (BUG-0023-001)
    vector_db: PineconeIndex
    config: AgentConfig

agent = Agent('openai:gpt-4o', deps_type=SessionDependencies)

# Tools create independent sessions
@agent.tool
async def search_directory(ctx: RunContext[SessionDependencies], query: str) -> str:
    async with get_db_session() as session:  # Independent session
        return await service.search(session, query)
```

**Important**: Session-per-operation pattern prevents concurrent operation errors. See [BUG-0023-001](../project-management/bugs-0023.md#bug-0023-001-sqlalchemy-concurrent-operations-error-complete) for implementation details.

### Cost Tracking ✅

**Pydantic AI Usage:**
```python
result = await agent.run(prompt, deps=deps)
usage = result.usage()  # RunUsage(input_tokens=..., output_tokens=...)
# Track usage in llm_requests table
```

---

## Migration Checklist

### High Priority ⚠️

- [x] **FastAPI Lifespan**: Migrate from `@app.on_event()` to `lifespan()` context manager ✅ **COMPLETE**
- [x] **SQLAlchemy Queries**: Add `selectinload()` for all relationship accesses ✅ **COMPLETE** (January 12, 2025)
  - **Implementation**: Added selectinload() to all relationship queries across 7 files
  - **Files Updated**: session_service.py, message_service.py, directory_service.py, prompt_generator.py, simple_session_middleware.py, main.py, account_agents.py
  - **Relationships Covered**: Session.account, Session.agent_instance, Message.session, Message.agent_instance, Message.llm_request, DirectoryList.entries, DirectoryList.account, DirectoryEntry.directory_list
  - **Commit**: `c78799a`
  - **Status**: All queries now prevent N+1 issues by eagerly loading relationships
- [ ] **Alembic Async**: Ensure migrations use async engine patterns
- [x] **Pydantic AI**: Verify all tools use `RunContext[DepsType]` pattern ✅ **COMPLETE** (January 12, 2025)
  - **Implementation**: Verified all tool functions use RunContext type annotations
  - **Files Updated**: agent_base.py (tool_wrapper), vector_tools.py (vector_search), directory_tools.py (search_directory)
  - **Status**: All tools verified to use RunContext[SessionDependencies] or RunContext[DepsType]
  - **Commit**: Pending

### Medium Priority 📋

- [ ] **Pinecone Namespaces**: Verify namespace isolation per account
- [ ] **Logfire Instrumentation**: Ensure all libraries instrumented
- [ ] **Connection Pools**: Review pool sizing for production load (add `max_overflow` per BUG-0023-003)
- [ ] **Transaction Management**: Verify all multi-step operations use transactions
- [x] **Session-Per-Operation**: ✅ Complete - All tools create independent sessions (BUG-0023-001)

---

## References

- **Pydantic AI**: `/pydantic/pydantic-ai` (693 code snippets, Trust Score: 9.6)
- **FastAPI**: `/fastapi/fastapi` (845 code snippets, Trust Score: 9.9)
- **SQLAlchemy**: `/websites/sqlalchemy_en_20` (9579 code snippets, Trust Score: 7.5)
- **Alembic**: `/sqlalchemy/alembic` (363 code snippets)
- **Pydantic**: `/pydantic/pydantic` (555 code snippets, Trust Score: 9.6)
- **Pinecone**: `/pinecone-io/pinecone-python-client` (180 code snippets, Trust Score: 9.4)
- **Logfire**: `/pydantic/logfire` (419 code snippets, Trust Score: 9.6)
- **asyncpg**: `/magicstack/asyncpg` (49 code snippets, Trust Score: 7.9)

---

## Next Steps

1. Review current codebase against these patterns
2. Prioritize migration tasks (FastAPI lifespan highest priority)
3. Add `selectinload()` to all relationship queries
4. Verify Pydantic AI dependency injection patterns
5. Test async migration patterns with Alembic

