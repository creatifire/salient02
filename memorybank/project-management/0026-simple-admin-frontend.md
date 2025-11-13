# Epic 0026 - Simple Admin Frontend for Chat Tracing

**Status**: Draft  
**Created**: 2025-11-12  
**Epic Owner**: Development Team  
**Priority**: Medium  
**Category**: Developer Tools / Debugging

---

## Purpose

Provide a simple, lightweight admin interface for developers to:
- Browse chat sessions by account/agent
- View conversation history (user ↔ agent messages)
- Inspect LLM prompts and tool calls for debugging
- Trace tool selection decisions (why `vector_search` vs `search_directory`)
- Monitor prompt module loading and positioning

**Primary Use Case**: Debug why LLM is choosing wrong tools (e.g., `vector_search` instead of `search_directory` for phone queries)

---

## Design Principles

- **Simple**: HTMX-based, server-rendered, minimal JavaScript
- **Fast**: No complex SPA framework, just fetch and render
- **Pragmatic**: Read-only views, no editing/admin controls
- **Developer-focused**: Raw data display, JSON inspection, copy-paste friendly

---

## Technology Stack

- **Frontend**: Astro (already in use at `/web`)
- **Interactivity**: Preact (lightweight React alternative, already installed)
- **Backend**: FastAPI (existing backend at `/backend/app`)
- **Styling**: TailwindCSS (already installed at 4.1.12)

---

## Pages & Routes

### 1. Session List Page
**Route**: `/admin/sessions`

**Purpose**: Browse all chat sessions

**Display**:
- Table with columns:
  - Session ID (UUID, truncated)
  - Account (wyckoff, etc.)
  - Agent (wyckoff_info_chat1, etc.)
  - Created At
  - Last Activity
  - Message Count
  - Actions: [View Details]

**Filters** (HTMX-powered):
- Account dropdown
- Agent dropdown
- Date range picker
- Anonymous vs. logged-in sessions

**Backend Endpoint**:
```
GET /api/admin/sessions?account={slug}&agent={slug}&limit=50&offset=0
```

---

### 2. Session Detail Page
**Route**: `/admin/sessions/{session_id}`

**Purpose**: View full conversation with prompt inspection

**Display**:
- **Session Metadata** (top card):
  - Session ID, Account, Agent, User ID/Email, Created/Last Activity
  
- **Conversation Timeline** (scrollable):
  - Each message pair (user → assistant) in chronological order
  - User message: Blue bubble, left-aligned
  - Assistant message: Gray bubble, right-aligned
  - Expandable "Show Details" for each assistant message:
    - **LLM Request ID** (clickable → jump to prompt details)
    - **Model Used** (e.g., `google/gemini-2.5-flash`)
    - **Tokens**: Input/Output/Total
    - **Cost**: $X.XXXX
    - **Duration**: XXXms
    - **Tool Calls**: List of tools invoked (if any)

- **Prompt Inspector** (right sidebar, toggleable):
  - When "Show Details" clicked, displays:
    - Full system prompt (with line numbers, syntax highlighting)
    - Critical rules section (highlighted in yellow)
    - Directory docs section (highlighted in blue)
    - Module sections (highlighted in green)
    - Tool descriptions (highlighted in purple)
    - User message history
    - Copy button for full prompt

**Backend Endpoints**:
```
GET /api/admin/sessions/{session_id}/messages
GET /api/admin/llm-requests/{request_id}/prompt
```

---

### 3. LLM Request Detail Page (Optional Deep Dive)
**Route**: `/admin/llm-requests/{request_id}`

**Purpose**: Deep dive into a single LLM request

**Display**:
- **Request Metadata**:
  - Request ID, Session ID, Account, Agent, Model, Timestamp
  
- **Prompt Breakdown** (accordion sections):
  - 1️⃣ Critical Tool Selection Rules (char count, position)
  - 2️⃣ Base System Prompt (char count, position)
  - 3️⃣ Directory Tool Documentation (char count, position)
  - 4️⃣ Pydantic AI Tool Descriptions (char count, position)
  - 5️⃣ Other Modules (char count, position)
  - Full Prompt (collapsible, raw text, line numbers)
  
