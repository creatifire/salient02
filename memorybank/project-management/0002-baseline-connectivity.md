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
- [x] 0002-003-001 - TASK - Chat completion call
  - [x] 0002-003-001-01 - CHUNK - Minimal LLM client
    - SUB-TASKS:
      - Use `OPENROUTER_API_KEY` from `.env` (Bearer)
      - Model from YAML: `openai/gpt-oss-20b:free`
      - Optional headers: `HTTP-Referer`, `X-Title`
      - Basic system prompt file + user message
    - STATUS: Completed — Implemented `openrouter_client.py` and integrated with `/events/stream` when `llm=1`
  - [x] 0002-003-001-02 - CHUNK - Wire UI to LLM streaming
    - SUB-TASKS:
      - From the base page, send textarea content to `/events/stream?llm=1&message=...`
      - Append streamed tokens into the chat pane incrementally
      - Handle disconnect/error gracefully; allow re-start
    - STATUS: Completed — Send now opens SSE to `/events/stream?llm=1` and appends streamed tokens into a bot message; closes previous streams
  - [x] 0002-003-001-03 - CHUNK - Non-stream fallback (POST /chat)
    - SUB-TASKS:
      - Implement `POST /chat` to call OpenRouter and return a rendered snippet
      - Update the UI to submit non-streaming when streaming is disabled
      - Render assistant response in the chat pane
    - STATUS: Completed — Added `POST /chat` returning plain text; client uses it when `ui.sse_enabled` is false

## 0002-004 - FEATURE - Logging Foundation
- [x] 0002-004-001 - TASK - Loguru init
  - [x] 0002-004-001-01 - CHUNK - JSONL to stdout and file
    - SUB-TASKS:
      - YAML-configured: `logging.level`, `logging.path`, `rotation`, `retention`
      - Log start/end of requests, SSE streaming events, errors
    - STATUS: Completed — Loguru initialized on startup per YAML; JSONL to stdout and file
  - [x] 0002-004-001-02 - CHUNK - Backend request logging
    - SUB-TASKS:
      - Log incoming `GET /` and `GET /events/stream` with query params
      - Log disconnects/errors in SSE generator
    - STATUS: Completed — Added logs for base page, SSE params, disconnects, errors, and completion
  - [x] 0002-004-001-03 - CHUNK - LLM call logging (redacted)
    - SUB-TASKS:
      - Log model, latency, token counts/cost if available (no secrets/body)
      - Log error responses from OpenRouter succinctly
    - STATUS: Completed — Added logging in `openrouter_client.py` for model, latency, token usage/cost (when present), and succinct error details; no bodies/secrets logged
  - [x] 0002-004-001-04 - CHUNK - Client-side console diagnostics
    - SUB-TASKS:
      - Console logs for SSE open/message/error during troubleshooting (toggle via YAML `logging.frontend_debug`)
    - STATUS: Completed — Frontend console diagnostics gated by `logging.frontend_debug` and wired for SSE message/end/error

## 0002-005 - FEATURE - Config
- [x] 0002-005-001 - TASK - Load YAML + .env
  - [x] 0002-005-001-01 - CHUNK - Config loader
    - SUB-TASKS:
      - Parse YAML keys: `llm.model`, `llm.temperature`, `llm.max_tokens`, `ui.sse_enabled`, `chat.input.*`
      - Read `.env` for `OPENROUTER_API_KEY`
    - STATUS: Completed — Centralized `.env` loading; added defaults/validation for `llm.temperature` and `llm.max_tokens`; parsed `ui.sse_enabled` and wired it through backend → template → client; SSE endpoint gated when disabled

## 0002-006 - FEATURE - Jinja Partials
- [x] 0002-006-001 - TASK - Message snippet templates
  - [x] 0002-006-001-01 - CHUNK - Render inbound/outbound messages
    - SUB-TASKS:
      - Ensure escaping; allow basic HTML if `ui.allow_basic_html`
    - STATUS: Completed — Added `templates/partials/message.html` (kept for reuse/emails). Current flows render Markdown client-side on completion for both SSE and POST.

## 0002-007 - FEATURE - UI Presentation & Streaming UX
- [x] 0002-007-001 - TASK - Layout reorder
  - SUB-TASKS:
    - Order: Title → Chat History (scrollable) → Input box → Buttons row
    - Buttons row: left group (Send, Clear), right (Stream Demo)
  - STATUS: Completed — Reordered layout; user messages right-aligned with extra left padding; bot messages left-aligned with extra right padding and pale yellow background; chat pane scrollable
- [x] 0002-007-002 - TASK - Client-side Markdown render with DOMPurify on end
  - SUB-TASKS:
    - Accumulate tokens as plain text
    - On `end` event, render Markdown to HTML and sanitize
  - STATUS: Completed — Integrated marked.js + DOMPurify; accumulate during stream and render sanitized HTML on end; respects `ui.allow_basic_html`
- [x] 0002-007-003 - TASK - Subtle "streaming" indicator while receiving
  - SUB-TASKS:
    - Show spinner/text during active SSE, hide on `end`/error
  - STATUS: Completed — Added a small "Streaming…" indicator shown during SSE and POST fallback; hides on end/error
- [ ] 0002-007-004 - TASK - Disable Send while a stream is active
  - SUB-TASKS:
    - Disable Send (and Ctrl/Cmd+Enter) on open; re-enable on `end`/error
- [ ] 0002-007-005 - TASK - Ensure Clear only clears history, not input
  - SUB-TASKS:
    - Clear pane only; preserve input contents

## Definition of Done
- Multiple back-and-forths with the LLM via SSE (no memory, no DB)
- Submit and clear buttons work, Ctrl+Enter submits, Enter adds newline
- Logs emitted in JSONL with configured level/path