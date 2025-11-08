<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Dynamic Prompting Architecture

**Problem**: Single static system prompt cannot optimize for diverse request types (directory search vs. billing questions vs. emergency guidance).

**Goal**: Adapt prompt content based on request context to improve response quality without architectural complexity.

---

## Current State

**Static Prompt Loading**:
- Each agent instance loads one system prompt at creation: `{account}/{instance}/system_prompt.md`
- Pydantic AI `Agent(model, system_prompt=...)` accepts string at construction
- Existing dynamic augmentation: `prompt_generator.py` appends directory tool docs

**Location**: `backend/app/agents/simple_chat.py` (lines 150-220)

**Current Behavior (Already Progressive)**:
```python
# 1. Simple agent: Just base prompt
if no directory tools configured:
    prompt = load_base_prompt()  # Just system_prompt.md

# 2. Directory-enhanced agent: Base + directory docs
if directory tools configured:
    prompt = load_base_prompt() + generate_directory_tool_docs()
```

**Limitations** (for complex scenarios):
- Same prompt for all request types (no context modules)
- Cannot prioritize urgent vs. routine queries
- Cannot inject domain-specific knowledge based on context
- Difficult to A/B test prompts for specific scenarios

**What works well**:
- ✅ Simple agents work with zero config (just system_prompt.md)
- ✅ Directory enhancement is automatic (if tools.directory configured)
- ✅ No complexity unless needed

---

## Progressive Enhancement Model (Opt-In Complexity)

**Design Principle**: Agents should work with minimal configuration. Add complexity only when needed.

### Agent Complexity Levels

```
Level 1: Simple Agent (Zero Config)
├─ system_prompt.md only
├─ No tools, no dynamic prompting
└─ Use case: Basic chatbot, FAQ bot

Level 2: Directory-Enhanced Agent (Current - Automatic)
├─ system_prompt.md
├─ + Auto-generated directory tool docs (if tools.directory configured)
└─ Use case: Doctor finder, phone directory lookup

Level 3: Module-Enhanced Agent (Proposed - Opt-In)
├─ system_prompt.md
├─ + Directory tool docs (if configured)
├─ + Context modules (keyword-based selection)
└─ Use case: Hospital assistant with emergency/billing context

Level 4: Fully Dynamic Agent (Future - Opt-In)
├─ system_prompt.md
├─ + Directory tool docs
├─ + Context modules
├─ + Dynamic instructions (message prepending)
└─ Use case: Multi-domain assistant with urgent query handling
```

### Configuration Examples

#### Example 1: Simple Agent (Minimal Config)

**Use case**: Basic chatbot with no special features

```yaml
# agent_configs/default_account/simple_chat1/config.yaml

name: "Simple Chat Bot"
model_settings:
  model: "deepseek/deepseek-chat-v3.1"
  temperature: 0.7

# That's it! Just uses system_prompt.md
```

**Prompt composition**:
```
Final prompt = system_prompt.md
```

---

#### Example 2: Directory-Only Agent (Current Behavior)

**Use case**: Doctor finder with medical directory

```yaml
# agent_configs/wyckoff/doctor_finder/config.yaml

name: "Doctor Finder"
model_settings:
  model: "deepseek/deepseek-chat-v3.1"

tools:
  directory:
    enabled: true
    accessible_lists:
      - "doctors"

# Directory docs auto-generated from schema - no extra config needed!
```

**Prompt composition**:
```
Final prompt = system_prompt.md 
             + auto-generated directory tool docs (from medical_professional.yaml)
```

**No prompting config needed** - directory enhancement is automatic!

---

#### Example 3: Module-Enhanced Agent (Proposed - Opt-In)

**Use case**: Hospital assistant with emergency + billing context

```yaml
# agent_configs/wyckoff/hospital_assistant/config.yaml

name: "Hospital Assistant"
model_settings:
  model: "deepseek/deepseek-chat-v3.1"

tools:
  directory:
    enabled: true
    accessible_lists:
      - "doctors"
      - "phone_directory"

# NEW: Opt-in to dynamic prompting
prompting:
  modules:
    enabled: true  # Must explicitly enable
    selection_mode: "keyword"  # keyword | llm | manual
    available_modules:
      - "medical/emergency_protocols"
      - "administrative/billing_policies"
      - "shared/hipaa_compliance"
    # Or use "auto" to discover all modules in account folder
    # available_modules: "auto"
```

**Prompt composition**:
```
Final prompt = system_prompt.md 
             + auto-generated directory tool docs
             + dynamically selected modules (based on user query keywords)
```

**Module selection** (keyword-based):
- Query: "What's the ER number?" → Loads `medical/emergency_protocols.md`
- Query: "Do you take Medicare?" → Loads `administrative/billing_policies.md`
- Query: "General question" → No modules loaded (just base + directory)

---

#### Example 4: Fully Dynamic Agent (Future - Opt-In)

**Use case**: Multi-domain assistant with urgent query handling

```yaml
# agent_configs/wyckoff/full_assistant/config.yaml

name: "Full Hospital Assistant"
model_settings:
  model: "deepseek/deepseek-chat-v3.1"

tools:
  directory:
    enabled: true
    accessible_lists:
      - "doctors"
      - "phone_directory"

prompting:
  modules:
    enabled: true
    selection_mode: "keyword"
    available_modules: "auto"  # Discover all modules
  
  dynamic_instructions:
    enabled: true  # Opt-in to message prepending
    emergency_detection: true
    followup_context: true
```

**Prompt composition**:
```
Final prompt = system_prompt.md 
             + auto-generated directory tool docs
             + dynamically selected modules
             + [URGENT] prefix (if emergency detected in query)
```

---

### Configuration Design Principles

**1. Zero Config Works**
```yaml
# Minimal agent - just needs model and system_prompt.md
name: "Simple Bot"
model_settings:
  model: "deepseek/deepseek-chat-v3.1"
```

**2. Progressive Enhancement**
```yaml
# Add directory → Auto-generates tool docs (no prompting config)
tools:
  directory:
    enabled: true
    accessible_lists: ["doctors"]
```

**3. Explicit Opt-In for Complexity**
```yaml
# Want modules? Must explicitly enable
prompting:
  modules:
    enabled: true  # ← Explicit opt-in
    available_modules: [...]
```

**4. No Breaking Changes**
- Existing agents without `prompting` config → Continue to work exactly as before
- Adding `prompting.modules.enabled: false` → Same as not having config at all
- Only agents with `prompting.modules.enabled: true` → Use dynamic modules

**5. Sensible Defaults**
```yaml
# Minimal module config
prompting:
  modules:
    enabled: true
    # Defaults:
    # - selection_mode: "keyword" (fast, deterministic)
    # - available_modules: "auto" (discover from account folder)
    # - token_budget: 2000 (total prompt size limit)
```