- **Tool Calls Made**:
  - List of tool invocations with parameters
  - Tool outputs (truncated, expandable)
  
- **Response**:
  - Assistant's final response
  - Tokens, cost, duration

**Backend Endpoint**:
```
GET /api/admin/llm-requests/{request_id}
```

---

## Data Schema (Backend API)

### Sessions List Response
```json
{
  "sessions": [
    {
      "id": "uuid",
      "account_slug": "wyckoff",
      "agent_instance_slug": "wyckoff_info_chat1",
      "user_email": "user@example.com",
      "is_anonymous": false,
      "created_at": "2025-11-12T20:46:10Z",
      "last_activity_at": "2025-11-12T20:47:55Z",
      "message_count": 4
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### Session Messages Response
```json
{
  "session_id": "uuid",
  "account": "wyckoff",
  "agent": "wyckoff_info_chat1",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "what is the number of the pharmacy",
      "created_at": "2025-11-12T20:47:49Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "I don't have the specific phone number...",
      "created_at": "2025-11-12T20:47:55Z",
      "llm_request_id": "uuid",
      "meta": {
        "model": "google/gemini-2.5-flash",
        "input_tokens": 15410,
        "output_tokens": 69,
        "cost": 0.04623,
        "duration_ms": 6724,
        "tool_calls": [
          {
            "tool_name": "vector_search",
            "args": {"query": "phone number of the pharmacy"}
          }
        ]
      }
    }
  ]
}
```

### LLM Request Detail Response
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "account_slug": "wyckoff",
  "agent_instance_slug": "wyckoff_info_chat1",
  "model": "google/gemini-2.5-flash",
  "created_at": "2025-11-12T20:47:49Z",
  "prompt_breakdown": {
    "critical_rules": {
      "content": "## CRITICAL: Tool Selection Rules\n...",
      "char_count": 4928,
      "position": 1,
      "source": "tool_selection_hints.md"
    },
    "base_prompt": {
      "content": "You are Wyckoff Hospital Assistant...",
      "char_count": 3200,
      "position": 2,
      "source": "system_prompt.md"
    },
    "directory_docs": {
      "content": "## Directory Tool\n...",
      "char_count": 6100,
      "position": 3,
      "source": "auto-generated"
    },
    "tool_descriptions": {
      "content": "search_directory(list_name: str, ...)\n...",
      "char_count": 1200,
      "position": 4,
      "source": "pydantic-ai"
    },
    "other_modules": [
      {
        "name": "directory_selection_hints",
        "content": "## Directory Selection Hints\n...",
        "char_count": 1153,
        "position": 5
      }
    ],
    "full_prompt": "## CRITICAL: Tool Selection Rules\n...(entire 15,410 char prompt)..."
  },
  "tool_calls": [
    {
      "tool_name": "vector_search",
      "args": {"query": "phone number of the pharmacy", "threshold": 0.4},
      "output": "[{\"score\": 0.82, \"text\": \"...\"}]"
    }
  ],
  "response": {
    "content": "I don't have the specific phone number...",
    "input_tokens": 15410,
    "output_tokens": 69,
    "total_tokens": 15479,
    "cost": 0.04623,
    "duration_ms": 6724
  }
}
```

---

## Implementation Plan

### Phase 0: Foundation Setup (Pre-Work)
**Goal**: Prepare data capture and authentication infrastructure before building admin UI

**Status**: Required before Phase 1

---

#### Feature 0026-000: Foundation Prerequisites

##### Task 0026-000-001: Add meta Column to llm_requests Table
**Purpose**: Store prompt breakdown metadata for admin inspection

**Implementation**:
```sql
ALTER TABLE llm_requests 
ADD COLUMN meta JSONB;

COMMENT ON COLUMN llm_requests.meta IS 'Extensible metadata including prompt breakdown for debugging';
```

**Manual Tests**:
- ✅ Column exists and accepts JSONB data
- ✅ Existing rows have NULL meta (nullable field)
- ✅ Can insert/update meta field with JSON

**Effort**: 5 minutes

---

