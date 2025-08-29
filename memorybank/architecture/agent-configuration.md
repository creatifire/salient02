# Agent Configuration (Short-Term YAML → Long-Term Database)

## Purpose
Define how agent behavior is configured today (YAML files in the repo) and how it will migrate to database-backed configuration as part of multi-account support. This enables fast iteration now with a clear path to scalable management later.

## Location (Short Term)
- Backend config directory: `backend/config/agent_configs/`
- Files by agent type (examples):
  - `simple_chat.yaml`
  - `sales.yaml`
  - `digital_expert.yaml`
  - `simple_research.yaml`
  - `deep_research.yaml`

See `memorybank/architecture/code-organization.md` for directory layout and project structure.

## YAML Schema (Minimum Viable)
```yaml
# Example: backend/config/agent_configs/sales.yaml

agent_type: "sales"                  # simple_chat | sales | simple_research | deep_research | digital_expert
display_name: "Sales Agent"

model_settings:
  model: "openai:gpt-4o"            # LLM id via OpenRouter
  temperature: 0.3
  max_tokens: 2000

memory:
  # Conversation summarization, titles, and context window policy
  auto_summary_threshold: 10         # Trigger summary every N messages
  summary_model: "gpt-4o-mini"      # Cost-optimized summary model
  title_revision_model: "gpt-4o-mini"
  context_window_messages: 30        # Recent message window to pass to the LLM

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

Notes:
- Secrets (keys/tokens) stay in environment variables or secret stores, not YAML.
- YAML values define behavior, thresholds, and toggles to keep code paths generic.

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
- Keep model ids and thresholds out of code paths; reference `model_settings` and `memory` sections.
- Ensure endpoint transition plan remains compatible: legacy `/chat` and `/events/stream` plus `/agents/{type}/chat`.


