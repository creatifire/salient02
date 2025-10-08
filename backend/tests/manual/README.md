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

## Example Workflow

```bash
# 1. Make changes to instance_loader.py
vim app/agents/instance_loader.py

# 2. Quick manual verification
python tests/manual/test_config_loader.py

# 3. Run full test suite
pytest tests/ -v

# 4. Commit if all pass
git add -A
git commit -m "feat: improve instance loader"
```

---

**Note**: These tests require a running database and valid configuration files. Ensure your `.env` is properly configured and the database is initialized.