##### Task 0026-000-002: Create Prompt Breakdown Service
**Purpose**: Centralized service for capturing prompt composition metadata (reusable across all agents)

**File**: `backend/app/services/prompt_breakdown_service.py`

**Implementation**:
```python
from typing import Dict, List, Optional
import logfire

class PromptBreakdownService:
    """
    Centralized service for capturing prompt breakdown metadata.
    Used by all agents to track prompt composition for admin debugging.
    """
    
    @staticmethod
    def capture_breakdown(
        base_prompt: str,
        critical_rules: Optional[str] = None,
        directory_docs: Optional[str] = None,
        modules: Optional[Dict[str, str]] = None,
        account_slug: Optional[str] = None,
        agent_instance_slug: Optional[str] = None
    ) -> dict:
        """
        Capture prompt breakdown with character counts and sources.
        
        Args:
            base_prompt: Base system prompt content
            critical_rules: Critical tool selection rules (injected at top)
            directory_docs: Auto-generated directory documentation
            modules: Dict of {module_name: content} for additional modules
            account_slug: Account identifier for logging
            agent_instance_slug: Agent instance identifier for logging
            
        Returns:
            Dict suitable for storing in llm_requests.meta['prompt_breakdown']
        """
        breakdown = {
            "sections": []
        }
        
        position = 1
        total_chars = 0
        
        # 1. Critical rules (if present, injected at top)
        if critical_rules:
            breakdown["sections"].append({
                "name": "critical_rules",
                "position": position,
                "char_count": len(critical_rules),
                "source": "tool_selection_hints.md"
            })
            total_chars += len(critical_rules)
            position += 1
        
        # 2. Base system prompt
        breakdown["sections"].append({
            "name": "base_prompt",
            "position": position,
            "char_count": len(base_prompt),
            "source": "system_prompt.md"
        })
        total_chars += len(base_prompt)
        position += 1
        
        # 3. Directory documentation (if present)
        if directory_docs:
            breakdown["sections"].append({
                "name": "directory_docs",
                "position": position,
                "char_count": len(directory_docs),
                "source": "auto-generated"
            })
            total_chars += len(directory_docs)
            position += 1
        
        # 4. Additional modules
        if modules:
            module_sections = []
            for module_name, content in modules.items():
                module_sections.append({
                    "name": module_name,
                    "position": position,
                    "char_count": len(content),
                    "source": f"{module_name}.md"
                })
                total_chars += len(content)
                position += 1
            
            if module_sections:
                breakdown["sections"].append({
                    "name": "other_modules",
                    "modules": module_sections
                })
        
        # Add summary
        breakdown["total_char_count"] = total_chars
        breakdown["section_count"] = len(breakdown["sections"])
        
        # Log breakdown for monitoring
        logfire.info(
            'service.prompt_breakdown.captured',
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug,
            total_chars=total_chars,
            section_count=breakdown["section_count"]
        )
        
        return breakdown
```

**Manual Tests**:
- ✅ Service captures breakdown from simple_chat.py
- ✅ Returns valid JSON structure
- ✅ Handles optional fields (critical_rules, directory_docs)
- ✅ Logfire event logged with correct data

**Effort**: 30 minutes

---

##### Task 0026-000-003: Integrate Breakdown Service into simple_chat.py
**Purpose**: Capture prompt breakdown during agent creation and store in llm_requests.meta

**Changes to**: `backend/app/agents/simple_chat.py`

**Implementation**:
```python
# At top of file, add import
from ..services.prompt_breakdown_service import PromptBreakdownService

# In create_simple_chat_agent(), after system_prompt construction:
async def create_simple_chat_agent(...):
    # ... existing code to build system_prompt ...
    
    # Capture prompt breakdown for admin debugging
    breakdown = PromptBreakdownService.capture_breakdown(
        base_prompt=base_system_prompt,
        critical_rules=critical_rules if critical_rules else None,
        directory_docs=directory_docs if directory_config.get("enabled") else None,
        modules={
            name: load_prompt_module(name, account_slug)
            for name in prompting_config.get('selected', [])
        } if prompting_config.get('enabled') else None,
        account_slug=account_slug,
        agent_instance_slug=instance_config.get('slug') if instance_config else None
    )
    
    # Store breakdown for later use when tracking LLM requests
    # (We'll pass this to track_llm_request via a new parameter)
    
    # ... rest of agent creation ...
```

