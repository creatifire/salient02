<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# FEATURE-0026-010: Refactoring Workflow

This document describes the workflow for refactoring `simple_chat.py` as outlined in Epic 0026, Feature 010.

## Branch

```bash
git checkout refactor/extract-services-simple-chat
```

## Goal

Refactor `simple_chat.py` (1,386 lines) into modular, testable services (~700-800 lines) while preserving ALL functionality, especially:
- ✅ Prompt breakdown capture
- ✅ Cost tracking
- ✅ Tool call extraction
- ✅ Multi-turn conversations
- ✅ Streaming and non-streaming

## Workflow

### Before Starting Any Chunk

1. **Capture Baseline** (first time only):
   ```bash
   cd backend
   # Start server in terminal 1
   uvicorn app.main:app --reload
   
   # Run baseline capture in terminal 2
   python tests/manual/test_baseline_metrics.py
   ```
   
   This creates `test_results/baseline_TIMESTAMP.json` with metrics to compare against.

2. **Review Current State**:
   - Read the chunk description in `memorybank/project-management/0026-simple-admin-frontend.md`
   - Understand what code is being extracted
   - Review the verification checklist

### During Chunk Implementation

3. **Make Changes**:
   - Create new service files
   - Extract code from `simple_chat.py`
   - **Keep old code commented out** during transition (mark with `# OLD CODE - REMOVE AFTER VERIFICATION`)
   - Update imports

4. **Test Incrementally**:
   - Test new service methods in isolation
   - Test integration with `simple_chat.py`
   - Verify server still starts without errors

### After Completing Each Chunk

5. **Run Checkpoint Verification**:
   ```bash
   python tests/manual/test_refactor_checkpoint.py --chunk CHUNK-0026-010-001
   ```
   
   This will:
   - Run all test scenarios
   - Compare against baseline metrics
   - Report any regressions
   - Save results to `test_results/checkpoint_CHUNK_TIMESTAMP.json`

6. **Review Verification Checklist**:
   - Go through the chunk-specific checklist in the plan document
   - Manually verify critical items (especially prompt breakdown, cost tracking)
   - Check Logfire for any errors

7. **Run Manual Tests** (optional, for extra confidence):
   ```bash
   # Test non-streaming
   python tests/manual/test_chat_endpoint.py
   
   # Test streaming
   python tests/manual/test_streaming_endpoint.py
   
   # Test database integrity
   python tests/manual/test_data_integrity.py
   ```

8. **Admin UI Verification**:
   - Open `http://localhost:4321/admin/sessions.html`
   - Find the test sessions created by checkpoint script
   - Verify:
     - ✅ Prompt breakdown displays correctly
     - ✅ Full assembled prompt visible
     - ✅ Cost tracking shows values
     - ✅ Tool calls captured
     - ✅ LLM metadata present

9. **Commit Checkpoint**:
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

### If Checkpoint Fails

10. **Debug and Fix**:
    - Review regression details from checkpoint output
    - Compare baseline vs checkpoint JSON files
    - Check Logfire for errors
    - Fix issues
    - Re-run checkpoint verification
    - Do NOT proceed to next chunk until checkpoint passes

### Final Steps (After All Chunks Complete)

11. **Remove Old Code**:
    - Find all `# OLD CODE` comments
    - Remove commented-out code
    - Clean up imports

12. **Final Verification**:
    ```bash
    # Run all manual tests
    python tests/manual/test_chat_endpoint.py
    python tests/manual/test_streaming_endpoint.py
    python tests/manual/test_data_integrity.py
    
    # Run final checkpoint
    python tests/manual/test_refactor_checkpoint.py --chunk FINAL
    ```

13. **Measure Impact**:
    ```bash
    # Count lines in simple_chat.py
    wc -l app/agents/simple_chat.py
    
    # Expected: ~700-800 lines (down from 1,386)
    ```

14. **Create PR**:
    ```bash
    git push origin refactor/extract-services-simple-chat
    ```

## Chunk Order

Execute chunks in this order:

1. **CHUNK-0026-010-001**: Create CostTrackingService (~300 lines extracted)
2. **CHUNK-0026-010-002**: Enhance MessagePersistenceService (~200 lines extracted)
3. **CHUNK-0026-010-003**: Create AgentExecutionService (~150 lines extracted)
4. **CHUNK-0026-010-004**: Create ConfigurationService (~100 lines extracted)
5. **CHUNK-0026-010-005**: Update simple_chat.py to use all services (integration)

## Critical Verification Items

After EVERY chunk, verify these work:

- ✅ Non-streaming chat works (curl test)
- ✅ Streaming chat works (browser test)
- ✅ Cost tracking accurate (check database)
- ✅ Token counts correct (compare to baseline)
- ✅ Messages saved (check sessions table)
- ✅ **Prompt breakdown captured** (check llm_requests.meta)
- ✅ **Admin UI displays prompt breakdown** (visual check)
- ✅ Tool calls captured (check messages.meta)
- ✅ Directory tools work (test query)
- ✅ Vector search works (test query)
- ✅ No errors in Logfire

## Test Results Location

All test results are saved to:
```
backend/test_results/
├── baseline_TIMESTAMP.json          # Initial baseline
├── checkpoint_CHUNK-001_TIMESTAMP.json
├── checkpoint_CHUNK-002_TIMESTAMP.json
├── checkpoint_CHUNK-003_TIMESTAMP.json
├── checkpoint_CHUNK-004_TIMESTAMP.json
├── checkpoint_CHUNK-005_TIMESTAMP.json
└── checkpoint_FINAL_TIMESTAMP.json  # Final verification
```

## Rollback Strategy

If a chunk introduces regressions that can't be quickly fixed:

```bash
# Revert to previous checkpoint
git reset --hard HEAD~1

# Or revert specific chunk
git revert <commit-hash>

# Fix issues offline
# Re-implement chunk
# Run checkpoint again
```

## Success Criteria

Final verification must show:
- ✅ simple_chat.py < 800 lines
- ✅ All services have test coverage
- ✅ No functional regressions (checkpoint passes)
- ✅ Performance within 5% of baseline
- ✅ Cost tracking accuracy maintained
- ✅ All manual tests pass
- ✅ Logfire shows no errors

## Documentation

After completion, update:
- `memorybank/architecture/agent-and-tool-design.md` - Document new services
- `memorybank/project-management/0026-simple-admin-frontend.md` - Mark chunks complete
- This file - Add lessons learned section

---

**Remember**: The goal is maintainability, not just line count. Every extracted service should have a clear, single responsibility and be independently testable.

