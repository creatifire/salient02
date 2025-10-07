# Account Agent Instance Architecture

> **Goal**: Explicit agent instances per account, eliminating routing complexity while enabling flexible multi-agent deployments.

## Core Concept

**Agent Instances**: Each account has named agent instances (not just agent types). An instance is a specific configuration of an agent type.

```
Account "acme":
  - simple-chat-customer-support   (type: simple_chat, temp: 0.3, tools: [email])
  - simple-chat-lead-qualification (type: simple_chat, temp: 0.7, tools: [crm])
  - sales-enterprise               (type: sales_agent, temp: 0.5, tools: [crm, email])
  - sales-smb                      (type: sales_agent, temp: 0.8, tools: [crm])
```

## URL Structure

```
/accounts/{account-slug}/agents/{agent-instance-slug}/chat
/accounts/{account-slug}/agents/{agent-instance-slug}/stream
```

**Examples**:
```
POST /accounts/acme/agents/simple-chat-customer-support/chat
GET  /accounts/acme/agents/sales-enterprise/stream?message=hello
POST /accounts/default/agents/simple-chat/chat
```

**Key**: `{agent-instance-slug}` uniquely identifies a specific agent instance within an account.

## Multi-Tenancy Schema

### Entity Relationships

```
accounts (1) ──< (M) user_roles (M) >── (1) users
    │                    │
    │                    └──> (1) roles
    │
    ├──< (M) sessions
    │           └──< (M) messages
    │
    ├──< (M) llm_requests
    │
    └──< (M) agent_instances (config files)
```

**Key Relationships**:
- **Account ↔ User**: Many-to-many through `user_roles` (user can belong to multiple accounts)
- **User ↔ Account ↔ Role**: Account-scoped roles (user is "admin" in account A, "viewer" in account B)
- **Account → Sessions**: One-to-many (account has many sessions, both anonymous and authenticated)
- **Account → Agent Instances**: One-to-many (account has many agent instance configs)
- **Session → User**: Optional (nullable for anonymous sessions)

### Permission Checking Pattern

```python
async def check_permission(user_id: UUID, account_slug: str, permission: str) -> bool:
    """Check if user has permission in account."""
    query = """
        SELECT r.permissions 
        FROM user_roles ur
        JOIN accounts a ON ur.account_id = a.id
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = $1 AND a.slug = $2
    """
    
    row = await db.fetchrow(query, user_id, account_slug)
    if not row:
        return False
    
    permissions = row['permissions']
    return permissions.get('all') or permissions.get(permission)

# Usage
if not await check_permission(user_id, "acme", "use_agents"):
    raise HTTPException(403, "Insufficient permissions")
```

## Configuration Structure

```
config/agent_configs/
  {account-slug}/
    {agent-instance-slug}/
      config.yaml
```

**Example**: `config/agent_configs/acme/simple-chat-customer-support/config.yaml`
```yaml
agent_type: "simple_chat"              # Which agent function to call
account: "acme"
instance_name: "simple-chat-customer-support"

llm:
  model: "moonshotai/kimi-k2-0905"
  temperature: 0.3
  max_tokens: 2000

tools:
  vector_search:
    enabled: true
  email_summary:
    enabled: true

context_management:
  history_limit: 10
```

## Implementation

### Agent Instance Loader

```python
async def load_agent_instance(account_slug: str, instance_slug: str) -> AgentInstance:
    """
    Load agent instance configuration.
    
    Returns:
        AgentInstance with agent_type, config, account info
    """
    config_path = f"config/agent_configs/{account_slug}/{instance_slug}/config.yaml"
    config = load_yaml(config_path)
    
    return AgentInstance(
        account=account_slug,
        instance_name=instance_slug,
        agent_type=config["agent_type"],
        config=config
    )
```

### Endpoint Handler

