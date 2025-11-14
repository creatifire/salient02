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

### 📋 **Phase 3: Session-Based Authentication** (PLANNED)
- ⏳ Feature 0026-006: Replace HTTP Basic Auth with session-based login
  - Task 001: Create POST /api/admin/login endpoint
  - Task 002: Update AdminAuthMiddleware to check session
  - Task 003: Create /admin/login page
  - Task 004: Create LoginForm component
  - Task 005: Update existing components to use credentials: 'include'

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

**Next Steps**:
1. Run database migration: `alembic upgrade head`
2. Set ADMIN_USERNAME/ADMIN_PASSWORD in .env
3. Test current implementation at /admin/sessions
4. Implement Phase 3 (session-based auth) for better UX
5. Implement Phase 4 (UI polish) for professional appearance

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

### Phase 4: UI Polish & Layout Improvements

**Goal**: Transform basic admin interface into polished, professional-looking dashboard matching modern design standards

**Current State**: Basic HTML pages with minimal styling - functional but not polished

**Target State**: Clean, modern interface with:
- Professional sidebar navigation with icons
- Polished header with breadcrumbs and user info
- Card-based layouts with proper shadows and spacing
- Improved tables with avatars, badges, and hover states
- Consistent color scheme and typography
- Responsive design for mobile/tablet

**Implementation**: Pure TailwindCSS (already installed at v4.1.12)

#### Feature 0026-007: Admin UI Polish

##### Task 0026-007-001: Create Admin Layout Wrapper
**File**: `web/src/layouts/AdminLayout.astro`

Create consistent layout with sidebar navigation:

```astro
---
interface Props {
    title: string;
    breadcrumbs?: Array<{ label: string; href?: string }>;
}

const { title, breadcrumbs = [] } = Astro.props;
---

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Admin</title>
</head>
<body class="bg-gray-50">
    <div class="flex h-screen">
        <!-- Sidebar -->
        <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
            <!-- Logo -->
            <div class="h-16 flex items-center px-6 border-b border-gray-200">
                <h1 class="text-xl font-bold text-gray-900">OpenThought</h1>
            </div>
            
            <!-- Navigation -->
            <nav class="flex-1 px-4 py-6 space-y-1">
                <a href="/admin/sessions" 
                   class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span class="font-medium">Sessions</span>
                </a>
                
                <a href="/admin/analytics" 
                   class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span class="font-medium">Analytics</span>
                </a>
            </nav>
            
            <!-- User Info -->
            <div class="p-4 border-t border-gray-200">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <span class="text-blue-600 font-semibold">A</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900 truncate">Admin</p>
                        <p class="text-xs text-gray-500 truncate">admin@localhost</p>
                    </div>
                </div>
                <a href="/api/admin/logout" 
                   class="mt-2 block text-xs text-gray-500 hover:text-gray-700">
                    Logout
                </a>
            </div>
        </aside>
        
        <!-- Main Content -->
        <div class="flex-1 flex flex-col overflow-hidden">
            <!-- Header -->
            <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
                <div>
                    <nav class="flex items-center gap-2 text-sm text-gray-500 mb-1">
                        {breadcrumbs.map((crumb, i) => (
                            <>
                                {i > 0 && <span>/</span>}
                                {crumb.href ? (
                                    <a href={crumb.href} class="hover:text-gray-700">{crumb.label}</a>
                                ) : (
                                    <span class="text-gray-900 font-medium">{crumb.label}</span>
                                )}
                            </>
                        ))}
                    </nav>
                    <h1 class="text-xl font-semibold text-gray-900">{title}</h1>
                </div>
            </header>
            
            <!-- Page Content -->
            <main class="flex-1 overflow-auto p-6">
                <slot />
            </main>
        </div>
    </div>
</body>
</html>
```

##### Task 0026-007-002: Create Reusable UI Components
**File**: `web/src/components/admin/ui/Card.tsx`

