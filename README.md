# SalesBot (Salient02)

Minimal RAG-powered sales assistant with server-driven HTMX UI, FastAPI backend, and optional Astro host site.

## Repository layout
```
./
  backend/       # FastAPI app, Jinja2 templates, HTMX, SSE, YAML config
  web/           # Astro app (pnpm), Tailwind v4 + Basecoat, optional host page
  memorybank/    # Project docs (architecture, plans, standards)
  requirements.txt
  .env           # OPENROUTER_API_KEY, etc. (not committed)
```

## Quick start

### 1) Backend (FastAPI)
- Create/activate a venv
- Install deps:
```bash
pip install -r requirements.txt
```
- Run dev server:
```bash
uvicorn backend.app.main:app --reload
```
- Visit: http://localhost:8000/

Notes:
- Baseline shows a minimal HTMX-enabled chat page (no memory/DB yet).
- YAML config placeholder: `backend/config/app.yaml`.
- Logs are configured via YAML; see Logging section below.

### 2) Web (Astro host, optional)
```bash
cd web
pnpm install
pnpm dev
```
- Visit: http://localhost:4321/
- Tailwind v4 via @tailwindcss/vite, Basecoat imported in src/styles/global.css.
- Ensure global.css is imported from your layout.

## Environment
- .env at repo root (untracked)
  - OPENROUTER_API_KEY=
  - MAILGUN_API_KEY=  (future)
  - MAILGUN_DOMAIN=mail.ape4.com  (from POC)
  - PINECONE_API_KEY=  (future)
  - OPENAI_API_KEY=  (embeddings / ingestion app)

## Key documentation
- Project Brief: memorybank/project-brief.md
- Technology Stack: memorybank/architecture/technology-stack.md
- Technical Constraints: memorybank/architecture/technical-constraints.md
- Code Organization: memorybank/architecture/code-organization.md
- Preliminary Design: memorybank/project-management/0001-preliminary-design.md
- Baseline Connectivity: memorybank/project-management/0002-baseline-connectivity.md
- Commit Message Conventions: memorybank/commit-messages.md
- Salesbot Integration Approaches: memorybank/architecture/salesbot-integration.md

## Conventions
- Commit messages: Conventional Commits + Chris Beams 50/72 (see docs)
- Planning statuses: [ ] open, [x] completed for FEATURES/TASKS/CHUNKS

## License

Copyright (c) 2025 Ape4, Inc. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, 
or use of this software is strictly prohibited. See [LICENSE](./LICENSE) for details.

For licensing inquiries, contact Ape4, Inc.

## Logging configuration
- Location: `backend/config/app.yaml` under `logging:`
- Keys and meanings:
  - `level`: `DEBUG|INFO|WARN|ERROR` (default `INFO`)
  - `prefix`: File prefix when `path` is not set. Final file name becomes `<prefix><timestamp>.jsonl` (default `salient-log-`)
  - `path`: Explicit file path; when set, overrides `prefix` naming (e.g., `./backend/logs/app.jsonl`)
  - `rotation`: When to rotate logs. Accepts size or time, e.g. `50 MB`, `1 day`, `1 hour`, `00:30` (every 30 minutes)
  - `retention`: How long/how many to keep (e.g., `14 days`)
  - `compression`: Optional compression for rotated files (`zip`, `gz`, `bz2`)
  - `enqueue`: Write logs via a background thread (recommended under concurrency)

Recommended policies:
- Development: `rotation: 50 MB`, `retention: 7 days`
- Production: `rotation: 1 day` or `1 hour`; `retention: 14 days`; enable `enqueue: true` and `compression: zip`

Example (30-minute rotation with prefix-based naming):
```yaml
logging:
  level: INFO
  prefix: salient-log-
  # path: ./backend/logs/app.jsonl   # uncomment to force a fixed filepath instead
  rotation: 00:30
  retention: 14 days
  compression: zip
  enqueue: true
```
