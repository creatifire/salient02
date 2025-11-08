<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Advanced Agent Strategies: Alternatives & Enhancements

**Purpose**: Evaluate alternative approaches to improving agent response quality beyond the dynamic prompting architecture.

**Date**: February 1, 2025

**Context**: During design review of `dynamic-prompting.md`, several alternative strategies were identified that could improve response quality. This document evaluates each strategy's trade-offs and applicability.

---

## Strategy 1: Agent Chaining (Multi-Agent Orchestration)

### Concept

Instead of one agent with dynamic prompts, use specialized agents coordinated by a router:

```
User Query
    ↓
Router Agent (classifies intent)
    ↓
├─→ Directory Agent (specialized for directory search)
├─→ Research Agent (specialized for vector/knowledge search)
├─→ Emergency Agent (specialized for urgent queries)
└─→ General Agent (fallback for simple queries)
    ↓
Response Aggregator
    ↓
User Response
```

### Implementation

**Router Agent**:
```python
async def route_query(query: str) -> str:
    """Classify query intent and route to specialist."""
    classification_prompt = f"""
    Classify this query into one category:
    - emergency: Medical emergency or urgent care needed
    - directory: Looking for a doctor or department
    - research: Information about conditions, procedures, policies
    - general: Simple questions, greetings, other
    
    Query: {query}
    Category:
    """
    category = await lightweight_llm_call(classification_prompt)
    return category

async def orchestrate(query: str):
    category = await route_query(query)
    
    if category == "emergency":
        return await emergency_agent.run(query)
    elif category == "directory":
        return await directory_agent.run(query)
    elif category == "research":
        return await research_agent.run(query)
    else:
        return await general_agent.run(query)
```

**Specialized Agents**:
- Each agent has focused system prompt
- Only tools relevant to specialty
- Simpler prompts, easier to optimize

### Pros

✅ **Each agent simpler, focused**: Easier to understand and maintain  
✅ **Easier to optimize per domain**: Can tune each specialist independently  
✅ **Can run specialists in parallel**: For queries needing multiple agents  
✅ **Clear separation of concerns**: Directory logic separate from emergency logic  
✅ **A/B testing friendly**: Can swap out specialist implementations  

### Cons

❌ **Latency overhead**: Minimum 2 LLM calls (router + specialist), often 3+  
❌ **Router can misclassify**: "chest pain" might route to directory instead of emergency  
❌ **More complex orchestration**: Need routing logic, fallback handling, error recovery  
❌ **Higher cost**: Multiple LLM calls per query (2-3x cost increase)  
❌ **Context loss**: Hard to share context between specialists  
❌ **Debugging complexity**: Failures can occur in router OR specialist  

### Cost Analysis

**Typical Query Flow**:
1. Router classification: 100 tokens in, 10 tokens out = 110 tokens
2. Specialist agent: 2000 tokens in (prompt), 200 tokens out = 2200 tokens
3. **Total**: 2310 tokens vs. 2200 tokens for single agent = **5% overhead**

**Complex Query** (needs 2 specialists):
1. Router: 110 tokens
2. Directory agent: 2200 tokens
3. Research agent: 2200 tokens
4. **Total**: 4510 tokens vs. 2200 tokens = **105% overhead** (2x cost!)

### When to Reconsider

- **Latency is not critical** (batch processing, email responses)
- **Clear domain boundaries** (medical vs. billing vs. IT support are totally separate)
- **Specialists need different models** (cheap router, expensive specialists)
- **Parallel execution valuable** (query needs directory + research simultaneously)

### Assessment

**Not recommended for Wyckoff use case**. Users expect fast single responses, not multi-agent pipelines. The latency overhead (200-500ms additional) and cost increase (2x for complex queries) outweigh the benefits of specialization.

**Better fit for**: Internal tools, email bots, complex workflows where latency doesn't matter.

---

## Strategy 2: Prompt Caching at LLM Provider Level

### Concept

Use OpenRouter/Anthropic prompt caching to cache expensive static content, reducing cost and latency.

**Cached** (loaded once, reused 1000x):
- Base system prompt
- Directory tool documentation
- HIPAA compliance module
- Standard disclaimers

**Dynamic** (per-request):
- User query
- Selected context modules (emergency, billing)
- Conversation history

### Implementation

