<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# API Endpoints Documentation

> **Last Updated**: January 31, 2025  
> **Updates**: Merged Pydantic AI implementation matrix, consolidated endpoint documentation  
> Comprehensive documentation of all current and planned API endpoints for the Salient AI Chat System, organized by implementation phases and functionality.

## Overview

The Salient AI Chat System uses a **multi-tenant, multi-agent architecture** with explicit account and agent instance URLs. Legacy endpoints remain operational for backward compatibility but should be migrated to the new architecture.

### Implementation Status
```
✅ COMPLETE: Multi-Tenant Account-Instance Architecture (Phase 3)
   - Pydantic AI-based agents with proper cost tracking
   - Account-scoped agent instances with unique configurations
   - Streaming (SSE) and non-streaming endpoints
   - Multi-tenant aware chat history
   - Production-ready with all critical bugs fixed

🚧 IN PROGRESS: Legacy endpoint migration to Pydantic AI
   
📋 PLANNED: Additional agent types (Sales, Research, etc.)
📋 PLANNED: Optional Router Agent (Phase 4)
```

**See**: [Epic 0022 - Multi-Tenant Architecture](../project-management/0022-multi-tenant-architecture.md) for detailed implementation.

---

## 🔄 **CURRENT ENDPOINTS** (Implemented)

### **Main Application Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/` | Main chat interface with HTMX frontend | HTML | ✅ Active |
| `GET` | `/health` | System health check with database connectivity | JSON | ✅ Active |
| `GET` | `/static/*` | Static asset serving (CSS, JS, images, SVG) | Files | ✅ Active |

### **Multi-Tenant Chat Endpoints** (New Architecture - Pydantic AI)
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/accounts/{account}/agents/{instance}/chat` | Multi-tenant chat (non-streaming) | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/{instance}/stream` | Multi-tenant streaming chat (SSE) | SSE Stream | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/{instance}/history` | Multi-tenant chat history | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/{instance}/metadata` | Agent instance metadata (model, status, display_name) | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents` | List agent instances for account | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/health` | Health check for multi-tenant router | JSON | ✅ **Production** |

**Features**:
- ✅ Pydantic AI agents with proper `agent.run()` / `agent.run_stream()`
- ✅ Full cost tracking (`prompt_cost`, `completion_cost`, `total_cost` with `NUMERIC(12,8)` precision)
- ✅ Multi-tenant isolation (session + agent instance filtering)
- ✅ Streaming with SSE protocol compliance (multi-line markdown support)
- ✅ Client-side markdown rendering (GFM tables, code blocks)
- ✅ Debug logging with auto dev/prod toggle
- ✅ Dynamic model information via metadata endpoint

**Example URLs**:
```
POST   /accounts/default_account/agents/simple_chat1/chat
GET    /accounts/default_account/agents/simple_chat1/stream?message=hello
GET    /accounts/default_account/agents/simple_chat1/history
GET    /accounts/default_account/agents/simple_chat1/metadata
GET    /accounts/default_account/agents
GET    /accounts/default_account/agents/health
GET    /accounts/acme/agents/acme_chat1/stream?message=test
```

### **Legacy Chat Endpoints** (Pre-Multi-Tenant) ⚠️ **DEPRECATED**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/chat` | **Legacy** - Non-streaming chat (direct API) | PlainText | ⚠️ **DEPRECATED** - Use `/accounts/{account}/agents/{instance}/chat` |
| `GET` | `/events/stream` | **Legacy** - Streaming SSE (direct API) | SSE Stream | ⚠️ **DEPRECATED** - Use `/accounts/{account}/agents/{instance}/stream` |
| `POST` | `/agents/simple-chat/chat` | **Legacy** - Agent-specific chat endpoint | JSON | ⚠️ **DEPRECATED** - Use `/accounts/{account}/agents/{instance}/chat` |

**Issues**:
- ❌ Direct OpenRouter HTTP calls (no Pydantic AI)
- ❌ Estimated token counts (unreliable)
- ❌ No cost tracking to `llm_requests` table
- ⚠️ Used by `localhost:8000` main page (needs migration)
- ❌ No multi-tenant account isolation

