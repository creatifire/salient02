# Epic 0026 - Simple Admin Frontend for Chat Tracing

**Status**: Phase 3B Complete ✅ (Core functionality shipped)  
**Created**: 2025-11-12  
**Updated**: 2025-11-14  
**Priority**: Medium  
**Category**: Developer Tools / Debugging

**Shipped Features**:
- ✅ Session browser with account/agent filters
- ✅ Conversation timeline with message history
- ✅ Prompt breakdown viewer (module composition)
- ✅ LLM metadata display (model, tokens, cost, latency)
- ✅ Tool call inspection
- ✅ Response Quality UI (ready for Epic 0027)

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

### **Phase 3: Admin UI Refinement**

#### ❌ **Phase 3A: Session-Based Authentication** (DEPRECATED)
- Feature 0026-006: Replace HTTP Basic Auth with session-based login
  - Status: **Removed per BUG-0026-0002** (authentication unnecessary for localhost debugging tool)
  - Tasks 001-005: Login/logout endpoints, session middleware, Astro login page (all removed)

#### ✅ **Phase 3B: Session Browser in HTMX** (COMPLETE)
- ✅ Feature 0026-008: Replace Astro+Preact with HTMX+Vanilla JS
  - ✅ Task 001: Create `sessions.html` (sessions list with filters)
  - ✅ Task 002: Create `session.html` (conversation timeline with prompt inspector)
  - ✅ Task 003: Delete Astro pages and Preact components (6 files removed)
  - ✅ Task 004: Update Astro config (optional cleanup)
  - ✅ Task 005: Add Response Quality UI section (Epic 0027 prep - confidence scores & reasoning chains)
  - ✅ Task 006: Fix BUG-0026-0003 (session creation without account/agent context on page load)
- **Result**: 2 static HTML files, no build step, HTMX v2.0.7, TailwindCSS CDN
- **Bug Fixes**: Session creation now deferred to first user message; admin routes skip session handling

#### 📋 **Phase 3C: Inline Prompt Content Viewer with Module Breakdown** (PROPOSED)
- ⏳ Feature 0026-009: Structured prompt breakdown with directory separation + full assembled prompt viewer
  - ✅ Task 3C-001: Verify button visibility logic (confirmed: user messages only) *(already implemented correctly)*
  - ✅ Task 3C-002: Add `assembled_prompt` column to `llm_requests` table
  - ✅ Task 3C-003: Refactor `prompt_generator.py` to return `DirectoryDocsResult` + externalize hardcoded guidance
  - Task 3C-004: Update `PromptBreakdownService` to handle structured directories
  - Task 3C-005: Update `simple_chat.py` to use new structure and capture assembled prompt
  - Task 3C-006: Update `LLMRequestTracker` to accept assembled_prompt parameter
  - Task 3C-007: Add "View Full Assembled Prompt" UI toggle
  - Task 3C-008: Update frontend to render nested sections with CSS indentation
- **Goal**: Show each prompt module independently, break out directory sections for multi-tool debugging, and view the complete assembled prompt as sent to LLM

### 📋 **Phase 4: UI Polish & Layout Improvements** (PLANNED)
- ⏳ Feature 0026-007: Professional dashboard UI (HTMX + TailwindCSS)
  - Task 0026-007-001: Create shared admin.css stylesheet
  - Task 0026-007-002: Add navigation header with branding
  - Task 0026-007-003: Polish sessions list (stats cards, improved filters/table)
  - Task 0026-007-004: Polish session detail (metadata card, message styling, prompt breakdown)
  - Task 0026-007-005: Add loading/empty states
  - Task 0026-007-006: Add keyboard shortcuts
  
**Note**: Phase 4 updated post-Phase 3C to work with HTMX + Vanilla JS architecture (no build step, pure TailwindCSS utilities). See detailed plan below after Phase 3C.

**Commits**:
- `5cae767` - Phase 0-2 implementation (14 files changed)
- `304f32e` - Phase 3A documentation (session auth - later deprecated)
- `7835ae3` - Phase 4 documentation (UI polish)
- Multiple commits - Phase 3B implementation (HTMX migration, bug fixes)
- Latest - BUG-0026-0003 fix (session creation deferral)

**Current Status**: Phase 3B COMPLETE ✅
- Admin UI fully functional at `http://localhost:4321/admin/sessions.html`
- No authentication required (localhost debugging tool)
- Sessions list, detail view, prompt breakdown, tool calls all working
- Session creation bug fixed (no more "vapid sessions")
- Response Quality UI ready for Epic 0027 (reasoning chains & confidence scores)

**Next Steps**:
1. **Phase 3C** (Optional): Implement structured prompt breakdown
   - Break out directory sections for multi-tool debugging
   - Add "View Full Assembled Prompt" toggle
   - Enhanced nested UI for prompt modules
2. **Phase 4** (Optional): UI polish and professional styling
   - Shared stylesheet, navigation header, stats cards
   - Loading states, keyboard shortcuts
3. **Epic 0027**: Capture reasoning chains and confidence scores
   - Backend implementation (6 tasks)
   - UI already ready to display data

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