```python
@app.post("/accounts/{account_slug}/agents/{instance_slug}/chat")
async def agent_instance_chat(
    account_slug: str,
    instance_slug: str,
    chat_request: ChatRequest,
    request: Request
):
    # Load instance
    instance = await load_agent_instance(account_slug, instance_slug)
    
    # Load conversation history
    session = get_current_session(request)
    history = await load_chat_history(
        session.id, 
        limit=instance.config["context_management"]["history_limit"]
    )
    
    # Call agent function based on type
    if instance.agent_type == "simple_chat":
        return await simple_chat(
            message=chat_request.message,
            session_id=str(session.id),
            message_history=history,
            config=instance.config
        )
    elif instance.agent_type == "sales_agent":
        return await sales_agent(
            message=chat_request.message,
            session_id=str(session.id),
            message_history=history,
            config=instance.config
        )
    else:
        raise ValueError(f"Unknown agent type: {instance.agent_type}")
```

### Streaming Handler

```python
@app.get("/accounts/{account_slug}/agents/{instance_slug}/stream")
async def agent_instance_stream(
    account_slug: str,
    instance_slug: str,
    message: str,
    request: Request
):
    instance = await load_agent_instance(account_slug, instance_slug)
    session = get_current_session(request)
    history = await load_chat_history(session.id, limit=instance.config["context_management"]["history_limit"])
    
    async def event_generator():
        if instance.agent_type == "simple_chat":
            stream_func = simple_chat_stream
        elif instance.agent_type == "sales_agent":
            stream_func = sales_agent_stream
        else:
            yield {"event": "error", "data": json.dumps({"message": f"Unknown agent type: {instance.agent_type}"})}
            return
        
        async for event in stream_func(message, str(session.id), history, instance.config):
            yield event
    
    return EventSourceResponse(event_generator())
```

## Agent Functions

Agent functions accept instance-specific config:

```python
async def simple_chat(
    message: str,
    session_id: str,
    message_history: Optional[List[ModelMessage]] = None,
    config: Optional[Dict] = None
) -> Dict:
    """
    Simple chat agent using Pydantic AI.
    
    Args:
        config: Instance-specific configuration (overrides defaults)
    """
    # Create agent with instance config
    agent = await create_simple_chat_agent(config)
    deps = await SessionDependencies.create(session_id)
    
    # Run agent
    result = await agent.run(message, deps=deps, message_history=message_history)
    
    # Track cost with instance info
    await tracker.track_llm_request(
        account=config.get("account"),
        agent_instance=config.get("instance_name"),
        agent_type="simple_chat",
        ...
    )
    
    return {"response": result.output, "usage": result.usage(), ...}
```

## Implementation Details

### SSE Format & Event Types

**Format**: Enhanced SSE with event types for semantic messages

```python
# Text chunks
yield {"event": "message", "data": chunk}

# Completion
yield {"event": "done", "data": ""}

# Errors  
yield {"event": "error", "data": json.dumps({"message": "..."})}
```

**Benefits**: Better semantics than data-only format, standard pattern, supports reconnection and typing indicators.

### Pydantic AI Streaming Pattern

```python
async def simple_chat_stream(message: str, session_id: str, message_history: Optional[List[ModelMessage]] = None, config: Optional[Dict] = None):
    """Streaming version using Pydantic AI agent.run_stream()"""
    agent = await create_simple_chat_agent(config)
    deps = await SessionDependencies.create(session_id)
    
    chunks = []
    try:
        async with agent.run_stream(message, deps=deps, message_history=message_history) as result:
            # Stream with delta=True for incremental chunks only
            async for chunk in result.stream_text(delta=True):
                chunks.append(chunk)
                yield {"event": "message", "data": chunk}
            
            # Track cost after stream completes
            usage = result.usage()
            await tracker.track_llm_request(
                account=config.get("account"),
                agent_instance=config.get("instance_name"),
                agent_type=config.get("agent_type"),
                tokens={"prompt": usage.request_tokens, "completion": usage.response_tokens, "total": usage.total_tokens},
                completion_status="complete"
            )
            
            yield {"event": "done", "data": ""}
            
    except Exception as e:
        # Save partial response and error
        await tracker.track_llm_request(..., completion_status="partial")
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
```

