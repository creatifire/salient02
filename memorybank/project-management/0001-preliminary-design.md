# Preliminary Design
## 0001-001 - FEATURE - Database Design

### Scope
- Multi-tenant and single-tenant modes. Separate ingestion app handles website/PDF scraping and indexing into Pinecone; reindexing is out of scope for this app.
- This app reads from Pinecone index(es) and stores all runtime state in Postgres.

### Conventions
- ORM/Migrations/Driver: SQLAlchemy 2.0 ORM + Alembic + asyncpg.
- All primary keys are GUIDs.
- JSON fields use `JSONB`.

### Tables (initial)
- `tenants`: `id`, `name`, `slug`, `is_active`, `created_at`.
- `sessions`: `id`, `tenant_id`, `session_key`, `email` (nullable), `is_anonymous`, `created_at`, `last_activity_at`, `metadata` (JSONB).
- `messages`: `id`, `tenant_id`, `session_id`, `role` (human|assistant|system), `content` (TEXT), `metadata` (JSONB: citations, doc_ids, scores), `created_at`.
- `conversation_summaries`: `id`, `tenant_id`, `session_id`, `summary` (TEXT), `created_at`.
- `profiles`: `id`, `tenant_id`, `session_id`, `customer_name`, `phone`, `email`, `address_street`, `address_city`, `address_state`, `address_zip`, `products_of_interest` (TEXT[]), `services_of_interest` (TEXT[]), `preferences` (JSONB), `updated_at`.
- `llm_requests`: `id`, `tenant_id`, `session_id`, `provider` (openrouter), `model`, `request_body` (JSONB), `response_body` (JSONB), `prompt_tokens`, `completion_tokens`, `total_tokens`, `unit_cost_prompt`, `unit_cost_completion`, `computed_cost`, `latency_ms`, `created_at`.
- `personas`: `id`, `tenant_id`, `code`, `name`, `description`, `system_prompt` (TEXT), `is_default`.
- `email_events`: `id`, `tenant_id`, `session_id`, `to_email`, `subject`, `body` (TEXT/HTML), `provider_response` (JSONB), `status`, `created_at`.
- `otp_links`: `id`, `tenant_id`, `email`, `purpose` (link_session|delete_data), `otp_hash`, `expires_at`, `consumed_at`.

### Indices
- `sessions(tenant_id, email)`, `messages(session_id, created_at)`, `llm_requests(session_id, created_at)`.

### Retention
- No automatic TTL initially; purge via admin tooling later.

## 0001-002 - FEATURE - Middle Tier
- 0001-002-001 - LLM Connectivity
  - Provider: OpenRouter; model configurable via YAML.
  - Track request/response, tokens, latency, and computed cost to `llm_requests`.
  - Structured output: Use Pydantic.AI with Pydantic models for typed responses (email extraction, routing, citations). Prefer model JSON mode/function-calling via OpenRouter when available; otherwise validate/ retry from text. Note: streaming SSE typically buffers until a valid object is formed.
- 0001-002-002 - Postgres Database Connectivity
  - Use pooled connections; GUID PK generation in app layer.
- 0001-002-003 - Pinecone Connectivity
  - Read-only retrieval against configured Pinecone `index_name`.
  - Embeddings: OpenAI `text-embedding-3-small` by default (configurable). `OPENAI_API_KEY` in `.env`.
- 0001-002-004 - Mailgun Connectivity
  - Send HTML summaries. Initial target recipient comes from YAML (`email.mock_sales_recipient`).
  - Store send attempts in `email_events`.
- 0001-002-005 - Logging (Priority)
  - Use Loguru; JSONL output.
  - YAML-configured: `logging.level` and `logging.path` (plus optional `rotation`, `retention`).
  - Log request IDs, tenant ID, session ID, event type, and latencies.

### Configuration (YAML + .env)
- YAML (example):
```yaml
app:
  name: SalesBot
  mode: multi-tenant  # single-tenant|multi-tenant
chat:
  inactivity_minutes: 30
  input:
    debounce_ms: 250
    submit_shortcut: ctrl+enter
    enter_inserts_newline: true
email:
  mock_sales_recipient: sales@example.com
logging:
  level: INFO         # DEBUG|INFO|WARN|ERROR
  path: ./logs/app.jsonl
  rotation: 50 MB
  retention: 14 days
vector:
  pinecone:
    index_name: agrofresh01
embeddings:
  model: text-embedding-3-small
llm:
  provider: openrouter
  model: openai/gpt-oss-20b:free
  temperature: 0.3
  max_tokens: 1024
ui:
  sse_enabled: true
  allow_basic_html: true
```
- Environment (.env): `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `PINECONE_API_KEY`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`.

### Example logger init (for clarity only)
```python
from loguru import logger
import json, sys

logger.remove()
logger.add(sys.stdout, level=config.logging.level, serialize=True)  # JSON to stdout
logger.add(config.logging.path, level=config.logging.level, serialize=True, rotation=config.logging.rotation, retention=config.logging.retention)
```

## 0001-003 - FEATURE - Chat UI
- 0001-003-001 - Chat Window Components & Styling
  - HTMX + Basecoat CSS, server-driven UI.
  - SSE for token streaming enabled when `ui.sse_enabled` is true.
  - Templates: Jinja2 for server-rendered partials/snippets and HTML emails (layouts, includes, macros; safe auto-escaping).
  - Input UX: Submit button or Ctrl+Enter; Enter inserts newline. Debounce enabled. Append-only to chat pane. Clear button clears chat pane only. HTMX embedded as a popup in host pages.
  - Future: Mock an Astro page to simulate embedding.
  - Endpoints (doc only):
    - `POST /chat`: accepts message, session key; returns partials.
    - `GET /events/stream?session_id=...`: SSE stream for incremental assistant messages.
  - Link citations to Pinecone metadata when available.

### Summarization & Inactivity
- Inactivity threshold taken from YAML `chat.inactivity_minutes`.
- Summaries stored in `conversation_summaries`; email sending optional per prompt and router.

### Personas
- Each persona has a Python file (for prompt scaffolding) and a DB row in `personas` (`system_prompt`).
- Base prompts from `memorybank/reference/glm_prompts_03c.py` inform initial persona.

## Security & Compliance
- Anonymous chat by default. Email-based soft linking via OTP (Mailgun) to associate prior sessions.
- Data deletion flow: public page → enter email → OTP → delete sessions/messages/summaries for that email and tenant.

## Non-Functional & Ops
- Concurrency: multiple simultaneous chats expected; ensure DB pool sizing and streaming stability.
- Observability: structured JSONL logs; later add metrics/traces.
- Backup/Restore: Postgres via SQL dumps; Pinecone via index-level export/import procedures.

## Knowledge Ingestion (Out of Scope for this app)
- Separate loader scrapes and indexes content into Pinecone (see `memorybank/reference/site_loader_pinecone03.py`).
- Typical loader settings (reference): `index_name`, `text-embedding-3-small`, chunk_size 500, overlap 50, custom `User-Agent`.