---

### Implementation: Backward Compatible

**In `prompt_generator.py`**:

```python
async def generate_full_prompt(
    agent_config: dict,
    account_id: UUID,
    db_session: AsyncSession,
    user_query: Optional[str] = None  # New optional param
) -> str:
    """Generate complete prompt with optional dynamic modules."""
    
    # 1. Always load base prompt
    base = load_base_prompt(agent_config)
    
    # 2. Auto-generate directory docs if tools configured
    directory_docs = ""
    if agent_config.get("tools", {}).get("directory", {}).get("enabled"):
        directory_docs = await generate_directory_tool_docs(
            agent_config, account_id, db_session
        )
    
    # 3. Optionally load context modules (NEW - opt-in only)
    module_content = ""
    prompting_config = agent_config.get("prompting", {})
    modules_config = prompting_config.get("modules", {})
    
    if modules_config.get("enabled") and user_query:  # Must opt-in + have query
        selection_mode = modules_config.get("selection_mode", "keyword")
        available_modules = modules_config.get("available_modules", [])
        
        selected = select_modules(user_query, available_modules, selection_mode)
        module_content = load_and_combine_modules(selected)
    
    # 4. Compose final prompt
    parts = [base]
    if directory_docs:
        parts.append(directory_docs)
    if module_content:
        parts.append(module_content)
    
    return "\n\n".join(parts)
```

**Agent creation code** (backward compatible):

```python
# OLD: Works without user_query (existing behavior)
prompt = await generate_full_prompt(agent_config, account_id, db_session)

# NEW: Optionally pass user_query for dynamic modules
prompt = await generate_full_prompt(agent_config, account_id, db_session, user_query)
```

**Key**: If `user_query` not provided or modules not enabled → Same behavior as before!

---

### Summary: How to Enable/Disable Dynamic Prompting

| Agent Type | Configuration Required | Behavior |
|------------|------------------------|----------|
| **Simple** | None (just model + system_prompt.md) | Base prompt only |
| **Directory** | `tools.directory.enabled: true` | Base + auto-generated directory docs |
| **Module-Enhanced** | `prompting.modules.enabled: true` | Base + directory + context modules |
| **Fully Dynamic** | `prompting.modules.enabled: true`<br>`prompting.dynamic_instructions.enabled: true` | Base + directory + modules + message prepending |

**To disable dynamic prompting**:
- **Option 1**: Don't add `prompting` config (existing behavior)
- **Option 2**: Add `prompting.modules.enabled: false` (explicit)
- **Option 3**: Remove `prompting` section entirely

**To enable directory enhancement only** (current behavior):
```yaml
tools:
  directory:
    enabled: true
    accessible_lists: ["doctors"]
# No prompting config = directory auto-enhancement only
```

**To enable dynamic modules**:
```yaml
tools:
  directory:
    enabled: true
    accessible_lists: ["doctors", "phone_directory"]

prompting:
  modules:
    enabled: true  # ← Explicit opt-in
    available_modules: ["medical/emergency_protocols"]
```

**Progressive enhancement is automatic**:
- Add directories → Directory docs auto-generated
- Add modules config → Modules loaded dynamically
- No config → Simple agent (no complexity)

---

## Architectural Approach: Modular Prompt Composition

**Why This Approach**: Balances specialization with simplicity. No agent recreation needed (Pydantic AI compatible), no extra LLM calls (low latency), and progressive enhancement means complexity is opt-in.

**Alternative approaches considered**: [Prompt Routing, Multi-Agent, Message Prepending](./dynamic-prompting-alternatives.md) - documented separately for reference.

---

### Modular Prompt Composition

**Mechanism**: Assemble prompt from reusable modules based on request context

**Structure** (Hybrid: System + Account Level):
```
backend/config/
  prompt_modules/                      # SYSTEM-LEVEL (shared across all accounts)
    ├── medical/
    │   ├── clinical_disclaimers.md    # Standard medical disclaimers
    │   └── symptom_guidance.md        # General symptom guidance
    ├── administrative/
    │   └── insurance_info.md          # Generic insurance information
    └── shared/
        ├── hipaa_compliance.md        # Federal law (same for all)
        └── tone_guidelines.md         # General best practices
  
  agent_configs/{account}/
    modules/                           # ACCOUNT-LEVEL (overrides system)
      ├── medical/
      │   └── emergency_protocols.md   # Account-specific (Wyckoff ER #)
      └── administrative/
          ├── billing_policies.md      # Account-specific insurance
          └── appointment_scheduling.md # Account hours/process

**Resolution**: Account modules override system modules (account-first lookup)
```

**Module Resolution Logic** (Account → System):
```python
def find_module(module_path: str, account_slug: str) -> Path:
    """
    Find module with account-first resolution (overrides).
    
    Resolution order:
    1. Account-specific module (highest priority)
    2. System-level module (fallback)
    3. Not found (raise error)
    """
    # 1. Check account-specific first
    account_module = Path(f"agent_configs/{account_slug}/modules/{module_path}")
    if account_module.exists():
        return account_module  # Account override
    
    # 2. Fall back to system-level
    system_module = Path(f"prompt_modules/{module_path}")
    if system_module.exists():
        return system_module  # System default
    
    # 3. Not found
    raise ModuleNotFoundError(f"Module not found: {module_path}")

# Example usage:
# Wyckoff: find_module("medical/emergency_protocols.md", "wyckoff")
# → Returns: agent_configs/wyckoff/modules/medical/emergency_protocols.md (account-specific ER #)
#
# Wyckoff: find_module("shared/hipaa_compliance.md", "wyckoff")
# → Returns: prompt_modules/shared/hipaa_compliance.md (system-level, same for all)
```

**Module Selection Logic** (keyword-based, no LLM call):
```python
def select_modules(query: str, agent_config: dict) -> List[str]:
    """Select which modules to load based on query keywords."""
    modules = []
    
    # Billing context → Account-specific or system fallback
    if any(word in query.lower() for word in ["billing", "insurance", "payment"]):
        modules.append("administrative/billing_policies.md")
    
    # Emergency context → Account-specific (ER numbers vary!)
    if any(word in query.lower() for word in ["emergency", "urgent", "er", "911"]):
        modules.append("medical/emergency_protocols.md")
    
    # Medical symptoms → System-level (standard disclaimers)
    if any(word in query.lower() for word in ["symptom", "pain", "sick", "hurt"]):
        modules.append("medical/clinical_disclaimers.md")
    
    # Compliance → System-level (federal law)
    if agent_config.get("requires_hipaa_compliance"):
        modules.append("shared/hipaa_compliance.md")
    
    return modules  # Returns list of module paths (not resolved yet)

# Then resolve each module path:
# resolved_modules = [find_module(m, account_slug) for m in selected_modules]
```