**Anthropic Caching** (via OpenRouter):
```python
from anthropic import Anthropic

client = Anthropic(api_key="...")

# Mark static content for caching
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": base_prompt + directory_docs + hipaa_module,
                "cache_control": {"type": "ephemeral"}  # Cache this!
            },
            {
                "type": "text",
                "text": f"User query: {user_query}"  # Dynamic, not cached
            }
        ]
    }
]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=messages
)
```

**Cache Invalidation**:
- Directory updates → Invalidate cache (use version hash in prompt)
- Module updates → Invalidate cache
- Agent config changes → Invalidate cache

### Pros

✅ **Massive cost savings**: 90% cache hit = 10x cheaper for cached tokens  
✅ **Faster responses**: Cached prompts process instantly (no re-encoding)  
✅ **OpenRouter supports today**: Claude 3.5 Sonnet, Haiku have caching  
✅ **Easy to implement**: Just add `cache_control` markers  
✅ **No architecture changes**: Works with existing prompt composition  

### Cons

⚠️ **Requires prompt structure design**: Must separate static vs. dynamic content  
⚠️ **Cache invalidation complexity**: Need versioning strategy for directory updates  
⚠️ **Not all models support**: Only Anthropic Claude models currently  
⚠️ **Cache misses waste tokens**: If prompt changes slightly, full re-cache  

### Cost Analysis

**Without Caching**:
- Request: 10K tokens (prompt) + 200 tokens (response) = 10,200 tokens
- Cost: $0.003 per 1K tokens = **$0.0306 per query**
- 1000 queries/day = **$30.60/day**

**With Caching** (90% hit rate):
- Cached read: 9K tokens × $0.0003 (10x cheaper) = $0.0027
- Non-cached: 1K tokens × $0.003 = $0.003
- Response: 200 tokens × $0.015 = $0.003
- Cost per query: **$0.0087** (71% savings!)
- 1000 queries/day = **$8.70/day** (saves $21.90/day)

**ROI**: For 1000 queries/day, saves ~$650/month in LLM costs.

### Implementation Complexity

**Low** (1-2 days):
1. Update `create_simple_chat_agent()` to structure prompt with cache markers
2. Add version hash to cached content (invalidate on directory updates)
3. Monitor cache hit rate in Logfire

### When to Use

- ✅ **High query volume** (>100 queries/day per agent)
- ✅ **Large static prompts** (directory docs >5K tokens)
- ✅ **Stable content** (directory updates infrequent)
- ✅ **Using Anthropic models** (Claude Sonnet/Haiku)

### Assessment

**Highly recommended as Phase 3 enhancement**. Easy implementation, immediate cost/latency benefits, no architectural changes needed. Can implement alongside multi-tool infrastructure.

**Action**: Add to Phase 3 (Multi-Tool Infrastructure + Prompt Caching).

---

## Strategy 3: Few-Shot Learning Module Library

### Concept

Instead of keyword-based module selection, use few-shot examples to teach the LLM patterns.

**Traditional Module** (keyword-based):
```markdown
## Emergency Protocols

**If query contains "chest pain", "difficulty breathing", "severe bleeding"**:
1. Provide emergency contact: 911
2. Provide ER direct line: 718-963-7272
3. Then provide specialist if applicable
```

**Few-Shot Module**:
```markdown
## Emergency Response Examples

**Example 1**:
User: "I'm having chest pain"
Agent: "This is a medical emergency. Call 911 immediately if you're experiencing severe chest pain. Our Emergency Department is available 24/7 at 718-963-7272 (Main Building, Ground Floor). Once stabilized, our Cardiology department can provide follow-up care."

**Example 2**:
User: "My head hurts for 2 days"
Agent: "For non-emergency symptoms lasting several days, I recommend scheduling an appointment with your primary care physician. You can reach our Appointments Department at 718-963-8000. If your headache worsens or is accompanied by fever, vision changes, or confusion, visit our Emergency Department immediately."

**Example 3**:
User: "Where is the emergency room?"
Agent: "The Emergency Department is located in the Main Building, Ground Floor. Direct line: 718-963-7272. For life-threatening emergencies, always call 911 first."
```

### Implementation

**Module Structure**:
```markdown
## {Module Name}

**Learn from these examples**:

Example 1: {user query} → {ideal response}
Example 2: {user query} → {ideal response}
Example 3: {user query} → {ideal response}

**Pattern**: {describe the pattern to follow}
```

**Selection Logic** (same as current):
- Keyword-based module selection stays the same
- Just change module content format from instructions to examples

### Pros

