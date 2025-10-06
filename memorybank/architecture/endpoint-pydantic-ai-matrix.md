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

## 🚨 Migration Priority

### High Priority (Production)

1. **`/events/stream`** - Used by localhost:8000 (main chat interface)
   - Replace with Pydantic AI SSE streaming
   - Update `backend/templates/index.html` to use new endpoint
   - Maintain session compatibility

### Medium Priority (Demos & Widgets)

2. **`/chat`** - Used as fallback by multiple clients
   - Replace with Pydantic AI non-streaming endpoint
   - Update all clients using this as primary endpoint

3. **Shadow DOM Widget** - Embeddable widget
   - Update to use Pydantic AI endpoints
   - Maintain backward compatibility via feature flags

4. **HTMX Demos** - Demo pages
   - Update to use Pydantic AI endpoints
   - Use as testing ground for new patterns

### Low Priority (Reference Only)

5. **Iframe Demo** - Will inherit once backend is migrated
   - No direct changes needed
   - Tests cross-origin embedding

---

## 📋 Migration Checklist

For each endpoint migration:

- [ ] Create new Pydantic AI agent endpoint (e.g., `/agents/simple-chat/stream`)
- [ ] Implement proper SSE streaming with Pydantic AI
- [ ] Add automatic LLM cost tracking via `track_llm_call()`
- [ ] Update frontend client to use new endpoint
- [ ] Test session persistence and message history
- [ ] Verify `llm_requests` table tracking
- [ ] Add tests for the new endpoint
- [ ] Update documentation
- [ ] Deprecate old endpoint (with migration period if needed)

---

## 📚 Related Documentation

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

