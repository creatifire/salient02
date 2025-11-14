# Epic 0026 - Simple Admin Frontend for Chat Tracing

**Status**: In Progress (Phases 0-2 Complete)  
**Created**: 2025-11-12  
**Updated**: 2025-11-14  
**Priority**: Medium  
**Category**: Developer Tools / Debugging

---

## Implementation Status

### ✅ **Phase 0: Foundation Setup** (COMPLETE)
- ✅ Task 0026-000-001: Add meta JSONB column to llm_requests
- ✅ Task 0026-000-002: Create PromptBreakdownService
- ✅ Task 0026-000-003: Integrate into simple_chat.py (both streaming/non-streaming)
- ✅ Task 0026-000-004: Verify/implement tool call storage in message.meta
- ✅ Task 0026-000-005: Create AdminAuthMiddleware with HTTP Basic Auth

### ✅ **Phase 1: Backend API Endpoints** (COMPLETE)
- ✅ Feature 0026-001: GET /api/admin/sessions (list with filters)
- ✅ Feature 0026-002: GET /api/admin/sessions/{id}/messages
- ✅ Feature 0026-003: GET /api/admin/llm-requests/{id}

### ✅ **Phase 2: Frontend Pages** (COMPLETE)
- ✅ Feature 0026-004: Session list page (/admin/sessions) with SessionFilters component
- ✅ Feature 0026-005: Session detail page (/admin/sessions/[id]) with PromptInspector

### ✅ **Phase 3: Session-Based Authentication** (COMPLETE)
- ✅ Feature 0026-006: Replace HTTP Basic Auth with session-based login
  - ✅ Task 001: Create POST /api/admin/login and POST /api/admin/logout endpoints
  - ✅ Task 002: Update AdminAuthMiddleware to check session instead of Basic Auth
  - ✅ Task 003: Create /admin/login.astro page
  - ✅ Task 004: Create LoginForm.tsx component
  - ✅ Task 005: Update existing components with credentials: 'include' and 401 handling

### 📋 **Phase 4: UI Polish & Layout Improvements** (PLANNED)
- ⏳ Feature 0026-007: Transform to professional dashboard UI
  - Task 001: Create AdminLayout wrapper with sidebar
  - Task 002: Create reusable UI components (Card, Badge, Avatar)
  - Task 003: Update sessions list with stats cards
  - Task 004: Improve table styling with hover states
  - Task 005: Polish session detail page

**Commits**:
- `5cae767` - Phase 0-2 implementation (14 files changed)
- `304f32e` - Phase 3 documentation (session auth)
- `7835ae3` - Phase 4 documentation (UI polish)
- `[pending]` - Phase 3 implementation (session-based auth)

**Next Steps**:
1. Run database migration: `cd backend && alembic upgrade head`
2. Set environment variables in `.env`:
   ```bash
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-password
   ADMIN_SESSION_EXPIRY_MINUTES=120  # 2 hours default
   ```
3. Restart backend to load new auth middleware
4. Visit `http://localhost:4321/admin/login` to authenticate
5. Test session persistence (no repeated logins for 2 hours)
6. Implement Phase 4 (UI polish) for professional appearance

---

## Purpose

Debug LLM tool selection and prompt composition issues via simple admin UI.

**Core Features**:
- Browse sessions by account/agent
- View conversation history with LLM metadata
- Inspect prompt breakdown (critical rules, modules, directory docs)
- Trace tool calls (which tool, why, with what args)

**Primary Use Case**: Debug why LLM chooses wrong tools (e.g., `vector_search` instead of `search_directory` for phone queries)

---

## Technology Stack

- **Frontend**: Astro + Preact (already installed)
- **Backend**: FastAPI
- **Styling**: TailwindCSS (already installed)
- **Auth**: Session-based authentication (Phase 3) / HTTP Basic Auth (Phase 0-2)

---

## Routes

### `/admin/login` - Admin Login (Phase 3)
Simple login form for admin authentication. On success, stores session authentication.

**API**: `POST /api/admin/login` with `{username, password}`

### `/admin/sessions` - Session List
Table with filters (account, agent, date range) showing session metadata and message counts.

**API**: `GET /api/admin/sessions?account={slug}&agent={slug}&limit=50&offset=0`

### `/admin/sessions/{id}` - Session Detail
Conversation timeline with expandable LLM request details (model, tokens, cost, tool calls) and prompt inspector sidebar.

**APIs**: 
- `GET /api/admin/sessions/{id}/messages`
- `GET /api/admin/llm-requests/{request_id}`

### `/admin/llm-requests/{id}` - LLM Request Deep Dive (Optional)
Full prompt breakdown with accordion sections, tool call analysis, and raw JSON views.

---

## Implementation Plan

### Phase 0: Foundation Setup

#### Task 0026-000-001: Add meta Column
```sql
ALTER TABLE llm_requests ADD COLUMN meta JSONB;
```

#### Task 0026-000-002: Create PromptBreakdownService

**What it does**: Captures how the LLM prompt was assembled (what sections, in what order, how long each section is). This data gets stored in the database so the admin UI can show exactly what prompt the LLM saw when it made a bad decision.

**Why it matters**: When debugging "why did the LLM choose the wrong tool?", you need to see the exact prompt it received. This service tracks all the pieces (critical rules, base prompt, directory docs, modules) and their positions.

**File**: `backend/app/services/prompt_breakdown_service.py`

```python
from typing import Dict, Optional
import logfire

class PromptBreakdownService:
    @staticmethod
    def capture_breakdown(
        base_prompt: str,
        critical_rules: Optional[str] = None,
        directory_docs: Optional[str] = None,
        modules: Optional[Dict[str, str]] = None,
        account_slug: Optional[str] = None,
        agent_instance_slug: Optional[str] = None
    ) -> dict:
        breakdown = {"sections": []}
        position = 1
        total_chars = 0
        
        if critical_rules:
            breakdown["sections"].append({
                "name": "critical_rules",
                "position": position,
                "char_count": len(critical_rules),
                "source": "tool_selection_hints.md"
            })
            total_chars += len(critical_rules)
            position += 1
        
        breakdown["sections"].append({
            "name": "base_prompt",
            "position": position,
            "char_count": len(base_prompt),
            "source": "system_prompt.md"
        })
        total_chars += len(base_prompt)
        position += 1
        
        if directory_docs:
            breakdown["sections"].append({
                "name": "directory_docs",
                "position": position,
                "char_count": len(directory_docs),
                "source": "auto-generated"
            })
            total_chars += len(directory_docs)
            position += 1
        
        if modules:
            for module_name, content in modules.items():
                breakdown["sections"].append({
                    "name": module_name,
                    "position": position,
                    "char_count": len(content),
                    "source": f"{module_name}.md"
                })
                total_chars += len(content)
                position += 1
        
        breakdown["total_char_count"] = total_chars
        
        logfire.info(
            'service.prompt_breakdown.captured',
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug,
            total_chars=total_chars
        )
        
        return breakdown
```

**Storage**: Prompt breakdown gets stored in `llm_requests.meta["prompt_breakdown"]` (one per LLM request). This captures the INPUT to the LLM - what prompt structure it received.

#### Task 0026-000-003: Integrate into simple_chat.py
**Changes**: `simple_chat.py`, `cost_calculator.py`, `llm_request_tracker.py`

```python
# simple_chat.py - In create_simple_chat_agent()
from ..services.prompt_breakdown_service import PromptBreakdownService

breakdown = PromptBreakdownService.capture_breakdown(
    base_prompt=base_system_prompt,
    critical_rules=critical_rules if critical_rules else None,
    directory_docs=directory_docs if directory_config.get("enabled") else None,
    modules={name: load_prompt_module(name, account_slug) 
             for name in prompting_config.get('selected', [])} if prompting_config.get('enabled') else None,
    account_slug=account_slug,
    agent_instance_slug=instance_config.get('slug') if instance_config else None
)

# cost_calculator.py - Add prompt_breakdown parameter
async def track_chat_request(
    tracker: Any,
    # ... existing params ...
    prompt_breakdown: Optional[dict] = None  # NEW
) -> Optional[UUID]:
    llm_request_id = await tracker.track_llm_request(
        # ... existing params ...
        meta={"prompt_breakdown": prompt_breakdown} if prompt_breakdown else None
    )

# llm_request_tracker.py - Add meta parameter
async def track_llm_request(
    self,
    # ... existing params ...
    meta: Optional[Dict[str, Any]] = None  # NEW
) -> UUID:
    llm_request = LLMRequest(
        # ... existing fields ...
        meta=meta
    )
```

#### Task 0026-000-004: Verify Tool Call Storage

**Storage**: Tool calls get stored in `messages.meta["tool_calls"]` (one per assistant message). This captures the OUTPUT from the LLM - which tools it decided to call and with what arguments.

**Why separate from prompt breakdown**: This lets you compare INPUT (prompt structure) vs OUTPUT (tool choices) to debug wrong tool selection.


Check if `message.meta["tool_calls"]` is populated. If missing:

```python
# In simple_chat() after agent.run()
tool_calls_meta = []
if result.all_messages():
    for msg in result.all_messages():
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    tool_calls_meta.append({
                        "tool_name": part.tool_name,
                        "args": part.args
                    })

await message_service.save_message(
    # ...
    meta={"tool_calls": tool_calls_meta} if tool_calls_meta else None
)
```

#### Task 0026-000-005: Admin Auth Middleware
**File**: `backend/app/middleware/admin_auth_middleware.py`

