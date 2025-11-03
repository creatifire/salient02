<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Multi-Tenant Security Architecture

> **Last Updated**: January 31, 2025  
> **Status**: Design Discussion  
> **Priority**: 🔴 **CRITICAL** - Account isolation and API security

## Overview

Multi-tenant security architecture for protecting account-scoped APIs from unauthorized access and account hijacking. Addresses authentication, authorization, rate limiting, and account isolation.

**Current State**: ⚠️ **VULNERABLE** - Account slug in URL with no authentication/authorization  
**Goal**: Secure account-isolated endpoints with proper access control

---

## Security Requirements

### 1. Account Authentication
- **Requirement**: Verify caller identity before allowing account access
- **Current Gap**: No authentication - anyone can call `/accounts/{any_slug}/...`
- **Risk**: Account enumeration, unauthorized data access, cost attribution fraud

### 2. Account Authorization
- **Requirement**: Validate that authenticated caller owns/accesses requested account
- **Current Gap**: Session exists but not validated against `account_slug` in URL
- **Risk**: Account hijacking via URL manipulation

### 3. Account Isolation
- **Requirement**: Ensure data queries filter by `account_id` at all layers
- **Current State**: ✅ Data layer filters by account (good)
- **Risk**: Bypass risk if authorization layer fails

### 4. Rate Limiting
- **Requirement**: Prevent abuse and cost exhaustion per account
- **Current Gap**: No rate limiting implemented
- **Risk**: DoS attacks, runaway costs from malicious queries

---

## Threat Model

### Attack Vectors

| Attack | Description | Current Protection | Risk Level |
|--------|-------------|-------------------|------------|
| **Account Enumeration** | Guessing account slugs (`/accounts/acme/...`) | None | 🔴 HIGH |
| **Account Hijacking** | Accessing another account's data via URL | Data layer only | 🔴 HIGH |
| **Cost Attribution Fraud** | Making LLM calls billed to victim account | None | 🔴 HIGH |
| **DoS / Resource Exhaustion** | Flooding endpoints to exhaust resources | None | 🟡 MEDIUM |
| **Session Hijacking** | Stealing session cookies | HTTP-only cookies | 🟢 LOW |
| **Data Exfiltration** | Accessing another account's conversations | Data layer filters | 🟡 MEDIUM |

---

## Security Design Options

### Option A: API Key Authentication (Recommended for Phase 1)

**Pattern**: Per-account API keys for programmatic access

**Implementation**:
```python
# Request Header
X-Account-API-Key: sk_acme_abc123...

# Endpoint Validation
@router.post("/{account_slug}/agents/{instance_slug}/chat")
async def chat_endpoint(
    request: Request,
    account_slug: str = Path(...),
    instance_slug: str = Path(...),
    api_key: str = Header(..., alias="X-Account-API-Key")
):
    # Validate API key belongs to account_slug
    account = await validate_api_key(api_key, account_slug)
    if not account:
        raise HTTPException(403, "Invalid API key for account")
    
    # Proceed with authenticated request
    ...
```

**Pros**:
- ✅ Simple implementation
- ✅ Works for programmatic access (widgets, integrations)
- ✅ Per-account isolation
- ✅ Can track usage per key

**Cons**:
- ❌ Doesn't work for browser-based sessions
- ❌ Key management overhead
- ❌ Key rotation complexity

**Use Case**: Widgets, third-party integrations, programmatic access

---

### Option B: Session-Based Account Binding

**Pattern**: Bind session to account on first access, validate on subsequent requests

**Implementation**:
```python
# Session Model Extension
class Session(Base):
    account_id: Optional[UUID] = None  # Bound account
    account_binding_ip: Optional[str] = None  # IP when bound
    account_bound_at: Optional[datetime] = None

# Endpoint Validation
session = get_current_session(request)
if session.account_id:
    # Validate session account matches URL account
    if str(session.account_id) != account_slug_to_id(account_slug):
        raise HTTPException(403, "Session not authorized for this account")
else:
    # First access: bind session to account
    account = await load_account(account_slug)
    session.account_id = account.id
    await session.commit()
```

