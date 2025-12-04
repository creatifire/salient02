<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# System Prompt Assembly Guide

> **Last Updated**: December 4, 2025  
> **Related**: [agent-configuration-guide.md](agent-configuration-guide.md), [adding-modifying-directory-schemas.md](adding-modifying-directory-schemas.md)

## Overview

The system prompt is **NOT a single file** - it's a **multi-component assembly** that combines multiple sources to create comprehensive agent instructions. This guide explains how the system prompt is constructed and what gets sent to the LLM with each request.

## System Prompt Assembly Process

The system prompt is assembled in a **specific order** from multiple sources. Each component serves a distinct purpose in guiding the LLM's behavior.

### Assembly Order

```
FINAL SYSTEM PROMPT = 
  [1. Critical Rules - tool_selection_hints.md]           ← Position 1 (TOP)
  + [2. Base System Prompt - system_prompt.md]            ← Position 2
  + [3. Directory Documentation - auto-generated]         ← Position 3
  + [4. Other Prompt Modules - selected modules]          ← Position 4
```

---

## Component 1: Critical Rules (Optional)

**File**: `backend/config/prompt_modules/system/tool_selection_hints.md`

**Purpose**: Tool selection guidance - how to choose between available tools

**When included**: If `prompting.modules.enabled: true` in agent config

**Position**: **TOP of prompt** (most critical - LLM sees this first)

**Why it's first**: Tool selection logic must be established before the LLM sees tool descriptions or other instructions.

**Example content**:
```markdown
## Tool Selection Rules

When a user asks to find a doctor:
1. Use search_directory() with list_name="doctors"
2. Use filters parameter for specialty/department/gender
3. Use tag parameter for language searches

When a user asks about hospital services:
1. Use vector_search() to search website content
2. Return specific information with citations
```

**Configuration**:
```yaml
prompting:
  modules:
    enabled: true
    selected:
      - tool_selection_hints  # This module goes at the top
```

---

## Component 2: Base System Prompt

**File**: `backend/config/agent_configs/{account}/{instance}/system_prompt.md`

**Purpose**: Agent's core persona, role, and instructions

**When included**: Always (required)

**Position**: After critical rules

**Example file**: `backend/config/agent_configs/windriver/windriver_info_chat1/system_prompt.md`

**Content includes**:
- Agent persona and approach
- Primary role and responsibilities
- Communication guidelines
- Available services (specific to the organization)
- Contact information and important numbers

**Example excerpt**:
```markdown
You are an AI assistant for Wind River Hospital, a comprehensive 
healthcare facility providing exceptional medical care to the 
community since 1895.

## Your Persona
You are a warm, compassionate healthcare guide who genuinely cares 
about making people's lives easier during what can be stressful times.

## Your Role
- Help users find doctors and specialists based on their needs
- Provide information about medical services, departments, and facilities
- Answer questions about visiting hours, locations, and contact information
```

---

## Component 3: Directory Documentation (Auto-Generated)

**Generated from**:
- Agent config: `tools.directory.accessible_lists`
- Database: List metadata, entry counts
- Schema files: `backend/config/directory_schemas/*.yaml`

**Purpose**: Specific documentation for each enabled directory with searchable fields, available tags, and example queries

**When included**: Only if `tools.directory.enabled: true` AND `account_id` is provided

**Position**: After base system prompt

**Generation function**: `generate_directory_tool_docs()` in `backend/app/agents/tools/prompt_generator.py`

