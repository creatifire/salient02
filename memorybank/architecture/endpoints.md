# API Endpoints Documentation

> Comprehensive documentation of all current and planned API endpoints for the Salient AI Chat System, organized by implementation phases and functionality.

## Overview

The Salient AI Chat System follows a **parallel endpoint strategy** that ensures zero disruption during development while evolving from legacy chat functionality to a sophisticated multi-agent, multi-account architecture.

### Endpoint Evolution Strategy
```
Phase 1: Legacy + Simple Chat Agent (Single Account)
Phase 2: + Sales Agent (Multiple Agents, Single Account) 
Phase 3: Multi-Account Architecture (Account-scoped endpoints)
Phase 4: Router Agent (Intelligent agent selection)
```

---

## 🔄 **CURRENT ENDPOINTS** (Implemented)

### **Main Application Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/` | Main chat interface with HTMX frontend | HTML | ✅ Active |
| `GET` | `/health` | System health check with database connectivity | JSON | ✅ Active |
| `GET` | `/static/*` | Static asset serving (CSS, JS, images, SVG) | Files | ✅ Active |

### **Chat & Messaging Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/chat` | **Legacy chat endpoint** - Non-streaming chat | PlainText | ✅ Active |
| `GET` | `/events/stream` | **Legacy SSE endpoint** - Streaming LLM responses | SSE Stream | ✅ Active |

### **API Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/api/config` | Frontend configuration and feature flags | JSON | ✅ Active |
| `GET` | `/api/session` | Session information for debugging/development | JSON | ✅ Active |
| `GET` | `/api/chat/history` | Chat history retrieval for current session | JSON | ✅ Active |

### **Development & Monitoring Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/dev/logs/tail` | Live log tailing for debugging (configurable) | JSON | ✅ Active |

### **Demo & Testing Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/demo/htmx-chat` | Astro demo chat page | HTML | ✅ Active |
| `GET` | `/htmx-chat.html` | Standalone HTMX chat page | HTML | ✅ Active |

---

## 🆕 **PHASE 1 ENDPOINTS** (In Development - Parallel Strategy)

### **Simple Chat Agent Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/agents/simple-chat/chat` | **NEW**: Simple chat agent endpoint | PlainText | 🚧 Planned |
| `GET` | `/agents/simple-chat/stream` | **FUTURE**: Agent-specific SSE streaming | SSE Stream | 📋 Future |
| `GET` | `/agents/simple-chat/` | **FUTURE**: Agent-specific page | HTML | 📋 Future |

**Key Features:**
- ✅ **Parallel Operation**: Works alongside legacy `/chat` endpoint
- ✅ **Session Compatibility**: Shares session management with legacy endpoints
- ✅ **Message History**: Maintains conversation continuity between endpoints
- ✅ **Pydantic AI Integration**: Native Pydantic AI agent implementation
- ✅ **Integrated Research Tools**: Vector search, web search, document intelligence, chat summarization

---

## 📈 **PHASE 2 ENDPOINTS** (Roadmap)

### **Sales Agent Addition**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/agents/sales/chat` | Sales agent with CRM integration | PlainText | 📋 Planned |
| `GET` | `/agents/sales/stream` | Sales agent SSE streaming | SSE Stream | 📋 Planned |
| `GET` | `/agents/sales/` | Sales agent interface page | HTML | 📋 Planned |

### **Digital Expert Agent**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/agents/digital-expert/chat` | Content modeling and persona agent | PlainText | 📋 Planned |
| `GET` | `/agents/digital-expert/stream` | Digital expert SSE streaming | SSE Stream | 📋 Planned |

### **Research Agents**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/agents/deep-research/chat` | Multi-step investigation agent | PlainText | 📋 Planned |

**Note**: Simple research functionality (document intelligence, web search, vector search) has been integrated into the Simple Chat Agent through tool access.

---

## 🏢 **PHASE 3 ENDPOINTS** (Multi-Account Architecture)

### **Account-Scoped Agent Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/accounts/{account-slug}/agents/{agent-type}/chat` | Account-isolated agent access | PlainText | 📋 Future |
| `GET` | `/accounts/{account-slug}/agents/{agent-type}/stream` | Account-scoped agent streaming | SSE Stream | 📋 Future |
| `GET` | `/accounts/{account-slug}/agents` | Agent discovery for account | JSON | 📋 Future |

### **Account Management Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `GET` | `/accounts/{account-slug}/profile` | Account profile and settings | JSON | 📋 Future |
| `GET` | `/accounts/{account-slug}/usage` | Usage metrics and billing | JSON | 📋 Future |
| `POST` | `/accounts/{account-slug}/agents/{agent-type}/configure` | Agent instance configuration | JSON | 📋 Future |

### **Backward Compatibility Mappings**
```
POST /agents/simple-chat/chat → POST /accounts/default/agents/simple-chat/chat
POST /agents/sales/chat       → POST /accounts/default/agents/sales/chat
```

---

## 🤖 **PHASE 4 ENDPOINTS** (Router Agent)

### **Intelligent Routing Endpoints**
| Method | Endpoint | Description | Response | Status |
|--------|----------|-------------|----------|--------|
| `POST` | `/accounts/{account-slug}/chat` | Router selects appropriate agent | PlainText | 📋 Future |
| `POST` | `/accounts/default/chat` | Default account router | PlainText | 📋 Future |
| `GET` | `/accounts/{account-slug}/chat/stream` | Router-managed streaming | SSE Stream | 📋 Future |

### **Legacy Deprecation Strategy**
```
POST /chat → POST /accounts/default/chat  # Redirect to router
```

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
- ✅ **Logging**: Structured JSON logging with Loguru
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
