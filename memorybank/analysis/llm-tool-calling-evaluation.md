# LLM Tool Calling Evaluation

**Date**: October 28, 2025  
**Context**: Evaluating which LLM models reliably execute tool calls for PrepExcellence and Wyckoff agents using Pydantic AI + OpenRouter

## Problem Statement

Claude 3.5/3.7 Sonnet and GPT-5 failed to reliably call tools in production:
- **Claude 3.5/3.7**: Says "I'll search" but doesn't execute `vector_search` tool
- **GPT-5**: Extremely slow tool calling performance

## Testing Results

| Model | Tool Calling | Speed | Result |
|-------|-------------|-------|--------|
| `google/gemini-2.5-flash` | ✅ Works | Fast | **PRODUCTION** |
| `anthropic/claude-3.5-sonnet` | ❌ Broken | N/A | Says will search, doesn't execute |
| `anthropic/claude-3.7-sonnet` | ❌ Broken | N/A | Same issue as 3.5 |
| `openai/gpt-5` | ⚠️ Slow | Very Slow | Works but unusable |

### Evidence from Logs

**Gemini 2.5 Flash** (Working):
```
00:07:48.071     running 1 tool
00:07:48.072       running tool: vector_search
00:07:48.417         pinecone.query
00:07:49.409           pinecone.search
```

**Claude 3.7 Sonnet** (Broken):
```
prompt_tokens: 2650, completion_tokens: 104
Response: "I'll search for information..." 
[No tool execution logged]
```

## Research Findings

### Sources

1. **Anthropic Documentation**: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use
2. **Berkeley Function Calling Leaderboard (BFCL)**: https://gorilla.cs.berkeley.edu/leaderboard.html
3. **Community Reports**: AWS re:Post, Meta Discourse, GitHub discussions
4. **Pydantic AI Documentation**: https://github.com/pydantic/pydantic-ai

### Claude 3.7 Sonnet Issue

**Root Cause**: Claude 3.7 introduced "thinking tokens" and extended reasoning mode which interferes with tool execution.

**Known Problems** (multiple sources):
- Incorrect function call formats
- Model describes tool usage instead of executing
- Higher token consumption
- Repeated tool calls without parameters

**Official Solution**: Use `tool_choice` parameter to force tool execution:
```json
{"tool_choice": {"type": "tool", "name": "vector_search"}}
```

**Blocker**: Pydantic AI doesn't expose `tool_choice` parameter for Anthropic models.

### Top Models for Tool Calling

Based on Berkeley Function Calling Leaderboard and testing:

| Rank | Model | Availability | Cost | Notes |
|------|-------|--------------|------|-------|
| 1 | GPT-4o | OpenRouter | Medium | Industry standard, reliable |
| 2 | Gemini 2.5 Flash | OpenRouter | Low | **Best balance: speed/cost/reliability** |
| 3 | Gemini 2.5 Pro | OpenRouter | Medium | More capable, slower |
| 4 | Cohere Command R+ | OpenRouter | Medium | Built for RAG/tools |
| 5 | Qwen 2.5-72B | OpenRouter | Very Low | Strong open-source option |
| 6 | Mistral Large | OpenRouter | Medium | Good European alternative |
| 7 | DeepSeek V3 | OpenRouter | Very Low | Surprisingly good for price |

### Specialized Tool-Calling Models

| Model | Size | Accuracy | Use Case |
|-------|------|----------|----------|
| Gorilla OpenFunctions v2 | 7B | 85%+ | Pure API calling |
| Nous Hermes 2 Pro | 7B | 90% | Fast, edge deployment |
| FireFunction V1 | Mixtral 8x7B | Near GPT-4 | Multi-agent routing |

## Analysis Method

1. **Empirical Testing**: Tested Claude 3.7, Gemini 2.5 Flash with PrepExcellence agent
2. **Log Analysis**: Examined tool execution traces in Logfire
3. **Literature Review**: Researched Berkeley BFCL leaderboard, community reports
4. **Cross-reference**: Validated findings against Pydantic AI capabilities

## Recommendations

### Use Gemini 2.5 Flash for:
- Production agents requiring reliable tool calling
- Vector search (PrepExcellence)
- Directory search (Wyckoff)
- Multi-tool scenarios
- Cost-sensitive deployments

### Alternative Options:
- **GPT-4o-mini**: OpenAI ecosystem compatibility needed
- **Qwen 2.5-72B**: High-volume, budget-critical applications
- **DeepSeek V3**: Extreme cost optimization ($0.27/$1.10 per 1M tokens)
- **Cohere Command R+**: Complex RAG with citation requirements

### Avoid:
- **Claude 3.5/3.7 Sonnet**: Until Pydantic AI exposes `tool_choice` parameter
- **GPT-5 (o-series)**: Too slow for real-time applications
- **Claude Opus**: Similar issues to Sonnet models

## Implementation

Current production configuration:
```yaml
# backend/config/agent_configs/prepexcellence/prepexcel_info_chat1/config.yaml
model_settings:
  model: "google/gemini-2.5-flash"
  temperature: 0.3
  max_tokens: 2000
```

**Status**: ✅ Working reliably in production (Wyckoff + PrepExcellence agents)

## Future Considerations

1. Monitor Pydantic AI for `tool_choice` parameter support
2. Watch for Claude model updates addressing tool calling
3. Benchmark Qwen 2.5 and DeepSeek V3 if cost optimization needed
4. Re-evaluate when Berkeley BFCL updates rankings