**Migration Path**:
- Replace `/chat` → `/accounts/default_account/agents/simple_chat1/chat`
- Replace `/events/stream` → `/accounts/default_account/agents/simple_chat1/stream`
- Replace `/agents/simple-chat/chat` → `/accounts/{account}/agents/{instance}/chat`

### **API Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/api/config` | Frontend configuration and feature flags | JSON | ✅ Active |
| `GET` | `/api/session` | Session information for debugging/development | JSON | ✅ Active |
| `GET` | `/api/chat/history` | **Legacy** chat history (session-only filter) | JSON | ⚠️ **DEPRECATED** - Use `/accounts/{account}/agents/{instance}/history` |

### **Development & Monitoring Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/dev/logs/tail` | Live log tailing for debugging (configurable) | JSON | ✅ Active |

### **Demo & Testing Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/demo/simple-chat` | Astro simple chat demo (multi-tenant) | HTML | ✅ Production |
| `GET` | `/demo/widget` | Floating widget demo (multi-tenant) | HTML | ✅ Production |
| `GET` | `/htmx-chat.html` | Standalone HTMX chat (multi-tenant) | HTML | ✅ Production |
| `GET` | `/demo/htmx-chat` | Astro demo chat page (legacy) | HTML | ⚠️ Legacy |

**Demo Status**:
- ✅ All demos migrated to multi-tenant endpoints
- ✅ Use `default_account/simple_chat1` by default
- ✅ Support URL params for account/agent selection (e.g., `?account=acme&agent=acme_chat1`)
- ✅ Full markdown rendering with GFM table support
- ✅ Debug logging with dev/prod auto-toggle

---

## 🏢 **MULTI-TENANT ARCHITECTURE** (Phase 3 - ✅ Complete)

### **Account-Scoped Agent Instance Endpoints**

**Status**: ✅ **Production Ready** - All endpoints implemented and tested

| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/accounts/{account}/agents/{instance}/chat` | Agent instance chat (non-streaming) | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/{instance}/stream` | Agent instance streaming (SSE) | SSE Stream | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/{instance}/history` | Multi-tenant chat history | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/{instance}/metadata` | Agent instance metadata (model, status, display_name) | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents` | List agent instances for account | JSON | ✅ **Production** |
| `GET` | `/accounts/{account}/agents/health` | Health check for multi-tenant router | JSON | ✅ **Production** |

**Implemented Features**:
- ✅ Full Pydantic AI integration (`agent.run()`, `agent.run_stream()`)
- ✅ Multi-tenant data isolation (session + agent instance filtering)
- ✅ Precise cost tracking with OpenRouter `provider_details`
- ✅ Streaming cost calculation via `genai-prices` + fallback config
- ✅ SSE protocol compliance (multi-line data formatting)
- ✅ Client-side markdown rendering (marked.js with GFM)
- ✅ Session management with cookie-based persistence
- ✅ Message history with conversation continuity
- ✅ Debug logging infrastructure
- ✅ Dynamic model information retrieval via metadata endpoint
- ✅ Health check endpoint for router monitoring

**Frontend Clients Using Multi-Tenant Endpoints**:
- ✅ `localhost:4321/demo/simple-chat` - Astro standalone chat
- ✅ `localhost:4321/demo/widget` - Floating chat widget
- ✅ `localhost:4321/htmx-chat.html` - Standalone HTMX page
- ⚠️ `localhost:8000/` - Main backend page (still uses legacy, needs migration)

**Example URLs**:
```
# Default account/agent
POST /accounts/default_account/agents/simple_chat1/chat
GET  /accounts/default_account/agents/simple_chat1/stream?message=hello
GET  /accounts/default_account/agents/simple_chat1/history
GET  /accounts/default_account/agents/simple_chat1/metadata
GET  /accounts/default_account/agents
GET  /accounts/default_account/agents/health

