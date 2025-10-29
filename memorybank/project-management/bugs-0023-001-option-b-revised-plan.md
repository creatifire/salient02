<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# BUG-0023-001 Option B: Session-per-Operation Architecture (REVISED PLAN)

> **Status**: Ready for Implementation  
> **Based On**: Current library documentation (SQLAlchemy 2.1, FastAPI 0.118, Pydantic AI 1.0)  
> **Original Plan**: `bugs-0023.md` lines 148-197  
> **Date**: October 29, 2025

## Executive Summary

This plan implements session-per-operation architecture to eliminate concurrent database operations errors while preserving parallel tool execution performance. Based on current library best practices and existing codebase architecture.

**Key Insight from Documentation Review**:
- ✅ `get_db_session()` **already exists** in `backend/app/database.py` (line 581)
- ✅ Uses proper FastAPI `yield` pattern with automatic cleanup
- ✅ SQLAlchemy docs confirm: async context managers are the correct pattern
- ✅ Pydantic AI docs confirm: Tools can create their own resources via `ctx.deps`

**What Changed from Original Plan**:
1. Don't create new `get_db_session()` - use existing one from `database.py`
2. Clarified SessionDependencies role - keep other deps, remove `db_session`
3. Added service layer adapter pattern to minimize changes
4. Corrected import paths based on actual codebase structure
5. Added proper error handling with rollback as per SQLAlchemy docs

---

## Current Architecture (Problem)

### Problem Flow:

```python
# 1. Single session created and stored in SessionDependencies
deps = SessionDependencies(
    db_session=session,  # ← ONE shared session
    # ... other dependencies
)

# 2. LLM runs agent with parallel tools
result = await agent.run(prompt, deps=deps)
  ├─ Tool 1: search_directory(ctx) → uses ctx.deps.db_session ← SAME SESSION
  └─ Tool 2: search_directory(ctx) → uses ctx.deps.db_session ← SAME SESSION (💥 CONFLICT!)

# 3. Cost tracking tries to write during tool execution
await llm_request_tracker.track_request(deps.db_session, ...)  # ← SAME SESSION (💥 CONFLICT!)
```

**SQLAlchemy Error**: 
```
This session is provisioning a new connection; concurrent operations are not permitted
(Background: https://sqlalche.me/e/20/isce)
```

---

## Target Architecture (Solution)

### Solution Flow:

```python
# 1. NO shared session in SessionDependencies
deps = SessionDependencies(
    # db_session removed!
    instance_config=config,
    embedding_service=embedding_service,
    # ... other dependencies
)

# 2. Each tool creates its own session
@agent.tool
async def search_directory(ctx: RunContext[SessionDependencies], query: str) -> str:
    async with get_db_session() as session:  # ← NEW independent session
        results = await directory_service.search(session, query)
        return format_results(results)

# 3. Cost tracking creates its own session
async def track_request(...) -> UUID:
    async with get_db_session() as session:  # ← NEW independent session
        llm_request = LLMRequest(...)
        session.add(llm_request)
        await session.commit()
        return llm_request.id
```

**Result**: No conflicts - each operation isolated with its own session from the connection pool

---

## Implementation Plan

### Phase 1: Update SessionDependencies (No Breaking Changes)

**File**: `backend/app/agents/base/dependencies.py`

**Current** (line 116):
```python
@dataclass
class SessionDependencies(BaseDependencies):
    # ... other fields ...
    
    # Database session (for tool data access)
    db_session: Optional[Any] = None  # ← REMOVE THIS
```

**After**:
```python
@dataclass
class SessionDependencies(BaseDependencies):
    # ... other fields ...
    
    # Database session REMOVED - tools create their own sessions
    # This eliminates shared session conflicts during parallel tool execution
    # See: bugs-0023.md BUG-0023-001 for rationale
    
    # Keep all other dependencies:
    instance_config: Optional[Dict[str, Any]] = None
    embedding_service: Optional[Any] = None
    agent_instance_id: Optional[int] = None
    account_id: Optional[UUID] = None
    # ... etc
```