**Key Features**:
- `delta=True` yields only new content (perfect for SSE)
- Usage data available after stream completes
- Context manager for automatic cleanup

### Message History Conversion

**Database Format**: `role` = `"human"` or `"assistant"`  
**Pydantic AI Format**: `ModelRequest` / `ModelResponse` with typed parts

```python
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart

def db_message_to_model_message(db_msg) -> ModelMessage:
    """Convert database message to Pydantic AI ModelMessage format."""
    if db_msg.role == "human":
        return ModelRequest(parts=[UserPromptPart(content=db_msg.content)])
    else:  # assistant
        return ModelResponse(parts=[TextPart(content=db_msg.content)])
```

### Error Handling & Retry Logic

**Two-Level Strategy**:
1. **Transport-level** (handled by Pydantic AI): HTTP errors, connection errors
2. **Application-level**: Stream-specific failures

```python
async def simple_chat_stream(..., _retry_count=0):
    try:
        async with agent.run_stream(...) as result:
            # ... stream processing
    except Exception as e:
        if _retry_count == 0:
            # Retry once at application level
            async for event in simple_chat_stream(..., _retry_count=1):
                yield event
        else:
            # Second failure - save partial and error
            await save_partial_response(chunks, error=e)
            yield {"event": "error", "data": json.dumps({"message": str(e)})}
```

### Partial Response Persistence

Save incomplete responses with metadata:

```python
await message_service.save_message(
    session_id=session.id,
    role="assistant",
    content="".join(chunks),
    metadata={
        "partial": True,
        "error": str(error),
        "completion_status": "partial",
        "chunks_received": len(chunks)
    }
)
```

**UI Treatment**: Display with visual indicator: "⚠️ Response incomplete due to error"

### Frontend Error Handling

```javascript
// Add SSE event listeners
sse.addEventListener('error', (ev) => {
    const error = JSON.parse(ev.data);
    
    // Stop streaming indicator
    setStreaming(false);
    
    // Show toast notification
    showToast('error', 'Connection error. Please try again.');
    
    // Preserve partial response if any
    if (activeBotDiv && activeBotDiv.textContent.trim()) {
        activeBotDiv.classList.add('partial-response');
        const warning = document.createElement('div');
        warning.className = 'error-notice';
        warning.textContent = '⚠️ Response incomplete';
        activeBotDiv.appendChild(warning);
    }
});

sse.addEventListener('done', () => {
    setStreaming(false);
});
```

### Testing Strategy

**Unit Tests** (fast, always run):
```python
from pydantic_ai.models.function import FunctionModel

def test_stream_format():
    # Use FunctionModel for predictable responses
    model = FunctionModel(lambda msgs, info: ModelResponse(...))
    agent = Agent(model)
    # Test streaming behavior
```

**Integration Tests** (slow, optional):
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("RUN_INTEGRATION_TESTS"))
async def test_real_openrouter_streaming():
    # Real API call with test key
    result = await simple_chat_stream("test", session_id)
    # Verify actual behavior
```

**CI/CD**: Unit tests every commit, integration tests nightly or on release branches.

## Cost Tracking

Track per instance, not just per agent type:

```python
llm_requests:
  - account: "acme"
  - agent_instance: "simple-chat-customer-support"
  - agent_type: "simple_chat"
  - model: "moonshotai/kimi-k2-0905"
  - tokens: {...}
  - cost: 0.0023
```

**Benefits**:
- Cost per instance
- Compare instance performance
- Identify expensive configurations
- Account-level billing

## Legacy Endpoint Migration

**Option A: Reverse Proxy (Transparent)**
```python
@app.post("/chat")
async def legacy_chat(request: Request):
    # Map to default instance
    return await agent_instance_chat("default", "simple-chat", request)

@app.get("/events/stream")
async def legacy_stream(request: Request):
    return await agent_instance_stream("default", "simple-chat", request)
