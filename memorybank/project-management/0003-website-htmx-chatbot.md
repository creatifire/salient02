# 0003 - Website & HTMX Chatbot (Host Demo)

> Convention: Use `[ ]` for open items and `[x]` for completed items across FEATURES, TASKS, and CHUNKS.
>
> Goal: Ship a simple, same-origin website that links to (or lightly hosts) the existing HTMX chat UI for demos. No memory and no RAG in this epic. Focus on a clean host page, navigation, and a robust demo story.

## 0003-001 - FEATURE - Dummy Website Shell
- [x] 0003-001-01 - TASK - Astro scaffolding in `web/`
  - [x] 0003-001-01-01 - CHUNK - Scaffold and scripts
    - SUB-TASKS:
      - Initialize an Astro project in `web/` (pnpm/Node per tech stack)
      - Add minimal layout (`src/layouts/Layout.astro`) and routes (`src/pages/...`)
      - Document dev commands: `pnpm dev` for web, `uvicorn` for backend; note same-origin linking to chat
    - STATUS: Completed — `web/` initialized; `Layout.astro` + routes in place; README documents `pnpm dev` and backend `uvicorn` commands

- [x] 0003-001-02 - TASK - Shared layout & components
  - [x] 0003-001-02-01 - CHUNK - Layout.astro; Nav.astro; Footer.astro; OpenChatCta.astro
    - SUB-TASKS:
      - Create `web/src/layouts/Layout.astro` (imports Basecoat/Tailwind, slots content)
      - Create components: `web/src/components/Nav.astro`, `Footer.astro`, `OpenChatCta.astro`
      - `OpenChatCta.astro` links to backend chat (FastAPI `GET /`) for Cycle-1
    - STATUS: Completed — Implemented `Nav.astro`, `Footer.astro`, `OpenChatCta.astro`; updated `Layout.astro`

- [x] 0003-001-03 - TASK - Home page
  - [x] 0003-001-03-01 - CHUNK - index.astro with "Open Chat" CTA
    - SUB-TASKS:
      - Create `web/src/pages/index.astro` (landing with value prop + "Open Chat" CTA)
      - Include shared nav/footer via `web/src/layouts/Layout.astro`
      - Footer links to README and project brief
    - STATUS: Completed — Added `index.astro` with CTA; wired `Nav`/`Footer` via `Layout.astro`

- [x] 0003-001-04 - TASK - About/Contact
  - [x] 0003-001-04-01 - CHUNK - about.astro; contact.astro
    - SUB-TASKS:
      - Add `web/src/pages/about.astro` and `web/src/pages/contact.astro`
      - Ensure consistent header/nav across pages
    - STATUS: Completed — Added `about.astro` and `contact.astro`; both use shared `Layout.astro` (Nav/Footer consistent)

- [x] 0003-001-05 - TASK - Page placement & routes
  - [x] 0003-001-05-01 - CHUNK - Place pages under web/src/pages; add demo/iframe (banner)
    - SUB-TASKS:
      - Place all pages under `web/src/pages/...` per the hierarchy note below
      - Add `web/src/pages/demo/iframe.astro` with a banner warning (demo-only)
    - STATUS: Completed — Created `web/src/pages/demo/iframe.astro` with warning banner; pages placed under `web/src/pages/...`

- Note: Initial Site Hierarchy (Astro)
  - Orientation only; adjust page mix during implementation.
  ```text
  web/
    src/
      layouts/
        Layout.astro
      components/
        Nav.astro, Footer.astro, OpenChatCta.astro
      pages/
        index.astro                 # Home
        about.astro                 # About
        contact.astro               # Contact us (static form UI)
        markets/
          growers.astro             # Markets → Growers
        crops/
          apples.astro              # Crops → Apples
        solutions/
          smartfresh.astro          # Solutions → SmartFresh
        digital/
          freshcloud.astro          # Digital Solutions → FreshCloud
        resources/
          zalar-farms.astro         # Resources → Customer Success Story
        products/
          index.astro               # Product overview
          product-a.astro           # Product detail (example)
        demo/
          iframe.astro              # Optional demo page (iframe warning)
  ```

