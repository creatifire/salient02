<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Chat Endpoints & Pydantic AI Implementation Matrix

> **Last Updated**: January 12, 2025

## Overview

This document provides a comprehensive view of all chat endpoints, which frontend clients use them, and whether they properly use Pydantic AI for LLM interactions.

## 🎯 Core Principle

**ALL LLM interactions MUST use Pydantic AI.** Any endpoint marked ❌ below violates this principle and needs migration.

## ✅ Current Status

**Multi-Tenant Architecture: COMPLETE**
- All new endpoints use Pydantic AI properly
- 3 frontend clients migrated to multi-tenant endpoints
- Legacy endpoints remain for `localhost:8000` (migration pending)

---

## Chat Endpoints & Client Matrix

| Endpoint | Method | Uses Pydantic AI? | LLM Cost Tracking? | Frontend Clients | Implementation | Status |
|----------|--------|-------------------|-------------------|------------------|----------------|---------|
| `/` | `GET` | N/A | N/A | Browser (localhost:8000) | Serves HTML page | ✅ Working |
| `/accounts/{account}/agents/{instance}/chat` | `POST` | ✅ **YES** | ✅ **YES** | All Astro demos<br>HTMX chat<br>Widget | Pydantic AI `simple_chat()` | ✅ **PRODUCTION** |
| `/accounts/{account}/agents/{instance}/stream` | `GET` | ✅ **YES** | ✅ **YES** | All Astro demos<br>HTMX chat<br>Widget | Pydantic AI `simple_chat_stream()` | ✅ **PRODUCTION** |
| `/accounts/{account}/agents/{instance}/history` | `GET` | N/A | N/A | All Astro demos<br>HTMX chat<br>Widget | Multi-tenant DB query | ✅ **PRODUCTION** |
| `/accounts/{account}/agents` | `GET` | N/A | N/A | Future use | Lists instances | ✅ **PRODUCTION** |
| `/events/stream` | `GET` | ❌ **NO** | ❌ **NO** | localhost:8000 only | Direct HTTP<br>`stream_chat_chunks()` | ⚠️ **LEGACY** |
| `/chat` | `POST` | ❌ **NO** | ❌ **NO** | localhost:8000 only | Direct HTTP<br>`chat_completion_content()` | ⚠️ **LEGACY** |

---

## Frontend Client Details

| Client | Location | Primary Endpoint | Pydantic AI? | Notes |
|--------|----------|------------------|--------------|-------|
| **Backend Main Chat** | `localhost:8000`<br>`backend/templates/index.html` | `/events/stream` (SSE)<br>`/chat` (fallback) | ❌ **NO** | ⚠️ Legacy - needs migration |
| **Astro Simple Chat Demo** | `localhost:4321/demo/simple-chat`<br>`web/src/pages/demo/simple-chat.astro` | `/accounts/{account}/agents/{instance}/chat`<br>`/accounts/{account}/agents/{instance}/stream` | ✅ **YES** | ✅ **PRODUCTION READY** |
| **Floating Chat Widget** | `web/public/widget/chat-widget.js`<br>Used by `localhost:4321/demo/widget` | `/accounts/{account}/agents/{instance}/stream` (SSE)<br>`/accounts/{account}/agents/{instance}/chat` (fallback) | ✅ **YES** | ✅ **PRODUCTION READY** |
| **HTMX Chat (Standalone)** | `web/public/htmx-chat.html` | `/accounts/{account}/agents/{instance}/stream` (SSE)<br>`/accounts/{account}/agents/{instance}/chat` (fallback) | ✅ **YES** | ✅ **PRODUCTION READY** |
| **HTMX Chat Demo (Astro)** | `localhost:4321/demo/htmx-chat`<br>`web/src/pages/demo/htmx-chat.astro` | `/events/stream` (SSE)<br>`/chat` (fallback) | ❌ **NO** | ⚠️ Legacy demo - low priority |
| **Iframe Demo** | `localhost:4321/demo/iframe`<br>`web/src/pages/demo/iframe.astro` | Inherits from backend<br>(`/events/stream` via iframe) | ❌ **NO** | ⚠️ Embeds legacy backend |