**Example generated content**:
```markdown
---

## Available Directory: doctors

This agent has access to search the **doctors** directory containing 
medical staff profiles.

**Directory**: doctors
**Total entries**: 42 doctors
**Search mode**: Full-text search with ranking (fts)

### Searchable Fields
- `name` (text) - Doctor's full name
- `specialty` (text) - Medical specialty (Cardiology, Neurology, etc.)
- `department` (text) - Hospital department
- `gender` (text) - Gender (male, female)
- `phone` (text) - Contact phone number
- `email` (text) - Contact email

### Available Language Tags
English, Spanish, Hindi, Mandarin, Arabic, Russian, Portuguese, French

### Example Search Patterns

Find cardiologist:
search_directory(list_name="doctors", filters={"specialty": "Cardiology"})

Find Spanish-speaking doctors:
search_directory(list_name="doctors", tag="Spanish")

Find female endocrinologist:
search_directory(list_name="doctors", filters={"specialty": "Endocrinology", "gender": "female"})

Find specific doctor:
search_directory(list_name="doctors", query="Dr. Smith")
```

**What makes this dynamic**:
- Entry counts are live from the database
- Available tags reflect actual tags in use
- Searchable fields come from the schema YAML
- Generated fresh each time the agent is created

---

## Component 4: Other Prompt Modules (Optional)

**Files**: Additional modules from `backend/config/prompt_modules/system/`

**Purpose**: Optional enhancements like few-shot examples, chain-of-thought guidance, structured output templates

**When included**: If `prompting.modules.enabled: true` and modules are selected in config

**Position**: After directory documentation

**Note**: `tool_selection_hints` is excluded here because it's already at the top

**Available modules** (examples):
- `tool_calling_few_shot.md` - Example tool calls
- `tool_calling_cot.md` - Chain-of-thought reasoning
- `tool_calling_structured.md` - Structured output formats

**Configuration**:
```yaml
prompting:
  modules:
    enabled: true
    selected:
      - tool_selection_hints      # Goes to top (position 1)
      - tool_calling_few_shot      # Goes to position 4
      - tool_calling_cot            # Goes to position 4
```

---

## Complete Assembly Example

For the Wind River Hospital agent, the assembled prompt looks like:

```markdown
# [Position 1] Critical Rules
## Tool Selection Rules
[Content from tool_selection_hints.md]

---

# [Position 2] Base System Prompt
You are an AI assistant for Wind River Hospital...

## Your Persona
You are a warm, compassionate healthcare guide...

## Your Role
- Help users find doctors and specialists
- Provide information about medical services
...

## Wind River Hospital Services
- Emergency Services - 24/7 Level II Trauma Center
- Cardiology - Comprehensive heart and vascular care
...

---

# [Position 3] Auto-Generated Directory Documentation
## Available Directory: doctors

This agent has access to search the **doctors** directory...

**Total entries**: 42 doctors
**Search mode**: fts

### Searchable Fields
- name (text)
- specialty (text)
...

### Available Language Tags
English, Spanish, Hindi, Mandarin...

---

# [Position 4] Additional Modules (if enabled)
[Content from other selected prompt modules]
```

**Total size**: Typically 5,000-15,000 characters depending on:
- Number of enabled directories
- Number of entries in each directory
- Number of additional modules
- Length of base system prompt

---

## What Gets Sent with Each LLM Request

The system prompt is **sent with EVERY request** to the LLM, along with conversation history and tool definitions.

### Complete Request Structure

```json
{
  "model": "openai/gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "[FULL ASSEMBLED SYSTEM PROMPT - all 4 components]"
    },
    {
      "role": "user",
      "content": "Hello, I need to find a cardiologist"
    },
    {
      "role": "assistant", 
      "content": "I'll search our doctors directory for you..."
    },
    {
      "role": "user",
      "content": "Do you have Spanish-speaking doctors?"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 2000,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "search_directory",
        "description": "Search directories for entries...",
        "parameters": {
          "type": "object",
          "properties": {
            "list_name": {"type": "string"},
            "query": {"type": "string"},
            "filters": {"type": "object"},
            "tag": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "vector_search",
        "description": "Search website content...",
        "parameters": {...}
      }
    }
  ]
}
```

### Components Sent Per Request

