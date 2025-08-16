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

- [ ] 0003-001-06 - TASK - Realistic Mock Site (3–5 pages)
  - [ ] 0003-001-06-01 - CHUNK - Company home + contact us
    - SUB-TASKS:
      - Hero + brief value prop, simple contact form (no backend action yet)
  - [ ] 0003-001-06-02 - CHUNK - Product pages (1–2)
    - SUB-TASKS:
      - Create simple product detail pages with content blocks, CTA to “Open Chat”

- [ ] 0003-001-07 - TASK - Dummy Pages to Retrieve (scrape/summarize content)
  - [ ] 0003-001-07-01 - CHUNK - Page set and targets
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

- [ ] 0003-001-08 - TASK - Build & Dev Commands
  - [ ] 0003-001-08-01 - CHUNK - Document dev runbook
    - SUB-TASKS:
      - Document running website + backend concurrently
      - Note ports and same-origin strategy for SSE

## 0003-002 - FEATURE - Link to Backend Chat
> Clarification: The chat interface continues to be served by the Python backend (FastAPI) at `GET /`, rendering `backend/templates/index.html`. The website’s role in this epic is to provide clear entry points (CTAs/links) to that backend page. No embedding here (see 0003-003 for non-iframe embed options).
- [ ] 0003-002-001 - TASK - Same-Origin Link
  - [ ] 0003-002-001-01 - CHUNK - "Open Chat" link to backend `/`
    - SUB-TASKS:
      - Prominent CTA to open chat in same tab/new tab
      - Pass no PII in query strings
  - [ ] 0003-002-001-02 - CHUNK - Optional `/chat` route in Astro
    - SUB-TASKS:
      - Create lightweight `web/src/pages/chat.astro` that redirects or provides a CTA to the backend chat
      - Keep content minimal; actual chat UI remains in backend
 - [ ] 0003-002-003 - TASK - Production exposure switch (backend)
   - [ ] 0003-002-003-01 - CHUNK - Gate backend chat page
     - SUB-TASKS:
       - Add/configure a flag (e.g., `ui.expose_backend_chat: true|false`) to hide `GET /` chat UI in production
       - When disabled, return 404 or redirect to site home; remove any site links to backend chat
       - Document reverse-proxy alternative (route block) and YAML setting in README

- [ ] 0003-002-002 - TASK - (Demo Only) Inline Embed Option
  - [ ] 0003-002-002-01 - CHUNK - Iframe demo page (optional)
    - SUB-TASKS:
      - Create a single demo page with an iframe to backend `/`
      - Add banner: "Iframe for demo only; not recommended for production"

## 0003-003 - FEATURE - Embedding Options (non-iframe)
> Avoid duplication with 0003-002-002 (iframe demo). This feature implements production-preferred, non-iframe integrations.

> Cycle-1 verified path: Astro/Preact component is the supported integration target. Shadow-DOM widget and server-include are planned and may be delivered as docs or alpha prototypes.

- [ ] 0003-003-001 - TASK - Shadow-DOM Widget (floating button + slide-in pane)
  - [ ] 0003-003-001-01 - CHUNK - Minimal loader script
    - SUB-TASKS:
      - Floating button appears on all pages; toggles a slide-in pane
      - Mounts a Shadow DOM container; fetches same-origin HTMX partials/HTML
      - Basic theming variables (colors, radius); no cross-origin calls

- [ ] 0003-003-002 - TASK - Astro/Preact Component (host demo)
  - [ ] 0003-003-002-01 - CHUNK - Component + props
    - SUB-TASKS:
      - Provide a `<SalesChatWidget />` that renders the floating button/pane
      - Same-origin fetch of HTMX content; document install and usage

- [ ] 0003-003-003 - TASK - Layout-level Server Include
  - [ ] 0003-003-003-01 - CHUNK - Include + partials
    - SUB-TASKS:
      - Add layout include that renders a button and hidden pane scaffolding
      - HTMX swaps populate pane content; same-origin only

## 0003-004 - FEATURE - Styling & Accessibility
- [ ] 0003-004-001 - TASK - Basic Styles
  - [ ] 0003-004-001-01 - CHUNK - Light layout polish
    - SUB-TASKS:
      - Ensure responsive layout and readable typography
      - Keep styles minimal; no heavy frameworks beyond Basecoat/Tailwind (if present)

- [ ] 0003-004-002 - TASK - A11y Checks
  - [ ] 0003-004-002-01 - CHUNK - Keyboard and landmarks
    - SUB-TASKS:
      - Ensure skip-to-content, focus outlines, accessible nav

## 0003-005 - FEATURE - Ops & Observability (Lite)
- [ ] 0003-005-001 - TASK - Diagnostics & Links
  - [ ] 0003-005-001-01 - CHUNK - Footer diagnostics block (dev only)
    - SUB-TASKS:
      - Link to backend `/health`
      - Link to backend logs directory (readme/pointer)

## 0003-006 - FEATURE - Integration Guides (CMS/SSG)
- [ ] 0003-006-001 - TASK - WordPress integration notes (doc-only)
  - [ ] 0003-006-001-01 - CHUNK - Snippet + constraints
    - SUB-TASKS:
      - Provide guidance for injecting floating-button script or embed include
      - Note same-origin constraints and security considerations
- [ ] 0003-006-002 - TASK - Static site generators (generic)
  - [ ] 0003-006-002-01 - CHUNK - Include patterns
    - SUB-TASKS:
      - Document how to include widget/component in common SSGs (e.g., Hugo, Eleventy)
      - Emphasize production switch to hide backend chat page

## Definition of Done
- Host site provides a clean landing with an "Open Chat" entry point
- SSE remains same-origin or linked (no cross-origin streaming in this epic)
- Optional iframe demo page exists with clear "demo-only" warning
- Basic accessibility and responsive layout are in place
- Floating button/pane available via at least one non-iframe option (widget or component)