```python
import os
import secrets
import base64
from typing import Callable
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import logfire

class AdminAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        if self.admin_password == "changeme":
            logfire.warn('security.admin_auth.default_password',
                        message="Change ADMIN_PASSWORD env var")
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not request.url.path.startswith("/api/admin/"):
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return self._unauthorized()
        
        try:
            credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = credentials.split(":", 1)
            
            if not (secrets.compare_digest(username, self.admin_username) and 
                    secrets.compare_digest(password, self.admin_password)):
                logfire.warn('security.admin_auth.failed', username=username)
                return self._unauthorized()
            
            logfire.info('security.admin_auth.success', username=username,
                        ip=request.client.host if request.client else None)
        except Exception as e:
            logfire.error('security.admin_auth.error', error=str(e))
            return self._unauthorized()
        
        return await call_next(request)
    
    def _unauthorized(self):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Admin authentication required"},
            headers={"WWW-Authenticate": "Basic realm=\"Admin Area\""}
        )
```

**Register in `main.py`**:
```python
from .middleware.admin_auth_middleware import AdminAuthMiddleware
app.add_middleware(AdminAuthMiddleware)
```

**`.env`**:
```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here
```

---

### Phase 1: Backend API Endpoints

**Note**: All admin APIs use GET requests (read-only). No POST/PUT/DELETE - admin UI is for debugging/inspection only, no data modification.

#### Feature 0026-001: Sessions List API
**File**: `backend/app/api/admin.py`

```python
from fastapi import APIRouter, Query
from sqlalchemy import select, func
from ..models import Session, Message

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/sessions")
async def list_sessions(
    account: str = Query(None),
    agent: str = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    # Query sessions with filters
    # Join with messages for count
    # Return paginated results
    pass
```

#### Feature 0026-002: Session Messages API
```python
@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    # Query messages for session
    # Join with llm_requests for metadata
    # Return chronological list
    pass
```

#### Feature 0026-003: LLM Request Detail API
```python
@router.get("/llm-requests/{request_id}")
async def get_llm_request(request_id: str):
    # Query llm_requests table
    # Return prompt_breakdown from meta field
    # Include tool calls and response
    pass
```

---

### Phase 2: Frontend Pages

#### Feature 0026-004: Session List Page
**File**: `web/src/pages/admin/sessions.astro`
- Server-side fetch sessions on load
- Embed `<SessionFilters client:load />` Preact component for interactivity
- TailwindCSS table styling

**Component**: `web/src/components/admin/SessionFilters.tsx`
```tsx
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';

export function SessionFilters() {
  const [account, setAccount] = useState('');
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchSessions = async () => {
      setLoading(true);
      const params = new URLSearchParams();
      if (account) params.append('account', account);
      const response = await fetch(`/api/admin/sessions?${params}`);
      const data = await response.json();
      setSessions(data.sessions || []);
      setLoading(false);
    };
    fetchSessions();
  }, [account]);

  return (
    <div class="p-4">
      <select value={account} onChange={(e) => setAccount(e.currentTarget.value)}
              class="border rounded p-2">
        <option value="">All Accounts</option>
        <option value="wyckoff">Wyckoff</option>
      </select>
      
      {loading ? <div>Loading...</div> : (
        <table class="w-full mt-4">
          {/* Render sessions */}
        </table>
      )}
    </div>
  );
}
```

#### Feature 0026-005: Session Detail Page
**File**: `web/src/pages/admin/sessions/[id].astro`
- Dynamic route with session ID
- Server-side fetch messages
- Conversation timeline with Preact components

**Component**: `web/src/components/admin/PromptInspector.tsx`
```tsx
import { h } from 'preact';
import { useState } from 'preact/hooks';

export function PromptInspector({ requestId }: { requestId: string }) {
  const [breakdown, setBreakdown] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const loadBreakdown = async () => {
    const response = await fetch(`/api/admin/llm-requests/${requestId}`);
    const data = await response.json();
    setBreakdown(data.prompt_breakdown);
  };

  return (
    <aside class="border-l p-4">
      <h3 class="font-bold mb-4">Prompt Inspector</h3>
      {breakdown && breakdown.sections.map((section) => (
        <div key={section.name} class="mb-2">
          <button 
            onClick={() => setExpanded(expanded === section.name ? null : section.name)}
            class="w-full text-left p-2 bg-gray-100 hover:bg-gray-200 rounded">
            {section.name} ({section.char_count} chars)
          </button>
          {expanded === section.name && (
            <pre class="p-2 bg-gray-50 text-sm overflow-auto">
              <code>{section.content}</code>
            </pre>
          )}
        </div>
      ))}
    </aside>
  );
}
```

---

### Phase 3: Session-Based Authentication

**Goal**: Replace HTTP Basic Auth with session-based login to eliminate repeated credential prompts

**Problem**: Current HTTP Basic Auth prompts for username/password on every request (field change, page refresh). Poor UX for admin debugging.

**Solution**: Piggyback on existing `SimpleSessionMiddleware` infrastructure with session-stored authentication flag.

#### Feature 0026-006: Session-Based Admin Login

##### Task 0026-006-001: Create Admin Login Endpoint
**File**: `backend/app/api/admin.py`

```python
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, Depends
from pydantic import BaseModel

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def admin_login(credentials: AdminLoginRequest, request: Request):
    """
    Validate admin credentials and set session authentication.
    
    On success, sets session["admin_authenticated"] with expiry timestamp.
    Returns success message and expiry time.
    """
    # Load credentials from env
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
    
    # Validate credentials (timing-safe comparison)
    if not (secrets.compare_digest(credentials.username, admin_username) and 
            secrets.compare_digest(credentials.password, admin_password)):
        logfire.warn('api.admin.login.failed', username=credentials.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Set session authentication with expiry (default: 2 hours)
    expiry_minutes = int(os.getenv("ADMIN_SESSION_EXPIRY_MINUTES", "120"))
    expiry = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    
    request.session["admin_authenticated"] = True
    request.session["admin_expiry"] = expiry.isoformat()
    
    logfire.info(
        'api.admin.login.success',
        username=credentials.username,
        expiry_minutes=expiry_minutes
    )
    
    return {
        "success": True,
        "expires_in_minutes": expiry_minutes,
        "expires_at": expiry.isoformat()
    }

@router.post("/logout")
async def admin_logout(request: Request):
    """Clear admin session authentication."""
    if "admin_authenticated" in request.session:
        del request.session["admin_authenticated"]
    if "admin_expiry" in request.session:
        del request.session["admin_expiry"]
    
    return {"success": True, "message": "Logged out"}
```

##### Task 0026-006-002: Update AdminAuthMiddleware
**File**: `backend/app/middleware/admin_auth_middleware.py`

Replace HTTP Basic Auth logic with session check:

```python
async def dispatch(self, request: Request, call_next: Callable):
    """Check session authentication for /api/admin/* requests."""
    
    # Skip auth check for login endpoint itself
    if request.url.path == "/api/admin/login":
        return await call_next(request)
    
    # Only apply auth to other admin endpoints
    if not request.url.path.startswith("/api/admin/"):
        return await call_next(request)
    
    # Check session authentication
    if not request.session.get("admin_authenticated"):
        return self._unauthorized("Not authenticated")
    
    # Check session expiry
    expiry_str = request.session.get("admin_expiry")
    if expiry_str:
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.now(timezone.utc) > expiry:
            # Session expired, clear it
            del request.session["admin_authenticated"]
            del request.session["admin_expiry"]
            return self._unauthorized("Session expired")
    
    # Authentication valid
    return await call_next(request)

def _unauthorized(self, message: str = "Admin authentication required"):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": message, "login_required": True}
    )
```

##### Task 0026-006-003: Create Admin Login Page
**File**: `web/src/pages/admin/login.astro`

Simple login form that posts to `/api/admin/login`:

```astro
---
// Server-side: redirect if already authenticated
---

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Login</title>
</head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center">
    <div class="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 class="text-2xl font-bold mb-6">Admin Login</h1>
        <div id="login-form"></div>
    </div>

    <script>
        import { h, render } from 'preact';
        import { LoginForm } from '../components/admin/LoginForm';
        
        const container = document.getElementById('login-form');
        if (container) {
            render(h(LoginForm, { apiUrl: import.meta.env.PUBLIC_API_URL || 'http://localhost:8000' }), container);
        }
    </script>
</body>
</html>
```

##### Task 0026-006-004: Create LoginForm Component
**File**: `web/src/components/admin/LoginForm.tsx`

```tsx
import { h } from 'preact';
import { useState } from 'preact/hooks';

export function LoginForm({ apiUrl }: { apiUrl: string }) {
    const [username, setUsername] = useState('admin');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: Event) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${apiUrl}/api/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include', // Important: send cookies
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Login failed');
            }

            // Redirect to sessions page
            window.location.href = '/admin/sessions';
        } catch (err: any) {
            setError(err.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} class="space-y-4">
            {error && (
                <div class="bg-red-50 border border-red-200 text-red-800 rounded p-3 text-sm">
                    {error}
                </div>
            )}
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Username
                </label>
                <input
                    type="text"
                    value={username}
                    onInput={(e) => setUsername((e.target as HTMLInputElement).value)}
                    class="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                />
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Password
                </label>
                <input
                    type="password"
                    value={password}
                    onInput={(e) => setPassword((e.target as HTMLInputElement).value)}
                    class="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                />
            </div>

            <button
                type="submit"
                disabled={loading}
                class="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
                {loading ? 'Logging in...' : 'Login'}
            </button>
        </form>
    );
}
```

