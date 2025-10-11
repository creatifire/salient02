# Lesson Learned: Pydantic AI Streaming Cost Tracking

**Date**: 2025-10-11  
**Issue**: Streaming requests were not capturing cost data from OpenRouter  
**Severity**: High - Revenue impact (lost billing data)  
**Status**: ✅ Resolved

---

## Problem Statement

When using Pydantic AI's `agent.run_stream()` for streaming responses, the `provider_details` field (which contains OpenRouter's cost data) was `NULL` in the final message response. This caused all streaming requests to record $0.00 costs, despite OpenRouter charging for the tokens used.

**Symptom**: 
- Non-streaming requests: ✅ Costs captured correctly
- Streaming requests: ❌ Costs always $0.00 (prompt_cost, completion_cost, total_cost all NULL)

**Database Evidence**:
```sql
-- Non-streaming request (working)
SELECT id, prompt_cost, completion_cost, total_cost, response_body->'provider_details' 
FROM llm_requests WHERE id = '591fd82e-4357-4f9a-86e5-aa030930181a';
-- Result: prompt_cost=0.0000408, completion_cost=0.003646, total_cost=0.0036868

-- Streaming request (broken)
SELECT id, prompt_cost, completion_cost, total_cost, response_body->'provider_details' 
FROM llm_requests WHERE id = '010923c6-9972-4454-974e-730cabe5d8dd';
-- Result: prompt_cost=0, completion_cost=0, total_cost=0, provider_details=NULL
```

---

## Root Cause Analysis

### 1. OpenRouter's Streaming Behavior (✅ Working Correctly)

