# OpenRouter Cost Tracking Solution Plan

## Problem Analysis
- **Root Cause**: OpenRouter requires `"usage": {"include": true}` parameter to return cost data  
- **Current Issue**: Pydantic AI doesn't support passing this parameter through `agent.run()`
- **Evidence**: Direct API call works, Pydantic AI call returns `cost: 0.0`

## Solution Approaches to Test

### Approach 1: Configure Pydantic AI OpenAI Provider with extra_body
**Theory**: OpenAI SDK supports `extra_body` parameter to pass additional fields
**Test**: See if Pydantic AI's OpenAI provider forwards extra_body to the API
**Expected**: If successful, should get cost data in Pydantic AI response

### Approach 2: Use OpenAI SDK Directly with OpenRouter
**Theory**: Bypass Pydantic AI, use OpenAI SDK configured for OpenRouter
**Test**: Configure OpenAI client with OpenRouter base_url and usage parameter  
**Expected**: Full control over API request, guaranteed cost data

### Approach 3: Use Fixed openrouter_client.py 
**Theory**: Our existing client now has `"usage": {"include": true}` parameter
**Test**: Replace Pydantic AI call with openrouter_client.chat_completion_with_usage()
**Expected**: Single API call with accurate cost tracking

### Approach 4: Hybrid - Best of Both Worlds
**Theory**: Use Pydantic AI for features + openrouter_client for cost data
**Test**: Make both calls but use same conversation context
**Expected**: Get Pydantic AI benefits + accurate costs (but doubles API calls)

## Implementation Plan

1. **Test Approach 1** - Most ideal if it works
2. **Test Approach 2** - Good compromise 
3. **Test Approach 3** - Reliable fallback
4. **Avoid Approach 4** - Doubles costs (user feedback)

## Success Criteria
- ✅ Get real OpenRouter cost data (not 0.0)
- ✅ Single API call (no cost doubling) 
- ✅ Maintain conversation quality
- ✅ Store accurate costs in database
