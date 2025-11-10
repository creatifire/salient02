<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Dynamic Prompting Design Variations

Analysis of potential improvements to `dynamic-prompting.md` based on tool calling research and planning agent patterns.

---

## Summary

**Current Design Assessment**: The existing 6-phase approach in `dynamic-prompting.md` is sound. Most tool calling improvements are **optional enhancements** that can be added incrementally if real-world data shows they're needed.

**Recommendation**: Implement Phases 1-3 as designed. After Phase 3 validation with real multi-directory data (doctors + phone_directory), evaluate whether tool calling enhancements are necessary based on actual LLM performance.

---

## Potential Improvements from Tool Calling Research

### 1. Few-Shot Examples for Directory Selection (Phase 3 Enhancement)

**Research Finding**: 2-3 examples of correct tool calls improve consistency and parameter extraction

**Current Design**: Schema-driven directory selection guide (descriptions, use_for, example_queries, not_for)

**Potential Enhancement**:
- Add few-shot examples to `prompt_generator.py` output
- Example structure:
  ```markdown
  ## Example Directory Selection
  
  **Query**: "What's the ER number?"
  **Reasoning**: User asking for department phone number (not doctor info)
  **Tool Call**: search_directory(list_name="phone_directory", query="emergency")
  
  **Query**: "Find me a Spanish-speaking cardiologist"
  **Reasoning**: User seeking specific doctor by specialty and language
  **Tool Call**: search_directory(list_name="doctors", filters={"specialty": "Cardiology", "languages": "Spanish"})
  ```

**When to Add**:
- ✅ After Phase 3 if LLM struggles with multi-directory routing
- ⚠️ Skip if schema-driven selection guide already works well
- ⚠️ Adds ~200-300 tokens per example (increases cost)

**Implementation**: ~1-2 hours to add examples to `prompt_generator.py`

---

### 2. Chain-of-Thought for Tool Selection (Phase 3 Enhancement)

**Research Finding**: Explicit reasoning step improves tool selection accuracy in multi-tool scenarios

**Current Design**: LLM selects tools based on schema documentation (implicit reasoning)

**Potential Enhancement**:
- Add instruction to system prompt:
  ```markdown
  **Before calling a tool, briefly explain:**
  1. Which tool(s) are relevant to this query
  2. What information you're looking for
  3. Which directory/tool to search first
  
  Then make the appropriate tool call(s).
  ```

**Trade-offs**:
- ✅ Improves interpretability (see why tool was chosen)
- ✅ Better accuracy for ambiguous queries
- ⚠️ Increases latency (~50-100 tokens reasoning per query)
- ⚠️ Higher token costs

**When to Add**:
- ✅ After Phase 3 if multi-directory selection has >10% error rate
- ❌ Skip if single-directory agents (no selection needed)

**Implementation**: ~30 minutes to add CoT instruction

---

### 3. Output Validation + Retry Layer (Phase 4 Enhancement)

**Research Finding**: Validation layer with retry logic catches malformed tool calls

**Current Design**: Relies on Pydantic AI's native tool call validation

**Potential Enhancement**:
- Add explicit validation for tool parameters
- Retry loop for failed tool calls
- Example:
  ```python
  @agent.tool
  async def search_directory(ctx: RunContext, list_name: str, query: str):
      # Validate list_name against accessible_lists
      accessible = ctx.deps.agent_config["tools"]["directory"]["accessible_lists"]
      if list_name not in accessible:
          logfire.warning(f"Invalid directory: {list_name}")
          raise ValueError(f"Directory '{list_name}' not accessible. Available: {accessible}")
      
      # Execute search...
  ```

**Trade-offs**:
- ✅ Prevents invalid tool calls early
- ✅ Better error messages for LLM (can retry)
- ⚠️ Adds complexity to tool functions

**When to Add**:
- ✅ Phase 6 (MCP integration) where external tools may fail
- ⚠️ May not be needed for directory/vector (reliable internal tools)

**Implementation**: ~4-8 hours for validation layer across all tools

---

### 4. Decision Token Strategy (Optional Enhancement)

**Research Finding**: Help LLM decide when to call tool vs. respond directly (reduces spurious calls)

**Current Design**: LLM decides implicitly based on prompt and available tools

**Potential Enhancement**:
- Add explicit guidance:
  ```markdown
  **When to use tools:**
  - User asking for specific doctor/department → Use directory tool
  - User asking about hospital information → Use vector search
  - General chat/greetings → Respond directly (no tool call needed)
  
  **When NOT to use tools:**
  - Information already in conversation history
  - General knowledge questions
  - Greetings, acknowledgments, clarifications
  ```

**Trade-offs**:
- ✅ Reduces unnecessary tool calls (cost savings)
- ✅ Faster responses for simple queries
- ⚠️ Increases prompt size
- ⚠️ May need tuning per agent

