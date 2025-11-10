<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Improving Tool Calling Reliability

Research summary of proven strategies for improving LLM tool/function calling accuracy and reliability.

---

## 1. Structured Template-Based Prompts

**Technique**: Explicit templates with clear sections (task, context, parameters, output format) using delimiters (`###`, XML tags)

**Pros**:
- Reduces parsing errors and hallucinations
- Works immediately with existing prompts (no training)
- Model-agnostic (GPT-4, Claude, DeepSeek)

**Cons**:
- Requires prompt redesign/refactoring
- Can increase prompt token count
- Manual maintenance for each tool

**Effort**: Low (~2-4 hours per agent to refactor system prompts)

**Sources**: [Dextra Labs](https://dextralabs.com/blog/prompt-engineering-for-llm/), [AI Weekly](https://ai-weekly.ai/top-20-prompting-techniques-in-use-today/)

---

## 2. Few-Shot Examples (In-Context Learning)

**Technique**: Provide 2-4 examples of correct tool calls in system prompt showing input → reasoning → function call

**Pros**:
- Significantly improves consistency and format adherence
- Quick to implement (add examples to prompt)
- Helps with edge cases and parameter extraction

**Cons**:
- Increases prompt size (~200-500 tokens per example)
- Examples must be maintained as tools evolve
- May not generalize to novel scenarios

**Effort**: Low (~1-2 hours to create examples per tool)

**Sources**: [Lakera Guide](https://www.lakera.ai/blog/prompt-engineering-guide), [OpenAI Community](https://community.openai.com/t/prompting-best-practices-for-tool-use-function-calling/1123036)

---

## 3. Chain-of-Thought (CoT) for Tool Selection

**Technique**: Instruct model to reason step-by-step before calling tools ("First explain which tool to use and why, then make the call")

**Pros**:
- Improves tool selection accuracy in multi-tool scenarios
- Better parameter extraction via explicit reasoning
- Interpretable (see why model chose specific tool)

**Cons**:
- Increases latency (extra reasoning tokens)
- Higher token costs (reasoning + tool call)
- May be verbose for simple queries

**Effort**: Low (~30 minutes to add CoT instruction to prompts)

**Sources**: [Google Research](https://arxiv.org/html/2509.18076v1), [AI Weekly](https://ai-weekly.ai/top-20-prompting-techniques-in-use-today/)

---

## 4. Explicit Output Constraints

**Technique**: Force strict output format ("Respond ONLY with valid JSON, no explanations") with validation + retry loops

**Pros**:
- Eliminates prose/explanations mixed with tool calls
- Makes parsing deterministic
- Easy to implement validation layer

**Cons**:
- Requires backend validation logic
- Retry loops add complexity
- May need multiple attempts for complex calls

**Effort**: Medium (~4-8 hours for validation layer + retry logic)

**Sources**: [OpenAI Community](https://community.openai.com/t/prompting-best-practices-for-tool-use-function-calling/1123036), [Vellum Guide](https://www.vellum.ai/blog/the-ultimate-llm-agent-build-guide)

---

## 5. Decision Token Strategy (OpenAI 2024)

**Technique**: Special prompt token/instruction enabling model to decide: respond directly OR call function (includes negative examples in training)

**Pros**:
- Reduces spurious function calls (when direct answer better)
- Improves tool selection precision
- Better relevance detection

**Cons**:
- Requires prompt engineering experimentation
- May need model-specific tuning (works best with GPT-4+)
- Negative examples increase prompt complexity

**Effort**: Medium (~6-10 hours for prompt design + negative examples + testing)

**Sources**: [OpenAI Function Calling Strategy](https://www.rohan-paul.com/p/openais-function-calling-strategy)

---

## 6. Dual-Layer Data Verification (TOOLACE - ICLR 2025)

**Technique**: Rule verification (format, required params, API spec compliance) + LLM agent verification (hallucination check, content correctness)

**Pros**:
- Highest reliability (research-backed, ICLR 2025)
- Catches both format errors AND semantic errors
- Improves training data quality (if fine-tuning)

**Cons**:
- Complex implementation (two validation layers)
- Requires LLM call for verification (cost + latency)
- Overkill for simple tool scenarios

**Effort**: High (~2-3 days for dual verification pipeline)

**Sources**: [TOOLACE Paper - ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/663865ea167425c6c562cb0b6bcf76c7-Paper-Conference.pdf)

---

## 7. Comprehensive Evaluation Framework

**Technique**: Test tool calling across multiple benchmarks (BFCL, NFCL) + real-world scenarios, not single metrics

**Pros**:
- Identifies specific weaknesses (parameter extraction vs. tool selection)
- Data-driven optimization
- Prevents overfitting to single test case

**Cons**:
- Requires benchmark setup
- Ongoing maintenance (update tests as tools evolve)
- Analysis overhead

**Effort**: Medium (~1-2 days for initial benchmark suite + analysis)

**Sources**: [Databricks Blog](https://www.databricks.com/blog/unpacking-function-calling-eval), [Quotient AI](https://blog.quotientai.co/evaluating-tool-calling-capabilities-in-large-language-models-a-literature-review/)

---

## Recommendation

**Immediate (Phase 1 - Low Effort, High Impact)**:
1. ✅ **Few-Shot Examples** - Add 2-3 examples per tool to system prompts (1-2 hours)
2. ✅ **Structured Templates** - Refactor prompts with clear sections/delimiters (2-4 hours)
3. ✅ **CoT for Multi-Tool** - Add reasoning step for agents with 3+ tools (30 minutes)

**Near-Term (Phase 2 - Medium Effort, High Value)**:
4. ⚠️ **Output Constraints + Validation** - Build validation layer with retry logic (4-8 hours)
5. ⚠️ **Decision Token Strategy** - Experiment with relevance gating (6-10 hours)

**Future (Phase 3 - High Effort, Research-Grade)**:
6. 🔬 **Dual-Layer Verification** - For critical/high-stakes tools only (2-3 days)
7. 🔬 **Evaluation Framework** - Systematic testing and improvement (1-2 days initial setup)

**Rationale**: 
- **Phase 1** strategies are prompt-only (no code changes), proven effective, immediate ROI
- **Phase 2** adds robustness for production reliability (worth the engineering time)
- **Phase 3** is overkill for MVP but valuable for high-stakes scenarios (medical, financial)

**Priority for Our Multi-Directory Agents**:
- After Phase 2 (phone_directory), test Few-Shot + Structured Templates for directory selection
- If LLM struggles with doctors vs. phone_directory routing, add CoT reasoning step
- Validation layer useful for Phase 4 (MCP integration) where external tool calls are expensive

**Total Effort for Phase 1+2**: ~1.5-2 days engineering time, significant reliability improvement.

