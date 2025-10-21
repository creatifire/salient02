# Pydantic AI Fork

## Problem
OpenRouter cost tracking failed because Pydantic AI's `_map_usage()` function only accepted integers, but OpenRouter returns floating-point costs.

## Solution
Forked pydantic-ai and modified `_map_usage()` to accept both integers and floats:
```python
# Before: isinstance(value, int)
# After: isinstance(value, (int, float))
```

## Integration Approach
Instead of using the fork, we implemented a custom `OpenRouterModel` that extends `OpenAIChatModel` to extract cost data from `ModelResponse.provider_details`.

## Current Implementation
- `backend/app/agents/openrouter.py` - Custom OpenRouter model with cost extraction
- `backend/app/agents/simple_chat.py` - Uses `OpenRouterModel` with cost tracking
- Cost data extracted from `result.new_messages()[-1].provider_details.get('cost')`

## Status
Fork created but not used. Custom solution provides OpenRouter cost tracking without dependency on forked code.