| Component | Included | Notes |
|-----------|----------|-------|
| **System Prompt** | ✅ Every request | Full assembled prompt (all 4 components) |
| **Conversation History** | ✅ Every request | All previous user/assistant messages from session |
| **Current Message** | ✅ Every request | User's current question |
| **Tool Definitions** | ✅ Every request | Function signatures for all enabled tools |
| **Model Settings** | ✅ Every request | Temperature, max_tokens, etc. |

### Cost Implications

**System prompt tokens are charged on EVERY request**:
- Longer system prompts = more prompt tokens per request
- Longer conversation history = more prompt tokens per request
- More enabled directories = longer auto-generated docs = higher base cost

**Example token costs** (approximate):
- Base system prompt: ~1,000 tokens
- Directory docs (2 directories): ~2,000 tokens
- 10-message conversation history: ~500 tokens
- Current message: ~20 tokens
- **Total prompt tokens**: ~3,520 tokens per request

**Cost per request** (using GPT-4o-mini at $0.15/1M tokens):
- Prompt: 3,520 tokens × $0.15 / 1M = $0.000528
- Completion: ~200 tokens × $0.60 / 1M = $0.00012
- **Total**: ~$0.00065 per request

**Over 1,000 requests per day**: ~$0.65/day = ~$20/month just for this agent

---

## Implementation Details

### Where Assembly Happens

**File**: `backend/app/agents/simple_chat.py`  
**Function**: `create_simple_chat_agent()`  
**Lines**: 205-325

### Assembly Code Flow

```python
# Phase 1: Load critical rules (top of prompt)
critical_rules = ""
if prompting_config.get('enabled', False):
    tool_selection_content = load_prompt_module("tool_selection_hints", account_slug)
    if tool_selection_content:
        critical_rules = tool_selection_content + "\n\n---\n\n"

# Phase 2: Load base system prompt
base_system_prompt = instance_config['system_prompt']

# Phase 3: Construct initial prompt
system_prompt = critical_rules + base_system_prompt

# Phase 4: Add directory documentation
if directory_config.get("enabled", False) and account_id is not None:
    directory_result = await generate_directory_tool_docs(
        agent_config=instance_config,
        account_id=account_id,
        db_session=db_session
    )
    directory_docs = directory_result.full_text
    system_prompt = system_prompt + "\n\n" + directory_docs

# Phase 5: Add other prompt modules
if prompting_config.get('enabled', False):
    other_modules = [m for m in selected_modules if m != 'tool_selection_hints']
    for module_name in other_modules:
        module_content = load_prompt_module(module_name, account_slug)
        if module_content:
            system_prompt = system_prompt + "\n\n---\n\n" + module_content
```

### Prompt Breakdown Tracking

For debugging and admin visibility, the system tracks each component:

```python
prompt_breakdown = {
    "critical_rules": {
        "source": "tool_selection_hints.md",
        "length": len(critical_rules),
        "position": 1
    },
    "base_prompt": {
        "source": "system_prompt.md",
        "length": len(base_system_prompt),
        "position": 2
    },
    "directory_docs": {
        "source": "auto-generated",
        "directories": ["doctors", "services"],
        "length": len(directory_docs),
        "position": 3
    },
    "modules": {
        "loaded": ["tool_calling_few_shot"],
        "length": len(modules_content),
        "position": 4
    },
    "total_length": len(system_prompt)
}
```

This breakdown is stored in the `llm_requests` table for analysis.

---

## Caching and Performance

### System Prompt is NOT Cached

**IMPORTANT**: The system prompt is assembled **fresh for every single request**. There is no caching at the session level or agent level.

#### Why No Caching?

From the codebase comments:
> "Global caching disabled for production reliability. Configuration changes take effect immediately after server restart without requiring session cookie clearing or cache invalidation."

**Design Decision**:
```python
async def get_chat_agent():
    """Create a fresh chat agent instance."""
    # Always create fresh agent to pick up latest configuration
    agent = await create_simple_chat_agent()
    return agent
```