- **Frontend**: Static HTML + HTMX v2.0.7 + Vanilla JavaScript (no build step)
- **Backend**: FastAPI (Python 3.11+)
- **Styling**: TailwindCSS CDN (no build step)
- **Auth**: None (localhost-only debugging tool)

---

## Routes

### `http://localhost:4321/admin/sessions.html` - Session List ✅
Static HTML page with HTMX filters (account, agent) showing session metadata and message counts.

**Features**:
- Account dropdown filter (acme, agrofresh, wyckoff, etc.)
- Agent instance dropdown filter (dynamically populated)
- Refresh button
- Sortable table with session ID, account, agent, message count, created date
- Click row to view session detail

**API**: `GET /api/admin/sessions?account={slug}&agent={slug}&limit=50`

### `http://localhost:4321/admin/session.html?id={session_id}` - Session Detail ✅
Conversation timeline showing user/assistant messages with expandable metadata.

**Features**:
- Message timeline (user messages in blue, assistant in white)
- LLM Metadata box (model, tokens, cost, latency) for assistant messages
- Response Quality box (confidence scores, reasoning chains) - ready for Epic 0027
- Tool Calls box (always visible for assistant messages with tool calls)
- Prompt Breakdown button (user messages only) - shows prompt composition
- Back to Sessions link

**APIs**: 
- `GET /api/admin/sessions/{id}/messages` - Fetch conversation history
- `GET /api/admin/llm-requests/{request_id}` - Fetch prompt breakdown (HTMX on-demand)

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

#### Task 3C-001: Verify Message Card Content Display (COMPLETE ✅)

**Goal**: Ensure proper information display for User vs Assistant message cards.

**Status**: Already implemented correctly in `session.html` (Phase 3B).

---

**User Message Cards** (Blue background):
- Message content
- **"View Prompt Breakdown" button** - Shows prompt composition (modules, directories, etc.)
  - Button condition: `msg.role === 'user' && msg.llm_request_id`
  - Expandable breakdown section below

**Assistant Message Cards** (White background):
- Message content
- **NO "View Prompt Breakdown" button** (prompt composition is not relevant to assistant output)
- **LLM Metadata** (Purple box) - Always displayed when available:
  - Model used
  - Input/Output/Total tokens
  - Cost
  - Latency (ms)
  - Condition: `!isUser && msg.meta && (msg.meta.model || msg.meta.input_tokens)`
- **Response Quality** (Green box) - Displayed when available (Epic 0027):
  - Confidence score (as percentage)
  - Reasoning chain (formatted text)
  - Condition: `!isUser && msg.meta && (msg.meta.confidence_score || msg.meta.reasoning_chain)`
- **Tool Calls** (Yellow box) - Always displayed when present:
  - Tool name and arguments (JSON formatted)
  - Always visible (not behind a button)
  - Condition: `msg.meta?.tool_calls`

---

**File**: `web/public/admin/session.html` (lines 67-129)

**Verification**:
```javascript
// User messages: Show breakdown button
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

// Assistant messages: LLM Metadata (purple box)
${!isUser && msg.meta && (msg.meta.model || msg.meta.input_tokens) ? `
    <div class="mt-3 p-3 bg-purple-50 rounded border border-purple-200">
        <p class="text-xs font-semibold text-purple-800 mb-2">📊 LLM Metadata:</p>
        <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <div><span class="font-medium text-purple-700">Model:</span> ...</div>
            <div><span class="font-medium text-purple-700">Latency:</span> ...</div>
            <div><span class="font-medium text-purple-700">Input Tokens:</span> ...</div>
            <div><span class="font-medium text-purple-700">Output Tokens:</span> ...</div>
            <div><span class="font-medium text-purple-700">Total Tokens:</span> ...</div>
            <div><span class="font-medium text-purple-700">Cost:</span> ...</div>
        </div>
    </div>
` : ''}

// Assistant messages: Response Quality (green box) - Epic 0027
${!isUser && msg.meta && (msg.meta.confidence_score || msg.meta.reasoning_chain) ? `
    <div class="mt-3 p-3 bg-green-50 rounded border border-green-200">
        <p class="text-xs font-semibold text-green-800 mb-2">✨ Response Quality:</p>
        <div class="space-y-2 text-xs">
            ${msg.meta.confidence_score ? `
                <div><span class="font-medium text-green-700">Confidence:</span> 
                <span class="text-gray-700">${(msg.meta.confidence_score * 100).toFixed(1)}%</span></div>
            ` : ''}
            ${msg.meta.reasoning_chain ? `
                <div class="mt-2">
                    <span class="font-medium text-green-700">Reasoning Chain:</span>
                    <pre class="mt-1 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">...</pre>
                </div>
            ` : ''}
        </div>
    </div>
` : ''}

// Assistant messages: Tool Calls (yellow box) - always visible
${msg.meta?.tool_calls ? `
    <div class="mt-3 p-3 bg-yellow-50 rounded border border-yellow-200">
        <p class="text-xs font-semibold text-yellow-800 mb-2">🛠️ Tool Calls:</p>
        <pre class="text-xs text-gray-700 overflow-x-auto">${JSON.stringify(msg.meta.tool_calls, null, 2)}</pre>
    </div>
` : ''}
```