**Why This Works**:
- `db_session` is already `Optional[Any] = None` - removing it is backward compatible
- Existing code that doesn't use `db_session` continues working
- Tools that need database access will use new pattern

---

### Phase 2: Update Tools to Create Own Sessions

**File**: `backend/app/agents/tools/directory_tools.py`

**Import Statement** (add at top):
```python
from backend.app.database import get_db_session  # Existing function from database.py
```

**Current Pattern**:
```python
@agent.tool
async def search_directory(
    ctx: RunContext[SessionDependencies],
    query: str,
    schema_name: str,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """Search directory for entries matching query."""
    
    # OLD: Uses shared session from dependencies
    session = ctx.deps.db_session  # ← PROBLEM: shared session
    
    results = await directory_service.search(
        session=session,
        schema_name=schema_name,
        query=query,
        filters=filters
    )
    
    return format_results(results)
```

**New Pattern** (Following SQLAlchemy + FastAPI docs):
```python
@agent.tool
async def search_directory(
    ctx: RunContext[SessionDependencies],
    query: str,
    schema_name: str,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """Search directory for entries matching query."""
    
    # NEW: Create independent session for this tool
    # Follows FastAPI dependency pattern from official docs
    async with get_db_session() as session:
        try:
            results = await directory_service.search(
                session=session,
                schema_name=schema_name,
                query=query,
                filters=filters
            )
            
            # Format and return results
            return format_results(results)
            
        except Exception as e:
            # Session auto-rolls back via context manager
            # Re-raise for agent error handling
            logfire.error("search_directory_failed", error=str(e))
            raise
```

**What This Does** (per SQLAlchemy docs):
1. `async with get_db_session() as session:` - Creates new session from pool
2. Tool executes query using its own session
3. Exception → automatic rollback (context manager `__aexit__`)
4. Success/Failure → automatic `session.close()` (returns connection to pool)
5. No conflicts with other parallel tools or cost tracking

**Apply Same Pattern To**:
- `backend/app/agents/tools/vector_tools.py` (if using db_session)
- `backend/app/agents/tools/profile_tools.py` (if exists and uses db_session)
- Any other `@agent.tool` functions accessing database

---

### Phase 3: Update Cost Tracking (Critical)

**File**: `backend/app/services/llm_request_tracker.py`

**Current** (approximate):
```python
class LLMRequestTracker:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session  # ← PROBLEM: shared session
    
    async def track_request(
        self,
        session_id: UUID,
        provider: str,
        model: str,
        # ... other params
    ) -> UUID:
        llm_request = LLMRequest(...)
        self.db_session.add(llm_request)
        await self.db_session.commit()
        return llm_request.id
```

**New Pattern**:
```python
from backend.app.database import get_db_session

class LLMRequestTracker:
    # Remove db_session from __init__ - create sessions per operation instead
    def __init__(self):
        pass  # No shared session needed
    
    async def track_request(
        self,
        session_id: UUID,
        provider: str,
        model: str,
        request_body: dict,
        response_body: dict,
        tokens: dict,
        cost_data: dict,
        latency_ms: int,
        agent_instance_id: UUID,
        account_id: UUID,
        account_slug: str,
        agent_instance_slug: str,
        agent_type: str,
        completion_status: str = "complete"
    ) -> UUID:
        """Track LLM request with its own database session."""
        
        # Create independent session for cost tracking
        async with get_db_session() as session:
            try:
                llm_request = LLMRequest(
                    id=uuid4(),
                    session_id=session_id,
                    provider=provider,
                    model=model,
                    request_body=request_body,
                    response_body=response_body,
                    prompt_tokens=tokens.get("prompt", 0),
                    completion_tokens=tokens.get("completion", 0),
                    total_tokens=tokens.get("total", 0),
                    prompt_cost=cost_data.get("prompt_cost", 0.0),
                    completion_cost=cost_data.get("completion_cost", 0.0),
                    total_cost=cost_data.get("total_cost", 0.0),
                    latency_ms=latency_ms,
                    agent_instance_id=agent_instance_id,
                    account_id=account_id,
                    account_slug=account_slug,
                    agent_instance_slug=agent_instance_slug,
                    agent_type=agent_type,
                    completion_status=completion_status,
                    created_at=datetime.now(UTC)
                )
                
                session.add(llm_request)
                await session.commit()
                
                # IMPORTANT: Refresh to get the ID after commit
                await session.refresh(llm_request)
                
                logfire.info(
                    "llm_request_tracked",
                    llm_request_id=str(llm_request.id),
                    total_cost=cost_data.get("total_cost", 0.0)
                )
                
                return llm_request.id
                
            except Exception as e:
                # Session auto-rolls back via context manager
                logfire.error("cost_tracking_failed", error=str(e))
                raise
```

