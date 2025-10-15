# Agent Configurations

> **Last Updated**: October 15, 2025

This directory contains YAML configuration files and system prompts for all agent instances in the multi-tenant architecture.

## Directory Structure

```
agent_configs/
├── default_account/
│   ├── simple_chat1/      # Primary demo agent
│   └── simple_chat2/      # Secondary test agent
├── agrofresh/
│   └── agro_info_chat1/   # Agricultural products info
├── wyckoff/
│   └── wyckoff_info_chat1/ # Hospital info + doctor search
└── acme/
    └── acme_chat1/        # Testing instance
```

## Agent Access Map

### default_account/simple_chat1

**Model**: `moonshotai/kimi-k2-0905`  
**Purpose**: Primary demo agent for testing core functionality

**Accessible From**:
- ✅ **System URL** (not for production): http://localhost:8000/
- ✅ **Floating Widget**: http://localhost:4321/demo/widget
- ✅ **Simple Chat Page**: http://localhost:4321/demo/simple-chat
- ✅ **HTMX Chat**: http://localhost:4321/htmx-chat.html
- ⚠️ **Iframe Demo**: http://localhost:4321/demo/iframe (needs bug fixes)

### default_account/simple_chat2

**Model**: `openai/gpt-oss-120b`  
**Purpose**: Secondary test agent for multi-model verification

**Accessible From**:
- ✅ **HTMX Chat 2**: http://localhost:4321/htmx-chat2.html

### agrofresh/agro_info_chat1

**Model**: `deepseek/deepseek-chat-v3-0324`  
**Purpose**: Agricultural products information assistant

**Accessible From**:
- ✅ **AgroFresh Site**: http://localhost:4321/agrofresh (all pages via footer widget)

### wyckoff/wyckoff_info_chat1

**Model**: `qwen/qwen3-235b-a22b-thinking-2507`  
**Purpose**: Hospital information + AI-powered doctor search (vector search enabled)

**Accessible From**:
- ✅ **Wyckoff Hospital Site**: http://localhost:4321/wyckoff (all pages via footer widget)

### acme/acme_chat1

**Model**: `mistralai/mistral-small-3.2-24b-instruct`  
**Purpose**: Testing instance with higher temperature (0.5)

**Accessible From**:
- 🚧 **TBD**: Not yet assigned to demo site

## Configuration Files

Each agent instance directory contains:

```
agent_name/
├── config.yaml         # Agent configuration (model, tools, context management)
└── system_prompt.md    # Agent system prompt (personality, instructions)
```

### config.yaml Structure

```yaml
agent_type: "simple_chat"
account: "account_slug"
instance_name: "agent_slug"
name: "Display Name"
description: "Agent description"

prompts:
  system_prompt_file: "./system_prompt.md"

model_settings:
  model: "provider/model-name"
  temperature: 0.3
  max_tokens: 2000

tools:
  vector_search:
    enabled: true/false
  web_search:
    enabled: true/false
  conversation_management:
    enabled: true

context_management:
  history_limit: 50
  context_window_tokens: 8000
```

## Backend Endpoint Pattern

All agents follow the multi-tenant endpoint pattern:

```
GET  /accounts/{account_slug}/agents/{agent_slug}/history
POST /accounts/{account_slug}/agents/{agent_slug}/chat
GET  /accounts/{account_slug}/agents/{agent_slug}/stream
```

**Examples**:
- `GET /accounts/default_account/agents/simple_chat1/history`
- `POST /accounts/agrofresh/agents/agro_info_chat1/chat`
- `GET /accounts/wyckoff/agents/wyckoff_info_chat1/stream?message=...`

## Frontend Integration

### Shadow DOM Widget (Recommended)

Load `chat-widget.js` with configuration:

```html
<script>
  window.__SALIENT_WIDGET_CONFIG = {
    account: 'agrofresh',
    agent: 'agro_info_chat1',
    backend: 'http://localhost:8000',
    allowCross: true,
    debug: true  // Enable in development
  };
</script>
<script src="/widget/chat-widget.js?v=11"></script>
```

### Inline Implementation

Vanilla JavaScript with direct endpoint calls (see `htmx-chat.html`, `simple-chat.astro`).

### Iframe (Future)

Client-hostable wrapper for maximum isolation (deferred, see Epic 0022-001-004-02).

## Model Diversity

Each agent uses a different LLM model to demonstrate multi-model support:

| Agent | Model | Provider | Context | Cost ($/1M in/out) |
|-------|-------|----------|---------|-------------------|
| simple_chat1 | kimi-k2-0905 | Moonshot AI | 256k | 0.39 / 1.90 |
| simple_chat2 | gpt-oss-120b | OpenAI | 120k | 0.04 / 0.40 |
| agro_info_chat1 | deepseek-chat-v3-0324 | DeepSeek | 64k | varies |
| wyckoff_info_chat1 | qwen3-235b-a22b-thinking-2507 | Qwen/Alibaba | 128k | varies |
| acme_chat1 | mistral-small-3.2-24b-instruct | Mistral AI | 32k | varies |

**Benefits**:
- ✅ Model-agnostic Pydantic AI implementation
- ✅ Provider diversity via OpenRouter
- ✅ Cost optimization per use case
- ✅ Performance comparison across domains
- ✅ Regression testing across capabilities

## Database Setup

Agents are registered in the `agent_instances` table:

```sql
SELECT ai.instance_slug, a.slug AS account_slug, ai.agent_type, ai.display_name
FROM agent_instances ai
JOIN accounts a ON ai.account_id = a.id
ORDER BY a.slug, ai.instance_slug;
```

**Required records**:
- Account: `default_account`, `agrofresh`, `wyckoff`, `acme`
- Agent instances: linked to accounts via `account_id`

## Adding a New Agent

1. **Create directory**: `mkdir -p agent_configs/{account}/{agent_name}/`
2. **Create config.yaml**: Define model, tools, context settings
3. **Create system_prompt.md**: Define agent personality and instructions
4. **Register in database**:
   ```sql
   INSERT INTO agent_instances (account_id, instance_slug, agent_type, display_name)
   VALUES (
     (SELECT id FROM accounts WHERE slug = 'account_name'),
     'agent_name',
     'simple_chat',
     'Agent Display Name'
   );
   ```
5. **Update this README**: Document URLs where agent is accessible
6. **Test**: Verify agent loads, streams correctly, tracks costs

## Testing Agents

**Manual Testing**:
1. Navigate to agent's demo URL
2. Send test message
3. Verify streaming works (chunks appear incrementally)
4. Verify markdown formatting applied after completion
5. Check chat history loads on page refresh

**Database Verification**:
```sql
-- Verify session, messages, and cost tracking
SELECT 
  s.id AS session_id,
  ai.instance_slug,
  COUNT(m.id) AS message_count,
  lr.total_cost
FROM sessions s
JOIN agent_instances ai ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.session_id = s.id
LEFT JOIN llm_requests lr ON lr.session_id = s.id
WHERE ai.instance_slug = 'agent_name'
GROUP BY s.id, ai.instance_slug, lr.total_cost
ORDER BY s.created_at DESC;
```

**Expected Results**:
- ✅ 1 session per browser
- ✅ 2 messages per exchange (1 user + 1 assistant)
- ✅ 1 LLM request per exchange
- ✅ Non-zero costs in `llm_requests` table
- ✅ No NULL `account_id` or `agent_instance_id` values

## Troubleshooting

**Agent not loading**:
- Check agent registered in `agent_instances` table
- Verify config.yaml syntax (valid YAML)
- Restart Python backend after config changes

**Streaming not working**:
- Check browser console for SSE errors
- Verify backend URL in widget config
- Check CORS settings if cross-origin

**Cost tracking shows zero**:
- Verify model in `fallback_pricing.yaml` or `genai-prices`
- Check logs for `streaming_cost_calculation_failed`
- Restart backend after pricing updates

**Markdown not formatting**:
- Verify `marked.js` loaded with `gfm: true`
- Check `renderMarkdownOrFallback()` called on `done` event
- Verify raw markdown stored in database

## Related Documentation

- **Epic 0017**: [Simple Chat Agent](../../memorybank/project-management/0017-simple-chat-agent.md)
- **Epic 0022**: [Multi-Tenant Architecture](../../memorybank/project-management/0022-multi-tenant-architecture.md)
- **Bug Report**: [Epic 0017 Bugs](../../memorybank/project-management/bugs-0017.md)
- **Cost Tracking**: [Pydantic AI Cost Tracking](../../memorybank/architecture/pydantic-ai-cost-tracking.md)
- **Endpoints**: [API Endpoints](../../memorybank/architecture/endpoints.md)

## Maintenance Notes

- **Verify pricing monthly**: Check OpenRouter for rate changes
- **Update system prompts**: As agent capabilities evolve
- **Monitor costs**: Review `llm_requests` table regularly
- **Test after updates**: Run regression tests on all agents
- **Update this README**: When adding/modifying agents

---

**Status**: 4 agents active, 1 TBD | **Testing**: BUG-0017-001 ✅ FIXED, BUG-0017-002 ✅ FIXED