**Design Rationale**:
- **User cards focus on INPUT**: What prompt was sent to the LLM
- **Assistant cards focus on OUTPUT**: What the LLM returned and how it performed
- **Always-visible Tool Calls**: Critical for debugging tool selection (no click required)
- **Color-coded sections**: Purple (performance), Green (quality), Yellow (actions)

---

#### Task 3C-002: Add `assembled_prompt` Column to llm_requests Table

**Goal**: Store the complete assembled system prompt (after all concatenation) for debugging.

**Why**: The `meta.prompt_breakdown` stores structured metadata and content per section, but we also need the exact final text sent to the LLM for copy/paste testing and debugging.

**Database Migration**:

```sql
-- Migration: Add assembled_prompt column
ALTER TABLE llm_requests 
ADD COLUMN assembled_prompt TEXT;

CREATE INDEX idx_llm_requests_assembled_prompt_not_null 
ON llm_requests (id) WHERE assembled_prompt IS NOT NULL;
```

**Alembic Migration File**: `backend/migrations/versions/XXXX_add_assembled_prompt_to_llm_requests.py`

```python
"""Add assembled_prompt column to llm_requests

Revision ID: XXXX
Revises: YYYY
Create Date: 2025-11-14

"""
from alembic import op
import sqlalchemy as sa

revision = 'XXXX'
down_revision = 'YYYY'
branch_labels = None
depends_on = None

def upgrade():
    # Add assembled_prompt column
    op.add_column('llm_requests', sa.Column('assembled_prompt', sa.Text(), nullable=True))
    
    # Add partial index for performance (only index non-null values)
    op.create_index(
        'idx_llm_requests_assembled_prompt_not_null',
        'llm_requests',
        ['id'],
        postgresql_where=sa.text('assembled_prompt IS NOT NULL')
    )

def downgrade():
    op.drop_index('idx_llm_requests_assembled_prompt_not_null', table_name='llm_requests')
    op.drop_column('llm_requests', 'assembled_prompt')
```

**Model Update**: `backend/app/models/llm_request.py`

Add after line 100 (after `meta` column):

```python
# Full assembled system prompt (for debugging and copy/paste)
assembled_prompt = Column(Text, nullable=True, comment="Complete system prompt as sent to LLM (after all module concatenation)")
```

Update `to_dict()` method to include new field:

```python
def to_dict(self) -> dict:
    """Convert to dictionary for JSON serialization.""" 
    return {
        # ... existing fields ...
        "assembled_prompt": self.assembled_prompt,  # NEW
        "meta": self.meta,
        "created_at": self.created_at.isoformat() if self.created_at else None
    }
```

**Storage Estimate**:
- Average prompt size: 10-30 KB
- Impact: Moderate (similar to storing in JSONB sections, but deduplicated)
- Retention: Can be cleared for old requests (keep metadata)

---

#### Task 3C-003: Refactor `generate_directory_tool_docs()` to Return Structured Data

**Goal**: Return both the full markdown text (for prompt assembly) AND structured breakdown (for debugging).

**Files**: 
- `backend/app/agents/tools/prompt_generator.py` (refactor)
- `backend/config/prompt_modules/system/directory_selection_hints.md` (update)

**Architectural Decision**: Move hardcoded multi-directory orchestration guidance (lines 177-184 in prompt_generator.py) to `directory_selection_hints.md`. This maintains separation of concerns:
- `tool_selection_hints.md` = Cross-tool selection ("use directory vs vector vs web")
- `directory_selection_hints.md` = Within-tool orchestration ("which directory + how to combine")

**Changes to directory_selection_hints.md**:
1. Add "Multi-Directory Orchestration" section at the top
2. Keep existing pattern matching rules below
3. Source attribution in admin UI will show "directory_selection_hints.md"

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

1. Load multi-directory orchestration from `directory_selection_hints.md` (if multiple directories)
2. Build `header_content` string and `header_section` object combining loaded guidance + auto-generated directory summaries
3. For each directory, build both `dir_content` string and `DirectorySection` object
4. Concatenate all strings into `full_text`
5. Return `DirectoryDocsResult(full_text=..., header_section=..., directory_sections=[...])`

**Example construction**:

```python
# Inside generate_directory_tool_docs()
header_section = None
directory_sections = []
all_text_parts = []

if len(lists_metadata) > 1:
    # Load orchestration guidance from markdown file
    from ..utils.prompt_loader import load_prompt_module
    multi_dir_guidance = load_prompt_module("directory_selection_hints", account_slug="system")
    
    # Build header with guidance + directory summaries
    header_text = "## Directory Tool\n\n"
    if multi_dir_guidance:
        header_text += multi_dir_guidance + "\n\n"
    header_text += "You have access to multiple directories..."
    # ... add directory summaries from schema ...
    
    header_section = DirectorySection(
        name="directory_docs_header",
        content=header_text,
        character_count=len(header_text),
        metadata={
            "type": "multi_directory_header",
            "source": "directory_selection_hints.md + auto-generated summaries"
        }
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

#### Task 3C-004: Update `PromptBreakdownService` to Handle Structured Directories

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

#### Task 3C-005: Update `simple_chat.py` to Use New Structure and Capture Assembled Prompt

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

**Find the tracker.track_llm_request() call** (in streaming and non-streaming paths):

Look for calls to `track_llm_request()` that pass `meta={"prompt_breakdown": prompt_breakdown}`.

**Add `assembled_prompt` parameter**:

```python
# The complete assembled system prompt is in the variable `system_prompt`
# (after all concatenation: critical_rules + base_system_prompt + directory_docs + modules)