##### Task 0026-006-005: Update Existing Components
Remove HTTP Basic Auth prompts from:
- `SessionFilters.tsx` - use fetch with `credentials: 'include'`
- `SessionDetail.tsx` - use fetch with `credentials: 'include'`
- `PromptInspector.tsx` - use fetch with `credentials: 'include'`

Handle 401 responses by redirecting to `/admin/login`.

**Environment Variables**:
```bash
# .env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
ADMIN_SESSION_EXPIRY_MINUTES=120  # 2 hours default
```

**Benefits**:
- No repeated credential prompts
- Session persists across tabs
- Configurable expiry time
- Reuses existing session infrastructure
- Logout functionality
- Better UX for debugging

---

### Bug 0026-0001: Admin Pages Not Checking Authentication on Initial Load

**Problem**: Visiting `/admin` or `/admin/sessions` loads the page without checking authentication. User sees the UI briefly before client-side code detects 401 and redirects to login.

**Expected Behavior**: Unauthenticated users should be redirected to `/admin/login` BEFORE the page loads.

**Root Cause**: Astro pages don't perform server-side authentication checks. Only client-side Preact components check auth (after page load).

#### Desired Authentication Flow

**Step 1: User visits `/admin` or `/admin/sessions`**
- Astro SSR receives request
- Astro has access to request cookies (via `Astro.cookies`)
- **Cookie name**: `salient_session` (from `SimpleSessionMiddleware`)
- **Cookie contains**: Session key (e.g., `"xva_WipVFTED2LZ0j-hV5_KwgV3yTdzX"`)

**Step 2: Astro checks session cookie**
```astro
---
const sessionCookie = Astro.cookies.get('salient_session');
if (!sessionCookie) {
    // No session cookie = not logged in
    return Astro.redirect('/admin/login');
}
---
```

**Step 3A: If cookie exists, verify authentication with backend - DEPRECATED** 
- **Option A (Simple)**: Make server-side fetch to `/api/admin/sessions?limit=1`
  - If 200: User is authenticated → render page
  - If 401: Session exists but not authenticated → redirect to login
  
- **Option B (Direct DB Check)**: Query `sessions` table directly in Astro
  - Look up session by `session_key` from cookie
  - Check if `session.meta["admin_authenticated"]` is `true`
  - Check if `session.meta["admin_expiry"]` is not expired
  - If valid: render page
  - If invalid: redirect to login

**Step 4a: User IS authenticated**
- Astro renders page HTML
- Client-side Preact components mount
- Components fetch data with `credentials: 'include'`
- Session cookie automatically sent with API requests
- Backend validates session and returns data

**Step 4b: User is NOT authenticated**
- Astro redirects to `/admin/login` (HTTP 302)
- User never sees admin page
- Login page loads
- User enters credentials
- `POST /api/admin/login` validates and sets `session["admin_authenticated"] = true`
- Login redirects to `/admin/sessions`
- Now authenticated, flow goes to Step 4a

