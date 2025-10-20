# Manual Verification Tests

This directory contains standalone Python scripts for manual verification and sanity checking during development.

## Purpose

**Manual tests** are different from automated pytest tests:

- ✅ **Run independently** - No pytest required, just `python script.py`
- ✅ **Quick sanity checks** - Verify critical functionality hasn't broken
- ✅ **Human-readable output** - Clear, formatted results for visual inspection
- ✅ **Development verification** - Run after making changes to confirm everything still works
- ✅ **Database integration** - Connect to real database to verify live data

## When to Use Manual Tests

Use manual tests when you want to:

1. **Quick verification** after making changes
2. **Visual confirmation** with formatted output
3. **Database inspection** with real data
4. **Debugging** to see detailed information
5. **Pre-commit checks** before pushing changes

## Available Tests

### `test_chat_endpoint.py`

Tests the multi-tenant chat endpoint with a real HTTP request to verify end-to-end functionality.

**What it tests:**
- POST `/accounts/{account}/agents/{instance}/chat` endpoint
- Real LLM integration via OpenRouter
- Response structure (response, usage, model fields)
- Token usage tracking
- Actual AI model responses

**Prerequisites:**
- FastAPI server must be running (`uvicorn app.main:app --reload`)
- Database initialized with seed data
- OpenRouter API key in `.env`

**How to run:**
```bash
# Terminal 1: Start the server
cd backend
uvicorn app.main:app --reload

# Terminal 2: Run the test
cd backend
python tests/manual/test_chat_endpoint.py
```

**Expected output:**
```
📍 Endpoint: http://localhost:8000/accounts/default_account/agents/simple_chat1/chat
💬 Message: What LLM are you and what is your knowledge cutoff date?

✅ Response received in 2.34s

🤖 LLM Response:
--------------------------------------------------------------------------------
I am Kimi, an AI assistant powered by Moonshot AI. My knowledge cutoff date 
is September 2024...
--------------------------------------------------------------------------------

📦 Model: moonshotai/kimi-k2-0905
📈 Token Usage:
  - input_tokens: 45
  - output_tokens: 89
  - total_tokens: 134

✅ All required fields present
✅ TEST PASSED
```

### `test_data_integrity.py` 🆕

**Comprehensive multi-agent database integrity verification script** that tests all 5 multi-tenant agent instances to ensure proper data model implementation after Priority 3 changes.

**What it tests:**
- **Sessions table**: account_id, agent_instance_id, agent_instance_slug populated correctly
- **Messages table**: session_id, llm_request_id FK, role/content validation
- **LLM_requests table**: Denormalized fields (account_slug, agent_type, completion_status)
- **Cost tracking**: prompt_cost, completion_cost, total_cost non-zero for successful requests
- **Multi-tenant isolation** (all 3 scenarios):
  - Session-level: Messages don't leak between sessions
  - Agent-level: Data properly attributed within account
  - Account-level: Complete data isolation between accounts

**Prerequisites:**
- FastAPI server must be running (`uvicorn app.main:app --reload`)
- Database initialized with multi-tenant schema (Epic 0022)
- All 5 agents configured: agrofresh/agro_info_chat1, wyckoff/wyckoff_info_chat1, default_account/simple_chat1, default_account/simple_chat2, acme/acme_chat1

**How to run:**
```bash
# Rich output (default) - ASCII tables with colors
python backend/tests/manual/test_data_integrity.py

# Simple output - grep-friendly plain text
python backend/tests/manual/test_data_integrity.py --format simple

# JSON output - for CI/CD integration
python backend/tests/manual/test_data_integrity.py --format json > results.json

# Strict mode - exit 1 on any failure
python backend/tests/manual/test_data_integrity.py --strict
```

**Expected output (rich format):**
```
╔════════════════════════════════════════════════════════════════════════════════╗
║          MULTI-AGENT DATA INTEGRITY VERIFICATION REPORT                        ║
╚════════════════════════════════════════════════════════════════════════════════╝

AGENT VERIFICATION RESULTS
┌─────────────────────────────────┬────────┬──────────┬──────────┬──────────┬────────┬───────────┐
│ Agent                           │ Status │ Sessions │ Messages │ LLM_Reqs │ Costs  │ Isolation │
├─────────────────────────────────┼────────┼──────────┼──────────┼──────────┼────────┼───────────┤
│ agrofresh/agro_info_chat1       │ ✅ PASS│    ✅     │    ✅     │    ✅     │   ✅    │     ✅     │
│ wyckoff/wyckoff_info_chat1      │ ✅ PASS│    ✅     │    ✅     │    ✅     │   ✅    │     ✅     │
│ default_account/simple_chat1    │ ✅ PASS│    ✅     │    ✅     │    ✅     │   ✅    │     ✅     │
│ default_account/simple_chat2    │ ✅ PASS│    ✅     │    ✅     │    ✅     │   ✅    │     ✅     │
│ acme/acme_chat1                 │ ✅ PASS│    ✅     │    ✅     │    ✅     │   ✅    │     ✅     │
└─────────────────────────────────┴────────┴──────────┴──────────┴──────────┴────────┴───────────┘

ISOLATION VERIFICATION (3 scenarios)
┌────────────────────────────┬───────────────────────────────────────────────────┐
│ Scenario                   │ Result                                            │
├────────────────────────────┼───────────────────────────────────────────────────┤
│ Session-level isolation    │ ✅ PASS - No cross-session data leakage           │
│ Agent-level isolation      │ ✅ PASS - Agents within account isolated          │
│ Account-level isolation    │ ✅ PASS - Complete account separation             │
└────────────────────────────┴───────────────────────────────────────────────────┘

✅ ALL CHECKS PASSED (5/5 agents verified)

💾 Test data preserved for manual inspection
🧹 Run cleanup_test_data.py to delete test data
```

