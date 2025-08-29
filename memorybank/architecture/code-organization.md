# Code Organization

## Goals
- Keep Python backend and JS frontend decoupled but co-located
- Use pnpm for the frontend (Basecoat/Tailwind, optional Astro host page)
- Preserve server-driven HTMX + Jinja for the chat UI, with SSE
- Allow easy local dev: run backend and web independently
- Support Pydantic AI agents with config file-based setup initially, database-driven instances later
- Enable five agent types: simple-chat, sales, digital-expert, simple-research, deep-research

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
        simple_chat/           # Simple chat agent (Epic 0017)
          __init__.py
          agent.py             # Simple chat agent implementation
          dependencies.py      # Chat agent dependencies
          models.py           # Chat-specific Pydantic models
          tools/              # Simple chat tools
            __init__.py
            vector_tools.py   # Vector search tools
            web_search_tools.py # Web search integration
            conversation_tools.py # Conversation management
            crossfeed_tools.py # CrossFeed MCP integration
        sales/                # Sales agent (Epic 0008)  
          __init__.py
          agent.py            # Sales agent implementation
          dependencies.py     # Sales-specific dependencies
          models.py          # Sales-specific Pydantic models
          tools/             # Sales-specific tools
            __init__.py
            crm_tools.py     # CRM integration tools
            email_tools.py   # Email and communication tools
            scheduling_tools.py # Calendar and appointment tools
            product_tools.py # Product search and recommendation tools
            profile_tools.py # Customer profile capture and qualification
        simple_research/      # Simple research agent (Epic 0015)
          __init__.py
          agent.py           # Research agent implementation
          dependencies.py    # Research-specific dependencies
          models.py         # Research-specific Pydantic models
          tools/            # Research-specific tools
            __init__.py
            search_tools.py # Multi-engine web search
            memory_tools.py # Research memory management
            document_tools.py # Document intelligence
            library_tools.py # Library Manager integration
        deep_research/        # Deep research agent (Epic 0016)
          __init__.py
          agent.py           # Deep research agent implementation
          dependencies.py    # Deep research dependencies  
          models.py         # Deep research Pydantic models
          tools/            # Advanced research tools
            __init__.py
            investigation_tools.py # Multi-step investigation
            hypothesis_tools.py # Hypothesis formation
            validation_tools.py # Evidence validation
            synthesis_tools.py # Research synthesis
        digital_expert/       # Digital expert agent (Epic 0009)
          __init__.py
          agent.py           # Digital expert agent implementation
          dependencies.py    # Expert-specific dependencies
          models.py         # Expert-specific Pydantic models
          tools/            # Expert-specific tools
            __init__.py
            content_tools.py # Content analysis and ingestion tools
            persona_tools.py # Digital persona modeling tools
            knowledge_tools.py # Knowledge extraction and management
        factory/               # Agent factory (Phase 3: Multi-Account)
          __init__.py
          agent_factory.py     # Creates agent instances (config files → database)
          config_loader.py     # Loads configurations (YAML files initially)
          instance_manager.py  # Agent instance lifecycle (added in Phase 3)
          registry.py          # Instance tracking (added in Phase 3)
          cache.py             # LRU cache for instances (added in Phase 3)
        router/                # Router agent (Phase 4: Multi-Agent Routing)
          __init__.py
          intent_router.py     # Routes between simple-chat, sales, research agents
          delegation.py        # Agent handoff and context preservation
        shared/                # Shared agent resources
          __init__.py
          mcp_client.py       # MCP server integration client
          vector_tools.py     # Vector database tools (Pinecone/pgvector)
          config_manager.py   # Agent configuration management
          auth_tools.py       # Authentication and authorization tools
    templates/                 # Jinja2 templates (HTMX partials/snippets)
    static/                    # Static assets served by backend (if any)
    config/                    # YAML app config, schema, examples
      app.yaml                 # Global application configuration
      agent_configs/           # Agent configurations (Phase 1-2: Config files)
        simple_chat.yaml      # Simple chat agent configuration
        sales.yaml            # Sales agent configuration  
        digital_expert.yaml   # Digital expert agent configuration
        simple_research.yaml  # Simple research agent configuration (future)
        deep_research.yaml    # Deep research agent configuration (future)
    logs/                      # Loguru JSONL output path (from YAML)
    tests/                     # Backend tests (pytest)
      agents/                  # Agent-specific tests
        test_simple_chat_agent.py
        test_sales_agent.py
        test_digital_expert_agent.py
        test_research_agents.py
        test_router_agent.py    # Phase 4: Multi-agent routing tests
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
- **Endpoint Strategy**: Parallel endpoints for backward compatibility (see [agent-endpoint-transition.md](../design/agent-endpoint-transition.md))
  - Legacy: `POST /chat`, `GET /events/stream` (preserved during transition)
  - Agent: `POST /agents/{agent-type}/chat`, `GET /agents/{agent-type}/stream` (new)
  - Future: `POST /accounts/{account-slug}/agents/{agent-type}/chat` (Phase 3+)