**Changes to**: `backend/app/agents/cost_calculator.py` (track_chat_request function)

Add `prompt_breakdown` parameter and store in meta:
```python
async def track_chat_request(
    tracker: Any,
    # ... existing params ...
    prompt_breakdown: Optional[dict] = None  # NEW
) -> Optional[UUID]:
    """Track LLM request with prompt breakdown metadata."""
    
    # Build request body
    request_body = {
        "messages": request_messages,
        # ...
    }
    
    # Track the request with breakdown metadata
    llm_request_id = await tracker.track_llm_request(
        # ... existing params ...
        meta={"prompt_breakdown": prompt_breakdown} if prompt_breakdown else None  # NEW
    )
```

**Changes to**: `backend/app/services/llm_request_tracker.py`

Add `meta` parameter:
```python
async def track_llm_request(
    self,
    # ... existing params ...
    meta: Optional[Dict[str, Any]] = None  # NEW
) -> UUID:
    """Track LLM request with optional metadata."""
    
    llm_request = LLMRequest(
        # ... existing fields ...
        meta=meta  # NEW
    )
```

**Manual Tests**:
- ✅ Breakdown captured for every simple_chat request
- ✅ Stored in llm_requests.meta['prompt_breakdown']
- ✅ Query database to verify JSON structure is correct
- ✅ Logfire shows breakdown capture events

**Effort**: 45 minutes

---

##### Task 0026-000-004: Verify Tool Call Storage in message.meta
**Purpose**: Ensure tool calls are being stored for admin inspection

**Investigation**:
1. Check if `simple_chat.py` currently populates `message.meta` with tool calls
2. Verify format matches expected structure: `{"tool_calls": [{"tool_name": "...", "args": {...}, "output": "..."}]}`

**If Missing, Implement**:
```python
# In simple_chat() after agent.run() and tool calls complete:
tool_calls_meta = []
if result.all_messages():
    for msg in result.all_messages():
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    tool_calls_meta.append({
                        "tool_name": part.tool_name,
                        "args": part.args,
                        # Store output separately if available
                    })

# Include in message.meta when saving assistant response
await message_service.save_message(
    # ...
    meta={"tool_calls": tool_calls_meta} if tool_calls_meta else None
)
```

**Manual Tests**:
- ✅ Tool calls appear in message.meta for directory queries
- ✅ Tool calls appear for vector_search queries
- ✅ Format is consistent and parseable

**Effort**: 30 minutes (if implementation needed)

---

##### Task 0026-000-005: Implement Admin Authentication Middleware
**Purpose**: Secure `/api/admin/*` routes with HTTP Basic Auth

**File**: `backend/app/middleware/admin_auth_middleware.py`

**Implementation**:
```python
"""
Admin authentication middleware for securing admin API endpoints.
Uses HTTP Basic Auth with credentials from environment variables.
"""
import os
import secrets
from typing import Callable

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import logfire

security = HTTPBasic()

class AdminAuthMiddleware(BaseHTTPMiddleware):
    """
    HTTP Basic Auth middleware for admin routes.
    
    Protects all /api/admin/* endpoints with username/password.
    Credentials configured via environment variables:
    - ADMIN_USERNAME (default: "admin")
    - ADMIN_PASSWORD (default: "changeme" - MUST be changed in production)
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        if self.admin_password == "changeme":
            logfire.warn(
                'security.admin_auth.default_password',
                message="Admin password is set to default 'changeme'. Change ADMIN_PASSWORD env var."
            )
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Only protect /api/admin/* routes
        if not request.url.path.startswith("/api/admin/"):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return self._unauthorized_response()
        
        # Decode and verify credentials
        try:
            import base64
            credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = credentials.split(":", 1)
            
            # Constant-time comparison to prevent timing attacks
            username_correct = secrets.compare_digest(username, self.admin_username)
            password_correct = secrets.compare_digest(password, self.admin_password)
            
            if not (username_correct and password_correct):
                logfire.warn(
                    'security.admin_auth.failed',
                    username=username,
                    path=request.url.path
                )
                return self._unauthorized_response()
            
            # Log successful admin access
            logfire.info(
                'security.admin_auth.success',
                username=username,
                path=request.url.path,
                ip=request.client.host if request.client else None
            )
            
        except Exception as e:
            logfire.error(
                'security.admin_auth.error',
                error=str(e),
                path=request.url.path
            )
            return self._unauthorized_response()
        
        return await call_next(request)
    
    def _unauthorized_response(self):
        """Return 401 with WWW-Authenticate header to trigger browser login prompt."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Admin authentication required"},
            headers={"WWW-Authenticate": "Basic realm=\"Admin Area\""}
        )
```