**Composition**:
```python
async def generate_full_prompt(agent_config, account_id, db_session, user_query) -> str:
    base = load_base_prompt(agent_config)
    directory_docs = await generate_directory_tool_docs(...)  # Existing
    modules = load_modules(select_modules(user_query, agent_config))
    
    return f"{base}\n\n{directory_docs}\n\n{modules}"
```

**Pros**: Builds on existing infrastructure, DRY principle, flexible combinations, no latency penalty, easy maintenance, hybrid system+account model reduces duplication while allowing customization

**Cons**: Prompt length increases, need logic for module selection and resolution, potential instruction conflicts

---

### Module Storage Strategy: Hybrid (System + Account)

**Why Hybrid?** Balance between DRY (Don't Repeat Yourself) and customization flexibility.

**System-Level Modules** (`backend/config/prompt_modules/`):
- ✅ **Use for**: Universal content that applies to all accounts
- ✅ **Examples**:
  - `shared/hipaa_compliance.md` - Federal law (same for everyone)
  - `shared/tone_guidelines.md` - General best practices
  - `medical/clinical_disclaimers.md` - Standard "not medical advice"
  - `administrative/insurance_info.md` - Generic insurance concepts
- ✅ **Benefits**: Single source of truth, easy to maintain, no duplication
- ✅ **Update once**: All accounts get the latest version

**Account-Level Modules** (`backend/config/agent_configs/{account}/modules/`):
- ✅ **Use for**: Account-specific customizations and overrides
- ✅ **Examples**:
  - `medical/emergency_protocols.md` - Wyckoff ER: 718-963-7272 (specific!)
  - `administrative/billing_policies.md` - Wyckoff insurance list (unique!)
  - `administrative/appointment_scheduling.md` - Wyckoff hours (varies!)
- ✅ **Benefits**: Multi-tenant isolation, account can customize without affecting others
- ✅ **Override**: Account version takes precedence over system version

**Resolution Rule**: **Account First, System Fallback**
```
Query: Load "medical/emergency_protocols.md"

1. Check: agent_configs/wyckoff/modules/medical/emergency_protocols.md
   → Found! Use Wyckoff version (has Wyckoff ER number)

Query: Load "shared/hipaa_compliance.md"

1. Check: agent_configs/wyckoff/modules/shared/hipaa_compliance.md
   → Not found
2. Check: prompt_modules/shared/hipaa_compliance.md
   → Found! Use system version (federal law, same for all)
```

**Real-World Example**:

| Module | Level | Rationale |
|--------|-------|-----------|
| `medical/emergency_protocols.md` | **Account** | ER phone numbers vary by hospital |
| `shared/hipaa_compliance.md` | **System** | Federal law, same for all |
| `administrative/billing_policies.md` | **Account** | Insurance accepted varies |
| `medical/clinical_disclaimers.md` | **System** | Standard disclaimers, universal |
| `administrative/appointment_scheduling.md` | **Account** | Hours/process varies |
| `shared/tone_guidelines.md` | **System** | Best practices, universal |

**Why NOT agent-level storage?**
- ❌ Too granular (massive duplication)
- ❌ Hard to maintain (update N agents vs. 1 account)
- ✅ Use **configuration** for per-agent control instead:
  ```yaml
  # doctor_finder agent - minimal modules
  prompting:
    modules:
      enabled: true
      available_modules: ["medical/emergency_protocols"]
  
  # hospital_assistant agent - full modules
  prompting:
    modules:
      enabled: true
      available_modules: 
        - "medical/emergency_protocols"
        - "administrative/billing_policies"
        - "shared/hipaa_compliance"
  ```

**Key Insight**: **Storage** at system/account level, **selection** at agent level via config!

---

## Core Design Principles

**IMPORTANT**: Dynamic prompting is OPTIONAL. Most agents work perfectly with just base prompt or base + directory docs!

**When to use dynamic prompting**:
- ✅ Multi-use case agents (emergency + billing + general)
- ✅ Context-critical responses (HIPAA disclaimers, emergency protocols)
- ✅ Domain compliance requirements
- ❌ Simple chatbots (not needed)
- ❌ Single-purpose agents (directory-only is fine)

---

**Foundation: Schema-Driven Directory Tools** (Already Exists - Always On If Configured)

All directory-specific knowledge lives in YAML schemas:
- `generate_directory_tool_docs()` reads schemas dynamically
- No domain-specific code in `prompt_generator.py`
- Works for any directory type (medical, phone, product, etc.)
- **Automatic enhancement** - no extra config needed!

**Phase 1: Modular Composition** (OPTIONAL Enhancement - Opt-In)

Add context-specific prompt modules for complex agents:

```python
# backend/app/agents/tools/prompt_generator.py (enhanced)

async def generate_context_aware_prompt(
    agent_config: dict,
    account_id: UUID,
    db_session: AsyncSession,
    user_query: str
) -> str:
    # Load base prompt
    base = load_base_prompt(agent_config)
    
    # Generate directory docs from schemas (EXISTING - schema-driven)
    directory_docs = await generate_directory_tool_docs(
        agent_config, account_id, db_session
    )
    
    # Load context modules based on query (NEW - context-driven)
    modules = select_modules(user_query, agent_config)
    module_content = load_and_combine_modules(modules)
    
    # Final composition: base + schema-driven + context-driven
    return f"{base}\n\n{directory_docs}\n\n{module_content}"
```

**Key Design**: 
- **Schemas** = Directory domain knowledge (what to search for)
- **Modules** = Contextual enhancements (how to respond in specific situations)

---

## Implementation Details

### Schema-Driven Prompt Generation (Foundation)

**Core Principle**: `prompt_generator.py` must remain domain-agnostic. All domain-specific content lives in schema files.

**Current State**: Code has medical-domain assumptions that limit reusability:
- Hard-coded heading: "Medical Term Mappings (Lay → Formal)"
- Hard-coded key: `medical_specialties` in synonym mappings
- Result: Works for medical directories, breaks for phone directories, product catalogs, etc.

**Solution**: Schema defines its own presentation metadata using standardized conventions.

---

#### Standardized Schema Convention

**All directory schemas use consistent key names**:

```yaml
search_strategy:
  # Optional: Custom heading for synonym mappings
  synonym_mappings_heading: "Medical Term Mappings (Lay → Formal)"
  
  # Required: Guidance text for LLM
  guidance: |
    **BEFORE searching, think step-by-step:**
    1. What does this term refer to in our domain?
    2. What are the formal names?
    3. Make multiple tool calls if needed
  
  # Required: Standard structure using consistent keys
  synonym_mappings:
    - lay_terms: ["kidney doctor", "renal specialist"]
      formal_terms: ["Nephrology"]  # ← Standardized key
      search_approach: "Search for 'Nephrology'"
```

**Examples by domain**:

**Medical Directory** (`medical_professional.yaml`):
```yaml
search_strategy:
  synonym_mappings_heading: "Medical Term Mappings (Lay → Formal)"
  synonym_mappings:
    - lay_terms: ["heart doctor", "cardiac specialist"]
      formal_terms: ["Cardiology", "Interventional Cardiology"]
```

**Phone Directory** (`phone_directory.yaml`):
```yaml
search_strategy:
  synonym_mappings_heading: "Department Mappings (Common Terms → Official Names)"
  synonym_mappings:
    - lay_terms: ["ER", "emergency room", "urgent care"]
      formal_terms: ["Emergency Department"]
```

**Product Catalog** (`product_directory.yaml`):
```yaml
search_strategy:
  synonym_mappings_heading: "Product Category Mappings (Customer → Internal)"
  synonym_mappings:
    - lay_terms: ["laptop", "notebook computer", "portable PC"]
      formal_terms: ["Portable Computers", "Laptops"]
```

---

#### Code Changes Required

**In `prompt_generator.py` (lines 140-147) - Current (domain-specific)**:
```python
# PROBLEM: Hard-coded for medical domain
strategy_parts.append("\n**Medical Term Mappings (Lay → Formal):**")
medical = ', '.join(f'"{spec}"' for spec in mapping.get('medical_specialties', []))
```

**Updated (domain-agnostic)**:
```python
# Read heading from schema, fall back to generic
heading = strategy.get('synonym_mappings_heading', 'Term Mappings')
strategy_parts.append(f"\n**{heading}:**")

# Use standardized key with backward compatibility
formal_terms = (
    mapping.get('formal_terms') or           # New standard
    mapping.get('medical_specialties') or    # Backward compat
    mapping.get('department_names') or       # Backward compat
    []
)
formal = ', '.join(f'"{term}"' for term in formal_terms)
```

---

#### Benefits

**For Schema Authors**:
- ✅ Full control over domain presentation
- ✅ No code changes needed for new directory types
- ✅ Self-documenting (heading explains the mapping)
- ✅ Reusable patterns across industries

**For Developers**:
- ✅ `prompt_generator.py` works with any domain
- ✅ No if/else logic for different directory types
- ✅ Easy to test (just swap schemas)
- ✅ Single codebase supports unlimited directory types

**For Multi-Domain Support**:
- ✅ Healthcare: "Medical Term Mappings"
- ✅ Hospitality: "Service Mappings (Guest Request → Service Type)"
- ✅ Finance: "Account Type Mappings (Customer → Official)"
- ✅ Legal: "Practice Area Mappings (Client → Legal)"
- ✅ Education: "Course Subject Mappings (Student → Catalog)"
- ✅ Real Estate: "Property Type Mappings (Common → MLS Terms)"

---

#### Migration Path

**Phase 1**: Update existing schemas
1. Add `synonym_mappings_heading` to `medical_professional.yaml`
2. Rename `medical_specialties` → `formal_terms` (keep old key for backward compat)
3. Update `phone_directory.yaml` to use `formal_terms` from the start

**Phase 2**: Update `prompt_generator.py`
1. Read heading from schema with fallback
2. Use standardized `formal_terms` key
3. Maintain backward compatibility with old keys

**Phase 3**: Documentation
1. Create schema authoring guide with examples
2. Document convention in architecture docs
3. Update existing schemas to new standard

---

#### Design Principle: Configuration Over Code

**Rule**: Never hard-code domain knowledge in Python

✅ **DO**: Add new directory type → Create YAML schema (no code changes)  
✅ **DO**: Change presentation → Edit schema heading (no deployment)  
✅ **DO**: Add synonym mapping → Update schema (agent learns immediately)  
❌ **DON'T**: Add if/else logic for different domains  
❌ **DON'T**: Hard-code domain terminology in code  
❌ **DON'T**: Create domain-specific functions in `prompt_generator.py`

This makes the system truly extensible for any domain.

---

### Multi-Directory Selection (Schema-Driven)

**Problem**: When an agent has access to multiple directories, how does the LLM know which directory to search?

**Example scenario**:
```yaml
# Wyckoff agent config.yaml
tools:
  directory:
    accessible_lists:
      - "doctors"          # Medical professionals
      - "phone_directory"  # Department phone numbers
```

**Query ambiguity**:
- "I need a cardiologist" → Should search `doctors` only
- "What's the ER number?" → Should search `phone_directory` only
- "I need a cardiologist, what's the phone number?" → Should search `doctors`, maybe `phone_directory`

---

#### Solution: Add `directory_purpose` to Schemas

**Standard convention** (all schemas):
```yaml
# Required for ALL directory schemas
directory_purpose:
  description: "Short description of what this directory contains"
  
  # When to use this directory (primary use cases)
  use_for:
    - "Use case 1"
    - "Use case 2"
  
  # Example queries that should use this directory
  example_queries:
    - "Query example 1"
    - "Query example 2"
  
  # Optional: When NOT to use this directory (helps avoid confusion)
  not_for:
    - "Anti-pattern 1 (use other_directory instead)"
```

---

#### Example: Medical Professional Schema

```yaml
# medical_professional.yaml

entry_type: medical_professional
schema_version: "1.0"

directory_purpose:
  description: "Medical professionals including doctors, nurses, specialists"
  
  use_for:
    - "Finding a doctor by medical specialty (cardiology, nephrology, etc.)"
    - "Finding a doctor by name"
    - "Finding doctors who speak a specific language"
    - "Getting doctor contact information and office location"
  
  example_queries:
    - "I need a cardiologist"
    - "Do you have kidney specialists?"
    - "Who is Dr. Jane Smith?"
    - "Are there Spanish-speaking doctors?"
  
  not_for:
    - "General hospital department phone numbers (use phone_directory)"
    - "Hospital services information (use services)"

# ... rest of schema (required_fields, searchable_fields, search_strategy, etc.)
```

---

#### Example: Phone Directory Schema

```yaml
# phone_directory.yaml

entry_type: phone_directory
schema_version: "1.0"

directory_purpose:
  description: "Hospital department phone numbers and service contact information"
  
  use_for:
    - "Getting department phone numbers (ER, billing, appointments)"
    - "Finding contact information for hospital services"
    - "Getting hours of operation for departments"
    - "Finding building locations for services"
  
  example_queries:
    - "What's the emergency room number?"
    - "How do I reach the billing department?"
    - "What's the main hospital number?"
    - "When is the pharmacy open?"
  
  not_for:
    - "Finding individual doctors (use doctors directory)"
    - "Medical specialty information (use doctors directory)"

# ... rest of schema
```

---

#### Generated "Directory Selection Guide"

When `prompt_generator.py` detects **multiple accessible directories**, it generates a selection guide:

```markdown
## Directory Tool

You have access to multiple directories. Choose the appropriate directory based on the query:

### Directory: `doctors` (52 medical_professionals)
**Contains**: Medical professionals including doctors, nurses, specialists
**Use for**:
- Finding a doctor by medical specialty (cardiology, nephrology, etc.)
- Finding a doctor by name
- Finding doctors who speak a specific language
- Getting doctor contact information and office location

**Example queries**: "I need a cardiologist", "Who is Dr. Jane Smith?"
**Don't use for**: General hospital department phone numbers (use phone_directory)

---

### Directory: `phone_directory` (15 phone_directorys)
**Contains**: Hospital department phone numbers and service contact information
**Use for**:
- Getting department phone numbers (ER, billing, appointments)
- Finding contact information for hospital services
- Getting hours of operation for departments

**Example queries**: "What's the ER number?", "How do I reach billing?"
**Don't use for**: Finding individual doctors (use doctors directory)

---

### Multi-Directory Queries

**If a query involves multiple aspects**:
1. Search the most specific directory first
2. Combine results if relevant to the query
3. Example: "I need a cardiologist, what's the phone number?"
   - First: Search `doctors` for cardiologists → Get doctor's contact info
   - Then: If scheduling mentioned, check `phone_directory` for appointments

**Available**: `doctors` (52 medical_professionals), `phone_directory` (15 phone_directorys)

[... rest of search strategy and tool documentation ...]
```

---

#### Code Changes: `prompt_generator.py`

**Current behavior** (lines 94-188):
- Iterates through all accessible directories
- Generates combined documentation
- No guidance on which directory to use

**Enhanced behavior**:
```python
async def generate_directory_tool_docs(...) -> str:
    # ... (existing code to load directories) ...
    
    # NEW: If multiple directories, generate selection guide first
    if len(lists_metadata) > 1:
        docs_lines.append("\n**You have access to multiple directories. Choose based on the query:**\n")
        
        for list_meta in lists_metadata:
            schema = DirectoryImporter.load_schema(list_meta.schema_file)
            purpose = schema.get('directory_purpose', {})
            
            # Extract directory purpose
            description = purpose.get('description', 'N/A')
            use_for = purpose.get('use_for', [])
            example_queries = purpose.get('example_queries', [])
            not_for = purpose.get('not_for', [])
            
            # Generate directory card
            docs_lines.append(f"\n### Directory: `{list_meta.list_name}` ({entry_count} {list_meta.entry_type}s)")
            docs_lines.append(f"**Contains**: {description}")
            
            if use_for:
                docs_lines.append("**Use for**:")
                for use_case in use_for:
                    docs_lines.append(f"- {use_case}")
            
            if example_queries:
                examples_text = ', '.join(f'"{q}"' for q in example_queries[:3])
                docs_lines.append(f"**Example queries**: {examples_text}")
            
            if not_for:
                for anti_pattern in not_for:
                    docs_lines.append(f"**Don't use for**: {anti_pattern}")
            
            docs_lines.append("---")
        
        # Multi-directory query guidance
        docs_lines.append("\n### Multi-Directory Queries")
        docs_lines.append("**If a query involves multiple aspects**:")
        docs_lines.append("1. Search the most specific directory first")
        docs_lines.append("2. Combine results if relevant to the query\n")
    
    # ... (existing code for search strategy, field documentation) ...
```

---

#### Benefits

**For LLMs**:
- ✅ Clear guidance on which directory to use
- ✅ Reduces incorrect directory searches
- ✅ Better handling of multi-faceted queries

**For Schema Authors**:
- ✅ Define directory purpose once in schema
- ✅ No code changes needed to add new directories
- ✅ Self-documenting system

**For Developers**:
- ✅ No hardcoded directory routing logic
- ✅ Works with any combination of directories
- ✅ Easy to test (just check generated docs)

---

#### Edge Cases

**Single directory**: Skip selection guide, go straight to tool docs (existing behavior)

**Overlapping directories**: Use `not_for` field to clarify boundaries
```yaml
# doctors directory
not_for:
  - "General department phone numbers (use phone_directory)"

# phone_directory
not_for:
  - "Individual doctor contact (use doctors directory)"
```

**Cross-directory queries**: LLM instructed to search multiple directories sequentially
```
Query: "I need a cardiologist, what's the scheduling number?"
1. Search doctors → Find cardiologist with contact info
2. Search phone_directory → Find appointments department number
3. Combine results in response
```

---

### Module Selection Strategy

**Keyword-based detection** (fast, deterministic):

```python
BILLING_KEYWORDS = ["billing", "insurance", "payment", "cost", "price", "charge"]
EMERGENCY_KEYWORDS = ["emergency", "urgent", "er", "911", "chest pain", "bleeding"]
SYMPTOM_KEYWORDS = ["symptom", "pain", "sick", "hurt", "fever", "nausea"]
DIRECTORY_KEYWORDS = ["doctor", "find", "who", "specialist", "physician"]

def select_modules(query: str, agent_config: dict) -> List[str]:
    q_lower = query.lower()
    modules = []
    
    if any(kw in q_lower for kw in BILLING_KEYWORDS):
        modules.append("administrative/billing_policies.md")
    
    if any(kw in q_lower for kw in EMERGENCY_KEYWORDS):
        modules.append("medical/emergency_protocols.md")
    
    if any(kw in q_lower for kw in SYMPTOM_KEYWORDS):
        modules.append("medical/clinical_disclaimers.md")
    
    return modules
```

**Trade-offs**:
- ✅ Zero latency (no LLM call)
- ✅ Deterministic (testable)
- ⚠️ Simple keyword matching (may miss nuanced queries)

**Future enhancement**: Add lightweight LLM-based classifier if keyword approach proves insufficient.

---

### Use Case Examples

These examples demonstrate how module selection works in practice:

**Emergency Detection**:
- Query: "My chest hurts, who should I see?"
- Modules loaded: `emergency_protocols.md`, `clinical_disclaimers.md`
- Expected behavior: Agent prioritizes emergency contact, then suggests cardiologists

**Billing Question**:
- Query: "Do you take Medicare?"
- Modules loaded: `billing_policies.md`, `insurance_info.md`
- Expected behavior: Agent provides insurance acceptance details, payment options

**Doctor Search**:
- Query: "Who are your cardiologists?"
- Modules loaded: Directory tool docs (auto-generated from `medical_professional.yaml` schema)
- Expected behavior: Agent uses search_directory tool with synonym mappings from YAML

**General Chat**:
- Query: "What are your hours?"
- Modules loaded: None (base prompt sufficient)
- Expected behavior: Simple response from base knowledge

---

### Module Structure

**Example module** (`medical/emergency_protocols.md`):

```markdown
## Emergency Response Protocol

**CRITICAL**: If user mentions any of the following, provide emergency contact immediately:
- Chest pain, difficulty breathing, severe bleeding
- Stroke symptoms (FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 911)
- Loss of consciousness, seizures, severe allergic reaction

**Response Pattern**:
1. Acknowledge urgency
2. Provide: "Call 911 immediately for life-threatening emergencies"
3. Provide: Emergency Department direct line: [phone from directory]
4. Then provide relevant specialist information if applicable

**Example**:
User: "I have severe chest pain"
Response: "This could be a medical emergency. Call 911 immediately if you're experiencing severe chest pain. 
Our Emergency Department is also available 24/7 at 718-963-7272 (Main Building, Ground Floor).
Once stabilized, our Cardiology department can provide follow-up care."
```

**Module size**: Keep under 500 tokens each to avoid prompt bloat.

---

### Prompt Caching Strategy

**Cache key**: `(base_prompt_hash, modules_hash, directory_config_hash)`

```python
@lru_cache(maxsize=50)
def get_cached_prompt(base_hash: str, modules_tuple: tuple, dir_hash: str) -> str:
    return cached_prompt

# Invalidate on:
# - Prompt file updates (base or modules)
# - Directory configuration changes
# - Agent config updates
```

**Target**: Cache hit rate > 70% for common query patterns.

---

### Token Budget Management

**Current prompt sizes**:
- Base prompt: ~800 tokens
- Directory docs: ~400 tokens (auto-generated)
- Per module: ~300 tokens average

**Budget allocation**:
- Base + directory: 1200 tokens (fixed)
- Modules: Max 800 tokens (2-3 modules)
- **Total cap**: 2000 tokens

**Enforcement**: Module selector prioritizes most relevant modules if multiple match.

---

## Integration Points

### File Locations

```
backend/config/
  # SCHEMAS: Directory domain knowledge (existing)
  directory_schemas/
    medical_professional.yaml    # Medical directory schema
    phone_directory.yaml         # Phone directory schema
    product_catalog.yaml         # Product catalog schema
  
  # MODULES: System-level (shared, reusable)
  prompt_modules/
    medical/
      clinical_disclaimers.md    # Standard medical disclaimers (shared)
      symptom_guidance.md        # General symptom guidance (shared)
    administrative/
      insurance_info.md          # Generic insurance info (shared)
    shared/
      hipaa_compliance.md        # Federal law (same for all)
      tone_guidelines.md         # General best practices (shared)
  
  # AGENTS: Account + Instance configuration
  agent_configs/
    {account}/
      modules/                   # Account-level modules (overrides system)
        medical/
          emergency_protocols.md # Wyckoff ER: 718-963-7272
        administrative/
          billing_policies.md    # Wyckoff insurance policies
          appointment_scheduling.md # Wyckoff hours
      
      {instance}/
        system_prompt.md         # Agent's unique identity (stays here!)
        config.yaml              # Agent config (which modules to use)

backend/app/agents/tools/
  prompt_generator.py            # DOMAIN-AGNOSTIC - Reads schemas + modules
  module_loader.py               # NEW - Handles account→system resolution
```

**Key Architecture Points**:
- **Schemas** = Directory domain knowledge (auto-generates tool docs)
- **System Modules** = Shared, reusable content (DRY principle)
- **Account Modules** = Customizations & overrides (multi-tenant isolation)
- **system_prompt.md** = Agent's unique identity (per-instance)
- **Code** = Generic logic only (no domain assumptions)

**Module Resolution**:
1. Agent config lists modules: `["medical/emergency_protocols", "shared/hipaa_compliance"]`
2. For each module, check account folder first, then system folder
3. Compose: `system_prompt.md` + directory docs + resolved modules

### API Changes

**Minimal changes required**:

1. `generate_directory_tool_docs()` → `generate_context_aware_prompt()`
   - Add `user_query` parameter
   - Add module selection logic
   - Compose final prompt

2. `create_simple_chat_agent()` or agent initialization
   - Pass `user_query` to prompt generator
   - Create agent with composed prompt

**Backward compatible**: If `user_query` not provided, falls back to current behavior.

---

## Schema Creation Tasks

**Directory Schemas Needed** (create in `backend/config/directory_schemas/`):

- [x] **medical_professional.yaml** - EXISTING (needs Phase 0 updates)
  - Status: Exists, needs `synonym_mappings_heading` + `directory_purpose` added
  - Location: `backend/config/directory_schemas/medical_professional.yaml`
  - Use case: Wyckoff doctors directory

- [ ] **phone_directory.yaml** - NEW (for hospital departments)
  - Status: Not created yet
  - Use case: Wyckoff hospital department phone numbers (ER, billing, appointments, etc.)
  - Required sections:
    - `entry_type: phone_directory`
    - `directory_purpose` (description, use_for, example_queries, not_for)
    - `required_fields` (department_name, phone_number, service_type)
    - `optional_fields` (hours_of_operation, building_location, fax, email)
    - `search_strategy` (guidance, synonym_mappings with `formal_terms`, examples)
    - `searchable_fields` (department_name, service_type, hours_of_operation)
  - Referenced in: Feature 0023-009 (Phone Directory for Hospital Departments)

- [ ] **pharmaceutical.yaml** - EXISTING MAPPER, NEEDS SCHEMA
  - Status: Mapper exists (`DirectoryImporter.pharmaceutical_mapper`), schema file missing
  - Use case: Pharmaceutical/drug information directories
  - Required sections: TBD (analyze existing mapper to determine fields)

- [ ] **product_catalog.yaml** - EXISTING MAPPER, NEEDS SCHEMA
  - Status: Mapper exists (`DirectoryImporter.product_mapper`), schema file missing
  - Use case: Product catalogs for e-commerce or inventory
  - Required sections: TBD (analyze existing mapper to determine fields)

- [ ] **services.yaml** - FUTURE (mentioned in examples)
  - Status: Not started
  - Use case: Hospital services and programs (e.g., physical therapy, lab services, imaging)
  - Required sections: TBD (design based on future requirements)

**Schema Creation Priority**:
1. **Update existing**: `medical_professional.yaml` (Phase 0 Part A & B)
2. **Create for Wyckoff**: `phone_directory.yaml` (Feature 0023-009)
3. **Backfill existing mappers**: `pharmaceutical.yaml`, `product_catalog.yaml`
4. **Future expansion**: `services.yaml` and others as needed

**Schema Creation Checklist** (for each new schema):
- [ ] Define `entry_type` and `schema_version`
- [ ] Add `directory_purpose` section (description, use_for, example_queries, not_for)
- [ ] Define `required_fields` and `optional_fields`
- [ ] Define `searchable_fields` with descriptions and examples
- [ ] Create `search_strategy` section:
  - [ ] Add `synonym_mappings_heading`
  - [ ] Add `guidance` text for LLM
  - [ ] Add `synonym_mappings` using standardized `formal_terms` key
  - [ ] Add concrete `examples` with thought processes
- [ ] Define `tags_usage` if applicable
- [ ] Define `contact_info_fields` if applicable
- [ ] Create corresponding mapper function in `DirectoryImporter`
- [ ] Add mapper to registry in `seed_directory.py`
- [ ] Create sample CSV data file
- [ ] Test import and search functionality

---

## Migration Path

**Phase 0**: Schema Standardization (Foundation) - CRITICAL PREREQUISITE

**Part A: Synonym Mapping Standardization**
1. Update `medical_professional.yaml`:
   - Add `synonym_mappings_heading` field
   - Rename `medical_specialties` → `formal_terms` (keep old for backward compat)
2. Update `prompt_generator.py`:
   - Read `synonym_mappings_heading` from schema
   - Use `formal_terms` with fallback to old keys
   - Remove hard-coded "Medical Term Mappings" heading
3. Test with existing medical directory (should work identically)

**Part B: Multi-Directory Selection**
1. Add `directory_purpose` section to ALL schemas:
   - `medical_professional.yaml`: Add purpose, use_for, example_queries, not_for
   - `phone_directory.yaml`: Add same fields (when created)
2. Update `prompt_generator.py`:
   - Detect multiple accessible directories (if len(lists_metadata) > 1)
   - Generate "Directory Selection Guide" section
   - Extract and format directory_purpose from each schema
   - Add multi-directory query guidance
3. Test with single directory (should skip selection guide)
4. Test with multiple directories (should show selection guide)

**Part C: Documentation**
1. Create "Schema Authoring Guide" in architecture docs
2. Document `directory_purpose` convention
3. Document `formal_terms` convention
4. Update existing schema documentation

**Why Phase 0 is critical**: Dynamic prompting (modules) builds on schema-driven directory selection. If the LLM can't pick the right directory, contextual modules won't help.

---

**Phase 1**: Modular Prompts (OPTIONAL - Opt-In Feature)

**Who needs this?**: Agents that require context-specific enhancements (emergency handling, billing info, disclaimers)

**Who doesn't need this?**: Simple agents and directory-only agents work fine without it!

**Implementation**:
1. **Create hybrid module structure**:
   - System-level: `backend/config/prompt_modules/` (shared modules)
   - Account-level: `backend/config/agent_configs/{account}/modules/` (overrides)
   
2. **Create initial system-level modules** (shared across all accounts):
   - `shared/hipaa_compliance.md` - Federal law (universal)
   - `shared/tone_guidelines.md` - Best practices (universal)
   - `medical/clinical_disclaimers.md` - Standard disclaimers (universal)
   
3. **Create Wyckoff account-level modules** (Wyckoff-specific):
   - `wyckoff/modules/medical/emergency_protocols.md` - Wyckoff ER: 718-963-7272
   - `wyckoff/modules/administrative/billing_policies.md` - Wyckoff insurance
   - `wyckoff/modules/administrative/appointment_scheduling.md` - Wyckoff hours

4. **Implement module loader** (`backend/app/agents/tools/module_loader.py`):
   - `find_module()` - Account-first resolution (account → system → error)
   - `load_module_content()` - Read and return module markdown
   - `load_and_combine_modules()` - Load multiple modules, concatenate

5. **Enhance `prompt_generator.py`**:
   - Add `user_query` parameter (optional, backward compatible)
   - Add module selection logic (keyword-based)
   - Use `module_loader` for account→system resolution
   - Compose: base + directory + resolved modules

6. **Add `prompting.modules` config section** to agent config schema:
   ```yaml
   prompting:
     modules:
       enabled: true
       selection_mode: "keyword"
       available_modules: [...]
   ```

7. **Update agent creation** to optionally pass `user_query`

8. **Test with Wyckoff agent**:
   - Enable modules via config
   - Test emergency query (loads Wyckoff ER number)
   - Test HIPAA query (loads system compliance module)

**Backward compatibility**: Existing agents continue to work without any changes!

---

## Future Enhancements

### Phase 2: Dynamic Instructions (Message Prepending)

**Status**: Proposed enhancement for handling time-critical context

**Problem**: Some context cannot be predetermined at agent creation time and needs runtime injection. Examples:
- Emergency/urgent queries requiring immediate priority handling
- Follow-up questions needing conversation history awareness
- Time-sensitive instructions (e.g., "Pharmacy closes in 30 minutes")

**Solution**: Inject context-specific instructions directly into the user message before agent processing.

**Implementation Approach**:
```python
# backend/app/agents/simple_chat.py

async def simple_chat_stream(message: str, message_history: list, ...):
    # Detect critical context patterns
    instructions = []
    
    # Emergency detection
    if has_emergency_keywords(message):
        instructions.append("[URGENT: Provide emergency contact first (911 + ER direct line)]")
    
    # Follow-up detection
    if is_followup_question(message_history):
        instructions.append("[CONTEXT: User following up on previous answer]")
    
    # Inject instructions before message
    if instructions:
        message = "\n".join(instructions) + f"\n\n{message}"
    
    result = await agent.run(message, ...)
```

**Configuration** (opt-in via agent config):
```yaml
prompting:
  dynamic_instructions:
    enabled: true
    emergency_detection: true      # Detect emergency keywords
    followup_context: true          # Add context for follow-ups
```

**Why Optional**: Adds message length overhead and may conflict with base prompt if not carefully designed. Most agents don't need this level of runtime control.

**When to Reconsider**: If agents frequently miss critical context cues or need runtime priority adjustments based on query urgency.

---

### Phase 3: Advanced Module Selection

**Status**: Future refinement if keyword-based approach proves insufficient

**Problem**: Simple keyword matching may miss nuanced queries or context that requires more sophisticated intent classification.

**Proposed Enhancements**:

1. **LLM-Based Intent Classifier**:
   - Use lightweight LLM call to classify query intent before module selection
   - More accurate than keyword matching for complex queries
   - Trade-off: Added latency (~50-100ms) and cost per request

2. **Conversation History Analysis**:
   - Load modules based on conversation context, not just current query
   - Example: User asked about billing 2 turns ago → Keep billing modules loaded
   - Improves coherence for multi-turn conversations

3. **Dynamic Module Prioritization**:
   - Track which modules actually improved response quality
   - Auto-adjust module selection based on effectiveness metrics
   - Machine learning approach to optimize module combinations

4. **Multi-Language Support**:
   - Translate keywords or use language-agnostic embeddings for module selection
   - Support non-English queries with same module library

**When to Reconsider**: After collecting real-world usage data showing keyword approach limitations. Current approach should be tested first before adding complexity.

---

### Other Future Considerations

**Token Budget Optimization**:
- Dynamic token allocation based on query complexity
- Compress or summarize less-critical modules when approaching budget

**Module Versioning**:
- Version control for modules with rollback capability
- A/B testing framework for comparing module versions

**Cross-Account Module Sharing**:
- Marketplace or library of community-contributed modules
- Standardized format for sharing best practices

---

## Related Architecture

**Schema-Driven Directory System** (Foundation):
- `directory_schemas/*.yaml` - Domain knowledge for directory types
- `prompt_generator.py` - Schema-driven tool doc generation (MUST remain domain-agnostic)
- `directory_service.py` - Schema-driven search implementation

**Agent Infrastructure**:
- `agent_base.py` - Agent creation and initialization
- `simple_chat.py` - Agent execution and message handling
- `configuration-reference.md` - Agent config structure

**Key Principle**: All domain knowledge lives in YAML files, never in Python code.

---

## Summary: Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ User Query: "I need a kidney doctor"                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Dynamic Prompting (Proposed)                                │
│ • Base prompt (static)                                      │
│ • Context modules (keyword-detected: billing, emergency)    │
│ • Dynamic instructions (message prepending if urgent)       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Schema-Driven Directory Tools (Existing)                    │
│ • Reads medical_professional.yaml                           │
│ • Generates tool docs: "kidney doctor" → "Nephrology"       │
│ • LLM learns synonym mappings from schema                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LLM Agent: Calls search_directory(filters={"specialty":    │
│            "Nephrology"}) based on schema-provided mappings │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Directory Service: Searches JSONB for matching specialists  │
└─────────────────────────────────────────────────────────────┘
```

**Key**: Schemas provide domain knowledge, modules provide context enhancements.

---

## Design Decision Summary

### Module Storage Architecture: Hybrid (System + Account)

**Decision**: Use **both** system-level and account-level module storage with account-first resolution.

**Rationale**:
- **System modules** (`prompt_modules/`) = DRY principle for universal content
- **Account modules** (`agent_configs/{account}/modules/`) = Multi-tenant isolation + customization
- **Agent config** = Controls which modules each agent uses (not storage location)
- **system_prompt.md** = Stays at agent instance level (unique identity per agent)

**Resolution Order**: Account → System → Error

**Benefits**:
1. ✅ Reduces duplication (shared modules used by all accounts)
2. ✅ Allows customization (accounts can override any module)
3. ✅ Multi-tenant isolation (account modules private to account)
4. ✅ Easy maintenance (update system module once, all accounts benefit)
5. ✅ Flexible control (agents choose modules via config, not file location)

**Example**:
- `shared/hipaa_compliance.md` → System (federal law, same for all)
- `medical/emergency_protocols.md` → Account (ER numbers vary per hospital)
- `system_prompt.md` → Agent instance (each agent has unique personality)

**Key Insight**: **Storage** location (system vs. account) determined by **content scope**, not by who uses it. **Selection** controlled by agent config.

---

### Directory Schema Storage Architecture: System-Level Only

**Decision**: Directory schemas remain **system-level only** (`backend/config/directory_schemas/`). No account-level schema overrides.

**Rationale**:
- **Schemas define data structure** (database JSONB fields, search logic)
- **Modules define content** (what to say in responses)
- **Critical difference**: Varying schemas = data fragmentation, varying modules = safe content customization

**Why NOT System + Account for Schemas?**

| Concern | Impact |
|---------|--------|
| **Database inconsistency** | Same `directory_entries` table has entries with different JSONB structures |
| **Search logic complexity** | Code must handle multiple schema versions per entry_type |
| **Migration nightmare** | Which schema version for each account? How to migrate? |
| **Cross-account features break** | Can't aggregate/compare data across accounts |
| **Maintenance burden** | N schemas to maintain instead of 1 |
| **Breaking changes risk** | Account schema could conflict with core fields |

**Recommended Approach: System-Level + JSONB Extensibility**

```yaml
# medical_professional.yaml (system-level)

required_fields:
  - department
  - specialty

optional_fields:
  - board_certifications
  - education
  # ... standard fields

# CRITICAL: JSONB allows additional fields not in schema
# Accounts can add custom fields via CSV import
# System code ignores unknown fields gracefully
```

**Example: Account adds custom field**
```csv
# Wyckoff CSV import
doctor_name,department,specialty,medical_license_number,npi_number
Dr. Smith,Cardiology,Interventional Cardiology,NYS-12345,1234567890
```

**Result**:
- Entry stored with `entry_data: {department, specialty, medical_license_number, npi_number}`
- System code works (uses `department`, `specialty` per schema)
- Account-specific queries can use `medical_license_number` if needed
- No schema override required! JSONB is inherently extensible

**When Account Needs Different Structure**: Create new `entry_type` with its own system-level schema

**Example**:
- ✅ Standard: `medical_professional.yaml` (system) - used by Wyckoff, Windriver, etc.
- ✅ Standard: `phone_directory.yaml` (system) - used by all hospitals
- ✅ Unique: `produce_inventory.yaml` (system) - used by AgroFresh only
- ❌ Avoid: `wyckoff_medical_professional.yaml` (account override) - causes fragmentation

**Key Principle**: Use **entry_type** differentiation (system-level schemas), not account-level schema overrides!

**Benefits**:
1. ✅ **Data consistency** - All accounts use same structure for same entry_type
2. ✅ **Uniform search logic** - Code doesn't need schema version handling
3. ✅ **Easy maintenance** - Update schema once, all accounts benefit
4. ✅ **Cross-account analytics** - Can compare/aggregate data across accounts
5. ✅ **Simpler migrations** - One schema version to manage
6. ✅ **Extensibility** - JSONB supports custom fields without schema changes

**Comparison: Schemas vs. Modules**

| Aspect | Directory Schemas | Prompt Modules |
|--------|-------------------|----------------|
| **What it is** | Data structure (how data is organized) | Content (what to say) |
| **Storage** | System-level only | Hybrid (System + Account) |
| **Varies safely?** | ❌ No (causes data fragmentation) | ✅ Yes (content customization) |
| **Database impact** | Direct (JSONB structure) | None |
| **Search impact** | Direct (fields queried) | None |
| **Migration impact** | High (data structure changes) | None |
| **Multi-tenant** | Via `account_id`, not schema variance | Via account-level modules |

**Summary**:
- **Schemas** = Structure (must be consistent) → System-level only
- **Modules** = Content (can vary) → Hybrid (System + Account)
- **system_prompt.md** = Identity (unique per agent) → Agent instance level

---

**Status**: Proposed (not implemented)

**Complexity**: Medium (builds on existing schema-driven infrastructure)

**Impact**: High (improves response quality across diverse request types)

**Foundation**: Schema standardization (Phase 0) must complete before dynamic prompting

**Module Architecture**: Hybrid system + account level (documented above)