```tsx
import { h } from 'preact';

interface CardProps {
    children: any;
    className?: string;
}

export function Card({ children, className = '' }: CardProps) {
    return (
        <div class={`bg-white rounded-xl shadow-sm border border-gray-200 ${className}`}>
            {children}
        </div>
    );
}

export function CardHeader({ children, className = '' }: CardProps) {
    return (
        <div class={`px-6 py-4 border-b border-gray-200 ${className}`}>
            {children}
        </div>
    );
}

export function CardBody({ children, className = '' }: CardProps) {
    return (
        <div class={`px-6 py-4 ${className}`}>
            {children}
        </div>
    );
}
```

**File**: `web/src/components/admin/ui/Badge.tsx`

```tsx
import { h } from 'preact';

interface BadgeProps {
    children: any;
    variant?: 'blue' | 'green' | 'red' | 'yellow' | 'gray';
}

const variantStyles = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    gray: 'bg-gray-50 text-gray-700 border-gray-200'
};

export function Badge({ children, variant = 'gray' }: BadgeProps) {
    return (
        <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantStyles[variant]}`}>
            {children}
        </span>
    );
}
```

**File**: `web/src/components/admin/ui/Avatar.tsx`

```tsx
import { h } from 'preact';

interface AvatarProps {
    name: string;
    src?: string;
    size?: 'sm' | 'md' | 'lg';
}

const sizeStyles = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base'
};

export function Avatar({ name, src, size = 'md' }: AvatarProps) {
    const initials = name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    
    return (
        <div class={`${sizeStyles[size]} rounded-full bg-blue-100 flex items-center justify-center overflow-hidden`}>
            {src ? (
                <img src={src} alt={name} class="w-full h-full object-cover" />
            ) : (
                <span class="text-blue-600 font-semibold">{initials}</span>
            )}
        </div>
    );
}
```

##### Task 0026-007-003: Update Sessions List Page
Replace basic styling with polished design:

```astro
---
import AdminLayout from '../../layouts/AdminLayout.astro';
---

<AdminLayout 
    title="Chat Sessions" 
    breadcrumbs={[
        { label: 'Admin', href: '/admin' },
        { label: 'Sessions' }
    ]}
>
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="flex items-center justify-between mb-2">
                <p class="text-sm font-medium text-gray-600">Total Sessions</p>
                <svg class="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z"/>
                    <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z"/>
                </svg>
            </div>
            <p class="text-3xl font-bold text-gray-900">127</p>
            <p class="text-sm text-green-600 mt-1">↑ 12% from last week</p>
        </div>
        
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="flex items-center justify-between mb-2">
                <p class="text-sm font-medium text-gray-600">Avg Messages</p>
                <svg class="w-5 h-5 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 5a2 2 0 012-2h8a2 2 0 012 2v10a2 2 0 002 2H4a2 2 0 01-2-2V5zm3 1h6v4H5V6zm6 6H5v2h6v-2z"/>
                </svg>
            </div>
            <p class="text-3xl font-bold text-gray-900">4.2</p>
            <p class="text-sm text-gray-500 mt-1">per session</p>
        </div>
        
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="flex items-center justify-between mb-2">
                <p class="text-sm font-medium text-gray-600">Tool Calls</p>
                <svg class="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"/>
                </svg>
            </div>
            <p class="text-3xl font-bold text-gray-900">234</p>
            <p class="text-sm text-red-600 mt-1">↓ 3% from yesterday</p>
        </div>
    </div>

    <!-- Filters & Table -->
    <div id="session-filters"></div>