llm_request_id = await tracker.track_llm_request(
    # ... existing parameters ...
    meta={"prompt_breakdown": prompt_breakdown},
    assembled_prompt=system_prompt  # NEW: Pass the complete assembled prompt
)
```

**Note**: The variable `system_prompt` contains the final assembled text sent to the LLM. This is what we want to capture for the full prompt viewer.

---

#### Task 3C-006: Update `LLMRequestTracker` to Accept assembled_prompt Parameter

**File**: `backend/app/services/llm_request_tracker.py`

**Update `track_llm_request()` signature**:

```python
async def track_llm_request(
    self,
    # ... existing parameters ...
    meta: Optional[Dict[str, Any]] = None,
    assembled_prompt: Optional[str] = None  # NEW
) -> UUID:
    """
    Track LLM request with cost and usage data.
    
    Args:
        # ... existing args ...
        meta: Extensible metadata (e.g., prompt breakdown)
        assembled_prompt: Complete system prompt as sent to LLM (NEW)
        
    Returns:
        UUID of created LLM request
    """
```

**Update LLMRequest instantiation**:

```python
llm_request = LLMRequest(
    # ... existing fields ...
    meta=meta,
    assembled_prompt=assembled_prompt  # NEW
)
```

---

#### Task 3C-007: Add "View Full Assembled Prompt" UI Toggle

**File**: `web/public/admin/session.html`

**Update the user message breakdown buttons section** (in `renderMessages()`):

```javascript
${msg.role === 'user' && msg.llm_request_id ? `
    <div class="mt-3 flex gap-2">
        <!-- Existing: View Prompt Breakdown button -->
        <button class="px-3 py-1 bg-gray-200 text-gray-800 rounded-md text-sm hover:bg-gray-300"
                hx-get="/api/admin/llm-requests/${msg.llm_request_id}"
                hx-trigger="click"
                hx-target="#breakdown-${msg.llm_request_id}"
                hx-swap="none"
                hx-on::after-request="renderPromptBreakdown(event.detail.xhr.responseText, '${msg.llm_request_id}');">
            🔍 View Prompt Breakdown
        </button>
        
        <!-- NEW: View Full Assembled Prompt button -->
        <button class="px-3 py-1 bg-blue-200 text-blue-800 rounded-md text-sm hover:bg-blue-300"
                hx-get="/api/admin/llm-requests/${msg.llm_request_id}"
                hx-trigger="click"
                hx-target="#full-prompt-${msg.llm_request_id}"
                hx-swap="none"
                hx-on::after-request="renderFullPrompt(event.detail.xhr.responseText, '${msg.llm_request_id}');">
            📄 View Full Assembled Prompt
        </button>
        
        <!-- Container for prompt breakdown -->
        <div id="breakdown-${msg.llm_request_id}" class="hidden mt-3 p-3 bg-gray-50 rounded text-sm">
            <!-- Prompt breakdown will be loaded here -->
        </div>
        
        <!-- NEW: Container for full assembled prompt -->
        <div id="full-prompt-${msg.llm_request_id}" class="hidden mt-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
            <!-- Full assembled prompt will be loaded here -->
        </div>
    </div>
` : ''}
```

**Add new `renderFullPrompt()` function**:

```javascript
function renderFullPrompt(responseText, requestId) {
    const fullPromptDiv = document.getElementById(`full-prompt-${requestId}`);
    
    // Toggle visibility if already loaded
    if (!fullPromptDiv.classList.contains('hidden') && 
        fullPromptDiv.innerHTML.includes('Assembled Prompt')) {
        fullPromptDiv.classList.add('hidden');
        return;
    }

    const data = JSON.parse(responseText);
    const assembledPrompt = data.assembled_prompt;

    if (assembledPrompt && assembledPrompt.trim().length > 0) {
        const charCount = assembledPrompt.length;
        const lineCount = assembledPrompt.split('\n').length;
        
        let html = `
            <div class="flex items-center justify-between mb-3 pb-2 border-b border-blue-300">
                <h4 class="font-semibold text-blue-900 flex items-center gap-2">
                    <span>📄</span>
                    Full Assembled Prompt
                </h4>
                <div class="flex gap-3 text-xs text-blue-700">
                    <span class="bg-blue-100 px-2 py-1 rounded">${charCount.toLocaleString()} characters</span>
                    <span class="bg-blue-100 px-2 py-1 rounded">${lineCount.toLocaleString()} lines</span>
                    <button onclick="copyToClipboard('full-prompt-content-${requestId}')" 
                            class="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition">
                        📋 Copy
                    </button>
                </div>
            </div>
            <div class="bg-white border border-blue-200 rounded p-3 max-h-96 overflow-y-auto">
                <pre id="full-prompt-content-${requestId}" 
                     class="text-xs whitespace-pre-wrap font-mono text-gray-800 leading-relaxed">${escapeHtml(assembledPrompt)}</pre>
            </div>
            <p class="mt-2 text-xs text-blue-600 italic">
                💡 This is the exact system prompt sent to the LLM (before chat history)
            </p>
        `;
        
        fullPromptDiv.innerHTML = html;
    } else {
        fullPromptDiv.innerHTML = `
            <p class="text-gray-500 italic">
                ⚠️ Assembled prompt not available for this request (captured in future requests only)
            </p>
        `;
    }
    
    fullPromptDiv.classList.remove('hidden');
}