**Configuration:**
Edit `test_data_integrity_config.yaml` to customize:
- Test prompts per agent
- Expected keywords for validation
- Backend URL and timeouts
- Field validation rules

**Important Notes:**
- ⚠️ **Test data is preserved by default** - Manual inspection is required
- 🧹 Use `cleanup_test_data.py` to delete test data after verification
- 🚫 **Legacy endpoints excluded** - Only tests multi-tenant agents (see BUG-0017-007)
- 📊 **See**: Epic 0017-005-003 in project management docs for detailed implementation

### `cleanup_test_data.py` 🆕

**Safe test data cleanup script** with confirmation prompts, dry-run mode, and production environment protection.

**What it does:**
- Deletes test data created by `test_data_integrity.py`
- Removes sessions, messages, and llm_requests in proper order (respects foreign keys)
- Provides summary of what will be deleted before confirmation
- Supports selective deletion by agent or time window

**Safety features:**
- ✅ Interactive confirmation prompt (unless --all flag)
- ✅ Dry-run mode to preview deletions
- ✅ Production environment detection and blocking
- ✅ Selective deletion by agent
- ✅ Time window filtering (default: last 60 minutes)

**How to run:**
```bash
# Interactive mode with confirmation
python backend/tests/manual/cleanup_test_data.py

# Dry-run - see what would be deleted
python backend/tests/manual/cleanup_test_data.py --dry-run

# Delete specific agent's test data
python backend/tests/manual/cleanup_test_data.py --agent wyckoff/wyckoff_info_chat1

# Custom time window (last 120 minutes)
python backend/tests/manual/cleanup_test_data.py --time-window 120

# Skip confirmation (dangerous!)
python backend/tests/manual/cleanup_test_data.py --all
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════════════════
  TEST DATA CLEANUP SCRIPT
═══════════════════════════════════════════════════════════════════════════════

⏱️  Time window: Last 60 minutes

Data to be deleted:

  Sessions:           5
  Messages:          10
  LLM Requests:       5

  Affected agents:
    • agrofresh/agro_info_chat1
    • wyckoff/wyckoff_info_chat1
    • default_account/simple_chat1
    • default_account/simple_chat2
    • acme/acme_chat1

⚠️  WARNING: About to delete test data

Are you sure you want to delete this data? [y/N]: y

Deleting data...

═══════════════════════════════════════════════════════════════════════════════
  DELETION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

  ✓ Sessions deleted:           5
  ✓ Messages deleted:          10
  ✓ LLM Requests deleted:       5

✅ Cleanup complete!
```

**Typical Workflow:**
```bash
# 1. Run integrity tests
python backend/tests/manual/test_data_integrity.py

# 2. Review test results and manually inspect database
psql $DATABASE_URL -c "SELECT account_slug, agent_instance_slug, COUNT(*) FROM llm_requests GROUP BY 1,2;"

# 3. Preview cleanup (dry-run)
python backend/tests/manual/cleanup_test_data.py --dry-run

# 4. Clean up test data
python backend/tests/manual/cleanup_test_data.py
```

### `test_config_loader.py`

Verifies that agent instance configuration loading works correctly across multiple accounts and instances.

**What it tests:**
- Database queries for agent instances
- Config file loading from disk
- Model settings extraction (different LLMs per instance)
- Context settings (history limits)
- Tool settings (Pinecone namespaces)
- Account isolation (acme vs default_account)
- Multi-instance support (multiple agents per account)

**How to run:**
```bash
cd backend
python tests/manual/test_config_loader.py
```

