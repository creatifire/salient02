# Agent Endpoint Transition Strategy
> **Last Updated**: August 28, 2025

> Design document for transitioning from legacy chat endpoints to Pydantic AI agent-based endpoints while maintaining backward compatibility and preparing for multi-account, multi-agent architecture.

## Overview

This document outlines the strategy for introducing Pydantic AI agent endpoints alongside existing chat functionality, ensuring zero disruption during development while establishing the foundation for future multi-account and multi-agent capabilities.

## Current State

### Existing Endpoints
```
GET /                        # Main chat page (index.html)
POST /chat                   # Chat endpoint (streaming SSE)
GET /events/stream           # SSE streaming endpoint
GET /demo/htmx-chat          # Astro demo page
GET /htmx-chat.html          # Standalone HTMX page
```

### Current Functionality
- Session management with browser cookies
- Message persistence to PostgreSQL database
- Markdown formatting and rendering
- Chat history loading on session resume
- Server-sent events (SSE) for streaming responses

## Transition Strategy: Parallel Endpoints

### Phase 1: Simple Chat Agent (Single Account)

**New Agent Endpoints:**
```
POST /agents/simple-chat/chat       # Simple chat agent endpoint
GET /agents/simple-chat/stream      # Agent-specific SSE endpoint
GET /agents/simple-chat/            # Agent-specific page (optional)
```

**Legacy Endpoints (Unchanged):**
```
POST /chat                          # Continue working unchanged
GET /events/stream                  # Continue working unchanged
GET /                               # Continue working unchanged
```

### Phase 2: Sales Agent Addition

**Additional Agent Endpoints:**
```
POST /agents/sales/chat             # Sales agent endpoint
GET /agents/sales/stream            # Sales agent SSE endpoint
```

### Phase 3: Multi-Account Architecture

**Account-Scoped Endpoints:**
```
POST /accounts/default/agents/simple-chat/chat
POST /accounts/{account-slug}/agents/{agent-type}/chat
GET /accounts/{account-slug}/agents               # Agent discovery
```

**Backward Compatibility Mapping:**
```
POST /agents/simple-chat/chat → POST /accounts/default/agents/simple-chat/chat
POST /agents/sales/chat       → POST /accounts/default/agents/sales/chat
```

### Phase 4: Multi-Agent Routing

**Router Endpoints:**
```
POST /accounts/{account-slug}/chat               # Router selects agent
POST /accounts/default/chat                     # Default account router
```

**Legacy Deprecation:**
```
POST /chat → POST /accounts/default/chat         # Redirect to router
```

## Implementation Details

### Session Management Compatibility

**Shared Session Infrastructure:**
- Both legacy and agent endpoints use identical session management
- Same `sessions` table and session middleware
- Same browser cookie handling
- Seamless chat history between endpoints

**Message Attribution:**
```sql
-- Enhanced message metadata to track agent handling
{
  "agent_type": "simple-chat",
  "agent_instance": "default",
  "endpoint_version": "v2",
  "tool_calls": [...]
}
```

### Configuration Strategy

**app.yaml Configuration:**
```yaml
# Legacy endpoint configuration
legacy:
  enabled: true                    # Can disable when ready to deprecate
  endpoint: "/chat"
  stream_endpoint: "/events/stream"

# Agent endpoint configuration
agents:
  simple_chat:
    enabled: true
    endpoint: "/agents/simple-chat"
    config_file: "agent_configs/simple_chat.yaml"
  
  sales:
    enabled: false                 # Enable in Phase 2
    endpoint: "/agents/sales"
    config_file: "agent_configs/sales.yaml"

# Multi-account (Phase 3)
multi_account:
  enabled: false                   # Enable in Phase 3
  default_account: "default"
  endpoint_pattern: "/accounts/{account_slug}/agents/{agent_type}"
```

### FastAPI Route Organization

**Route Structure:**
```python
# Legacy routes (preserve existing)
@app.post("/chat")
async def legacy_chat_endpoint():
    # Existing implementation unchanged

@app.get("/events/stream")
async def legacy_stream_endpoint():
    # Existing implementation unchanged

# Agent routes (new)
@app.post("/agents/{agent_type}/chat")
async def agent_chat_endpoint(agent_type: str):
    # New Pydantic AI agent implementation

@app.get("/agents/{agent_type}/stream")
async def agent_stream_endpoint(agent_type: str):
    # Agent-specific SSE streaming

# Future: Multi-account routes
@app.post("/accounts/{account_slug}/agents/{agent_type}/chat")
async def multi_account_agent_endpoint(account_slug: str, agent_type: str):
    # Multi-account agent implementation
```

