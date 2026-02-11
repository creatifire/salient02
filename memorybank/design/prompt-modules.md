# Prompt Modules System - Dynamic Prompt Construction

**Last Updated**: February 1, 2025  
**Status**: Implemented (Phase 4A)  
**Reference**: `memorybank/project-management/0025-dynamic-prompting-plan.md`

---

## Overview

The Prompt Modules system enables configurable, modular prompt enhancements that can be dynamically loaded and positioned within the agent's system prompt. This document describes the prompt construction order, file sources, and the critical "nuclear option" implementation that solves token position bias.

---

## Problem Statement

Initial implementation loaded prompt modules **AFTER** all other prompt components, resulting in:

- **Token Position Bias**: LLMs give more weight to earlier tokens in the prompt
- **Late Guidance**: Critical tool selection rules appeared at position ~12,000 chars
- **Tool Descriptions First**: Pydantic AI's automatic tool descriptions appeared before our rules
- **Decision Made Early**: LLM decided on tools before reading our guidance

**Result**: LLM consistently chose `vector_search` for phone queries despite explicit "YOU MUST use search_directory" instructions in 6,088 chars of guidance.

---

## Solution: Nuclear Option (Option A)

**Strategy**: Inject critical tool selection rules at the **TOP** of the prompt, before everything else.

**Key Insight**: Token position bias can work **FOR** us if we put critical rules first.

---

## Prompt Construction Order

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ FINAL PROMPT SENT TO LLM (~15,000 chars)                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 1. CRITICAL TOOL SELECTION RULES (~4000 chars)                        │   │
│ │    "YOU MUST use search_directory for phone..."                       │   │
│ │    "NEVER use vector_search - IT WILL FAIL"                           │   │
│ │    Decision flowchart, ✅ CORRECT vs ❌ WRONG examples                │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│   📁 SOURCE: backend/config/prompt_modules/system/                          │
│              tool_selection_hints.md (167 lines)                             │
│   🔧 LOADED: simple_chat.py line 194 (load_prompt_module)                   │
│   📍 POSITION: Prepended at line 224 (FIRST in prompt)                      │
│                                                                               │
│ ─────────────────────────────────────────────────────────────────            │
│                                                                               │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 2. BASE SYSTEM PROMPT (~3000 chars)                                   │   │
│ │    "You are Wyckoff Hospital Assistant..."                            │   │
│ │    Personality, role, guidelines, tone, constraints                   │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│   📁 SOURCE: backend/config/agent_configs/wyckoff/wyckoff_info_chat1/       │
│              system_prompt.md                                                │
│   🔧 LOADED: simple_chat.py line 207 (from instance_config)                 │
│   📍 POSITION: Added at line 224 (after critical rules)                     │
│                                                                               │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 3. DIRECTORY TOOL DOCUMENTATION (~6000 chars)                         │   │
│ │    "## Directory Tool"                                                │   │
│ │    "You have access to multiple directories..."                       │   │
│ │    "Directory: doctors (24 medical_professionals)"                    │   │
│ │    "Directory: phone_directory (10 departments)"                      │   │
│ │    Schema-driven guidance, synonym mappings, examples                 │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│   📁 SOURCE: Auto-generated from:                                            │
│              - backend/config/directory_schemas/medical_professional.yaml    │
│              - backend/config/directory_schemas/phone_directory.yaml         │
│              - Database (entry counts, metadata)                             │
│   🔧 LOADED: simple_chat.py line 211 (generate_directory_tool_docs)         │
│   📍 POSITION: Appended at line 233 (after base prompt)                     │
│                                                                               │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 4. TOOL DESCRIPTIONS (Pydantic AI automatic)                          │   │
│ │    search_directory(                                                  │   │
│ │        list_name: str,                                                │   │
│ │        filters: Optional[Dict[str, str]],                             │   │
│ │        ...                                                            │   │
│ │    )                                                                  │   │
│ │    vector_search(query: str, threshold: float, ...)                  │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│   📁 SOURCE: Generated by Pydantic AI from:                                  │
│              - backend/app/agents/tools/directory_tools.py                   │
│              - backend/app/agents/tools/vector_tools.py                      │
│              - backend/app/agents/tools/toolsets.py (FunctionToolset)        │
│   🔧 LOADED: Automatically when Agent() created (line ~305)                  │
│   📍 POSITION: Injected by Pydantic AI (after system_prompt)                │
│                                                                               │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 5. OTHER MODULES (~2000 chars)                                        │   │
│ │    "## Directory Selection Hints"                                     │   │
│ │    "When query mentions department + phone..."                        │   │
│ │    "Use phone_directory for department contacts"                      │   │
│ │    "Use doctors for medical professionals"                            │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│   📁 SOURCE: backend/config/prompt_modules/system/                          │
│              directory_selection_hints.md (33 lines)                         │
│   🔧 LOADED: simple_chat.py line 277 (load_prompt_module, loop)             │
│   📍 POSITION: Appended at line 283 (LAST in prompt)                        │
│   📝 NOTE: tool_selection_hints skipped (already at top, line 272)          │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## File Locations