✅ **LLM learns patterns naturally**: Few-shot learning is LLM's strength  
✅ **More robust than keyword matching**: Handles variations better  
✅ **Easier for non-technical users to author**: Write examples, not rules  
✅ **Self-documenting**: Examples show what "good" looks like  
✅ **No architecture changes**: Just change module format  
✅ **Can combine with instructions**: Examples + explicit rules  

### Cons

⚠️ **Takes more tokens**: 3-5 examples = 300-500 tokens per module  
⚠️ **Harder to debug**: "Why did it respond this way?" less clear  
⚠️ **Example quality critical**: Bad examples teach bad patterns  
⚠️ **Overfitting risk**: LLM might copy examples too literally  

### Token Analysis

**Instruction-Based Module**:
```
Emergency protocols: 150 tokens
```

**Few-Shot Module**:
```
3 examples × 150 tokens each = 450 tokens
Pattern description: 50 tokens
Total: 500 tokens
```

**Cost Impact**: 3.3x more tokens per module, but better response quality.

### When to Use

- ✅ **Complex decision-making**: Emergency vs. non-emergency requires nuance
- ✅ **Tone/style consistency**: Examples show desired communication style
- ✅ **Multi-step workflows**: Examples demonstrate complete interaction patterns
- ✅ **Non-technical module authors**: Easier than writing precise instructions

### Assessment

**Consider for Phase 4 (Module System)**. Better than keyword matching for complex scenarios, but start with instruction-based modules (simpler, debuggable). Can migrate to few-shot after validating module selection logic works.

**Recommendation**: Start instruction-based (Phase 4), add few-shot option (Phase 6).

---

## Strategy 4: Query Preprocessing Pipeline

### Concept

Analyze query before agent execution to extract structured context and enhance prompt.

**Pipeline Stages**:

```
User Query: "Necesito un cardiólogo de emergencia"
    ↓
┌─────────────────────────────────────────┐
│ 1. Language Detection                   │
│    → Spanish detected                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. Entity Extraction                    │
│    → Medical specialty: "cardiólogo"    │
│    → Urgency: "emergencia"              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. Intent Classification                │
│    → Primary: directory_search          │
│    → Secondary: emergency_handling      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. Tool Selection                       │
│    → Enable: directory_tool             │
│    → Load modules: emergency, spanish   │
└─────────────────────────────────────────┘
    ↓
Enhanced Prompt + Metadata → Agent
```

### Implementation

**Lightweight Classification** (Llama 3B, 50ms):
```python
async def preprocess_query(query: str) -> QueryContext:
    """Extract structured context from query."""
    
    # 1. Language detection (via langdetect or lightweight LLM)
    language = detect_language(query)
    
    # 2. Entity extraction (spaCy or lightweight LLM)
    entities = extract_entities(query)  # {specialty, department, symptoms}
    
    # 3. Urgency classification (keyword + LLM hybrid)
    urgency = classify_urgency(query)  # emergency, urgent, routine
    
    # 4. Intent classification (lightweight LLM)
    intent = classify_intent(query)  # directory, research, billing, general
    
    return QueryContext(
        language=language,
        entities=entities,
        urgency=urgency,
        intent=intent,
        suggested_tools=["directory"] if intent == "directory" else [],
        suggested_modules=["emergency"] if urgency == "emergency" else []
    )

async def enhanced_agent_run(query: str):
    # Preprocess
    context = await preprocess_query(query)
    
    # Build enhanced prompt
    prompt_additions = []
    if context.language != "en":
        prompt_additions.append(f"[Respond in {context.language}]")
    if context.urgency == "emergency":
        prompt_additions.append("[URGENT: Prioritize emergency protocols]")
    
    enhanced_query = "\n".join(prompt_additions) + f"\n\n{query}"
    
    # Select tools and modules based on context
    tools = context.suggested_tools
    modules = context.suggested_modules
    
    # Run agent with enhanced context
    return await agent.run(enhanced_query, tools=tools, modules=modules)
```

### Pros

✅ **More intelligent than keyword matching**: Understands language, entities, urgency  
✅ **Language support**: Auto-detect Spanish, load Spanish modules  
✅ **Structured metadata**: Can log/analyze query patterns  
✅ **Tool selection optimization**: Only enable relevant tools  
✅ **Can use lightweight models**: Llama 3B for classification (cheap, fast)  

### Cons