- [x] 0003-001-06 - TASK - Realistic Mock Site (3–5 pages)
  - [x] 0003-001-06-01 - CHUNK - Company home + contact us
    - SUB-TASKS:
      - Hero + brief value prop, simple contact form (no backend action yet)
    - STATUS: Completed — Home (`index.astro`) and Contact (`contact.astro`) created; CTAs present
  - [x] 0003-001-06-02 - CHUNK - Product pages (1–2)
    - SUB-TASKS:
      - Create simple product detail pages with content blocks, CTA to “Open Chat”
    - STATUS: Completed — Added `products/index.astro` and `products/product-a.astro` with CTAs; linked from `products/` index

- [x] 0003-001-07 - TASK - Dummy Pages to Retrieve (scrape/summarize content)
  - [x] 0003-001-07-01 - CHUNK - Page set and targets
    - SUB-TASKS:
      - Home → `web/src/pages/index.astro` (source: [AgroFresh Home](https://www.agrofresh.com/))
      - Markets → Growers → `web/src/pages/markets/growers.astro` (source: [AgroFresh](https://www.agrofresh.com/))
      - Crops → Apples → `web/src/pages/crops/apples.astro` (source: [AgroFresh](https://www.agrofresh.com/))
      - Solutions → SmartFresh → `web/src/pages/solutions/smartfresh.astro` (source: [AgroFresh](https://www.agrofresh.com/))
      - Digital Solutions → FreshCloud → `web/src/pages/digital/freshcloud.astro` (source: [AgroFresh](https://www.agrofresh.com/))
      - Resources → Customer Success (Zalar Farms) → `web/src/pages/resources/zalar-farms.astro` (source: [AgroFresh](https://www.agrofresh.com/))
      - About → `web/src/pages/about.astro` (source: [AgroFresh](https://www.agrofresh.com/))
      - Contact → `web/src/pages/contact.astro` (source: [AgroFresh](https://www.agrofresh.com/))
    - Notes:
      - Content will be summarized/genericized for a brand-neutral demo; no trademarked names reused verbatim
      - If scope requires fewer pages for v1, prioritize: Home, SmartFresh, FreshCloud, Apples, Contact
    - STATUS: Completed — All listed pages created with brand-neutral summaries and CTAs

- [x] 0003-001-08 - TASK - Build & Dev Commands
  - [x] 0003-001-08-01 - CHUNK - Document dev runbook
    - SUB-TASKS:
      - Document running website + backend concurrently
      - Note ports and same-origin strategy for SSE
    - STATUS: Completed — Basics added to `web/README.md` and root `README.md`

## 0003-002 - FEATURE - Link to Backend Chat
> Clarification: The chat interface continues to be served by the Python backend (FastAPI) at `GET /`, rendering `backend/templates/index.html`. The website’s role in this epic is to provide clear entry points (CTAs/links) to that backend page. No embedding here (see 0003-003 for non-iframe embed options).
- [x] 0003-002-001 - TASK - Same-Origin Link
  - [x] 0003-002-001-01 - CHUNK - "Open Chat" link to backend `/`
    - SUB-TASKS:
      - Prominent CTA to open chat in same tab/new tab
      - Pass no PII in query strings
    - STATUS: Completed — CTAs added site-wide and `/chat` helper route present; links use same-origin target
  - [x] 0003-002-001-02 - CHUNK - Optional `/chat` route in Astro
    - SUB-TASKS:
      - Create lightweight `web/src/pages/chat.astro` that redirects or provides a CTA to the backend chat
      - Keep content minimal; actual chat UI remains in backend
    - STATUS: Completed — Added `web/src/pages/chat.astro` with optional redirect to backend `/` and CTA fallback
 - [x] 0003-002-003 - TASK - Production exposure switch (backend)
  - [x] 0003-002-003-01 - CHUNK - Gate backend chat page
    - SUB-TASKS:
      - Add/configure a flag (e.g., `ui.expose_backend_chat: true|false`) to hide `GET /` chat UI in production
      - When disabled, return 404 or redirect to site home; remove any site links to backend chat
      - Document reverse-proxy alternative (route block) and YAML setting in README
    - STATUS: Completed — Added `ui.expose_backend_chat` in `backend/config/app.yaml`; GET `/` returns 404 when disabled

- [x] 0003-002-002 - TASK - (Demo Only) Inline Embed Option
  - [x] 0003-002-002-01 - CHUNK - Iframe demo page (optional)
    - SUB-TASKS:
      - Create a single demo page with an iframe to backend `/`
      - Add banner: "Iframe for demo only; not recommended for production"
    - STATUS: Completed — `web/src/pages/demo/iframe.astro` uses shared `CHAT_TARGET` and includes a demo-only banner

## 0003-003 - FEATURE - Embedding Options (non-iframe)
> Avoid duplication with 0003-002-002 (iframe demo). This feature implements production-preferred, non-iframe integrations.

> Cycle-1 verified path: Astro/Preact component is the supported integration target. Shadow-DOM widget and server-include are planned and may be delivered as docs or alpha prototypes.

- [x] 0003-003-001 - TASK - Shadow-DOM Widget (floating button + slide-in pane)
  - [x] 0003-003-001-01 - CHUNK - Floating button + ShadowRoot pane (toggle)
    - SUB-TASKS:
      - Inject fixed-position button on all pages (bottom-right)
      - Create hidden pane inside Shadow DOM; slide-in/out on toggle
      - Z-index and overlay to ensure visibility above page content
      - Acceptance: Button visible; click opens/closes pane with animation
    - STATUS: Completed — `web/public/widget/chat-widget.js` injects floating button + pane (Shadow DOM) with overlay and ESC-to-close; demo at `web/src/pages/demo/widget.astro`
  - [x] 0003-003-001-02 - CHUNK - Fetch and inject chat HTML (same-origin)
    - SUB-TASKS:
      - Default source: `/` (backend chat page) or configurable partial path
      - Fetch on first open; cache in widget; re-open is instant
      - Strict same-origin enforcement; no cross-origin fetches
      - Acceptance: Chat UI loads and functions inside pane
    - STATUS: Completed — Implemented minimal in-pane chat UI posting to `/chat` (same-origin via dev proxy); configurable via `data-chat-path`, `data-backend`, `data-allow-cross`; verbose error logging; renders Markdown replies
  - [x] 0003-003-001-03 - CHUNK - Basic theming variables
    - SUB-TASKS:
      - Expose CSS variables (e.g., `--widget-accent`, `--widget-bg`, `--widget-radius`)
      - Apply styles within Shadow DOM; document host overrides
      - Acceptance: Changing variables updates button/pane look
  - [x] 0003-003-001-04 - CHUNK - Accessibility & focus handling
    - SUB-TASKS:
      - ARIA labels (`aria-expanded`, `aria-controls`), `role="dialog"` for pane
      - Trap focus while open; Escape to close; return focus to trigger
      - Acceptance: Keyboard-only users can open/close/use chat
  - [x] 0003-003-001-05 - CHUNK - Config API (init options / data-attrs)
    - SUB-TASKS:
      - Options: `sourceUrl`, `position` (br/bl), `openOnLoad` (false), `theme` vars
      - Provide `window.SalientChatWidget.init({...})` and data-attribute fallback
      - Acceptance: Options change behavior without code edits
  - [x] 0003-003-001-06 - CHUNK - Build & include path
    - SUB-TASKS:
      - Ship script at `web/public/widget/chat-widget.js` (no bundler required)
      - Astro integration snippet added to `web/README.md` and demo layout
      - Acceptance: Adding one `<script src="/widget/chat-widget.js">` enables widget
    - STATUS: Completed — Loader shipped at `web/public/widget/chat-widget.js`; demo includes `<script src="/widget/chat-widget.js" is:inline>`
  - [x] 0003-003-001-07 - CHUNK - Demo/QA page
    - SUB-TASKS:
      - Add `web/src/pages/demo/widget.astro` to validate open/close, theme, options
      - Checklist for manual tests (open, close, ESC, same-origin fetch)
      - Acceptance: All checks pass on demo page
    - STATUS: Completed — `/demo/widget` validates toggle, send/clear, error surfacing; ESC/overlay close work
  - [x] 0003-003-001-08 - CHUNK - Safety & constraints
    - SUB-TASKS:
      - Enforce same-origin; block cross-origin URLs
      - Sanitize/ignore inline scripts in fetched HTML (rely on server-side content)
      - Acceptance: Widget refuses external URLs; no CSP violations reported
  - [x] 0003-003-001-09 - CHUNK - Copy-to-clipboard on bot messages (widget)
    - SUB-TASKS:
      - Add a small copy icon button to each `.msg.bot` rendered in the Shadow DOM pane
      - Click copies the underlying full message content (prefer raw accumulated text before Markdown render)
      - Show non-blocking confirmation (e.g., transient "Copied" toast) within the pane; keyboard accessible
      - Fallback if `navigator.clipboard.writeText` is unavailable (use a hidden textarea + execCommand)
      - Acceptance: Icon visible on hover/focus; Enter/Space activates; copied text matches message content exactly
    - STATUS: Completed — Icon button (bottom-right) copies raw text with toast + keyboard support; Clipboard API fallback implemented

## 0003-007 - FEATURE - Standalone HTMX Chat Page (web)
- [x] 0003-007-001 - TASK - Page scaffold
  - [x] 0003-007-001-01 - CHUNK - Create `web/src/pages/demo/htmx-chat.astro` (or plain `/public/htmx-chat.html`) with HTMX + minimal CSS
    - SUB-TASKS:
      - Load HTMX via CDN
      - Include message textarea, Send, Clear, chat pane containers
    - STATUS: Completed — Added `web/src/pages/demo/htmx-chat.astro` and `web/public/htmx-chat.html` scaffolds (UI elements present; wiring follows in 0003-007-002)
- [x] 0003-007-002 - TASK - Wire to backend endpoints (same-origin)
  - [x] 0003-007-002-01 - CHUNK - SSE `/events/stream` + POST `/chat` fallback
    - SUB-TASKS:
      - Stream tokens into a bot message div; send final `end` handling
      - Non-stream fallback with Markdown render
    - STATUS: Completed — Astro page (`/demo/htmx-chat`) and plain page (`/htmx-chat.html`) use SSE to `/events/stream` with live tokens and POST `/chat` fallback; render Markdown (DOMPurify + marked) on completion
- [x] 0003-007-003 - TASK - UI/UX parity with backend `index.html`
  - [x] 0003-007-003-01 - CHUNK - Controls & behavior
    - SUB-TASKS:
      - Keyboard: Ctrl/Cmd+Enter submit; Enter newline
      - Debounce input; disable Send while active; subtle “Receiving…” indicator
      - Clear only clears history, not input
      - Client-side Markdown + DOMPurify when `allow_basic_html=true`
      - Add copy-to-clipboard button with copy icon on each bot message
    - STATUS: Completed — Keyboard submit, input debounce, disable controls during stream (Send/Clear/Copy), subtle “Receiving…” indicator, Clear only clears history, client-side Markdown render, copy-to-clipboard implemented.
- [x] 0003-007-004 - TASK - Config plumbing (targets/flags)
  - [x] 0003-007-004-01 - CHUNK - Use `PUBLIC_CHAT_TARGET` (default same-origin) and honor flags
    - SUB-TASKS:
      - Respect `ui.sse_enabled`, `ui.allow_basic_html` semantics
    - STATUS: Completed — Astro standalone page reads `PUBLIC_CHAT_TARGET`, `PUBLIC_SSE_ENABLED`, and `PUBLIC_ALLOW_BASIC_HTML`; plain page defaults to same-origin.
- [x] 0003-007-005 - TASK - Styling & A11y
  - [x] 0003-007-005-01 - CHUNK - Light Basecoat/Tailwind polish + landmarks/skip link
    - STATUS: Completed — Added skip link, main landmark, focus-visible outlines, and accessible labels to both standalone pages.
- [x] 0003-007-006 - TASK - Exposure controls
  - [x] 0003-007-006-01 - CHUNK - Dev-only route or flag guard (no prod exposure by default)
    - STATUS: Completed — Guarded Astro standalone page with `PUBLIC_ENABLE_STANDALONE_CHAT` (default false in prod, true in dev) and redirects when disabled.
- [ ] 0003-007-007 - TASK - Documentation
  - [ ] 0003-007-007-01 - CHUNK - README notes (how to run, flags, caveats)
- [x] 0003-007-008 - TASK - Copy-to-clipboard on messages (standalone page)
  - [x] 0003-007-008-01 - CHUNK - Add copy button to `.msg.bot`
    - SUB-TASKS:
      - Same behavior as widget: icon button, keyboard accessible, toast on success, fallback when clipboard API is unavailable
      - Acceptance: copying matches the message text (raw accumulated or final rendered if raw not retained)
    - STATUS: Completed — Icon button added on both standalone pages; copies raw accumulated text with fallback.

## 0003-004 - FEATURE - Styling & Accessibility
- [x] 0003-004-001 - TASK - Basic Styles
  - [x] 0003-004-001-01 - CHUNK - Light layout polish
    - SUB-TASKS:
      - Ensure responsive layout and readable typography
      - Keep styles minimal; no heavy frameworks beyond Basecoat/Tailwind (if present)
    - STATUS: Completed — Brand link colors/underline, stable nav hover/active (no shift), themed CTA

- [x] 0003-004-002 - TASK - A11y Checks
  - [x] 0003-004-002-01 - CHUNK - Keyboard and landmarks
    - SUB-TASKS:
      - Ensure skip-to-content, focus outlines, accessible nav
    - STATUS: Completed — Added skip link, header/main/footer landmarks, visible focus for links

## 0003-005 - FEATURE - Ops & Observability (Lite)
- [x] 0003-005-001 - TASK - Diagnostics & Links
  - [x] 0003-005-001-01 - CHUNK - Footer diagnostics block (dev only)
    - SUB-TASKS:
      - Link to backend `/health`
      - Link to backend logs directory (readme/pointer)
    - STATUS: Completed — Footer shows dev-only diagnostics with link to backend `/health`

## 0003-009 - FEATURE - Refactor Astro HTMX Demo To Proper HTMX 2.0.6 Idioms
- [ ] 0003-009-001 - TASK - Bump HTMX + load SSE ext (Astro page)
  - [ ] 0003-009-001-01 - CHUNK - Scripts + integrity
    - SUB-TASKS:
      - Replace `unpkg htmx@1.9.12` with `htmx.org@2.0.6` (jsDelivr or unpkg) on `web/src/pages/demo/htmx-chat.astro`
      - Add SSE extension `htmx-ext-sse@2.2.2` after core; body/wrapper uses `hx-ext="sse"`
      - Acceptance: Page loads with 2.0.6, no console errors

- [ ] 0003-009-002 - TASK - Non-stream POST flow via `hx-post`
  - [ ] 0003-009-002-01 - CHUNK - Form wiring
    - SUB-TASKS:
      - Wrap input/buttons in a form: `hx-post="/chat" hx-trigger="click from:#send, keydown[key=='Enter' && (ctrlKey || metaKey)] from:#msg"`
      - Use `hx-include="#msg"` and name textarea `message`
      - Set `hx-target="#chatPane"` (or `.chat`) and `hx-swap="beforeend"`, `hx-indicator="#hint"`
      - On `htmx:beforeRequest` append user bubble; server returns bot bubble partial (HTML) appended automatically
      - Acceptance: Send/Ctrl+Enter posts and appends bot reply without custom JS

- [ ] 0003-009-003 - TASK - Streaming via SSE extension
  - [ ] 0003-009-003-01 - CHUNK - SSE container
    - SUB-TASKS:
      - Add wrapper `hx-ext="sse" sse-connect="/events/stream?llm=1"`
      - If server uses default `message` event: set `sse-swap="message"` on a target element that renders bot bubble HTML
      - Close on server `end` event; optionally listen to `htmx:sseClose` for cleanup
      - Acceptance: Live incremental bot updates render into chat; no console errors

- [ ] 0003-009-004 - TASK - Controls/disabled states & indicators
  - [ ] 0003-009-004-01 - CHUNK - hx-disabled / hx-on
    - SUB-TASKS:
      - Prefer `hx-indicator="#hint"` and `hx-disabled-elt="#send,#clear"` on the form
      - If needed, use `hx-on` to disable/enable buttons on submit/afterOnLoad
      - Keep Clear button as a plain control that wipes chat history only

- [ ] 0003-009-005 - TASK - Targeting, swap strategy, a11y & security
  - [ ] 0003-009-005-01 - CHUNK - Policies
    - SUB-TASKS:
      - Keep `aria-live="polite"`, skip link, focus-visible outlines
      - Use `hx-target` + `hx-swap="beforeend"`; consider morphing swaps later if needed
      - Prefer server-rendered, sanitized bot bubble HTML for HTMX swaps; retain DOMPurify fallback if server returns text/Markdown
      - Same-origin enforcement; dev proxy for local

- [ ] 0003-009-006 - TASK - QA & docs
  - [ ] 0003-009-006-01 - CHUNK - Manual test + notes
    - SUB-TASKS:
      - Validate POST + SSE flows, keyboard shortcuts, indicator/disabled states; inspect `htmx:sseOpen/sseMessage/sseClose`
      - Update README notes for flags, proxy, and extension scripts

## 0003-008 - FEATURE - HTMX 2.0.6 Upgrade & Proper Usage
- [ ] 0003-008-001 - TASK - Upgrade HTMX to 2.0.6 across demo pages
  - [ ] 0003-008-001-01 - CHUNK - Version bump + breaking changes audit
    - SUB-TASKS:
      - Read htmx 2.x migration notes; extensions moved out of core. SSE requires separate ext v2.x
      - Update CDN tags: core `https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js` (or unpkg) + SSE ext `https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.2`
      - Acceptance: All pages load 2.0.6 with no console errors

- [ ] 0003-008-002 - TASK - Rework `web/public/htmx-chat.html` to HTMX idioms
  - [ ] 0003-008-002-01 - CHUNK - Non-stream POST with `hx-post`
    - SUB-TASKS:
      - Use a form: `hx-post="/chat" hx-trigger="click from:#send, keydown[key=='Enter' && (ctrlKey || metaKey)] from:#msg" hx-include="#msg" hx-target="#chat" hx-swap="beforeend" hx-indicator="#hint"`
      - Name textarea `message` or set `hx-vals` to include `{ message: value }`
      - On `htmx:beforeRequest`, append user bubble; server returns a bot bubble partial (HTML) appended via `beforeend`
      - Acceptance: Send/Ctrl+Enter append user + bot bubbles, indicator toggles
  - [ ] 0003-008-002-02 - CHUNK - Streaming via SSE extension
    - SUB-TASKS:
      - Add on a wrapper: `hx-ext="sse" sse-connect="/events/stream?llm=1"`
      - If server emits named events, set `sse-swap="message"` (or specific event name); emit HTML chunks (bot bubble partials) from server
      - Close on server `end` event; optionally listen to `htmx:sseClose` for cleanup
      - Acceptance: Live bot updates appear incrementally; no console errors
  - [ ] 0003-008-002-03 - CHUNK - Controls/disabled & indicators
    - SUB-TASKS:
      - Prefer `hx-indicator="#hint"` + `hx-disabled-elt="#send,#clear"` (or `hx-on` to disable/enable on submit/afterOnLoad)
      - Keep Clear as a plain button that wipes the history container only
  - [ ] 0003-008-002-04 - CHUNK - Targeting, swap, a11y & security
    - SUB-TASKS:
      - Use `hx-target="#chat"` and `hx-swap="beforeend"`; consider morphing swaps in future if needed
      - Retain `aria-live="polite"`, skip link, and focus-visible outlines
      - Sanitize markdown-rendered HTML (DOMPurify) or sanitize server-side before emit
      - Enforce same-origin; document CORS; use dev proxy for local

- [ ] 0003-008-003 - TASK - Test plan
  - [ ] 0003-008-003-01 - CHUNK - Manual QA matrix
    - SUB-TASKS:
      - Verify POST + SSE flows; keyboard shortcuts; indicator/disabled states; recovery on SSE close
      - Inspect headers (HX-*) and events (`htmx:sseOpen`, `htmx:sseMessage`, `htmx:sseClose`); update docs as needed