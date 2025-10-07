# Chat Endpoints & Pydantic AI Implementation Matrix

> **Last Updated**: October 7, 2025

## Overview

This document provides a comprehensive view of all chat endpoints, which frontend clients use them, and whether they properly use Pydantic AI for LLM interactions.

## 🎯 Core Principle

**ALL LLM interactions MUST use Pydantic AI.** Any endpoint marked ❌ below violates this principle and needs migration.

---

## Chat Endpoints & Client Matrix

| Endpoint | Method | Uses Pydantic AI? | LLM Cost Tracking? | Frontend Clients | Implementation | Status |
|----------|--------|-------------------|-------------------|------------------|----------------|---------|
| `/` | `GET` | N/A | N/A | Browser (localhost:8000) | Serves HTML page | ✅ Working |
| `/events/stream` | `GET` | ❌ **NO** | ❌ **NO** | localhost:8000<br>HTMX demos<br>Shadow DOM widget<br>Iframe demo | Direct HTTP via `openrouter_client.py`<br>`stream_chat_chunks()` | 🚨 **NEEDS MIGRATION** |
| `/chat` | `POST` | ❌ **NO** | ❌ **NO** | HTMX demos (fallback)<br>Widget (fallback) | Direct HTTP via `openrouter_client.py`<br>`chat_completion_content()` | 🚨 **NEEDS MIGRATION** |
| `/agents/simple-chat/chat` | `POST` | ✅ **YES** | ✅ **YES** | Astro simple-chat demo<br>(localhost:4321/demo/simple-chat) | Pydantic AI via `simple_chat()` agent | ✅ **CORRECT** |

---

## Frontend Client Details

| Client | Location | Primary Endpoint | Pydantic AI? | Notes |
|--------|----------|------------------|--------------|-------|
| **Backend Main Chat** | `localhost:8000`<br>`backend/templates/index.html` | `/events/stream` (SSE)<br>`/chat` (fallback) | ❌ **NO** | 🚨 Legacy - needs migration |
| **Astro Simple Chat Demo** | `localhost:4321/demo/simple-chat`<br>`web/src/pages/demo/simple-chat.astro` | `/agents/simple-chat/chat` | ✅ **YES** | ✅ Correct implementation |
| **HTMX Chat Demo (Astro)** | `localhost:4321/demo/htmx-chat`<br>`web/src/pages/demo/htmx-chat.astro` | `/events/stream` (SSE)<br>`/chat` (fallback) | ❌ **NO** | 🚨 Demo - needs migration |
| **HTMX Chat Demo (Plain)** | `web/public/htmx-chat.html` | `/events/stream` (SSE)<br>`/chat` (fallback) | ❌ **NO** | 🚨 Demo - needs migration |
| **Shadow DOM Widget** | `web/public/widget/chat-widget.js` | `/events/stream` (SSE)<br>`/chat` (fallback) | ❌ **NO** | 🚨 Widget - needs migration |
| **Iframe Demo** | `localhost:4321/demo/iframe`<br>`web/src/pages/demo/iframe.astro` | Inherits from backend<br>(`/events/stream` via iframe) | ❌ **NO** | 🚨 Embeds legacy backend |
| **Widget Demo Page** | `localhost:4321/demo/widget`<br>`web/src/pages/demo/widget.astro` | Inherits from Shadow DOM widget<br>(`/events/stream`) | ❌ **NO** | 🚨 Demo - needs migration |

---

## 🔍 Implementation Details

### ✅ Correct: `/agents/simple-chat/chat`

**File**: `backend/app/api/agents.py:26-202`

**Implementation**:
```python
# Calls Pydantic AI agent directly
result = await simple_chat(
    message=message, 
    session_id=str(session.id),
    message_history=chat_request.message_history
)
```

**Features**:
- ✅ Uses Pydantic AI `Agent` class
- ✅ Automatic usage tracking via `result.usage()`
- ✅ Tracks to `llm_requests` table via `LLMRequestTracker`
- ✅ Proper cost calculation
- ✅ Token counts from API response
- ✅ Session persistence
- ✅ Message history

---

### ❌ Incorrect: `/events/stream` (SSE)

**File**: `backend/app/main.py:710-955`

**Implementation**:
```python
# Direct HTTP call, bypasses Pydantic AI
async for chunk in stream_chat_chunks(
    message=message,
    model=model,
    temperature=temperature,
    max_tokens=max_tokens,
    conversation_history=history
):
    yield chunk
```

**Problems**:
- ❌ Uses raw `httpx` HTTP client
- ❌ Calls OpenRouter API directly
- ❌ No Pydantic AI agent
- ❌ No automatic usage tracking
- ❌ Estimated token counts (unreliable)
- ❌ Doesn't track to `llm_requests` table
- ❌ No cost calculation