// Copy to clipboard utility
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const text = element.textContent;
        navigator.clipboard.writeText(text).then(() => {
            // Show temporary success message
            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.innerHTML = '✅ Copied!';
            btn.classList.add('bg-green-600');
            btn.classList.remove('bg-blue-600');
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.add('bg-blue-600');
                btn.classList.remove('bg-green-600');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
        });
    }
}
```

**Benefits**:
- Side-by-side comparison with breakdown (both buttons visible)
- Copy button for testing prompts in other tools
- Character and line count stats
- Clean, collapsible UI
- Works alongside existing breakdown viewer

---

#### Task 3C-008: Update Frontend to Render Nested Sections

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

## Phase 4: UI Polish & Layout Improvements

**Status**: PLANNED (Post Phase 3C)

**Goal**: Transform the functional HTMX admin UI into a polished, professional debugging tool with better visual hierarchy, improved readability, and modern design elements.

**Design Inspiration**: `memorybank/sample-screens/dribble-admin-business-analytics-app-prody.webp`

---

### Context: What Changed in Phase 3C

Phase 3C made architectural decisions that impact Phase 4:

| Aspect | Phase 3B | Phase 3C Impact | Phase 4 Consideration |
|--------|----------|-----------------|----------------------|
| **Architecture** | HTMX + Vanilla JS | Added nested prompt sections | Polish nested UI, improve indentation |
| **Files** | 2 HTML files | Same (sessions.html, session.html) | In-place polish, no new files |
| **Styling** | TailwindCSS CDN | Same | Pure utility classes, no build |
| **Components** | Vanilla JS functions | Same | Extract shared CSS snippets |
| **Prompt Breakdown** | Flat list | Nested hierarchy (directories) | Visual polish for nested items |

**Key Constraint**: No build step, no component frameworks - pure HTML + TailwindCSS + vanilla JS.

---

### Feature 0026-007: Professional Dashboard UI

#### Task 0026-007-001: Create Shared Admin Stylesheet

**Goal**: Centralize common styles and avoid TailwindCSS class repetition.

**File**: `web/public/admin/admin.css`

**Contents**:
```css
/* Admin UI Shared Styles */

/* Custom scrollbar for code sections */
.admin-code-block::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

.admin-code-block::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.admin-code-block::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}

.admin-code-block::-webkit-scrollbar-thumb:hover {
    background: #555;
}

/* Improved nested prompt sections */
.prompt-section-nested {
    margin-left: 1.5rem;
    border-left: 2px solid #e5e7eb;
    padding-left: 0.75rem;
    position: relative;
}

.prompt-section-nested::before {
    content: '';
    position: absolute;
    left: -2px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(to bottom, #3b82f6 0%, #e5e7eb 100%);
}

/* Loading state animation */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.admin-loading-skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite;
    border-radius: 4px;
}

/* Card shadow for depth */
.admin-card {
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    transition: box-shadow 0.2s ease;
}

.admin-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* Stats badge */
.admin-stat-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.875rem;
}

/* Improved button states */
.admin-button {
    transition: all 0.15s ease;
}

.admin-button:active {
    transform: scale(0.98);
}

/* Improved prompt section header */
.prompt-section-header {
    transition: all 0.15s ease;
    border-radius: 0.375rem;
}

.prompt-section-header:hover {
    background-color: #f3f4f6;
    transform: translateX(2px);
}

.prompt-section-header.expanded {
    background-color: #dbeafe;
    border-left: 3px solid #3b82f6;
}
```

**Add to both HTML files**:
```html
<link rel="stylesheet" href="/admin/admin.css">
```

---

#### Task 0026-007-002: Add Navigation Header with Branding

**Goal**: Add a consistent header with branding, breadcrumbs, and quick stats.

**Apply to**: Both `sessions.html` and `session.html`

**Add before existing header**:
```html
<!-- Global Admin Header -->
<div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
            <!-- Branding -->
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                    <span class="text-2xl">🔍</span>
                </div>
                <div>
                    <h1 class="text-xl font-bold">OpenThought Admin</h1>
                    <p class="text-xs text-blue-100">LLM Debug Console</p>
                </div>
            </div>
            
            <!-- Breadcrumbs (dynamic per page) -->
            <nav class="flex items-center gap-2 text-sm">
                <a href="/admin/sessions.html" class="text-blue-100 hover:text-white transition">
                    Sessions
                </a>
                <!-- Add more breadcrumb items in session.html -->
            </nav>
            
            <!-- Quick Stats (optional, from API) -->
            <div class="hidden md:flex items-center gap-4 text-sm">
                <div class="admin-stat-badge">
                    <span>📊</span>
                    <span id="total-sessions-stat">-</span> Sessions
                </div>
            </div>
        </div>
    </div>