**Key Changes**:
1. Remove `db_session` from constructor
2. Create session inside `track_request()` method
3. Use `async with` for automatic cleanup
4. Add logging for success/failure
5. Proper exception handling (rollback automatic)

---

### Phase 4: Update Callers of LLMRequestTracker

**File**: `backend/app/agents/simple_chat.py`

**Current** (approximate):
```python
# Initialize tracker with shared session
llm_request_tracker = LLMRequestTracker(db_session=deps.db_session)

# Track request
llm_request_id = await llm_request_tracker.track_request(...)
```

**New**:
```python
# Initialize tracker without session
llm_request_tracker = LLMRequestTracker()

# Track request - creates its own session internally
llm_request_id = await llm_request_tracker.track_request(...)
```

**Files to Update**:
- `backend/app/agents/simple_chat.py` (line ~800 in `simple_chat_stream()`)
- `backend/app/agents/simple_chat.py` (line ~400 in `simple_chat()`)
- Any other files creating `LLMRequestTracker` instances

---

### Phase 5: Update Service Layer (If Needed)

**Assessment**: Check if services expect session to be passed:

**Current Service Pattern** (example):
```python
class DirectoryService:
    async def search(
        self,
        session: AsyncSession,  # ← Session passed as parameter
        schema_name: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        result = await session.execute(...)
        return result.scalars().all()
```

**Action**: 
- ✅ **Keep this pattern** - it's correct and flexible
- Services that accept session as parameter work perfectly with new tool pattern
- No changes needed to service layer

**Why This Works**:
- Tools create session: `async with get_db_session() as session:`
- Tools pass session to services: `await service.search(session, ...)`
- Service uses the session provided by the tool
- Each tool call gets independent session
- No conflicts possible

---

## Service Initialization Pattern

**File**: `backend/app/agents/simple_chat.py` (or wherever deps are created)

**Before** (creates shared session):
```python
async def create_session_dependencies(
    session_id: str,
    instance_config: Dict[str, Any],
    # ...
) -> SessionDependencies:
    # OLD: Create shared database session
    db_service = get_database_service()
    async with db_service.get_session() as db_session:  # ← Creates shared session
        
        deps = SessionDependencies(
            session_id=session_id,
            db_session=db_session,  # ← PROBLEM
            instance_config=instance_config,
            # ...
        )
        
        # Agent runs with this shared session
        result = await agent.run(prompt, deps=deps)
        return result
```

**After** (no shared session):
```python
async def create_session_dependencies(
    session_id: str,
    instance_config: Dict[str, Any],
    # ...
) -> SessionDependencies:
    # NEW: No shared session needed
    deps = SessionDependencies(
        session_id=session_id,
        # db_session removed!
        instance_config=instance_config,
        embedding_service=get_embedding_service(),
        agent_instance_id=instance_config.get("id"),
        account_id=session.account_id,
        # ... other dependencies
    )
    
    # Agent runs - tools create their own sessions as needed
    result = await agent.run(prompt, deps=deps)
    return result
```

---

## Connection Pool Considerations

**Current Configuration** (`backend/app/database.py` line 188-203):
```python
self._engine = create_async_engine(
    database_url,
    pool_size=20,        # Persistent connections
    max_overflow=0,      # ← Change to 10 per BUG-0023-003
    pool_timeout=30,
    pool_pre_ping=True,
    echo=False,
)
```

