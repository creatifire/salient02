# Epics
> Convention: Use `[ ]` for open items and `[x]` for completed items across FEATURES, TASKS, and CHUNKS.
01. [Preliminary Design](./0001-preliminary-design.md)
02. [Baseline Connectivity](./0002-baseline-connectivity.md)
03. [Website & HTMX Chatbot](./0003-website-htmx-chatbot.md)
04. [Agent Infrastructure & Sales Agent]
05. [Persistence, Sessions, multi-user support]

## Candidate Epics

### Proposed Epics (shippable increments)

- 0003 – Core Persistence & Sessions
  - Define Alembic migrations; create `sessions`, `messages`, `llm_requests` tables
  - Store chat turns (no RAG yet); list past sessions; resume by session key
  - Record OpenRouter usage/cost in `llm_requests`
  - DoD: restart-safe chats; basic session switcher; JSONL + DB logs agree

- 0004 – Retrieval-Augmented Answers (Pinecone)
  - Connect Pinecone with namespace per tenant
  - Add retrieval step + cite sources; toggle RAG on/off via YAML
  - Inline citation links; basic rank/score display
  - DoD: side-by-side demo: with/without RAG; clickable citations

- 0005 – Email Summaries & Handoff
  - Summarize conversation; send HTML summary via Mailgun to mock recipient
  - Configurable triggers (manual button, inactivity)
  - Store `email_events`; link to session
  - DoD: one-click “Email Summary” works; summary archived; log + DB entry

- 0006 – Profiles & Preferences (Light CRM)
  - Capture optional email; soft link sessions via OTP
  - Store basic profile + products/services of interest
  - Attach profile to future sessions when verified
  - DoD: OTP flow; profile card in UI; verified sessions linked

- 0007 – Multi-Agent Ready Routing (Single Agent shipped)
  - Introduce `/a/{agent}/chat` path; keep only Sales agent enabled
  - Minimal `agents` + `tenant_agents` tables for future use
  - Per-agent config overrides (model/persona) read from YAML
  - DoD: app runs under `/a/sales/...`; toggling agent name works

- 0008 – Embeddable Widget (Site Integration)
  - Floating button + slide-in pane; tiny JS loader; same-origin
  - Astro/Preact host demo; SSE-compatible
  - Basic theme variables; DOM isolation
  - DoD: drop-in snippet renders widget on any page

- 0009 – Admin & Ops (Config + Observability)
  - Read-only config page; YAML download; runtime flags view
  - Metrics: request counts, tokens, latency; simple /metrics JSON
  - Rotating log viewer (tail last N)
  - DoD: operator can verify health/usage without SSH

- 0010 – Safety, Rate Limits, Compliance
  - Per-IP/session rate limit; CSRF on POST initializer (future GET stream_id)
  - Prompt/PII logging redaction; configurable allow_basic_html defaults
  - Data deletion flow (OTP-protected)
  - DoD: limits enforced; redaction tests; deletion verified

- 0011 – Quality UX Pass
  - Markdown tables/images; code blocks; copy button
  - Streaming cursor/typing indicator; resend message
  - Keyboard/nav polish; accessibility audit
  - DoD: polished demo showcasing UX improvements

- 0012 - Deployment Option: Netlify/Vercel - Variation 1: 
    - Astro
    - Supabase
        - Relational DB
        - Vector DB
        - Auth

- 0013 - Deployment Option - Azure/Wordpress
    - Dedicated Server
    - WordPress?
    - Postgres Backend
    - Pinecone
    - OAuth?

- 0014 - Deployment Option - AWS

- 0015 - Netlify/Vercel - Variation 2: 
    - Astro
    - Directus (Headless CMS)
    - Clerk/Auth0
    - Supabase
        - Relational DB
    - Vector Databae
        - Pinecone

- 0016 - Deployment Option - GCP

These build cleanly on what’s done, and each epic yields a demoable slice.