```

**Option B: 301 Redirect**
```python
@app.post("/chat")
async def legacy_chat():
    return RedirectResponse("/accounts/default/agents/simple-chat/chat", status_code=301)
```

**Recommendation**: Option A during transition, Option B for final deprecation.

## Frontend Changes

**Before**:
```javascript
fetch('/events/stream?message=hello')
```

**After**:
```javascript
const account = 'acme';  // From session/config
const instance = 'simple-chat-customer-support';  // From UI selection or default

fetch(`/accounts/${account}/agents/${instance}/stream?message=hello`)
```

**Agent Selection UI**:
```javascript
// Fetch available instances for account
const response = await fetch('/accounts/acme/agents');
const instances = await response.json();
// [
//   {slug: "simple-chat-customer-support", name: "Customer Support Chat", type: "simple_chat"},
//   {slug: "sales-enterprise", name: "Enterprise Sales", type: "sales_agent"}
// ]

// User selects from dropdown
<select id="agent-selector">
  <option value="simple-chat-customer-support">Customer Support Chat</option>
  <option value="sales-enterprise">Enterprise Sales</option>
</select>
```

## What This Eliminates

From complex routing design:
- ❌ Agent registry (`AGENT_REGISTRY`)
- ❌ Router agent with decision logic
- ❌ Default agent selection
- ❌ Agent enable/disable flags in app.yaml
- ❌ Complex dispatcher with type checking

Keeps (simplified):
- ✅ Agent functions (`simple_chat`, `sales_agent`)
- ✅ Streaming functions (`simple_chat_stream`, `sales_agent_stream`)
- ✅ Instance-specific configuration
- ✅ Cost tracking (now per instance)
- ✅ Pydantic AI integration

## Benefits

**Explicitness**: URL specifies exact instance, no guessing or routing.

**Flexibility**: Each instance has independent configuration.

**Multi-tenancy**: Account isolation built into URL structure.

**Cost Tracking**: Per-instance costs, not just per-type.

**Simplicity**: No registry, no router, no complex dispatcher.

**Scalability**: Add instances by adding config files, no code changes.

## Implementation Approach

**Strategy**: Phased deployment with zero risk to existing endpoints. New account-instance architecture runs in parallel with legacy endpoints initially.

**Key Principle**: The new `/accounts/` URL pattern doesn't conflict with existing endpoints (`/chat`, `/events/stream`), enabling safe parallel operation during development and testing.

**Phases**:
- **Phase 1**: Build new infrastructure alongside existing code (zero production impact)
- **Phase 2**: Migrate existing endpoints internally while maintaining backward compatibility
- **Phase 3**: Deprecation and cleanup (optional, can be delayed indefinitely)

---

## Phase 1: Build New Infrastructure

**Goal**: Implement account-instance architecture without touching existing endpoints.

**Risk Level**: Low (no production impact, completely isolated)

### Deliverables

**1. Database Schema Updates**

**Create Core Tables**:
```sql
-- Accounts table (first-class entity for multi-tenancy)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) UNIQUE NOT NULL,           -- URL-friendly identifier (e.g., "acme", "default")
    name VARCHAR(255) NOT NULL,                   -- Display name (e.g., "Acme Corp")
    status VARCHAR(20) DEFAULT 'active',          -- active, suspended, deleted
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT accounts_slug_format CHECK (slug ~ '^[a-z0-9-]+$')
);

-- Users table (authentication and identity)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),                   -- Nullable for OAuth/SSO users
    full_name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',          -- active, suspended, deleted
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Roles table (define available roles)
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,             -- owner, admin, member, viewer
    description TEXT,
    permissions JSONB DEFAULT '{}'::jsonb,        -- Role capabilities
    created_at TIMESTAMP DEFAULT NOW()
);

-- User-Account-Role mapping (many-to-many, account-scoped roles)
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),         -- Who granted this role
    
    UNIQUE(user_id, account_id)                   -- One role per user per account
);