# ACME account with custom agent
POST /accounts/acme/agents/acme_chat1/chat
GET  /accounts/acme/agents/acme_chat1/stream?message=test
GET  /accounts/acme/agents/acme_chat1/metadata
GET  /accounts/acme/agents
```

**Metadata Endpoint Response Example**:
```json
{
  "account_slug": "default_account",
  "instance_slug": "simple_chat1",
  "agent_type": "simple_chat",
  "display_name": "Simple Chat 1",
  "model": "moonshotai/kimi-k2-0905",
  "status": "active",
  "last_used_at": "2025-01-12T14:30:00Z"
}
```

**Configuration**:
- Database-driven account/agent instance metadata
- YAML-based agent configurations (`backend/config/agent_configs/{account}/{instance}/`)
- Hybrid approach: DB for validation, YAML for agent behavior

### **Account Management Endpoints** (Future)
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/accounts/{account}/profile` | Account profile and settings | JSON | 📋 Planned |
| `GET` | `/accounts/{account}/usage` | Usage metrics and billing | JSON | 📋 Planned |
| `POST` | `/accounts/{account}/agents/{instance}/configure` | Update instance configuration | JSON | 📋 Planned |

### **Legacy Endpoint Migration Plan** ⚠️ **IN PROGRESS**

**Deprecated Endpoints** (Targeted for removal):
```
POST /chat                        → POST /accounts/{account}/agents/{instance}/chat
GET  /events/stream               → GET  /accounts/{account}/agents/{instance}/stream
POST /agents/simple-chat/chat     → POST /accounts/{account}/agents/{instance}/chat
GET  /api/chat/history            → GET  /accounts/{account}/agents/{instance}/history
```

**Migration Benefits**:
- ✅ Same URL, same response format (backward compatible)
- ✅ Gains Pydantic AI, cost tracking, proper usage data
- ✅ Zero impact on existing clients
- ✅ Multi-tenant account isolation
- ✅ Proper cost attribution per account/instance

**Status**: Legacy endpoints remain active for backward compatibility but should not be used for new development. All new clients should use multi-tenant endpoints.

---

## 🆕 **FUTURE AGENT TYPES** (Roadmap)

### **Sales Agent** (Planned)
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/accounts/{account}/agents/{sales-instance}/chat` | Sales agent with CRM integration | JSON | 📋 Planned |
| `GET` | `/accounts/{account}/agents/{sales-instance}/stream` | Sales agent SSE streaming | SSE Stream | 📋 Planned |

### **Research Agents** (Planned)
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/accounts/{account}/agents/{research-instance}/chat` | Multi-step investigation agent | JSON | 📋 Planned |

**Note**: Multi-tenant architecture already supports multiple agent types. New agents can be added by:
1. Creating agent instance records in `agent_instances` table
2. Adding YAML configs in `backend/config/agent_configs/{account}/{instance}/`
3. Implementing agent logic (if not using existing `simple_chat` base)

---

## 🤖 **PHASE 4 ENDPOINTS** (Router Agent - Optional)

**Note**: The account-instance architecture (Phase 3) makes routing optional. URLs explicitly specify the agent instance, eliminating the need for automatic agent selection. However, a router can still be useful for specific use cases.

### **Optional Router Instance**
A router can be implemented as just another agent instance:

| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/accounts/{account-slug}/agents/router-auto/chat` | Router instance selects other agents | JSON | 📋 Optional |
| `GET` | `/accounts/{account-slug}/agents/router-auto/stream` | Router streaming | SSE Stream | 📋 Optional |

**Example**:
```
# Create a router instance with agent_type: "router"
POST /accounts/acme/agents/router-auto/chat
  → Router analyzes request and internally calls:
  → /accounts/acme/agents/sales-enterprise/chat (for sales queries)
  → /accounts/acme/agents/simple-chat-customer-support/chat (for support)
```

**Benefits of Optional Router**:
- Transparent to user (no manual agent selection)
- Logs routing decisions for analytics
- Can be enabled per-account
- Doesn't complicate core architecture

---

## 🔧 **INFRASTRUCTURE ENDPOINTS**

### **Health & Monitoring**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/health` | System health with database connectivity | JSON | ✅ Active |
| `GET` | `/health/detailed` | Comprehensive system diagnostics | JSON | 📋 Future |
| `GET` | `/metrics` | Prometheus metrics endpoint | Text | 📋 Future |