**Used by**: 
- localhost:8000 (main production chat)
- Most demos and widgets

---

### ❌ Incorrect: `/chat` (Non-streaming)

**File**: `backend/app/main.py:1033-1262`

**Implementation**:
```python
# Direct HTTP call, bypasses Pydantic AI
text = await chat_completion_content(
    message=message,
    model=model,
    temperature=temperature,
    max_tokens=max_tokens,
    extra_headers=headers or None,
)
```

**Problems**:
- ❌ Uses raw `httpx` HTTP client
- ❌ Calls OpenRouter API directly  
- ❌ No Pydantic AI agent
- ❌ No automatic usage tracking
- ❌ Estimated token counts (unreliable)
- ❌ Doesn't track to `llm_requests` table
- ❌ No cost calculation

**Used by**: 
- Fallback for SSE failures
- Some HTMX demos

---

## 🚨 Migration Strategy

**See**: [Account-Agent Instance Architecture](../design/account-agent-instance-architecture.md) for the complete migration plan.

### Migration Approach: Zero-Risk Parallel Deployment

The new architecture uses explicit account and agent instance identifiers in URLs:

```
New: /accounts/{account-slug}/agents/{instance-slug}/chat
New: /accounts/{account-slug}/agents/{instance-slug}/stream
```

**Key Insight**: The new `/accounts/` URL pattern doesn't conflict with existing endpoints, enabling safe parallel operation.

### Phase 1: Build New Infrastructure (Zero Production Impact)

- Implement new account-instance endpoints alongside existing code
- Existing endpoints (`/chat`, `/events/stream`) remain completely untouched
- Can test thoroughly before any production impact

### Phase 2: Internal Migration (Backward Compatible)

- Migrate existing endpoints to use new infrastructure internally
- Same URLs, same response formats
- Legacy endpoints become reverse proxies to default instance:
  - `/chat` → `/accounts/default/agents/simple-chat/chat`
  - `/events/stream` → `/accounts/default/agents/simple-chat/stream`

### Phase 3: Deprecation & Cleanup (Optional, Can Be Delayed)

- Update frontend clients to use new URLs
- Add deprecation warnings
- Eventually remove legacy code

### Migration Priority

1. **High Priority**: `/events/stream` and `/chat` (used by localhost:8000)
2. **Medium Priority**: Shadow DOM Widget, HTMX demos
3. **Low Priority**: Iframe demo (inherits from backend migration)

---

## 📋 Migration Checklist

For each endpoint migration (see [Account-Agent Instance Architecture](../design/account-agent-instance-architecture.md) for details):

### Phase 1: New Infrastructure
- [ ] Add database columns (`account`, `agent_instance`, `agent_type`, `completion_status`)
- [ ] Create instance loader (`load_agent_instance()`)
- [ ] Implement `simple_chat_stream()` with Pydantic AI `agent.run_stream()`
- [ ] Create new endpoints (`/accounts/{account}/agents/{instance}/chat` and `/stream`)
- [ ] Update `LLMRequestTracker` to record account/instance/type
- [ ] Add tests for new endpoints
- [ ] Verify cost tracking in `llm_requests` table

### Phase 2: Legacy Migration
- [ ] Update `simple_chat()` to accept optional `config` parameter
- [ ] Create `load_instance_or_default()` helper
- [ ] Migrate `/chat` endpoint to use instance infrastructure internally
- [ ] Migrate `/events/stream` endpoint to use instance infrastructure internally
- [ ] Test backward compatibility
- [ ] Verify identical response formats

### Phase 3: Frontend Updates
- [ ] Update frontend clients to use new `/accounts/{account}/agents/{instance}/` URLs
- [ ] Add deprecation warnings to legacy endpoints
- [ ] Monitor usage patterns
- [ ] Remove legacy code when ready

---

## 📚 Related Documentation

- [Account-Agent Instance Architecture](../design/account-agent-instance-architecture.md) - **Primary migration guide**
- [LLM Cost Tracking Architecture](./tracking_llm_costs.md) - Detailed cost tracking implementation
- [Project Brief - Core Principles](../project-brief.md#core-architectural-principles) - Pydantic AI mandate
- [Simple Chat Agent Design](../design/simple-chat.md) - Agent architecture
- [API Endpoints](./endpoints.md) - Complete endpoint documentation
- [Chat Widget Architecture](./chat-widget-architecture.md) - Widget implementation details

---

## ✅ Success Criteria

**Migration complete when**:

1. All chat endpoints use Pydantic AI agents
2. All LLM requests appear in `llm_requests` table
3. Token counts are accurate (from API, not estimated)
4. Cost calculations are precise
5. No direct OpenRouter HTTP calls in production code
6. All automated tests pass
7. Session persistence maintained across all clients