| Component | File Path | Lines | Loaded By | Position |
|-----------|-----------|-------|-----------|----------|
| **Critical Rules** | `backend/config/prompt_modules/system/`<br>`tool_selection_hints.md` | 167 | `simple_chat.py:194` | **TOP** (1st) |
| **Base Prompt** | `backend/config/agent_configs/wyckoff/`<br>`wyckoff_info_chat1/system_prompt.md` | ~200 | `simple_chat.py:207` | 2nd |
| **Directory Docs** | Auto-generated from:<br>`backend/config/directory_schemas/*.yaml` | N/A | `simple_chat.py:211`<br>`prompt_generator.py` | 3rd |
| **Tool Descriptions** | Generated from:<br>`backend/app/agents/tools/*.py` | N/A | Pydantic AI<br>(automatic) | 4th |
| **Other Modules** | `backend/config/prompt_modules/system/`<br>`directory_selection_hints.md` | 33 | `simple_chat.py:277` | 5th (LAST) |

---

## Code Implementation

### Module Loading Infrastructure

**File**: `backend/app/agents/tools/prompt_modules.py`

```python
def load_prompt_module(module_name: str, account_slug: Optional[str] = None) -> Optional[str]:
    """
    Load a prompt module from markdown file.
    
    Cascade:
    1. Try account-level: backend/config/prompt_modules/accounts/{account_slug}/{module_name}.md
    2. Fall back to system-level: backend/config/prompt_modules/system/{module_name}.md
    """
    # Account-level override
    if account_slug:
        account_path = ACCOUNT_MODULES_DIR / account_slug / f"{module_name}.md"
        if account_path.exists():
            return account_path.read_text()
    
    # System-level default
    system_path = SYSTEM_MODULES_DIR / f"{module_name}.md"
    if system_path.exists():
        return system_path.read_text()
    
    return None
```

### Prompt Construction in simple_chat.py

**File**: `backend/app/agents/simple_chat.py`

