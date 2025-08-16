# 0002 - Baseline Connectivity (HTMX → Middle Tier → OpenRouter LLM)

## 0002-001 - FEATURE - Minimal UI + SSE
- [x] 0002-001-001 - TASK - Serve Base Page
  - [x] 0002-001-001-01 - CHUNK - Route `GET /` renders minimal Jinja2 page
    - SUB-TASKS:
      - Include HTMX via CDN
      - Message textarea + Submit + Clear buttons
      - Append-only chat pane container
    - STATUS: Completed — Implemented `GET /` rendering `templates/index.html` with HTMX CDN, textarea, Send/Clear buttons, and append-only chat pane
  - [x] 0002-001-001-02 - CHUNK - Input UX
    - SUB-TASKS:
      - Ctrl+Enter submits; Enter inserts newline
      - Debounce per YAML `chat.input.debounce_ms`
      - Clear button wipes pane only
    - STATUS: Completed — Input UX is configurable via YAML (debounce_ms, submit_shortcut, enter_inserts_newline) and applied on page load
  - Optional (not in baseline): Host Page Link/Embed
    - Dev note: Astro on 4321 can link to the backend chat page on 8000; consider an iframe only for quick demos to avoid CORS. Production approach will use a site-wide widget (see 0001 integration notes).

## 0002-002 - FEATURE - SSE Streaming Endpoint
- [x] 0002-002-001 - TASK - SSE route
  - [x] 0002-002-001-01 - CHUNK - `GET /events/stream` emits tokens
    - SUB-TASKS:
      - Reads model, temperature, max_tokens from YAML
      - Sends server-sent events with incremental text chunks
      - Handles errors/timeouts gracefully
    - STATUS: Completed — Implemented `GET /events/stream` with incremental token-like chunks; added Stream Demo button on base page to verify SSE

## 0002-003 - FEATURE - OpenRouter Connectivity
- [ ] 0002-003-001 - TASK - Chat completion call
  - [x] 0002-003-001-01 - CHUNK - Minimal LLM client
    - SUB-TASKS:
      - Use `OPENROUTER_API_KEY` from `.env` (Bearer)
      - Model from YAML: `openai/gpt-oss-20b:free`
      - Optional headers: `HTTP-Referer`, `X-Title`
      - Basic system prompt file + user message
    - STATUS: Completed — Implemented `openrouter_client.py` and integrated with `/events/stream` when `llm=1`
  - [ ] 0002-003-001-02 - CHUNK - Wire UI to LLM streaming
    - SUB-TASKS:
      - From the base page, send textarea content to `/events/stream?llm=1&message=...`
      - Append streamed tokens into the chat pane incrementally
      - Handle disconnect/error gracefully; allow re-start
  - [ ] 0002-003-001-03 - CHUNK - Non-stream fallback (POST /chat)
    - SUB-TASKS:
      - Implement `POST /chat` to call OpenRouter and return a rendered snippet
      - Update the UI to submit non-streaming when streaming is disabled
      - Render assistant response in the chat pane

## 0002-004 - FEATURE - Logging Foundation
- [ ] 0002-004-001 - TASK - Loguru init
  - [ ] 0002-004-001-01 - CHUNK - JSONL to stdout and file
    - SUB-TASKS:
      - YAML-configured: `logging.level`, `logging.path`, `rotation`, `retention`
      - Log start/end of requests, SSE streaming events, errors

## 0002-005 - FEATURE - Config
- [ ] 0002-005-001 - TASK - Load YAML + .env
  - [ ] 0002-005-001-01 - CHUNK - Config loader
    - SUB-TASKS:
      - Parse YAML keys: `llm.model`, `llm.temperature`, `llm.max_tokens`, `ui.sse_enabled`, `chat.input.*`
      - Read `.env` for `OPENROUTER_API_KEY`

## 0002-006 - FEATURE - Jinja Partials
- [ ] 0002-006-001 - TASK - Message snippet templates
  - [ ] 0002-006-001-01 - CHUNK - Render inbound/outbound messages
    - SUB-TASKS:
      - Ensure escaping; allow basic HTML if `ui.allow_basic_html`

## Definition of Done
- Multiple back-and-forths with the LLM via SSE (no memory, no DB)
- Submit and clear buttons work, Ctrl+Enter submits, Enter adds newline
- Logs emitted in JSONL with configured level/path