# Salesbot Website Integration Approaches

## Goals
- Reusable, site-wide chat trigger (floating button) opening a slide-in pane
- Server-driven content via HTMX + Jinja with SSE; minimal JS
- Easy embed across frameworks (Astro or any site), strong UX/A11y, and safe defaults

## Baseline (current)
- Backend-only HTMX page and SSE stream (no host-page coupling). Astro not required for baseline.

## Integration options (future)

### 1) Shadow DOM Widget (recommended)
- How: Single `<script>` tag loads a small ES module that:
  - Injects a floating button and a slide-in pane into `document.body`
  - Uses Shadow DOM to scope styles; fetches HTMX partials for messages; opens SSE to `/events/stream`
- Pros: Style isolation; no framework dependency; works on any site; drop-in
- Cons: Slightly more JS; careful bridge for HTMX swaps within shadow root
- Config: `<script src="/widget/salesbot.js" data-backend-origin="https://app.example.com" data-position="right" data-open-after-ms="5000"></script>`

### 2) Astro/Preact Component (hosted in web/)
- How: Provide `<SalesbotWidget />` that renders the button + pane; pane content pulled via HTMX to backend endpoints
- Pros: Great DX in Astro sites; easier theming via Tailwind/Basecoat
- Cons: Requires Astro/Preact; less framework-agnostic

### 3) Layout-level server include (HTMX-native)
- How: Add a layout partial (Jinja/HTMX) containing the button and a hidden pane scaffold, loaded on every page
- Pros: Minimal JS; server-driven
- Cons: Tighter coupling to server templating; weaker portability

### 4) iframe host (demo only)
- How: Embed backend chat route in an iframe modal
- Pros: Fastest POC; no cross-bundle concerns
- Cons: Styling/height/SEO limitations; message passing overhead

### 5) Micro-frontend ES module served by backend
- How: Versioned ES module (`/static/salesbot@x.y.z.esm.js`) that sites import and initialize
- Pros: CDN-friendly; version pinning; works across stacks
- Cons: Packaging/release lifecycle overhead

### 6) No-bundler single-script injection
- How: One `<script>` that self-injects UI and uses fetch + HTMX swaps; no build step
- Pros: Works on legacy sites
- Cons: Larger script; fewer optimizations

## Cross-cutting concerns
- Styling: Tailwind/Basecoat for pane; Shadow DOM for isolation (Option 1). Ensure z-index, responsive height, safe area
- Accessibility: Focus trap in pane; ARIA roles; keyboard (Esc to close); readable contrasts
- State: Anonymous session id via cookie/localStorage until DB memory added
- SSE: Reconnect/backoff; surface transient errors; cancel on pane close
- Security: CSP-friendly (nonce or hashed inline); no eval; CORS avoided by same-origin or iframe; sanitize HTML when `ui.allow_basic_html`
- Performance: Lazy-load widget (idle or `data-open-after-ms`); defer SSE until pane opens
- Telemetry: Loguru server logs; optional client beacons for open/close/error
- Configuration: Backed by YAML on server; client can override non-sensitive via `data-*` attributes

## Recommended path
1. Baseline backend chat page + SSE (done in 0002)
2. Quick demo via Astro link to chat page (optional)
3. Implement Shadow DOM Widget (Option 1)
4. Publish Astro/Preact `<SalesbotWidget />` (Option 2) for first-class Astro sites

## Backend endpoints (for all options)
- `GET /` base chat page (HTMX)
- `POST /chat` submit user message → returns partial
- `GET /events/stream?session_id=...` SSE tokens

## Minimal host usage examples
- Shadow DOM widget:
```html
<script src="/widget/salesbot.js" data-backend-origin="https://localhost:8000" data-open-after-ms="5000" defer></script>
```
- Astro component:
```astro
---
import '../styles/global.css';
import SalesbotWidget from '@/components/SalesbotWidget.jsx';
---
<SalesbotWidget backendOrigin={import.meta.env.PUBLIC_BACKEND_ORIGIN} />
```

