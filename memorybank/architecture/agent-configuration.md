# Agent Configuration (Short-Term YAML → Long-Term Database)
> **Last Updated**: September 17, 2025

## Purpose
Define how agent behavior is configured today (YAML files in the repo) and how it will migrate to database-backed configuration as part of multi-account support. This enables fast iteration now with a clear path to scalable management later.

For comprehensive configuration documentation including global `app.yaml` settings, see [Configuration Reference](./configuration-reference.md).

## Location (Short Term)
- Backend config directory: `backend/config/agent_configs/`
- Agent-specific folder structure (NEW):
  - `simple_chat/config.yaml` + `simple_chat/system_prompt.md`
  - `sales/config.yaml` + `sales/system_prompt.md`
  - `digital_expert/config.yaml` + `digital_expert/system_prompt.md`
- Legacy flat structure (backward compatibility):
  - `simple_chat.yaml`, `sales.yaml`, etc.

See `memorybank/architecture/code-organization.md` for directory layout and project structure.

## YAML Schema (Minimum Viable)
```yaml
# Example: backend/config/agent_configs/sales/config.yaml

agent_type: "sales"                  # simple_chat | sales | simple_research | deep_research | digital_expert
name: "Sales Agent"
description: "AI sales assistant with CRM integration"

# System prompt configuration (NEW)
prompts:
  system_prompt_file: "./system_prompt.md"  # External prompt file

model_settings:
  model: "openai:gpt-4o"            # LLM id via OpenRouter
  temperature: 0.3
  max_tokens: 2000

context_management:
  # Chat history and memory management (NEW SECTION)
  history_limit: 50                  # STANDARDIZED: Override app.yaml chat.history_limit (database queries)
  context_window_tokens: 8000        # Token limit for conversation context passed to LLM
  
  # Conversation summarization, titles, and context window policy
  summarization:
    enabled: true
    trigger_threshold: 10            # Trigger summary every N messages
    summary_model: "gpt-4o-mini"     # Cost-optimized summary model
    title_revision_model: "gpt-4o-mini"
    summary_length: 200              # Target summary length in words

vector_database:
  provider: "pinecone"              # pinecone | pgvector (future option)
  index: "shared-index"             # optional, depends on Pinecone setup
  namespace: "acme-sales"           # per-account or per-instance namespace
  top_k: 5

tools:
  vector_search:
    enabled: true
    max_results: 5

  web_search:
    enabled: true
    default_engine: "exa"           # exa | tavily | linkup (router can choose)

  conversation_management:
    enabled: true
    auto_summarize_threshold: 10

  crm_integration:
    enabled: true
    provider: "zoho"                # zoho (first), salesforce, hubspot (future)
    # Provider-specific values go here
    zoho:
      base_url: "https://www.zohoapis.com/crm/v2"
      # OAuth/app credentials are provided via environment/secrets, not YAML

email:
  enabled: false                     # Mailgun integration (future)

scheduling:
  enabled: false                     # Nylas/Calendly integration (future)

feature_flags:
  allow_basic_html: true
  sse_enabled: true
```

## Configuration Cascade (Agent-First Priority)

**Cascade Order**: Agent Config → Global Config → Code Fallback

1. **Agent-specific config** (`simple_chat/config.yaml`) - **Highest Priority**
2. **Global config** (`app.yaml`) - **Fallback**  
3. **Code constants** - **Last Resort** (e.g., `history_limit: 50`)

**Example for `history_limit`:**
```
Agent Config: context_management.history_limit: 75    ← WINS
Global Config: chat.history_limit: 50                 ← Ignored
Code Fallback: 50                                     ← Not used
Result: 75
```

**System Prompt File Separation:**
- System prompts moved to external `.md` files for better editing
- Referenced via `prompts.system_prompt_file: "./system_prompt.md"`
- Paths resolved relative to agent config directory

Notes:
- Secrets (keys/tokens) stay in environment variables or secret stores, not YAML.
- YAML values define behavior, thresholds, and toggles to keep code paths generic.
- Parameter names standardized: use `history_limit` (not `max_history_messages`)

## Migration Path (Phase 3+)
- Move YAML configuration into database tables defined in `datamodel.md`:
  - `agent_templates` – schema/validation, default settings per agent type
  - `agent_instances` – per-account overrides, display names, status
  - `vector_db_configs` – per-instance vector routing (Pinecone namespace/index, or pgvector)
- Use an Agent Factory with LRU caching to load and hot-reload configurations.

## Decision Log
- Pinecone-first for RAG (scalability, familiar integration). Consider `pgvector` as a budget option around Milestone 2.
- First CRM: Zoho CRM (owner’s current stack and website integration target).
- Widget roadmap: keep Shadow DOM widget now; defer Preact/React widgets until end of Milestone 1.

## Implementation Checklist
- Read agent YAML at startup and inject into agent dependencies. Start with `backend/config/agent_configs/simple_chat.yaml` using the schema above.
- Keep model ids and thresholds out of code paths; reference `model_settings` and `context_management` sections.
- Ensure endpoint transition plan remains compatible: legacy `/chat` and `/events/stream` plus `/agents/{type}/chat`.