</div>
```

---

#### Task 0026-007-003: Polish Sessions List Page

**File**: `web/public/admin/sessions.html`

**Changes**:

1. **Add Summary Stats Cards** (above filters):
```html
<!-- Summary Stats -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
    <div class="admin-card bg-white rounded-lg p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm text-gray-500 font-medium">Total Sessions</p>
                <p id="stat-total" class="text-3xl font-bold text-gray-900 mt-2">-</p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <span class="text-2xl">💬</span>
            </div>
        </div>
    </div>
    
    <div class="admin-card bg-white rounded-lg p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm text-gray-500 font-medium">Active Today</p>
                <p id="stat-today" class="text-3xl font-bold text-gray-900 mt-2">-</p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <span class="text-2xl">✨</span>
            </div>
        </div>
    </div>
    
    <div class="admin-card bg-white rounded-lg p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm text-gray-500 font-medium">Avg Messages</p>
                <p id="stat-avg-msgs" class="text-3xl font-bold text-gray-900 mt-2">-</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <span class="text-2xl">📈</span>
            </div>
        </div>
    </div>
</div>
```

2. **Improve Filter Section** (better visual hierarchy):
```html
<!-- Filters -->
<div class="admin-card bg-white rounded-lg mb-6 p-6">
    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <span>🔎</span>
        Filter Sessions
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Account
            </label>
            <select id="account-filter" 
                    class="w-full border border-gray-300 rounded-lg px-4 py-2.5 
                           focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           transition admin-button"
                    onchange="updateAgentDropdown(); fetchSessions();">
                <!-- Options populated by JS -->
            </select>
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Agent Instance
            </label>
            <select id="agent-filter" 
                    class="w-full border border-gray-300 rounded-lg px-4 py-2.5
                           focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           transition admin-button"
                    onchange="fetchSessions();">
                <!-- Options populated by JS -->
            </select>
        </div>
        <div class="flex items-end">
            <button onclick="fetchSessions()" 
                    class="w-full px-6 py-2.5 bg-blue-600 text-white rounded-lg 
                           hover:bg-blue-700 font-medium admin-button
                           flex items-center justify-center gap-2">
                <span>🔄</span>
                Refresh
            </button>
        </div>
    </div>
</div>
```

3. **Improve Table Styling**:
```html
<!-- In renderSessions() function -->
<div class="admin-card bg-white rounded-lg overflow-hidden">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gradient-to-r from-gray-50 to-gray-100">
            <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Session ID
                </th>
                <!-- More headers with icons -->
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    <span class="flex items-center gap-1">
                        <span>👤</span> Account
                    </span>
                </th>
                <!-- ... -->
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-100">
            <!-- Rows with improved hover state -->
            <tr class="hover:bg-blue-50 transition-colors duration-150">
                <!-- Cells with better typography -->
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="font-mono text-sm text-gray-900 bg-gray-100 px-2 py-1 rounded">
                        ${session.id.substring(0, 13)}...
                    </span>
                </td>
                <!-- More cells with badges, icons -->
            </tr>
        </tbody>
    </table>
</div>
```

---

#### Task 0026-007-004: Polish Session Detail Page

**File**: `web/public/admin/session.html`

**Changes**:

1. **Add Session Metadata Card** (after header):
```html
<!-- Session Metadata -->
<div class="admin-card bg-white rounded-lg p-6 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div>
            <p class="text-xs text-gray-500 font-medium uppercase tracking-wide">Session ID</p>
            <p class="mt-1 font-mono text-sm text-gray-900 bg-gray-100 px-2 py-1 rounded inline-block">
                <span id="session-id-display"></span>
            </p>
        </div>
        <div>
            <p class="text-xs text-gray-500 font-medium uppercase tracking-wide">Account</p>
            <p id="session-account" class="mt-1 text-sm font-semibold text-gray-900">-</p>
        </div>
        <div>
            <p class="text-xs text-gray-500 font-medium uppercase tracking-wide">Agent</p>
            <p id="session-agent" class="mt-1 text-sm font-semibold text-gray-900">-</p>
        </div>
        <div>
            <p class="text-xs text-gray-500 font-medium uppercase tracking-wide">Messages</p>
            <p id="session-msg-count" class="mt-1 text-2xl font-bold text-blue-600">-</p>
        </div>
    </div>
</div>
```

2. **Improve Message Cards** (in `renderMessages()`):
```javascript
// User message styling
const userBg = 'bg-gradient-to-r from-blue-50 to-indigo-50';
const userBorder = 'border-l-4 border-blue-500';
const userIcon = '👤';
const userLabel = 'User';

// Assistant message styling
const assistantBg = 'bg-gradient-to-r from-purple-50 to-pink-50';
const assistantBorder = 'border-l-4 border-purple-500';
const assistantIcon = '🤖';
const assistantLabel = 'Assistant';

