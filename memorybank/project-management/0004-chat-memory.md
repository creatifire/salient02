# Epic 0004 - Chat Memory & Persistence
> **Last Updated**: August 29, 2025

> Goal: Add persistent chat history and session management to the existing baseline system. Messages and sessions stored in Postgres, with automatic session resumption and profile data accumulation.

## Scope & Approach
- **Single-account mode**: No `accounts` table for now; simplify schema
- **Multiple concurrent sessions**: Full support for multiple users having separate, distinct conversations simultaneously. Each browser/user gets unique session_key, ensuring complete conversation isolation
- **Modify existing endpoints**: Enhance current `POST /chat` and `GET /events/stream` to use database
- **Session resumption**: Automatic based on browser session cookie/ID matching database
- **Incremental profiles**: Collect profile data (name, email, preferences) as it comes during conversations
- **Email linking**: Only when same email provided in different sessions (post-cache-clear scenario)
- **Code organization**: Separate related functionality into maintainable modules
- **No Pydantic AI needed**: This epic focuses on persistence/sessions; Pydantic AI reserved for future structured output (email extraction, routing, citations) in RAG/automation epics

## Database Schema

### Core Tables
```sql
-- Session management and resumption
sessions: 
  id (GUID, PK)
  session_key (VARCHAR, unique) -- browser session cookie value
  email (VARCHAR, nullable)     -- if provided during conversation
  is_anonymous (BOOLEAN)        -- starts true, becomes false when email provided
  created_at (TIMESTAMP)
  last_activity_at (TIMESTAMP)
  metadata (JSONB)              -- extensible for future session data

-- Chat message history
messages:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  role (VARCHAR)                -- 'human'|'assistant'|'system'
  content (TEXT)                -- message content
  metadata (JSONB)              -- citations, doc_ids, scores for future RAG
  created_at (TIMESTAMP)

-- LLM cost tracking and request logging
llm_requests:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  provider (VARCHAR)            -- 'openrouter'
  model (VARCHAR)               -- model used
  request_body (JSONB)          -- sanitized request payload
  response_body (JSONB)         -- response metadata
  prompt_tokens (INTEGER)
  completion_tokens (INTEGER)
  total_tokens (INTEGER)
  unit_cost_prompt (DECIMAL)
  unit_cost_completion (DECIMAL)
  computed_cost (DECIMAL)
  latency_ms (INTEGER)
  created_at (TIMESTAMP)

-- Profile data accumulation (dribs and drabs)
profiles:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)  -- initially 1:1, future: many sessions → 1 profile
  customer_name (VARCHAR, nullable)
  phone (VARCHAR, nullable)
  email (VARCHAR, nullable)
  address_street (VARCHAR, nullable)
  address_city (VARCHAR, nullable)
  address_state (VARCHAR, nullable)
  address_zip (VARCHAR, nullable)
  products_of_interest (TEXT[])
  services_of_interest (TEXT[])
  preferences (JSONB)           -- flexible key-value storage
  updated_at (TIMESTAMP)
```

