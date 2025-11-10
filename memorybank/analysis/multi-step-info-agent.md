<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Multi-Step Planning Agent Strategy

## High-Level Flow

```
User Query
    ↓
[0] Safety Check → Emergency? → Immediate Response (call 911)
    ↓ No
[1] Build Plan (JSON):
    - metadata_filters: {category: "X", language: "Y"}
    - directories: ["doctors", "phone_directory"]
    ↓
[2-3] Execute Plan (Parallel):
    - vector_search(filters=metadata_filters)
    - search_directory("doctors", filters={...})
    - search_directory("phone_directory", filters={...})
    ↓
[4] Combine Results → Seamless Response
```

---

## Pydantic AI Implementation

### Step 0: Safety Fork

**Pattern**: Output validator with conditional response

```python
@agent.output_validator
async def safety_check(ctx: RunContext, output: str) -> str:
    if is_emergency(output):
        raise ModelRetry("EMERGENCY: Call 911 immediately")
    return output
```

**Alternative**: System prompt instruction to call `emergency_response` tool directly

---

### Step 1: Plan Generation

**Pattern**: Structured output with Pydantic model

```python
class SearchPlan(BaseModel):
    metadata_filters: dict[str, str]
    directories: list[str]

planning_agent = Agent(
    'openai:gpt-5',
    output_type=SearchPlan,
    system_prompt='Analyze query and create search plan'
)

plan = await planning_agent.run(user_query)
# Returns: SearchPlan(metadata_filters={...}, directories=[...])
```

**Pydantic AI Feature**: Native structured output validation

---

### Step 2-3: Parallel Execution

**Pattern**: Tool orchestration with `asyncio.gather`

```python
@execution_agent.tool
async def execute_plan(ctx: RunContext, plan: SearchPlan) -> dict:
    tasks = []
    
    # Vector search
    if plan.metadata_filters:
        tasks.append(vector_search(ctx, plan.metadata_filters))
    
    # Directory searches
    for dir_name in plan.directories:
        tasks.append(search_directory(ctx, dir_name))
    
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

**Pydantic AI Features**:
- `RunContext` for shared dependencies (DB session, account)
- Async tools by default
- Multiple tool calls in single turn

---

### Step 4: Response Synthesis

**Pattern**: Agent delegation with combined context

```python
synthesis_agent = Agent(
    'openai:gpt-5',
    system_prompt='Synthesize search results into seamless response'
)

@synthesis_agent.tool
async def get_search_results(ctx: RunContext) -> dict:
    # Results from Step 2-3 passed via context
    return ctx.deps.search_results

final_response = await synthesis_agent.run(
    "Synthesize results",
    deps=Deps(search_results=combined_results)
)
```

**Pydantic AI Feature**: Agent delegation pattern (agent calls agent)

---

## Implementation Options

### Option A: Single Agent with Tools (Simpler)

**Architecture**: One agent, multiple tools, manual orchestration

- `plan_search` tool → returns JSON plan
- `execute_vector_search` tool
- `execute_directory_search` tool
- Agent calls tools sequentially/parallel as needed

**Pros**: Single agent, simpler setup, natural conversation flow
**Cons**: LLM decides orchestration (less control), multiple LLM calls

---

### Option B: Multi-Agent Pipeline (More Control)

**Architecture**: Three specialized agents

1. **Planning Agent** → outputs `SearchPlan` (structured)
2. **Execution Agent** → runs parallel searches via tools
3. **Synthesis Agent** → combines results into response

**Pros**: Explicit control, can cache plans, testable stages
**Cons**: More code, 3 LLM calls minimum, higher latency

---

## Recommendation

**Start with Option A** (Single Agent with Tools):
- Less complex for MVP
- Pydantic AI handles tool orchestration
- Add Option B if need explicit plan caching or stage-by-stage testing

**Key Pydantic AI Features Needed**:
- ✅ Structured output (`output_type=SearchPlan`)
- ✅ Async tools (`@agent.tool` with async functions)
- ✅ RunContext for dependencies (DB session, account, results)
- ✅ Tool calls with `asyncio.gather` for parallel execution
- ✅ Output validators for safety checks

**Implementation Effort**: ~1-2 days (using existing directory + vector tools)