#### What Happens on Every Request

1. **Load prompt files** - 4-5 file reads (`tool_selection_hints.md`, `system_prompt.md`, modules)
2. **Query database** - Live query for directory metadata (entry counts, available tags)
3. **Parse schema files** - Load YAML schemas for enabled directories
4. **Assemble prompt** - Concatenate all components in correct order
5. **Create agent** - New Pydantic AI Agent instance with assembled prompt
6. **Process request** - Execute user query
7. **Discard agent** - Agent not reused for next request

#### Performance Impact

| Component | Time per Request | Notes |
|-----------|------------------|-------|
| **Load prompt files** | ~5-10ms | File I/O for markdown files |
| **Database query** | ~10-50ms | Directory list metadata + entry counts |
| **Parse schema YAML** | ~5-10ms | Load directory schemas |
| **String assembly** | ~1ms | Concatenate components |
| **Total Assembly Overhead** | **~20-70ms** | Per request |
| **LLM Request Time** | ~500-3000ms | For comparison |
| **Assembly % of Total** | **~1-5%** | Minimal overhead |

#### Benefits of Fresh Assembly

✅ **Configuration changes immediate** - Edit `system_prompt.md`, restart server, changes take effect  
✅ **No cache invalidation complexity** - No need to track when to clear cache  
✅ **Always current directory data** - Entry counts and tags are always live  
✅ **Simpler debugging** - No "clear cache and try again" troubleshooting  
✅ **Memory efficient** - No large prompt cache in memory  
✅ **Multi-tenant safe** - Each account/agent gets fresh assembly

#### Dynamic Components Stay Fresh

The **directory documentation** (Position 3) benefits most from fresh assembly:

```markdown
## Available Directory: doctors
**Total entries**: 42 doctors  ← Queried from database LIVE
**Available Language Tags**: English, Spanish, Hindi...  ← From actual entries
```

If cached, these could become stale when:
- New entries added to directories
- Entries removed or updated
- Language tags change
- Schema fields modified

#### When Changes Take Effect

| Change Type | When It Takes Effect |
|-------------|---------------------|
| **Edit system_prompt.md** | After server restart |
| **Add/edit prompt module** | After server restart |
| **Change agent config.yaml** | After server restart |
| **Add directory entry** | Immediately (live query) |
| **Update directory schema** | After server restart |
| **Enable/disable tools** | After server restart |

**Note**: "After server restart" means you need to restart the uvicorn backend server. Frontend-only changes (widget, pages) don't require backend restart.

#### Could Caching Be Added?

Yes, with these considerations:

**Potential Caching Strategy**:
```python
_agent_cache: Dict[str, tuple[Agent, datetime]] = {}
_cache_ttl = 300  # 5 minutes

async def get_chat_agent_cached(instance_config, account_id):
    cache_key = f"{account_id}:{instance_config['instance_name']}"
    
    if cache_key in _agent_cache:
        agent, cached_at = _agent_cache[cache_key]
        if (datetime.now(UTC) - cached_at).seconds < _cache_ttl:
            return agent  # Use cached
    
    # Cache miss or expired - create fresh
    agent = await create_simple_chat_agent(instance_config, account_id)
    _agent_cache[cache_key] = (agent, datetime.now(UTC))
    return agent
```

**When to Consider Caching**:
- Request volume >100 req/sec per agent
- Profiling shows assembly is a bottleneck
- Directory data rarely changes
- Need to implement proper cache invalidation

**Current Recommendation**: No caching needed. The ~20-70ms overhead is minimal compared to LLM request time (~500-3000ms).

---

## Configuration Examples

### Minimal Configuration (No Modules)