### Indices
Database indices for optimal performance are defined in [architecture/datamodel.md](../architecture/datamodel.md#performance-indices). Key indices include session lookup, message retrieval, cost analysis, and profile management.

## Concurrent Session Architecture

### Multi-User Support Design
The schema and session management fully supports multiple concurrent users:

**🔀 Session Isolation**:
- Each browser generates unique `session_key` (stored in HTTP-only cookie)
- Database enforces `sessions.session_key` uniqueness via index
- All tables link via `session_id` FK, ensuring complete data isolation

**👥 Concurrent User Scenarios**:
- **User A** (Chrome, laptop): Gets session_key `abc123`, all messages/requests/profile linked to session ID `uuid-A`
- **User B** (Firefox, phone): Gets session_key `def456`, all data linked to session ID `uuid-B` 
- **User A** (new tab): Same session_key cookie, resumes existing conversation
- **User A** (incognito): New session_key `ghi789`, starts fresh conversation

**⚡ Performance & Concurrency**:
- PostgreSQL connection pooling handles concurrent database access
- Session middleware runs per-request, no shared state between users
- Each HTTP request includes session context, enabling full parallel processing

**🔒 Data Security**:
- No cross-session data leakage possible due to FK constraints
- Session cookies are HTTP-only, secure, and SameSite protected
- Profile data accumulates per-session, never mixed between users

## [x] 0004-001 - FEATURE - Development Environment & Database Setup

### [x] 0004-001-001 - TASK - Docker Development Environment
- [x] 0004-001-001-01 - CHUNK - Docker Compose setup
  - SUB-TASKS:
    - Create `docker-compose.dev.yml` for local development services
    - Configure PostgreSQL container with persistent volume
    - Add Adminer for database administration (web UI)
    - Add Redis container for future session/cache storage
    - Configure environment variables and networking
    - Acceptance: `docker-compose up -d` starts all services; DB accessible

- [x] 0004-001-001-02 - CHUNK - Database initialization scripts
  - SUB-TASKS:
    - Create `docker/postgres/init.sql` for initial database setup
    - Add development user creation and permissions
    - Configure database extensions (uuid-ossp, pg_trgm for text search)
    - Add sample data script for testing
    - Acceptance: Fresh container starts with configured database

- [x] 0004-001-001-03 - CHUNK - Development scripts and documentation
  - SUB-TASKS:
    - Create `scripts/dev-setup.sh` for one-command environment setup
    - Add `scripts/dev-reset.sh` to reset database with fresh data
    - Update `backend/README.md` with Docker development instructions
    - Document database connection strings and admin URLs
    - Acceptance: New developer can start working with single script

## [x] 0004-002 - FEATURE - Database Setup & Migrations

### [x] 0004-002-001 - TASK - SQLAlchemy Models & Alembic Setup
- [x] 0004-002-001-01 - CHUNK - Install and configure Alembic
  - SUB-TASKS:
    - Add `alembic` to requirements.txt if not already present
    - Initialize Alembic in `backend/migrations/`
    - Configure `alembic.ini` and `env.py` for asyncpg connection
    - Set up `backend/app/models/` module structure
    - Acceptance: `alembic init` complete, can connect to DB

- [x] 0004-002-001-02 - CHUNK - Define SQLAlchemy models
  - SUB-TASKS:
    - Create `backend/app/models/__init__.py`
    - Create `backend/app/models/session.py` (Session model)
    - Create `backend/app/models/message.py` (Message model)  
    - Create `backend/app/models/llm_request.py` (LLMRequest model)
    - Create `backend/app/models/profile.py` (Profile model)
    - Use GUID primary keys, proper relationships, nullable fields
    - Acceptance: Models import cleanly, relationships defined

- [x] 0004-002-001-03 - CHUNK - Initial migration
  - SUB-TASKS:
    - Generate migration: `alembic revision --autogenerate -m "Initial chat memory schema"`
    - Review and adjust migration file
    - Test migration: `alembic upgrade head`
    - Add sample data insertion for testing
    - Acceptance: Tables created successfully in Postgres

### [x] 0004-002-002 - TASK - Database Connection & Configuration
- [x] 0004-002-002-01 - CHUNK - Database configuration
  - SUB-TASKS:
    - Add database settings to `backend/config/app.yaml`
    - Add `DATABASE_URL` to `.env` template
    - Update `backend/app/config.py` to load DB config
    - Create connection pooling setup
    - Acceptance: DB config loads correctly, connection successful

- [x] 0004-002-002-02 - CHUNK - Database service module
  - SUB-TASKS:
    - Create `backend/app/database.py` with async session management
    - Implement connection pool, session lifecycle
    - Add database health check endpoint
    - Integration with existing health endpoint
    - Acceptance: DB sessions work, health check passes

## 0004-003 - FEATURE - Session Management & Resumption

### [x] 0004-003-001 - TASK - Session Creation & Lookup
- [x] 0004-003-001-01 - CHUNK - Session service module
  - SUB-TASKS:
    - Create `backend/app/services/session_service.py`
    - Implement `create_session()`, `get_session_by_key()`, `update_last_activity()`
    - Handle session key generation (secure random)
    - Set browser cookie with session key
    - Acceptance: Sessions created and retrieved by key
  - STATUS: Completed — Created comprehensive SessionService with secure key generation, database operations, activity tracking, email updates, and cookie configuration utilities

- [x] 0004-003-001-02 - CHUNK - Session middleware integration
  - SUB-TASKS:
    - Create session middleware for FastAPI
    - Auto-create session if none exists
    - Load existing session if valid session key in cookie
    - Update `last_activity_at` on each request
    - Acceptance: Session tracking works transparently
  - STATUS: Completed — Created comprehensive SessionMiddleware for automatic session management, integrated with FastAPI main app, added session context to all routes, and created helper functions for session access

### [x] 0004-003-002 - TASK - Frontend Session Handling
- [x] 0004-003-002-01 - CHUNK - Session cookie management
  - SUB-TASKS:
    - Configure secure session cookies (httpOnly, secure, sameSite)
    - Handle session cookie in chat UI
    - Display session status in dev diagnostics
    - Acceptance: Session persistence across browser refreshes
  - STATUS: Completed — Implemented secure session cookies with HttpOnly/SameSite protection, automatic session handling in chat UI, added session diagnostics panel with real-time session info display, and verified session persistence across browser refreshes

## 0004-004 - FEATURE - Message Persistence & Chat History

### [ ] 0004-004-001 - TASK - Message Storage
- [x] 0004-004-001-01 - CHUNK - Message service module
  - SUB-TASKS:
    - Create `backend/app/services/message_service.py`
    - Implement `save_message()`, `get_session_messages()`, `get_recent_context()`
    - Handle human, assistant, system message types
    - Store metadata field for future RAG citations
    - Acceptance: Messages saved and retrieved by session

- [x] 0004-004-001-02 - CHUNK - Chat history loading
  - SUB-TASKS:
    - Load existing messages when session resumes
    - Display chat history in UI on page load
    - Handle empty history gracefully
    - Limit initial history load (e.g., last 50 messages)
    - Acceptance: Previous conversations visible on return
  - STATUS: Completed — Implemented _load_chat_history_for_session() function that loads last 50 messages with UI-optimized formatting, modified main page template to pre-populate chat history on load, added graceful empty history handling, and created comprehensive test suite verifying all functionality including message limits, role filtering, and error handling

### [ ] e - TASK - Modify Existing Chat Endpoints

#### Configuration Architecture Analysis & Recommendation

**Problem Identified:** During testing, discovered configuration inconsistency between backend and frontend for endpoint selection, leading to messages not persisting when using demo pages.

**Current Architecture:**
- **Backend:** Uses `sse_enabled` setting in `app.yaml` under `ui` section
- **Frontend Demo Pages:** Use separate `PUBLIC_SSE_ENABLED` environment variable
- **Chat Endpoints:** 
  - `GET /events/stream` (SSE streaming, primary)
  - `POST /chat` (non-streaming fallback)

**Analysis - app.yaml vs .env:**

**app.yaml Advantages:**
- ✅ Version controlled and consistent across environments
- ✅ Structured configuration with logical organization
- ✅ Backend-centric (server knows its own capabilities)
- ✅ Production ready with deployment templating support
- ✅ Single source of truth for application configuration
- ✅ Type validation possible at startup

**app.yaml Disadvantages:**
- ❌ Requires application restart for changes
- ❌ Less flexible for environment-specific overrides

**.env Advantages:**
- ✅ Runtime flexibility without rebuild
- ✅ Environment-specific configuration
- ✅ Conventional location for secrets
- ✅ Developer-friendly modification

**.env Disadvantages:**
- ❌ Not version controlled (environment drift risk)
- ❌ Frontend/backend configuration duplication
- ❌ Type unsafe (all values are strings)

**Recommendation:**
- **Single setting:** `sse_enabled` in `app.yaml` under `ui` section
- **Rationale:** This controls implementation strategy, not separate protocols. Both endpoints provide same functionality with different UX (streaming vs complete response)
- **Implementation:** Backend passes setting to frontend templates, eliminating duplication
- **Environment variables:** Reserved for secrets only (DATABASE_URL, API keys)

**Root Cause:** The configuration location isn't the issue - the SSE endpoint lacks message persistence. Solution is implementing CHUNK 0004-004-002-02 rather than configuration changes.

#### Chat Interface Endpoint Usage Matrix

| **Page/Widget** | **Location** | **Primary Endpoint** | **Fallback Endpoint** | **Configuration Source** | **Notes** |
|---|---|---|---|---|---|
| **Backend Main Chat** | `backend/templates/index.html` | `GET /events/stream` | `POST /chat` | `app.yaml: ui.sse_enabled` | Production chat interface, session-aware |
| **HTMX Demo (Astro)** | `web/src/pages/demo/htmx-chat.astro` | `POST /chat` | `GET /events/stream` | `SSE_ENABLED = false` (hardcoded) | Modified for persistence testing |
| **HTMX Demo (Plain)** | `web/public/htmx-chat.html` | `GET /events/stream` | `POST /chat` | SSE with POST fallback on error | Standalone HTML file |
| **Shadow DOM Widget** | `web/public/widget/chat-widget.js` | `GET /events/stream` | `POST /chat` | `data-sse="0"` attribute | Embeddable widget, configurable |
| **Widget Demo Page** | `web/src/pages/demo/widget.astro` | Inherits from widget | Inherits from widget | Widget configuration | Demonstrates widget integration |
| **Iframe Demo** | `web/src/pages/demo/iframe.astro` | Inherits from backend | Inherits from backend | Backend configuration | Embeds backend main chat |

**Test Coverage Requirements:**
- ✅ **POST /chat persistence** - Verified via HTMX Demo (Astro) and direct API testing
- ✅ **GET /events/stream persistence** - Completed in CHUNK 0004-004-002-02
- ✅ **Cross-origin session handling** - Completed in CHUNK 0004-004-002-04
- ✅ **Configuration consistency** - Backend controls behavior, frontend respects settings
- ✅ **Backend markdown formatting** - Tables, line breaks, copy buttons working
- ❌ **Frontend markdown consistency** - Need to apply fixes to demo pages and widget (CHUNK 0004-004-002-06)

**Endpoint Decision Logic:**
1. **SSE-first interfaces**: Check `sse_enabled` setting, fall back to POST on errors
2. **POST-first interfaces**: Use POST directly (current testing configuration)
3. **Widget**: Configurable via `data-sse` attribute (default: SSE enabled)

**Implementation Chunks:**

- [x] 0004-004-002-01 - CHUNK - Update POST /chat endpoint
  - SUB-TASKS:
    - Save human message to database before LLM call
    - Save assistant response after LLM completion
    - Include session context in request logging
    - Maintain existing response format/behavior
    - Acceptance: Chat persists without UI changes
  - STATUS: Completed — Enhanced POST /chat endpoint with comprehensive message persistence, saving user messages before LLM calls and assistant responses after completion, added detailed session context logging with message previews and metadata, maintained existing response format/behavior for compatibility, implemented graceful error handling for database failures, and verified functionality through testing

- [x] 0004-004-002-02 - CHUNK - Update GET /events/stream endpoint  
  - SUB-TASKS:
    - Save assistant message chunks during streaming
    - Handle streaming vs non-streaming message persistence
    - Ensure message completeness on stream end
    - Link to session properly
    - Acceptance: Streamed messages persist correctly
  - STATUS: Completed — Enhanced SSE endpoint with comprehensive message persistence, saving user messages before streaming starts and accumulating assistant response chunks during streaming, implemented complete message saving on stream end for both LLM and demo modes, added proper session linking and metadata tracking, maintained existing streaming functionality while adding full database persistence, and verified functionality through testing with both demo and real LLM responses

- [x] 0004-004-002-03 - CHUNK - Configuration consistency cleanup ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Remove PUBLIC_SSE_ENABLED from Astro demo pages
    - ✅ Update demo pages to read sse_enabled from backend API or build-time injection
    - ✅ Verify frontend templates receive sse_enabled from app.yaml consistently
    - ✅ Remove environment variable duplication for configuration settings
    - ✅ Update documentation to reflect single source of truth approach
    - Acceptance: ✅ All frontend components use consistent configuration source
  
  **Implementation Details:**
  - **Added `/api/config` endpoint**: Provides centralized configuration API for frontend components
  - **Updated Astro demo**: Now fetches backend configuration at build time instead of hardcoded values
  - **Updated standalone HTML**: Added configuration fetching with graceful fallbacks
  - **Updated widget**: Respects backend `sse_enabled` setting in addition to client preferences
  - **Maintained environment variables**: Only kept appropriate env vars for feature enablement and deployment targets
  - **Single source of truth**: All UI behavior settings now flow from `app.yaml` → backend API → frontend components

- [x] 0004-004-002-04 - CHUNK - Cross-origin session handling
  - SUB-TASKS:
    - Document session cookie behavior across different ports (localhost:8000 vs localhost:4321)
    - Add development mode detection for relaxed cookie settings during demo testing
    - Implement session bridging mechanism for demo pages or document workarounds
    - Add clear documentation about demo page limitations and testing approaches
    - Acceptance: Demo pages work correctly or limitations are clearly documented
  - STATUS: Completed — Implemented production-ready cross-origin session management with environment-based configuration (PRODUCTION_CROSS_ORIGIN, COOKIE_SECURE, COOKIE_DOMAIN), added comprehensive production deployment documentation, created proper CORS configuration for FastAPI backend, added session and chat history API endpoints for frontend integration, documented complete production architecture with Docker deployment and Nginx configuration, and provided deployment checklist for cross-origin Astro + FastAPI applications

- [x] 0004-004-002-05 - CHUNK - Frontend chat history loading for demo pages ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Add JavaScript function to load chat history via `/api/chat/history` endpoint
    - ✅ Implement history rendering in HTMX demo page (`web/src/pages/demo/htmx-chat.astro`)
    - ✅ Handle empty history gracefully in frontend components
    - ✅ Add proper error handling for history loading failures
    - ✅ Ensure history loads on page refresh and maintains proper message ordering
    - ✅ Style historical messages consistently with new messages
    - ✅ Add loading indicators during history fetch
    - Acceptance: ✅ Demo pages reload chat history on page refresh, displaying previous conversation seamlessly
  
  **Implementation Details:**
  - **Added `/api/chat/history` endpoint integration**: Both demo pages now fetch chat history dynamically on page load using the backend API
  - **Fixed Vite proxy configuration**: Added `/api` route to `web/astro.config.mjs` for proper API routing in development
  - **Implemented consistent message rendering**: Bot messages use pre-rendered HTML from API, user messages display as plain text
  - **Fixed CSS formatting issue**: Changed `.content{ white-space:pre-wrap; }` to `.msg.user .content{ white-space:pre-wrap; }` to prevent extra line spacing in bot messages
  - **Added table and paragraph styling**: Applied backend CSS styles for proper markdown table and paragraph rendering
  - **Comprehensive error handling**: Graceful degradation for empty history, network errors, and session issues
  - **Loading indicators**: Visual feedback during history fetch with proper show/hide logic
  - **Session compatibility**: Works correctly with existing session management and cross-origin scenarios

- [x] 0004-004-002-10 - CHUNK - Chat Widget History Loading Integration ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Add chat history loading functionality to Shadow DOM Widget (`web/public/widget/chat-widget.js`)
    - ✅ Implement `/api/chat/history` endpoint integration for widget
    - ✅ Handle cross-origin session management for embedded widgets
    - ✅ Add loading indicators and error handling for widget history loading
    - ✅ Ensure widget history displays consistently with session data
    - ✅ Handle empty history gracefully in widget environment
    - ✅ Test widget history loading across different embedding scenarios (architecture verified)
    - Acceptance: ✅ Chat widget loads previous conversation history when opened
  - PRIORITY: High - Widget users expect conversation continuity
  - DEPENDENCIES: Requires `/api/chat/history` endpoint (already available) and cross-origin session handling (completed in 0004-004-002-04)

  **Implementation Details:**
  - **History loading function**: Added `loadHistory()` function with comprehensive error handling and loading states
  - **Loading indicator**: Added CSS animations and HTML for loading spinner with "Loading chat history..." message
  - **Cross-origin support**: Implemented proper CORS handling with `credentials: 'include'` for cross-origin session management
  - **API integration**: Integrated `/api/chat/history` endpoint with proper error handling for 401 (no session) and other HTTP errors
  - **Message rendering**: Bot messages use `innerHTML` for pre-rendered HTML, user messages use `textContent` for raw text
  - **State management**: Added `historyLoaded` flag to prevent duplicate loading, resets on clear action
  - **Trigger integration**: History loads automatically when widget opens via `open()` function
  - **Graceful degradation**: Handles empty history, network errors, and missing sessions gracefully with debug logging
  - **Shadow DOM compatibility**: All functionality properly encapsulated within shadow DOM scope
  - **Session consistency**: Maintains consistency with backend session data and cookie handling across origins

- [x] 0004-004-002-06 - CHUNK - Markdown formatting for HTMX-Based Chat Integration (Astro Framework) ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Fix HTMX Demo (Astro) at `web/src/pages/demo/htmx-chat.astro`
    - ✅ Add `{ breaks: true }` to markdown processing in Astro HTMX implementation
    - ✅ Implement interim line break preservation (`\n` → `<br>`) during streaming
    - ✅ Add table styling CSS to Astro demo page
    - ✅ Add proper paragraph spacing and user message whitespace preservation
    - ✅ Add DOMPurify script dependency for HTML sanitization
    - Acceptance: ✅ Astro HTMX demo renders markdown consistently with backend
  - PRIORITY: High - Server-side rendered Astro page with HTMX for dynamic chat
  - DEPENDENCIES: Requires completed backend markdown processing (already done)
  
  **Implementation Details:**
  - **Enhanced markdown processing**: Added `{ breaks: true }` to `marked.parse()` calls for proper line break handling
  - **Streaming line break preservation**: Implemented interim `\n` → `<br>` conversion during streaming for better real-time display
  - **Comprehensive table styling**: Added complete CSS for markdown tables with borders, hover effects, and alternating row colors
  - **Proper paragraph spacing**: Added paragraph margin and line-height styles specifically for bot messages
  - **User message whitespace**: Preserved `white-space: pre-wrap` only for user messages to maintain intended formatting
  - **HTML sanitization**: Added DOMPurify script dependency for secure HTML rendering
  - **Consistent with backend**: All formatting now matches the backend `index.html` implementation

- [x] 0004-004-002-07 - CHUNK - Markdown formatting for Standalone HTMX Integration (Plain HTML) ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Fix Plain HTMX Demo at `web/public/htmx-chat.html`
    - ✅ Update standalone HTML file with proper markdown configuration
    - ✅ Ensure table rendering and line break handling match backend behavior
    - ✅ Add table styling CSS to standalone HTML implementation (already present)
    - ✅ Verify cross-origin functionality and session handling
    - Acceptance: ✅ Standalone HTML demo renders markdown consistently with backend
  - PRIORITY: High - Self-contained HTML file with HTMX, no framework dependencies
  - DEPENDENCIES: Requires completed backend markdown processing (already done)
  
  **Implementation Details:**
  - **Enhanced markdown processing**: Added `{ breaks: true }` to `marked.parse()` call in `renderMarkdownOrFallback` function
  - **Streaming line break preservation**: Implemented interim `\n` → `<br>` conversion during SSE streaming for better real-time display
  - **Comprehensive table styling**: Table CSS was already properly implemented with borders, hover effects, and alternating row colors
  - **Proper paragraph spacing**: Paragraph CSS was already correctly configured for bot messages
  - **User message whitespace**: `white-space: pre-wrap` already properly scoped to user messages only
  - **HTML sanitization**: DOMPurify already integrated for secure HTML rendering
  - **Cross-origin compatibility**: Session handling and API calls work correctly across different origins
  - **Consistent with backend**: All formatting now matches the backend `index.html` and Astro implementations

- [x] 0004-004-002-08 - CHUNK - Markdown formatting for Embeddable Widget Integration (Shadow DOM) ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Update Shadow DOM Widget (`web/public/widget/chat-widget.js`) markdown processing
    - ✅ Fix line 37: Add `{ breaks: true }` to `marked.parse()` calls
    - ✅ Fix line 201: Add interim line break preservation during streaming
    - ✅ Add table styling CSS within shadow DOM styles
    - ✅ Ensure copy button functionality works within shadow DOM
    - ✅ Test widget embedding across different domains and contexts (verified architecture)
    - Acceptance: ✅ Widget renders markdown consistently with backend in all embedding scenarios
  - PRIORITY: High - Encapsulated widget for embedding in third-party sites
  - DEPENDENCIES: Requires completed backend markdown processing (already done)

  **Implementation Details:**
  - **Enhanced markdown processing**: Added `{ breaks: true }` to `marked.parse()` call in `renderMarkdownInto` function
  - **Streaming line break preservation**: Implemented interim `\n` → `<br>` conversion during SSE streaming with proper shadow DOM content targeting
  - **Comprehensive table styling**: Added complete CSS for markdown tables within shadow DOM styles including borders, hover effects, and alternating row colors
  - **Proper paragraph spacing**: Added paragraph margin and line-height styles specifically for bot messages within shadow DOM
  - **User message whitespace**: Scoped `white-space: pre-wrap` to user messages only (`.msg.user .content`)
  - **HTML sanitization**: DOMPurify already properly integrated for secure HTML rendering
  - **Shadow DOM isolation**: All styles and functionality properly encapsulated within shadow DOM
  - **Copy button functionality**: Verified proper operation within shadow DOM with fallback mechanisms
  - **Cross-domain embedding**: Architecture supports embedding across different domains with proper CORS handling
  - **Consistent rendering**: All formatting now matches backend, Astro, and standalone HTML implementations

- [deprecated] 0004-004-002-09 - CHUNK - Cross-Strategy Markdown Validation (All 5 Integration Strategies)
  - SUB-TASKS:
    - Verify markdown consistency across all FIVE integration strategies:
      1. **Backend FastAPI Template** (`backend/templates/index.html`) - ✅ Already working
      2. **HTMX-Based Chat (Astro Framework)** (`web/src/pages/demo/htmx-chat.astro`) - Needs fixes
      3. **Standalone HTMX (Plain HTML)** (`web/public/htmx-chat.html`) - Needs fixes  
      4. **Embeddable Widget (Shadow DOM)** (`web/public/widget/chat-widget.js`) - Needs fixes
      5. **iFrame Integration** (`web/src/pages/demo/iframe.astro`) - ✅ Already working (uses backend template)
    - Test identical content (tables, poetry, formatting) renders the same way across all 5 strategies
    - Ensure copy functionality preserves original markdown in all strategies
    - Validate streaming behavior consistency across SSE and POST endpoints for all interfaces
    - Document integration-specific considerations and limitations for each strategy
    - Create comprehensive test matrix for markdown rendering across all 5 chat interfaces
    - Verify cross-origin functionality works correctly for strategies 2, 3, 4, and 5
    - Ensure session handling consistency across all integration approaches
    - Acceptance: (Deprecated) strict DOM/CSS parity across backend/astro/widget is not required. We rely on functional checks (history loads, copy works, streaming completes) and ad‑hoc visual review.
  - STATUS: Deprecated — keep functional parity only; no cross‑strategy DOM/CSS equality enforcement.
  - RATIONALE: Different surfaces (SSR template, Astro HTMX, Shadow DOM widget) intentionally differ in wrappers and CSS scope; enforcing equality is noisy and low-value.
  - DEPENDENCIES: N/A

#### Implementation Details for CHUNK 0004-004-002-04

**Files Modified:**
- `backend/config/app.yaml`: Updated session configuration for production cross-origin support
- `backend/app/middleware/simple_session_middleware.py`: Enhanced with environment-based cookie configuration
- `backend/app/main.py`: Added `/api/chat/history` endpoint for frontend integration
- `memorybank/architecture/cross-origin-session-handling.md`: Comprehensive development documentation
- `memorybank/architecture/production-cross-origin-plan.md`: Complete production deployment guide
- `memorybank/architecture/production-deployment-config.md`: Environment configuration and Docker setup

**Backend Configuration Enhancements:**
```yaml
# backend/config/app.yaml - Updated session section
session:
  cookie_name: "salient_session"
  cookie_max_age: 604800  # 7 days
  cookie_secure: false    # true in production (set via environment)
  cookie_httponly: true
  cookie_samesite: "lax"  # "none" for cross-origin production (set via environment)
  cookie_domain: null     # Set via environment for production (e.g., ".yourcompany.com")
  inactivity_minutes: 30  # Session timeout after 30 minutes of inactivity
  # Cross-origin settings for production deployment
  production_cross_origin: false  # Enable cross-origin session sharing for production
```

**Session Middleware Updates:**
- Environment variable detection: `PRODUCTION_CROSS_ORIGIN`, `COOKIE_SECURE`, `COOKIE_DOMAIN`
- Dynamic cookie configuration based on deployment mode
- Production cross-origin: `SameSite=none` with `Secure=true`
- Development cross-origin: No SameSite restriction with HTTP support
- Comprehensive logging for configuration decisions

**New API Endpoints:**
```python
# Added to backend/app/main.py
@app.get("/api/chat/history", response_class=JSONResponse)
async def get_chat_history(request: Request) -> JSONResponse:
    # Returns chat history for current session in JSON format
    # Enables frontend components to load chat history dynamically
```

**Production Architecture Documentation:**
- Complete Astro + FastAPI cross-origin deployment pattern
- Docker containerization with multi-service setup
- Nginx reverse proxy configuration for HTTPS termination
- CORS configuration for FastAPI backend
- Environment variable management for production security
- Session cookie sharing across subdomains
- Frontend API integration patterns with credentials

**Security Considerations:**
- HTTPS-only cookies in production with `Secure=true`
- Cross-origin compatibility with `SameSite=none`
- Domain-wide session sharing with `Domain=.yourcompany.com`
- Comprehensive CORS allowlist configuration
- Environment-driven security flag management

**Deployment Checklist:**
- Frontend: Static Astro deployment with environment configuration
- Backend: Dockerized FastAPI with production-grade session handling
- Database: PostgreSQL with proper connection pooling
- Monitoring: Health checks and session activity logging
- Testing: Cross-origin request validation and session persistence verification

### [ ] 0004-004-003 - TASK - Enhanced Session Information Display
- [x] 0004-004-003-01 - CHUNK - Session info API enhancement ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Extend GET /api/session endpoint to include LLM configuration
    - ✅ Add current model, provider, temperature, and max_tokens to response
    - ✅ Include configuration source information (YAML vs environment)
    - ✅ Add last LLM usage statistics (if available)
    - Acceptance: ✅ Session API returns comprehensive configuration data

  **Implementation Details:**
  - **Enhanced session endpoint**: Extended `/api/session` to include comprehensive LLM configuration section
  - **LLM configuration display**: Added provider, model, temperature, max_tokens with current values
  - **Configuration source tracking**: Implemented detection of YAML vs environment vs default sources for each setting
  - **Environment variable override detection**: Checks for LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
  - **Usage statistics framework**: Added placeholder structure for future LLM usage tracking implementation
  - **Response structure**: Added `llm_configuration` section with nested `config_sources` for operational transparency
  - **Backward compatibility**: Maintains all existing session information while adding new LLM data
  - **Security**: Configuration source information helps identify potential security/deployment issues

- [x] 0004-004-003-02 - CHUNK - Frontend session info UI enhancement ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Update session info button display to include LLM model information
    - ✅ Add formatted display for model configuration (provider/model)
    - ✅ Include temperature and max_tokens settings with user-friendly labels
    - ✅ Add visual indicators for configuration source (config file vs environment)
    - ✅ Style LLM configuration section distinctly from session data
    - Acceptance: ✅ Session info shows current LLM model and settings clearly

  **Implementation Details:**
  - **Enhanced session display**: Updated session info JavaScript to include comprehensive LLM configuration section
  - **Configuration source badges**: Added color-coded badges (YAML/ENV/DEFAULT) to show source of each setting
  - **User-friendly formatting**: Provider/model displayed in code blocks, temperature/max_tokens with descriptive labels
  - **Visual distinction**: LLM section has blue left border, light background, and distinct styling from session data
  - **Responsive layout**: Configuration items use flexbox for proper wrapping and alignment
  - **Descriptive labels**: Added explanatory text for temperature (randomness) and max_tokens (response length)
  - **Usage statistics placeholder**: Framework ready for future LLM usage tracking display
  - **Error handling**: Graceful degradation when LLM configuration is unavailable
  - **Accessibility**: Clear headings and semantic structure for screen readers

- [x] 0004-004-003-03 - CHUNK - Configuration change detection ✅ **COMPLETED**
  - SUB-TASKS: ✅ **ALL COMPLETED**
    - ✅ Add configuration version/timestamp to session info
    - ✅ Detect when configuration differs from what was used for last request
    - ✅ Add warning indicators for configuration mismatches
    - ✅ Include configuration reload timestamp in display
    - Acceptance: ✅ Users can see if configuration has changed since last interaction

  **Implementation Details:**
  - **Configuration metadata tracking**: Added versioning system with timestamps, hashes, and file modification tracking
  - **Backend enhancements**: Extended config.py with `_generate_config_metadata()` and `get_config_metadata()` functions
  - **API enhancement**: Added `configuration_metadata` section to `/api/session` endpoint with version, timestamps, and hashes
  - **Change detection logic**: Implemented automatic detection of stale configurations (>24 hours) and YAML file modifications
  - **Warning system**: Added visual warning indicators for configuration mismatches with emoji icons and color coding
  - **Metadata display**: Shows configuration version, load timestamp, YAML modification time, and hash values
  - **Hash-based versioning**: Uses MD5 hashes of configuration and environment variables for change detection
  - **Timestamp formatting**: Human-readable UTC timestamps for operational clarity
  - **Visual styling**: Distinct metadata section with blue background and comprehensive warning indicators

## 0004-005 - FEATURE - LLM Request Tracking

### [ ] 0004-005-001 - TASK - Cost & Usage Tracking
- [ ] 0004-005-001-01 - CHUNK - LLM request service
  - SUB-TASKS:
    - Create `backend/app/services/llm_service.py`
    - Wrap OpenRouter calls with cost tracking
    - Extract token counts, latency, cost from responses
    - Store sanitized request/response data
    - Acceptance: All LLM calls tracked with cost data

- [ ] 0004-005-001-02 - CHUNK - Usage reporting endpoints
  - SUB-TASKS:
    - Add `GET /api/session/{session_id}/usage` endpoint
    - Aggregate cost, token counts, request counts per session
    - Add basic usage display in dev diagnostics
    - Export usage data as JSON
    - Acceptance: Session usage visible and exportable

## 0004-006 - FEATURE - Profile Data Collection

> **⚠️ DESIGN REVIEW REQUIRED**: Before implementing profile gathering, review design to add support for configurable profile field definitions via YAML/JSON file (stored in database or filesystem alongside app.yaml, but not in app.yaml itself). This will allow customizable profile data collection based on business requirements.

### [ ] 0004-006-001 - TASK - Profile Creation & Updates
- [ ] 0004-006-001-01 - CHUNK - Profile service module
  - SUB-TASKS:
    - Create `backend/app/services/profile_service.py`
    - Implement `create_profile()`, `update_profile()`, `get_session_profile()`
    - Handle incremental profile data updates
    - Support array fields (products_of_interest, services_of_interest)
    - Acceptance: Profile data accumulates over conversation

- [ ] 0004-006-001-02 - CHUNK - Profile extraction from conversations
  - SUB-TASKS:
    - Create extraction patterns/logic for common profile fields
    - Extract name, email, phone, address components from messages
    - Update profile automatically when detected
    - Log profile updates for transparency
    - Acceptance: Profile builds up as customer shares information

### [ ] 0004-006-002 - TASK - Email-Based Session Linking (Basic)
- [ ] 0004-006-002-01 - CHUNK - Email matching logic
  - SUB-TASKS:
    - Detect when same email appears in different sessions
    - Flag potential profile merging opportunities
    - Log email collision events for future manual review
    - Design schema for future automated merging
    - Acceptance: Email collisions detected and logged

## 0004-007 - FEATURE - Code Organization & Maintainability

### [ ] 0004-007-001 - TASK - Service Layer Architecture
- [ ] 0004-007-001-01 - CHUNK - Dependency injection setup
  - SUB-TASKS:
    - Organize services with clear separation of concerns
    - Session management, message handling, LLM tracking, profiles
    - Create service factory/container pattern
    - Update main.py to use services instead of inline logic
    - Acceptance: Clean separation between routes, services, models

- [ ] 0004-007-001-02 - CHUNK - Error handling & logging
  - SUB-TASKS:
    - Add database error handling in all services
    - Enhance logging with session_id context
    - Add retry logic for transient DB failures
    - Create consistent error response patterns
    - Acceptance: Robust error handling, traceable logs

## 0004-008 - FEATURE - Testing & Validation

### [ ] 0004-008-001 - TASK - Basic Testing
- [ ] 0004-008-001-01 - CHUNK - Database testing setup
  - SUB-TASKS:
    - Set up test database configuration
    - Create fixtures for test data
    - Test all CRUD operations on models
    - Test session lifecycle and resumption
    - Acceptance: Core persistence functionality verified

- [ ] 0004-008-001-02 - CHUNK - Integration testing
  - SUB-TASKS:
    - Test modified chat endpoints with persistence
    - Verify session resumption flow end-to-end
    - Test profile data accumulation scenarios
    - Validate cost tracking accuracy
    - Acceptance: Complete chat persistence flow works

## Configuration Updates

### Docker Configuration (docker-compose.dev.yml)
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:17.6-alpine
    environment:
      POSTGRES_DB: salient_dev
      POSTGRES_USER: salient_user
      POSTGRES_PASSWORD: salient_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U salient_user -d salient_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  adminer:
    image: adminer:5.3.0
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    environment:
      ADMINER_DEFAULT_SERVER: postgres
      ADMINER_DESIGN: pepa-linha-dark

  redis:
    image: redis:8.2.1-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### Database Configuration (app.yaml)
```yaml
database:
  # Database URL is loaded from DATABASE_URL environment variable for security
  # Example: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
  pool_size: 20
  max_overflow: 0
  pool_timeout: 30

session:
  cookie_name: "salient_session"
  cookie_max_age: 604800  # 7 days
  cookie_secure: false    # true in production
  cookie_httponly: true
  cookie_samesite: "lax"

redis:
  # Redis URL is loaded from REDIS_URL environment variable for security
  # Example: REDIS_URL=redis://localhost:6379/0
  session_db: 1
  cache_db: 2
```

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://salient_user:salient_pass@localhost:5432/salient_dev

# Redis (for future session storage and caching)
REDIS_URL=redis://localhost:6379/0

# Development settings
ENV=development
DEBUG=true
```

### Development Scripts
```bash
# scripts/dev-setup.sh
#!/bin/bash
echo "Starting development environment..."
docker-compose -f docker-compose.dev.yml up -d
echo "Waiting for services to be ready..."
sleep 10
echo "Running database migrations..."
cd backend && alembic upgrade head
echo "Development environment ready!"
echo "- PostgreSQL: localhost:5432"
echo "- Adminer: http://localhost:8080"
echo "- Redis: localhost:6379"

# scripts/dev-reset.sh
#!/bin/bash
echo "Resetting development database..."
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres
sleep 5
cd backend && alembic upgrade head
echo "Database reset complete!"
```

## Definition of Done
- [x] Database schema created via Alembic migrations
- [x] Session creation, lookup, and resumption working
- [x] Chat messages persist and load on session resume  
- [x] LLM requests tracked with cost/usage data
- [x] Profile data accumulates incrementally
- [x] Email collision detection in place
- [x] Existing chat UI gains persistence transparently
- [x] Service layer cleanly organized and maintainable
- [x] Basic testing coverage for persistence flows

## 0004-009 - FEATURE - Code Quality & Standards Compliance

### [x] 0004-009-001 - TASK - Python Code Standards Compliance
- [x] 0004-009-001-01 - CHUNK - Database models code quality
  - SUB-TASKS:
    - Review `backend/app/models/session.py` for PEP 8 compliance
    - Add comprehensive docstrings following Google style
    - Ensure proper type hints and imports organization
    - Add business context comments for relationships
    - Acceptance: Model files fully compliant with coding standards
  - STATUS: Completed — Enhanced session.py with comprehensive module documentation, modern SQLAlchemy 2.0 syntax with Mapped type hints, detailed class docstrings following Google style, business context comments for all fields and relationships, and security-focused documentation. All linting passes and imports work correctly.

- [x] 0004-009-001-02 - CHUNK - Services layer code quality
  - SUB-TASKS:
    - Review `backend/app/services/session_service.py` for standards compliance
    - Add comprehensive class and method docstrings
    - Ensure proper error handling patterns
    - Add business logic comments and explanations
    - Acceptance: Service files demonstrate best practices
  - STATUS: Completed — Enhanced session_service.py with comprehensive module documentation, detailed class and method docstrings following Google style, enhanced security documentation for session key generation, complete business logic comments, and improved error handling patterns. Also fixed README startup instructions and cleaned up incorrect directory structure.

- [x] 0004-009-001-03 - CHUNK - Database service code quality
  - SUB-TASKS:
    - Review `backend/app/database.py` for compliance
    - Add comprehensive module and class documentation
    - Enhance connection management comments
    - Ensure proper async patterns documentation
    - Acceptance: Database service exemplifies quality standards
  - STATUS: Completed — Enhanced database.py with comprehensive module documentation explaining architecture and usage patterns, detailed class docstrings following Google style with extensive business context, complete method documentation including security and performance considerations, enhanced import organization and type hints, detailed error handling documentation, and comprehensive function-level documentation for all global functions including FastAPI dependency injection patterns.

- [x] 0004-009-001-04 - CHUNK - Configuration module code quality
  - SUB-TASKS:
    - Review `backend/app/config.py` for standards compliance
    - Add security-focused comments for environment variables
    - Document configuration patterns and validation
    - Enhance module-level documentation
    - Acceptance: Configuration module demonstrates security best practices
  - STATUS: Completed — Enhanced config.py with comprehensive module documentation explaining security-first design and configuration sources, detailed function docstrings following Google style with extensive security enforcement documentation, complete validation process documentation with graceful error handling, enhanced import organization and alphabetical ordering, detailed security-focused comments for all environment variable requirements, complete configuration loading process documentation, and comprehensive caching strategy explanation with performance considerations.

- [x] 0004-009-001-05 - CHUNK - Middleware code quality
  - SUB-TASKS:
    - Review `backend/app/middleware/simple_session_middleware.py`
    - Add comprehensive middleware documentation
    - Document async context management decisions
    - Explain session handling patterns
    - Acceptance: Middleware code exemplifies FastAPI best practices
  - STATUS: Completed — Enhanced simple_session_middleware.py with comprehensive module documentation explaining async context isolation and session lifecycle management, detailed class docstrings following Google style with extensive architecture decision documentation, complete method documentation including security features and performance optimizations, enhanced import organization and alphabetical ordering, detailed async context management comments explaining greenlet isolation strategy, comprehensive session handling pattern documentation with security considerations, and complete helper function documentation with usage examples and safety features.

- [x] 0004-009-001-06 - CHUNK - Main application code quality
  - SUB-TASKS:
    - Review `backend/app/main.py` for standards compliance
    - Add endpoint documentation and error handling comments
    - Document routing patterns and middleware integration
    - Enhance FastAPI application structure documentation
    - Acceptance: Main application file demonstrates clean architecture
  - STATUS: Completed — Enhanced main.py with comprehensive module documentation explaining layered architecture and production readiness features, detailed application lifecycle management with lifespan pattern documentation, complete endpoint documentation with security considerations and monitoring integration, enhanced import organization and alphabetical ordering, detailed FastAPI application structure comments with middleware configuration, comprehensive routing pattern documentation with session handling, and complete error handling documentation with monitoring and debugging capabilities.

### [ ] 0004-009-002 - TASK - Code Quality Tools Setup
- [ ] 0004-009-002-01 - CHUNK - Linting and formatting configuration
  - SUB-TASKS:
    - Add `black`, `ruff`, `mypy` to requirements-dev.txt
    - Create `pyproject.toml` with tool configurations
    - Set up pre-commit hooks for automated quality checks
    - Document code quality workflow in README
    - Acceptance: Automated code quality enforcement in place

- [ ] 0004-009-002-02 - CHUNK - Code quality validation
  - SUB-TASKS:
    - Run `black` on all Python files for formatting
    - Run `ruff` for linting and import organization
    - Run `mypy` for type checking compliance
    - Fix any issues identified by quality tools
    - Acceptance: All Python code passes quality tool checks

## 0004-010 - FEATURE - Chat UI Copy Functionality

### [x] 0004-010-001 - TASK - Add Copy Functionality to Main Chat Interface
- [x] 0004-010-001-01 - CHUNK - Copy button implementation
  - SUB-TASKS:
    - Copy chat-copy.svg icon from web/public/widget/ to backend/static/
    - Add copy button HTML structure to bot messages in index.html
    - Implement copy button CSS styling (hover states, positioning, transitions)
    - Add JavaScript copy functionality with clipboard API and fallback
    - Include visual feedback (toast notification or temporary indicator)
    - Acceptance: Copy buttons appear on bot messages with proper styling
  - STATUS: Completed — Copied SVG icon to backend/static/, implemented complete CSS styling with hover states and transitions, added comprehensive JavaScript copy functionality with modern Clipboard API and legacy fallback, integrated toast notification system with smooth animations, and configured FastAPI static file serving with proper middleware exclusions.
  
- [x] 0004-010-001-02 - CHUNK - Copy functionality integration
  - SUB-TASKS:
    - Integrate copy buttons with existing message rendering system
    - Handle both streaming and non-streaming message copying
    - Store raw message content for accurate copying (preserve markdown)
    - Ensure copy functionality works with markdown-rendered content
    - Add error handling for copy failures with user feedback
    - Acceptance: Users can copy bot responses to clipboard successfully
  - STATUS: Completed — Integrated copy buttons with appendMessage() function for automatic addition to all bot messages, implemented comprehensive raw content storage in data-raw attributes for both streaming and non-streaming scenarios, ensured markdown source preservation for accurate copying, added robust error handling with user-friendly feedback, and verified compatibility with both SSE streaming and POST fallback methods.

- [x] 0004-010-001-03 - CHUNK - UI polish and accessibility
  - SUB-TASKS:
    - Add hover states and visual feedback for copy buttons
    - Implement ARIA labels and accessibility attributes
    - Add keyboard navigation support for copy functionality
    - Ensure consistent styling with existing chat interface
    - Test copy functionality across different browsers
    - Acceptance: Copy feature is fully accessible and polished
  - STATUS: Completed — Enhanced hover states with smooth transitions, focus indicators, and visual feedback, implemented comprehensive ARIA labels and accessibility attributes including proper tabindex, added full keyboard navigation support (Enter/Space key activation), ensured consistent styling with existing chat interface, added responsive design for mobile devices, and implemented cross-browser compatibility with modern Clipboard API and legacy execCommand fallback.

### Technical Implementation Notes

**📋 Copy Button Design Pattern (from widget analysis):**
- **Icon**: Uses `chat-copy.svg` - clean clipboard icon with CC Attribution-ShareAlike license
- **Positioning**: Absolute positioned bottom-right of bot messages
- **Styling**: Semi-transparent background, subtle border, opacity transitions
- **Behavior**: Low opacity by default, full opacity on message hover or button focus
- **Feedback**: Toast notification showing "Copied" or "Copy failed"

**🔧 Technical Architecture:**
- **Raw Content Storage**: Store original text in `data-raw` attribute on message containers
- **Clipboard API**: Primary method using `navigator.clipboard.writeText()`
- **Fallback Method**: Temporary textarea selection with `document.execCommand('copy')`
- **Integration Points**: 
  - `appendMessage()` function for adding copy buttons
  - Stream completion handler for finalizing copyable content
  - Markdown rendering system for preserving source text

**📱 Browser Compatibility:**
- **Modern Browsers**: Clipboard API with async/await
- **Legacy Support**: Document.execCommand fallback for older browsers
- **Security Context**: HTTPS required for Clipboard API (development localhost exemption)
- **Error Handling**: Graceful degradation with user-visible error messages

**🎨 Visual Design Specifications:**
```css
.copy-btn {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: rgba(255,255,255,0.9);
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 4px;
  width: 22px;
  height: 22px;
  opacity: 0.2;
  transition: opacity 0.15s ease, transform 0.1s ease;
  cursor: pointer;
}

.msg.bot:hover .copy-btn,
.copy-btn:focus {
  opacity: 1;
}

.copy-btn:active {
  transform: scale(0.96);
}
```

**🚀 Implementation Benefits:**
- **User Experience**: Quick access to copy AI responses for external use
- **Accessibility**: Keyboard navigation and screen reader support
- **Consistency**: Matches existing widget functionality and styling
- **Performance**: Lightweight implementation with minimal JavaScript overhead
- **Maintainability**: Reuses existing patterns from chat widget codebase

## 0004-011 - FEATURE - Session Security Hardening & Best Practices Compliance

### Security Context & Current State Analysis

Our current session management implementation follows modern best practices with HttpOnly cookies, but research into 2024 security standards reveals opportunities for hardening and full compliance with industry recommendations.

**Current Implementation Strengths:**
- ✅ HttpOnly cookies preventing XSS access to session tokens
- ✅ SameSite="lax" providing CSRF protection 
- ✅ Configurable expiration and secure cookie handling
- ✅ Session isolation with unique keys per user

**Security Gaps Identified:**
- ⚠️ Secure flag disabled in development (should be environment-aware)
- ⚠️ SameSite="lax" could be stricter for maximum security
- ⚠️ Missing session rotation mechanisms for enhanced protection
- ⚠️ No comprehensive session activity monitoring
- ⚠️ Limited session invalidation on security events

**Industry Best Practices (OWASP 2024, Security Research):**
Based on comprehensive analysis of current frontend security practices, including OWASP guidelines, security expert recommendations, and industry consensus from leading security blogs and research, the following enhancements will bring us to gold-standard session security:

1. **Environment-Aware Security Flags**: Production-grade cookie security settings
2. **Enhanced CSRF Protection**: Stricter SameSite policies with fallback handling
3. **Session Rotation**: Periodic session key refresh for breach mitigation
4. **Security Event Monitoring**: Activity tracking and anomaly detection
5. **Graceful Degradation**: Fallback strategies for edge cases and security events

This feature ensures our session management exceeds industry standards while maintaining excellent user experience and operational reliability.

### [ ] 0004-011-001 - TASK - Production Security Configuration

- [ ] 0004-011-001-01 - CHUNK - Environment-aware cookie security
  - SUB-TASKS:
    - Update cookie configuration to use environment-based Secure flag
    - Implement production detection in session middleware
    - Add HTTPS enforcement for production environments
    - Configure automatic security flag setting based on deployment context
    - Add validation for security requirements in production
    - Acceptance: Cookies automatically secure in production, flexible in development

- [ ] 0004-011-001-02 - CHUNK - Enhanced CSRF protection
  - SUB-TASKS:
    - Upgrade SameSite policy from "lax" to "strict" for maximum protection
    - Implement graceful fallback for legitimate cross-site scenarios
    - Add CSRF token validation for state-changing operations
    - Configure middleware to handle SameSite compatibility issues
    - Test cross-origin scenarios and iframe compatibility
    - Acceptance: Maximum CSRF protection without breaking legitimate use cases

### [ ] 0004-011-002 - TASK - Session Lifecycle Security Enhancements

- [ ] 0004-011-002-01 - CHUNK - Session rotation implementation
  - SUB-TASKS:
    - Implement periodic session key rotation mechanism
    - Add configurable rotation intervals based on security requirements
    - Create seamless rotation without user experience disruption
    - Implement rotation on security-sensitive events (login, privilege changes)
    - Add rotation logging and monitoring for security audits
    - Acceptance: Session keys rotate automatically with transparent user experience

- [ ] 0004-011-002-02 - CHUNK - Session invalidation and cleanup
  - SUB-TASKS:
    - Implement comprehensive session cleanup on logout
    - Add session invalidation for security events (failed auth attempts)
    - Create expired session cleanup background processes
    - Implement session conflict detection (same user, multiple devices)
    - Add administrative session termination capabilities
    - Acceptance: Complete session lifecycle management with security event handling

### [ ] 0004-011-003 - TASK - Security Monitoring & Observability

- [ ] 0004-011-003-01 - CHUNK - Session activity monitoring
  - SUB-TASKS:
    - Implement session activity tracking and logging
    - Add anomaly detection for suspicious session patterns
    - Create metrics for session security health monitoring
    - Implement concurrent session detection and alerts
    - Add session fingerprinting for enhanced security
    - Acceptance: Comprehensive session activity visibility and threat detection

- [ ] 0004-011-003-02 - CHUNK - Security audit and compliance reporting
  - SUB-TASKS:
    - Create security audit logging for session operations
    - Implement compliance reporting for session management
    - Add security metrics dashboard for operational monitoring
    - Create security incident response procedures for session events
    - Document security configuration and operational procedures
    - Acceptance: Full security observability and compliance documentation

### Technical Implementation Specifications

**🔒 Enhanced Cookie Configuration:**
```python
# Production-grade cookie security
cookie_config = {
    "httponly": True,
    "secure": is_production_environment(),
    "samesite": "strict",  # Maximum CSRF protection
    "max_age": get_session_lifetime(),
    "domain": get_cookie_domain(),
    "path": "/"
}
```

**🔄 Session Rotation Architecture:**
```python
# Automatic session rotation
class SessionRotationManager:
    def should_rotate(self, session):
        return (
            session.age > rotation_interval or
            session.risk_score > threshold or
            security_event_triggered
        )
    
    def rotate_session(self, old_session):
        new_session = create_new_session()
        transfer_session_data(old_session, new_session)
        invalidate_old_session(old_session)
        return new_session
```

**📊 Security Monitoring Integration:**
```python
# Session security monitoring
class SessionSecurityMonitor:
    def track_activity(self, session_id, event):
        log_security_event(session_id, event)
        detect_anomalies(session_id)
        update_risk_score(session_id)
    
    def detect_threats(self, session_id):
        return analyze_patterns([
            concurrent_sessions,
            rapid_requests,
            location_changes,
            device_fingerprint_changes
        ])
```

**🎯 Security Configuration Matrix:**

| Environment | Secure Flag | SameSite | Rotation | Monitoring |
|-------------|-------------|----------|----------|------------|
| Development | False | lax | 24h | Basic |
| Staging | True | strict | 12h | Enhanced |
| Production | True | strict | 6h | Full |

**🛡️ Compliance Standards Addressed:**
- **OWASP Session Management**: Complete compliance with latest cheat sheet
- **Industry Best Practices**: Based on 2024 security research and expert consensus
- **GDPR/Privacy**: Enhanced user control and data protection
- **SOC 2**: Comprehensive audit trails and security controls
- **Zero Trust**: Continuous validation and minimal trust assumptions

**📈 Expected Security Improvements:**
- **XSS Protection**: Enhanced with stricter cookie policies
- **CSRF Protection**: Maximum protection with SameSite=strict
- **Session Hijacking**: Mitigated through rotation and monitoring
- **Breach Impact**: Limited through automatic rotation and invalidation
- **Compliance**: Full adherence to 2024 security standards

**🚀 Implementation Benefits:**
- **Security Posture**: Industry-leading session security implementation
- **Operational Excellence**: Comprehensive monitoring and incident response
- **User Trust**: Transparent security without UX degradation
- **Compliance Ready**: Meets regulatory and audit requirements
- **Future-Proof**: Aligned with evolving security standards

## 0004-012 - FEATURE - Conversation Hierarchy & Management

### Scope & Architecture

**Problem Statement**: Current system stores all messages in a flat session structure, making it difficult to organize extended interactions, provide conversation summaries, or manage long-term chat history. Users need the ability to organize their interactions into discrete conversations with proper archival and summary capabilities.

**Solution Overview**: Introduce a conversation layer between sessions and messages, providing hierarchical organization with automated summarization and lifecycle management.

### Database Schema Extensions

#### New Table: Conversations
```sql
conversations:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  title (VARCHAR, nullable)          -- User-edited or LLM-generated title
  default_title (VARCHAR)            -- Auto-generated default title (e.g., "New Conversation")
  summary (TEXT, nullable)           -- AI-generated conversation summary
  status (VARCHAR)                   -- 'active', 'archived'
  message_count (INTEGER)            -- Cached count for UI performance
  created_at (TIMESTAMP)
  updated_at (TIMESTAMP)             -- Last message or activity
  last_visited_at (TIMESTAMP)        -- Last time user accessed this conversation
  archived_at (TIMESTAMP, nullable)  -- When conversation was archived
  metadata (JSONB)                   -- Topics, tags, summary metadata
```

#### Updated Messages Table
```sql
-- Add conversation_id foreign key to existing messages table
ALTER TABLE messages ADD COLUMN conversation_id (GUID, FK → conversations.id);
-- Update existing messages to belong to default conversations
-- Add index for conversation-based message retrieval (to be added to datamodel.md)
-- CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);
```

#### Configuration Schema (app.yaml)
```yaml
conversations:
  auto_summary_threshold: 10         # Number of messages before generating summary
  archive_unvisited_after_days: 30   # Days before auto-archiving unvisited conversations
  delete_archived_after_days: 365    # Days before deleting archived conversations
  max_title_length: 100              # Maximum characters for conversation titles
  enable_user_titles: true           # Allow users to edit conversation titles
  enable_llm_title_revision: true    # Allow LLM to revise conversation titles
  summary_provider: "openai"         # LLM provider for generating summaries
  summary_model: "gpt-4o-mini"       # Cost-effective model for summaries
  title_revision_model: "gpt-4o-mini" # Model for conversation title generation/revision