```python
async def create_simple_chat_agent(instance_config, account_id):
    # ============================================================
    # STEP 1: Load CRITICAL rules FIRST (line 182-202)
    # ============================================================
    from .tools.prompt_modules import load_prompt_module
    
    account_slug = instance_config.get("account") if instance_config else None
    
    critical_rules = ""
    prompting_config = (instance_config or {}).get('prompting', {}).get('modules', {})
    if prompting_config.get('enabled', False):
        tool_selection_content = load_prompt_module("tool_selection_hints", account_slug)
        if tool_selection_content:
            critical_rules = tool_selection_content + "\n\n---\n\n"
            logfire.info('agent.critical_rules.injected', 
                        module='tool_selection_hints',
                        position='top_of_prompt',
                        length=len(tool_selection_content))
    
    # ============================================================
    # STEP 2: Load BASE prompt (line 204-221)
    # ============================================================
    if instance_config and 'system_prompt' in instance_config:
        base_system_prompt = instance_config['system_prompt']
    else:
        agent_config = await get_agent_config("simple_chat")
        base_system_prompt = agent_config.system_prompt
    
    # ============================================================
    # STEP 3: PREPEND critical rules to base (line 224)
    # ============================================================
    system_prompt = critical_rules + base_system_prompt  # Rules go FIRST!
    
    # ============================================================
    # STEP 4: Append DIRECTORY docs (line 227-233)
    # ============================================================
    directory_config = (instance_config or {}).get("tools", {}).get("directory", {})
    if directory_config.get("enabled", False) and account_id:
        from .tools.prompt_generator import generate_directory_tool_docs
        
        directory_docs = await generate_directory_tool_docs(
            agent_config=instance_config or {},
            account_id=account_id,
            db_session=db_session
        )
        
        if directory_docs:
            system_prompt = system_prompt + "\n\n" + directory_docs
    
    # ============================================================
    # STEP 5: Append OTHER modules (line 265-291)
    # ============================================================
    if prompting_config.get('enabled', False):
        selected_modules = prompting_config.get('selected', [])
        # Skip tool_selection_hints (already loaded at top)
        other_modules = [m for m in selected_modules if m != 'tool_selection_hints']
        
        if other_modules:
            other_module_contents = []
            for module_name in other_modules:
                module_content = load_prompt_module(module_name, account_slug)
                if module_content:
                    other_module_contents.append(module_content)
            
            if other_module_contents:
                combined = "\n\n---\n\n".join(other_module_contents)
                system_prompt = system_prompt + "\n\n" + combined
    
    # ============================================================
    # STEP 6: Create Agent (Pydantic AI adds tool descriptions)
    # ============================================================
    toolsets = get_enabled_toolsets(instance_config or {})
    
    agent = Agent(
        model_name,
        deps_type=SessionDependencies,
        system_prompt=system_prompt,  # Complete prompt with critical rules at top
        toolsets=toolsets  # Pydantic AI will add tool descriptions here
    )
    
    return agent
```

---

## Why This Works

### Token Position Bias

LLMs exhibit **token position bias**: earlier tokens have more influence on the model's behavior than later tokens.

**Evidence**:
- First 1000 tokens: **Highest weight** - model "internalizes" these as core rules
- Middle tokens: Moderate weight - context and details
- Last 1000 tokens: **Lower weight** - supplementary information

**Our Strategy**:
1. Put **CRITICAL RULES** in first ~4,000 chars (tokens 1-1000)
2. LLM reads "YOU MUST use search_directory for phone" **BEFORE** seeing tools
3. By the time it sees Pydantic AI's tool descriptions, rules are internalized
4. Tool descriptions become implementation details, not decision factors

### Before vs After

**BEFORE (Failed)**:
```
Position 1-3000:   Base prompt (personality, role)
Position 3000-9000: Directory docs (search guidance)
Position 9000-12000: Tool descriptions (Pydantic AI)
Position 12000-15000: Critical rules ← TOO LATE! LLM already decided
```

**AFTER (Fixed)**:
```
Position 1-4000:   CRITICAL RULES ← LLM reads THIS first!
Position 4000-7000: Base prompt
Position 7000-13000: Directory docs
Position 13000-15000: Tool descriptions (Pydantic AI)
Position 15000-17000: Other modules
```

---

## Configuration

### Enable Prompt Modules

**File**: `backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml`

```yaml
prompting:
  modules:
    enabled: true
    selected:
      - tool_selection_hints       # Loaded at TOP (Layer 1: tool selection)
      - directory_selection_hints  # Loaded at END (Layer 2: directory selection)
```

### Module Files

**System-level modules** (apply to all agents unless overridden):
```
backend/config/prompt_modules/system/
├── tool_selection_hints.md         # Layer 1: Choose tool (directory vs vector)
└── directory_selection_hints.md    # Layer 2: Choose directory (doctors vs phone_directory)
```