**Register in**: `backend/app/main.py`

```python
# Add after SimpleSessionMiddleware registration
from .middleware.admin_auth_middleware import AdminAuthMiddleware

app.add_middleware(AdminAuthMiddleware)
```

**Environment Variables** (add to `.env`):
```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here
```

**Manual Tests**:
- ✅ `/api/admin/sessions` returns 401 without auth
- ✅ Browser shows Basic Auth login prompt
- ✅ Correct credentials grant access
- ✅ Incorrect credentials denied
- ✅ Non-admin routes (e.g., `/api/config`) still work without auth
- ✅ Logfire shows auth attempts (success/failure)

**Effort**: 30 minutes

---

### Phase 0: Summary

**Total Effort**: ~2.5 hours

**Completion Criteria**:
- ✅ `llm_requests.meta` column exists
- ✅ `PromptBreakdownService` created and tested
- ✅ Prompt breakdown captured for every LLM request
- ✅ Tool calls stored in `message.meta`
- ✅ Admin routes secured with HTTP Basic Auth

**Once Phase 0 is complete**, all data needed for the admin UI will be captured and secured.

---

### Phase 1: Backend API Endpoints (Foundation)
**Goal**: Create read-only API endpoints for admin data

#### Feature 0026-001: Sessions List API
**Endpoint**: `GET /api/admin/sessions`

**Tasks**:
- **0026-001-001**: Create `/backend/app/api/admin.py` with `list_sessions()` endpoint
  - Query `sessions` table with filters (account, agent, date range)
  - Join with `messages` table for message count
  - Paginate results (limit/offset)
  - Return JSON response matching schema
  
- **0026-001-002**: Add query params: `account`, `agent`, `start_date`, `end_date`, `limit`, `offset`
  
- **0026-001-003**: Test with curl/Postman
  ```bash
  curl http://localhost:8000/api/admin/sessions?account=wyckoff&limit=10
  ```

**Manual Tests**:
- ✅ Returns sessions for Wyckoff account
- ✅ Pagination works (limit/offset)
- ✅ Filters by account/agent work
- ✅ Message count is accurate

**Effort**: 1 hour

---

#### Feature 0026-002: Session Messages API
**Endpoint**: `GET /api/admin/sessions/{session_id}/messages`

**Tasks**:
- **0026-002-001**: Create `get_session_messages()` endpoint in `admin.py`
  - Query `messages` table for session_id
  - Join with `llm_requests` table for LLM metadata
  - Include tool calls from `meta` field
  - Return chronological message list
  
- **0026-002-002**: Test with sample session ID from database
  ```bash
  curl http://localhost:8000/api/admin/sessions/{uuid}/messages
  ```

**Manual Tests**:
- ✅ Returns all messages for session
- ✅ LLM metadata included (tokens, cost, duration)
- ✅ Tool calls parsed correctly from meta field
- ✅ Messages in chronological order

**Effort**: 1 hour

---

#### Feature 0026-003: LLM Request Detail API
**Endpoint**: `GET /api/admin/llm-requests/{request_id}`