❌ **Adds latency**: 50-100ms per preprocessing step (4 steps = 200-400ms)  
❌ **More complex codebase**: 4 new components to maintain  
❌ **Requires training/tuning**: Classification models need optimization  
❌ **Failure modes multiply**: Preprocessing errors cascade to agent  
❌ **Harder to debug**: "Was the issue in preprocessing or agent?"  
❌ **Infrastructure overhead**: Need lightweight LLM deployment  

### Latency Analysis

**Without Preprocessing**:
- Agent execution: 800ms
- **Total**: 800ms

**With Preprocessing**:
- Language detection: 10ms (langdetect)
- Entity extraction: 50ms (spaCy)
- Urgency classification: 50ms (Llama 3B)
- Intent classification: 100ms (Llama 3B)
- Agent execution: 800ms
- **Total**: 1010ms (26% slower)

### Cost Analysis

**Preprocessing** (per query):
- Llama 3B calls: 2 × 200 tokens × $0.0001 = $0.00004
- **Negligible cost impact**

### When to Reconsider

- **Multi-language critical**: Spanish, Mandarin, etc. support needed
- **Complex entity extraction**: Medical terms, drug names, ICD codes
- **Advanced analytics**: Want to track query patterns, urgency distribution
- **Latency acceptable**: 200-400ms overhead tolerable for better accuracy

### Assessment

**Defer to Phase 6+**. Overkill for MVP - keyword-based module selection is 80% as good with 0 latency overhead. Great for sophistication later when you have data showing where simple keywords fail.

**Better fit for**: Multi-language deployments, complex entity-driven workflows, analytics-heavy applications.

---

## Strategy 5: Hybrid Static + Dynamic Prompting

### Concept

Balance cost (cache static content) and flexibility (add dynamic context per-request).

**Architecture**:

```
┌─────────────────────────────────────────────────┐
│ STATIC PROMPT (cached, loaded once)            │
│ • Base system prompt                            │
│ • Directory tool documentation                  │
│ • HIPAA compliance module                       │
│ • Standard disclaimers                          │
│ • Total: ~8K tokens                             │
│ • Cost: $0.0003/query (cached read)            │
└─────────────────────────────────────────────────┘
                    +
┌─────────────────────────────────────────────────┐
│ DYNAMIC PROMPT (per-request)                   │
│ • User query                                    │
│ • Selected modules (emergency, billing)         │
│ • Conversation history (last 5 messages)        │
│ • Total: ~2K tokens                             │
│ • Cost: $0.003/query (full price)              │
└─────────────────────────────────────────────────┘
```

### Implementation

**Prompt Composition**:
```python
async def generate_hybrid_prompt(
    agent_config: dict,
    account_id: UUID,
    user_query: str,
    conversation_history: list
) -> tuple[str, str]:
    """Generate static and dynamic prompt components."""
    
    # STATIC (cache this)
    static_parts = []
    static_parts.append(load_base_prompt(agent_config))
    static_parts.append(await generate_directory_tool_docs(...))
    static_parts.append(load_module("shared/hipaa_compliance.md"))
    static_parts.append(load_module("shared/clinical_disclaimers.md"))
    
    static_prompt = "\n\n".join(static_parts)
    
    # DYNAMIC (per-request)
    dynamic_parts = []
    
    # Context modules (keyword-selected)
    if "emergency" in user_query.lower():
        dynamic_parts.append(load_module("medical/emergency_protocols.md"))
    if "billing" in user_query.lower():
        dynamic_parts.append(load_module("administrative/billing_policies.md"))
    
    # Conversation history
    if conversation_history:
        history_text = format_history(conversation_history[-5:])
        dynamic_parts.append(f"## Recent Conversation\n{history_text}")
    
    # User query
    dynamic_parts.append(f"## Current Query\n{user_query}")
    
    dynamic_prompt = "\n\n".join(dynamic_parts)
    
    return static_prompt, dynamic_prompt
```

**Cache Strategy**:
```python
# Mark static prompt for caching (Anthropic)
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": static_prompt,
                "cache_control": {"type": "ephemeral"}
            },
            {
                "type": "text",
                "text": dynamic_prompt
            }
        ]
    }
]
```

### Pros

✅ **Balances cost and flexibility**: Cache static (8K tokens), pay for dynamic (2K)  
✅ **Reduces prompt length**: Only add modules when needed (not all modules in static)  
✅ **Easier to debug**: Static parts don't change, dynamic parts logged per-request  
✅ **Fast cache invalidation**: Only dynamic modules need updates  
✅ **Best of both worlds**: Stability + adaptability  

### Cons

