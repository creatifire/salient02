<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Dynamic Prompting - Alternative Approaches Considered

**Parent Document**: [dynamic-prompting.md](./dynamic-prompting.md)

This document captures alternative architectural approaches that were evaluated but not selected for the dynamic prompting implementation. These remain documented for future reference and potential reconsideration.

**Selected Approach**: Option 2 (Modular Composition) - documented in main design file.

---

## Option 1: Request Classification + Prompt Routing

**Mechanism**: Classify request intent, load specialized prompt template

```
User Request → Intent Classifier → Select Prompt → Run Agent
     ↓              ↓                    ↓              ↓
"Find doctor"   directory_search    directory.md    Execute
"Billing"       administrative      admin.md        Execute
```

**Structure**:
```
agent_configs/wyckoff/wyckoff_info_chat1/
  ├── system_prompt.md           # Default
  ├── prompts/
  │   ├── directory_search.md    # Doctor/service finding
  │   ├── administrative.md      # Billing, insurance
  │   ├── clinical_info.md       # Medical education
  │   └── emergency.md           # Urgent care
```

**Pros**:
- ✅ High specialization per intent
- ✅ Clean separation of concerns
- ✅ Easy A/B testing per intent
- ✅ Clear prompt boundaries

**Cons**:
- ❌ Added latency (requires classifier LLM call)
- ❌ Pydantic AI constructs agent with static prompt (would need agent recreation per request)
- ❌ Misclassification risk (wrong prompt selected)
- ❌ Overhead for simple queries
- ❌ Complex fallback handling

**Why Not Selected**: The need for agent recreation per request conflicts with Pydantic AI's architecture, and the added latency from classification calls is undesirable. Modular composition achieves similar specialization without these drawbacks.

---

## Option 3: Multi-Agent Routing

**Mechanism**: Route to specialized agents instead of changing prompts

```
Frontend → Router Agent → Specialized Agent → Response
              ↓              ↓
         "Find doctor"   DirectoryAgent (directory-optimized prompt)
         "Billing"       AdminAgent (billing-optimized prompt)
```

**Agent Definitions**:
```
agent_configs/wyckoff/
  ├── wyckoff_router/          # Routes requests
  ├── wyckoff_directory/       # Doctor search specialist
  ├── wyckoff_admin/           # Billing specialist
  ├── wyckoff_clinical/        # Medical info specialist
  └── wyckoff_general/         # Fallback
```

**Pros**:
- ✅ True specialization (each agent optimized for its domain)
- ✅ Can use different models per domain (cost optimization)
- ✅ Easier testing (test each agent independently)
- ✅ Scales independently (add new agents without touching existing)
- ✅ Clear responsibility boundaries

**Cons**:
- ❌ Higher complexity (multiple agents to maintain)
- ❌ 2x latency (router call + specialist call)
- ❌ 2x cost (two LLM calls per request)
- ❌ Routing errors (wrong agent selected)
- ❌ Context loss on handoff (conversation history management)
- ❌ More configuration overhead

**Why Not Selected**: The double latency and cost are prohibitive for most use cases. The added complexity of maintaining multiple agents and handling context handoffs outweighs the benefits. Modular composition provides sufficient specialization with a single agent.

---

## Option 4: Dynamic Instructions (Message Prepending)

**Mechanism**: Inject context-specific instructions into user message at runtime

```python
async def run_with_context(agent, user_message: str) -> str:
    context = analyze_request(user_message)
    
    instructions = []
    if context.needs_directory:
        instructions.append("[CONTEXT: Directory search - use search_directory tool]")
    
    if context.is_urgent:
        instructions.append("[PRIORITY: Urgent - provide emergency contact first]")
    
    enhanced = "\n".join(instructions) + f"\n\nUser: {user_message}"
    return await agent.run(enhanced)
```

**Example**:
```
Original: "I need a cardiologist"
Enhanced: "[CONTEXT: Directory search - use search_directory tool]

User: I need a cardiologist"
```

**Pros**:
- ✅ No architecture changes required
- ✅ Single agent (simple)
- ✅ Works with current Pydantic AI setup
- ✅ Minimal latency (just string manipulation)
- ✅ Easy to implement and test

**Cons**:
- ❌ Longer messages (counts against token budget)
- ❌ Less clean (mixing instructions with user input)
- ❌ Instructions might conflict with base prompt
- ❌ LLM may ignore injected context (not in system prompt)
- ❌ Hard to debug (instructions not visible in agent config)
- ❌ Limited specialization (can't load domain knowledge)

**Why Not Selected**: Message prepending is too limited for rich contextual enhancements. It cannot load domain-specific knowledge (e.g., billing policies, emergency protocols) that modules can provide. However, this approach may be useful as a complementary technique for urgent/time-sensitive context (see Future Enhancements in main design).

---

## Comparison Matrix

| Option | Complexity | Latency | Specialization | Maintainability | Cost | Works with Pydantic AI |
|--------|-----------|---------|----------------|-----------------|------|------------------------|
| **1. Prompt Routing** | Medium | High (+1 LLM call) | High | Medium | Medium | Requires agent recreation |
| **2. Modular Composition** ⭐ | **Medium** | **Low** | **Medium-High** | **High** | **Low** | **Yes** |
| **3. Multi-Agent** | High | High (+1 LLM call) | Very High | Medium | High (2x) | Yes |
| **4. Dynamic Instructions** | Low | Low | Low | High | Low | Yes |

---

## When to Reconsider These Approaches

**Prompt Routing (Option 1)**: If Pydantic AI adds support for dynamic prompt swapping without agent recreation, this could become viable.

**Multi-Agent (Option 3)**: If we need true domain isolation (e.g., HIPAA-compliant medical agent vs. non-compliant general agent) or want to use different models for cost optimization.

**Dynamic Instructions (Option 4)**: Already being considered as a complementary technique for Phase 2 (Future Enhancements) to handle urgent/time-sensitive context that can't be predetermined.

---

**Last Updated**: February 8, 2025

**Related**: [dynamic-prompting.md](./dynamic-prompting.md) (selected approach)

