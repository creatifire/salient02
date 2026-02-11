# Chat API Token Security Architecture

Securing chat endpoints with API tokens managed by Salient instead of direct, unauthenticated access.

## Current State

**Endpoints**:
- `POST /accounts/{account_slug}/agents/{instance_slug}/chat`
- `GET /accounts/{account_slug}/agents/{instance_slug}/stream` (SSE)
- `GET /accounts/{account_slug}/agents/{instance_slug}/history`

**Security**:
- ❌ No authentication required
- ⚠️ Session middleware exists but not validated against account
- ⚠️ `multi-tenant-security.md` documents this as "VULNERABLE"
- ⚠️ Anyone can call any account's chat endpoint if they know the slug

**Current Clients**:
- `web/public/widget/chat-widget.js` - Embeddable chat widget
- `web/src/pages/demo/simple-chat.astro` - Demo chat interface
- `web/public/htmx-chat2.html` - HTMX-based chat
- Account-specific footers (WindRiver, Wyckoff, PrepExcellence, AgroFresh)

## Proposed Architecture

### API Token Model

**Salient-managed tokens** for each customer account:

```
Token Format: sk_{account_slug}_{random_32_chars}
Example: sk_windriver_a7b9c3d2e4f5g6h7i8j9k0l1m2n3o4p5

Pattern Breakdown:
- sk_         : Indicates "secret key"
- {slug}_     : Account identifier (readable)
- {random}    : 32-character random string (secure)
```

**Token Storage**:
```sql
api_tokens (
  id UUID PRIMARY KEY,
  account_id UUID REFERENCES accounts(id),
  token_hash TEXT NOT NULL,           -- bcrypt hash
  token_prefix TEXT NOT NULL,         -- First 8 chars for identification
  name VARCHAR(100),                  -- "Production Widget", "Dev Key"
  scopes TEXT[],                      -- ['chat:read', 'chat:write', 'history:read']
  created_at TIMESTAMP,
  created_by UUID,                    -- Admin user who created it
  last_used_at TIMESTAMP,
  expires_at TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  usage_count INT DEFAULT 0
);

CREATE INDEX idx_api_tokens_hash ON api_tokens(token_hash);
CREATE INDEX idx_api_tokens_account ON api_tokens(account_id);
CREATE INDEX idx_api_tokens_prefix ON api_tokens(token_prefix);
```

### Authentication Flow

**Client Request**:
```http
POST /accounts/windriver/agents/windriver_info_chat1/chat
Authorization: Bearer sk_windriver_a7b9c3d2e4f5g6h7i8j9k0l1m2n3o4p5
Content-Type: application/json

{
  "message": "What are your hours?"
}
```

**Server Validation**:
```python
async def validate_api_token(
    account_slug: str,
    token: str = Header(..., alias="Authorization")
) -> Account:
    """Validate API token belongs to account and has required scopes."""
    
    # Extract token from "Bearer {token}"
    if not token.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header format")
    
    token_value = token.replace("Bearer ", "")
    
    # Hash and lookup token
    token_hash = bcrypt.hash(token_value)
    db_token = await db.query(APIToken).filter_by(
        token_hash=token_hash,
        is_active=True
    ).first()
    
    if not db_token:
        logfire.warning('security.invalid_token_attempt',
            account_slug=account_slug,
            token_prefix=token_value[:8]
        )
        raise HTTPException(401, "Invalid API token")
    
    # Check token hasn't expired
    if db_token.expires_at and db_token.expires_at < datetime.now():
        raise HTTPException(401, "API token has expired")
    
    # Verify token belongs to requested account
    account = await db.query(Account).filter_by(id=db_token.account_id).first()
    if account.slug != account_slug:
        logfire.error('security.token_account_mismatch',
            account_slug=account_slug,
            token_account=account.slug,
            token_id=str(db_token.id)
        )
        raise HTTPException(403, "API token not valid for this account")
    
    # Update last_used_at and usage_count
    db_token.last_used_at = datetime.now()
    db_token.usage_count += 1
    await db.commit()
    
    logfire.info('security.token_validated',
        account_slug=account.slug,
        token_name=db_token.name,
        scopes=db_token.scopes
    )
    
    return account
```

**Endpoint Protection**:
```python
@router.post("/{account_slug}/agents/{instance_slug}/chat")
async def chat_endpoint(
    account_slug: str = Path(...),
    instance_slug: str = Path(...),
    chat_request: ChatRequest,
    account: Account = Depends(validate_api_token)
):
    agent_instance = await load_agent_instance(
        account_id=account.id,
        instance_slug=instance_slug
    )
    
    if not agent_instance:
        raise HTTPException(404, "Agent instance not found")
    
    # Proceed with chat logic...
```

