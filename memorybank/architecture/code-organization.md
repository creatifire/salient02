# Code Organization

## Goals
- Keep Python backend and JS frontend decoupled but co-located
- Use pnpm for the frontend (Basecoat/Tailwind, optional Astro host page)
- Preserve server-driven HTMX + Jinja for the chat UI, with SSE
- Allow easy local dev: run backend and web independently

## Top-level layout
```
salient02/
  backend/                     # Python FastAPI app
    app/                       # Python modules (routers, services)
      agents/                  # Pydantic AI agents module (NEW)
        __init__.py
        base/                  # Base agent classes and shared functionality
          __init__.py
          agent_base.py        # Base agent class with common dependencies
          dependencies.py      # Common dependency injection classes
          tools_base.py        # Base tool classes and utilities
          types.py            # Shared types and Pydantic models
        router/                # Router agent for intent classification
          __init__.py
          intent_router.py     # Main router agent implementation
          delegation.py        # Agent delegation and handoff logic
        sales/                 # Sales agent implementation (Epic 0008)
          __init__.py
          agent.py            # Main SalesAgent class
          dependencies.py     # SalesDependencies class
          models.py           # Sales-specific Pydantic models
          config.py           # Sales agent configuration
          tools/              # Sales-specific tools
            __init__.py
            crm_tools.py      # CRM integration tools (Zoho, Salesforce, HubSpot)
            email_tools.py    # Email and communication tools
            scheduling_tools.py # Calendar and appointment tools
            product_tools.py  # Product search and recommendation tools
            profile_tools.py  # Customer profile capture and qualification
        digital_expert/        # Digital expert agent (Epic 0009)
          __init__.py
          agent.py            # Main DigitalExpertAgent class
          dependencies.py     # Expert-specific dependencies
          models.py           # Expert-specific Pydantic models
          tools/              # Expert-specific tools
            __init__.py
            content_tools.py  # Content analysis and ingestion tools
            persona_tools.py  # Digital persona modeling tools
            knowledge_tools.py # Knowledge extraction and management
        shared/                # Shared agent resources
          __init__.py
          mcp_client.py       # MCP server integration client
          vector_tools.py     # Vector database tools (Pinecone/pgvector)
          config_manager.py   # Agent configuration management
          auth_tools.py       # Authentication and authorization tools
    templates/                 # Jinja2 templates (HTMX partials/snippets)
    static/                    # Static assets served by backend (if any)
    config/                    # YAML app config, schema, examples
      app.yaml
      agents/                  # Agent-specific configurations (NEW)
        sales.yaml            # Sales agent configuration
        digital_expert.yaml  # Digital expert agent configuration
    logs/                      # Loguru JSONL output path (from YAML)
    tests/                     # Backend tests (pytest)
      agents/                  # Agent-specific tests (NEW)
        test_sales_agent.py
        test_digital_expert.py
        test_router_agent.py
    pyproject.toml             # Python project metadata (or requirements.txt)
    README.md

  web/                         # Frontend workspace (pnpm)
    src/
      pages/                   # Astro pages (e.g., host page, popup entry)
        index.astro
      components/              # Astro components
      layouts/
      styles/
        global.css             # Tailwind/Basecoat imports
    public/                    # Public assets
    astro.config.mjs
    package.json
    tsconfig.json
    # Tailwind v4 via @tailwindcss/vite (config files optional)

  memorybank/                  # Project docs (leave as-is)
  .env                         # OPENROUTER_API_KEY, MAILGUN_API_KEY, etc.
  README.md
```

Notes:
- `memorybank/` remains at the repo root as the project’s documentation space.
- The backend serves the HTMX chat UI and SSE. The Astro site is a host/shell that can embed or link to the backend UI (for future embedding scenarios).

## Frontend: pnpm + Basecoat + Tailwind + (optional) Astro
- Place the frontend in `web/` as a standalone Astro app (matches Astro docs: `src/pages`, `src/components`, `public`, `astro.config.mjs`, `package.json`).
- Tailwind v4 setup: use `@tailwindcss/vite` plugin and `@import "tailwindcss";` in `web/src/styles/global.css`.
- Install Basecoat and import in `web/src/styles/global.css` after Tailwind: `@import "basecoat-css";`.
- Ensure global styles are loaded by importing the stylesheet in your layout:
  ```astro
  ---
  import '../styles/global.css';
  ---
  ```
