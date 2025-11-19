# Pydantic AI Message History and SystemPromptPart Requirement

**Date:** 2025-01-19  
**Category:** Framework Integration, Multi-Turn Conversations  
**Impact:** Critical - Affects all multi-turn agent conversations  
**Status:** Resolved

## Problem Statement

Multi-turn conversations stopped working after the first query. The LLM would successfully call tools on the first user message but would refuse to call tools on subsequent messages, claiming it "cannot directly access" information despite tools being available.

**Symptoms:**
- Turn 1: ✅ Tools called correctly, accurate responses
- Turn 2+: ❌ No tool calls, LLM claims lack of access
- Database confirmed tools were being sent to the API on all turns
- Session example: `019a99c9-c281-74b2-ac8c-8552ec736c9b`

## Investigation Process

### Phase 1: Single-Turn Investigation

Created `tool_calling_wyckoff.py` to test tool calling with real Wyckoff data:
- **Result:** All single-turn queries worked perfectly
- **Conclusion:** Tools, prompts, and Pydantic AI integration were correct

### Phase 2: Multi-Turn Investigation

Created `tool_calling_wyckoff_multiturn.py` to test passing `message_history`:

```python
# Turn 1 (works)
result1 = await agent.run(query1, deps=mock_deps)

# Extract message history (like production does)
message_history = result1.all_messages()

# Turn 2 (reproduces production bug)
result2 = await agent.run(query2, deps=mock_deps, message_history=message_history)
```

**Critical Discovery:**

When inspecting `message_history` structure, found:

```
Message 1: ModelRequest
   Parts count: 2
      Part 1: SystemPromptPart  ← KEY FINDING!
      Part 2: UserPromptPart
```

The first `ModelRequest` in the message history contained a `SystemPromptPart`!

## Root Cause

### How Pydantic AI Handles System Prompts

**Single-turn (fresh conversation):**
```python
agent = Agent(model, system_prompt="You are helpful...")
result = await agent.run("query", deps=deps)
```
- Pydantic AI automatically creates a `SystemPromptPart`
- Adds it to the first `ModelRequest` internally
- Sends to LLM with proper `systemInstruction` field (Gemini) or system message (OpenAI)

**Multi-turn (with message_history):**
```python
result = await agent.run("query", deps=deps, message_history=previous_messages)
```
- Pydantic AI **does NOT** automatically inject `SystemPromptPart`
- It expects `message_history` to already contain it
- If missing, LLM receives conversation without system instructions
- LLM loses context about its role, available tools, and behavior guidelines

### Our Production Bug

In `simple_chat.py`, the `load_conversation_history()` function (line 111) had:

```python
for msg in db_messages:
    if msg.role in ("human", "user"):
        pydantic_message = ModelRequest(...)
    elif msg.role == "assistant":
        pydantic_message = ModelResponse(...)
    else:
        # Skip system messages - Pydantic AI handles them
        continue  # ← BUG: This is wrong for multi-turn!
```

**Why this was wrong:**
1. Database only stores user/assistant messages (not system prompts)
2. We load these into `message_history` without system prompt
3. Pass to `agent.run()` with incomplete history
4. Pydantic AI doesn't add system prompt (assumes history is complete)
5. LLM receives no system instructions on turn 2+
6. LLM behavior degrades without context

## Solution

### Implementation

Inject `SystemPromptPart` into the first `ModelRequest` after loading history:

```python
from pydantic_ai.messages import SystemPromptPart

# After loading message_history and creating agent (which has system_prompt text)
if message_history and len(message_history) > 0:
    first_msg = message_history[0]
    if isinstance(first_msg, ModelRequest):
        # Check if SystemPromptPart already exists
        has_system_prompt = any(isinstance(part, SystemPromptPart) for part in first_msg.parts)
        
        if not has_system_prompt:
            # Inject SystemPromptPart at the beginning
            system_prompt_part = SystemPromptPart(content=system_prompt)
            new_parts = [system_prompt_part] + list(first_msg.parts)
            message_history[0] = ModelRequest(parts=new_parts)
```

### Files Modified

1. **`backend/app/agents/simple_chat.py`**:
   - Added `SystemPromptPart` to imports (line 28)
   - Injected system prompt after loading history (lines 494-515)
   - Applied same fix to streaming path (lines 905-927)
   - Added debug logging for message_history structure

2. **`backend/investigate/tool-calling/tool_calling_wyckoff_multiturn.py`**:
   - Created multi-turn investigation script
   - Demonstrated the bug and validated the fix

## Key Learnings