**Migration Summary**:
- ✅ **3 of 6 clients migrated** to multi-tenant Pydantic AI endpoints
- ✅ All production demos now use proper architecture
- ⚠️ Main backend page (`localhost:8000`) still uses legacy (next priority)
- ⚠️ Astro HTMX demo and Iframe demo are low priority (demo-only pages)

---

## 🔍 Implementation Details

### ✅ Correct: Multi-Tenant Endpoints (Pydantic AI)

**Files**: 
- `backend/app/api/account_agents.py` - Multi-tenant endpoint router
- `backend/app/agents/simple_chat.py` - Pydantic AI agent implementation

#### Non-Streaming Chat: `POST /accounts/{account}/agents/{instance}/chat`

**Implementation**:
```python
# Load agent instance configuration
instance = await load_agent_instance(account_slug, instance_slug)

# Call Pydantic AI agent with instance config
result = await simple_chat(
    message=user_message,
    session_id=str(session.id),
    agent_instance_id=instance.id,
    message_history=message_history,
    instance_config=instance.config
)
```

#### Streaming Chat: `GET /accounts/{account}/agents/{instance}/stream`

**Implementation**:
```python
# Stream using Pydantic AI async generator
async for event in simple_chat_stream(
    message=message_value,
    session_id=str(session.id),
    agent_instance_id=instance.id,
    message_history=message_history,
    instance_config=instance.config
):
    yield f"event: {event['event']}\ndata: {event['data']}\n\n"
```

**Pydantic AI Agent Core**:
```python
# backend/app/agents/simple_chat.py

# Non-streaming
agent = await get_chat_agent(instance_config=instance_config)
result = await agent.run(message, deps=session_deps, message_history=message_history)
response_text = result.output
usage_data = result.usage()

# Streaming
agent = await get_chat_agent(instance_config=instance_config)
async with agent.run_stream(message, deps=session_deps, message_history=message_history) as result:
    async for chunk in result.stream_text(delta=True):
        yield {"event": "message", "data": chunk}
    usage_data = result.usage()
```

**Features**:
- ✅ Uses Pydantic AI `Agent(model, deps_type=SessionDependencies, system_prompt)`
- ✅ Proper `agent.run()` and `agent.run_stream()` execution
- ✅ Automatic token tracking via `result.usage()`
- ✅ Full cost tracking to `llm_requests` table via `LLMRequestTracker`
- ✅ Precise cost calculation:
  - Non-streaming: OpenRouter `provider_details.cost_details`
  - Streaming: `genai-prices.calc_price()` + fallback pricing config
- ✅ Multi-tenant data isolation (session + agent instance filtering)
- ✅ Message persistence with `agent_instance_id` attribution
- ✅ Conversation history with `ModelRequest`/`ModelResponse` conversion
- ✅ Instance-specific configuration from YAML + database
- ✅ SSE protocol compliance (multi-line data formatting)
- ✅ Markdown rendering (GFM tables, code blocks)
- ✅ Debug logging infrastructure

---

### ⚠️ Legacy: `/events/stream` (SSE) - Needs Migration

**File**: `backend/app/main.py` (legacy code)

**Status**: ⚠️ **LEGACY - Only used by `localhost:8000` main page**

