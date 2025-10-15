# Agent Configuration Reference

> **Last Updated**: October 15, 2025

## Agents & Access URLs

| Agent | Model | Frontend URLs |
|-------|-------|---------------|
| **default_account/simple_chat1** | `moonshotai/kimi-k2-0905` | http://localhost:8000/ (system)<br>http://localhost:4321/demo/widget<br>http://localhost:4321/demo/simple-chat<br>http://localhost:4321/htmx-chat.html<br>http://localhost:4321/demo/iframe ⚠️ needs fixes |
| **default_account/simple_chat2** | `openai/gpt-oss-120b` | http://localhost:4321/htmx-chat2.html |
| **agrofresh/agro_info_chat1** | `deepseek/deepseek-chat-v3-0324` | http://localhost:4321/agrofresh (footer widget) |
| **wyckoff/wyckoff_info_chat1** | `qwen/qwen3-235b-a22b-thinking-2507` | http://localhost:4321/wyckoff (footer widget, vector search enabled) |
| **acme/acme_chat1** | `mistralai/mistral-small-3.2-24b-instruct` | 🚧 TBD |

## Configuration

Each agent directory: `{account}/{agent}/config.yaml` + `system_prompt.md`

**Backend endpoints**: `/accounts/{account}/agents/{agent}/{history|chat|stream}`

## Testing

1. Navigate to URL
2. Send message
3. Verify: streaming works, markdown formats, history loads on refresh

**Check DB**:
```sql
SELECT ai.instance_slug, COUNT(m.id) AS msgs, lr.total_cost
FROM agent_instances ai
LEFT JOIN sessions s ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.session_id = s.id
LEFT JOIN llm_requests lr ON lr.session_id = s.id
WHERE ai.instance_slug = 'agent_name'
GROUP BY ai.instance_slug, lr.total_cost;
```

Expected: 1 session, 2 messages per exchange, non-zero costs

---

**Status**: 4 active, 1 TBD | **Bugs**: BUG-0017-001 ✅ FIXED, BUG-0017-002 ✅ FIXED