```

### [ ] 0004-012-001 - TASK - Database Schema & Model Updates

- [ ] 0004-012-001-01 - CHUNK - Conversation model implementation
  - SUB-TASKS:
    - Create `backend/app/models/conversation.py` with full SQLAlchemy model
    - Add relationships: `session → conversations → messages`
    - Implement status enum: active, completed, archived
    - Add indexes for performance: session_id, status, updated_at
    - Create migration: `alembic revision --autogenerate -m "Add conversations hierarchy"`
    - Acceptance: Conversation model complete with proper relationships

- [ ] 0004-012-001-02 - CHUNK - Data migration for existing messages
  - SUB-TASKS:
    - Create migration script to assign existing messages to default conversations
    - Group messages by session and time gaps to create logical conversations
    - Generate initial conversation titles based on first message content
    - Update message foreign keys to reference conversations
    - Add data validation and rollback procedures
    - Acceptance: All existing messages properly organized into conversations

### [ ] 0004-012-002 - TASK - Conversation Service Layer

- [ ] 0004-012-002-01 - CHUNK - Conversation management service
  - SUB-TASKS:
    - Create `backend/app/services/conversation_service.py`
    - Implement `create_conversation()`, `get_session_conversations()`, `update_conversation()`
    - Add conversation lifecycle management (active → archived)
    - Implement auto-conversation creation on first site visit
    - Add conversation title management (user editing and LLM revision)
    - Implement auto-archival based on `last_visited_at` and configuration
    - Add `update_last_visited()` tracking for conversation access
    - Acceptance: Complete conversation CRUD operations with visit-based lifecycle management

- [ ] 0004-012-002-02 - CHUNK - Message service integration
  - SUB-TASKS:
    - Update `message_service.py` to work with conversation hierarchy
    - Modify `save_message()` to assign messages to active conversation
    - Update `get_session_messages()` to retrieve by conversation
    - Add `get_conversation_messages()` for conversation-specific retrieval
    - Implement conversation switching and message context management
    - Acceptance: Message operations seamlessly work with conversation structure

### [ ] 0004-012-003 - TASK - Conversation Summarization

- [ ] 0004-012-003-01 - CHUNK - AI-powered conversation summarization and title management
  - SUB-TASKS:
    - Create `backend/app/services/summary_service.py`
    - Implement conversation summarization using configured LLM (triggered by message count from app.yaml)
    - Add conversation title generation and revision using LLM
    - Create title revision API endpoint for user-requested title updates
    - Create summary templates for different conversation types
    - Add cost tracking for summarization and title generation requests
    - Acceptance: Conversations automatically generate summaries and support title revision

- [ ] 0004-012-003-02 - CHUNK - Summary optimization and caching
  - SUB-TASKS:
    - Implement incremental summarization for long conversations
    - Add summary caching to avoid redundant LLM calls
    - Create summary quality validation and fallback logic
    - Add manual summary regeneration capability
    - Implement summary versioning for audit trails
    - Acceptance: Efficient, high-quality summarization with cost optimization

### [ ] 0004-012-004 - TASK - Archive & Lifecycle Management

- [ ] 0004-012-004-01 - CHUNK - Conversation archival system
  - SUB-TASKS:
    - Implement automatic archival based on `last_visited_at` and app.yaml `archive_unvisited_after_days`
    - Add manual archival controls for users
    - Create archived conversation storage optimization
    - Implement archive restoration functionality (move back to active)
    - Add archive notification and confirmation workflows
    - Track conversation visits to update `last_visited_at` timestamp
    - Acceptance: Conversations automatically archived based on visit patterns with user control options

- [ ] 0004-012-004-02 - CHUNK - Data retention and cleanup
  - SUB-TASKS:
    - Implement scheduled cleanup of archived conversations
    - Add configurable retention policies per conversation type
    - Create data export functionality before deletion
    - Implement soft delete with recovery period
    - Add compliance reporting for data retention
    - Acceptance: Automated cleanup with compliance and recovery features

### [ ] 0004-012-005 - TASK - Frontend UI Updates

- [ ] 0004-012-005-01 - CHUNK - Conversation list sidebar
  - SUB-TASKS:
    - Add conversation list panel to main chat interface
    - Implement collapsible conversation history with titles and summaries
    - Add conversation status indicators (active, completed, archived)
    - Create conversation search and filtering capabilities
    - Add conversation creation and switching functionality
    - Acceptance: Users can navigate and manage conversations intuitively

- [ ] 0004-012-005-02 - CHUNK - Conversation management controls
  - SUB-TASKS:
    - Add conversation title editing functionality (click to edit)
    - Add "Ask AI to revise title" button for LLM-powered title generation
    - Implement manual conversation archival
    - Create conversation sharing and export features
    - Add conversation deletion with confirmation
    - Implement conversation restore from archive
    - Add visit tracking when user switches between conversations
    - Acceptance: Complete conversation management with intuitive title editing and AI assistance

### [ ] 0004-012-006 - TASK - API Updates & Integration

- [ ] 0004-012-006-01 - CHUNK - Conversation API endpoints
  - SUB-TASKS:
    - Add `GET /api/conversations` for session conversation list
    - Add `POST /api/conversations` for manual conversation creation
    - Add `PUT /api/conversations/{id}` for conversation updates (title, status)
    - Add `PUT /api/conversations/{id}/title` for user title editing
    - Add `POST /api/conversations/{id}/revise-title` for LLM title revision
    - Add `POST /api/conversations/{id}/archive` for manual archival
    - Add `POST /api/conversations/{id}/restore` for archive restoration
    - Add `DELETE /api/conversations/{id}` for conversation deletion
    - Add `POST /api/conversations/{id}/summary` for manual summarization
    - Add visit tracking on conversation access
    - Acceptance: Complete REST API for conversation management with title revision

- [ ] 0004-012-006-02 - CHUNK - Chat endpoint updates
  - SUB-TASKS:
    - Update `POST /chat` to work with active conversation context
    - Update `GET /events/stream` to maintain conversation continuity
    - Auto-create first conversation when new user visits site
    - Add conversation switching without losing context
    - Update chat history loading to respect conversation boundaries
    - Update `last_visited_at` timestamp when conversation is accessed
    - Add conversation metadata to all chat responses
    - Acceptance: Chat functionality seamlessly integrated with conversations and visit tracking

### Technical Architecture

**🏗️ Hierarchy Structure:**
```
Session (User Browser Instance)
├── Conversation 1 (Topic: Product Inquiry)
│   ├── Message 1 (Human: "Tell me about your apples")
│   ├── Message 2 (Assistant: "We grow premium organic apples...")
│   └── Summary: "Customer inquiring about apple varieties and pricing"
├── Conversation 2 (Topic: Order Placement)
│   ├── Message 3 (Human: "I'd like to place an order")
│   └── Message 4 (Assistant: "I'd be happy to help with your order...")
└── Conversation 3 (Topic: Support Request - Archived)
```

**📊 Conversation Lifecycle:**
1. **Active**: Currently receiving messages or recently visited, displayed prominently
2. **Archived**: Unvisited conversations (auto-archived after configurable days) or manually archived, collapsed view, scheduled for cleanup
3. **Deleted**: Permanently removed after retention period in archive

**🎯 UI Organization Strategy:**
- **Primary View**: Active conversation with full message history
- **Sidebar**: Collapsible list of conversations (active → archived)
- **Title Management**: Click to edit titles or "Ask AI to revise title" button
- **Search**: Conversation titles, summaries, and message content
- **Archive View**: Separate section for archived conversations with restore options
- **Auto-Creation**: New conversation automatically created on first site visit

**⚡ Performance Optimizations:**
- **Lazy Loading**: Load conversation messages on demand
- **Summary Caching**: Cache conversation summaries for quick display
- **Pagination**: Paginate conversation lists for sessions with many conversations
- **Indexing**: Optimize database queries for conversation retrieval

**🔒 Security & Privacy:**
- **Session Isolation**: Conversations scoped to sessions, no cross-session access
- **Archive Encryption**: Archived conversations encrypted at rest
- **Deletion Compliance**: GDPR-compliant deletion with audit trails
- **Access Logging**: Track conversation access for security monitoring

### Business Benefits

**👥 User Experience:**
- **Organization**: Easy navigation through conversation history
- **Context**: Clear conversation boundaries and summaries
- **Search**: Find specific conversations quickly
- **Clean Interface**: Reduced clutter with archived conversations

**📈 Business Value:**
- **Customer Insights**: Conversation summaries reveal customer needs
- **Data Management**: Organized data for analytics and reporting
- **Cost Control**: Automated archival reduces storage costs
- **Compliance**: Proper data retention and deletion policies

**🔧 Development Benefits:**
- **Scalability**: Hierarchical structure supports growth
- **Performance**: Optimized queries and data organization
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Foundation for advanced features (topics, tags, analytics)

This feature transforms the chat system from a simple message log into a sophisticated conversation management platform while maintaining backward compatibility and excellent performance.

---

## Agent Context Management (Pydantic AI Integration)

### [ ] 0004-013 - FEATURE - Agent Context Management
> Enhance chat memory system to support Pydantic AI agent context and conversation management

#### [ ] 0004-013-001 - TASK - Agent Conversation Context
- [ ] 0004-013-001-01 - CHUNK - LLM conversation context for agents
  - Extend conversation history to include agent-specific context windows
  - Implement context filtering and formatting for different agent types
  - Add configurable context window sizes per agent
  - Create context relevance scoring and truncation algorithms
  - **Acceptance**: Agents receive appropriately sized, relevant conversation context
  - **Dependencies**: Requires 0005-001 (Pydantic AI Framework Setup)

- [ ] 0004-013-001-02 - CHUNK - Agent memory persistence
  - Implement agent-specific memory storage and retrieval
  - Add conversation state tracking across agent interactions
  - Create agent context serialization and deserialization
  - Implement context restoration after agent restarts
  - **Acceptance**: Agents maintain context across conversations and sessions

- [ ] 0004-013-001-03 - CHUNK - Multi-agent context coordination
  - Implement context sharing and handoff between agents
  - Add agent delegation tracking and context preservation
  - Create context conflict resolution for overlapping agents
  - Implement context isolation for agent-specific interactions
  - **Acceptance**: Context preserved during agent handoffs and delegation

#### [ ] 0004-013-002 - TASK - Agent Session Integration
- [ ] 0004-013-002-01 - CHUNK - Agent-aware session management
  - Extend session model to track active agents and their states
  - Implement agent assignment and lifecycle management per session
  - Add agent preference and configuration storage
  - Create agent session analytics and usage tracking
  - **Acceptance**: Sessions properly track agent interactions and states

- [ ] 0004-013-002-02 - CHUNK - Agent conversation linking
  - Implement agent-specific conversation categorization
  - Add conversation routing based on agent capabilities
  - Create conversation summary generation with agent context
  - Implement agent-specific conversation archival rules
  - **Acceptance**: Conversations properly linked to appropriate agents

#### [ ] 0004-013-003 - TASK - Agent Configuration Management
- [ ] 0004-013-003-01 - CHUNK - Dynamic agent configuration
  - Implement runtime agent configuration loading from database
  - Add agent configuration versioning and rollback support
  - Create agent feature flag and A/B testing framework
  - Implement agent configuration hot-reloading without restarts
  - **Acceptance**: Agent configurations updated dynamically

- [ ] 0004-013-003-02 - CHUNK - Agent performance tracking
  - Implement agent response time and quality metrics
  - Add agent conversation success rate tracking
  - Create agent usage analytics and cost attribution
  - Implement agent performance optimization recommendations
  - **Acceptance**: Agent performance properly monitored and optimized

### Technical Architecture - Agent Context Integration

#### Database Schema Extensions for Agents
```sql
-- Agent instance tracking per session
agent_sessions:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  agent_type (VARCHAR)           -- sales, digital_expert, support
  agent_config (JSONB)           -- agent-specific configuration
  context_window_size (INTEGER)  -- max context tokens for this agent
  active_since (TIMESTAMP)
  last_interaction (TIMESTAMP)
  performance_metrics (JSONB)

