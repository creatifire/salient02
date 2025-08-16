# 0003 - Website & HTMX Chatbot (Host Demo)

> Convention: Use `[ ]` for open items and `[x]` for completed items across FEATURES, TASKS, and CHUNKS.
>
> Goal: Ship a simple, same-origin website that links to (or lightly hosts) the existing HTMX chat UI for demos. No memory and no RAG in this epic. Focus on a clean host page, navigation, and a robust demo story.

## 0003-001 - FEATURE - Dummy Website Shell
- [ ] 0003-001-001 - TASK - Scaffolding & Pages
  - [ ] 0003-001-001-01 - CHUNK - Home page + basic nav
    - SUB-TASKS:
      - Create simple landing with project summary and "Open Chat" button
      - Include footer with links to docs (README, project brief)
  - [ ] 0003-001-001-02 - CHUNK - About/Contact placeholders
    - SUB-TASKS:
      - Add two placeholder pages to make the site feel real
      - Ensure consistent header/nav across pages

- [ ] 0003-001-004 - TASK - Astro app in `web/` folder
  - [ ] 0003-001-004-01 - CHUNK - Scaffold and scripts
    - SUB-TASKS:
      - Initialize an Astro project in `web/` (pnpm/Node per tech stack)
      - Add minimal layout (`src/layouts/Layout.astro`) and routes (`src/pages/...`)
      - Document dev commands: `pnpm dev` for web, `uvicorn` for backend; note same-origin linking to chat

- [ ] 0003-001-003 - TASK - Realistic Mock Site (3–5 pages)
  - [ ] 0003-001-003-01 - CHUNK - Company home + contact us
    - SUB-TASKS:
      - Hero + brief value prop, simple contact form (no backend action yet)
  - [ ] 0003-001-003-02 - CHUNK - Product pages (1–2)
    - SUB-TASKS:
      - Create simple product detail pages with content blocks, CTA to “Open Chat”

- [ ] 0003-001-002 - TASK - Build & Dev Commands
  - [ ] 0003-001-002-01 - CHUNK - Document dev runbook
    - SUB-TASKS:
      - Document running website + backend concurrently
      - Note ports and same-origin strategy for SSE

## 0003-002 - FEATURE - Link to Backend Chat
- [ ] 0003-002-001 - TASK - Same-Origin Link
  - [ ] 0003-002-001-01 - CHUNK - "Open Chat" link to backend `/`
    - SUB-TASKS:
      - Prominent CTA to open chat in same tab/new tab
      - Pass no PII in query strings

- [ ] 0003-002-002 - TASK - (Demo Only) Inline Embed Option
  - [ ] 0003-002-002-01 - CHUNK - Iframe demo page (optional)
    - SUB-TASKS:
      - Create a single demo page with an iframe to backend `/`
      - Add banner: "Iframe for demo only; not recommended for production"

## 0003-003 - FEATURE - Embedding Options (non-iframe)
> Avoid duplication with 0003-002-002 (iframe demo). This feature implements production-preferred, non-iframe integrations.

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
- [ ] 0003-003-001 - TASK - Basic Styles
  - [ ] 0003-003-001-01 - CHUNK - Light layout polish
    - SUB-TASKS:
      - Ensure responsive layout and readable typography
      - Keep styles minimal; no heavy frameworks beyond Basecoat/Tailwind (if present)

- [ ] 0003-003-002 - TASK - A11y Checks
  - [ ] 0003-003-002-01 - CHUNK - Keyboard and landmarks
    - SUB-TASKS:
      - Ensure skip-to-content, focus outlines, accessible nav

## 0003-005 - FEATURE - Ops & Observability (Lite)
- [ ] 0003-004-001 - TASK - Diagnostics & Links
  - [ ] 0003-004-001-01 - CHUNK - Footer diagnostics block (dev only)
    - SUB-TASKS:
      - Link to backend `/health`
      - Link to backend logs directory (readme/pointer)

## Definition of Done
- Host site provides a clean landing with an "Open Chat" entry point
- SSE remains same-origin or linked (no cross-origin streaming in this epic)
- Optional iframe demo page exists with clear "demo-only" warning
- Basic accessibility and responsive layout are in place
- Floating button/pane available via at least one non-iframe option (widget or component)