**Recommendation**: Implement BUG-0023-003 (connection pool sizing) **after** this fix:
- Current: 20 persistent, 0 overflow = max 20 concurrent operations
- After BUG-0023-001 fix: Each tool + cost tracking = 3 sessions per request
- With overflow: 20 + 10 = 30 total capacity = 10 parallel tool requests safely

**Why Wait**:
- Don't mask the root cause by increasing pool size first
- Fix session management architecture first
- Then optimize pool sizing based on actual concurrent load

---

## Testing Strategy

### Pre-Implementation Test (Reproduce Bug)

**Script**: `tests/manual/test_parallel_tool_bug.py`
```python
"""
Test to reproduce BUG-0023-001: Concurrent operations error
"""
import asyncio
from backend.app.agents.simple_chat import create_simple_chat_agent
from backend.app.agents.base.dependencies import SessionDependencies
from backend.app.database import initialize_database

async def test_parallel_tools():
    """Send message that triggers parallel tool calls."""
    
    await initialize_database()
    
    # Create agent
    agent = create_simple_chat_agent()
    
    # Create dependencies with shared session (OLD WAY)
    deps = SessionDependencies(
        session_id="test-session",
        db_session=shared_session,  # PROBLEM
        # ...
    )
    
    # Send prompt that triggers parallel tools
    result = await agent.run(
        "Find me cardiologists in Seattle who accept Medicare",
        deps=deps
    )
    
    # Check logs for error
    # Expected: "concurrent operations not permitted"

if __name__ == "__main__":
    asyncio.run(test_parallel_tools())
```

**Expected Before Fix**:
```
ERROR: Cost tracking failed (non-critical): This session is provisioning a new connection; concurrent operations are not permitted
llm_request_id: None
```

### Post-Implementation Test (Verify Fix)

**Same script, updated for new architecture**:
```python
async def test_parallel_tools_fixed():
    """Verify parallel tool calls work without errors."""
    
    await initialize_database()
    
    # Create agent
    agent = create_simple_chat_agent()
    
    # Create dependencies WITHOUT shared session (NEW WAY)
    deps = SessionDependencies(
        session_id="test-session",
        # db_session removed!
        instance_config=config,
        # ...
    )
    
    # Send prompt that triggers parallel tools
    result = await agent.run(
        "Find me cardiologists in Seattle who accept Medicare",
        deps=deps
    )
    
    # Check logs for success
    # Expected: No concurrent operations errors
    # Expected: llm_request_id is valid UUID

if __name__ == "__main__":
    asyncio.run(test_parallel_tools_fixed())
```

**Expected After Fix**:
```
INFO: search_directory called (tool_instance_1)
INFO: search_directory called (tool_instance_2)
INFO: llm_request_tracked, llm_request_id: 'a1b2c3d4-...', total_cost: 0.00123
SUCCESS: result='Found 5 cardiologists...'
```

### SQL Verification

```sql
-- Verify cost tracking worked
SELECT 
    id,
    account_slug,
    agent_instance_slug,
    model,
    total_cost,
    completion_status,
    created_at
FROM llm_requests
WHERE session_id = 'test-session'
ORDER BY created_at DESC;

-- Expected: 1 row with valid UUID id and non-zero cost
```

---

## Migration Checklist

### Files to Modify (in order):

1. ✅ **`backend/app/agents/base/dependencies.py`**
   - Remove `db_session: Optional[Any] = None` from SessionDependencies
   - Add comment explaining why

2. ✅ **`backend/app/services/llm_request_tracker.py`**
   - Remove `db_session` from `__init__`
   - Update `track_request()` to create own session
   - Add proper error handling

3. ✅ **`backend/app/agents/simple_chat.py`**
   - Remove shared session creation from dependency setup
   - Update LLMRequestTracker initialization (remove db_session argument)
   - Update both `simple_chat()` and `simple_chat_stream()` functions

