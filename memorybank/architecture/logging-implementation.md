<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Logging Implementation Guide

> **Status**: Production  
> **Last Updated**: January 2025  
> **Migration**: Completed (Priority 11)

Complete guide to implementing Logfire-based logging across the application, including patterns, conventions, and critical lessons learned.

---

## Quick Reference

| Task | Pattern |
|------|---------|
| **Import** | `import logfire` |
| **Simple log** | `logfire.info('event.name', key=value)` |
| **Exception** | `logfire.exception('event.error')` |
| **Span** | `with logfire.span('operation'):` |
| **Safe logging** | `from app.utils.logfire_safe import safe_logfire_error` |

---

## Why Logfire

### Technical Advantages

**Native Python Integration**:
- Built by Pydantic creators for Python/FastAPI stacks
- Zero-config auto-instrumentation for our libraries
- Type-safe structured logging
- OpenTelemetry standard (no vendor lock-in)

**Developer Experience**:
- Simple API: `logfire.info('event', key=value)`
- Real-time console + cloud dashboard
- Queryable structured data (no regex parsing)
- Automatic distributed tracing

**Cost-Effective**:
- Free tier for development/small production
- Pay-as-you-grow pricing
- Single tool replaces logging + APM + tracing
- Reduced infrastructure overhead

---

## Configuration

### Setup (`backend/app/main.py`)

```python
import logfire

# Configure once at application startup
logfire.configure()

# Enable automatic instrumentation
logfire.instrument_fastapi(app)
logfire.instrument_pydantic_ai()
logfire.instrument_pydantic()
```

### Environment Variables

```bash
# Required for cloud dashboard (optional for local dev)
LOGFIRE_TOKEN=your_token_here

# Project configuration (automatically detected)
# LOGFIRE_PROJECT_NAME=salient-dev
```

### Built-in Integrations

Logfire automatically instruments:

| Library | What It Captures | Setup |
|---------|------------------|-------|
| **FastAPI** | HTTP requests, responses, errors | `logfire.instrument_fastapi(app)` |
| **Pydantic AI** | Agent runs, tool calls, LLM usage | `logfire.instrument_pydantic_ai()` |
| **Pydantic** | Model validation, errors | `logfire.instrument_pydantic()` |
| **SQLAlchemy** | Database queries, performance | `logfire.instrument_sqlalchemy(engine)` |
| **AsyncPG** | PostgreSQL operations | Automatic via OpenTelemetry |
| **HTTPX** | External API calls | Automatic via OpenTelemetry |

**No code changes required** - instrumentation is automatic once enabled.

---

## Event Naming Convention

### Pattern: `category.subcategory.action`

**Examples**:
```python
# Agent operations
logfire.info('agent.chat.request')
logfire.info('agent.chat.response')
logfire.error('agent.chat.failed')

# Service operations
logfire.info('service.llm_tracker.tracked')
logfire.info('service.message.saved')

# Database operations
logfire.info('database.session.loaded')
logfire.error('database.query.failed')

# Tool operations
logfire.info('tool.directory.search_complete')
logfire.info('tool.vector.query_complete')
```

### Guidelines

- **Use dots** for hierarchy (not underscores)
- **Past tense** for completed actions
- **Failed/error** suffix for errors
- **3 levels max** (category.subcategory.action)
- **Lowercase** only

---

## Structured Logging Patterns

### Basic Logging

```python
import logfire

# Simple event
logfire.info('agent.created')

# With structured data
logfire.info(
    'agent.created',
    model='gpt-4',
    session_id=session_id,
    account_id=account_id
)

# Different levels
logfire.debug('agent.config.loaded', config_keys=list(config.keys()))
logfire.warn('agent.fallback_mode', reason='no_api_key')
logfire.error('agent.creation_failed', error=str(e))
```

### Multi-Tenant Context

**Always include** for multi-tenant operations:

```python
logfire.info(
    'event.name',
    account_id=account_id,           # Required
    account_slug=account_slug,       # Required
    session_id=session_id,           # For session operations
    agent_instance_id=instance_id    # For agent operations
)
```

These attributes enable filtering:
- "Show all logs for account X"
- "Find errors in agent Y"
- "Trace conversation Z"