**Tasks**:
- **0026-003-001**: Create `get_llm_request_detail()` endpoint in `admin.py`
  - Query `llm_requests` table for request_id
  - Parse `request_body` to extract prompt breakdown
  - Parse `response_body` for tool calls and response
  - **Challenge**: Need to reconstruct prompt breakdown from stored data
    - Option A: Store prompt breakdown in `meta` field during agent creation (recommended)
    - Option B: Reverse-engineer from `request_body` (fragile)
  
- **0026-003-002**: **Decision Point**: Add prompt breakdown logging to `simple_chat.py`
  - Modify `create_simple_chat_agent()` to log prompt breakdown to Logfire
  - Store breakdown in `llm_requests.meta` field as JSON:
    ```json
    {
      "prompt_breakdown": {
        "critical_rules": {"char_count": 4928, "source": "tool_selection_hints.md"},
        "base_prompt": {"char_count": 3200, "source": "system_prompt.md"},
        ...
      }
    }
    ```
  
- **0026-003-003**: Test endpoint with recent LLM request

**Manual Tests**:
- ✅ Returns full prompt (reconstructed or from meta)
- ✅ Prompt breakdown shows sections with char counts
- ✅ Tool calls displayed with args and outputs
- ✅ Response metadata correct

**Effort**: 2 hours (includes adding prompt breakdown logging)

---

### Phase 2: Frontend Pages (Astro + Preact)
**Goal**: Create simple, functional admin UI

#### Feature 0026-004: Session List Page
**Route**: `/admin/sessions`

**Tasks**:
- **0026-004-001**: Create `/web/src/pages/admin/sessions.astro`
  - Fetch sessions from API on page load (server-side)
  - Embed Preact component for interactive table
  - Add "View Details" link to session detail page
  
- **0026-004-002**: Create Preact component for filters
  - File: `/web/src/components/admin/SessionFilters.tsx`
  - Dropdown selects for account and agent
  - Fetch filtered data on selection change
  - Update table without page reload
  
- **0026-004-003**: Style with TailwindCSS
  - Simple table layout
  - Hover effects on rows
  - Loading spinner during fetch requests

**Manual Tests**:
- ✅ Page loads and displays sessions
- ✅ Filters reload table without full page refresh
- ✅ "View Details" links navigate to correct session
- ✅ Pagination buttons work

**Effort**: 2 hours

---

#### Feature 0026-005: Session Detail Page
**Route**: `/admin/sessions/[id].astro`

**Tasks**:
- **0026-005-001**: Create `/web/src/pages/admin/sessions/[id].astro`
  - Dynamic route with session ID param
  - Fetch session messages from API (server-side)
  - Render conversation timeline (user/assistant bubbles)
  
- **0026-005-002**: Create Preact component for message details
  - File: `/web/src/components/admin/MessageDetails.tsx`
  - "Show Details" button for each assistant message
  - Fetch LLM request details on click
  - Display in sidebar: model, tokens, cost, duration, tool calls
  
- **0026-005-003**: Create Preact prompt inspector component
  - File: `/web/src/components/admin/PromptInspector.tsx`
  - Expandable sections for prompt breakdown
  - Syntax highlighting with `<pre><code>` blocks
  - Copy button for full prompt (navigator.clipboard API)
  
- **0026-005-004**: Style conversation timeline with TailwindCSS
  - User messages: blue bubble, left-aligned
  - Assistant messages: gray bubble, right-aligned
  - Timestamp below each message
  - Smooth scrolling behavior

**Manual Tests**:
- ✅ Session loads with all messages
- ✅ "Show Details" loads prompt inspector without page reload
- ✅ Prompt breakdown displays all sections
- ✅ Copy button copies full prompt to clipboard
- ✅ Conversation timeline is readable and scrollable

**Effort**: 3 hours

---

#### Feature 0026-006: LLM Request Detail Page (Optional)
**Route**: `/admin/llm-requests/[id].astro`

**Tasks**:
- **0026-006-001**: Create deep-dive page for single LLM request
  - Accordion sections for prompt breakdown
  - Raw JSON view for request/response bodies
  - Tool call inspection
  
- **0026-006-002**: Add "Analyze Tool Selection" section
  - Show keywords detected in user query
  - Show which tool was selected and why
  - Highlight mismatches (e.g., "phone" keyword but `vector_search` chosen)