From [OpenRouter documentation](https://openrouter.ai/docs/api-reference/overview):

> **"If your request has the `stream` parameter set to `true`, OpenRouter delivers responses as server-sent events (SSE). In this mode, the `usage` field is included only in the final message of the stream, accompanied by an empty `choices` array."**

**Key Point**: OpenRouter **DOES** send cost/usage data for streaming requests, but only in the **final SSE message**.

### 2. Pydantic AI's Message Handling (⚠️ Gotcha!)

**The Bug**: We were calling `result.new_messages()` after streaming completed:

```python
# ❌ WRONG - Incomplete messages during/after streaming
async with agent.run_stream(message, ...) as result:
    async for chunk in result.stream_text(delta=True):
        yield {"event": "message", "data": chunk}
    
    # This returns incomplete messages WITHOUT provider_details!
    new_messages = result.new_messages()
    latest_message = new_messages[-1]
    cost = latest_message.provider_details  # ← NULL for streaming!
```

**Why `new_messages()` Failed**:
- `result.new_messages()` returns messages added **in this run only**
- During streaming, these messages are **incomplete** - they don't include the final metadata
- The `provider_details` field is only populated when Pydantic AI processes the **final complete message**

**The Fix**: Use `result.all_messages()` **AFTER** streaming completes:

```python
# ✅ CORRECT - Complete messages after streaming finishes
async with agent.run_stream(message, ...) as result:
    async for chunk in result.stream_text(delta=True):
        yield {"event": "message", "data": chunk}
    
    # AFTER streaming completes, get ALL messages (includes complete metadata)
    all_messages = result.all_messages()
    latest_message = all_messages[-1]
    cost = latest_message.provider_details  # ← Now populated with cost data!
```

### 3. Documented Pattern We Missed

From our own `memorybank/design/account-agent-instance-architecture.md`:

```python
async with agent.run_stream(...) as result:
    async for chunk in result.stream_text(delta=True):
        chunks.append(chunk)
        yield {"event": "message", "data": chunk}
    
    # ✅ Track cost after stream completes
    usage = result.usage()  # Usage data available after stream completes
```

**We documented the solution ourselves** but used the wrong method (`new_messages()` vs `all_messages()`).

---

## The Fix

### Code Change

**File**: `backend/app/agents/simple_chat.py` (line ~584)

```python
# BEFORE (broken for streaming)
new_messages = result.new_messages()
if new_messages:
    latest_message = new_messages[-1]
    if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
        # Extract costs... (always NULL for streaming)

# AFTER (fixed)
all_messages = result.all_messages()  # ← KEY CHANGE
if all_messages:
    latest_message = all_messages[-1]
    if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
        # Extract costs... (now populated!)
```

### Why This Works

1. **During streaming**: Pydantic AI accumulates message parts as they arrive via SSE
2. **Final SSE message**: OpenRouter sends usage/cost data with empty `choices` array
3. **After streaming completes**: Pydantic AI processes the final message and populates `provider_details`
4. **`result.all_messages()`**: Returns the **complete, finalized** message history with all metadata

---

## Best Practices for Pydantic AI Streaming

### ✅ Do This

1. **Use `result.all_messages()` after streaming completes** to get complete metadata:
   ```python
   async with agent.run_stream(...) as result:
       async for chunk in result.stream_text(delta=True):
           yield chunk
       
       # Extract cost AFTER streaming completes
       all_messages = result.all_messages()
       latest = all_messages[-1]
       cost = latest.provider_details.get('cost')
   ```

2. **Access `result.usage()` for token counts** - always available after completion:
   ```python
   usage = result.usage()
   prompt_tokens = usage.input_tokens
   completion_tokens = usage.output_tokens
   ```

3. **Use context manager** - ensures proper cleanup and finalization:
   ```python
   async with agent.run_stream(...) as result:
       # Streaming logic
       pass
   # result is now finalized with complete metadata
   ```

### ❌ Don't Do This

1. **Don't use `result.new_messages()` for cost extraction in streaming**:
   ```python
   # ❌ This returns incomplete messages without provider_details
   new_messages = result.new_messages()
   ```

2. **Don't try to extract costs during streaming**:
   ```python
   # ❌ Metadata not available yet
   async for chunk in result.stream_text():
       cost = result.usage()  # Incomplete/unavailable
   ```

3. **Don't assume streaming and non-streaming behave the same**:
   ```python
   # Non-streaming: provider_details available immediately
   result = agent.run_sync(...)
   cost = result.new_messages()[-1].provider_details  # ✅ Works
   
   # Streaming: provider_details only available after completion
   async with agent.run_stream(...) as result:
       cost = result.new_messages()[-1].provider_details  # ❌ NULL
   ```

---

## Testing & Verification

### Manual Test Script

```bash
cd backend
python tests/manual/test_streaming_endpoint.py
```

**Expected**: Both streaming and non-streaming requests should show non-zero costs in the database.

### Database Verification

```sql
-- Check last 5 streaming requests
SELECT 
    id,
    created_at,
    prompt_cost,
    completion_cost,
    total_cost,
    prompt_tokens,
    completion_tokens,
    response_body->'provider_details'->'cost' as openrouter_cost
FROM llm_requests 
WHERE response_body->>'stream' = 'true'
ORDER BY created_at DESC 
LIMIT 5;
```

**Expected**: All costs should be non-zero if tokens > 0.

---

## Impact

**Before Fix**:
- ❌ Lost revenue tracking for all streaming requests (~50% of traffic)
- ❌ Inaccurate billing reports
- ❌ No cost-based optimization insights for streaming

**After Fix**:
- ✅ Accurate cost tracking for both streaming and non-streaming
- ✅ Complete billing data for revenue reports
- ✅ Proper cost attribution per session/agent

---

## Related Documentation

- **OpenRouter Docs**: [Streaming Responses](https://openrouter.ai/docs/api-reference/overview)
- **Pydantic AI Docs**: [Streaming Output](https://ai.pydantic.dev/docs/output/#streaming)
- **Pydantic AI API**: [Usage Tracking](https://ai.pydantic.dev/api/usage/)
- **Our Design Docs**: `memorybank/design/account-agent-instance-architecture.md` (line 265-303)
- **Cost Tracking Architecture**: `memorybank/architecture/tracking_llm_costs.md`

---

## Key Takeaways

1. **Read the docs carefully** - The solution was documented in both Pydantic AI and our own memorybank
2. **`new_messages()` ≠ `all_messages()`** in streaming context:
   - `new_messages()`: Returns messages added in this run (may be incomplete)
   - `all_messages()`: Returns complete, finalized message history
3. **OpenRouter streams cost data correctly** - The issue was on our side
4. **Test both streaming and non-streaming** - They have different data availability timing
5. **Trust the context manager** - `async with agent.run_stream()` ensures proper finalization

---

## Prevention

- ✅ **Code review checklist**: Verify `all_messages()` is used for cost extraction in streaming
- ✅ **Integration tests**: Compare streaming vs non-streaming cost tracking
- ✅ **Monitoring**: Alert on $0.00 costs when tokens > 0
- ✅ **Documentation**: Reference this lesson in cost tracking code comments