- If you later add more JS packages, consider pnpm workspaces by placing a `package.json` at the repo root with `"workspaces": ["web"]`. This keeps Node dependencies sandboxed to the `web/` folder.

### Astro alignment (verified with current docs)
- Astro default structure under `web/`:
  - `src/pages/index.astro`, `astro.config.mjs`, `package.json`, `tsconfig.json`, `public/` (ref: Astro project structure)
- Create via: `pnpm create astro@latest` (run inside `web/` parent). You will follow the wizard to scaffold files.
 - Preact integration (optional): add `@astrojs/preact` in `astro.config.mjs` and set `tsconfig.json` jsx settings to:
   ```json
   {
     "compilerOptions": {
       "jsx": "react-jsx",
       "jsxImportSource": "preact"
     }
   }
   ```

## Backend: Python FastAPI + Jinja + HTMX + SSE + Pydantic AI Agents
- Keep all Python server code in `backend/`.
- Jinja templates (HTMX partials/snippets) under `backend/templates/`.
- SSE endpoint exposed by backend (e.g., `GET /events/stream`).
- YAML config under `backend/config/app.yaml` with keys already defined in the design docs.
- **NEW**: Agent-specific configurations under `backend/config/agents/` for modular agent settings.
- Loguru configured from YAML to write JSONL to `backend/logs/` (path in YAML).

### Agent Development Patterns
- **Base Agent Classes**: Common functionality in `backend/app/agents/base/`
  - `agent_base.py`: Base Pydantic AI agent class with shared dependencies
  - `dependencies.py`: Common dependency injection patterns (database, vector DB, MCP servers)
  - `tools_base.py`: Base tool classes with authentication, error handling, usage tracking
  - `types.py`: Shared Pydantic models and type definitions

- **Specialized Agents**: Agent-specific implementations in dedicated modules
  - Each agent has its own module (e.g., `sales/`, `digital_expert/`)
  - Agent-specific dependencies, models, and tools in separate files
  - Tools organized in `tools/` subdirectory for each agent

- **Shared Resources**: Common agent utilities in `backend/app/agents/shared/`
  - MCP server integration client for external tool calling
  - Vector database tools (Pinecone/pgvector routing based on account tier)
  - Configuration management for hot-reloadable agent settings
  - Authentication and authorization tools for secure agent operations

- **Router Agent**: Intent classification and delegation in `backend/app/agents/router/`
  - Route incoming queries to appropriate specialist agents
  - Maintain conversation context across agent handoffs
  - Handle fallback scenarios for ambiguous queries

## Integration between web and backend
- The Astro host page (`web/src/pages/index.astro`) can:
  - Link to the backend chat route; or
  - Embed the chat UI in an `<iframe>` pointing to the backend page (no CORS needed for baseline; revisit CSP/headers later).
- The primary chat interactions remain server-driven via HTMX over the backend.

## Environment & config
- `.env` at repo root for secrets (e.g., `OPENROUTER_API_KEY`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `PINECONE_API_KEY`, `OPENAI_API_KEY`).
- App runtime config in `backend/config/app.yaml` (model, temperature, max_tokens, logging, UI flags, debounce, etc.).
- **NEW**: Agent-specific configs in `backend/config/agents/` (e.g., `sales.yaml`, `digital_expert.yaml`).
- **NEW**: Agent configuration includes system prompts, tool configurations, pricing tiers, and feature flags.
- Keep model IDs out of code paths (refer to YAML `llm.model` or agent-specific model overrides).

## Local development flow
- Backend:
  - Create/activate Python venv in `salient02/` or `backend/`.
  - Run the FastAPI app (serves HTMX and SSE).
- Frontend:
  - `cd web && pnpm install && pnpm dev` to run Astro dev server.
  - Visit the Astro page to see the shell/host experience; it embeds or links to the backend chat UI.

## Future growth
- More apps can be added under `web/` or `apps/` if needed (e.g., admin UI).
- Shared frontend libraries can live under `packages/` and be included in pnpm workspaces.
- Database migrations, ORM models, and ingest tools remain under `backend/` per existing design.

## Rationale
- Mirrors Astro’s documented structure (src/pages/components/layouts, public, config files).
- Keeps Node dependencies isolated under `web/` (pnpm-friendly), while Python dependencies stay in `backend/`.
- Preserves the server-driven HTMX approach while allowing an Astro host page for embedding scenarios.