### **Authentication & Security** (Future)
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/auth/login` | User authentication | JSON | 📋 Future |
| `POST` | `/auth/logout` | Session termination | JSON | 📋 Future |
| `GET` | `/auth/profile` | User profile information | JSON | 📋 Future |

### **Admin & Management** (Future)
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/admin/users` | User management interface | JSON | 📋 Future |
| `GET` | `/admin/agents` | Agent management dashboard | JSON | 📋 Future |
| `POST` | `/admin/agents/{agent-id}/restart` | Agent instance restart | JSON | 📋 Future |

---

## 📊 **ENDPOINT CONFIGURATION**

### **app.yaml Configuration Structure**
```yaml
# Legacy endpoint configuration (remains enabled)
legacy:
  enabled: true
  endpoint: "/chat"
  stream_endpoint: "/events/stream"

# Agent endpoint configuration
agents:
  simple_chat:
    enabled: true
    endpoint: "/agents/simple-chat"
    config_file: "agent_configs/simple_chat.yaml"
  
  sales:
    enabled: false  # Enable in Phase 2
    endpoint: "/agents/sales"
    config_file: "agent_configs/sales.yaml"

# Route mapping (connects endpoints to agents)
routes:
  "/chat": simple_chat                 # Legacy uses simple_chat agent
  "/agents/simple-chat": simple_chat   # Explicit agent routing
  "/agents/sales": sales_agent         # Sales agent routing (Phase 2)

# Multi-account (Phase 3)
multi_account:
  enabled: false
  default_account: "default"
  endpoint_pattern: "/accounts/{account_slug}/agents/{agent_type}"
```

### **Session & Request Handling**

**Shared Infrastructure (All Endpoints):**
- ✅ **Session Management**: `SimpleSessionMiddleware` with secure cookies
- ✅ **Message Persistence**: PostgreSQL with async SQLAlchemy
- ✅ **Configuration Loading**: Dynamic `app.yaml` with environment overrides
- ✅ **Logging**: Structured logging with Logfire (observability platform)
- ✅ **Error Handling**: Graceful degradation and comprehensive error logging

**Excluded Paths (No Session Processing):**
```
/health, /favicon.ico, /robots.txt, /dev/logs/tail, /static/*, /assets/*
```

### **Response Formats**

| Format | Content-Type | Usage | Endpoints |
|--------|--------------|-------|-----------|
| **HTML** | `text/html` | Chat interfaces, demo pages | `/`, `/demo/htmx-chat` |
| **PlainText** | `text/plain` | Chat responses (legacy compatibility) | `/chat`, `/agents/*/chat` |
| **JSON** | `application/json` | API responses, configuration | `/api/*`, `/health` |
| **SSE Stream** | `text/event-stream` | Streaming chat responses | `/events/stream`, `/agents/*/stream` |
| **Static Files** | Various | Assets (CSS, JS, images, SVG) | `/static/*` |

---

## 🚀 **DEPLOYMENT CONSIDERATIONS**

### **Load Balancer Configuration**
```nginx
# Health check endpoint
location /health {
    proxy_pass http://backend;
    proxy_set_header Host $host;
}

# Static assets (CDN/caching)
location /static/ {
    proxy_pass http://backend;
    proxy_cache_valid 200 1h;
}

# Main application endpoints
location / {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### **Rate Limiting & Security**
- **Chat Endpoints**: 60 requests/minute per session
- **API Endpoints**: 120 requests/minute per session  
- **Static Assets**: No rate limiting (cached)
- **Health Checks**: No rate limiting (monitoring)

### **CORS Configuration**
```yaml
# Development
cors:
  allow_origins: ["http://localhost:3000", "http://localhost:4321"]
  allow_credentials: true

# Production  
cors:
  allow_origins: ["https://yourdomain.com"]
  allow_credentials: true