- YAML config under `backend/config/app.yaml` with keys already defined in the design docs.
- **Phase 1-2**: Agent configurations under `backend/config/agent_configs/` for config file-based setup.
- Loguru configured from YAML to write JSONL to `backend/logs/` (path in YAML).

### Agent Development Patterns

#### **Implementation Phases**

**Phase 1-2: Config File-Based Agents (Simple Setup)**
- Agent configurations in YAML files (`backend/config/agent_configs/`)
- Single account, single instance per agent type
- Direct agent instantiation from config files
- No multi-account complexity

**Phase 3: Multi-Account Architecture**
- Database-driven agent instances (see [datamodel.md](datamodel.md))
- Agent factory system with LRU caching
- Account isolation and subscription tiers
- Dynamic instance provisioning

**Phase 4: Multi-Agent Routing**
- Router agent for intent classification
- Agent delegation and context handoff
- Intelligent routing between agent types

#### **Core Architecture Components**

- **Base Agent Classes**: Common functionality in `backend/app/agents/base/`
  - `agent_base.py`: Base Pydantic AI agent class with shared dependencies
  - `dependencies.py`: Common dependency injection patterns (database, vector DB, MCP servers)
  - `tools_base.py`: Base tool classes with authentication, error handling, usage tracking
  - `types.py`: Shared Pydantic models and type definitions

- **Five Agent Types**: Specific implementations in `backend/app/agents/`
  - `simple_chat/`: Multi-tool foundation agent (Epic 0017)
  - `sales/`: Sales-focused agent with CRM integration (Epic 0008)
  - `digital_expert/`: Digital persona agent with content modeling (Epic 0009)
  - `simple_research/`: Research agent with document intelligence (Epic 0015)
  - `deep_research/`: Advanced multi-step investigation agent (Epic 0016)

- **Agent Factory System**: Dynamic creation in `backend/app/agents/factory/` (Phase 3+)
  - `agent_factory.py`: Creates configured agent instances
  - `config_loader.py`: Loads configurations (YAML → database transition)
  - `instance_manager.py`: Manages agent instance lifecycle
  - `registry.py`: Tracks active agent instances
  - `cache.py`: LRU cache for frequently accessed instances

- **Shared Resources**: Common utilities in `backend/app/agents/shared/`
  - MCP server integration client for external tool calling
  - Vector database tools (Pinecone/pgvector routing)
  - Configuration management and authentication tools

- **Router Agent**: Intent classification in `backend/app/agents/router/` (Phase 4)
  - Route queries between simple-chat, sales, digital-expert, and research agents
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
- **Phase 1-2**: Agent configs in `backend/config/agent_configs/` (e.g., `simple_chat.yaml`, `sales.yaml`).
- **Phase 3+**: Agent instance configurations stored in database for multi-account support (see [datamodel.md](datamodel.md)).
- Agent configurations include system prompts, tool configurations, and model settings.
- Keep model IDs out of code paths (refer to YAML `llm.model` or agent-specific model overrides).
 - Short-term YAML knobs must include per-agent thresholds and models: `model_settings` (model, temperature, max_tokens) and `memory` (e.g., `auto_summary_threshold`, `context_window_messages`). See `memorybank/architecture/agent-configuration.md`.
 - Pinecone is the default vector DB in Milestone 1; consider `pgvector` as a budget alternative in Milestone 2.

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