⚠️ **Need to decide what's static vs. dynamic**: Some content ambiguous (frequently-updated modules)  
⚠️ **Cache management**: Versioning strategy for static content  
⚠️ **Complexity**: Two-tier prompt composition logic  

### Decision Framework: Static vs. Dynamic

| Content | Static? | Rationale |
|---------|---------|-----------|
| Base system prompt | ✅ Yes | Never changes per-request |
| Directory tool docs | ✅ Yes | Updates infrequent (daily at most) |
| HIPAA compliance | ✅ Yes | Universal, never changes |
| Clinical disclaimers | ✅ Yes | Universal, never changes |
| Emergency protocols | ❌ No | Context-specific (only if query suggests emergency) |
| Billing policies | ❌ No | Context-specific (only if query mentions billing) |
| Conversation history | ❌ No | Unique per request |
| User query | ❌ No | Unique per request |

**Rule of Thumb**: Static = Universal + Stable. Dynamic = Contextual + Per-Request.

### Cost Analysis

**All Static** (no caching):
- Prompt: 10K tokens × $0.003 = $0.030
- **Cost**: $0.030/query

**Hybrid Static (8K) + Dynamic (2K)** (with caching):
- Static cached read: 8K × $0.0003 = $0.0024
- Dynamic: 2K × $0.003 = $0.006
- **Cost**: $0.0084/query
- **Savings**: 72% vs. no caching

### Assessment

**This is the recommended architecture!** The proposed dynamic-prompting design IS already hybrid. Just need to implement prompt caching (Phase 3) to realize cost savings.

**Commit to this approach** - it's the right balance for your use case.

---

## Strategy Comparison Matrix

| Strategy | Cost Impact | Latency Impact | Complexity | Quality Gain | Recommended Phase |
|----------|-------------|----------------|------------|--------------|-------------------|
| **Agent Chaining** | +100% | +200-500ms | High | +10-20% | ❌ Not recommended |
| **Prompt Caching** | -70% | -50-100ms | Low | +0% (cost/latency only) | ✅ Phase 3 |
| **Few-Shot Modules** | +10% | +0ms | Low | +15-25% | ✅ Phase 6 (after MVP) |
| **Query Preprocessing** | +0.1% | +200-400ms | High | +20-30% | ⚠️ Phase 8+ (future) |
| **Hybrid Prompting** | -72% | -50-100ms | Medium | +0% (cost/latency only) | ✅ Phase 3 (with caching) |

---

## Recommendations

### Implement Now (Phase 3-4)

1. **Prompt Caching** (Phase 3)
   - Easy win: 70% cost reduction, faster responses
   - Low complexity: Just add cache markers
   - Works with existing architecture

2. **Hybrid Static + Dynamic** (Phase 3)
   - Already part of design
   - Enables prompt caching effectiveness
   - Best balance of cost/flexibility

### Implement Later (Phase 6-7)

3. **Few-Shot Learning Modules** (Phase 6)
   - After validating keyword-based module selection works
   - Better quality for complex scenarios
   - Easy migration path (just change module format)

### Defer Indefinitely (Phase 8+)

4. **Agent Chaining** - Only if latency doesn't matter
5. **Query Preprocessing** - Only if multi-language critical or keyword matching proves insufficient

---

## Measuring Success

**Quality Metrics** (track in Logfire):
- User satisfaction ratings (thumbs up/down)
- Query resolution rate (did user get answer?)
- Follow-up query rate (did user need to ask again?)
- Tool usage accuracy (was correct tool called?)

**Cost Metrics**:
- Average tokens per query (breakdown: static, dynamic, response)
- Cache hit rate (should be >80%)
- Cost per query (target: <$0.01)

**Latency Metrics**:
- Time to first token (TTFT) - target: <300ms
- Total response time - target: <1000ms for typical queries

**Target Improvements** (vs. current baseline):
- Quality: +50% (emergency queries handled correctly 90% → 95%)
- Cost: -70% (with prompt caching)
- Latency: -30% (with prompt caching)

---

## Conclusion

**Recommended Strategy**: Hybrid Static + Dynamic Prompting with Prompt Caching (Phase 3-4)

**Why**:
- Lowest risk, highest ROI
- 70% cost reduction immediately
- No architecture changes needed
- Enables all future enhancements

**Not Recommended**:
- Agent Chaining (too slow, too expensive for your use case)
- Query Preprocessing (premature optimization)

**Future Consideration**:
- Few-Shot Modules (after MVP validated)
- Multi-language preprocessing (if international expansion)