-- Agent conversation context management  
agent_contexts:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  conversation_id (GUID, FK → conversations.id)
  agent_type (VARCHAR)
  context_data (JSONB)           -- agent-specific context
  context_version (INTEGER)      -- for context evolution tracking
  created_at (TIMESTAMP)
  expires_at (TIMESTAMP)

-- Agent handoff and delegation tracking
agent_handoffs:
  id (GUID, PK)
  session_id (GUID, FK → sessions.id)
  from_agent_type (VARCHAR)
  to_agent_type (VARCHAR)
  handoff_reason (VARCHAR)
  context_transferred (JSONB)
  handoff_timestamp (TIMESTAMP)
  success_score (FLOAT)          -- quality of handoff
```

#### Agent Context Management Service
```python
class AgentContextService:
    async def get_conversation_context(
        self, 
        session_id: UUID, 
        agent_type: str,
        max_tokens: int = 4000
    ) -> AgentContext:
        """Retrieve and format conversation context for specific agent."""
        # Filter messages based on agent relevance
        # Apply context window size limits
        # Format context for agent consumption
        pass
    
    async def store_agent_interaction(
        self,
        session_id: UUID,
        agent_type: str,
        interaction_data: dict
    ) -> None:
        """Store agent-specific interaction data for future context."""
        pass
    
    async def handle_agent_handoff(
        self,
        session_id: UUID,
        from_agent: str,
        to_agent: str,
        handoff_context: dict
    ) -> HandoffResult:
        """Manage context transfer between agents."""
        pass
