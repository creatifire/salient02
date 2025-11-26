# FEATURE-0026-010 Refactoring Setup Complete ✅

**Date**: November 26, 2025  
**Branch**: `refactor/extract-services-simple-chat`  
**Commit**: c8735a8

---

## What We've Done

### 1. ✅ Created Feature Branch
```bash
git checkout -b refactor/extract-services-simple-chat
```

### 2. ✅ Reviewed Refactoring Plan
- **FEATURE-0026-010**: Extract Services (Modularization)
- **Goal**: Reduce `simple_chat.py` from 1,386 lines → ~700-800 lines
- **5 Chunks** planned with detailed verification checklists
- **Critical preservations**: Prompt breakdown, cost tracking, tool calls

### 3. ✅ Created Testing Infrastructure

**New Files Created:**

1. **`backend/tests/manual/test_baseline_metrics.py`**
   - Captures baseline metrics before refactoring
   - Tests 3 scenarios: simple query, directory query, knowledge query
   - Measures: response times, cost tracking, token counts, database persistence
   - Saves results to `test_results/baseline_TIMESTAMP.json`

2. **`backend/tests/manual/test_refactor_checkpoint.py`**
   - Runs after each chunk to verify no regressions
   - Compares current metrics against baseline
   - Allows 20% variance in response times
   - Allows 5% variance in token counts
   - Flags any cost tracking or database persistence regressions
   - Saves results to `test_results/checkpoint_CHUNK_TIMESTAMP.json`

3. **`backend/REFACTORING-WORKFLOW.md`**
   - Complete workflow documentation
   - Step-by-step instructions for each chunk
   - Verification checklists
   - Commit message templates
   - Rollback strategies

### 4. ✅ Identified Reusable Tests

From `backend/tests/manual/`:
- ✅ `test_chat_endpoint.py` - Non-streaming verification
- ✅ `test_streaming_endpoint.py` - Streaming verification
- ✅ `test_data_integrity.py` - Database integrity checks
- ✅ `test_config_loader.py` - Configuration loading

**No new tests needed** - existing manual tests provide excellent coverage!

### 5. ✅ Committed Setup
```bash
git commit -m "feat(refactor): add baseline testing and checkpoint verification"
```

---

## Next Steps

### Step 1: Capture Baseline (DO THIS NOW)

```bash
# Terminal 1: Start the server
cd backend
uvicorn app.main:app --reload

# Terminal 2: Capture baseline
cd backend
python tests/manual/test_baseline_metrics.py
```

**Expected Output:**
```
═══════════════════════════════════════════════════════════
          BASELINE METRICS CAPTURE - FEATURE-0026-010
═══════════════════════════════════════════════════════════

🎯 Target Agent: Wyckoff Info Chat
🌐 Base URL: http://localhost:8000
🧪 Test Scenarios: 3
⏰ Timestamp: 2025-11-26T20:45:00

═══════════════════════════════════════════════════════════
                    NON-STREAMING TESTS
═══════════════════════════════════════════════════════════

📝 Testing: simple_query
💬 Message: Hello, can you help me?
✅ Response received in 2341ms
📦 Model: google/gemini-2.5-flash
📈 Tokens: 5172 in | 124 out | 5296 total
💰 Cost: $0.001862

[... more tests ...]

═══════════════════════════════════════════════════════════
✅ BASELINE CAPTURE COMPLETE - ALL TESTS PASSED
═══════════════════════════════════════════════════════════

💾 Results saved to: test_results/baseline_20251126_204500.json
```

### Step 2: Review Baseline Results

Check that all metrics were captured:
- ✅ Response times recorded
- ✅ Cost tracking working
- ✅ Token counts accurate
- ✅ Database persistence confirmed

### Step 3: Begin CHUNK-0026-010-001

**What**: Create CostTrackingService  
**Estimated Time**: 3-4 hours  
**Lines Extracted**: ~300 lines

**Tasks:**
1. Create `backend/app/services/cost_tracking_service.py`
2. Extract cost extraction logic from `simple_chat.py` lines 570-610
3. Extract streaming cost calculation from lines 1019-1110
4. Extract fallback pricing logic from lines 1053-1089
5. Update `simple_chat.py` to use new service
6. **Keep old code commented** with `# OLD CODE - REMOVE AFTER VERIFICATION`

**Verification Checklist** (from plan):
- [ ] CostTrackingService created with all methods
- [ ] Cost extraction works for non-streaming responses
- [ ] Cost calculation works for streaming responses
- [ ] Fallback pricing loads correctly
- [ ] Token counts accurate (compare before/after)
- [ ] Cost values match OpenRouter values
- [ ] Admin UI shows correct cost data
- [ ] No cost tracking errors in logs

**After completing CHUNK-001:**
```bash
python tests/manual/test_refactor_checkpoint.py --chunk CHUNK-0026-010-001
```

If checkpoint passes:
```bash
git add -A
git commit -m "feat(refactor): complete CHUNK-0026-010-001 - CostTrackingService

- Extract cost tracking logic to dedicated service
- Preserve all cost calculation functionality
- Maintain OpenRouter cost extraction
- Keep genai-prices integration

Testing:
- Checkpoint verification passed
- Cost tracking accuracy verified
- Admin UI displays costs correctly

Refs: CHUNK-0026-010-001"
```

---

## Workflow Summary

For each chunk:

1. **Implement** → Make changes, keep old code commented
2. **Test** → Run checkpoint verification
3. **Verify** → Check Admin UI manually
4. **Commit** → If checkpoint passes
5. **Repeat** → Move to next chunk

After all 5 chunks:
- Remove all old commented code
- Run final verification
- Measure line count reduction
- Create PR

---

## Critical Success Factors

✅ **MUST Preserve**:
- Prompt breakdown capture in `llm_requests.meta`
- Assembled prompt storage in `llm_requests.assembled_prompt`
- Cost tracking accuracy
- Tool call extraction in `messages.meta`
- Multi-turn conversations (SystemPromptPart injection)
- Streaming and non-streaming functionality

✅ **Verification Required After Each Chunk**:
- Checkpoint script passes
- Admin UI displays all data correctly
- No errors in Logfire
- Manual tests pass

✅ **Documentation**:
- Follow commit message conventions
- Update verification checklists
- Save all checkpoint results

---

## Questions?

Refer to:
- `backend/REFACTORING-WORKFLOW.md` - Complete workflow details
- `memorybank/project-management/0026-simple-admin-frontend.md` - Full plan (lines 4603-4969)
- `backend/tests/manual/README.md` - Manual testing guide

Ready to begin! 🚀