**When to Add**:
- ✅ If monitoring shows >20% unnecessary tool calls
- ❌ Skip for MVP (optimize later)

**Implementation**: ~2-4 hours for prompt refinement + testing

---

## Potential Improvements from Planning Agent Research

### 5. Explicit Plan Generation (Alternative Architecture)

**Research Finding**: Multi-agent pipeline with planning → execution → synthesis stages

**Current Design**: Single agent with tools (implicit planning by LLM)

**Alternative Architecture**:
```
Planning Agent → SearchPlan(metadata_filters, directories)
    ↓
Execution Agent → Parallel tool calls (asyncio.gather)
    ↓
Synthesis Agent → Combine results into response
```

**Trade-offs**:

**Pros**:
- ✅ Explicit control over tool selection
- ✅ Can cache/log plans for analysis
- ✅ Testable stages (unit test planning separately)
- ✅ Parallel execution optimization built-in

**Cons**:
- ❌ 3 LLM calls minimum (vs. 1 in current design)
- ❌ Higher latency (~2-3x slower)
- ❌ More complex codebase (~300 lines vs. ~100)
- ❌ Higher token costs (3 prompts vs. 1)

**When to Consider**:
- ⚠️ If need explicit plan inspection/caching for debugging
- ⚠️ If queries consistently require 3+ tool calls (planning overhead justified)
- ❌ Skip for simple directory lookups (1-2 tool calls)

**Implementation**: ~2-3 days for full multi-agent pipeline

---

### 6. Parallel Tool Execution Optimization (Phase 4 Enhancement)

**Research Finding**: `asyncio.gather` for concurrent tool calls reduces latency

**Current Design**: Pydantic AI handles tool orchestration (may be sequential by default)

**Potential Enhancement**:
- Explicit parallel execution tool:
  ```python
  @agent.tool
  async def search_multiple_sources(
      ctx: RunContext, 
      directories: list[str], 
      query: str
  ) -> dict:
      """Search multiple directories concurrently."""
      tasks = [
          search_directory(ctx, dir_name, query) 
          for dir_name in directories
      ]
      results = await asyncio.gather(*tasks, return_exceptions=True)
      return combine_results(results)
  ```

**Trade-offs**:
- ✅ 2-3x faster for multi-directory queries
- ✅ Better user experience (lower latency)
- ⚠️ Requires new tool implementation
- ⚠️ May not be needed if Pydantic AI already parallelizes

**When to Add**:
- ✅ Phase 4 if latency measurements show sequential tool calls
- ⚠️ Check Pydantic AI docs first (may already be parallel)

**Implementation**: ~2-4 hours for parallel execution tool

---

## Design Validation

### What's Already Handled

**Current design already includes**:
- ✅ Structured templates (schema-driven prompts)
- ✅ Clear tool documentation (auto-generated from schemas)
- ✅ Multi-tool support (Phase 4)
- ✅ Directory selection guide (Phase 3)
- ✅ Graceful error handling (logged to Logfire)
- ✅ Progressive enhancement (opt-in complexity)

**Pydantic AI already provides**:
- ✅ Tool call validation (type checking)
- ✅ Structured output support
- ✅ Async tool execution
- ✅ RunContext for dependencies

---

### What's Optional

**Low priority enhancements** (add only if data shows need):
- Few-shot examples (if directory selection struggles)
- Chain-of-Thought (if tool selection accuracy <90%)
- Validation layer (for MCP integration only)
- Decision tokens (if >20% spurious calls)

**Alternative architectures** (evaluate post-MVP):
- Planning agent pipeline (if need explicit plan caching)
- Parallel execution tool (if latency is bottleneck)

---

## Recommended Approach

**Phase 1-3: Implement as Designed**
- Test schema-driven multi-directory selection first
- Measure LLM performance on real queries (doctors + phone_directory)
- Collect metrics: tool selection accuracy, latency, token costs

**Post-Phase 3: Evaluate Enhancements**
- If directory selection accuracy <85% → Add few-shot examples
- If ambiguous queries struggle → Add Chain-of-Thought
- If latency >2s for multi-tool queries → Add parallel execution

**Phase 6: MCP Integration**
- Add validation layer for external tools (unreliable by nature)
- Monitor MCP call success rates, retry failed calls

**Defer to Post-MVP**:
- Planning agent architecture (complex, high cost, unclear ROI)
- Decision token optimization (premature optimization)
- Dual-layer verification (overkill for current use cases)

---

## Key Insight

**The current 6-phase design is already well-structured.** Most tool calling improvements are **prompt-level enhancements** that can be added incrementally (few hours each) if real-world data shows they're needed.

**Don't over-engineer for hypothetical problems.** Implement Phase 1-3, measure, then optimize based on actual LLM behavior with real multi-directory queries.