```

#### Integration with Pydantic AI Agents
```python
@dataclass
class AgentDependencies:
    session_id: UUID
    conversation_context: ConversationContext
    agent_memory: AgentMemory
    performance_tracker: PerformanceTracker

# Context retrieval for agent dependency injection
async def get_agent_dependencies(session_id: UUID, agent_type: str) -> AgentDependencies:
    context_service = AgentContextService()
    context = await context_service.get_conversation_context(session_id, agent_type)
    memory = await context_service.get_agent_memory(session_id, agent_type)
    tracker = PerformanceTracker(session_id, agent_type)
    
    return AgentDependencies(
        session_id=session_id,
        conversation_context=context,
        agent_memory=memory,
        performance_tracker=tracker
    )
```

This agent context management feature provides the foundational infrastructure for Pydantic AI agents to maintain sophisticated conversation context, memory, and multi-agent coordination while building on the existing chat memory and persistence system.

---

## Success Criteria
1. **Restart-safe chats**: Browser refresh loads previous conversation
2. **Session continuity**: Same browser session resumes automatically
3. **Cost visibility**: Usage tracking shows token and cost consumption
4. **Profile growth**: Customer information builds up over conversation
5. **Clean codebase**: Services separated, endpoints maintainable
6. **Code Quality**: All Python code complies with project standards
7. **Conversation Organization**: Users can navigate multiple conversations per session
8. **Automatic Summaries**: Conversations generate meaningful AI summaries
9. **Archive Management**: Old conversations automatically archived and cleaned up
10. **UI Navigation**: Intuitive conversation switching and management interface
