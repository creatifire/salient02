# Epic 0004 - Chat Memory & Persistence

> Goal: Add persistent chat history and session management to the existing baseline system. Messages and sessions stored in Postgres, with automatic session resumption and profile data accumulation.

## Scope & Approach
- **Single-tenant mode**: No `tenants` table for now; simplify schema
- **Modify existing endpoints**: Enhance current `POST /chat` and `GET /events/stream` to use database
- **Session resumption**: Automatic based on browser session cookie/ID matching database
- **Incremental profiles**: Collect profile data (name, email, preferences) as it comes during conversations
- **Email linking**: Only when same email provided in different sessions (post-cache-clear scenario)
- **Code organization**: Separate related functionality into maintainable modules

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
```sql
CREATE INDEX idx_sessions_session_key ON sessions(session_key);
CREATE INDEX idx_sessions_email ON sessions(email) WHERE email IS NOT NULL;
CREATE INDEX idx_messages_session_created ON messages(session_id, created_at);
CREATE INDEX idx_llm_requests_session_created ON llm_requests(session_id, created_at);
CREATE INDEX idx_profiles_session_id ON profiles(session_id);
CREATE INDEX idx_profiles_email ON profiles(email) WHERE email IS NOT NULL;
```

## 0004-001 - FEATURE - Database Setup & Migrations

### [ ] 0004-001-001 - TASK - SQLAlchemy Models & Alembic Setup
- [ ] 0004-001-001-01 - CHUNK - Install and configure Alembic
  - SUB-TASKS:
    - Add `alembic` to requirements.txt if not already present
    - Initialize Alembic in `backend/migrations/`
    - Configure `alembic.ini` and `env.py` for asyncpg connection
    - Set up `backend/app/models/` module structure
    - Acceptance: `alembic init` complete, can connect to DB

- [ ] 0004-001-001-02 - CHUNK - Define SQLAlchemy models
  - SUB-TASKS:
    - Create `backend/app/models/__init__.py`
    - Create `backend/app/models/session.py` (Session model)
    - Create `backend/app/models/message.py` (Message model)  
    - Create `backend/app/models/llm_request.py` (LLMRequest model)
    - Create `backend/app/models/profile.py` (Profile model)
    - Use GUID primary keys, proper relationships, nullable fields
    - Acceptance: Models import cleanly, relationships defined

- [ ] 0004-001-001-03 - CHUNK - Initial migration
  - SUB-TASKS:
    - Generate migration: `alembic revision --autogenerate -m "Initial chat memory schema"`
    - Review and adjust migration file
    - Test migration: `alembic upgrade head`
    - Add sample data insertion for testing
    - Acceptance: Tables created successfully in Postgres

### [ ] 0004-001-002 - TASK - Database Connection & Configuration
- [ ] 0004-001-002-01 - CHUNK - Database configuration
  - SUB-TASKS:
    - Add database settings to `backend/config/app.yaml`
    - Add `DATABASE_URL` to `.env` template
    - Update `backend/app/config.py` to load DB config
    - Create connection pooling setup
    - Acceptance: DB config loads correctly, connection successful

- [ ] 0004-001-002-02 - CHUNK - Database service module
  - SUB-TASKS:
    - Create `backend/app/database.py` with async session management
    - Implement connection pool, session lifecycle
    - Add database health check endpoint
    - Integration with existing health endpoint
    - Acceptance: DB sessions work, health check passes

## 0004-002 - FEATURE - Session Management & Resumption

### [ ] 0004-002-001 - TASK - Session Creation & Lookup
- [ ] 0004-002-001-01 - CHUNK - Session service module
  - SUB-TASKS:
    - Create `backend/app/services/session_service.py`
    - Implement `create_session()`, `get_session_by_key()`, `update_last_activity()`
    - Handle session key generation (secure random)
    - Set browser cookie with session key
    - Acceptance: Sessions created and retrieved by key

- [ ] 0004-002-001-02 - CHUNK - Session middleware integration
  - SUB-TASKS:
    - Create session middleware for FastAPI
    - Auto-create session if none exists
    - Load existing session if valid session key in cookie
    - Update `last_activity_at` on each request
    - Acceptance: Session tracking works transparently

### [ ] 0004-002-002 - TASK - Frontend Session Handling
- [ ] 0004-002-002-01 - CHUNK - Session cookie management
  - SUB-TASKS:
    - Configure secure session cookies (httpOnly, secure, sameSite)
    - Handle session cookie in chat UI
    - Display session status in dev diagnostics
    - Acceptance: Session persistence across browser refreshes

## 0004-003 - FEATURE - Message Persistence & Chat History

### [ ] 0004-003-001 - TASK - Message Storage
- [ ] 0004-003-001-01 - CHUNK - Message service module
  - SUB-TASKS:
    - Create `backend/app/services/message_service.py`
    - Implement `save_message()`, `get_session_messages()`, `get_recent_context()`
    - Handle human, assistant, system message types
    - Store metadata field for future RAG citations
    - Acceptance: Messages saved and retrieved by session