**Implementation**:
```python
# LEGACY: Direct HTTP call, bypasses Pydantic AI
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
- ❌ Uses raw `httpx` HTTP client via `openrouter_client.py`
- ❌ Calls OpenRouter API directly (no Pydantic AI)
- ❌ No `Agent` class, no `agent.run_stream()`
- ❌ No automatic usage tracking via `result.usage()`
- ❌ Estimated token counts (unreliable)
- ❌ Doesn't track to `llm_requests` table
- ❌ No cost calculation (`prompt_cost`, `completion_cost`, `total_cost` all missing)

**Migration Plan**: 
- Update `backend/templates/index.html` to use `/accounts/default_account/agents/simple_chat1/stream`
- Keep legacy endpoint as reverse proxy for backward compatibility (optional)

---

### ⚠️ Legacy: `/chat` (Non-streaming) - Needs Migration

**File**: `backend/app/main.py` (legacy code)

**Status**: ⚠️ **LEGACY - Only used by `localhost:8000` main page (fallback)**

**Implementation**:
```python
# LEGACY: Direct HTTP call, bypasses Pydantic AI
text = await chat_completion_content(
    message=message,
    model=model,
    temperature=temperature,
    max_tokens=max_tokens,
    extra_headers=headers or None,
)
```

**Problems**:
- ❌ Uses raw `httpx` HTTP client via `openrouter_client.py`
- ❌ Calls OpenRouter API directly (no Pydantic AI)
- ❌ No `Agent` class, no `agent.run()`
- ❌ No automatic usage tracking via `result.usage()`
- ❌ Estimated token counts (unreliable)
- ❌ Doesn't track to `llm_requests` table
- ❌ No cost calculation (`prompt_cost`, `completion_cost`, `total_cost` all missing)

**Migration Plan**: 
- Update `backend/templates/index.html` to use `/accounts/default_account/agents/simple_chat1/chat`
- Keep legacy endpoint as reverse proxy for backward compatibility (optional)

---

## 🚨 Migration Strategy

**See**: [Epic 0022 - Multi-Tenant Architecture](../project-management/0022-multi-tenant-architecture.md) for complete implementation details.

### Migration Status: Phase 1 Complete ✅

The new multi-tenant architecture uses explicit account and agent instance identifiers in URLs:

```
✅ IMPLEMENTED:
POST /accounts/{account}/agents/{instance}/chat        # Non-streaming
GET  /accounts/{account}/agents/{instance}/stream      # SSE streaming
GET  /accounts/{account}/agents/{instance}/history     # Multi-tenant history
GET  /accounts/{account}/agents                        # List instances
```

**Key Insight**: The new `/accounts/` URL pattern doesn't conflict with existing endpoints, enabling safe parallel operation with zero production impact.

### ✅ Phase 1: Build New Infrastructure (COMPLETE)

- ✅ Implemented new account-instance endpoints alongside existing code
- ✅ Existing endpoints (`/chat`, `/events/stream`) remain completely untouched
- ✅ 3 frontend clients migrated and production-ready
- ✅ All critical bugs fixed (CORS, SSE, markdown, cost tracking, etc.)
- ✅ Comprehensive testing (manual and automated)

**Migrated Clients**:
- ✅ `/demo/simple-chat` (Astro)
- ✅ `/demo/widget` (Floating widget)
- ✅ `/htmx-chat.html` (Standalone)

### 🚧 Phase 2: Internal Migration (IN PROGRESS)

**Next Step**: Migrate `localhost:8000` main page to use new infrastructure

**Options**:
1. **Direct Frontend Update** (Recommended):
   - Update `backend/templates/index.html` to call `/accounts/default_account/agents/simple_chat1/*`
   - No backend changes needed
   - Immediate benefit from Pydantic AI and cost tracking

2. **Backend Reverse Proxy** (Alternative):
   - Keep legacy URLs but internally route to new endpoints
   - More complex but maintains exact URL compatibility
   - `/chat` → internally calls `/accounts/default_account/agents/simple_chat1/chat`

### 📋 Phase 3: Deprecation & Cleanup (FUTURE)

- Add deprecation warnings to legacy endpoints
- Monitor usage patterns via logs
- Eventually remove legacy code when no longer used

### Current Migration Priority

1. ✅ **COMPLETE**: Frontend demos and widgets (3 of 6 clients)
2. 🚧 **IN PROGRESS**: Main backend page (`localhost:8000`)
3. 📋 **LOW PRIORITY**: Astro HTMX demo, Iframe demo (demo-only pages)

---

## 📋 Migration Checklist

### ✅ Phase 1: New Infrastructure (COMPLETE)
- ✅ Add database columns (`account_id`, `account_slug`, `agent_instance_id`, `agent_type`)
- ✅ Create database tables (`accounts`, `agent_instances`)
- ✅ Create instance loader (`load_agent_instance()`)
- ✅ Implement `simple_chat()` with Pydantic AI `agent.run()`
- ✅ Implement `simple_chat_stream()` with Pydantic AI `agent.run_stream()`
- ✅ Create new endpoints:
  - ✅ `POST /accounts/{account}/agents/{instance}/chat`
  - ✅ `GET /accounts/{account}/agents/{instance}/stream`
  - ✅ `GET /accounts/{account}/agents/{instance}/history`
  - ✅ `GET /accounts/{account}/agents` (list instances)
- ✅ Update `LLMRequestTracker` to record `agent_instance_id`
- ✅ Add tests for new endpoints (manual and automated)
- ✅ Verify cost tracking in `llm_requests` table:
  - ✅ Non-streaming: OpenRouter `provider_details.cost_details`
  - ✅ Streaming: `genai-prices.calc_price()` + fallback config
  - ✅ `NUMERIC(12,8)` precision for costs
- ✅ Fix critical bugs:
  - ✅ CORS configuration
  - ✅ SSE protocol compliance (multi-line data)
  - ✅ Markdown rendering (GFM tables)
  - ✅ Session management (vapid sessions)
  - ✅ Message persistence
- ✅ Migrate 3 frontend clients to new endpoints

### 🚧 Phase 2: Legacy Endpoint Migration (IN PROGRESS)
- [ ] **NEXT**: Update `backend/templates/index.html` to use multi-tenant endpoints
- [ ] Optional: Make legacy endpoints reverse proxies to new infrastructure
  - [ ] `/chat` → calls `/accounts/default_account/agents/simple_chat1/chat` internally
  - [ ] `/events/stream` → calls `/accounts/default_account/agents/simple_chat1/stream` internally
- [ ] Test backward compatibility for any remaining legacy clients
- [ ] Verify identical response formats

### 📋 Phase 3: Deprecation & Cleanup (FUTURE)
- [ ] Add deprecation warnings to legacy endpoints
- [ ] Monitor usage patterns via Logfire
- [ ] Update remaining demo pages (Astro HTMX demo, Iframe demo)
- [ ] Remove legacy code when no longer used
- [ ] Archive `openrouter_client.py` legacy code

---

## 📚 Related Documentation

- [Epic 0022 - Multi-Tenant Architecture](../project-management/0022-multi-tenant-architecture.md) - **Primary implementation epic**
- [Milestone 01 - Approach](../project-management/0000-approach-milestone-01.md) - Project roadmap
- [LLM Cost Tracking Architecture](./tracking_llm_costs.md) - Detailed cost tracking implementation
- [Pydantic AI Streaming Cost Tracking](../lessons-learned/pydantic-ai-streaming-cost-tracking.md) - Streaming cost solution
- [SSE Markdown Formatting Fix](../lessons-learned/sse-markdown-formatting-fix.md) - SSE protocol compliance
- [API Endpoints](./endpoints.md) - Complete endpoint documentation
- [Project Brief](../project-brief.md) - Core principles and Pydantic AI mandate

---

## ✅ Success Criteria

### Phase 1 (Multi-Tenant Infrastructure): ✅ **ACHIEVED**

1. ✅ All new chat endpoints use Pydantic AI agents (`agent.run()`, `agent.run_stream()`)
2. ✅ All LLM requests tracked in `llm_requests` table with `agent_instance_id`
3. ✅ Token counts accurate (from `result.usage()`, not estimated)
4. ✅ Cost calculations precise:
   - ✅ Non-streaming: OpenRouter `provider_details.cost_details`
   - ✅ Streaming: `genai-prices.calc_price()` + fallback config
   - ✅ `NUMERIC(12,8)` precision for all cost fields
5. ✅ No direct OpenRouter HTTP calls in new endpoints
6. ✅ All automated tests pass (with known skips for async issues)
7. ✅ Session persistence maintained across all clients
8. ✅ Multi-tenant data isolation (session + agent instance filtering)
9. ✅ Production-ready with all critical bugs fixed

### Phase 2 (Legacy Migration): 🚧 **IN PROGRESS**

1. [ ] Main backend page (`localhost:8000`) migrated to multi-tenant endpoints
2. [ ] Legacy endpoints either deprecated or converted to reverse proxies
3. [ ] No production code using `openrouter_client.py` direct API calls

### Phase 3 (Cleanup): 📋 **FUTURE**

1. [ ] All demo pages migrated
2. [ ] Deprecation warnings added
3. [ ] Legacy code removed