**Pros**:
- ✅ Works for browser sessions
- ✅ Transparent to user
- ✅ IP binding adds security layer

**Cons**:
- ❌ Account enumeration still possible
- ❌ IP binding fragile (mobile users, VPNs)
- ❌ Doesn't prevent initial unauthorized access

**Use Case**: Browser-based chat interfaces

---

### Option C: Hybrid: API Key + Session Binding

**Pattern**: API keys for programmatic, session binding for browsers, with account validation

**Implementation**:
```python
async def validate_account_access(
    request: Request,
    account_slug: str
) -> Account:
    """Validate caller has access to account via API key OR session."""
    
    # Check API key first (programmatic access)
    api_key = request.headers.get("X-Account-API-Key")
    if api_key:
        account = await validate_api_key(api_key, account_slug)
        if account:
            return account
    
    # Check session binding (browser access)
    session = get_current_session(request)
    if session and session.account_id:
        account = await load_account_by_id(session.account_id)
        if account and account.slug == account_slug:
            return account
    
    # No valid access
    raise HTTPException(403, "Unauthorized access to account")
```

**Pros**:
- ✅ Supports both access patterns
- ✅ Comprehensive coverage
- ✅ Flexible for different clients

**Cons**:
- ⚠️ More complex implementation
- ⚠️ Requires careful session binding logic

**Use Case**: Universal solution (browsers + programmatic)

---

### Option D: JWT-Based Authentication (Future)

**Pattern**: JWT tokens with account claims, signed with account-specific secret

**Pros**:
- ✅ Stateless
- ✅ Standard protocol
- ✅ Supports refresh tokens

**Cons**:
- ❌ More complex than needed for Phase 1
- ❌ Token management overhead
- ❌ Key rotation complexity

**Use Case**: Production SaaS with user management

---

## Recommended Approach: Hybrid (Option C)

### Phase 1: Core Authentication

**1. API Key Authentication**
- Add `api_keys` table: `account_id`, `key_hash`, `name`, `last_used_at`
- Per-account API key generation
- Header-based validation: `X-Account-API-Key`

**2. Session Account Binding**
- Extend `sessions` table: add `account_id` column
- First access: validate account exists, bind session
- Subsequent: validate `session.account_id == account_slug`

**3. Account Validation Middleware**
- Create `AccountAuthMiddleware` or dependency
- Validate before endpoint handlers execute
- Consistent error responses (401/403)

### Phase 2: Enhanced Security

**4. Rate Limiting**
- Per-account rate limits (Redis-based)
- Endpoint-specific limits (chat vs metadata)
- Cost-based throttling (max tokens per hour)

**5. Request Size Limits**
- Max message length (prevent resource exhaustion)
- Max history limit (prevent context window abuse)

**6. CORS Configuration**
- Production origins only
- Per-account origin whitelist (optional)

---

## Implementation Plan

### Phase 1A: API Key Authentication (2-3 days)

**Database Schema**:
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    key_hash TEXT NOT NULL,  -- bcrypt hash of actual key
    name VARCHAR(100),  -- "Widget Key", "Integration Key"
    created_at TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_account ON api_keys(account_id);
```

**Code Changes**:
- Create `backend/app/middleware/account_auth_middleware.py`
- Create `backend/app/services/api_key_service.py`
- Add FastAPI dependency: `get_authenticated_account()`
- Update endpoints to use dependency

**Migration**:
- Generate API keys for existing accounts
- Document key distribution process

---

### Phase 1B: Session Account Binding (1-2 days)

**Database Schema**:
```sql
ALTER TABLE sessions 
    ADD COLUMN account_id UUID REFERENCES accounts(id),
    ADD COLUMN account_bound_at TIMESTAMP,
    ADD INDEX idx_sessions_account ON sessions(account_id);