### Performance Spans

For operations > 100ms:

```python
with logfire.span('database.load_history', session_id=session_id):
    messages = await message_service.get_session_messages(session_id)
    # Automatically tracks duration

async with db_service.get_session() as session:
    with logfire.span('database.query', table='sessions'):
        result = await session.execute(query)
```

**When to use spans**:
- Database queries
- External API calls
- LLM requests
- File I/O operations
- Complex calculations

---

## Exception Handling

### Standard Pattern

```python
try:
    result = await risky_operation()
except Exception as e:
    logfire.exception(
        'operation.failed',
        session_id=session_id,
        additional_context=value
    )
    raise  # Re-raise if needed
```

`logfire.exception()` automatically includes:
- Exception type
- Exception message
- Full stack trace
- All structured attributes

### SQLAlchemy-Safe Logging

**Problem**: SQLAlchemy expressions can't be serialized for logging.

**Solution**: Use safe wrappers from `logfire_safe.py`:

```python
from backend.app.utils.logfire_safe import safe_logfire_error

# Instead of:
# logfire.error('event', value=might_be_sqlalchemy_expression)

# Use:
safe_logfire_error('event', value=might_be_sqlalchemy_expression)
```

**When to use**:
- Error paths where values might be SQLAlchemy expressions
- Logging database model attributes outside session context
- Any uncertain data from ORM operations

**Available wrappers**:
- `safe_logfire_info()`
- `safe_logfire_warn()`
- `safe_logfire_error()`
- `safe_logfire_exception()`

---

## Migration Guide

### Step-by-Step

1. **Remove old imports**:
```python
# Remove:
from loguru import logger
import logging
logger = logging.getLogger(__name__)
```

2. **Add Logfire**:
```python
# Add:
import logfire
```

3. **Replace logger calls**:
```python
# Before:
logger.info(f"Processing session {session_id}")
logger.error(f"Failed to load: {error}")

# After:
logfire.info('session.processing', session_id=session_id)
logfire.error('session.load_failed', error=str(error))
```

4. **Convert f-strings to structured attributes**:
```python
# Before:
logger.info(f"Agent {agent_id} created with model {model}")

# After:
logfire.info('agent.created', agent_id=agent_id, model=model)
```

5. **Use hierarchical event names**:
```python
# Before:
logger.info("cost_tracked")

# After:
logfire.info('service.llm_tracker.tracked')
```

### Complete Example

**Before (Loguru)**:
```python
from loguru import logger

class MessageService:
    async def save_message(self, session_id, content):
        logger.info(f"Saving message for session {session_id}")
        try:
            result = await self.db.save(content)
            logger.info(f"Message saved: {result.id}")
            return result
        except Exception as e:
            logger.error(f"Save failed: {e}")
            raise
```

**After (Logfire)**:
```python
import logfire

class MessageService:
    async def save_message(self, session_id, content):
        logfire.info('service.message.saving', session_id=session_id)
        try:
            with logfire.span('database.save', table='messages'):
                result = await self.db.save(content)
            logfire.info('service.message.saved', 
                        session_id=session_id, 
                        message_id=result.id)
            return result
        except Exception as e:
            logfire.exception('service.message.save_failed', 
                            session_id=session_id)
            raise
```

---

## Critical Issues & Solutions

### SQLAlchemy Expression Serialization

**Problem**: 
```python
# This crashes:
if combined_ts_query:  # TypeError: Boolean value not defined
    ...
```

**Root Cause**: SQLAlchemy expressions can't be evaluated as booleans.

**Solutions**:

1. **Check for None explicitly**:
```python
# Instead of:
if combined_ts_query:

# Use:
if combined_ts_query is not None:
```

2. **Use direct column queries**:
```python
# Instead of accessing model attributes:
account_id = session_record.account_id  # Might be expression

# Query columns directly:
stmt = select(Session.account_id).where(Session.id == session_id)
result = await db_session.execute(stmt)
account_id = result.scalar()  # Guaranteed Python primitive
```

3. **Use safe logging wrappers**:
```python
from backend.app.utils.logfire_safe import safe_logfire_error
safe_logfire_error('event', value=potentially_unsafe)
```