### 1. Pydantic AI Message History Expectations

**When using `message_history` parameter:**
- Pydantic AI treats it as a **complete, reconstructed conversation**
- It does NOT auto-inject system prompts
- First `ModelRequest` MUST contain `SystemPromptPart`
- This mirrors how the LLM API actually works (system instruction sent once, not repeated)

### 2. Database Storage vs. Runtime Requirements

**Storage (Database):**
- Only store user and assistant messages
- System prompts are configuration, not conversation data
- They change between deployments (don't belong in history)

**Runtime (Pydantic AI):**
- Must reconstruct complete message history INCLUDING system prompt
- Inject system prompt from current agent configuration
- Ensures LLM always has latest system instructions

### 3. Single-Turn vs Multi-Turn Behavior

| Scenario | System Prompt Handling |
|----------|------------------------|
| **Fresh conversation** (`agent.run(msg, deps)`) | Pydantic AI auto-injects `SystemPromptPart` |
| **With history** (`agent.run(msg, deps, message_history)`) | Must be present in `message_history[0]` |
| **After result** (`result.all_messages()`) | `SystemPromptPart` is included in first message |

### 4. Framework Integration Pitfalls

**Common mistake:** Assuming frameworks handle everything automatically

**Reality:**
- Frameworks provide primitives, but developers must understand the full lifecycle
- Read documentation AND inspect runtime behavior (messages, API calls)
- Test multi-turn scenarios explicitly (single-turn often hides bugs)

### 5. Debugging Strategy That Worked

1. ✅ **Start simple:** Single-turn test (Phase 2D) validated core functionality
2. ✅ **Add complexity gradually:** Multi-turn test (Phase 2E) isolated the issue
3. ✅ **Inspect data structures:** `analyze_message_history()` revealed `SystemPromptPart`
4. ✅ **Trace execution:** Compare test script (works) vs production (fails)
5. ✅ **Verify at API level:** Check what's actually sent to LLM (Logfire, database)

## Broader Implications

### For Other Pydantic AI Users

**If you're building multi-turn conversations with Pydantic AI:**

1. **Always include system prompt in reconstructed history**
   ```python
   # After loading from database
   first_msg.parts = [SystemPromptPart(content=system_prompt)] + first_msg.parts
   ```

2. **Don't rely on automatic injection with message_history**
   - It won't happen
   - LLM will lose context
   - Behavior will degrade

3. **Test multi-turn scenarios explicitly**
   - Don't assume single-turn success means multi-turn works
   - Create investigation scripts that pass `message_history`

### For LangGraph / LangChain Users

This issue is specific to Pydantic AI's message history handling. Other frameworks may:
- Store system messages in conversation history
- Re-inject system prompts automatically
- Use different message format primitives

Always verify how YOUR framework handles system prompts in multi-turn conversations.

## Testing Verification

After implementing the fix:

1. **Clear database tables:** `messages`, `llm_requests`, `sessions`
2. **Restart backend** to load updated code
3. **Test multi-turn conversation:**
   - Query 1: "What's the cardiology department phone number?"
   - Query 2: "What about the emergency room?"
   - Query 3: "What's the number of the heart department?"

**Expected Results:**
- ✅ Tools called on ALL turns (not just turn 1)
- ✅ Accurate responses throughout conversation
- ✅ No "I cannot access" refusals
- ✅ Admin UI shows `SystemPromptPart` in first message

## References

- **Investigation Script:** `backend/investigate/tool-calling/tool_calling_wyckoff_multiturn.py`
- **Fix Implementation:** `backend/app/agents/simple_chat.py` (lines 494-515, 905-927)
- **Bug Session:** `019a99c9-c281-74b2-ac8c-8552ec736c9b`
- **Pydantic AI Docs:** https://ai.pydantic.dev/message-history/
- **Commit:** `c47a368` - "Fix multi-turn conversation tool calling by injecting SystemPromptPart"

## Related Issues

- **Context Window Sizing:** Initially suspected, but was not the root cause
- **LLM Context Poisoning:** Real issue, but secondary to missing system prompt
- **Tool Selection Prompt Engineering:** Improved, but couldn't overcome missing system instructions

## Conclusion

This was a subtle but critical bug caused by incomplete understanding of how Pydantic AI handles message history. The framework's behavior is correct and well-designed (system prompts are configuration, not conversation data), but requires developers to explicitly reconstruct complete message history including system instructions.

**Key Takeaway:** When working with LLM frameworks, always inspect runtime message structures, test multi-turn scenarios, and understand the distinction between what the framework auto-handles vs. what you must provide.