```

**Code Changes**:
- Update `SimpleSessionMiddleware` to support account binding
- Add account validation in `account_agents.py` endpoints
- Handle first-access binding logic

**Security**:
- IP address logging on account binding
- Optional: Require API key for initial account binding (prevents enumeration)

---

### Phase 2: Rate Limiting (2-3 days)

**Implementation**:
- Redis-based rate limiting (per account, per endpoint)
- Configurable limits per account tier
- Cost-based throttling (max tokens per period)

**Configuration**:
```yaml
rate_limiting:
  per_account:
    chat_requests_per_minute: 60
    chat_requests_per_hour: 1000
    max_tokens_per_hour: 100000
  per_endpoint:
    /chat: 60/minute
    /stream: 30/minute
    /metadata: 120/minute
```

---

### Phase 3: Enhanced Protections (Future)

- Request size limits
- Input sanitization enhancements
- Security headers (CSP, HSTS)
- Account-level CORS whitelists
- Audit logging

---

## Account Enumeration Prevention

### Current Problem
URLs expose account slugs: `/accounts/{account_slug}/...`

**Attack**: Attacker tries `/accounts/acme/...`, `/accounts/competitor/...`

### Mitigation Strategies

**Option 1: Opaque Account IDs**
- Replace `account_slug` with UUID in URLs: `/accounts/{account_id}/...`
- Keep slugs for internal use only
- **Pros**: Prevents enumeration
- **Cons**: Less user-friendly URLs

**Option 2: API Key Required**
- Require API key for all access
- Return 401 if no key provided
- **Pros**: Prevents unauthenticated enumeration
- **Cons**: Breaks browser-based access without additional flow

**Option 3: Rate Limit + Monitoring**
- Rate limit unauthenticated requests
- Alert on enumeration patterns
- **Pros**: Detects attacks
- **Cons**: Doesn't prevent enumeration, only mitigates

**Recommendation**: Option 1 (Opaque IDs) for sensitive accounts, Option 2 (API Key Required) for all programmatic access

---

## Data Layer Isolation

**Current State**: ✅ Data queries filter by `account_id`

**Verification Required**:
- ✅ `load_agent_instance()` filters by account
- ✅ Message queries filter by `agent_instance.account_id`
- ✅ Directory queries filter by account
- ⚠️ Ensure all service methods accept `account_id` parameter

**Defense in Depth**:
- Authorization layer (API key/session validation)
- Data layer (account_id filtering)
- Database constraints (if applicable)

---

## Rate Limiting Strategy

### Per-Account Limits

| Limit Type | Threshold | Purpose |
|------------|----------|---------|
| **Chat Requests** | 60/minute | Prevent spam |
| **Streaming Requests** | 30/minute | Prevent connection exhaustion |
| **Total Tokens** | 100K/hour | Prevent cost exhaustion |
| **Concurrent Streams** | 5 per account | Prevent resource exhaustion |

### Per-Endpoint Limits

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `/chat` | 60/minute | Standard chat flow |
| `/stream` | 30/minute | More resource-intensive |
| `/metadata` | 120/minute | Lightweight endpoint |
| `/history` | 60/minute | Prevent data scraping |

### Implementation

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=lambda: get_account_from_request(request))

@router.post("/{account_slug}/agents/{instance_slug}/chat")
@limiter.limit("60/minute")
async def chat_endpoint(...):
    ...
```

---

## Input Validation

### Current State
- ✅ Basic message length validation (`min_length=1`)
- ⚠️ No max length enforced
- ⚠️ No content sanitization

### Recommended Validation

```python
class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,  # Prevent resource exhaustion
        description="User message"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        # Basic sanitization
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Message cannot be empty")
        # Optional: Check for injection patterns
        return v
```

**Limits**:
- Max message: 10,000 characters
- Max history: Configurable per account (default: 50 messages)
- Request body size: 1MB max

---

## CORS Configuration

### Current State
```python
allow_origins=["http://localhost:4321", "http://127.0.0.1:4321"]
```

### Production Requirements