-- Indexes for performance
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_account_id ON user_roles(account_id);
CREATE INDEX idx_users_email ON users(email);

-- Seed default account
INSERT INTO accounts (slug, name, status) 
VALUES ('default', 'Default Account', 'active');

-- Seed initial roles
INSERT INTO roles (name, description, permissions) VALUES
('owner', 'Full account ownership and billing', '{"all": true}'::jsonb),
('admin', 'Manage instances and users', '{"manage_instances": true, "manage_users": true, "view_billing": true}'::jsonb),
('member', 'Use agents and view history', '{"use_agents": true, "view_history": true}'::jsonb),
('viewer', 'Read-only access', '{"view_history": true}'::jsonb);
```

**Update Existing Tables**:
```sql
-- Sessions: Support both anonymous and authenticated sessions
ALTER TABLE sessions 
    ADD COLUMN account_id UUID REFERENCES accounts(id),
    ADD COLUMN account_slug VARCHAR(100),          -- Denormalized for query performance
    ADD COLUMN agent_instance VARCHAR(100),
    ADD COLUMN user_id UUID REFERENCES users(id);  -- Nullable for anonymous sessions

-- LLM Requests: Track costs per account/instance
ALTER TABLE llm_requests 
    ADD COLUMN account_id UUID REFERENCES accounts(id),
    ADD COLUMN account_slug VARCHAR(100),          -- Denormalized for query performance
    ADD COLUMN agent_instance VARCHAR(100),
    ADD COLUMN agent_type VARCHAR(50),
    ADD COLUMN completion_status VARCHAR(20) DEFAULT 'complete';

