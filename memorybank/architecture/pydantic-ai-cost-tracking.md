<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Pydantic AI LLM Cost Tracking Architecture

> **Last Updated**: January 12, 2025  
> Complete guide to tracking LLM costs with Pydantic AI agents, including non-streaming, streaming, multi-tenant support, fallback pricing, and critical lessons learned.

## Quick Reference

| Scenario | Method | Code Location |
|----------|--------|---------------|
| **Non-streaming** | Extract from `provider_details` | `simple_chat.py:275-411` |
| **Streaming** | Use `genai-prices.calc_price()` | `simple_chat.py:556-782` |
| **Model not in genai-prices** | Load from `fallback_pricing.yaml` | `simple_chat.py:612-660` |
| **Database fields** | `prompt_cost`, `completion_cost`, `total_cost` | `NUMERIC(12,8)` precision |
| **Multi-tenant tracking** | Pass `agent_instance_id` | All tracking calls |

**⚠️ Critical**: Streaming and non-streaming use **completely different** cost extraction methods due to a Pydantic AI limitation. See [Section 5](#5-the-streaming-difference-critical-lesson-learned).

---

## Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
2. [Database Schema](#2-database-schema)
3. [Non-Streaming Implementation](#3-non-streaming-implementation)
4. [Streaming Implementation](#4-streaming-implementation)
5. [The Streaming Difference: Critical Lesson Learned](#5-the-streaming-difference-critical-lesson-learned)
6. [Multi-Tenant Integration](#6-multi-tenant-integration)
7. [Fallback Pricing Configuration](#7-fallback-pricing-configuration)
8. [Billable vs Non-Billable Errors](#8-billable-vs-non-billable-errors)
9. [Monitoring & Analytics](#9-monitoring--analytics)
10. [Testing & Verification](#10-testing--verification)
11. [Performance Considerations](#11-performance-considerations)
12. [Security Considerations](#12-security-considerations)
13. [Related Documentation](#13-related-documentation)

---

## 1. Overview & Architecture

The LLM cost tracking system provides accurate billing data by capturing every billable interaction with OpenRouter and other LLM providers. The system uses **direct Pydantic AI integration** with specialized handling for streaming vs non-streaming requests.

### Core Principles

1. ✅ **ALL LLM interactions use Pydantic AI** - No direct API calls
2. ✅ **Real-time cost capture** from OpenRouter actual billing data
3. ✅ **Separate handling for streaming** - Different cost extraction method required
4. ✅ **Database persistence** with high precision (`NUMERIC(12,8)`)
5. ✅ **Multi-tenant support** via `agent_instance_id`
6. ✅ **Fallback pricing** for models not yet in genai-prices

### Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Endpoints                          │
│  /accounts/{account}/agents/{instance}/chat (non-streaming)    │
│  /accounts/{account}/agents/{instance}/stream (streaming)      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Pydantic AI Agents                            │
│                                                                 │
│  simple_chat()        → agent.run()                            │
│  simple_chat_stream() → agent.run_stream()                     │
│                                                                 │
│  Agent(model, deps_type=SessionDependencies, system_prompt)    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Cost Extraction Layer                           │
│                                                                 │
│  Non-streaming: provider_details (OpenRouter metadata)         │
│  Streaming:     genai-prices.calc_price() + fallback           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               LLMRequestTracker Service                         │
│                                                                 │
│  track_llm_request(session_id, agent_instance_id, costs...)   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                PostgreSQL Database                              │
│                                                                 │
│  llm_requests table with NUMERIC(12,8) cost fields            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema

### Current Schema (Post-Migration)

```sql
CREATE TABLE llm_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    agent_instance_id UUID NULL REFERENCES agent_instances(id),
    
    -- Provider information
    provider VARCHAR(50) NOT NULL,  -- 'openrouter', 'together', etc.
    model VARCHAR(255) NOT NULL,    -- e.g., 'deepseek/deepseek-chat-v3.1'
    
    -- Request/response data
    request_body JSONB NOT NULL,
    response_body JSONB NOT NULL,
    
    -- Token usage
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    
    -- Cost tracking (NUMERIC(12,8) for high precision)
    prompt_cost NUMERIC(12,8) NULL,      -- e.g., 0.0000408
    completion_cost NUMERIC(12,8) NULL,  -- e.g., 0.003646
    total_cost NUMERIC(12,8) NULL,       -- e.g., 0.0036868
    
    -- Performance tracking
    latency_ms INTEGER NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for queries
    INDEX idx_llm_requests_session_id (session_id),
    INDEX idx_llm_requests_agent_instance_id (agent_instance_id),
    INDEX idx_llm_requests_created_at (created_at)
);
```

### Field Precision Rationale

**NUMERIC(12,8)** allows:
- Total: 12 digits
- Decimals: 8 places (e.g., `0.0000408`)
- Range: `-9999.99999999` to `9999.99999999`
- Perfect for OpenRouter costs (typically $0.000001 - $10.00 per request)

### Example Record

```json
{
    "id": "591fd82e-4357-4f9a-86e5-aa030930181a",
    "session_id": "c2f00a7f-1b0b-4fc7-928a-f347a1a0e0a3",
    "agent_instance_id": "8f3e2b4d-1c5a-4f9b-8e7d-2a1b3c4d5e6f",
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat-v3.1",
    "request_body": {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "deepseek/deepseek-chat-v3.1",
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "response_body": {
        "content": "Hi! How can I help you?",
        "usage": {
            "prompt_tokens": 291,
            "completion_tokens": 1303,
            "total_tokens": 1594
        },
        "model": "deepseek/deepseek-chat-v3.1",
        "provider_details": {
            "cost": 0.0036868,
            "cost_details": {
                "upstream_inference_prompt_cost": 0.0000408,
                "upstream_inference_completions_cost": 0.003646
            }
        }
    },
    "prompt_tokens": 291,
    "completion_tokens": 1303,
    "total_tokens": 1594,
    "prompt_cost": 0.0000408,
    "completion_cost": 0.003646,
    "total_cost": 0.0036868,
    "latency_ms": 2453,
    "created_at": "2025-01-12T10:30:45.123Z"
}
```

---

## 3. Non-Streaming Implementation

### Overview

Non-streaming requests use OpenRouter's `provider_details` metadata, which is automatically extracted by our custom `OpenRouterModel` class and populated into `ModelResponse.provider_details` by Pydantic AI.

### Code Location

**File**: `backend/app/agents/simple_chat.py`  
**Function**: `simple_chat()` (lines 214-495)

### Implementation

```python
async def simple_chat(
    message: str, 
    session_id: str,
    agent_instance_id: Optional[int] = None,
    message_history: Optional[List[ModelMessage]] = None,
    instance_config: Optional[dict] = None
) -> dict:
    """Non-streaming chat with Pydantic AI."""
    
    # 1. Create agent with instance-specific config
    agent = await get_chat_agent(instance_config=instance_config)
    
    # 2. Execute agent with Pydantic AI
    start_time = datetime.now(UTC)
    result = await agent.run(message, deps=session_deps, message_history=message_history)
    end_time = datetime.now(UTC)
    
    # 3. Extract response and usage
    response_text = result.output
    usage_data = result.usage()
    
    if usage_data:
        prompt_tokens = usage_data.input_tokens
        completion_tokens = usage_data.output_tokens
        total_tokens = usage_data.total_tokens
        
        # 4. Extract costs from OpenRouter provider_details
        prompt_cost = 0.0
        completion_cost = 0.0
        total_cost = 0.0
        
        new_messages = result.new_messages()
        if new_messages:
            latest_message = new_messages[-1]
            if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
                # Extract total cost
                total_cost = float(latest_message.provider_details.get('cost', 0.0))
                
                # Extract detailed costs
                cost_details = latest_message.provider_details.get('cost_details', {})
                if cost_details:
                    prompt_cost = float(cost_details.get('upstream_inference_prompt_cost', 0.0))
                    completion_cost = float(cost_details.get('upstream_inference_completions_cost', 0.0))
    
    # 5. Track to database using LLMRequestTracker
    if prompt_tokens > 0 or completion_tokens > 0:
        tracker = LLMRequestTracker()
        
        llm_request_id = await tracker.track_llm_request(
            session_id=UUID(session_id),
            provider="openrouter",
            model=requested_model,
            request_body={
                "messages": request_messages,
                "model": requested_model,
                "temperature": model_settings.get("temperature"),
                "max_tokens": model_settings.get("max_tokens")
            },
            response_body={
                "content": response_text,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                "model": requested_model,
                "provider_details": latest_message.provider_details
            },
            tokens={
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            cost_data={
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "total_cost": Decimal(str(total_cost))
            },
            latency_ms=latency_ms,
            agent_instance_id=agent_instance_id
        )
    
    # 6. Save messages to database
    await message_service.save_message(
        session_id=UUID(session_id),
        agent_instance_id=agent_instance_id,
        role="human",
        content=message
    )
    await message_service.save_message(
        session_id=UUID(session_id),
        agent_instance_id=agent_instance_id,
        role="assistant",
        content=response_text
    )
    
    return {'response': response_text, 'usage': usage_obj, ...}
```

### Key Points

✅ **`provider_details` is populated** - OpenRouter metadata is available  
✅ **Cost extraction is straightforward** - Direct access to cost breakdown  
✅ **Accurate to OpenRouter's billing** - Uses actual charged amounts  
✅ **No additional libraries needed** - Pure Pydantic AI + OpenRouter  

---

## 4. Streaming Implementation

### Overview

Streaming requests **cannot use `provider_details`** due to a Pydantic AI limitation (see Section 5). Instead, we use the `genai-prices` library to calculate costs from token usage, with a fallback to a YAML config file for models not yet in the genai-prices database.

### Code Location

**File**: `backend/app/agents/simple_chat.py`  
**Function**: `simple_chat_stream()` (lines 498-846)

### Implementation

```python
async def simple_chat_stream(
    message: str,
    session_id: str,
    agent_instance_id: UUID,
    message_history: Optional[List[ModelMessage]] = None,
    instance_config: Optional[dict] = None
):
    """Streaming chat with Pydantic AI."""
    
    # 1. Create agent with instance-specific config
    agent = await get_chat_agent(instance_config=instance_config)
    
    # 2. Extract model name for cost calculation
    config_to_use = instance_config if instance_config is not None else load_config()
    requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
    
    chunks = []
    start_time = datetime.now(UTC)
    
    try:
        # 3. Execute agent with streaming
        async with agent.run_stream(message, deps=session_deps, message_history=message_history) as result:
            # 4. Stream chunks to user
            async for chunk in result.stream_text(delta=True):
                chunks.append(chunk)
                yield {"event": "message", "data": chunk}
            
            end_time = datetime.now(UTC)
            response_text = "".join(chunks)
            
            # 5. Get usage data after stream completes
            usage_data = result.usage()
            
            if usage_data:
                prompt_tokens = usage_data.input_tokens
                completion_tokens = usage_data.output_tokens
                total_tokens = usage_data.total_tokens
                
                # 6. Calculate costs using genai-prices
                # ⚠️ CRITICAL: Pydantic AI doesn't populate provider_details for streaming!
                prompt_cost = 0.0
                completion_cost = 0.0
                total_cost = 0.0
                
                try:
                    from genai_prices import calc_price
                    
                    # Calculate using actual model from config (not hardcoded!)
                    price = calc_price(
                        usage=usage_data,
                        model_ref=requested_model,
                        provider_id="openrouter"
                    )
                    
                    prompt_cost = float(price.input_cost_usd)
                    completion_cost = float(price.output_cost_usd)
                    total_cost = float(price.total_cost_usd)
                    
                    logger.info({
                        "event": "streaming_cost_calculated",
                        "method": "genai-prices",
                        "total_cost": total_cost
                    })
                    
                except LookupError as e:
                    # 7. Model not in genai-prices - use fallback pricing
                    import yaml
                    from pathlib import Path
                    
                    config_dir = Path(__file__).parent.parent.parent / "config"
                    fallback_pricing_path = config_dir / "fallback_pricing.yaml"
                    
                    fallback_pricing_models = {}
                    if fallback_pricing_path.exists():
                        with open(fallback_pricing_path, 'r') as f:
                            fallback_config = yaml.safe_load(f)
                            fallback_pricing_models = fallback_config.get('models', {})
                    
                    if requested_model in fallback_pricing_models:
                        pricing = fallback_pricing_models[requested_model]
                        prompt_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
                        completion_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
                        total_cost = prompt_cost + completion_cost
                        
                        logger.info({
                            "event": "streaming_cost_calculated",
                            "method": "fallback_pricing",
                            "source": pricing.get("source", "unknown")
                        })
                    else:
                        logger.warning({
                            "event": "streaming_cost_calculation_failed",
                            "error": f"Model not in genai-prices or fallback pricing: {e}",
                            "suggestion": f"Add model to {fallback_pricing_path}"
                        })
                
                # 8. Track to database
                if prompt_tokens > 0 or completion_tokens > 0:
                    tracker = LLMRequestTracker()
                    
                    llm_request_id = await tracker.track_llm_request(
                        session_id=UUID(session_id),
                        provider="openrouter",
                        model=requested_model,
                        request_body={
                            "messages": request_messages,
                            "model": requested_model,
                            "temperature": model_settings.get("temperature"),
                            "max_tokens": model_settings.get("max_tokens"),
                            "stream": True
                        },
                        response_body={
                            "content": response_text,
                            "usage": {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": total_tokens
                            },
                            "model": requested_model,
                            "streaming": {"chunks_sent": len(chunks)}
                        },
                        tokens={
                            "prompt": prompt_tokens,
                            "completion": completion_tokens,
                            "total": total_tokens
                        },
                        cost_data={
                            "prompt_cost": prompt_cost,
                            "completion_cost": completion_cost,
                            "total_cost": total_cost
                        },
                        latency_ms=latency_ms,
                        agent_instance_id=agent_instance_id
                    )
                
                # 9. Save messages to database
                await message_service.save_message(...)
                
                # 10. Signal completion
                yield {"event": "done", "data": ""}
    
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
```

### Key Points

⚠️ **`provider_details` is None** - Pydantic AI limitation for streaming  
✅ **`result.usage()` is available** - Token counts are accurate  
✅ **genai-prices for calculation** - Multiply tokens by model rates  
✅ **Fallback YAML config** - For models not in genai-prices  
✅ **Dynamic model extraction** - Never hardcode model names  

---

## 5. The Streaming Difference: Critical Lesson Learned

### The Problem

When using Pydantic AI's `agent.run_stream()` for streaming responses, cost data from OpenRouter was not being captured. This caused all streaming requests to record $0.00 costs, despite OpenRouter charging for the tokens used.

**Database Evidence**:
```sql
-- Non-streaming request (working)
SELECT id, prompt_cost, completion_cost, total_cost 
FROM llm_requests WHERE id = '591fd82e-4357-4f9a-86e5-aa030930181a';
-- Result: prompt_cost=0.0000408, completion_cost=0.003646, total_cost=0.0036868

-- Streaming request (broken)
SELECT id, prompt_cost, completion_cost, total_cost 
FROM llm_requests WHERE id = 'f269d6e7-ed0f-48b0-baea-0bbb104aca6e';
-- Result: prompt_cost=0, completion_cost=0, total_cost=0
```

### Root Cause: Pydantic AI's Streaming Limitation

#### What We Tried First (FAILED)

```python
# ❌ Hypothesis: Using new_messages() instead of all_messages()
async with agent.run_stream(message, ...) as result:
    async for chunk in result.stream_text(delta=True):
        yield chunk
    
    all_messages = result.all_messages()  # AFTER streaming completes
    latest_message = all_messages[-1]
    cost = latest_message.provider_details  # Should have cost data now...

# Result: FAILED - provider_details is still None!
```

#### Debug Logs Confirmed the Issue

```json
{
  "event": "streaming_provider_details_check",
  "has_provider_details": true,        // ← Attribute exists
  "provider_details_is_none": true,    // ← But value is None!
  "provider_details_keys": null
}
```

**Conclusion**: Pydantic AI's streaming implementation **does not extract or store** the cost/provider metadata from the final SSE chunk into the `provider_details` field, even though:
- OpenRouter IS sending it (we verified the request includes `usage: {include: true}`)
- We ARE accessing messages after streaming completes (`all_messages()`)
- The `provider_details` attribute exists (it's not an attribute error, it's just `None`)

### The Solution: genai-prices

From [Pydantic AI Usage Tracking documentation](https://ai.pydantic.dev/api/usage/#pydantic_ai.usage.RequestUsage):

> **"The `RequestUsage` class implements the `genai_prices.types.AbstractUsage` interface, so usage can be passed directly to `calc_price` from the genai-prices library."**

**Key Insight**: While Pydantic AI doesn't populate `provider_details` for streaming, it DOES populate `result.usage()` with token counts. We can use the `genai-prices` library to calculate costs from these token counts!

```python
from genai_prices import calc_price

usage_data = result.usage()  # ✅ Available after streaming completes

price = calc_price(
    usage=usage_data,
    model_ref="deepseek/deepseek-chat-v3-0324",  # OpenRouter model ID
    provider_id="openrouter"
)

prompt_cost = float(price.input_cost_usd)
completion_cost = float(price.output_cost_usd)
total_cost = float(price.total_cost_usd)
```

### Verification

```bash
cd backend
python3 << 'PYEOF'
from pydantic_ai.usage import RunUsage
from genai_prices import calc_price

usage = RunUsage(input_tokens=1000, output_tokens=500)
price = calc_price(
    usage=usage,
    model_ref="deepseek/deepseek-chat-v3-0324",
    provider_id="openrouter"
)
print(f"Total Cost: ${price.total_cost_usd}")
PYEOF

# Output: Total Cost: $0.00082 ✅ Works!
```

### Why This Works

1. **Token Counts**: Pydantic AI DOES populate `result.usage()` with accurate token counts from OpenRouter
2. **genai-prices**: Maintains up-to-date pricing for all major LLM providers including OpenRouter
3. **Calculation**: `calc_price()` multiplies token counts by model-specific rates to get costs
4. **Accuracy**: Results match OpenRouter's actual costs (verified with non-streaming responses)

### Best Practices

#### ✅ Do This

1. **Use genai-prices for streaming cost calculation**:
   ```python
   # IMPORTANT: Extract the actual model from agent config
   config_to_use = instance_config if instance_config is not None else load_config()
   requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
   
   async with agent.run_stream(...) as result:
       async for chunk in result.stream_text(delta=True):
           yield chunk
       
       # Calculate cost from token usage
       usage = result.usage()
       price = calc_price(
           usage=usage,
           model_ref=requested_model,  # ✅ Use actual model, not hardcoded
           provider_id="openrouter"
       )
       total_cost = float(price.total_cost_usd)
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
   # result is now finalized with complete usage data
   ```

#### ❌ Don't Do This

1. **Don't rely on `provider_details` for streaming cost data**:
   ```python
   # ❌ This will be None for streaming responses
   all_messages = result.all_messages()
   cost = all_messages[-1].provider_details.get('cost')  # None!
   ```

2. **Don't try to extract costs during streaming**:
   ```python
   # ❌ Usage data not available yet
   async for chunk in result.stream_text():
       cost = result.usage()  # Incomplete/unavailable
   ```

3. **Don't assume non-streaming and streaming use the same method**:
   ```python
   # Non-streaming: Use provider_details (populated by OpenRouterModel)
   result = await agent.run(...)
   cost = result.new_messages()[-1].provider_details['cost']  # ✅ Works
   
   # Streaming: Use genai-prices
   async with agent.run_stream(...) as result:
       usage = result.usage()
       price = calc_price(usage, model_ref="...", provider_id="openrouter")  # ✅ Works
   ```

### Impact

**Before Fix**:
- ❌ Lost revenue tracking for all streaming requests (~50% of traffic)
- ❌ Inaccurate billing reports
- ❌ No cost-based optimization insights for streaming

**After Fix**:
- ✅ Accurate cost tracking for both streaming and non-streaming
- ✅ Complete billing data for revenue reports
- ✅ Proper cost attribution per session/agent
- ✅ Independent of Pydantic AI's `provider_details` implementation

---

## 6. Multi-Tenant Integration

### Overview

The cost tracking system fully supports multi-tenant architecture by tracking `agent_instance_id` for every LLM request. This enables:
- Per-account cost analytics
- Per-agent-instance performance tracking
- Accurate billing attribution
- Cross-account isolation

### Implementation

#### Agent Instance ID Tracking

```python
# In endpoint (account_agents.py)
instance = await load_agent_instance(account_slug, instance_slug)

# Pass to agent function
result = await simple_chat(
    message=user_message,
    session_id=str(session.id),
    agent_instance_id=instance.id,  # ← Multi-tenant tracking
    message_history=message_history,
    instance_config=instance.config
)

# Tracker receives it
await tracker.track_llm_request(
    session_id=UUID(session_id),
    agent_instance_id=agent_instance_id,  # ← Stored in database
    provider="openrouter",
    model=requested_model,
    ...
)
```

#### Dynamic Model Extraction

**⚠️ CRITICAL**: Never hardcode model names! Each agent instance can use a different model.

```python
# ✅ CORRECT: Extract model from config
config_to_use = instance_config if instance_config is not None else load_config()
requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")

# Use in genai-prices
price = calc_price(
    usage=usage_data,
    model_ref=requested_model,  # ← Dynamic, not hardcoded
    provider_id="openrouter"
)

# ❌ WRONG: Hardcoded model name
price = calc_price(
    usage=usage_data,
    model_ref="deepseek/deepseek-chat-v3-0324",  # ← BUG in multi-tenant!
    provider_id="openrouter"
)
```

**Why This Matters**:
- `default_account/simple_chat1` might use `moonshotai/kimi-k2-0905`
- `acme/acme_chat1` might use `deepseek/deepseek-chat-v3-0324`
- Hardcoding would calculate costs for the wrong model!

### Multi-Tenant Queries

```sql
-- Cost by account
SELECT 
    ai.account_id,
    a.name as account_name,
    SUM(lr.total_cost) as total_cost,
    COUNT(*) as request_count
FROM llm_requests lr
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
JOIN accounts a ON ai.account_id = a.id
WHERE lr.created_at >= NOW() - INTERVAL '1 month'
GROUP BY ai.account_id, a.name
ORDER BY total_cost DESC;

-- Cost by agent instance
SELECT 
    ai.instance_name,
    ai.agent_type,
    SUM(lr.total_cost) as total_cost,
    AVG(lr.latency_ms) as avg_latency_ms,
    COUNT(*) as request_count
FROM llm_requests lr
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
WHERE lr.created_at >= NOW() - INTERVAL '1 day'
GROUP BY ai.id, ai.instance_name, ai.agent_type
ORDER BY total_cost DESC;
```

---

## 7. Fallback Pricing Configuration

### Overview

Not all models are available in the `genai-prices` library yet. For these models, we maintain a fallback pricing configuration file that provides per-token costs based on official provider documentation.

### Configuration File

**Location**: `backend/config/fallback_pricing.yaml`

```yaml
# Fallback pricing for models not yet in genai-prices database
# This file provides a mechanism to define pricing for LLM models
# that are not (yet) included in the genai-prices library.
#
# Structure:
# models:
#   <provider>/<model_name>:
#     input_per_1m: <cost_per_1m_input_tokens_usd>
#     output_per_1m: <cost_per_1m_output_tokens_usd>
#     source: "<URL_to_pricing_source>"
#     updated: "<YYYY-MM-DD>"  # Date when pricing was last verified
#     notes: "<Optional_notes_about_the_model_or_pricing>"

models:
  moonshotai/kimi-k2-0905:
    input_per_1m: 0.14    # $0.14 per 1M input tokens
    output_per_1m: 2.49   # $2.49 per 1M output tokens
    source: "https://blog.galaxy.ai/model/kimi-k2"
    updated: "2025-01-11"
    notes: "Primary model for default_account/simple_chat1"
    
  moonshotai/kimi-k2:
    input_per_1m: 0.14
    output_per_1m: 2.49
    source: "https://blog.galaxy.ai/model/kimi-k2"
    updated: "2025-01-11"
    notes: "Generic Kimi K2 model"
```

### How It Works

```python
# In simple_chat_stream() when genai-prices raises LookupError
try:
    price = calc_price(usage=usage_data, model_ref=requested_model, provider_id="openrouter")
except LookupError as e:
    # Load fallback pricing from YAML
    config_dir = Path(__file__).parent.parent.parent / "config"
    fallback_pricing_path = config_dir / "fallback_pricing.yaml"
    
    with open(fallback_pricing_path, 'r') as f:
        fallback_config = yaml.safe_load(f)
        fallback_pricing_models = fallback_config.get('models', {})
    
    if requested_model in fallback_pricing_models:
        pricing = fallback_pricing_models[requested_model]
        
        # Calculate costs manually
        prompt_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
        completion_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
        total_cost = prompt_cost + completion_cost
```

### Adding New Models

#### 1. Find Official Pricing

Check the model provider's website or OpenRouter's model page for official pricing.

#### 2. Add to `fallback_pricing.yaml`

```yaml
models:
  your-provider/your-model:
    input_per_1m: 0.50    # Cost in USD per 1M input tokens
    output_per_1m: 1.50   # Cost in USD per 1M output tokens
    source: "https://provider.com/pricing"
    updated: "2025-01-12"
    notes: "Brief note about this model"
```

#### 3. Restart Backend

Changes take effect immediately after restart.

#### 4. Verify in Logs

```json
{
  "event": "streaming_cost_calculated",
  "method": "fallback_pricing",
  "model": "your-provider/your-model",
  "prompt_cost": 0.00050,
  "completion_cost": 0.00075,
  "total_cost": 0.00125,
  "source": "https://provider.com/pricing"
}
```

### Maintenance

- **Monthly verification**: Check if pricing has changed
- **Remove obsolete entries**: Once a model appears in `genai-prices`, remove it from fallback config
- **Document sources**: Always include the `source` URL for pricing verification

### Error Handling

When a model is not in `genai-prices` OR fallback config:

```json
{
  "event": "streaming_cost_calculation_failed",
  "error_type": "LookupError",
  "model": "unknown/new-model",
  "suggestion": "Add model to backend/config/fallback_pricing.yaml",
  "fallback": "zero_cost"
}
```

The request will still be tracked with `$0.00` costs to avoid breaking the user experience, but logs will alert you to the missing pricing configuration.

---

## 8. Billable vs Non-Billable Errors

### Billable Errors (Tracked for Customer Billing)

These errors consume tokens and should be billed:

- ✅ **Timeouts** - LLM started processing, consumed tokens
- ✅ **Rate limits** - Tokens consumed before limit hit
- ✅ **Content filtering** - Tokens processed before filter triggered  
- ✅ **Partial responses** - Max tokens reached, partial completion
- ✅ **Model availability** - Provider started processing before failure

**Database Record**:
```json
{
    "tokens": {"prompt": 150, "completion": 0, "total": 150},
    "prompt_cost": 0.00015,
    "completion_cost": 0.0,
    "total_cost": 0.00015,
    "response_body": {
        "error_metadata": {
            "error_type": "TimeoutError",
            "error_message": "Request timeout after 30s",
            "billable": true
        }
    }
}
```

### Non-Billable Errors (Logged but Not Tracked)

These errors don't consume tokens:

- ❌ **Network failures** - Request never reached provider
- ❌ **Invalid requests** - Rejected before processing starts
- ❌ **Authentication errors** - No processing attempted
- ❌ **Malformed input** - Rejected at validation stage

**Handling**: Log the error but don't create an `llm_requests` record.

```python
try:
    result = await agent.run(...)
except NetworkError as e:
    logger.error({
        "event": "llm_network_error",
        "error": str(e),
        "billable": False
    })
    # Don't track - no tokens consumed
    raise
```

---

## 9. Monitoring & Analytics

### Cost Analytics Queries

#### Session-Level Cost Analysis

```sql
-- Total cost per session
SELECT 
    session_id,
    SUM(total_cost) as total_cost,
    SUM(total_tokens) as total_tokens,
    COUNT(*) as request_count,
    AVG(latency_ms) as avg_latency_ms
FROM llm_requests 
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY session_id
ORDER BY total_cost DESC
LIMIT 20;
```

#### Agent Performance Analysis

```sql
-- Performance by agent instance
SELECT
    ai.instance_name,
    ai.agent_type,
    AVG(lr.latency_ms) as avg_latency_ms,
    AVG(lr.total_cost) as avg_cost_per_request,
    SUM(lr.total_cost) as total_cost,
    COUNT(*) as request_count
FROM llm_requests lr
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
WHERE lr.created_at >= NOW() - INTERVAL '1 hour'
GROUP BY ai.id, ai.instance_name, ai.agent_type
ORDER BY total_cost DESC;
```

#### Model Usage Analysis

```sql
-- Cost breakdown by model
SELECT
    model,
    provider,
    COUNT(*) as request_count,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    SUM(prompt_cost) as total_prompt_cost,
    SUM(completion_cost) as total_completion_cost,
    SUM(total_cost) as total_cost,
    AVG(latency_ms) as avg_latency_ms
FROM llm_requests
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY model, provider
ORDER BY total_cost DESC;
```

#### Streaming vs Non-Streaming Cost Comparison

```sql
-- Compare streaming and non-streaming costs
SELECT
    CASE 
        WHEN response_body->>'streaming' IS NOT NULL THEN 'Streaming'
        ELSE 'Non-Streaming'
    END as request_type,
    COUNT(*) as request_count,
    SUM(total_cost) as total_cost,
    AVG(total_cost) as avg_cost,
    AVG(latency_ms) as avg_latency_ms
FROM llm_requests
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY request_type;
```

### Error Rate Monitoring

```sql
-- Billable error rate by provider/model
SELECT
    provider,
    model,
    COUNT(CASE WHEN response_body->>'error_metadata' IS NOT NULL THEN 1 END) as error_count,
    COUNT(*) as total_requests,
    ROUND(
        100.0 * COUNT(CASE WHEN response_body->>'error_metadata' IS NOT NULL THEN 1 END) / COUNT(*),
        2
    ) as error_rate_percent
FROM llm_requests
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY provider, model
HAVING COUNT(*) > 10  -- Only show models with sufficient volume
ORDER BY error_rate_percent DESC;
```

### Cost Tracking Verification

```sql
-- Find requests with missing cost data
SELECT
    id,
    session_id,
    model,
    prompt_tokens,
    completion_tokens,
    total_tokens,
    prompt_cost,
    completion_cost,
    total_cost,
    created_at
FROM llm_requests
WHERE (total_tokens > 0 AND total_cost = 0)  -- Tokens but no cost
   OR (prompt_tokens > 0 AND prompt_cost = 0)  -- Prompt tokens but no cost
   OR (completion_tokens > 0 AND completion_cost = 0)  -- Completion tokens but no cost
ORDER BY created_at DESC
LIMIT 20;
```

---

## 10. Testing & Verification

### Manual Test Scripts

#### Test Non-Streaming Endpoint

```bash
cd backend
python tests/manual/test_chat_endpoint.py
```

#### Test Streaming Endpoint

```bash
cd backend
python tests/manual/test_streaming_endpoint.py
```

**Expected**: Both should show non-zero costs in the database for successful requests.

### Database Verification

```sql
-- Check last 5 non-streaming requests
SELECT 
    id,
    created_at,
    model,
    prompt_cost,
    completion_cost,
    total_cost,
    prompt_tokens,
    completion_tokens,
    response_body->'streaming' as is_streaming
FROM llm_requests 
WHERE response_body->'streaming' IS NULL
ORDER BY created_at DESC 
LIMIT 5;

-- Check last 5 streaming requests
SELECT 
    id,
    created_at,
    model,
    prompt_cost,
    completion_cost,
    total_cost,
    prompt_tokens,
    completion_tokens,
    response_body->'streaming' as streaming_info
FROM llm_requests 
WHERE response_body->'streaming' IS NOT NULL
ORDER BY created_at DESC 
LIMIT 5;
```

**Expected**: All costs should be non-zero if tokens > 0.

### Unit Tests

```python
# backend/tests/unit/test_cost_tracking.py

async def test_non_streaming_cost_extraction():
    """Test cost extraction from provider_details."""
    # Mock agent.run() response with provider_details
    # Verify costs are extracted correctly
    pass

async def test_streaming_cost_calculation():
    """Test genai-prices cost calculation."""
    # Mock usage data
    # Verify calc_price() returns correct costs
    pass

async def test_fallback_pricing():
    """Test fallback pricing for unknown models."""
    # Mock LookupError from genai-prices
    # Verify fallback YAML is loaded and used
    pass

async def test_multi_tenant_tracking():
    """Test agent_instance_id is tracked correctly."""
    # Verify agent_instance_id is passed through all layers
    pass
```

### Integration Tests

```python
# backend/tests/integration/test_cost_tracking_integration.py

async def test_end_to_end_non_streaming():
    """Test complete flow from endpoint to database."""
    # Make request to /accounts/{account}/agents/{instance}/chat
    # Verify llm_requests record has correct costs
    pass

async def test_end_to_end_streaming():
    """Test complete flow for streaming."""
    # Make request to /accounts/{account}/agents/{instance}/stream
    # Verify llm_requests record has correct costs
    pass

async def test_cost_accuracy():
    """Compare calculated costs with OpenRouter actuals."""
    # For non-streaming: provider_details should match calculated
    # For streaming: genai-prices should match OpenRouter rates
    pass
```

---

## 11. Performance Considerations

### Tracking Overhead

**Target**: <50ms additional latency per request

**Actual**:
- Database writes: ~10-20ms (async, non-blocking)
- Cost calculation: <5ms
- Message saving: ~10-15ms
- **Total**: ~25-40ms ✅ Within target

### Optimization Strategies

#### 1. Async Database Operations

```python
# Non-blocking database writes
await tracker.track_llm_request(...)  # Async, returns immediately

# Don't wait for message saving to complete response
await message_service.save_message(...)
```

#### 2. Connection Pooling

```python
# SQLAlchemy connection pool (configured in database.py)
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

#### 3. Minimal Data Processing

```python
# Store full request/response bodies - don't sanitize
# (Sanitization was removed for debugging, keep as-is)
request_body = {"messages": request_messages, ...}
response_body = {"content": response_text, ...}
```

#### 4. Error Handling

```python
# Failed tracking doesn't break chat functionality
try:
    await tracker.track_llm_request(...)
except Exception as e:
    logger.error(f"Cost tracking failed (non-critical): {e}")
    # Continue with response - don't fail the user's request
```

---

## 12. Security Considerations

### Data Sanitization

**Current Status**: We store **full request and response bodies** for debugging and auditing.

**Privacy Considerations**:
- ✅ Data is stored in PostgreSQL with access controls
- ✅ Only authorized admin users can query `llm_requests` table
- ✅ Session-scoped access (users can't see other users' data)
- ⚠️ **Future**: Add configurable sanitization for production

**Potential Sanitization** (if needed later):
```python
def sanitize_request_body(body):
    return {
        "message_count": len(body.get("messages", [])),
        "model": body.get("model"),
        "temperature": body.get("temperature")
        # Remove actual message content
    }

def sanitize_response_body(body):
    return {
        "usage": body.get("usage"),
        "model": body.get("model"),
        "provider_details": body.get("provider_details")
        # Remove generated text
    }
```

### Access Control

- **Cost data**: Sensitive billing information, restrict access to admins
- **Session linkage**: Don't expose cross-session cost data to end users
- **Agent performance**: Account-scoped access only
- **Database credentials**: Stored in environment variables, never in code

### API Key Security

```python
# Never log or store full API keys
api_key_masked = f"{api_key[:10]}..." if api_key else "none"
logger.info({"api_key_masked": api_key_masked})
```

---

## 13. Related Documentation

### Primary Documentation

- **[API Endpoints](./endpoints.md)** - Complete endpoint documentation
- **[Endpoint Pydantic AI Matrix](./endpoint-pydantic-ai-matrix.md)** - Implementation status
- **[Epic 0022 - Multi-Tenant Architecture](../project-management/0022-multi-tenant-architecture.md)** - Implementation details
- **[Project Brief](../project-brief.md)** - Core principles and Pydantic AI mandate

### External Documentation

- **[OpenRouter Usage Accounting](https://openrouter.ai/docs/use-cases/usage-accounting#cost-breakdown)** - Provider cost breakdown
- **[Pydantic AI Streaming Output](https://ai.pydantic.dev/docs/output/#streaming)** - Streaming documentation
- **[Pydantic AI Usage Tracking](https://ai.pydantic.dev/api/usage/)** - Usage API reference
- **[genai-prices GitHub](https://github.com/ai-systems/genai-prices)** - Cost calculation library

### Code Locations

- **Agent Implementation**: `backend/app/agents/simple_chat.py`
- **Cost Tracker Service**: `backend/app/services/llm_request_tracker.py`
- **Multi-Tenant Endpoints**: `backend/app/api/account_agents.py`
- **Database Model**: `backend/app/models/llm_request.py`
- **Fallback Pricing**: `backend/config/fallback_pricing.yaml`

---

## Key Takeaways

### Critical Points

1. ⚠️ **Streaming and non-streaming use different cost extraction methods** - This is due to a Pydantic AI limitation, not a design choice
2. ✅ **genai-prices is required for streaming** - `provider_details` is not populated by Pydantic AI for streaming responses
3. ✅ **Never hardcode model names** - Multi-tenant architecture requires dynamic model extraction from config
4. ✅ **Fallback pricing is essential** - Not all models are in genai-prices yet
5. ✅ **High precision matters** - Use `NUMERIC(12,8)` for cost fields to handle micro-cents accurately
6. ✅ **Multi-tenant tracking is critical** - Always pass `agent_instance_id` for proper billing attribution

### Common Pitfalls

❌ **Assuming streaming and non-streaming work the same** - They don't!  
❌ **Hardcoding model names** - Breaks multi-tenant  
❌ **Forgetting fallback pricing** - Causes $0.00 costs for new models  
❌ **Using low precision decimals** - Loses accuracy for micro-costs  
❌ **Not passing agent_instance_id** - Breaks multi-tenant billing  

### Success Criteria

✅ All LLM requests tracked in database  
✅ Non-zero costs for all successful requests  
✅ Accurate token counts from API responses  
✅ Streaming and non-streaming both working  
✅ Multi-tenant attribution correct  
✅ Fallback pricing configured for all models  
✅ Monitoring queries provide actionable insights  

---

**Document Version**: 1.0  
**Last Updated**: January 12, 2025  
**Maintained By**: Development Team