**Files to Reference**:
- `backend/app/utils/logfire_safe.py` - Safe wrappers
- `backend/app/services/session_extractor.py` - Direct query pattern
- `memorybank/project-management/bugs-0023-005-sqlalchemy-expression-serialization.md` - Full analysis

---

## Testing & Verification

### Local Development

1. **Console Output**: Check terminal for structured logs
2. **Logfire Dashboard**: Visit https://logfire-us.pydantic.dev/
3. **Filter by event**: Search for specific event names
4. **Check spans**: Verify performance tracking

### Production Monitoring

```python
# Via MCP Logfire integration
from mcp_logfire import arbitrary_query

# Query recent errors
SELECT span_name, exception_type, exception_message
FROM records
WHERE exception_type IS NOT NULL
  AND start_timestamp > NOW() - INTERVAL '15 minutes'
```

### Verification Checklist

After migration:
- [ ] No `loguru` or `logging` imports remain
- [ ] All logs use hierarchical event names
- [ ] Multi-tenant attributes included where needed
- [ ] Exceptions use `logfire.exception()`
- [ ] Spans track long-running operations
- [ ] No errors in Logfire dashboard

---

## Best Practices

### DO

✅ Use structured attributes instead of f-strings  
✅ Include multi-tenant context (account_id, session_id)  
✅ Use spans for operations > 100ms  
✅ Check SQLAlchemy expressions with `is not None`  
✅ Use hierarchical event naming  
✅ Log at appropriate levels (info for normal, error for failures)

### DON'T

❌ Use f-strings for structured data  
❌ Log sensitive data (passwords, API keys, PII)  
❌ Evaluate SQLAlchemy expressions in boolean context  
❌ Over-log in hot paths (loops processing many items)  
❌ Use generic event names ("processing", "done")  
❌ Mix logging libraries (use Logfire only)

---

## Performance Considerations

**Low Overhead**:
- Logfire is async and non-blocking
- Minimal impact on request latency
- Automatic sampling in high-volume scenarios

**When to Be Careful**:
- Tight loops (log once before/after, not per iteration)
- Hot paths (use debug level for verbose logs)
- Large data (log counts/sizes, not full content)

**Example**:
```python
# Bad: Logs N times
for item in items:
    logfire.debug('processing.item', item=item)

# Good: Log once
logfire.info('processing.batch', count=len(items))
for item in items:
    process(item)
logfire.info('processing.complete', processed=len(items))
```

---

## Current State

**✅ Completed Migration** (Priority 11):

**Phase 1: Core Agent & Tools**
- `simple_chat.py`
- `vector_tools.py`
- `vector_service.py`
- `directory_tools.py`

**Phase 2: Services**
- `message_service.py`
- `session_service.py`
- `llm_request_tracker.py`
- `directory_service.py`
- `directory_importer.py`
- `agent_pinecone_config.py`
- `pinecone_client.py`
- `embedding_service.py`

**Phase 3: Middleware**
- `simple_session_middleware.py`
- `session_middleware.py`

**Phase 4: API Routes**
- `account_agents.py`
- `agents.py`

**⏳ Pending Migration** (Phase 5):
- `main.py` - Remove `_setup_logger()` function
- `database.py`
- `config_loader.py`
- `instance_loader.py`
- `cascade_monitor.py`

---

## Related Documentation

**Architecture**:
- [Agent & Tool Design](./agent-and-tool-design.md) - Development patterns
- [Multi-Tenant Security](./multi-tenant-security.md) - Security logging
- [Pydantic AI Cost Tracking](./pydantic-ai-cost-tracking.md) - Cost attribution

**Implementation**:
- [Priority 11: Logging Consolidation](../project-management/0000-approach-milestone-01.md) - Migration plan
- [BUG-0023-005](../project-management/bugs-0023-005-sqlalchemy-expression-serialization.md) - SQLAlchemy issues

**External**:
- [Logfire Documentation](https://logfire.pydantic.dev/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)

---

## Support

**Questions or Issues?**
1. Check this guide first
2. Review related documentation above
3. Search Logfire dashboard for similar patterns
4. Check `backend/app/utils/logfire_safe.py` for examples