-- Indexes for common queries
CREATE INDEX idx_sessions_account_id ON sessions(account_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_llm_requests_account_id ON llm_requests(account_id);
CREATE INDEX idx_llm_requests_agent_instance ON llm_requests(agent_instance);

-- Backfill existing data to default account
UPDATE sessions SET 
    account_id = (SELECT id FROM accounts WHERE slug = 'default'),
    account_slug = 'default'
WHERE account_id IS NULL;

UPDATE llm_requests SET 
    account_id = (SELECT id FROM accounts WHERE slug = 'default'),
    account_slug = 'default'
WHERE account_id IS NULL;
```

**Design Decisions**:
- **accounts table**: Required for proper multi-tenancy, account management, and cost tracking
- **Hybrid FKs + denormalized slugs**: `account_id` (FK for integrity) + `account_slug` (for query performance)
- **Account-scoped roles**: User can be "admin" in one account, "viewer" in another
- **Anonymous sessions**: `user_id` is nullable, allowing unauthenticated usage
- **Backward compatibility**: Existing data maps to "default" account automatically

### Phasing Strategy for User/Role Infrastructure

**Phase 1a: Accounts Only (Immediate)**
- Create `accounts` table
- Add `account_id`/`account_slug` to `sessions` and `llm_requests`
- Seed "default" account
- **Skip authentication**: Leave `users`, `roles`, `user_roles` tables for Phase 1b
- All sessions remain anonymous initially
- Focus: Enable account-instance URL structure and cost tracking

**Phase 1b: Users & Roles (When Authentication Needed)**
- Create `users`, `roles`, `user_roles` tables
- Add `user_id` to `sessions` (nullable)
- Implement authentication endpoints (`/auth/login`, `/auth/register`)
- Add permission checking to agent endpoints
- **Trigger**: When you need to distinguish users or enforce permissions

**Why Separate**:
- Can deploy account-instance architecture immediately without auth complexity
- Anonymous usage still works (sessions without `user_id`)
- Add authentication when business needs it (e.g., paid tiers, user management)
- Reduces Phase 1 scope and risk

**2. Default Instance Configuration**

Create: `config/agent_configs/default/simple-chat/config.yaml`
```yaml
agent_type: "simple_chat"
account: "default"
instance_name: "simple-chat"
llm:
  model: "moonshotai/kimi-k2-0905"
  temperature: 0.3
  max_tokens: 2000
tools:
  vector_search:
    enabled: true
context_management:
  history_limit: 10
```

**3. Agent Instance Infrastructure**

Create: `backend/app/agents/instance_loader.py`
- `AgentInstance` data class
- `load_agent_instance(account, instance)` function
- Config loading and validation

**4. Streaming Function**

Add to: `backend/app/agents/simple_chat.py`
- `simple_chat_stream()` function
- Uses Pydantic AI `agent.run_stream()`
- Yields SSE events with proper format
- Tracks costs after completion

**5. New Endpoint Handlers**

Create: `backend/app/api/account_agents.py`
```python
@router.post("/accounts/{account}/agents/{instance}/chat")
async def agent_instance_chat(...)

@router.get("/accounts/{account}/agents/{instance}/stream")
async def agent_instance_stream(...)

@router.get("/accounts/{account}/agents")
async def list_account_agents(...)
```

**6. Cost Tracking Updates**

Update: `backend/app/services/llm_request_tracker.py`
- Record `account`, `agent_instance`, `agent_type`
- Support new schema columns

**7. Tests**
- Unit tests for instance loader
- Unit tests for streaming function
- Integration tests for new endpoints
- Cost tracking verification

### Phase 1 Dependencies

```
1. Database migration (can run immediately)
   ↓
2. AgentInstance class + Cost tracking updates (parallel)
   ↓
3. Instance loader ← Config files
   ↓
4. simple_chat_stream() (can be parallel with #3)
   ↓
5. Endpoint handlers (needs #3 and #4)
   ↓
6. Tests
```

### Phase 1 Validation

Before proceeding to Phase 2:
- [ ] New endpoints work with real OpenRouter API
- [ ] Cost tracking records account/instance/agent_type correctly
- [ ] Streaming SSE format matches expected behavior
- [ ] Multiple instances can coexist (test with 2+ configs)
- [ ] Frontend can successfully call new URLs
- [ ] Session management works with account/instance

**Result**: New architecture fully functional, existing endpoints completely untouched.

---

## Phase 2: Internal Migration

**Goal**: Migrate existing endpoints to use new infrastructure internally while maintaining exact same external behavior.

**Risk Level**: Medium (changes production code, requires careful compatibility)

### Deliverables

**1. Update Agent Functions**

Modify: `backend/app/agents/simple_chat.py`
```python
async def simple_chat(
    message: str,
    session_id: str,
    message_history: Optional[List[ModelMessage]] = None,
    config: Optional[Dict] = None  # NEW: Optional instance config
):
    # If config provided, use it; otherwise load from existing cascade
    if config is None:
        config = await get_agent_config("simple_chat")
```
- Backward compatible (config is optional)
- Existing callers unaffected

**2. Backward Compatibility Helper**

Create: `backend/app/agents/instance_loader.py`
```python
async def load_instance_or_default(
    account: Optional[str] = None,
    instance: Optional[str] = None
) -> AgentInstance:
    """Load instance or fall back to default/simple-chat."""
    if account is None:
        account = "default"
    if instance is None:
        instance = "simple-chat"
    
    return await load_agent_instance(account, instance)
```

**3. Migrate `/chat` Endpoint**

Update: `backend/app/main.py`
```python
@app.post("/chat")
async def legacy_chat(request: Request):
    # Load default instance
    instance = await load_instance_or_default()
    
    # Use new infrastructure internally
    result = await simple_chat(
        message=message,
        session_id=str(session.id),
        message_history=history,
        config=instance.config  # NEW
    )
    
    # Same response format as before
    return PlainTextResponse(result["response"])
```

**4. Migrate `/events/stream` Endpoint**

Update: `backend/app/main.py`
```python
@app.get("/events/stream")
async def legacy_sse_stream(request: Request):
    instance = await load_instance_or_default()
    
    async def event_generator():
        # Use new streaming function
        async for event in simple_chat_stream(
            message=message,
            session_id=str(session.id),
            message_history=history,
            config=instance.config
        ):
            yield event
    
    return EventSourceResponse(event_generator())
```

**5. Session Management Updates**

Update: `backend/app/middleware/simple_session_middleware.py`
- Optionally track account/instance in session
- Default to None if not provided (backward compatible)

**6. Tests**
- Backward compatibility tests (old URLs work exactly as before)
- Response format verification
- Cost tracking works for both old and new URLs
- Session data migration handling

### Phase 2 Dependencies

```
1. Phase 1 fully validated
   ↓
2. Update simple_chat() signature (backward compatible)
   ↓
3. Create load_instance_or_default() helper
   ↓
4. Test updated simple_chat() with both paths
   ↓
5. Migrate /chat endpoint (simpler, non-streaming)
   ↓
6. Test /chat thoroughly
   ↓
7. Migrate /events/stream endpoint (more complex)
   ↓
8. Test /events/stream thoroughly
   ↓
9. Update session middleware
   ↓
10. Integration tests + production monitoring
```

### Phase 2 Risk Mitigation

- **Gradual Rollout**: Feature flag to enable new path for subset of users
- **A/B Testing**: Route some traffic to new implementation, monitor differences
- **Extensive Logging**: Log both paths to compare behavior
- **Easy Rollback**: Keep old `openrouter_client.py` as fallback
- **Monitoring**: Track error rates, latency, cost tracking accuracy

### Phase 2 Validation

- [ ] `/chat` returns identical responses to before
- [ ] `/events/stream` SSE format unchanged
- [ ] Cost tracking works for all endpoints
- [ ] Session persistence works
- [ ] No increase in error rates
- [ ] Latency remains acceptable
- [ ] Old sessions without account/instance work correctly

**Result**: All endpoints use Pydantic AI and track costs properly, no breaking changes.

---

## Phase 3: Deprecation & Cleanup (Optional)

**Goal**: Migrate frontend to new URLs and remove legacy code.

**Risk Level**: Low (only affects new frontend code)

**Timeline**: Can be delayed indefinitely - Phase 1 and Phase 2 can coexist permanently if needed.

### Deliverables

**1. Frontend Migration**

Update: `backend/templates/index.html` and frontend clients
- Change URLs to `/accounts/{account}/agents/{instance}`
- Add agent selection UI
- Fetch available agents from `/accounts/{account}/agents`

**2. Deprecation Warnings**

Update: `backend/app/main.py`
```python
@app.post("/chat")
async def legacy_chat(request: Request):
    logger.warning(
        "DEPRECATED: /chat endpoint used. "
        "Migrate to /accounts/default/agents/simple-chat/chat"
    )
    # Still works, just logs warning
```

**3. Usage Monitoring**
- Track usage of old vs new endpoints
- Identify clients still using legacy URLs
- Communication plan for migration

**4. Code Cleanup**

Remove when ready:
- `backend/app/openrouter_client.py`
- Functions: `stream_chat_chunks()`, `chat_completion_content()`
- Old endpoint handlers (or convert to 410 Gone)

### Phase 3 Dependencies

```
1. Phase 2 running successfully in production
   ↓
2. Frontend migrated to new URLs
   ↓
3. Legacy endpoint usage < 5%
   ↓
4. Add deprecation warnings
   ↓
5. Monitor for 30+ days
   ↓
6. Remove old code
```

**Result**: Clean codebase with only account-instance architecture.

## Success Criteria

- [ ] All endpoints use Pydantic AI
- [ ] Cost tracking per instance
- [ ] Multiple instances per account work
- [ ] Legacy endpoints reverse proxy correctly
- [ ] Frontend can select instances
- [ ] Session tied to account/instance
- [ ] Streaming works with SSE events
- [ ] Backwards compatible during migration

## Authentication & Authorization (Phase 1b)

### Authentication Endpoints

```python
@router.post("/auth/register")
async def register(email: str, password: str, full_name: str):
    """Register new user (creates user, no account association yet)."""
    user = await create_user(email, password_hash, full_name)
    return {"user_id": user.id, "email": user.email}

@router.post("/auth/login")
async def login(email: str, password: str, response: Response):
    """Authenticate user and create session."""
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # Create session token (JWT or session cookie)
    token = create_session_token(user.id)
    response.set_cookie("session_token", token, httponly=True)
    
    # Update last login
    await db.execute("UPDATE users SET last_login_at = NOW() WHERE id = $1", user.id)
    
    return {"user_id": user.id, "email": user.email}

@router.post("/auth/logout")
async def logout(response: Response):
    """Clear session."""
    response.delete_cookie("session_token")
    return {"status": "logged_out"}
```

### Account Management Endpoints

```python
@router.post("/accounts")
async def create_account(name: str, slug: str, current_user: User = Depends(get_current_user)):
    """Create new account and assign creator as owner."""
    account = await create_account(name, slug)
    
    # Grant owner role to creator
    owner_role = await get_role("owner")
    await grant_role(user_id=current_user.id, account_id=account.id, role_id=owner_role.id)
    
    return {"account": account}

@router.get("/accounts/{account_slug}/users")
async def list_account_users(
    account_slug: str, 
    current_user: User = Depends(get_current_user)
):
    """List users in account with their roles."""
    # Check permission
    if not await check_permission(current_user.id, account_slug, "manage_users"):
        raise HTTPException(403, "Insufficient permissions")
    
    users = await get_account_users(account_slug)
    return {"users": users}

@router.post("/accounts/{account_slug}/users/{user_id}/role")
async def grant_user_role(
    account_slug: str, 
    user_id: UUID, 
    role_name: str,
    current_user: User = Depends(get_current_user)
):
    """Grant or update user role in account."""
    # Check permission
    if not await check_permission(current_user.id, account_slug, "manage_users"):
        raise HTTPException(403, "Insufficient permissions")
    
    account = await get_account_by_slug(account_slug)
    role = await get_role(role_name)
    
    await grant_role(
        user_id=user_id, 
        account_id=account.id, 
        role_id=role.id,
        created_by=current_user.id
    )
    
    return {"status": "role_granted"}
```

### Protected Agent Endpoints

```python
@router.post("/accounts/{account_slug}/agents/{instance_slug}/chat")
async def agent_instance_chat(
    account_slug: str,
    instance_slug: str,
    chat_request: ChatRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)  # Optional for backward compat
):
    """Agent chat with optional authentication."""
    
    # If authenticated, check permission
    if current_user:
        if not await check_permission(current_user.id, account_slug, "use_agents"):
            raise HTTPException(403, "Insufficient permissions")
    
    # Load instance
    instance = await load_agent_instance(account_slug, instance_slug)
    
    # Create or get session (associate with user if authenticated)
    session = get_or_create_session(request, account_slug, user_id=current_user.id if current_user else None)
    
    # Load history and run agent
    history = await load_chat_history(session.id, limit=instance.config["context_management"]["history_limit"])
    result = await simple_chat(
        message=chat_request.message,
        session_id=str(session.id),
        message_history=history,
        config=instance.config
    )
    
    return result
```

## Future Extensions

**Router Instance** (optional):
- Create instance: `router-auto` with `agent_type: "router"`
- Router decides which other instance to call
- URL: `/accounts/{account}/agents/router-auto/chat`
- Transparent to user, logs routing decisions

**Instance Discovery**:
```
GET /accounts/{account}/agents
  → List instances with metadata (name, description, capabilities)
```

**Instance Templates**:
```
config/agent_templates/
  simple-chat-default.yaml
  sales-agent-default.yaml
```
Copy template to create new instance.

**Per-Instance Permissions** (Phase 2+):
- Extend `user_roles` with `agent_instance_id` column
- Allow: "User can access sales-enterprise instance but not sales-smb"
- More granular than account-level permissions

