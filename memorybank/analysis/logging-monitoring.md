<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Production Logging & Monitoring: Logfire

> **Status**: Adopted  
> **Implementation Plan**: `project-management/0017-simple-chat-agent.md` (Priority 2I: 0017-013)

## Decision

Using **Logfire** as the standard observability platform for all logging, tracing, and monitoring.

## Why Logfire

**Technical Fit**:
- Built by Pydantic creators with excellent Python support
- OpenTelemetry-based (open standard, no vendor lock-in)
- Automatic instrumentation for our stack (SQLAlchemy, Pydantic, PydanticAI, FastAPI)
- Structured logging by default (JSON, queryable)
- Distributed tracing across services
- Dual output: console (development) + cloud dashboard (production)

**Cost-Effective**:
- Free tier suitable for early production
- Scales with usage (no upfront enterprise pricing)
- Eliminates need for multiple tools (logging + APM + tracing)
- Reduces maintenance overhead vs self-hosted solutions

**Developer Experience**:
- Simple setup: `logfire.configure()` and `logfire.info()`
- Type-safe structured logging with keyword arguments
- Real-time console output preserved (no loss of visibility)
- Automatic Pydantic model validation tracking
- SQL query tracing without code changes

## Architecture

### Logging Pattern

```python
import logfire

logfire.configure(
    send_to_logfire='if-token-present',  # Cloud only if LOGFIRE_TOKEN set
    console=True  # Always show logs in terminal
)

# Structured logging with dot notation event names
logfire.info('agent.created', model='gpt-4', session_id=session_id)
logfire.error('database.query_failed', table='messages', error=str(e))

# Spans for performance tracking
with logfire.span('database.load_history', session_id=session_id):
    messages = await message_service.get_session_messages(session_id)
```

### Automatic Instrumentation

```python
# Enable automatic tracking for core libraries
logfire.instrument_pydantic()      # Pydantic model validation
logfire.instrument_pydantic_ai()   # LLM agent operations
logfire.instrument_sqlalchemy(engine=engine)  # Database queries
logfire.instrument_starlette(app)  # FastAPI/Starlette requests
```

### Multi-Tenant Observability

Each log and span includes:
- `account_id` - Multi-tenant segmentation
- `agent_instance_id` - Agent-specific filtering
- `session_id` - Trace user conversations
- `llm_request_id` - Link logs to cost tracking

Enables queries like:
- "Show all errors for account acme-corp"
- "Find slow database queries for wyckoff agent"
- "Track cost per customer using session_id"

## Current State

**Using Logfire**:
- `vector_service.py` - Vector search operations
- `directory_tools.py` - Directory search operations
- `prompt_generator.py` - Prompt generation

**Needs Migration**:
- `simple_chat.py` - Uses loguru (high priority)
- Most services in `app/services/` - Uses loguru
- Some legacy modules - Uses standard `logging`

**Target**: All modules use `logfire` exclusively by end of Milestone 1.

## Implementation Phases

**Phase 1** (Current Sprint):
- Migrate `simple_chat.py` to Logfire
- Migrate core services (`message_service.py`, `session_service.py`, `llm_request_tracker.py`)
- Add spans for performance tracking (agent execution, database queries, LLM calls)

**Phase 2** (Next Sprint):
- Migrate remaining services and utilities
- Add custom dashboards in Logfire UI (customer health, error rates, performance)
- Document logging patterns and event naming conventions

**Phase 3** (Future):
- Set up alerting rules (error spikes, performance degradation)
- Configure log retention policies
- Add uptime monitoring for external checks

## Configuration

**Development** (Local):
- Console output enabled (formatted, readable)
- Cloud dashboard optional (set `LOGFIRE_TOKEN` to enable)
- All log levels visible (min_level='trace')

**Production**:
- Console output to stdout (captured by container/systemd logs)
- Cloud dashboard enabled (requires `LOGFIRE_TOKEN`)
- Log level configurable (default 'info', adjustable per environment)
- Structured JSON format for parsing/analytics

## Key Features Utilized

1. **Structured Logging**: Queryable JSON attributes vs unstructured strings
2. **Distributed Tracing**: Follow requests across services and tool calls
3. **SQL Query Tracing**: Automatic capture of database operations
4. **Pydantic Model Tracking**: Validation success/failure metrics
5. **LLM Call Tracing**: Agent execution, tool calls, token usage
6. **Real-Time Dashboard**: Live tail, filtering, search in Logfire UI
7. **Cost Attribution**: Link logs to `llm_requests` table via `llm_request_id`

## Migration Pattern

```python
# BEFORE (loguru)
from loguru import logger
logger.info({"event": "agent_created", "model": model_name})

# AFTER (logfire)
import logfire
logfire.info('agent.created', model=model_name)
```

**Event Naming Convention**:
- Dot notation: `category.action`
- Past tense for completed: `agent.created`, `session.loaded`
- Present tense for ongoing: `agent.creating`, `session.loading`
- Errors: `agent.error`, `session.load_error`

## References

- **Logfire Docs**: https://logfire.pydantic.dev/
- **Implementation Plan**: `project-management/0017-simple-chat-agent.md` (0017-013)
- **Current Workspace Rule**: `.cursorrules/persona.mdc` (diagnostic logging principles)