const messageCard = `
    <div class="admin-card mb-4 rounded-lg ${isUser ? userBg : assistantBg} ${isUser ? userBorder : assistantBorder} overflow-hidden">
        <!-- Message header -->
        <div class="px-6 py-3 bg-white bg-opacity-50 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span class="text-lg">${isUser ? userIcon : assistantIcon}</span>
                <span class="font-semibold text-sm ${isUser ? 'text-blue-700' : 'text-purple-700'}">
                    ${isUser ? userLabel : assistantLabel}
                </span>
            </div>
            <span class="text-xs text-gray-500">
                ${new Date(msg.timestamp).toLocaleString()}
            </span>
        </div>
        
        <!-- Message content -->
        <div class="px-6 py-4">
            <p class="text-gray-900 whitespace-pre-wrap leading-relaxed">${msg.content}</p>
        </div>
        
        <!-- Rest of message (tool calls, prompt breakdown) -->
    </div>
`;
```

3. **Polish Prompt Breakdown Section** (from Phase 3C):

Update `renderPromptBreakdown()` to use new CSS classes:

```javascript
function renderPromptBreakdown(responseText, requestId) {
    // ... existing code ...
    
    breakdown.sections.forEach((section, index) => {
        const sectionId = `section-${requestId}-${index}`;
        const hasContent = section.content && section.content.trim().length > 0;
        const isNested = section.parent_position !== undefined;
        
        // Use new CSS class for nested sections
        const indentClass = isNested ? 'prompt-section-nested' : '';
        
        html += `
            <div class="mb-2 ${indentClass}">
                <!-- Clickable Header with improved states -->
                <button 
                    class="prompt-section-header w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 
                           font-medium flex justify-between items-center admin-button"
                    onclick="toggleSection('${sectionId}', this)"
                    ${!hasContent ? 'disabled opacity-50 cursor-not-allowed' : ''}>
                    <span class="flex items-center gap-3">
                        <span class="arrow text-blue-600 font-bold text-lg">▶</span> 
                        <span class="font-mono text-sm">${section.name}</span>
                    </span>
                    <span class="text-xs text-gray-600 bg-white px-2 py-1 rounded">
                        <span class="font-semibold">${section.position}</span> · 
                        ${section.characters.toLocaleString()} chars
                    </span>
                </button>
                
                <!-- Content box with improved styling -->
                ${hasContent ? `
                    <div id="${sectionId}" class="hidden mt-2">
                        <!-- Metadata bar with icons -->
                        <div class="px-4 py-2 text-xs bg-gradient-to-r from-gray-100 to-gray-50 
                                    rounded-t-lg border border-gray-200 flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span>📄</span>
                                <span class="font-medium">Source:</span>
                                <span class="text-gray-700">${section.source || 'N/A'}</span>
                            </div>
                            ${section.metadata && section.metadata.entry_count ? `
                                <div class="flex items-center gap-2 bg-white px-2 py-1 rounded">
                                    <span>📊</span>
                                    <span class="font-semibold text-blue-600">
                                        ${section.metadata.entry_count} ${section.metadata.entry_type}s
                                    </span>
                                </div>
                            ` : ''}
                        </div>
                        <!-- Content with improved styling -->
                        <div class="px-4 py-3 bg-white border-x border-b border-gray-200 rounded-b-lg">
                            <pre class="admin-code-block text-xs whitespace-pre-wrap font-mono text-gray-800 
                                       border-l-4 border-blue-400 pl-4 pr-2 py-2 bg-gray-50 rounded
                                       max-h-96 overflow-y-auto">${escapeHtml(section.content)}</pre>
                        </div>
                    </div>
                ` : `
                    <div class="px-4 py-3 text-xs text-gray-500 italic bg-gray-50 rounded-b-lg">
                        ⚠️ Content not captured for this section
                    </div>
                `}
            </div>
        `;
    });
    
    // ... rest of function ...
}

// Update toggleSection to add visual feedback
function toggleSection(sectionId, buttonEl) {
    const contentDiv = document.getElementById(sectionId);
    const arrow = buttonEl.querySelector('.arrow');
    
    if (contentDiv.classList.contains('hidden')) {
        contentDiv.classList.remove('hidden');
        arrow.textContent = '▼';
        buttonEl.classList.add('expanded');
    } else {
        contentDiv.classList.add('hidden');
        arrow.textContent = '▶';
        buttonEl.classList.remove('expanded');
    }
}
```

---

#### Task 0026-007-005: Add Loading States and Empty States

**Goal**: Improve UX during data loading and when no data exists.

**For both HTML files, update loading indicators**:

```html
<!-- Better loading state -->
<div class="admin-card bg-white rounded-lg p-8">
    <div class="flex flex-col items-center justify-center">
        <div class="relative w-16 h-16 mb-4">
            <div class="absolute inset-0 border-4 border-blue-200 rounded-full"></div>
            <div class="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
        </div>
        <p class="text-gray-600 font-medium">Loading sessions...</p>
        <p class="text-sm text-gray-400 mt-1">Fetching data from backend</p>
    </div>
</div>

<!-- Better empty state -->
<div class="admin-card bg-white rounded-lg p-12">
    <div class="flex flex-col items-center justify-center text-center">
        <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <span class="text-4xl">🔍</span>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 mb-2">No sessions found</h3>
        <p class="text-sm text-gray-500 max-w-sm">
            Try adjusting your filters or create a new chat session to get started.
        </p>
    </div>