4. ✅ **`backend/app/agents/tools/directory_tools.py`**
   - Add `from backend.app.database import get_db_session` import
   - Update `@agent.tool` functions to create own sessions
   - Add error handling

5. ✅ **`backend/app/agents/tools/vector_tools.py`** (if applicable)
   - Same pattern as directory_tools.py

6. ⚠️ **Any other files importing SessionDependencies**
   - Search codebase: `grep -r "deps.db_session" backend/`
   - Update each occurrence to use new pattern

### Testing Checklist:

- [ ] Pre-implementation test reproduces bug
- [ ] All modified files pass linting
- [ ] Unit tests updated (if any exist for affected components)
- [ ] Manual test: Wyckoff agent with parallel tool calls
- [ ] Manual test: AgroFresh agent with single tool call
- [ ] SQL verification: llm_requests table populated correctly
- [ ] Logfire verification: No concurrent operations errors
- [ ] Performance test: Compare parallel vs sequential tool timing

### Rollback Plan:

If issues discovered:
1. Revert changes to `dependencies.py` (restore `db_session` field)
2. Revert changes to `llm_request_tracker.py` (restore shared session)
3. Revert changes to tools (restore `ctx.deps.db_session` usage)
4. Deploy rollback immediately
5. Investigate root cause before retry

---

## Expected Outcomes

### Before Fix:
- ❌ Parallel tool calls → concurrent operations error
- ❌ Cost tracking fails → `llm_request_id: None`
- ❌ No billing data in database
- ❌ Audit trail gaps

### After Fix:
- ✅ Parallel tool calls complete successfully
- ✅ Cost tracking succeeds → `llm_request_id: <UUID>`
- ✅ Complete billing data in database
- ✅ All denormalized fields populated
- ✅ No performance regression (parallel still faster)

### Performance Expectations:
- Tool execution time: Same (parallel: ~2.4s, sequential would be ~4.8s)
- Connection pool: Sufficient with current 20 + 0 overflow (increase later per BUG-0023-003)
- Memory: Slight increase (3 sessions per request instead of 1, but sessions are lightweight)
- Latency: No measurable change (connection pool handles session creation efficiently)

---

## Documentation Updates

After successful implementation:

1. **Update `bugs-0023.md`**:
   - Mark BUG-0023-001 as ✅ **FIXED**
   - Add implementation date and commit hash
   - Add verification test results

2. **Update `memorybank/architecture/pydantic-ai-patterns.md`** (if exists):
   - Document session-per-operation pattern
   - Add best practices for tool database access

3. **Update `memorybank/architecture/database-patterns.md`** (if exists):
   - Document connection pool usage
   - Explain session lifecycle in agent context

---

## References

### SQLAlchemy Documentation (Version 2.1):
- **Async Sessions**: https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio
- **Context Managers**: Section "Using AsyncSession with async context managers"
- **Key Quote**: "AsyncSession should be used as an async context manager to ensure proper cleanup"
- **Pattern Used**: `async with async_sessionmaker(bind=engine) as session:`

### FastAPI Documentation (Version 0.118):
- **Database Dependencies**: https://github.com/fastapi/fastapi/blob/master/docs/en/docs/tutorial/sql-databases.md
- **Dependencies with Yield**: Section "A database dependency with yield"
- **Key Quote**: "The code before yield runs before the response, and the code after yield runs after the response"
- **Pattern Used**: `async def get_db_session() -> AsyncGenerator[AsyncSession, None]:`

### Pydantic AI Documentation (Version 1.0):
- **Dependencies**: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md
- **RunContext**: Section "Access Agent Dependencies via RunContext"
- **Key Quote**: "Dependencies are accessed through the RunContext object via the .deps attribute"
- **Pattern Used**: `async def my_tool(ctx: RunContext[MyDeps], ...) -> str:`

---

**Status**: Ready for Implementation  
**Estimated Effort**: 2-3 days (dev + testing)  
**Risk Level**: Medium (requires testing across multiple agents)  
**Priority**: P0 (blocking billing data, revenue loss)