**Account-level modules** (override system modules):
```
backend/config/prompt_modules/accounts/
└── wyckoff/
    ├── tool_selection_hints.md         # Optional: Wyckoff-specific overrides
    └── directory_selection_hints.md    # Optional: Wyckoff-specific overrides
```

---

## Configuration Cascade Rules

All configuration files follow a **3-level cascade** pattern: **Agent Instance → Account → System → None**.

### Standard Cascade Order

For any configuration file (prompt modules, system prompts, profile schemas, etc.):

1. **Agent Instance** - Most specific, highest priority
2. **Account** - Account-wide defaults
3. **System** - Global defaults
4. **None** - Return None if not found at any level

### File Path Resolution

#### Prompt Modules (e.g., `tool_selection_hints.md`)

```
1. backend/config/agent_configs/{account}/{instance}/tool_selection_hints.md
   ↓ (if not found)
2. backend/config/prompt_modules/accounts/{account}/tool_selection_hints.md
   ↓ (if not found)
3. backend/config/prompt_modules/system/tool_selection_hints.md
   ↓ (if not found)
4. Return None
```

#### System Prompt (`system_prompt.md`)

```
1. backend/config/agent_configs/{account}/{instance}/system_prompt.md
   ↓ (if not found)
2. backend/config/prompt_modules/accounts/{account}/system_prompt.md
   ↓ (if not found)
3. backend/config/prompt_modules/system/system_prompt.md
   ↓ (if not found)
4. Return None
```

#### Profile Schema (`profile.yaml`)

```
1. backend/config/agent_configs/{account}/{instance}/profile.yaml
   ↓ (if not found)
2. backend/config/prompt_modules/accounts/{account}/profile.yaml
   ↓ (if not found)
3. backend/config/prompt_modules/system/profile.yaml
   ↓ (if not found)
4. Return None
```

#### Email Summarization Prompt (`email_summarization_prompt.md`)

```
1. backend/config/agent_configs/{account}/{instance}/email_summarization_prompt.md
   ↓ (if not found)
2. backend/config/prompt_modules/accounts/{account}/email_summarization_prompt.md
   ↓ (if not found)
3. backend/config/prompt_modules/system/email_summarization_prompt.md
   ↓ (if not found)
4. Return None (use default in code)
```

### Current Implementation Status

**⚠️ WARNING**: As of December 5, 2025, the cascade implementation is **inconsistent** across different file types. See **BUG-0017-012** for details.

**Current Status**:
- ❌ **Prompt Modules**: 2-level cascade (account → system), **MISSING** instance level
- ❌ **System Prompt**: 1-level (instance only), **MISSING** account/system fallback
- ❌ **Profile Schema**: 2-level (instance → system), **SKIPS** account level

**Target State** (when BUG-0017-012 is fixed):
- ✅ **All files**: 3-level cascade (instance → account → system → none)

### Usage Examples

**Example 1**: Wyckoff-specific tool selection rules

```
File: backend/config/prompt_modules/accounts/wyckoff/tool_selection_hints.md
Result: All Wyckoff agents use this instead of system default
```

**Example 2**: Wind River instance-specific system prompt

```
File: backend/config/agent_configs/windriver/windriver_info_chat1/system_prompt.md
Result: This specific instance uses custom prompt, others fall back to account/system
```

**Example 3**: Global profile schema

```
File: backend/config/prompt_modules/system/profile.yaml
Result: All agents use this unless overridden at account or instance level
```

### Implementation Reference

**Current Implementation**: `backend/app/agents/tools/prompt_modules.py`

```python
def load_prompt_module(module_name: str, account_slug: Optional[str] = None) -> Optional[str]:
    """
    Load a prompt module from markdown file.
    
    CASCADE (current - 2-level):
    1. Try account-level: backend/config/prompt_modules/accounts/{account_slug}/{module_name}.md
    2. Fall back to system-level: backend/config/prompt_modules/system/{module_name}.md
    
    TODO (BUG-0017-012): Add instance-level as first priority
    """
```

**Target Implementation** (when BUG-0017-012 is fixed):

