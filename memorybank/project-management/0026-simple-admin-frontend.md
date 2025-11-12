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
- **Interactivity**: HTMX (lightweight, server-driven)
- **Backend**: FastAPI (existing backend at `/backend/app`)
- **Styling**: Minimal CSS (TailwindCSS if already available, otherwise plain CSS)

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

### Phase 2: Frontend Pages (Astro + HTMX)
**Goal**: Create simple, functional admin UI

#### Feature 0026-004: Session List Page
**Route**: `/admin/sessions`

**Tasks**:
- **0026-004-001**: Create `/web/src/pages/admin/sessions.astro`
  - Fetch sessions from API on page load
  - Render table with session data
  - Add "View Details" link to session detail page
  
- **0026-004-002**: Add HTMX filters for account/agent
  - Dropdown selects for account and agent
  - HTMX `hx-get` to reload table on filter change
  - Target: `#sessions-table` div
  
- **0026-004-003**: Style with minimal CSS (or TailwindCSS if available)
  - Simple table layout
  - Hover effects on rows
  - Loading spinner during HTMX requests

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
  - Fetch session messages from API
  - Render conversation timeline (user/assistant bubbles)
  
- **0026-005-002**: Add "Show Details" button for each assistant message
  - HTMX `hx-get` to load LLM request details
  - Target: `#prompt-inspector` sidebar
  - Display: model, tokens, cost, duration, tool calls
  
- **0026-005-003**: Create prompt inspector sidebar
  - Expandable sections for prompt breakdown
  - Syntax highlighting (optional, use `<pre><code>` blocks)
  - Copy button for full prompt (JavaScript or HTMX)
  
- **0026-005-004**: Style conversation timeline
  - User messages: blue bubble, left
  - Assistant messages: gray bubble, right
  - Timestamp below each message
  - Smooth scrolling

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
│   │   │   ├── SessionTable.astro             # Reusable session table
│   │   │   ├── MessageBubble.astro            # User/assistant message bubble
│   │   │   ├── PromptInspector.astro          # Prompt breakdown sidebar
│   │   │   └── ToolCallList.astro             # Tool calls display
│   └── styles/
│       └── admin.css                          # Admin-specific styles

backend/
├── app/
│   ├── api/
│   │   └── admin.py                           # Admin API endpoints (Features 0026-001-003)
```

---

## HTMX Examples

### Filter Sessions by Account (HTMX)
```html
<!-- /web/src/pages/admin/sessions.astro -->
<select 
  hx-get="/api/admin/sessions" 
  hx-target="#sessions-table"
  hx-swap="innerHTML"
  name="account"
>
  <option value="">All Accounts</option>
  <option value="wyckoff">Wyckoff</option>
  <option value="acme">ACME Corp</option>
</select>

<div id="sessions-table">
  <!-- Table will be inserted here via HTMX -->
</div>
```

### Load Prompt Inspector (HTMX)
```html
<!-- /web/src/pages/admin/sessions/[id].astro -->
<div class="message assistant">
  <p>I don't have the specific phone number...</p>
  <button 
    hx-get="/api/admin/llm-requests/{request_id}"
    hx-target="#prompt-inspector"
    hx-swap="innerHTML"
  >
    Show Details
  </button>
</div>

<aside id="prompt-inspector">
  <!-- Prompt breakdown will be inserted here via HTMX -->
</aside>
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

- Astro framework (already in `/web`)
- HTMX library (add to `package.json` if not present)
- FastAPI (already in `/backend`)
- SQLAlchemy (already in use for database queries)

---

## Notes

- **Keep it simple**: This is a developer tool, not a user-facing product
- **HTMX over React/Vue**: Reduces complexity, server-rendered is sufficient
- **Read-only for safety**: No accidental data modification during debugging
- **Prompt breakdown is key**: Helps debug token position bias and module loading issues

---

## Related Documents

- **Architecture**: `memorybank/architecture/agent-and-tool-design.md`
- **Dynamic Prompting**: `memorybank/design/dynamic-prompting.md`
- **Prompt Modules**: `memorybank/design/prompt-modules.md`
- **Implementation**: `memorybank/project-management/0025-dynamic-prompting-plan.md`