## Impact Analysis

### 1. Client-Side Changes

**Astro Server Endpoints** (Recommended - No Token in Client):

**New Server Endpoint**:
```typescript
// src/pages/api/chat.ts
import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  try {
    const { message, accountSlug, agentSlug } = await request.json();
    
    // Validate inputs
    if (!message || !accountSlug || !agentSlug) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400 }
      );
    }
    
    // Token stored securely server-side
    const API_TOKEN = import.meta.env.API_TOKEN;
    const CHAT_API_URL = import.meta.env.CHAT_API_URL || 'https://api.salient.ai';
    
    // Proxy to Salient chat API
    const response = await fetch(
      `${CHAT_API_URL}/accounts/${accountSlug}/agents/${agentSlug}/chat`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      }
    );
    
    if (!response.ok) {
      const error = await response.text();
      return new Response(error, { status: response.status });
    }
    
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    console.error('Chat proxy error:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500 }
    );
  }
};
```

**Client Update** (widget, demo pages):

**Before**:
```javascript
const response = await fetch(
  `https://api.salient.ai/accounts/${accountSlug}/agents/${agentSlug}/chat`,
  {
    method: 'POST',
    body: JSON.stringify({ message: userInput })
  }
);
```

**After**:
```javascript
// Call Astro server endpoint (no token needed in client)
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: userInput,
    accountSlug: 'windriver',
    agentSlug: 'windriver_info_chat1'
  })
});
```

**Affected Files**:
- `src/pages/api/chat.ts` (NEW)
- `web/public/widget/chat-widget.js` (UPDATE to use `/api/chat`)
- `web/src/pages/demo/simple-chat.astro` (UPDATE to use `/api/chat`)
- `web/public/htmx-chat2.html` (UPDATE to use `/api/chat`)
- All account-specific footer components (UPDATE to use `/api/chat`)

**For Embeddable Widget** (external sites):

Widget can still be embedded but must call back to the Astro site's server endpoint:

```javascript
// Widget configuration
window.ChatWidget.init({
  account: 'windriver',
  agent: 'windriver_info_chat1',
  apiEndpoint: 'https://windriver-site.com/api/chat'  // Astro server endpoint
});
```

**Alternative: Client-Side Token for Standalone Widget**

```javascript
const response = await fetch(
  `https://api.salient.ai/accounts/${accountSlug}/agents/${agentSlug}/chat`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${widget.dataset.apiToken}`
    },
    body: JSON.stringify({ message: userInput })
  }
);
```

Use Astro server endpoints for site-embedded chat. Only use client-side tokens for standalone widget deployments on third-party sites.

### 2. Token Distribution

**Option A: Astro Server Endpoints (Recommended)**

```javascript
// astro.config.mjs
export default defineConfig({
  output: 'hybrid',
  adapter: cloudflare() // or vercel(), netlify(), node()
});
```

```bash
# .env (server-side only)
API_TOKEN=sk_windriver_a7b9c3d2e4f5g6h7i8j9k0l1m2n3o4p5
CHAT_API_URL=https://api.salient.ai
```

**Option B: Client-Side Token (Fully Static)**

```javascript
const API_TOKEN = import.meta.env.PUBLIC_WINDRIVER_API_TOKEN;

const response = await fetch(
  `/accounts/${accountSlug}/agents/${agentSlug}/chat`,
  {
    headers: { 'Authorization': `Bearer ${API_TOKEN}` },
    body: JSON.stringify({ message })
  }
);
```

Tokens visible in client JavaScript.

### 3. Static Site Generation Impact

**Astro Hybrid Mode** (static pages + server endpoints):

```javascript
// astro.config.mjs
export default defineConfig({
  output: 'hybrid',        // Enable server endpoints
  adapter: cloudflare(),   // or vercel(), netlify(), node()
  
  // Mark API routes as server-rendered
  integrations: []
});
```

**Build-Time vs Runtime**:

| Approach | Token Location | When Token Used | Security |
|----------|---------------|-----------------|----------|
| **Hybrid (Recommended)** | Server `.env` only | Runtime (per request) | ✅ Secure |
| **Fully Static** | Client JavaScript | Build time (embedded) | ⚠️ Exposed |

**Build Service Changes** (for hybrid mode):

```typescript
// build-service/export-static-site.ts
async function buildStaticSite(siteConfig: SiteConfig) {
  // 1. Fetch or generate API token for this site
  const apiToken = await getOrCreateAPIToken(siteConfig.account_id, {
    name: `Static Site - ${siteConfig.domain}`,
    scopes: ['chat:read', 'chat:write', 'history:read']
  });
  
  // 2. Set environment variables for Astro build
  // NOTE: NO PUBLIC_ prefix = server-side only
  process.env.API_TOKEN = apiToken;
  process.env.CHAT_API_URL = 'https://api.salient.ai';
  
  // 3. Run Astro build (hybrid mode)
  await exec('npm run build');
  
  // 4. Deploy to platform that supports server endpoints
  // Cloudflare Pages, Vercel, Netlify all support Astro server endpoints
  await deployToPlatform(siteConfig);
}
```

**Deployment Platforms**:

| Platform | Astro Adapter | Server Endpoints | Environment Variables |
|----------|--------------|------------------|----------------------|
| **Cloudflare Pages** | `@astrojs/cloudflare` | ✅ Workers | ✅ Encrypted env vars |
| **Vercel** | `@astrojs/vercel` | ✅ Serverless | ✅ Encrypted env vars |
| **Netlify** | `@astrojs/netlify` | ✅ Functions | ✅ Encrypted env vars |
| **Self-hosted** | `@astrojs/node` | ✅ Node.js | ✅ `.env` files |

**Security Note**: With Astro server endpoints, tokens are **never exposed** to client-side JavaScript. They remain in encrypted environment variables on the hosting platform.

### 4. Token Rotation

**When**:
- Security breach detected
- Token exposed in logs/errors
- Account ownership change

**Process**:
1. Generate new token
2. Update client configurations
3. Rebuild and redeploy static sites
4. Monitor old token usage
5. Deactivate old token

```sql
api_tokens (
  ...
  rotation_scheduled_at TIMESTAMP,
  replaced_by UUID REFERENCES api_tokens(id)
);
```

### 5. Rate Limiting & Cost Protection

```sql
token_rate_limits (
  token_id UUID REFERENCES api_tokens(id),
  requests_per_minute INT DEFAULT 60,
  requests_per_hour INT DEFAULT 1000,
  requests_per_day INT DEFAULT 10000,
  max_tokens_per_hour INT DEFAULT 100000
);
```

```python
from slowapi import Limiter

def get_token_identifier(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        return f"token:{token[:8]}"
    return get_remote_address(request)

limiter = Limiter(key_func=get_token_identifier)

@router.post("/{account_slug}/agents/{instance_slug}/chat")
@limiter.limit("60/minute")
async def chat_endpoint(...):
    ...
```

**Cost Tracking**:
```sql
ALTER TABLE llm_requests 
  ADD COLUMN token_id UUID REFERENCES api_tokens(id);

SELECT 
  t.name, t.account_id,
  SUM(lr.total_cost) AS total_cost,
  COUNT(*) AS request_count
FROM llm_requests lr
JOIN api_tokens t ON lr.token_id = t.id
WHERE lr.created_at > NOW() - INTERVAL '24 hours'
GROUP BY t.id, t.name, t.account_id;
```

### 6. Admin UI

**Features**:
- List all tokens for account
- Create new token (one-time display)
- Revoke/deactivate token
- View token usage stats
- Set expiration date
- Configure rate limits
- View cost attribution

**Endpoints**:
```python
# POST /api/admin/accounts/{account_id}/tokens
async def create_token(account_id: UUID, token_request: TokenRequest):
    token = f"sk_{account.slug}_{secrets.token_urlsafe(24)}"
    token_hash = bcrypt.hash(token)
    
    db_token = APIToken(
        account_id=account_id,
        token_hash=token_hash,
        token_prefix=token[:8],
        name=token_request.name,
        scopes=token_request.scopes,
        expires_at=token_request.expires_at
    )
    await db.add(db_token)
    await db.commit()
    
    return {
        "token": token,
        "token_id": str(db_token.id),
        "expires_at": db_token.expires_at
    }

# GET /api/admin/accounts/{account_id}/tokens
async def list_tokens(account_id: UUID):
    tokens = await db.query(APIToken).filter_by(account_id=account_id).all()
    return [{
        "id": str(t.id),
        "name": t.name,
        "token_prefix": t.token_prefix,
        "scopes": t.scopes,
        "created_at": t.created_at,
        "last_used_at": t.last_used_at,
        "expires_at": t.expires_at,
        "is_active": t.is_active,
        "usage_count": t.usage_count
    } for t in tokens]

# DELETE /api/admin/accounts/{account_id}/tokens/{token_id}
async def revoke_token(account_id: UUID, token_id: UUID):
    token = await db.query(APIToken).filter_by(
        id=token_id,
        account_id=account_id
    ).first()
    
    if not token:
        raise HTTPException(404, "Token not found")
    
    token.is_active = False
    await db.commit()
    
    return {"message": "Token revoked"}
```

### 7. Migration

**Phase 1: Add Token Support**

1. Add `api_tokens` table
2. Implement `validate_api_token` dependency
3. Update endpoints to support optional token auth
4. Generate tokens for existing accounts
5. Monitor for unauthenticated requests

**Phase 2: Update Clients**

1. Create Astro `/api/chat` endpoint
2. Update widget, demo pages, footers
3. Test all clients

**Phase 3: Enforce Authentication**

1. Make token required
2. Return `401` for missing tokens
3. Deploy clients first, then enforce server-side
4. Monitor error rates

## Related Capabilities

### 1. Token Scopes

```
- chat:read     → Read chat history
- chat:write    → Send messages
- history:read  → Access conversation history
- admin:read    → View account metadata
- admin:write   → Modify account settings
```

### 2. Token Analytics

```sql
token_usage_analytics (
  id UUID PRIMARY KEY,
  token_id UUID REFERENCES api_tokens(id),
  date DATE,
  request_count INT,
  total_tokens_used INT,
  total_cost DECIMAL(10,4),
  unique_sessions INT,
  avg_response_time_ms INT
);
```

### 3. Webhook Notifications

```
- token.created
- token.used_first_time
- token.revoked
- token.approaching_limit
- token.high_cost_alert
- token.expired
```

### 4. Token Metadata

```sql
api_tokens (
  ...
  metadata JSONB
);
```

### 5. Public vs Private Tokens

**Public** (client-side):
- Scoped to `chat:write` only
- Rate limited aggressively
- Rotated frequently

**Private** (server-side):
- Full scopes
- Long-lived
- Stored in secure environment variables

```sql
api_tokens (
  ...
  token_type TEXT CHECK (token_type IN ('public', 'private'))
);
```

### 6. CORS Configuration

```sql
api_tokens (
  ...
  allowed_origins TEXT[]
);
```

```python
async def validate_api_token(...):
    if db_token.allowed_origins:
        origin = request.headers.get("Origin")
        if origin not in db_token.allowed_origins:
            raise HTTPException(403, "Token not allowed from this origin")
```

## Open Questions

### Q1: Token Visibility

Should we use Astro server endpoints (hybrid mode) or embed tokens in client JavaScript?

**Options**:
- **A**: Astro hybrid mode (secure)
- **B**: Fully static with client tokens
- **C**: Hybrid approach

### Q2: Token Expiration

**Options**:
- **A**: No expiration (rotate manually)
- **B**: Force rotation
- **C**: Long-lived with reminders

### Q3: Token Generation

Who generates tokens?

**Options**:
- **A**: Salient admin
- **B**: Customer self-service  
- **C**: Auto-generated during site setup

### Q4: Backward Compatibility

Support unauthenticated access for existing clients?

**Options**:
- **A**: Grace period with warnings
- **B**: Immediate enforcement
- **C**: Optional forever

### Q5: Rate Limiting

**Options**:
- **A**: Per-token
- **B**: Per-account  
- **C**: Both

## Security Considerations

### Token Storage

**Server-Side** (Astro Hybrid):
- Tokens in secure environment variables
- Never exposed to client JavaScript
- Encrypted at rest by hosting platform

**Client-Side** (Fully Static):
- Tokens visible in compiled JavaScript
- Users can extract tokens
- Mitigated by rate limiting and CORS

**Backend Services**:
- Tokens in secure environment variables
- Encrypted at rest (bcrypt hash)

### Token Compromise

If token is leaked:
1. User can make chat requests as that account
2. Rate limiting prevents large-scale abuse
3. Cost tracking alerts on unusual activity
4. Token can be revoked immediately

### CORS Protection

Tokens can include origin restrictions:
- Public widget token: Only works from `customersite.com`
- Can be bypassed with server-side requests

Enable CORS restrictions for high-value accounts.

## Summary

**Required Changes**:
1. Add `api_tokens` table and token generation service
2. Implement `validate_api_token` authentication dependency
3. Update all chat endpoints to require token
4. Create Astro server endpoint (`/api/chat`) as proxy
5. Update all web clients to use `/api/chat` endpoint
6. Add token management UI to admin CMS
7. Update static site build service to inject tokens
8. Configure Astro hybrid mode with appropriate adapter
9. Implement rate limiting per token
10. Add cost tracking per token
11. Add token usage analytics

**Capabilities**:
- Secure authentication for chat endpoints
- Per-account token management
- Token scoping
- Rate limiting and cost protection per token
- Token usage analytics
- Token rotation
- CORS restrictions per token
- Server-side token security

**Breaking Change**: Yes, clients must be updated to use `/api/chat` endpoint.