**Expected output:**
```
🧪 Testing Agent Instance Configuration Loading
======================================================================

📋 Loading: default_account/simple_chat1
----------------------------------------------------------------------
✅ Instance loaded successfully!
   Account: default_account
   Instance: simple_chat1
   Model: moonshotai/kimi-k2-0905
   Temperature: 0.3
   ...

📊 CONFIGURATION SUMMARY
======================================================================
Account              Instance        Model                           Temp   History
---------------------------------------------------------------------------------
default_account      simple_chat1    moonshotai/kimi-k2-0905        0.3    50
default_account      simple_chat2    openai/gpt-oss-120b            0.3    50
acme                 acme_chat1      qwen/qwen3-vl-235b-a22b-...    0.5    30

✅ ALL CONFIGURATIONS LOADED SUCCESSFULLY
```

## Adding New Manual Tests

When creating new manual tests:

1. **Descriptive names**: `test_<feature>_<aspect>.py`
2. **Human-readable output**: Use emojis, tables, and clear formatting
3. **Exit codes**: Return 0 for success, 1 for failure
4. **Standalone**: Include all necessary imports and database initialization
5. **Document here**: Add a section explaining what it tests and how to run it

## Best Practices

- 🔧 **Run before committing** - Quick check that your changes work
- 📝 **Keep updated** - If functionality changes, update the tests
- 🎯 **Focus on critical paths** - Test the most important functionality
- 🚫 **Don't replace pytest** - These complement, not replace, automated tests
- 💡 **Make them informative** - Clear output helps with debugging

## Relationship to Automated Tests

| Test Type | Purpose | When to Run | Output |
|-----------|---------|-------------|--------|
| **Manual Tests** | Quick verification during development | On demand by developer | Human-readable, formatted |
| **Pytest Unit Tests** | Isolated component testing | Every commit (CI/CD) | Pass/fail, coverage stats |
| **Pytest Integration Tests** | End-to-end workflows | Every commit (CI/CD) | Pass/fail, detailed logs |

## Logfire Observability

The application uses **Logfire** for LLM tracing and request monitoring. Logfire automatically captures:

- 🔍 **Full request traces**: HTTP → chat endpoint → agent → Pydantic AI → OpenRouter
- 🤖 **LLM interactions**: See what model was requested vs. what model OpenRouter actually used
- 💰 **Cost tracking**: Token usage and costs for each LLM call
- ⏱️ **Performance**: End-to-end latency and bottleneck identification
- 🔗 **Correlation**: All spans for a single request share the same trace ID

### Accessing Logfire UI

1. **Open Logfire Dashboard**: https://logfire.pydantic.dev
2. **Find Your Traces**: Look for traces from your recent test runs
3. **Inspect LLM Calls**: Click on any trace to see the full execution flow

### Key OpenTelemetry GenAI Attributes

Logfire automatically captures these critical attributes for every LLM call:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `gen_ai.request.model` | Model we asked OpenRouter to use | `"qwen/qwen3-vl-235b-a22b-instruct"` |
| `gen_ai.response.model` | Model OpenRouter actually used | `"moonshotai/kimi-k2-0905"` ⚠️ |
| `gen_ai.usage.input_tokens` | Tokens in the prompt | `45` |
| `gen_ai.usage.output_tokens` | Tokens in the response | `89` |
| `gen_ai.usage.total_tokens` | Total tokens used | `134` |
| `gen_ai.usage.total_cost` | Cost in USD | `0.00023` |

### Debugging Model Routing Issues

**Problem**: Agent configured for Model A but responds as Model B?

**Solution**: Use Logfire to compare `gen_ai.request.model` vs `gen_ai.response.model`:

1. Run manual test: `python tests/manual/test_chat_endpoint.py`
2. Open Logfire UI: https://logfire.pydantic.dev
3. Find the trace for your test (search by timestamp or trace ID)
4. Click on the LLM span to see GenAI attributes
5. Compare:
   - **Request model** = what we asked for in `config.yaml`
   - **Response model** = what OpenRouter actually used
6. If they differ → OpenRouter is routing/falling back to different models

### Logfire Setup (for reference)

The app is already configured for Logfire. If you need to set it up from scratch:

1. Sign up for free account: https://logfire.pydantic.dev (1M spans/month free tier)
2. Get your `LOGFIRE_TOKEN` from account settings
3. Add to `.env` file: `LOGFIRE_TOKEN=your-token-here`
4. Restart the server

**Privacy Note**: Logfire data is stored in Pydantic's cloud (US/EU regions available). For on-premise deployments, you can use a local OpenTelemetry collector instead.

## Example Workflow

```bash
# 1. Make changes to instance_loader.py
vim app/agents/instance_loader.py

# 2. Quick manual verification
python tests/manual/test_config_loader.py

# 3. Check traces in Logfire UI (if testing LLM interactions)
open https://logfire.pydantic.dev

# 4. Run full test suite
pytest tests/ -v

# 5. Commit if all pass
git add -A
git commit -m "feat: improve instance loader"
```

---

**Note**: These tests require a running database and valid configuration files. Ensure your `.env` is properly configured and the database is initialized. For LLM tracing, ensure `LOGFIRE_TOKEN` is set in `.env`.