```

---

## 🔗 **REFERENCES**

- **[Agent Endpoint Transition Strategy](../design/agent-endpoint-transition.md)** - Complete transition plan
- **[Code Organization](./code-organization.md)** - Implementation patterns and structure
- **[Multi-Account Support](./multi-account-support.md)** - Multi-tenant architecture details
- **[Simple Chat Agent Implementation](../project-management/0017-simple-chat-agent.md)** - Phase 1 agent details

**Key Insight**: The parallel endpoint strategy ensures **zero disruption** during development while providing a clear evolution path toward sophisticated multi-agent, multi-account architecture.

---

## Pydantic AI Implementation Status

> **Core Principle**: ALL LLM interactions MUST use Pydantic AI. Legacy endpoints violate this principle and need migration.

### ✅ Multi-Tenant Endpoints (Pydantic AI) - Production

| Endpoint | Method | Uses Pydantic AI? | LLM Cost Tracking? | Frontend Clients | Implementation | Status |
|----------|--------|-------------------|-------------------|------------------|----------------|---------|
| `/accounts/{account}/agents/{instance}/chat` | `POST` | ✅ **YES** | ✅ **YES** | All Astro demos<br>HTMX chat<br>Widget | Pydantic AI `simple_chat()` | ✅ **PRODUCTION** |
| `/accounts/{account}/agents/{instance}/stream` | `GET` | ✅ **YES** | ✅ **YES** | All Astro demos<br>HTMX chat<br>Widget | Pydantic AI `simple_chat_stream()` | ✅ **PRODUCTION** |
| `/accounts/{account}/agents/{instance}/history` | `GET` | N/A | N/A | All Astro demos<br>HTMX chat<br>Widget | Multi-tenant DB query | ✅ **PRODUCTION** |

### ⚠️ Legacy Endpoints (No Pydantic AI) - Deprecated

| Endpoint | Method | Uses Pydantic AI? | LLM Cost Tracking? | Frontend Clients | Implementation | Status |
|----------|--------|-------------------|-------------------|------------------|----------------|---------|
| `/events/stream` | `GET` | ❌ **NO** | ❌ **NO** | localhost:8000 only | Direct HTTP<br>`stream_chat_chunks()` | ⚠️ **LEGACY** |
| `/chat` | `POST` | ❌ **NO** | ❌ **NO** | localhost:8000 only | Direct HTTP<br>`chat_completion_content()` | ⚠️ **LEGACY** |

### Frontend Client Migration Status

| Client | Location | Primary Endpoint | Pydantic AI? | Notes |
|--------|----------|------------------|--------------|-------|
| **Backend Main Chat** | `localhost:8000`<br>`backend/templates/index.html` | `/events/stream` (SSE)<br>`/chat` (fallback) | ❌ **NO** | ⚠️ Legacy - needs migration |
| **Astro Simple Chat Demo** | `localhost:4321/demo/simple-chat` | `/accounts/{account}/agents/{instance}/chat`<br>`/accounts/{account}/agents/{instance}/stream` | ✅ **YES** | ✅ **PRODUCTION READY** |
| **Floating Chat Widget** | `web/public/widget/chat-widget.js` | `/accounts/{account}/agents/{instance}/stream` (SSE) | ✅ **YES** | ✅ **PRODUCTION READY** |
| **HTMX Chat (Standalone)** | `web/public/htmx-chat.html` | `/accounts/{account}/agents/{instance}/stream` (SSE) | ✅ **YES** | ✅ **PRODUCTION READY** |

**Migration Summary**: 3 of 6 clients migrated to multi-tenant Pydantic AI endpoints. Main backend page (`localhost:8000`) migration pending.

### Implementation Details

**Correct Implementation (Multi-Tenant)**:
```python
# Load agent instance configuration
instance = await load_agent_instance(account_slug, instance_slug)

# Call Pydantic AI agent
result = await simple_chat(
    message=user_message,
    session_id=str(session.id),
    agent_instance_id=instance.id,
    message_history=message_history,
    instance_config=instance.config
)

# Usage tracking via result.usage()
usage_data = result.usage()
```

**Problems with Legacy Endpoints**:
- ❌ Uses raw `httpx` HTTP client (no Pydantic AI)
- ❌ Calls OpenRouter API directly
- ❌ No automatic usage tracking via `result.usage()`
- ❌ Estimated token counts (unreliable)
- ❌ No cost calculation (missing `prompt_cost`, `completion_cost`, `total_cost`)

**Migration Plan**: Update `backend/templates/index.html` to use `/accounts/default_account/agents/simple_chat1/stream`