### Database Schema Compatibility

**No Schema Changes Required:**
- Existing `sessions`, `messages`, `llm_requests` tables work unchanged
- `messages.metadata` field extended to include agent information
- `agent_instance_id` field can be null for legacy messages

**Message Differentiation:**
```python
# Legacy message
{
  "role": "assistant",
  "content": "Response text",
  "metadata": {}  # Empty or minimal metadata
}

# Agent message
{
  "role": "assistant", 
  "content": "Response text",
  "metadata": {
    "agent_type": "simple-chat",
    "agent_instance": "default",
    "tools_used": ["vector_search", "web_search"],
    "sources": [...]
  }
}
```

## Migration Timeline

### Phase 1: Development & Testing (Weeks 1-2)
1. **Implement agent endpoints** alongside legacy
2. **Test agent functionality** with existing sessions
3. **Validate session compatibility** between endpoints
4. **No user-facing changes** - legacy endpoints remain primary

### Phase 2: Gradual Frontend Migration (Weeks 3-4)
1. **Update demo pages** to use agent endpoints
2. **A/B test** legacy vs agent functionality
3. **Monitor performance** and user experience
4. **Keep legacy as fallback**

### Phase 3: Legacy Deprecation Planning (Weeks 5-6)
1. **Add deprecation warnings** to legacy endpoints
2. **Update documentation** to recommend agent endpoints
3. **Monitor usage patterns**
4. **Plan final migration timeline**

### Phase 4: Legacy Retirement (Future)
1. **Redirect legacy endpoints** to router agent
2. **Remove legacy code paths**
3. **Clean up configuration**

## Testing Strategy

### Compatibility Testing
1. **Session Continuity**: Start chat on legacy, continue on agent endpoint
2. **History Loading**: Verify chat history loads correctly on both endpoints
3. **Metadata Handling**: Ensure agent metadata doesn't break legacy rendering
4. **Performance Comparison**: Legacy vs agent response times

### Integration Testing
1. **All Demo Pages**: Test each frontend integration separately
2. **Widget Compatibility**: Ensure chat widget works with both endpoints
3. **Markdown Rendering**: Verify consistent formatting across endpoints
4. **SSE Streaming**: Test both streaming implementations

### Load Testing
1. **Concurrent Requests**: Legacy and agent endpoints under load
2. **Session Management**: High session volume with mixed endpoint usage
3. **Database Performance**: Message persistence under dual endpoint load

## Risk Mitigation

### High-Risk Scenarios
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Agent endpoint failure** | Users can't access new features | Legacy endpoints continue working |
| **Session conflicts** | Data inconsistency | Shared session management prevents conflicts |
| **Performance degradation** | Poor user experience | Monitor and optimize both endpoints |
| **Database migration issues** | Data loss or corruption | No schema changes required |

### Rollback Strategy
1. **Immediate**: Disable agent endpoints in configuration
2. **Quick**: Route agent endpoints to legacy implementation
3. **Complete**: Remove agent code, restore legacy-only operation

## Success Metrics

### Phase 1 Success Criteria
- ✅ Agent endpoints functional alongside legacy
- ✅ Session compatibility verified
- ✅ No impact on existing user experience
- ✅ Agent response quality matches or exceeds legacy

### Phase 2 Success Criteria
- ✅ Demo pages successfully migrated to agent endpoints
- ✅ User experience consistent or improved
- ✅ Performance within acceptable bounds
- ✅ Error rates below threshold

### Phase 3 Success Criteria
- ✅ Legacy usage declined to <10% of traffic
- ✅ Agent endpoints handle majority of requests
- ✅ Multi-account preparation complete
- ✅ Ready for legacy deprecation

## Future Considerations

### Multi-Account Preparation
- Agent endpoints naturally extend to account-scoped URLs
- Configuration system scales to per-account agent instances
- Database schema supports account isolation
- Session management ready for account context

### Multi-Agent Router
- Router endpoint can intelligently select between agent types
- Context preservation across agent handoffs
- Fallback to simple-chat agent for ambiguous queries
- Legacy endpoints can redirect to router for transparent upgrade

### Performance Optimization
- Agent instance caching and pooling
- Optimized database queries for agent metadata
- SSE streaming efficiency improvements
- Load balancing between agent instances

This transition strategy ensures zero disruption to existing functionality while establishing the foundation for our sophisticated multi-agent, multi-account architecture.