```python
# app.yaml
cors:
  production:
    allow_origins:
      - "https://app.salient.ai"
      - "https://*.salient.ai"  # Subdomain support
    allow_credentials: true
    allow_methods: ["GET", "POST"]
    allow_headers: ["Content-Type", "X-Account-API-Key"]
    max_age: 3600
```

### Per-Account Origins (Optional)

```yaml
accounts:
  acme:
    cors_origins:
      - "https://chat.acme.com"
      - "https://widget.acme.com"
```

---

## Security Headers

### Recommended Headers

```python
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

---

## Cost Protection

### Per-Account Cost Limits

```yaml
accounts:
  acme:
    limits:
      max_cost_per_day: 100.00  # USD
      max_requests_per_day: 10000
      alert_threshold: 0.8  # Alert at 80% of limit
```

### Implementation
- Track costs via `llm_requests` table
- Daily aggregation per account
- Throttle/block when limits exceeded
- Alert via Logfire/webhooks

---

## Audit Logging

### Required Events

```python
logfire.info('security.account_access_attempt', 
    account_slug=account_slug,
    method=request.method,
    endpoint=request.url.path,
    api_key_present=bool(api_key),
    session_account_id=str(session.account_id) if session else None,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

logfire.warning('security.account_access_denied',
    account_slug=account_slug,
    reason="invalid_api_key" | "session_mismatch" | "rate_limit_exceeded",
    ip_address=request.client.host
)
```

---

## Testing Security

### Test Cases

| Test | Description | Expected Result |
|------|-------------|-----------------|
| **Valid API Key** | Correct key for account | ✅ 200 OK |
| **Invalid API Key** | Wrong key for account | ❌ 403 Forbidden |
| **No API Key (Browser)** | Session-based access | ✅ 200 OK (after binding) |
| **Account Mismatch** | Session for account A, request account B | ❌ 403 Forbidden |
| **Enumeration Attempt** | Try random account slugs | ❌ 404 (don't reveal existence) |
| **Rate Limit** | Exceed per-account limit | ❌ 429 Too Many Requests |
| **Cost Limit** | Exceed daily cost limit | ❌ 429 Too Many Requests |

---

## Migration Strategy

### Phase 1: Non-Breaking (Week 1)
1. Add `api_keys` table (migration)
2. Add `account_id` to `sessions` table (migration)
3. Implement API key service (no endpoint changes)
4. Generate API keys for existing accounts

### Phase 2: Soft Enforcement (Week 2)
1. Add authentication middleware (optional enforcement)
2. Add account validation dependency (logs warnings)
3. Update endpoints to use dependency
4. Monitor Logfire for unauthorized attempts

### Phase 3: Hard Enforcement (Week 3)
1. Require API key OR session binding for all `/accounts/...` endpoints
2. Return 401/403 for unauthenticated requests
3. Update frontend clients to include API keys
4. Remove soft enforcement mode

---

## Open Questions

1. **API Key Distribution**: How do accounts receive API keys?
   - Admin dashboard (Phase 3+)
   - Email delivery (manual initially)
   - Self-service key generation (future)

2. **Key Rotation**: Automatic rotation policy?
   - 90-day expiration?
   - Manual rotation only?
   - Alert-based rotation?

3. **Session vs API Key**: When to use each?
   - Browser sessions: Session binding
   - Widgets/embeds: API key
   - Third-party: API key only

4. **Account Enumeration**: Accept risk or implement opaque IDs?
   - Opaque IDs: Better security, worse UX
   - Keep slugs: Better UX, accept enumeration risk with auth

---

## References

- [API Endpoints](endpoints.md) - Current endpoint structure
- [Data Model](datamodel.md) - Database schema
- [Multi-Tenant Architecture](../project-management/0022-multi-tenant-architecture.md) - Architecture details
- [Open Questions](open-questions.md#security) - Security-related open questions

---

**Last Updated**: January 31, 2025  
**Priority**: 🔴 **CRITICAL** - Implementation recommended before production deployment

