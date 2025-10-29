<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# BUG-0023-001 Option B: Session-per-Operation (Implementation Plan)

> **Status**: Ready  
> **Based On**: SQLAlchemy 2.1, FastAPI 0.118, Pydantic AI 1.0  
> **Date**: October 29, 2025

## Summary

Session-per-operation architecture eliminates concurrent DB errors while preserving parallel tool execution.

**Key Findings**:
- `get_db_session()` exists in `backend/app/database.py:581` (use it, don't create new)
- SQLAlchemy docs confirm: async context managers are the pattern
- Services already accept session as parameter (no changes needed)

**Changes**:
1. Remove `db_session` from SessionDependencies
2. Tools create own sessions via `get_db_session()`
3. Cost tracking creates own session
4. No service layer changes needed

---

## Problem → Solution

**Before** (shared session):
```python
deps = SessionDependencies(db_session=session)  # ONE shared
result = await agent.run(prompt, deps=deps)
  ├─ Tool 1: uses ctx.deps.db_session  # CONFLICT
  └─ Tool 2: uses ctx.deps.db_session  # CONFLICT
```

**After** (independent sessions):
```python
deps = SessionDependencies(...)  # No db_session

@agent.tool
async def search_directory(...):
    async with get_db_session() as session:  # Independent
        return await service.search(session, ...)
```

---

## Implementation

### Phase 1: SessionDependencies

**File**: `backend/app/agents/base/dependencies.py:116`

Remove:
```python
db_session: Optional[Any] = None  # DELETE THIS LINE
```

Add comment:
```python
# db_session removed - tools create own sessions (BUG-0023-001)
```

---

### Phase 2: Tools

**File**: `backend/app/agents/tools/directory_tools.py`

```python
from backend.app.database import get_db_session

@agent.tool
async def search_directory(
    ctx: RunContext[SessionDependencies],
    query: str,
    schema_name: str,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    async with get_db_session() as session:
        try:
            results = await directory_service.search(
                session, schema_name, query, filters
            )
            return format_results(results)
        except Exception as e:
            logfire.error("search_directory_failed", error=str(e))
            raise
```

**Apply to**: All `@agent.tool` functions using database

---

### Phase 3: Cost Tracking

**File**: `backend/app/services/llm_request_tracker.py`

```python
from backend.app.database import get_db_session

class LLMRequestTracker:
    def __init__(self):
        pass  # No session
    
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
                await session.refresh(llm_request)
                
                logfire.info("llm_request_tracked",
                    llm_request_id=str(llm_request.id),
                    total_cost=cost_data.get("total_cost", 0.0))
                
                return llm_request.id
                
            except Exception as e:
                logfire.error("cost_tracking_failed", error=str(e))
                raise
```

---

### Phase 4: Update Callers

**File**: `backend/app/agents/simple_chat.py` (~lines 400, 800)

```python
# Before
llm_request_tracker = LLMRequestTracker(db_session=deps.db_session)

# After
llm_request_tracker = LLMRequestTracker()
```

---

### Phase 5: Service Layer

**No changes needed**. Services already accept session as parameter:

```python
class DirectoryService:
    async def search(self, session: AsyncSession, ...) -> List[Dict]:
        # Uses provided session
```

Tools pass session: `await service.search(session, ...)`

---

## Testing

### Pre-Fix (Reproduce)
```bash
# Send message triggering 2+ tool calls
# Check logs for "concurrent operations not permitted"
# Verify llm_request_id: None
```

### Post-Fix (Verify)
```bash
# Apply changes, restart
# Send message triggering 2+ tool calls
# Verify no errors, llm_request_id is UUID
```

### SQL Verification
```sql
SELECT id, account_slug, model, total_cost, completion_status
FROM llm_requests
WHERE session_id = '<test_session_id>'
ORDER BY created_at DESC;
-- Expected: 1 row with valid UUID, non-zero cost
```

---

## Checklist

### Files to Modify
1. `backend/app/agents/base/dependencies.py` - Remove `db_session`
2. `backend/app/services/llm_request_tracker.py` - Create own session
3. `backend/app/agents/simple_chat.py` - Update tracker init
4. `backend/app/agents/tools/directory_tools.py` - Create own sessions
5. `backend/app/agents/tools/vector_tools.py` - If using db_session

### Testing
- [ ] Reproduces bug (pre-fix)
- [ ] Linting passes
- [ ] Wyckoff agent (parallel tools)
- [ ] AgroFresh agent (single tool)
- [ ] SQL: llm_requests populated
- [ ] Logfire: No errors

### Rollback
If issues: revert all changes, redeploy immediately.

---

## Expected Results

**Before**: Cost tracking fails, llm_request_id: None, lost billing  
**After**: Cost tracking succeeds, llm_request_id: UUID, complete billing

**Performance**: Same (parallel: ~2.4s, sequential would be ~4.8s)

---

## References

- **SQLAlchemy 2.1**: [Async Sessions](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio)
- **FastAPI 0.118**: [Database Dependencies](https://github.com/fastapi/fastapi/blob/master/docs/en/docs/tutorial/sql-databases.md)
- **Pydantic AI 1.0**: [Dependencies](https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md)

---

**Effort**: 2-3 days | **Risk**: Medium | **Priority**: P0
