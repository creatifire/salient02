# Epics
> Convention: Use `[ ]` for open items and `[x]` for completed items across FEATURES, TASKS, and CHUNKS.
01. [Preliminary Design](./0001-preliminary-design.md)
02. [Baseline Connectivity](./0002-baseline-connectivity.md)
03. [Website & HTMX Chatbot](./0003-website-htmx-chatbot.md)
04. [Chat Memory & Persistence](./0004-chat-memory.md)
05. [Agent Infrastructure & Sales Agent]
06. [Advanced Persistence Features]

## Epic Backlog

### Proposed Epics (shippable increments)

- 1004 – Core Persistence & Sessions
  - Define Alembic migrations; create `sessions`, `messages`, `llm_requests` tables
  - Store chat turns (no RAG yet); list past sessions; resume by session key
  - Record OpenRouter usage/cost in `llm_requests`
  - DoD: restart-safe chats; basic session switcher; JSONL + DB logs agree

- 1005 – Retrieval-Augmented Answers (Pinecone)
  - Connect Pinecone with namespace per tenant
  - Add retrieval step + cite sources; toggle RAG on/off via YAML
  - Inline citation links; basic rank/score display
  - DoD: side-by-side demo: with/without RAG; clickable citations

- 1006 – Email Summaries & Handoff
  - Summarize conversation; send HTML summary via Mailgun to mock recipient
  - Configurable triggers (manual button, inactivity)
  - Store `email_events`; link to session
  - DoD: one-click "Email Summary" works; summary archived; log + DB entry

- 1007 – Profiles & Preferences (Light CRM)
  - Capture optional email; soft link sessions via OTP
  - Store basic profile + products/services of interest
  - Attach profile to future sessions when verified
  - DoD: OTP flow; profile card in UI; verified sessions linked

- 1008 – Multi-Agent Ready Routing (Single Agent shipped)
  - Introduce `/a/{agent}/chat` path; keep only Sales agent enabled
  - Minimal `agents` + `tenant_agents` tables for future use
  - Per-agent config overrides (model/persona) read from YAML
  - DoD: app runs under `/a/sales/...`; toggling agent name works

- 1009 – Embeddable Widget (Site Integration)
  - Floating button + slide-in pane; tiny JS loader; same-origin
  - Astro/Preact host demo; SSE-compatible
  - Basic theme variables; DOM isolation
  - DoD: drop-in snippet renders widget on any page

- 1010 – Admin & Ops (Config + Observability)
  - Read-only config page; YAML download; runtime flags view
  - Metrics: request counts, tokens, latency; simple /metrics JSON
  - Rotating log viewer (tail last N)
  - DoD: operator can verify health/usage without SSH

- 1011 – Safety, Rate Limits, Compliance
  - Per-IP/session rate limit; CSRF on POST initializer (future GET stream_id)
  - Prompt/PII logging redaction; configurable allow_basic_html defaults
  - Data deletion flow (OTP-protected)
  - DoD: limits enforced; redaction tests; deletion verified

- 1012 – Quality UX Pass
  - Markdown tables/images; code blocks; copy button
  - Streaming cursor/typing indicator; resend message
  - Keyboard/nav polish; accessibility audit
  - DoD: polished demo showcasing UX improvements

- 1013 – MCP Server Integration
  - Implement Model Context Protocol (MCP) client for external tool/data connections
  - Support multiple MCP servers via YAML configuration
  - Built-in MCP tools: filesystem, database, web scraping, API integration
  - Tool discovery, authentication, and session management
  - DoD: Connect to MCP servers; execute tools; display results in chat

- 1014 – CRM Integrations
  - Direct API integrations with popular CRM systems for customer data sync
  - Support: 
    - Salesforce
    - HubSpot
    - Zoho CRM
    - Pipedrive
    - Freshsales
    - LessAnnoyingCRM
    - OnePageCRM
    - Groundhogg
  - Lead creation, contact updates, opportunity tracking, activity logging
  - OAuth authentication, webhook handling, real-time data synchronization
  - DoD: Sales bot creates leads in CRM; syncs conversation data; updates contact records

- 1014a - Static Site Generators
  - Astro
  - Hugo

- 1015 – CMS Integrations  
  - Native integrations with popular Content Management Systems
  - Support: 
    - WordPress
    - Drupal
    - Joomla
    - Webflow
    - Contentful
    - Strapi
    - Ghost
  - Plugin/module development, REST API connections, content synchronization
  - Chat widget embedding, lead capture forms, content-aware responses
  - DoD: Chat widgets deploy to CMS sites; capture leads; sync with backend

- 1016 - Order Management Systems
  - Shopify
  - WooCommerce

- 1017 - Data as MCP Service
  - Cross-Sell
  - Up-Sell
  - Competitive Selling
  - Product Catalog
  - Sales Rep Terriory

- 1018 - Automation Tools
  https://encharge.io/zapier-alternatives/
  - Zapier 
  - Make 
  - Encharge.io
  - IFTTT
  - Zoho Flow
  - Integrately
  - Pabbly Connect
  - Automate.io
  - Outfunnel
  - Workato
  - Microsoft Power Automate
  - Tray.io
  - Appy Pie Automate

- 1019 - Nylas Integration/White Labeling
  - Email API
  - Calendar API
  - Contacts API
  - Scheduler API
  - NoteTaker API

- 1020 - Deployment Option: Netlify/Vercel - Variation 1: 
    - Astro
    - Supabase
        - Relational DB
        - Vector DB
        - Auth

- 1021 - Deployment Option - Azure/Wordpress
    - Dedicated Server
    - WordPress?
    - Postgres Backend
    - Pinecone
    - OAuth?

- 1022 - Deployment Option - AWS

- 1023 - Netlify/Vercel - Variation 2: 
    - Astro
    - Directus (Headless CMS)
    - Clerk/Auth0
    - Supabase
        - Relational DB
    - Vector Database
        - Pinecone

- 1024 - Deployment Option - GCP

- 1025 - Deploy to Render.com
    - Use Docker?
    - Astro on their CDN
    - Use their instances of Postgres
    - Spin up the infrastructure for Marc to do his customization

- 1026 - CRM Lite Back End
    - Have some basic CRM capability in the back end to verify interactions with other backkend systems, like:
        - CRM
        - Customer Profile
        - Appointments Scheduled
        - Daily Site Traffic

- 1027 - Analytics Dashboard
    - Ability to see basic statistics on the dashboard
        - Num appointments made
        - Cross-Sells
        - Up-Sells
        - New Profiles Added

- 1028 - SDK for Developing Applications with Salient