- [ ] 0004-003-001-02 - CHUNK - Chat history loading
  - SUB-TASKS:
    - Load existing messages when session resumes
    - Display chat history in UI on page load
    - Handle empty history gracefully
    - Limit initial history load (e.g., last 50 messages)
    - Acceptance: Previous conversations visible on return

### [ ] 0004-003-002 - TASK - Modify Existing Chat Endpoints
- [ ] 0004-003-002-01 - CHUNK - Update POST /chat endpoint
  - SUB-TASKS:
    - Save human message to database before LLM call
    - Save assistant response after LLM completion
    - Include session context in request logging
    - Maintain existing response format/behavior
    - Acceptance: Chat persists without UI changes

- [ ] 0004-003-002-02 - CHUNK - Update GET /events/stream endpoint  
  - SUB-TASKS:
    - Save assistant message chunks during streaming
    - Handle streaming vs non-streaming message persistence
    - Ensure message completeness on stream end
    - Link to session properly
    - Acceptance: Streamed messages persist correctly

## 0004-004 - FEATURE - LLM Request Tracking

### [ ] 0004-004-001 - TASK - Cost & Usage Tracking
- [ ] 0004-004-001-01 - CHUNK - LLM request service
  - SUB-TASKS:
    - Create `backend/app/services/llm_service.py`
    - Wrap OpenRouter calls with cost tracking
    - Extract token counts, latency, cost from responses
    - Store sanitized request/response data
    - Acceptance: All LLM calls tracked with cost data

- [ ] 0004-004-001-02 - CHUNK - Usage reporting endpoints
  - SUB-TASKS:
    - Add `GET /api/session/{session_id}/usage` endpoint
    - Aggregate cost, token counts, request counts per session
    - Add basic usage display in dev diagnostics
    - Export usage data as JSON
    - Acceptance: Session usage visible and exportable

## 0004-005 - FEATURE - Profile Data Collection

### [ ] 0004-005-001 - TASK - Profile Creation & Updates
- [ ] 0004-005-001-01 - CHUNK - Profile service module
  - SUB-TASKS:
    - Create `backend/app/services/profile_service.py`
    - Implement `create_profile()`, `update_profile()`, `get_session_profile()`
    - Handle incremental profile data updates
    - Support array fields (products_of_interest, services_of_interest)
    - Acceptance: Profile data accumulates over conversation

- [ ] 0004-005-001-02 - CHUNK - Profile extraction from conversations
  - SUB-TASKS:
    - Create extraction patterns/logic for common profile fields
    - Extract name, email, phone, address components from messages
    - Update profile automatically when detected
    - Log profile updates for transparency
    - Acceptance: Profile builds up as customer shares information

### [ ] 0004-005-002 - TASK - Email-Based Session Linking (Basic)
- [ ] 0004-005-002-01 - CHUNK - Email matching logic
  - SUB-TASKS:
    - Detect when same email appears in different sessions
    - Flag potential profile merging opportunities
    - Log email collision events for future manual review
    - Design schema for future automated merging
    - Acceptance: Email collisions detected and logged

## 0004-006 - FEATURE - Code Organization & Maintainability

### [ ] 0004-006-001 - TASK - Service Layer Architecture
- [ ] 0004-006-001-01 - CHUNK - Dependency injection setup
  - SUB-TASKS:
    - Organize services with clear separation of concerns
    - Session management, message handling, LLM tracking, profiles
    - Create service factory/container pattern
    - Update main.py to use services instead of inline logic
    - Acceptance: Clean separation between routes, services, models

- [ ] 0004-006-001-02 - CHUNK - Error handling & logging
  - SUB-TASKS:
    - Add database error handling in all services
    - Enhance logging with session_id context
    - Add retry logic for transient DB failures
    - Create consistent error response patterns
    - Acceptance: Robust error handling, traceable logs

## 0004-007 - FEATURE - Testing & Validation

### [ ] 0004-007-001 - TASK - Basic Testing
- [ ] 0004-007-001-01 - CHUNK - Database testing setup
  - SUB-TASKS:
    - Set up test database configuration
    - Create fixtures for test data
    - Test all CRUD operations on models
    - Test session lifecycle and resumption
    - Acceptance: Core persistence functionality verified

- [ ] 0004-007-001-02 - CHUNK - Integration testing
  - SUB-TASKS:
    - Test modified chat endpoints with persistence
    - Verify session resumption flow end-to-end
    - Test profile data accumulation scenarios
    - Validate cost tracking accuracy
    - Acceptance: Complete chat persistence flow works

## Configuration Updates

### Database Configuration (app.yaml)
```yaml
database:
  url: "postgresql+asyncpg://user:pass@localhost/salient"
  pool_size: 20
  max_overflow: 0
  pool_timeout: 30

session:
  cookie_name: "salient_session"
  cookie_max_age: 604800  # 7 days
  cookie_secure: false    # true in production
  cookie_httponly: true
  cookie_samesite: "lax"
```

### Environment Variables (.env)
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/salient
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

## Success Criteria
1. **Restart-safe chats**: Browser refresh loads previous conversation
2. **Session continuity**: Same browser session resumes automatically
3. **Cost visibility**: Usage tracking shows token and cost consumption
4. **Profile growth**: Customer information builds up over conversation
5. **Clean codebase**: Services separated, endpoints maintainable