#### What the Cookie Contains
- **Cookie name**: `salient_session` (configurable via `session_config.cookie_name`)
- **Cookie value**: Session key string (e.g., `"xva_WipVFTED2LZ0j-hV5_KwgV3yTdzX"`)
- **Cookie attributes**:
  - `HttpOnly=true` (JavaScript can't access it)
  - `SameSite=None` or `null` (for cross-origin in dev)
  - `Secure=false` (in dev), `Secure=true` (in production)
  - `Max-Age=604800` (7 days default)

#### What the Backend Looks For
1. **SimpleSessionMiddleware** (runs first):
   - Extracts `salient_session` cookie from request
   - Queries `sessions` table: `WHERE session_key = <cookie_value>`
   - Loads `session.meta` JSONB column
   - Sets `request.scope["session"] = session.meta` (makes it available as dict)
   
2. **AdminAuthMiddleware** (runs second):
   - Checks `request.session.get("admin_authenticated")`
   - If `True`: checks `request.session.get("admin_expiry")`
   - If expiry not passed: allows request through
   - If `False` or expired: returns 401 Unauthorized

#### Session Data Structure
```python
# sessions table row
{
  "id": "019a8045-623b-7670-a452-908588ff4143",
  "session_key": "xva_WipVFTED2LZ0j-hV5_KwgV3yTdzX",
  "meta": {
    "admin_authenticated": true,           # ← Set by POST /api/admin/login
    "admin_expiry": "2025-11-14T04:55:54Z" # ← Set by POST /api/admin/login
  },
  "created_at": "2025-11-14T02:50:22Z",
  "is_anonymous": true
}
```

#### Current vs Desired Flow

**Current (Broken)**:
1. User visits `/admin/sessions`
2. Astro renders page (no auth check)
3. Browser loads page, mounts Preact components
4. SessionFilters fetches `/api/admin/sessions`
5. Backend returns 401 Unauthorized
6. Component redirects to `/admin/login`
7. **Problem**: User sees flash of admin page before redirect

**Desired (Fixed)**:
1. User visits `/admin/sessions`
2. Astro checks session cookie server-side
3. Astro validates authentication (API call or DB query)
4. If not authenticated: Astro returns 302 redirect to `/admin/login`
5. If authenticated: Astro renders page
6. **Result**: No flash, seamless experience

#### Implementation Options

**Option 1: Server-Side API Call (Recommended)**
```astro
---
// web/src/pages/admin/sessions.astro
const apiUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';
const sessionCookie = Astro.cookies.get('salient_session');

if (!sessionCookie) {
    return Astro.redirect('/admin/login');
}

// Verify authentication with backend
try {
    const response = await fetch(`${apiUrl}/api/admin/sessions?limit=1`, {
        headers: {
            'Cookie': `salient_session=${sessionCookie.value}`
        }
    });
    
    if (response.status === 401) {
        return Astro.redirect('/admin/login');
    }
} catch (error) {
    console.error('Auth check failed:', error);
    return Astro.redirect('/admin/login');
}
---
```

**Option 2: Direct Database Query**
```astro
---
import { getSessionByKey, isAdminAuthenticated } from '../../lib/auth';

const sessionCookie = Astro.cookies.get('salient_session');

if (!sessionCookie) {
    return Astro.redirect('/admin/login');
}

const session = await getSessionByKey(sessionCookie.value);
if (!session || !isAdminAuthenticated(session)) {
    return Astro.redirect('/admin/login');
}
---
```

**Recommendation**: Use Option 1 (server-side API call) because:
- Reuses existing authentication logic in `AdminAuthMiddleware`
- No need to duplicate auth logic in Astro
- Centralized auth validation in one place
- Easier to maintain and test

#### Implementation Status: COMPLETE ✅

**Files Modified**:
1. `/web/src/pages/admin/sessions.astro` - Added server-side auth check
2. `/web/src/pages/admin/sessions/[id].astro` - Added server-side auth check
3. `/backend/app/api/admin.py` - Enhanced logging for login process
4. `/backend/app/middleware/admin_auth_middleware.py` - Added detailed session checking logs
5. `/backend/app/middleware/simple_session_middleware.py` - Enhanced session persistence logging

**Logging Added**:

1. **Login Process** (`api.admin.login.setting_flags`, `api.admin.login.success`):
   - Session ID
   - Session meta before/after setting flags
   - Username and expiry minutes

2. **Session Loading** (`middleware.session.resumed`):
   - Session ID
   - Session meta loaded from database
   - Confirms what authentication flags are present

3. **Session Persistence** (`middleware.session.saving`, `middleware.session.committing`, `middleware.session.saved`):
   - Session ID
   - Meta data before save
   - Meta data being committed
   - Meta data after commit
   - Verifies `flag_modified()` + `merge()` is working

4. **Auth Checking** (`security.admin_auth.checking`, `security.admin_auth.not_authenticated`):
   - Path being checked
   - Session ID
   - Session meta contents
   - Whether admin_authenticated flag is present

5. **Astro Server-Side** (console logs):
   - Cookie presence check
   - Backend auth verification response
   - Redirect decisions

#### Verification Checklist

**Test 1: Unauthenticated User**
1. Clear browser cookies
2. Visit `http://localhost:4321/admin/sessions`
3. **Expected**: Immediate redirect to `/admin/login` (NO page flash)
4. **Logfire**: Should see `[Admin Auth] No session cookie found`

**Test 2: Login Flow**
1. On login page, enter credentials
2. Submit login form
3. **Expected**: Redirect to `/admin/sessions` with page visible
4. **Logfire Sequence**:
   ```
   api.admin.login.setting_flags (session_meta_before: {})
   api.admin.login.success (session_meta_after: {admin_authenticated: true, admin_expiry: "..."})
   middleware.session.saving (meta_before_save: {admin_authenticated: true, ...})
   middleware.session.committing (meta_to_commit: {admin_authenticated: true, ...})
   middleware.session.saved (meta_saved: {admin_authenticated: true, ...})
   ```

**Test 3: Authenticated Session Persistence**
1. After successful login, refresh page
2. **Expected**: Page loads immediately (no redirect)
3. **Logfire Sequence**:
   ```
   middleware.session.resumed (meta_loaded: {admin_authenticated: true, admin_expiry: "..."})
   security.admin_auth.checking (has_admin_flag: true)
   security.admin_auth.session_valid
   ```

**Test 4: Database Verification**
1. After login, query database:
   ```sql
   SELECT id, session_key, meta FROM sessions 
   ORDER BY updated_at DESC LIMIT 1;
   ```
2. **Expected**: `meta` column contains:
   ```json
   {
     "admin_authenticated": true,
     "admin_expiry": "2025-11-14T06:55:54Z"
   }
   ```

**Test 5: Session Expiry**
1. Log in successfully
2. Manually set `ADMIN_SESSION_EXPIRY_MINUTES=1` in `.env`
3. Wait 2 minutes
4. Try to access `/admin/sessions`
5. **Expected**: Redirect to `/admin/login`
6. **Logfire**: Should see `security.admin_auth.session_expired`

**Test 6: Cross-Tab Persistence**
1. Log in on Tab 1
2. Open Tab 2, visit `/admin/sessions`
3. **Expected**: Immediate access (no login prompt)
4. **Reason**: Session cookie shared across tabs

#### Known Issues

**Issue**: Console logs in Astro SSR don't appear in browser console
**Solution**: Check server-side logs (terminal running `npm run dev`)

**Issue**: Session cookie not forwarding in Astro SSR fetch
**Status**: FIXED - Now forwarding `Cookie` header manually in server-side fetch

---

## BUG-0026-0002: Remove Login Functionality for Admin screen

**Problem**: We're building a simple internal debugging tool (view sessions, inspect prompts, trace tool calls) but we've added login/session complexity that's blocking progress. Authentication is unnecessary for a localhost debugging tool.

**Goal**: Strip out ALL authentication, keep the core value proposition:
1. Browse chat sessions
2. View conversation history
3. Inspect prompt breakdowns
4. Trace tool calls

**Decision**: No login, no auth checks, no session management. Just simple read-only data endpoints accessible on localhost during development.

### Files to DELETE

1. **`web/src/pages/admin/login.astro`** - Login page (not needed)
2. **`web/src/pages/admin/login-htmx.astro`** - HTMX login experiment (not needed)
3. **`web/src/components/admin/LoginForm.tsx`** - Login form component (not needed)
4. **`backend/app/middleware/admin_auth_middleware.py`** - Auth middleware (blocking requests)

**Total**: 4 files deleted

### Files to MODIFY (Remove Auth Logic)

#### Backend Changes

1. **`backend/app/main.py`**
   - **Remove**: `from .middleware.admin_auth_middleware import AdminAuthMiddleware`
   - **Remove**: `app.add_middleware(AdminAuthMiddleware)`
   - **Keep**: Everything else (CORS, session middleware for chat)

2. **`backend/app/api/admin.py`**
   - **Remove**: `POST /api/admin/login` endpoint
   - **Remove**: `POST /api/admin/logout` endpoint
   - **Remove**: All imports related to auth (secrets, datetime for expiry)
   - **Keep**: All GET endpoints (sessions, messages, llm-requests)

#### Frontend Changes

3. **`web/src/pages/admin/sessions.astro`**
   - **Remove**: Entire server-side auth check block (lines checking cookie, calling backend)
   - **Remove**: Auth-related imports
   - **Simplify**: Just render page directly, no redirects

4. **`web/src/pages/admin/sessions/[id].astro`**
   - **Remove**: Entire server-side auth check block
   - **Simplify**: Just fetch and render session data

5. **`web/src/components/admin/SessionFilters.tsx`**
   - **Remove**: `credentials: 'include'` from fetch calls (not needed)
   - **Remove**: 401 handling and redirect logic
   - **Simplify**: Just fetch data, show errors if fetch fails

6. **`web/src/components/admin/SessionDetail.tsx`**
   - **Remove**: `credentials: 'include'` from fetch calls
   - **Remove**: 401 handling and redirect logic
   - **Simplify**: Just fetch and display messages

7. **`web/src/components/admin/PromptInspector.tsx`**
   - **Remove**: `credentials: 'include'` from fetch calls
   - **Remove**: 401 handling and redirect logic
   - **Simplify**: Just fetch and display prompt breakdown

**Total**: 7 files modified

### What We're KEEPING (The Core Value)

✅ **Database Layer**:
- `llm_requests.meta` JSONB column for prompt breakdowns
- `messages.meta` for tool calls
- All existing tables and relationships

✅ **Backend Services**:
- `PromptBreakdownService` - captures prompt composition
- Integration in `simple_chat.py` - tracks how prompts are assembled

✅ **Backend APIs** (read-only):
- `GET /api/admin/sessions` - list sessions with filters
- `GET /api/admin/sessions/{id}/messages` - conversation history
- `GET /api/admin/llm-requests/{id}` - detailed prompt breakdown

✅ **Frontend Pages**:
- `/admin/sessions` - browse all sessions
- `/admin/sessions/{id}` - view conversation + prompt inspector
- `/admin` - redirect to sessions

✅ **Frontend Components**:
- `SessionFilters.tsx` - interactive table with filtering
- `SessionDetail.tsx` - conversation timeline
- `PromptInspector.tsx` - expandable prompt sections

### Architecture After Cleanup

```
┌─────────────────────────────────────────────┐
│  Browser: localhost:4321/admin/sessions    │
└────────────────┬────────────────────────────┘
                 │
                 │ Simple fetch (no auth)
                 │
┌────────────────▼────────────────────────────┐
│  Backend: localhost:8000/api/admin/*        │
│  - GET /sessions                            │
│  - GET /sessions/{id}/messages              │
│  - GET /llm-requests/{id}                   │
│                                             │
│  NO MIDDLEWARE (except CORS)                │
└────────────────┬────────────────────────────┘
                 │
                 │ SQLAlchemy queries
                 │
┌────────────────▼────────────────────────────┐
│  PostgreSQL Database                        │
│  - sessions table                           │
│  - messages table (meta["tool_calls"])      │
│  - llm_requests table (meta["breakdown"])   │
└─────────────────────────────────────────────┘
```

### Complexity Removed

**Before**: 
- Login page + form component
- Session-based auth middleware
- Cookie management across origins
- Server-side auth checks in Astro
- Client-side 401 handling and redirects
- Login/logout endpoints
- Password management
- Session expiry logic

**After**:
- Direct page access
- Simple fetch calls
- No redirects
- No authentication flow
- **Result**: ~500 lines of code removed, zero auth debugging

### Security Note

This is appropriate because:
1. **Development tool** - runs on localhost only
2. **Read-only** - no data modification endpoints
3. **Internal use** - not exposed to public internet
4. **Temporary** - if we deploy to production later, we can add proper auth then

For production deployment (if ever needed), we'd add:
- Reverse proxy auth (nginx basic auth)
- VPN requirement
- OAuth/SSO integration
- Or keep it localhost-only (SSH tunnel for remote access)

### Implementation Order

1. **Delete 4 files** (login pages, LoginForm, AdminAuthMiddleware)
2. **Clean backend**: Remove login endpoints, remove middleware registration
3. **Clean frontend**: Remove auth checks from Astro pages
4. **Simplify components**: Remove credentials/401 handling from Preact components
5. **Test**: Visit localhost:4321/admin/sessions → should load instantly, no redirects
6. **Commit**: "refactor: remove authentication complexity from admin UI"

### Expected Outcome

- Visit `localhost:4321/admin/sessions` → page loads immediately
- Click session → see conversation history
- Click "View Prompt" → see breakdown
- **Zero friction, zero auth errors, just data**

---

## Phase 3B: Session Browser in HTMX

**Goal**: Replace Astro + Preact complexity with simple HTMX + vanilla HTML/JS in `web/public/admin/`

**Current Problem**: 
- Astro SSR configuration causing routing issues (`GetStaticPathsRequired` errors)
- Preact hydration not working reliably
- Build complexity and framework overhead for a simple debugging tool
- ~15 files, multiple layers (Astro pages → Preact components → API calls)

**Solution**: 
- **3 static HTML files** in `web/public/admin/` (no build, no SSR, no hydration)
- **HTMX v2.0.7** for declarative data fetching
- **Vanilla JavaScript** for JSON → HTML rendering
- **TailwindCSS CDN** for styling (no build step)

**Architecture**:
```
web/public/admin/
├── sessions.html          # List all sessions (filters, table)
├── session.html           # View single session (messages + prompt inspector)
└── styles.css             # Shared styles (optional)

Backend APIs (already exist, no changes):
- GET /api/admin/sessions
- GET /api/admin/sessions/{id}/messages
- GET /api/admin/llm-requests/{id}
```

---

### Feature 0026-008: HTMX Session Browser

#### Task 0026-008-001: Create Sessions List Page

**File**: `web/public/admin/sessions.html`

**Requirements**:
- Load on page load (HTMX `hx-trigger="load"`)
- Fetch `/api/admin/sessions?limit=50`
- Render JSON as HTML table using vanilla JS
- Account/Agent filter dropdowns (trigger new fetch)
- Refresh button
- Link to session detail page

**Implementation**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Sessions | OpenThought</title>
    
    <!-- HTMX v2.0.7 (latest) -->
    <script src="https://unpkg.com/htmx.org@2.0.7"></script>
    
    <!-- TailwindCSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-6">
        <!-- Header -->
        <header class="bg-white shadow-sm rounded-lg mb-6 p-6">
            <h1 class="text-2xl font-bold text-gray-900">Chat Sessions</h1>
            <p class="text-sm text-gray-500 mt-1">Debug LLM tool selection and prompt composition</p>
        </header>

        <!-- Filters -->
        <div class="bg-white shadow-sm rounded-lg mb-6 p-6">
            <div class="flex gap-4 items-end">
                <div class="flex-1">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Account</label>
                    <select id="account-filter" 
                            class="w-full border border-gray-300 rounded-md px-3 py-2"
                            onchange="fetchSessions()">
                        <option value="">All Accounts</option>
                        <option value="wyckoff">Wyckoff</option>
                    </select>
                </div>
                <div class="flex-1">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Agent</label>
                    <select id="agent-filter" 
                            class="w-full border border-gray-300 rounded-md px-3 py-2"
                            onchange="fetchSessions()">
                        <option value="">All Agents</option>
                        <option value="wyckoff_info_chat1">wyckoff_info_chat1</option>
                    </select>
                </div>
                <div>
                    <button onclick="fetchSessions()" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                        Refresh
                    </button>
                </div>
            </div>
        </div>

        <!-- Sessions Table -->
        <div class="bg-white shadow-sm rounded-lg overflow-hidden">
            <div id="sessions-container" 
                 hx-get="/api/admin/sessions?limit=50" 
                 hx-trigger="load"
                 hx-on::after-request="renderSessions(event)">
                <div class="p-6 text-center text-gray-500">
                    <svg class="animate-spin h-8 w-8 mx-auto mb-2 text-blue-600" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading sessions...
                </div>
            </div>
        </div>
    </div>

    <script>
        // Render sessions table from JSON response
        function renderSessions(event) {
            const data = JSON.parse(event.detail.xhr.response);
            const container = document.getElementById('sessions-container');
            
            if (!data.sessions || data.sessions.length === 0) {
                container.innerHTML = `
                    <div class="p-6 text-center text-gray-500">
                        No sessions found
                    </div>
                `;
                return;
            }
            
            const html = `
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Session ID</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Messages</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${data.sessions.map(session => `
                            <tr class="hover:bg-gray-50">
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                                    ${session.id.substring(0, 13)}...
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${session.account_slug || '-'}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${session.agent_instance_slug || '-'}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${session.message_count || 0}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    ${new Date(session.created_at).toLocaleString()}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
                                    <a href="/admin/session.html?id=${session.id}" 
                                       class="text-blue-600 hover:text-blue-800 font-medium">
                                        View Detail →
                                    </a>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 text-sm text-gray-500">
                    Showing ${data.sessions.length} of ${data.total || data.sessions.length} sessions
                </div>
            `;
            
            container.innerHTML = html;
        }
        
        // Fetch sessions with filters
        function fetchSessions() {
            const account = document.getElementById('account-filter').value;
            const agent = document.getElementById('agent-filter').value;
            
            const params = new URLSearchParams();
            if (account) params.append('account', account);
            if (agent) params.append('agent', agent);
            params.append('limit', '50');
            
            // Manually trigger HTMX request with new URL
            const container = document.getElementById('sessions-container');
            htmx.ajax('GET', `/api/admin/sessions?${params}`, {
                target: '#sessions-container',
                swap: 'none' // We handle rendering in renderSessions()
            });
        }
    </script>
</body>
</html>
```

**Benefits**:
- No build step, edit and refresh
- HTMX handles loading state automatically
- Vanilla JS for full control over rendering
- TailwindCSS CDN for instant styling
- Works immediately in any browser

---

#### Task 0026-008-002: Create Session Detail Page

**File**: `web/public/admin/session.html`

**Requirements**:
- Read session ID from URL query param (`?id=xxx`)
- Fetch `/api/admin/sessions/{id}/messages` on load
- Display conversation timeline (user/assistant messages)
- Show LLM metadata (model, tokens, cost)
- Expandable prompt inspector (fetch `/api/admin/llm-requests/{id}` on click)
- Back to sessions link

**Implementation Sketch**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Session Detail | Admin</title>
    <script src="https://unpkg.com/htmx.org@2.0.7"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 py-6">
        <!-- Header with back link -->
        <header class="mb-6">
            <a href="/admin/sessions.html" class="text-blue-600 hover:text-blue-800 text-sm">
                ← Back to Sessions
            </a>
            <h1 class="text-2xl font-bold text-gray-900 mt-2">Session Detail</h1>
            <p id="session-id" class="text-sm text-gray-500 font-mono mt-1"></p>
        </header>

        <!-- Messages Timeline -->
        <div id="messages-container"
             hx-trigger="load"
             hx-on::after-request="renderMessages(event)">
            <div class="text-center text-gray-500">Loading messages...</div>
        </div>
    </div>

    <script>
        // Get session ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('id');
        
        if (!sessionId) {
            document.body.innerHTML = '<p class="text-red-600 p-6">No session ID provided</p>';
        } else {
            document.getElementById('session-id').textContent = sessionId;
            
            // Fetch messages on load
            htmx.ajax('GET', `/api/admin/sessions/${sessionId}/messages`, {
                target: '#messages-container',
                swap: 'none'
            });
        }
        
        function renderMessages(event) {
            const data = JSON.parse(event.detail.xhr.response);
            const container = document.getElementById('messages-container');
            
            if (!data.messages || data.messages.length === 0) {
                container.innerHTML = '<p class="text-gray-500 p-6">No messages in this session</p>';
                return;
            }
            
            const html = data.messages.map(msg => {
                const isUser = msg.role === 'user';
                const bgColor = isUser ? 'bg-blue-50' : 'bg-white';
                const borderColor = isUser ? 'border-blue-200' : 'border-gray-200';
                
                return `
                    <div class="mb-4 p-4 rounded-lg border ${borderColor} ${bgColor}">
                        <div class="flex items-center justify-between mb-2">
                            <span class="font-semibold text-sm ${isUser ? 'text-blue-700' : 'text-gray-700'}">
                                ${isUser ? '👤 User' : '🤖 Assistant'}
                            </span>
                            <span class="text-xs text-gray-500">
                                ${new Date(msg.created_at).toLocaleString()}
                            </span>
                        </div>
                        <p class="text-gray-900 whitespace-pre-wrap">${msg.content}</p>
                        
                        ${msg.llm_request_id ? `
                            <button onclick="loadPromptBreakdown('${msg.llm_request_id}')" 
                                    class="mt-3 text-sm text-blue-600 hover:text-blue-800">
                                🔍 View Prompt Breakdown
                            </button>
                            <div id="breakdown-${msg.llm_request_id}" class="hidden mt-3 p-3 bg-gray-50 rounded text-sm">
                                Loading...
                            </div>
                        ` : ''}
                        
                        ${msg.meta?.tool_calls ? `
                            <div class="mt-3 p-3 bg-yellow-50 rounded border border-yellow-200">
                                <p class="text-xs font-semibold text-yellow-800 mb-2">Tool Calls:</p>
                                <pre class="text-xs text-gray-700">${JSON.stringify(msg.meta.tool_calls, null, 2)}</pre>
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
            
            container.innerHTML = html;
        }
        
        function loadPromptBreakdown(requestId) {
            const breakdownDiv = document.getElementById(`breakdown-${requestId}`);
            
            if (!breakdownDiv.classList.contains('hidden')) {
                breakdownDiv.classList.add('hidden');
                return;
            }
            
            fetch(`/api/admin/llm-requests/${requestId}`)
                .then(r => r.json())
                .then(data => {
                    const breakdown = data.prompt_breakdown;
                    if (!breakdown) {
                        breakdownDiv.innerHTML = '<p class="text-gray-500">No breakdown available</p>';
                        breakdownDiv.classList.remove('hidden');
                        return;
                    }
                    
                    const html = `
                        <p class="font-semibold mb-2">Prompt Sections (${breakdown.total_char_count.toLocaleString()} chars):</p>
                        <ul class="space-y-2">
                            ${breakdown.sections.map(section => `
                                <li class="flex justify-between items-center">
                                    <span class="font-mono text-xs">${section.position}. ${section.name}</span>
                                    <span class="text-gray-600">${section.char_count.toLocaleString()} chars</span>
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    
                    breakdownDiv.innerHTML = html;
                    breakdownDiv.classList.remove('hidden');
                })
                .catch(err => {
                    breakdownDiv.innerHTML = `<p class="text-red-600">Error: ${err.message}</p>`;
                    breakdownDiv.classList.remove('hidden');
                });
        }
    </script>
</body>
</html>
```

---

#### Task 0026-008-003: Delete Astro and Preact Files

**Files to DELETE** (no longer needed):

**Astro Pages** (3 files):
1. `web/src/pages/admin/index.astro`
2. `web/src/pages/admin/sessions.astro`
3. `web/src/pages/admin/sessions/[id].astro`

**Preact Components** (3 files):
4. `web/src/components/admin/SessionFilters.tsx`
5. `web/src/components/admin/SessionDetail.tsx`
6. `web/src/components/admin/PromptInspector.tsx`

**Directories to DELETE** (if empty after removing above):
7. `web/src/pages/admin/` (entire directory)
8. `web/src/components/admin/` (entire directory)

**Total**: 6 files + 2 directories removed

**What's LEFT**:
- `web/public/admin/sessions.html` (new)
- `web/public/admin/session.html` (new)
- Backend APIs (unchanged)
- Database schema (unchanged)
- `PromptBreakdownService` (unchanged)

---

#### Task 0026-008-004: Update Astro Config (Optional Cleanup)

**File**: `web/astro.config.mjs`

Since we're no longer using Astro pages for admin, we can optionally:
- Remove `output: 'hybrid'` (revert to default static)
- Keep Preact integration for chat UI (if still needed elsewhere)
- Keep proxy config for API calls

**Decision**: Leave config as-is unless admin was the ONLY reason for SSR mode.

---

### Comparison: Before vs After

| Aspect | Before (Astro + Preact) | After (HTMX + Vanilla JS) |
|--------|------------------------|---------------------------|
| **Files** | 6 files (3 Astro + 3 Preact) | 2 HTML files |
| **Build** | Required (`npm run build`) | None (edit and refresh) |
| **Dependencies** | Astro, Preact, @astrojs/preact | HTMX CDN, TailwindCSS CDN |
| **Hydration** | Client-side hydration issues | No hydration needed |
| **Routing** | Astro SSR with dynamic routes | Simple URL query params |
| **Debugging** | Framework stack traces | Standard browser console |
| **Load Time** | ~200-500ms (SSR + hydration) | ~50-100ms (static HTML) |
| **Code Size** | ~500 lines across 6 files | ~200 lines across 2 files |

---

### Benefits of HTMX Approach

1. **Simplicity**: 2 HTML files vs 6+ framework files
2. **No Build Step**: Edit HTML, refresh browser, done
3. **No Hydration**: No framework mounting/rendering issues
4. **Standard Web**: Just HTML + JS + CSS (any developer can read it)
5. **Fast**: Static HTML loads instantly
6. **Debuggable**: Browser DevTools, no framework abstractions
7. **Portable**: Copy HTML files anywhere, they work

---

### Testing Checklist

**Test 1: Sessions List**
1. Visit `http://localhost:4321/admin/sessions.html`
2. **Expected**: Table loads with sessions from database
3. **Expected**: Account/Agent filters work
4. **Expected**: Refresh button reloads data

**Test 2: Session Detail**
1. Click "View Detail" on any session
2. **Expected**: Redirects to `/admin/session.html?id=xxx`
3. **Expected**: Messages display in timeline
4. **Expected**: User/Assistant messages styled differently

**Test 3: Prompt Inspector**
1. Click "🔍 View Prompt Breakdown" on any assistant message
2. **Expected**: Breakdown expands with sections list
3. **Expected**: Shows character counts and sources
4. **Expected**: Clicking again collapses it

**Test 4: Tool Calls**
1. Find message with tool calls in `meta`
2. **Expected**: Yellow box shows tool call details
3. **Expected**: JSON formatted and readable

**Test 5: Browser Compatibility**
1. Test in Chrome, Firefox, Safari
2. **Expected**: Works identically in all browsers
3. **Expected**: No console errors

---

### Migration Steps

1. **Create** `web/public/admin/sessions.html` (Task 0026-008-001)
2. **Create** `web/public/admin/session.html` (Task 0026-008-002)
3. **Test** both pages work correctly
4. **Delete** 6 Astro/Preact files (Task 0026-008-003)
5. **Delete** empty directories (`web/src/pages/admin/`, `web/src/components/admin/`)
6. **Commit**: `"refactor: replace Astro+Preact admin UI with HTMX+vanilla JS (2 HTML files, zero build)"`

---

### Future Enhancements (Post-MVP)

If we need more features later:
- **Pagination**: Add prev/next buttons with offset tracking
- **Search**: Add text search input that filters sessions
- **Export**: Add "Download as JSON" button for debugging
- **Real-time**: Use HTMX polling (`hx-trigger="every 5s"`) for auto-refresh
- **Theming**: Add dark mode toggle (pure CSS)

---

## Phase 3C: Inline Prompt Content Viewer with Module Breakdown

**Status**: PROPOSED

**Goal**: Enable viewing the **actual text content** of each prompt module inline, with proper separation for directory sections to debug multi-tool selection. Each module is independently expandable to see exactly what the LLM saw.

---

### Current Behavior (Phase 3B)

Click "🔍 View Prompt Breakdown" → inline expansion shows metadata only:

```
Prompt Sections: 3 sections, 14,228 characters total

Section 1: directory_docs
  Source: auto-generated | Position: 1 | Characters: 8,600

Section 2: system_prompt
  Source: system_prompt.md | Position: 2 | Characters: 3,200

Section 3: few_shot_examples
  Source: few_shot_examples.md | Position: 3 | Characters: 2,428
```

**Problems**:
1. Can't see the actual text sent to the LLM
2. `directory_docs` is one blob - can't see individual directories
3. No way to debug "why did the LLM choose doctors instead of phone_numbers?"

---

### Desired Behavior (Phase 3C)

Make each module **clickable** to expand/collapse full text inline, with directory sections broken out:

```
Prompt Sections: 6 modules, 14,228 characters total

▶ tool_selection_hints.md (1) - 4,928 chars
▼ directory_docs_header (2) - 150 chars — click to collapse
  ┌─────────────────────────────────────────────────┐
  │ ## Directory Tool                               │
  │ You have access to multiple directories...      │
  └─────────────────────────────────────────────────┘
  
  ▼ directory: doctors (3) - 3,500 chars
    ┌─────────────────────────────────────────────────┐
    │ ### Directory: `doctors` (45 doctors)           │
    │ **Contains**: Licensed physicians...            │
    │ **Use for**: Finding doctor info...             │
    └─────────────────────────────────────────────────┘
  
  ▶ directory: phone_numbers (4) - 2,600 chars
  
▶ system_prompt.md (5) - 3,200 chars
▶ few_shot_examples.md (6) - 2,100 chars
```

**Benefits:**
- See each prompt module independently
- Directory sections separated for debugging tool selection
- Visual hierarchy (nested indentation)
- No page navigation
- Compare prompts across multiple messages

---

### Architecture Changes

#### Backend: Structured Prompt Breakdown

**New Data Structure** (stored in `llm_requests.meta["prompt_breakdown"]`):

```json
{
  "sections": [
    {
      "name": "tool_selection_hints.md",
      "position": 1,
      "characters": 4928,
      "source": "tool_selection_hints.md",
      "content": "## Critical Rules...",
      "type": "module"
    },
    {
      "name": "directory_docs_header",
      "position": 2,
      "characters": 150,
      "source": "auto-generated",
      "content": "## Directory Tool\n\nYou have access to...",
      "type": "directory_header"
    },
    {
      "name": "directory: doctors",
      "position": 3,
      "characters": 3500,
      "source": "auto-generated (doctors.yaml schema)",
      "content": "### Directory: `doctors`...",
      "type": "directory",
      "parent_position": 2,
      "metadata": {
        "list_name": "doctors",
        "entry_count": 45,
        "entry_type": "doctor",
        "schema_file": "doctors.yaml"
      }
    },
    {
      "name": "directory: phone_numbers",
      "position": 4,
      "characters": 2600,
      "source": "auto-generated (phone_numbers.yaml schema)",
      "content": "### Directory: `phone_numbers`...",
      "type": "directory",
      "parent_position": 2,
      "metadata": {
        "list_name": "phone_numbers",
        "entry_count": 120,
        "entry_type": "contact",
        "schema_file": "phone_numbers.yaml"
      }
    },
    {
      "name": "system_prompt.md",
      "position": 5,
      "characters": 3200,
      "source": "system_prompt.md",
      "content": "You are a helpful assistant...",
      "type": "module"
    },
    {
      "name": "few_shot_examples.md",
      "position": 6,
      "characters": 2100,
      "source": "few_shot_examples.md",
      "content": "Example 1: User asks...",
      "type": "module"
    }
  ],
  "total_characters": 16478
}
```

**Key Changes**:
- `position`: Simple incrementing integer (order in final prompt)
- `type`: `"module"`, `"directory_header"`, or `"directory"`
- `parent_position`: Links directory sections to their header (for UI nesting)
- `metadata`: Directory-specific info (entry counts, schema file)
- `content`: **Full text** as sent to LLM

---

### Implementation Tasks

#### Task 3C-001: Fix Button Visibility Bug

**Issue**: "View Prompt Breakdown" button appears in both user AND assistant messages.

**Fix**: Only show for `msg.role === 'user'`.

**File**: `web/public/admin/session.html` in `renderMessages()`:

```javascript
${msg.role === 'user' && msg.llm_request_id ? `
    <div class="mt-3">
        <button class="px-3 py-1 bg-gray-200 text-gray-800 rounded-md text-sm hover:bg-gray-300"
                hx-get="/api/admin/llm-requests/${msg.llm_request_id}"
                hx-trigger="click"
                hx-target="#breakdown-${msg.llm_request_id}"
                hx-swap="none"
                hx-on::after-request="renderPromptBreakdown(event.detail.xhr.responseText, '${msg.llm_request_id}');">
            🔍 View Prompt Breakdown
        </button>
        <div id="breakdown-${msg.llm_request_id}" class="hidden mt-3 p-3 bg-gray-50 rounded text-sm">
            <!-- Prompt breakdown will be loaded here -->
        </div>
    </div>
` : ''}
```

---

#### Task 3C-002: Refactor `generate_directory_tool_docs()` to Return Structured Data

**Goal**: Return both the full markdown text (for prompt assembly) AND structured breakdown (for debugging).

**File**: `backend/app/agents/tools/prompt_generator.py`

**Add new Pydantic models**:

```python
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class DirectorySection(BaseModel):
    """Single directory's documentation section."""
    name: str = Field(description="Display name, e.g., 'directory: doctors'")
    content: str = Field(description="Full markdown text for this directory")
    character_count: int = Field(description="Character count")
    metadata: Dict[str, Any] = Field(description="list_name, entry_count, entry_type, schema_file")

class DirectoryDocsResult(BaseModel):
    """Complete result from directory docs generation."""
    full_text: str = Field(description="Concatenated markdown for prompt assembly")
    header_section: Optional[DirectorySection] = Field(None, description="Multi-directory header (if applicable)")
    directory_sections: List[DirectorySection] = Field(description="Individual directory docs")
```

**Update `generate_directory_tool_docs()` signature**:

```python
async def generate_directory_tool_docs(
    agent_config: Dict,
    account_id: UUID,
    db_session: AsyncSession
) -> DirectoryDocsResult:  # Changed return type
    """
    Auto-generate directory tool docs with structured breakdown.
    
    Returns:
        DirectoryDocsResult with full_text (for prompt) and sections (for breakdown)
    """
```

**Implementation approach**:

1. Build `header_content` string and `header_section` object (if multiple directories)
2. For each directory, build both `dir_content` string and `DirectorySection` object
3. Concatenate all strings into `full_text`
4. Return `DirectoryDocsResult(full_text=..., header_section=..., directory_sections=[...])`

**Example construction**:

```python
# Inside generate_directory_tool_docs()
header_section = None
directory_sections = []
all_text_parts = []

if len(lists_metadata) > 1:
    # Build header
    header_text = "## Directory Tool\n\nYou have access to multiple directories..."
    header_section = DirectorySection(
        name="directory_docs_header",
        content=header_text,
        character_count=len(header_text),
        metadata={"type": "multi_directory_header"}
    )
    all_text_parts.append(header_text)

for list_meta in lists_metadata:
    # Build directory-specific text
    dir_text = f"### Directory: `{list_meta.list_name}`\n..."
    
    directory_sections.append(DirectorySection(
        name=f"directory: {list_meta.list_name}",
        content=dir_text,
        character_count=len(dir_text),
        metadata={
            "list_name": list_meta.list_name,
            "entry_count": entry_count,
            "entry_type": list_meta.entry_type,
            "schema_file": list_meta.schema_file
        }
    ))
    all_text_parts.append(dir_text)

full_text = '\n\n'.join(all_text_parts)

return DirectoryDocsResult(
    full_text=full_text,
    header_section=header_section,
    directory_sections=directory_sections
)
```

---

#### Task 3C-003: Update `PromptBreakdownService` to Handle Structured Directories

**File**: `backend/app/services/prompt_breakdown_service.py`

**Update signature**:

```python
@staticmethod
def capture_breakdown(
    base_prompt: str,
    critical_rules: Optional[str] = None,
    directory_result: Optional['DirectoryDocsResult'] = None,  # NEW: Structured data
    modules: Optional[Dict[str, str]] = None,
    account_slug: Optional[str] = None,
    agent_instance_slug: Optional[str] = None
) -> dict:
    """
    Capture prompt breakdown with full content for each module.
    
    Args:
        base_prompt: Base system prompt content
        critical_rules: Critical tool selection rules
        directory_result: Structured directory docs (header + sections)
        modules: Dict of {module_name: content} for additional modules
        
    Returns:
        Dict with sections array, each containing name, position, characters, source, content, type
    """
```

**Implementation**:

```python
breakdown = {"sections": []}
position = 1

# 1. Critical rules (if present)
if critical_rules:
    breakdown["sections"].append({
        "name": "tool_selection_hints.md",
        "position": position,
        "characters": len(critical_rules),
        "source": "tool_selection_hints.md",
        "content": critical_rules,
        "type": "module"
    })
    position += 1

# 2. Base system prompt
breakdown["sections"].append({
    "name": "system_prompt.md",
    "position": position,
    "characters": len(base_prompt),
    "source": "system_prompt.md",
    "content": base_prompt,
    "type": "module"
})
position += 1

# 3. Directory documentation (structured)
if directory_result:
    header_position = None
    
    # 3a. Directory header (if multi-directory)
    if directory_result.header_section:
        header_position = position
        breakdown["sections"].append({
            "name": directory_result.header_section.name,
            "position": position,
            "characters": directory_result.header_section.character_count,
            "source": "auto-generated",
            "content": directory_result.header_section.content,
            "type": "directory_header"
        })
        position += 1
    
    # 3b. Individual directory sections
    for dir_section in directory_result.directory_sections:
        section_dict = {
            "name": dir_section.name,
            "position": position,
            "characters": dir_section.character_count,
            "source": f"auto-generated ({dir_section.metadata.get('schema_file', 'N/A')})",
            "content": dir_section.content,
            "type": "directory",
            "metadata": dir_section.metadata
        }
        if header_position is not None:
            section_dict["parent_position"] = header_position
        
        breakdown["sections"].append(section_dict)
        position += 1

# 4. Additional modules
if modules:
    for module_name, content in modules.items():
        breakdown["sections"].append({
            "name": f"{module_name}.md",
            "position": position,
            "characters": len(content),
            "source": f"{module_name}.md",
            "content": content,
            "type": "module"
        })
        position += 1

breakdown["total_characters"] = sum(s["characters"] for s in breakdown["sections"])

return breakdown
```

---

#### Task 3C-004: Update `simple_chat.py` to Use New Structure

**File**: `backend/app/agents/simple_chat.py`

**Find the existing call** (around lines 247-250):

```python
directory_docs = await generate_directory_tool_docs(
    agent_config=instance_config or {},
    account_id=account_id,
    db_session=db_session
)
```

**Change to**:

```python
directory_result = await generate_directory_tool_docs(
    agent_config=instance_config or {},
    account_id=account_id,
    db_session=db_session
)
directory_docs = directory_result.full_text if directory_result else None
```

**Find the `PromptBreakdownService.capture_breakdown()` call** (around line 308):

```python
prompt_breakdown = PromptBreakdownService.capture_breakdown(
    base_prompt=base_system_prompt,
    critical_rules=critical_rules if critical_rules else None,
    directory_docs=directory_docs if directory_config.get("enabled", False) else None,  # OLD
    modules={name: load_prompt_module(name, account_slug) 
             for name in other_modules} if prompting_config.get('enabled') and other_modules else None,
    account_slug=account_slug,
    agent_instance_slug=agent_instance_slug
)
```

**Change to**:

```python
prompt_breakdown = PromptBreakdownService.capture_breakdown(
    base_prompt=base_system_prompt,
    critical_rules=critical_rules if critical_rules else None,
    directory_result=directory_result if directory_config.get("enabled", False) and account_id else None,  # NEW
    modules={name: load_prompt_module(name, account_slug) 
             for name in other_modules} if prompting_config.get('enabled') and other_modules else None,
    account_slug=account_slug,
    agent_instance_slug=agent_instance_slug
)
```

---

#### Task 3C-005: Update Frontend to Render Nested Sections

**File**: `web/public/admin/session.html`

**Replace `renderPromptBreakdown()` function**:

```javascript
function renderPromptBreakdown(responseText, requestId) {
    const breakdownDiv = document.getElementById(`breakdown-${requestId}`);
    
    // Toggle visibility if already loaded
    if (!breakdownDiv.classList.contains('hidden') && 
        breakdownDiv.innerHTML.includes('Prompt Sections')) {
        breakdownDiv.classList.add('hidden');
        return;
    }

    const data = JSON.parse(responseText);
    const breakdown = data.prompt_breakdown;

    if (breakdown && breakdown.sections && breakdown.sections.length > 0) {
        let html = `
            <h4 class="font-semibold mb-3">
                Prompt Sections: ${breakdown.sections.length} modules, 
                ${breakdown.total_characters.toLocaleString()} characters total
            </h4>
        `;
        
        breakdown.sections.forEach((section, index) => {
            const sectionId = `section-${requestId}-${index}`;
            const hasContent = section.content && section.content.trim().length > 0;
            const isNested = section.parent_position !== undefined;
            const indentClass = isNested ? 'ml-6 border-l-2 border-gray-300 pl-3' : '';
            
            html += `
                <div class="mb-2 ${indentClass}">
                    <!-- Clickable Header -->
                    <button 
                        class="w-full text-left px-3 py-2 bg-gray-100 hover:bg-gray-200 
                               font-medium flex justify-between items-center rounded"
                        onclick="toggleSection('${sectionId}', this)"
                        ${!hasContent ? 'disabled' : ''}>
                        <span class="flex items-center gap-2">
                            <span class="arrow text-gray-600">▶</span> 
                            <span class="font-mono text-sm">${section.name}</span>
                        </span>
                        <span class="text-xs text-gray-600">
                            (${section.position}) ${section.characters.toLocaleString()} chars
                        </span>
                    </button>
                    
                    <!-- Content (expandable) -->
                    ${hasContent ? `
                        <div id="${sectionId}" class="hidden mt-2">
                            <!-- Metadata bar -->
                            <div class="px-3 py-1 text-xs text-gray-600 bg-gray-100 rounded-t border border-gray-300">
                                Source: ${section.source || 'N/A'}
                                ${section.metadata && section.metadata.entry_count ? 
                                    ` | ${section.metadata.entry_count} ${section.metadata.entry_type}s` : ''}
                            </div>
                            <!-- Content box -->
                            <div class="px-3 py-2 bg-white border-x border-b border-gray-300 rounded-b">
                                <pre class="text-xs whitespace-pre-wrap font-mono text-gray-800 
                                           border-l-4 border-blue-400 pl-3 max-h-96 overflow-y-auto">${escapeHtml(section.content)}</pre>
                            </div>
                        </div>
                    ` : `
                        <div class="px-3 py-2 text-xs text-gray-500 italic">
                            Content not captured for this section
                        </div>
                    `}
                </div>
            `;
        });
        
        breakdownDiv.innerHTML = html;
    } else {
        breakdownDiv.innerHTML = '<p class="text-gray-500">No prompt breakdown available.</p>';
    }
    
    breakdownDiv.classList.remove('hidden');
}

// Toggle section content visibility
function toggleSection(sectionId, buttonEl) {
    const contentDiv = document.getElementById(sectionId);
    const arrow = buttonEl.querySelector('.arrow');
    
    if (contentDiv.classList.contains('hidden')) {
        contentDiv.classList.remove('hidden');
        arrow.textContent = '▼';
    } else {
        contentDiv.classList.add('hidden');
        arrow.textContent = '▶';
    }
}

// HTML escape utility (already exists, keep as-is)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

**Key Features**:
- `isNested` check determines if section has `parent_position`
- `indentClass` adds left margin and border for nested items
- Position number shown in metadata: `(3) 3,500 chars`
- Entry count displayed for directory sections: `45 doctors`
- Arrow indicator (▶/▼) for expand/collapse

---

### Visual Example (After Implementation)

**Collapsed State**:
```
Prompt Sections: 6 modules, 16,478 characters total

▶ tool_selection_hints.md (1) 4,928 chars
▶ directory_docs_header (2) 150 chars
  ▶ directory: doctors (3) 3,500 chars
  ▶ directory: phone_numbers (4) 2,600 chars
▶ system_prompt.md (5) 3,200 chars
▶ few_shot_examples.md (6) 2,100 chars
```

**Partially Expanded** (directory_docs_header + doctors expanded):
```
Prompt Sections: 6 modules, 16,478 characters total

▶ tool_selection_hints.md (1) 4,928 chars
▼ directory_docs_header (2) 150 chars
  ┌─────────────────────────────────────────────────┐
  │ Source: auto-generated                          │
  ├─────────────────────────────────────────────────┤
  │ ## Directory Tool                               │
  │                                                  │
  │ You have access to multiple directories.        │
  │ Choose the appropriate directory...             │
  └─────────────────────────────────────────────────┘
  
  ▼ directory: doctors (3) 3,500 chars
    ┌─────────────────────────────────────────────────┐
    │ Source: auto-generated (doctors.yaml) | 45 doctors │
    ├─────────────────────────────────────────────────┤
    │ ### Directory: `doctors` (45 doctors)           │
    │ **Contains**: Licensed physicians...            │
    │ **Use for**: Finding doctor information...      │
    │                                                  │
    │ **Term Mappings (Lay → Formal):**               │
    │   • "heart doctor" → "cardiologist"             │
    │   • "bone doctor" → "orthopedist"               │
    │ ...                                              │
    └─────────────────────────────────────────────────┘
  
  ▶ directory: phone_numbers (4) 2,600 chars
  
▶ system_prompt.md (5) 3,200 chars
▶ few_shot_examples.md (6) 2,100 chars
```

---

### Testing Plan

#### Test 1: Simple Agent (No Directories)

**Agent**: `default_account > simple_chat1` (no directory tool)

**Expected Breakdown**:
```
▶ system_prompt.md (1) 800 chars
```

**Test**:
1. Navigate to session detail for simple_chat1 session
2. Click "View Prompt Breakdown" on user message
3. Verify only system_prompt appears
4. Click system_prompt → text expands
5. Click again → collapses

---

#### Test 2: Single Directory Agent

**Agent**: `wyckoff > wyckoff_info_chat1` (doctors directory only)

**Expected Breakdown**:
```
▶ tool_selection_hints.md (1) 4,928 chars
▶ system_prompt.md (2) 3,200 chars
▶ directory: doctors (3) 3,500 chars   ← NO header (single directory)
▶ few_shot_examples.md (4) 2,100 chars
```

**Test**:
1. Navigate to session with directory usage
2. Click "View Prompt Breakdown"
3. Verify NO "directory_docs_header" (single directory case)
4. Verify "directory: doctors" is top-level (no indentation)
5. Expand directory section → see doctor search strategy
6. Verify metadata shows entry count: "45 doctors"

---

#### Test 3: Multi-Directory Agent

**Agent**: `wyckoff > wyckoff_multi_chat1` (doctors + phone_numbers)

**Expected Breakdown**:
```
▶ tool_selection_hints.md (1) 4,928 chars
▶ system_prompt.md (2) 3,200 chars
▶ directory_docs_header (3) 150 chars
  ▶ directory: doctors (4) 3,500 chars        ← Indented
  ▶ directory: phone_numbers (5) 2,600 chars  ← Indented
▶ few_shot_examples.md (6) 2,100 chars
```

**Test**:
1. Navigate to session with multi-directory usage
2. Click "View Prompt Breakdown"
3. Verify "directory_docs_header" exists at top level
4. Verify directory sections are visually indented (CSS `ml-6`)
5. Expand header → see "You have access to multiple directories" text
6. Expand "directory: doctors" → see doctor-specific search strategy
7. Expand "directory: phone_numbers" → see phone-specific search strategy
8. Verify metadata shows different entry counts for each

---

#### Test 4: Button Visibility (Bug Fix)

**Test**:
1. View any session detail page
2. Verify "View Prompt Breakdown" button ONLY on user messages
3. Verify NO button on assistant messages
4. Verify tool calls still display (yellow box)

---

#### Test 5: Edge Cases

**Test 5a: Missing Content**
- Old session (before Phase 3C) → sections exist but no `content` field
- **Expected**: Button disabled, shows "Content not captured"

**Test 5b: Empty Session**
- Session with no LLM requests
- **Expected**: No breakdown buttons at all

**Test 5c: Database Query**
- Query `llm_requests` table after creating new session
- **Expected**: `meta["prompt_breakdown"]["sections"]` contains `content` field
- **Expected**: JSONB column size reasonable (< 500KB per request)

---

### Migration Checklist

**Phase 1: Backend Changes** (Breaking Changes)
1. ✅ Update `prompt_generator.py` - add Pydantic models, change return type
2. ✅ Update `PromptBreakdownService` - accept `directory_result`, store structured data
3. ✅ Update `simple_chat.py` - use new `DirectoryDocsResult`, pass to breakdown service
4. ✅ Test backend: Create new session, verify breakdown structure in database

**Phase 2: Frontend Changes**
5. ✅ Fix button visibility bug in `session.html`
6. ✅ Update `renderPromptBreakdown()` to handle nested sections
7. ✅ Test frontend: View existing session (should fail gracefully), view new session (should show nested structure)

**Phase 3: Verification**
8. ✅ Test single-directory agent
9. ✅ Test multi-directory agent
10. ✅ Test agent with no directories
11. ✅ Compare prompts across messages (expand multiple breakdowns)
12. ✅ Verify metadata display (entry counts, source files)

**Phase 4: Commit**
13. ✅ Commit: `"feat(admin): add inline prompt content viewer with structured directory breakdown (Phase 3C)"`

---

### Future Enhancements

**Post-MVP Features**:
- **Syntax Highlighting**: Use Prism.js for markdown rendering in expanded sections
- **Copy Button**: Copy individual section text to clipboard
- **Search**: Text search within expanded sections (highlight matches)
- **Diff View**: Side-by-side comparison of prompts across two messages
- **Export**: Download full prompt as markdown file
- **Collapse All / Expand All**: Buttons to toggle all sections at once
- **Filter by Type**: Show only directories, or only modules
- **Token Count**: Show token count alongside character count (using tiktoken)

---

### Database Impact

**Storage Estimate** (per LLM request):

| Component | Size |
|-----------|------|
| Metadata (position, name, source, type) | ~500 bytes |
| System prompt content | ~3 KB |
| Critical rules content | ~5 KB |
| Directory header content | ~200 bytes |
| Single directory content | ~3-5 KB each |
| Prompt module content | ~2-3 KB each |
| **Total (multi-directory agent)** | **~20-30 KB per request** |

**Mitigation**:
- JSONB compression (Postgres compresses text well)
- Add retention policy: Delete `meta["prompt_breakdown"]["sections"][*].content` for requests older than 30 days
- Keep metadata (position, characters, source) forever - only delete content
- Env var: `ADMIN_CAPTURE_PROMPT_CONTENT=true` (default: true for dev, false for prod)

**Example cleanup query**:
```sql
-- Remove content but keep metadata after 30 days
UPDATE llm_requests
SET meta = jsonb_set(
    meta,
    '{prompt_breakdown,sections}',
    (SELECT jsonb_agg(
        jsonb_strip_nulls(section - 'content')
    ) FROM jsonb_array_elements(meta->'prompt_breakdown'->'sections') AS section)
)
WHERE created_at < NOW() - INTERVAL '30 days'
  AND meta->'prompt_breakdown'->'sections' IS NOT NULL;
```

---

## Dependencies

- Astro 5.13.0 (installed)
- Preact 10.27.0 (installed)
- @astrojs/preact 4.1.0 (installed)
- TailwindCSS 4.1.12 (installed)
- FastAPI (installed)
- SQLAlchemy (installed)

---

## Related Documents

- `memorybank/architecture/agent-and-tool-design.md`
- `memorybank/design/dynamic-prompting.md`
- `memorybank/design/prompt-modules.md`
- `memorybank/project-management/0025-dynamic-prompting-plan.md`
