# Demo Integrations Strategy

This document describes how we demo multiple integration options (Shadow DOM widget, HTMX pages, Preact/React components) using a single Astro playground, without creating multiple web apps.

## Approach (single host)
- Use one Astro site at `web/` as a "playground" to showcase all variants
- Keep demos same-origin with the Python backend via the existing Vite proxy in `web/astro.config.mjs`
- Avoid separate web folders unless a framework-native demo is explicitly required

## Current demos
- Vanilla JS Shadow DOM widget
  - Source: `web/public/widget/chat-widget.js`
  - Demo route: `web/src/pages/demo/widget.astro`
  - Notes: same-origin enforcement by default; dev proxy enables local testing

- HTMX standalone pages (to be refactored to HTMX 2.0.6 idioms)
  - Plain HTML: `web/public/htmx-chat.html`
  - Astro page: `web/src/pages/demo/htmx-chat.astro`
  - Plans:
    - 0003-008: upgrade to HTMX 2.0.6 and use SSE extension (`hx-ext="sse"`, `sse-connect`, `sse-swap`)
    - 0003-009: apply the same to the Astro page with proper `hx-post`, `hx-trigger`, `hx-target`, `hx-swap`, `hx-indicator`

## Planned demos
- Preact chat widget component (in addition to Shadow DOM widget)
  - Plan: 0003-003-002
  - Component: `SalesChatWidget.tsx` (configurable props: `backend`, `chatPath`, `ssePath`, `ssePreferred`, `allowHtml`, `position`, `openOnLoad`)
  - Demo route: `web/src/pages/demo/preact-widget.astro`

- React chat widget component (future)
  - Add `@astrojs/react`
  - Create a demo route `web/src/pages/demo/react-widget.astro`
  - Implementation mirrors Preact component API

## Packaging option (optional)
- Publish a single npm package with multiple entry points:
  - Vanilla JS build (IIFE/ESM) for `<script>` tag inclusion
  - `preact` and `react` component builds
- Continue to use the Astro playground as the consumer/demo site

## Config & flags
- Backend targeting: `web/src/lib/chatTarget.ts` → `PUBLIC_CHAT_TARGET`
- Flags used in Astro demo pages:
  - `PUBLIC_SSE_ENABLED`, `PUBLIC_ALLOW_BASIC_HTML`
  - `PUBLIC_ENABLE_STANDALONE_CHAT` (guards `htmx-chat.astro` in production)
- Backend flags:
  - `ui.expose_backend_chat` (hides FastAPI GET `/` chat page in production)

## Same-origin & proxy
- Dev proxy in `web/astro.config.mjs` forwards `/chat`, `/events`, `/health` → backend at `http://localhost:8000`
- This enables same-origin fetches for the widget and HTMX pages without CORS

## Directory & routes (excerpt)
```text
web/
  public/
    widget/
      chat-widget.js
    htmx-chat.html
  src/
    pages/
      demo/
        widget.astro          # Shadow DOM widget demo
        htmx-chat.astro       # HTMX Astro demo
        preact-widget.astro   # (planned) Preact component demo
        react-widget.astro    # (future) React component demo
```

## A11y & security baselines
- A11y: skip link, `role="dialog"` + `aria-modal` for widgets, focus trap, `aria-live="polite"` for chat history, keyboard shortcuts (Ctrl/Cmd+Enter)
- Security: sanitize rendered Markdown (DOMPurify) or provide server-sanitized HTML; avoid cross-origin in demos

## QA checklist (per demo)
- Send via button and Ctrl/Cmd+Enter; disable controls during request; indicator toggles
- SSE streaming path and POST fallback both work
- Same-origin verified; no console errors; backend logs show expected requests

## Why one playground
- Single dev server and proxy; consistent same-origin behavior
- Easier navigation across multiple integration styles
- Reduced maintenance vs. multiple framework-specific hosts

## WordPress demo strategy (if required)
WordPress can host the widget with minimal friction using the Shadow DOM script variant.

- Quick embed (recommended)
  - Upload `chat-widget.js` to your site (or serve from our demo host), then add to WP theme/footer or a Code Snippets plugin:
    - `<script src="/widget/chat-widget.js" data-backend="https://your-demo-host" data-chat-path="/chat" data-sse="1"></script>`
  - Same-origin preferred. In production, reverse-proxy `/chat` and `/events` to the backend under the same domain to avoid CORS.

- Reverse proxy (preferred for demos)
  - Configure the WP front proxy (Nginx/Cloudflare/Apache) to route `/chat`, `/events`, `/health` to the Python backend
  - Keeps widget same-origin; avoids CORS and cookies issues

- Security & hardening
  - Sanitize any server-rendered HTML; widget already sanitizes client-side Markdown via DOMPurify
  - Disable the backend GET `/` page in production (`ui.expose_backend_chat: false`); use widget or Astro/Preact component only
  - Rate limit and log requests at the proxy; ensure no secrets in the page

- Optional: WP plugin wrapper (future)
  - Wrap the embed in a lightweight plugin exposing an admin settings page for backend URL and options
  - Not required for demos; the raw `<script>` embed suffices

### Hosting options for a WordPress demo
- Managed WP host (recommended)
  - Providers: WP Engine, Kinsta, Pressable, Pagely
  - Use host-level reverse proxy (Nginx) to route `/chat`, `/events`, `/health` → Python backend (Render/Fly/Railway/VM)
  - Pros: SSL, CDN, easy admin; same-origin via subpath routing; no CORS needed
  - Notes: Provide ops a short rewrite snippet and backend origin URL

- WordPress.com (Business/Commerce plans)
  - Script embed is possible; reverse-proxy rules limited
  - If subpath proxy not available, use a subdomain backend and temporarily enable CORS (not preferred for demos)

- Local demo (no external hosting)
  - Use LocalWP or Docker Compose (WordPress + MySQL) behind Traefik/Nginx
  - Expose via Cloudflare Tunnel or ngrok; terminate at a single hostname and reverse-proxy `/chat` and `/events` to backend
  - Pros: fully controlled; same-origin achievable; good for private demos

- Domain model
  - Single hostname (best): `demo.example.com` serves WP; `/chat`, `/events`, `/health` proxied to backend
  - Two hosts (fallback): `wp.example.com` + `api.example.com`; requires CORS and is not recommended for widget demos

## Multi-app workspaces (if framework-native demos are needed)
Keep one repo using pnpm workspaces. Only add extra apps if a customer needs native framework integration beyond Astro.

- Structure (example)
```text
salient02/
  web/                      # Astro playground (primary demo host)
  examples/
    nextjs/                 # Next.js app showing React component integration
    react-vite/             # React + Vite minimal host for the React/Preact components
    (optional) astro-preact/ # If you want a dedicated Preact-only host
```

- Guidance
  - Widgets/components are developed in `web/` first (Shadow DOM + Preact)
  - `examples/*` consume the packaged builds (or local links) for framework-native showcases
  - Keep backend endpoints and ports consistent; prefer same-origin via dev proxy or Next.js rewrites
  - Don’t duplicate logic: components live in one place; demos import them

- Next.js demo notes
  - Add a `Rewrites` config to forward `/chat` and `/events` to the backend during dev
  - Render the React/Preact widget component inside a simple page; confirm SSR/CSR behavior is acceptable

- Trade-offs
  - Pros: framework-native demos when demanded
  - Cons: higher maintenance; use only when the single Astro playground is insufficient