</div>
```

---

#### Task 0026-007-006: Add Keyboard Shortcuts

**Goal**: Power user features for navigation and actions.

**Add to both HTML files** (before closing `</body>`):

```html
<script>
    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K: Focus search/filter
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const accountFilter = document.getElementById('account-filter');
            if (accountFilter) accountFilter.focus();
        }
        
        // Ctrl/Cmd + R: Refresh data
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            if (typeof fetchSessions === 'function') {
                fetchSessions();
            }
        }
        
        // Escape: Close expanded sections
        if (e.key === 'Escape') {
            document.querySelectorAll('[id^="breakdown-"]:not(.hidden)').forEach(el => {
                el.classList.add('hidden');
            });
        }
    });
</script>

<!-- Keyboard shortcuts help (show on ?) -->
<div id="shortcuts-help" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 
                                  flex items-center justify-center p-4"
     onclick="this.classList.add('hidden')">
    <div class="admin-card bg-white rounded-lg p-6 max-w-md" onclick="event.stopPropagation()">
        <h3 class="text-lg font-semibold mb-4">Keyboard Shortcuts</h3>
        <div class="space-y-2 text-sm">
            <div class="flex justify-between">
                <span class="text-gray-600">Focus Filters</span>
                <kbd class="px-2 py-1 bg-gray-100 rounded text-xs font-mono">⌘K</kbd>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Refresh</span>
                <kbd class="px-2 py-1 bg-gray-100 rounded text-xs font-mono">⌘R</kbd>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Close Sections</span>
                <kbd class="px-2 py-1 bg-gray-100 rounded text-xs font-mono">ESC</kbd>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Show Shortcuts</span>
                <kbd class="px-2 py-1 bg-gray-100 rounded text-xs font-mono">?</kbd>
            </div>
        </div>
    </div>
</div>

<script>
    document.addEventListener('keydown', (e) => {
        if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            document.getElementById('shortcuts-help').classList.toggle('hidden');
        }
    });
</script>
```

---

### Testing Plan

#### Visual Regression Testing

**Test 1: Sessions List Page**
1. Visit `http://localhost:4321/admin/sessions.html`
2. Verify:
   - ✅ Global header with branding
   - ✅ Stats cards with icons and numbers
   - ✅ Filter section with improved styling
   - ✅ Table with hover states and badges
   - ✅ Loading states show spinner
   - ✅ Empty states show friendly message

**Test 2: Session Detail Page**
1. Click any session
2. Verify:
   - ✅ Global header with breadcrumbs
   - ✅ Session metadata card
   - ✅ Message cards with gradient backgrounds
   - ✅ User/Assistant visual distinction clear
   - ✅ Prompt breakdown sections styled correctly
   - ✅ Nested directory sections have border and indentation
   - ✅ Expanded sections have blue highlight

**Test 3: Prompt Breakdown (Phase 3C Integration)**
1. Click "View Prompt Breakdown" on user message
2. Verify:
   - ✅ Sections have position numbers and char counts
   - ✅ Nested directories are visually indented
   - ✅ Click section → expands with blue border
   - ✅ Metadata bar shows entry counts with icons
   - ✅ Code block has custom scrollbar
   - ✅ Click again → collapses smoothly

**Test 4: Responsive Design**
1. Resize browser to mobile width
2. Verify:
   - ✅ Tables remain scrollable
   - ✅ Filter grid stacks vertically
   - ✅ Stats cards stack on mobile
   - ✅ Message cards remain readable

**Test 5: Keyboard Shortcuts**
1. Press `⌘K` → account filter focuses
2. Press `⌘R` → data refreshes
3. Press `ESC` → expanded sections close
4. Press `?` → shortcuts help appears

---

### File Changes Summary

**Files Modified**:
1. `web/public/admin/admin.css` (NEW) - Shared stylesheet
2. `web/public/admin/sessions.html` - Add header, stats cards, polished filters, improved table
3. `web/public/admin/session.html` - Add header, metadata card, polished messages, improved prompt breakdown
4. Both HTML files - Add keyboard shortcuts, help modal

**Total Changes**: 3 files (1 new, 2 modified)

**Lines Added**: ~600 lines (CSS + HTML improvements)

**No Backend Changes**: This is pure frontend polish

---

### Design Principles Applied

1. **Visual Hierarchy**: Headers, cards, shadows create depth
2. **Consistent Spacing**: Tailwind's spacing scale (4, 6, 8, 12, 16)
3. **Color Palette**: Blue (primary), Purple (assistant), Gray (neutral)
4. **Typography**: Font weights (normal, medium, semibold, bold) for hierarchy
5. **Icons**: Emojis for quick visual cues (🔍, 👤, 🤖, 📊)
6. **States**: Hover, active, focus, disabled - all styled
7. **Animations**: Smooth transitions (150-200ms)
8. **Accessibility**: Focus rings, keyboard nav, ARIA labels

---

### Future Enhancements (Post-Phase 4)

**Phase 5 (Optional)**:
- **Dark Mode**: Toggle between light/dark themes (pure CSS variables)
- **Export**: Download session as JSON or markdown
- **Search**: Full-text search across sessions
- **Filters**: Date range picker, message count range
- **Sorting**: Click column headers to sort
- **Pagination**: Next/Previous buttons for large datasets
- **Real-time**: Auto-refresh with HTMX polling
- **Syntax Highlighting**: Use Prism.js for code in prompts

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
