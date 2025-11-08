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

---

## Deferred Optimization Features

These features were considered for the initial implementation but deferred to post-MVP based on the principle of "trust LLM context windows, focus on correctness first, optimize later."

---

### Token Budget Enforcement

**Problem**: Prevent prompts from becoming too large and consuming excessive tokens.

**Deferred Solution**: Complex enforcement strategies

**System defaults** (`backend/config/prompt_modules/token_budgets.yaml`):
```yaml
default_token_budgets:
  max_modules_tokens: 800
  total_cap: 2000
  enforcement: "prioritize"  # prioritize | truncate | reject
```

**Per-agent override**:
```yaml
prompting:
  token_budget:
    total_cap: 3000
    max_modules_tokens: 1200
    enforcement: "truncate"
```

**Enforcement strategies**:
1. **Prioritize**: Keep highest priority modules that fit within budget
2. **Truncate**: Truncate module content to fit
3. **Reject**: Reject entire request if over budget

**Why deferred**:
- Modern LLMs have 128K+ token context windows
- Adds ~150 lines of complexity (counting, enforcement, edge cases)
- No data showing this is actually needed
- Can add later if prompts grow problematically large

**When to reconsider**: If prompts consistently exceed 10K tokens or cause performance issues.

---

### Prompt Caching

**Problem**: Regenerating prompts on every request is wasteful if prompts rarely change.

**Deferred Solution**: LRU cache with TTL and invalidation

**Configuration** (`backend/config/app.yaml`):
```yaml
caching:
  prompt_cache:
    enabled: true
    maxsize: 50
    ttl_seconds: 300
    invalidate_on_file_change: true
    invalidate_on_config_update: true
```

**Implementation**:
```python
@lru_cache(maxsize=50)
def get_cached_prompt(base_hash: str, modules_tuple: tuple, dir_hash: str) -> str:
    return cached_prompt
```

**Why deferred**:
- Performance optimization, not core functionality
- Need real usage data to tune cache settings (maxsize, TTL)
- Adds complexity (cache invalidation, key generation)
- ~50 lines of code + testing overhead

**When to reconsider**: If profiling shows prompt generation is a bottleneck (>100ms per request).

---

### System-Level Keyword Mappings

**Problem**: Avoid repeating common keyword mappings across agents.

**Deferred Solution**: System defaults + agent overrides

**System defaults** (`backend/config/prompt_modules/keyword_mappings.yaml`):
```yaml
# Shared keyword mappings (optional defaults)
default_mappings:
  - keywords: ["emergency", "urgent", "911"]
    module: "medical/emergency_protocols.md"
    priority: 10
  
  - keywords: ["hipaa", "privacy"]
    module: "shared/hipaa_compliance.md"
    priority: 1
```

**Agent can reference or override**:
```yaml
prompting:
  modules:
    enabled: true
    use_system_defaults: true  # Inherit system mappings
    keyword_mappings:  # Add or override
      - keywords: ["billing"]  # Agent-specific
        module: "administrative/billing_policies.md"
```

**Why deferred**:
- Adds cascade complexity (system → agent resolution)
- Multi-tenant agents likely need different keywords anyway (language, domain)
- DRY can be achieved through config templates/examples, not runtime defaults
- Each agent defining its own mappings is clearer (no hidden behavior)

**When to reconsider**: If we have 50+ agents with identical keyword mappings and maintaining them becomes burdensome.

---

### Complex Phase 2 Conditions

**Problem**: Keyword matching for dynamic instructions may be insufficient for complex scenarios.

**Deferred Solution**: Multiple condition types beyond keywords

**Condition types proposed**:

1. **is_followup**: Detect follow-up question from conversation history
   ```yaml
   - condition: "is_followup"
     instruction: "[CONTEXT: User following up on previous answer]"
   ```

2. **message_count_gt_N**: Trigger after N messages in conversation
   ```yaml
   - condition: "message_count_gt_5"
     instruction: "[CONTEXT: Extended conversation, user may need summary]"
   ```

3. **time_based**: Trigger based on time of day
   ```yaml
   - condition: "after_hours"
     instruction: "[INFO: After hours - direct to emergency contact]"
   ```

4. **custom**: Custom condition function (Python callable)
   ```yaml
   - condition: "custom:check_urgent_symptoms"
     instruction: "[URGENT: Potential medical emergency]"
   ```

**Implementation complexity**:
```python
# Evaluate condition
applies = False

if condition == "keyword_match":
    keywords = mapping.get("keywords", [])
    applies = any(kw in message.lower() for kw in keywords)

elif condition == "is_followup":
    applies = is_followup_question(message_history)  # New function needed

elif condition == "message_count_gt_5":
    applies = len(message_history) > 5  # Simple

elif condition.startswith("time_based"):
    applies = check_time_condition(condition)  # New function needed

elif condition.startswith("custom:"):
    func_name = condition.split(":")[1]
    applies = call_custom_condition(func_name, message, message_history)  # Registry needed
```

**Why deferred**:
- Keyword matching covers 80% of use cases (emergency, pharmacy hours)
- Complex conditions add ~100 lines of code (detection logic, testing, edge cases)
- Need real usage data to know which conditions are actually useful
- Can add incrementally based on customer feedback

**When to reconsider**: After Phase 2 MVP deployment, if customers request specific condition types repeatedly.

---

### LLM-Based Module Selection (Phase 3)

**Problem**: Keyword matching may miss nuanced queries or domain-specific intent.

**Deferred Solution**: Use lightweight LLM call to classify query intent

**Implementation**:
```python
async def select_modules_llm(query: str, available_modules: List[str]) -> List[str]:
    """Use LLM to classify query and select relevant modules."""
    
    classification_prompt = f"""
    Available context modules:
    {format_modules(available_modules)}
    
    User query: "{query}"
    
    Which modules are relevant? Return JSON array of module names.
    """
    
    result = await classify_llm.run(classification_prompt)
    return result.output  # ["medical/emergency_protocols.md", ...]
```

**Configuration**:
```yaml
prompting:
  modules:
    enabled: true
    selection_mode: "llm"  # keyword | llm
    classifier_model: "deepseek/deepseek-chat-v3.1"  # Lightweight model
```

**Why deferred**:
- Adds latency (~50-100ms per request)
- Adds cost (extra LLM call per request)
- Need data showing keyword approach is insufficient
- Keyword matching is deterministic and testable

**When to reconsider**: If customers report module selection misses (e.g., "I asked about billing but didn't get billing info").

---

## Summary of Deferred Features

| Feature | Lines of Code | Complexity | When to Reconsider |
|---------|---------------|------------|---------------------|
| Token Budget Enforcement | ~150 | Medium | Prompts > 10K tokens consistently |
| Prompt Caching | ~50 | Low | Prompt generation > 100ms |
| System Keyword Mappings | ~30 | Low | 50+ agents with identical mappings |
| Complex Phase 2 Conditions | ~100 | Medium | Customer requests for specific conditions |
| LLM-Based Module Selection | ~150 | Medium | Keyword selection proves insufficient |
| **Total Deferred** | **~480 lines** | **- | Based on real usage data** |

**Philosophy**: Build the simplest thing that could work, validate with customers, then add sophistication based on real needs.