```yaml
# backend/config/agent_configs/myaccount/myagent/config.yaml

agent_type: "simple_chat"
account: "myaccount"
instance_name: "myagent"

prompts:
  system_prompt_file: "./system_prompt.md"  # Position 2 only

tools:
  directory:
    enabled: false  # No directory docs (position 3 skipped)
    
prompting:
  modules:
    enabled: false  # No modules (positions 1 & 4 skipped)
```

**Result**: Only base system prompt (position 2)

### Full Configuration (All Components)

```yaml
# backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml

agent_type: "simple_chat"
account: "windriver"
instance_name: "windriver_info_chat1"

prompts:
  system_prompt_file: "./system_prompt.md"  # Position 2

tools:
  directory:
    enabled: true  # Position 3 - auto-generated docs
    accessible_lists:
      - doctors
      - services
    
prompting:
  modules:
    enabled: true
    selected:
      - tool_selection_hints      # Position 1 (top)
      - tool_calling_few_shot      # Position 4
      - tool_calling_cot            # Position 4
```

**Result**: All 4 components assembled

---

## Best Practices

### 1. Keep Base System Prompt Focused

**DO**:
- Define persona and core role
- Provide organization-specific context
- Include contact information and important details

**DON'T**:
- Duplicate tool documentation (auto-generated)
- Include verbose examples (use prompt modules)
- Add field-level search syntax (in directory schemas)

### 2. Use Tool Selection Hints Strategically

**When to enable**:
- Agent has multiple tools (directory + vector search)
- Tools have overlapping use cases
- LLM makes incorrect tool choices

**What to include**:
- Clear decision criteria
- Common user query patterns
- Tool priority rules

### 3. Optimize Directory Schemas

Directory documentation is auto-generated from schemas, so:
- Keep field descriptions concise
- Add helpful examples to schemas
- Document common search patterns

### 4. Monitor Prompt Size

**Track metrics**:
- Total prompt tokens per request
- Cost per conversation
- Context window usage

**Optimize when**:
- Approaching model context limits
- Cost per conversation exceeds budget
- Response latency increases

### 5. Use Prompt Modules Sparingly

Each module adds to every request:
- Start with critical rules only
- Add modules based on observed LLM behavior
- Remove modules that don't improve performance

---

## Debugging System Prompts

### View Assembled Prompt

**Admin UI** (when available):
1. Navigate to session detail view
2. Click "View System Prompt" 
3. See full assembled prompt with component breakdown

**Database Query**:
```sql
SELECT 
    meta->'prompt_breakdown' as breakdown,
    assembled_prompt
FROM llm_requests
WHERE session_id = 'your-session-id'
ORDER BY created_at DESC
LIMIT 1;
```

**Logfire Logs**:
```python
logfire.info(
    'agent.system_prompt.enhanced',
    original_length=5000,
    directory_docs_length=3000,
    final_length=8000
)
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| LLM ignores directory tool | Tool selection hints not at top | Enable `tool_selection_hints` module |
| LLM uses wrong search syntax | Directory docs not generated | Ensure `account_id` provided to agent creation |
| Excessive cost per request | Too many directories enabled | Limit `accessible_lists` to needed directories only |
| Response quality degraded | Prompt too long, pushing out context | Remove unnecessary modules, reduce directory count |
| Directory search returns no results | Schema fields don't match database | Regenerate directory docs after schema changes |

---

## Related Documentation

- [Agent Configuration Guide](./agent-configuration-guide.md) - Complete agent config reference
- [Adding/Modifying Directory Schemas](./adding-modifying-directory-schemas.md) - Schema design and validation
- [Loading Directories](./loading-directories.md) - CSV import and data loading
- [Architecture: Agent and Tool Design](../architecture/agent-and-tool-design.md) - Technical architecture
- [Architecture: Simple Chat Agent Design](../architecture/simple-chat-agent-design.md) - Implementation details

---

**Last Updated**: December 4, 2025  
**Maintainer**: Architecture Team  
**Feedback**: Submit issues or suggestions via project management team