**Manual Tests**:
- ✅ Page displays full LLM request details
- ✅ Accordion sections expand/collapse
- ✅ Raw JSON is formatted and readable
- ✅ Tool selection analysis is helpful for debugging

**Effort**: 2 hours (optional, can defer)

---

## File Structure

```
web/
├── src/
│   ├── pages/
│   │   ├── admin/
│   │   │   ├── index.astro                    # Redirect to /admin/sessions
│   │   │   ├── sessions.astro                 # Session list page (Feature 0026-004)
│   │   │   └── sessions/
│   │   │       └── [id].astro                 # Session detail page (Feature 0026-005)
│   │   └── llm-requests/
│   │       └── [id].astro                     # LLM request detail (Feature 0026-006, optional)
│   ├── components/
│   │   ├── admin/
│   │   │   ├── SessionFilters.tsx             # Preact: Filter component with state
│   │   │   ├── SessionTable.tsx               # Preact: Interactive session table
│   │   │   ├── MessageBubble.tsx              # Preact: User/assistant message bubble
│   │   │   ├── MessageDetails.tsx             # Preact: LLM metadata display
│   │   │   ├── PromptInspector.tsx            # Preact: Prompt breakdown sidebar
│   │   │   └── ToolCallList.tsx               # Preact: Tool calls display

backend/
├── app/
│   ├── api/
│   │   └── admin.py                           # Admin API endpoints (Features 0026-001-003)
```

---

## Preact Component Examples

### Session Filter Component (TypeScript)
```tsx
// /web/src/components/admin/SessionFilters.tsx
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';

interface Session {
  id: string;
  account_slug: string;
  agent_instance_slug: string;
  created_at: string;
  message_count: number;
}

export function SessionFilters() {
  const [account, setAccount] = useState('');
  const [sessions, setSessions] = useState<Session[]>([]);
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
      <select 
        value={account}
        onChange={(e) => setAccount(e.currentTarget.value)}
        class="border rounded p-2"
      >
        <option value="">All Accounts</option>
        <option value="wyckoff">Wyckoff</option>
      </select>
      
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table class="w-full mt-4">
          {/* Render sessions table */}
        </table>
      )}
    </div>
  );
}
```

### Prompt Inspector Component (TypeScript)
```tsx
// /web/src/components/admin/PromptInspector.tsx
import { h } from 'preact';
import { useState } from 'preact/hooks';

interface PromptBreakdown {
  sections: Array<{
    name: string;
    position: number;
    char_count: number;
    source: string;
  }>;
  total_char_count: number;
}

export function PromptInspector({ requestId }: { requestId: string }) {
  const [breakdown, setBreakdown] = useState<PromptBreakdown | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const loadBreakdown = async () => {
    const response = await fetch(`/api/admin/llm-requests/${requestId}`);
    const data = await response.json();
    setBreakdown(data.prompt_breakdown);
  };

  const copyPrompt = async (text: string) => {
    await navigator.clipboard.writeText(text);
  };

  return (
    <aside class="border-l p-4">
      <h3 class="font-bold mb-4">Prompt Inspector</h3>
      {breakdown && (
        <div>
          {breakdown.sections.map((section) => (
            <div key={section.name} class="mb-2">
              <button 
                onClick={() => setExpanded(expanded === section.name ? null : section.name)}
                class="w-full text-left p-2 bg-gray-100 hover:bg-gray-200 rounded"
              >
                {section.name} ({section.char_count} chars)
              </button>
              {expanded === section.name && (
                <pre class="p-2 bg-gray-50 text-sm overflow-auto">
                  <code>{section.content}</code>
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
```

---

## Backend API Implementation Notes

### Add Prompt Breakdown Logging to simple_chat.py

**Location**: `backend/app/agents/simple_chat.py`

**Modification**: After constructing the full prompt, log the breakdown:

```python
async def create_simple_chat_agent(instance_config, account_id):
    # ... (existing prompt construction code) ...
    
    # NEW: Log prompt breakdown for admin inspection
    prompt_breakdown = {
        "critical_rules": {
            "char_count": len(critical_rules) if critical_rules else 0,
            "source": "tool_selection_hints.md"
        },
        "base_prompt": {
            "char_count": len(base_system_prompt),
            "source": "system_prompt.md"
        },
        "directory_docs": {
            "char_count": len(directory_docs) if directory_docs else 0,
            "source": "auto-generated"
        },
        "other_modules": [
            {"name": m, "char_count": len(load_prompt_module(m, account_slug) or "")}
            for m in other_modules
        ],
        "total_char_count": len(system_prompt)
    }
    
    logfire.info(
        'agent.prompt.breakdown',
        breakdown=prompt_breakdown,
        account_id=str(account_id),
        agent_instance_id=instance_config.get('id')
    )
    
    # ... (continue with agent creation) ...
```

**Why**: This allows the admin frontend to display prompt breakdown without reverse-engineering.

---

## Security Considerations

- **Authentication**: Add basic auth or restrict to localhost only (development tool)
- **Read-Only**: No editing/deletion capabilities (safer for production debugging)
- **Sensitive Data**: Consider redacting user emails or PII in session list (optional)

**Recommendation**: For MVP, restrict to localhost (`127.0.0.1` only). Add auth in Phase 3 if deploying to staging/production.

---

## Success Criteria

### Phase 1 (Backend API):
- ✅ Can list all sessions via API
- ✅ Can view session messages via API
- ✅ Can inspect LLM request details via API
- ✅ Prompt breakdown includes section char counts and sources

### Phase 2 (Frontend):
- ✅ Session list page displays all sessions
- ✅ Filters work without page reload (HTMX)
- ✅ Session detail page shows conversation timeline
- ✅ Prompt inspector loads on-demand (HTMX)
- ✅ Can copy full prompt to clipboard

### Phase 3 (Optional Enhancements):
- ⚠️ Deferred: Tool selection analysis (why wrong tool chosen)
- ⚠️ Deferred: Real-time session monitoring (WebSocket)
- ⚠️ Deferred: Export session as JSON/CSV

---

## Estimated Effort

| Phase | Features | Effort | Priority |
|-------|----------|--------|----------|
| Phase 1 (Backend API) | 0026-001 to 0026-003 | 4 hours | **High** |
| Phase 2 (Frontend) | 0026-004 to 0026-005 | 5 hours | **High** |
| Phase 3 (Optional) | 0026-006 | 2 hours | Low |
| **Total** | | **9-11 hours** | |

**MVP**: Phase 1 + Phase 2 (9 hours) = Fully functional admin UI for debugging chat sessions

---

## Future Enhancements (Post-MVP)

- **Real-time monitoring**: WebSocket updates for active sessions
- **Search**: Full-text search across messages
- **Analytics**: Charts for tool usage, cost per session, model comparison
- **Bulk export**: Download sessions as JSON/CSV for analysis
- **Tool selection analyzer**: Visual diff showing why LLM chose wrong tool
- **Prompt editor**: Test prompt variations without restarting backend

---

## Dependencies

- Astro framework (already in `/web` at 5.13.0)
- Preact (already installed at 10.27.0)
- @astrojs/preact integration (already installed at 4.1.0)
- TailwindCSS (already installed at 4.1.12)
- FastAPI (already in `/backend`)
- SQLAlchemy (already in use for database queries)

---

## Notes

- **Keep it simple**: This is a developer tool, not a user-facing product
- **Preact over React**: Lightweight (3KB) and already integrated with Astro
- **Component-based UI**: Cleaner than vanilla JS for interactive admin features
- **Read-only for safety**: No accidental data modification during debugging
- **Prompt breakdown is key**: Helps debug token position bias and module loading issues
- **TailwindCSS utilities**: Fast styling without custom CSS files

---

## Related Documents

- **Architecture**: `memorybank/architecture/agent-and-tool-design.md`
- **Dynamic Prompting**: `memorybank/design/dynamic-prompting.md`
- **Prompt Modules**: `memorybank/design/prompt-modules.md`
- **Implementation**: `memorybank/project-management/0025-dynamic-prompting-plan.md`