```python
def load_prompt_module(
    module_name: str,
    account_slug: Optional[str] = None,
    instance_name: Optional[str] = None
) -> Optional[str]:
    """
    Load a prompt module from markdown file with full cascade.
    
    CASCADE (3-level):
    1. Try instance-level: backend/config/agent_configs/{account}/{instance}/{module_name}.md
    2. Try account-level: backend/config/prompt_modules/accounts/{account}/{module_name}.md
    3. Fall back to system-level: backend/config/prompt_modules/system/{module_name}.md
    4. Return None if not found at any level
    """
```

---

## Monitoring

### Logfire Events

Track prompt construction with Logfire:

**Critical Rules Injection**:
```python
logfire.info('agent.critical_rules.injected',
            module='tool_selection_hints',
            position='top_of_prompt',
            length=4123)
```

**Module Loading**:
```python
logfire.info('agent.prompt_modules.loaded',
            module_count=1,
            modules=['directory_selection_hints'],
            content_length=2088,
            final_prompt_length=15410,
            note='tool_selection_hints loaded at top')
```

### Verification Queries

To verify the system is working:

**Logfire Query** (check critical rules injection):
```sql
SELECT 
    start_timestamp,
    message,
    attributes->'module' as module,
    attributes->'position' as position,
    attributes->'length' as length
FROM records 
WHERE span_name = 'agent.critical_rules.injected'
ORDER BY start_timestamp DESC
LIMIT 5
```

**Expected Result**: Should see `module='tool_selection_hints'` with `position='top_of_prompt'`

---

## Design Principles

### Hierarchical Guidance

**Layer 1** (Top of prompt): **Tool Selection**
- Which tool to use: `search_directory` vs `vector_search`
- Loaded FIRST for maximum influence
- Module: `tool_selection_hints.md`

**Layer 2** (End of prompt): **Directory Selection**
- Which directory to search: `doctors` vs `phone_directory`
- Loaded LAST (only applies if Layer 1 chose `search_directory`)
- Module: `directory_selection_hints.md`

### Modularity

**System-level modules**: Generic, reusable across accounts
- Location: `backend/config/prompt_modules/system/`
- Use case: Common patterns that work for all agents

**Account-level modules**: Domain-specific overrides
- Location: `backend/config/prompt_modules/accounts/{account_slug}/`
- Use case: Account-specific rules that override system defaults

### Backward Compatibility

- ✅ Works if modules disabled (`enabled: false`)
- ✅ Works if no modules selected (`selected: []`)
- ✅ Works if modules missing (graceful degradation)
- ✅ Existing agents without module config work unchanged

---

## Future Enhancements

### Phase 5: Modular Prompts (Expanded)

Build on this foundation with:
- Emergency protocols module
- Billing policies module
- HIPAA compliance disclaimers module
- Domain-specific context injection

### Phase 6: MCP Integration

Extend module system to support MCP servers:
- MCP-specific guidance modules
- Dynamic tool loading from MCP servers
- Cross-tool coordination rules

---

## References

- **Design**: `memorybank/design/dynamic-prompting.md`
- **Implementation Plan**: `memorybank/project-management/0025-dynamic-prompting-plan.md`
- **Code**: `backend/app/agents/simple_chat.py` (lines 182-291)
- **Module Infrastructure**: `backend/app/agents/tools/prompt_modules.py`
- **Example Modules**: `backend/config/prompt_modules/system/`

---

## Appendix: Evolution History

### Iteration 1: Polite Guidance (Failed)
- Module content: "Use this tool for..."
- Position: Appended at end
- Result: LLM ignored guidance

### Iteration 2: Commanding Language (Failed)
- Module content: "YOU MUST use this tool..."
- Position: Still appended at end
- Result: LLM still ignored (position bias)

### Iteration 3: Nuclear Option (Success)
- Module content: Commanding language + explicit examples
- Position: **Injected at TOP**
- Result: LLM follows guidance (position bias + strong language)

**Key Lesson**: **Content AND position** both matter. Strong language at the wrong position doesn't work. Polite language at the right position doesn't work. **Both together** = success.