</AdminLayout>
```

##### Task 0026-007-004: Update SessionFilters Component
Improve table styling with hover states, badges, and proper spacing:

```tsx
// Replace table rendering with:
<table class="min-w-full divide-y divide-gray-200">
    <thead>
        <tr class="bg-gray-50">
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Session
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Account
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Messages
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
            </th>
        </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
        {sessions.map((session) => (
            <tr key={session.id} class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10 bg-gray-100 rounded-lg flex items-center justify-center">
                            <svg class="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z"/>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">
                                {session.id.substring(0, 8)}
                            </div>
                            <div class="text-sm text-gray-500">
                                ID: {session.id.substring(0, 8)}...
                            </div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <Badge variant="blue">{session.account_slug || 'N/A'}</Badge>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {session.agent_instance_slug || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <span class="text-sm font-medium text-gray-900">{session.message_count}</span>
                        <span class="ml-2 text-xs text-gray-500">messages</span>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(session.created_at).toLocaleString()}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <a
                        href={`/admin/sessions/${session.id}`}
                        class="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                    >
                        View Details
                        <svg class="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                        </svg>
                    </a>
                </td>
            </tr>
        ))}
    </tbody>
</table>
```

##### Task 0026-007-005: Polish Session Detail Page
Add visual hierarchy, better message bubbles, and improved sidebar:

- Message bubbles with proper shadows and spacing
- User/assistant avatars
- Tool call badges with icons
- Sticky prompt inspector sidebar
- Better color coding (blue for user, green for assistant, yellow for tool calls)

**Benefits**:
- Professional, modern appearance
- Better visual hierarchy and information density
- Improved usability with hover states and clear CTAs
- Consistent design language across all admin pages
- Responsive design for different screen sizes
- Uses only TailwindCSS (no additional dependencies)

---

## File Structure

```
web/src/
├── pages/admin/
│   ├── index.astro                      # Redirect to /admin/sessions
│   ├── login.astro                      # Admin login page (Phase 3)
│   ├── sessions.astro                   # Session list
│   └── sessions/[id].astro              # Session detail
├── components/admin/
│   ├── LoginForm.tsx                    # Login form component (Phase 3)
│   ├── SessionFilters.tsx               # Filter component
│   ├── SessionDetail.tsx                # Conversation timeline
│   └── PromptInspector.tsx              # Prompt breakdown

backend/app/
├── api/admin.py                          # Admin endpoints (login, sessions, llm-requests)
├── middleware/admin_auth_middleware.py   # Session-based auth (Phase 3) / HTTP Basic Auth (Phase 0-2)
└── services/prompt_breakdown_service.py  # Breakdown capture
```

---

## API Response Schemas

### Sessions List
```json
{
  "sessions": [{
    "id": "uuid",
    "account_slug": "wyckoff",
    "agent_instance_slug": "wyckoff_info_chat1",
    "created_at": "2025-11-12T20:46:10Z",
    "message_count": 4
  }],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### Session Messages
```json
{
  "session_id": "uuid",
  "messages": [{
    "id": "uuid",
    "role": "user",
    "content": "what is the number of the pharmacy",
    "created_at": "2025-11-12T20:47:49Z"
  }, {
    "id": "uuid",
    "role": "assistant",
    "content": "I don't have the specific phone number...",
    "llm_request_id": "uuid",
    "meta": {
      "model": "google/gemini-2.5-flash",
      "input_tokens": 15410,
      "cost": 0.04623,
      "tool_calls": [{"tool_name": "vector_search", "args": {...}}]
    }
  }]
}
```

### LLM Request Detail
```json
{
  "id": "uuid",
  "model": "google/gemini-2.5-flash",
  "prompt_breakdown": {
    "sections": [
      {"name": "critical_rules", "char_count": 4928, "source": "tool_selection_hints.md"},
      {"name": "base_prompt", "char_count": 3200, "source": "system_prompt.md"},
      {"name": "directory_docs", "char_count": 6100, "source": "auto-generated"}
    ],
    "total_char_count": 14228
  },
  "tool_calls": [
    {"tool_name": "vector_search", "args": {"query": "phone number"}}
  ],
  "response": {
    "content": "I don't have the specific phone number...",
    "input_tokens": 15410,
    "cost": 0.04623
  }
}
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
