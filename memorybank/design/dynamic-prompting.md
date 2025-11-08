<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Dynamic Prompting Architecture

## Summary

**Problem**: Static system prompts can't adapt to query context (emergency vs. billing vs. directory search).

**Solution**: 5-phase incremental enhancement of `simple_chat.py` to support tool-agnostic prompt composition, schema-driven directory selection, multi-tool support with caching, context modules, and MCP integration.

**Strategy**: Evolve existing `simple_chat` incrementally (not build v2). 65% code reuse, 100% backward compatible at each phase.

**Phases**:
- Phase 1: Pydantic AI native toolsets → Foundation for multi-tool support
- Phase 2: Schema standardization → Multi-directory support
- Phase 3: Multi-tool + caching → 70% cost savings
- Phase 4: Modular prompts → 40% quality improvement
- Phase 5: MCP integration → External tool ecosystem (native support!)

**Expected Results**: 50-60% quality improvement for complex queries, 70% cost reduction via prompt caching.

**Design Principles**:
- ✅ **Graceful degradation** - failures logged but user experience remains seamless
- ✅ **Multi-tenant scalability** - concurrent agent instances without conflicts
- ✅ **Progressive enhancement** - complexity only when needed

**See Also**: `memorybank/analysis/advanced-agent-strategies.md` for alternative approaches evaluated.

---

## Progressive Enhancement Model

**Principle**: Agents work with minimal config. Add complexity only when needed.

### Complexity Levels

**Level 1: Simple Agent (Base Prompt Only)**
- `system_prompt.md` only
- Use case: Basic chatbot, FAQ bot
- Config: No tools configured

**Level 2: Single-Tool Agent**
- Base + ONE tool (directory OR vector search)
- Use case: Doctor finder, knowledge base search
- Config: `tools.directory.enabled: true` OR `tools.vector_search.enabled: true`

**Level 3: Multi-Tool Agent (Phase 1-3)**
- Base + MULTIPLE tools (directory + vector + MCP servers)
- Use case: Comprehensive assistant with multiple data sources
- Config: Multiple tools enabled + MCP servers configured
- Examples:
  - Directory + vector search (Wyckoff, Windriver)
  - Directory + vector + GitHub/Slack MCP servers
  - Vector + weather MCP server

**Level 4: Module-Enhanced (Phase 4)**
- Level 3 + context modules (keyword-selected)
- Use case: Hospital assistant with emergency/billing/HIPAA context
- Config: `prompting.modules.enabled: true` + keyword mappings

**Level 5: Fully Dynamic (Future)**
- Level 4 + dynamic instructions (message prepending)
- Use case: Multi-domain with urgent query detection
- Config: `prompting.dynamic_instructions.enabled: true`

**Key Insight**: Tools (directory, vector, MCP) are **orthogonal** to modules. Any tool combination can use modules!

### Configuration Examples

**Level 1: Simple Agent**
```yaml
name: "Simple Chat Bot"
model_settings:
  model: "deepseek/deepseek-chat-v3.1"
# That's it! Uses system_prompt.md only
```

**Level 2: Single-Tool Agent**
```yaml
name: "Doctor Finder"
tools:
  directory:
    enabled: true
    accessible_lists: ["doctors"]
# Directory docs auto-generated
```

**Level 3: Multi-Tool Agent** (Phase 1-3)
```yaml
name: "Comprehensive Assistant"
tools:
  directory:
    enabled: true
    accessible_lists: ["doctors", "phone_directory"]
  
  vector_search:
    enabled: true
  
  mcp:
    enabled: true
    servers:
      - "github"      # Code/issue management
      - "slack"       # Team notifications
# All tools work together, no prompting config needed yet
```

**Level 4: Module-Enhanced** (Phase 4)
```yaml
name: "Hospital Assistant"
tools:
  directory:
    enabled: true
    accessible_lists: ["doctors", "phone_directory"]
  
  vector_search:
    enabled: true

prompting:
  modules:
    enabled: true  # Explicit opt-in
    keyword_mappings:
      - keywords: ["emergency", "urgent", "er", "911"]
        module: "medical/emergency_protocols.md"
        priority: 10
      - keywords: ["billing", "insurance", "medicare"]
        module: "administrative/billing_policies.md"
        priority: 1
# Modules work with ANY tool combination
```

### Backward Compatibility Requirements

**Existing agent instances** (must continue working unchanged):
- `wyckoff/wyckoff_info_chat1` - vector_search + directory
- `windriver/windriver_info_chat1` - vector_search + directory
- `agrofresh/agro_info_chat1` - vector_search only
- `prepexcellence/prepexcel_info_chat1` - vector_search only
- `acme/acme_chat1` - vector_search + web_search
- `default_account/simple_chat1` - base agent (no tools)
- `default_account/simple_chat2` - vector_search + web_search

**Current implementation** (in `simple_chat.py`):
- Function-based Pydantic AI agent (not BaseAgent class)
- `tools.directory.enabled` - uses `prompt_generator.py` 
- `tools.vector_search.enabled` - Pinecone integration
- Configuration cascade from `config_loader.py`

**Backward compatibility guarantee**: All 7 agent instances work unchanged - they don't have `prompting.modules` config, so new code path never executes.

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

**Module Selection Logic** (config-based, domain-agnostic):
```python
def select_modules(query: str, agent_config: dict) -> List[str]:
    """Domain-agnostic module selection based on config."""
    modules = []
    q_lower = query.lower()
    
    # Read keyword mappings from config (not hardcoded!)
    prompting_config = agent_config.get("prompting", {}).get("modules", {})
    keyword_mappings = prompting_config.get("keyword_mappings", [])
    
    # Match keywords from config
    for mapping in keyword_mappings:
        keywords = mapping.get("keywords", [])
        module_path = mapping.get("module")
        priority = mapping.get("priority", 1)
        
        if any(kw in q_lower for kw in keywords):
            modules.append((module_path, priority))
    
    # Sort by priority (higher first), then return module paths
    modules.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in modules]  # Returns list of module paths (not resolved yet)

# Then resolve each module path:
# resolved_modules = [find_module(m, account_slug) for m in selected_modules]
```

**See "Configuration Examples" section for config structure.**

**Pros**: Builds on existing infrastructure, DRY principle, flexible combinations, no latency penalty, easy maintenance, hybrid system+account model reduces duplication while allowing customization

**Cons**: Prompt length increases, need logic for module selection and resolution, potential instruction conflicts

**See "Code Organization" section for implementation details.**

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
      keyword_mappings:
        - keywords: ["emergency", "urgent"]
          module: "medical/emergency_protocols.md"
  
  # hospital_assistant agent - more comprehensive
  prompting:
    modules:
      enabled: true
      keyword_mappings:
        - keywords: ["emergency", "urgent"]
          module: "medical/emergency_protocols.md"
        - keywords: ["billing", "insurance"]
          module: "administrative/billing_policies.md"
        - keywords: ["hipaa", "privacy"]
          module: "shared/hipaa_compliance.md"
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

**Phase 4: Modular Prompts** (OPTIONAL Enhancement - Opt-In)

Add context-specific prompt modules for complex agents.

**Key Design**: 
- **Schemas** = Directory domain knowledge (what to search for)
- **Modules** = Contextual enhancements (how to respond in specific situations)

**Implementation**: See "Code Organization" section for file structure and "Migration Path" section for implementation details.

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

**In `prompt_generator.py` - Current (domain-specific)**:
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

# Use standardized key (update all schemas to use 'formal_terms')
formal_terms = mapping.get('formal_terms', [])
formal = ', '.join(f'"{term}"' for term in formal_terms)
```

**Note**: Update `medical_professional.yaml` to use `formal_terms` instead of `medical_specialties`.

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

**Current behavior**:
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

**Config-based keyword detection** (Phase 1 - simple and effective):

**Mechanism**: Read `keyword_mappings` from agent config, match keywords in query, return matching modules.

**Configuration**: Each agent defines its own keyword mappings in `agent_configs/{account}/{instance}/config.yaml`

```yaml
# Example: agent_configs/wyckoff/wyckoff_info_chat1/config.yaml
prompting:
  modules:
    enabled: true
    keyword_mappings:
      - keywords: ["billing", "insurance", "payment"]
        module: "administrative/billing_policies.md"
        priority: 1
      
      - keywords: ["emergency", "urgent", "er", "911"]
        module: "medical/emergency_protocols.md"
        priority: 10  # Higher priority
```

**Benefits**:
- ✅ Zero latency (no LLM call)
- ✅ Deterministic (testable)
- ✅ **Domain-agnostic code** - module selection logic reads config, no hardcoded keywords
- ✅ **Multi-tenant flexibility** - accounts customize keywords (e.g., Spanish: "urgencia")
- ✅ **No deployment needed** - add/change keywords via config only
- ⚠️ Simple keyword matching (may miss nuanced queries)

**No system-level defaults** - Each agent explicitly defines its own mappings (clearer, no cascade complexity)

**See "Configuration Examples" section for full config structure.**

**Future enhancement**: LLM-based classifier (see [dynamic-prompting-alternatives.md](./dynamic-prompting-alternatives.md)).

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

---

### Simplified Configuration

**All prompting configuration in `backend/config/app.yaml`** (infrastructure config):

```yaml
# backend/config/app.yaml (add to existing file)

prompting:
  # Simple size guideline (informational, not enforced)
  recommended_module_size_tokens: 500  # Keep modules concise for readability
```

**Design Philosophy**:
- ✅ **Trust LLM context windows** - Modern LLMs (128K+ tokens) can handle large prompts
- ✅ **Focus on correctness** - Get functionality working before optimizing
- ✅ **Defer premature optimization** - Add complexity only when data shows it's needed

**Increase max_tokens to 32,000** (action item):
- Current: `llm.max_tokens: 1024` in `backend/config/app.yaml`
- Current fallback: `512` tokens in `backend/app/config.py` (line 239)
- Update to: `32000` tokens (leverage modern LLM capabilities)
- Ensure no other hardcoded limits in codebase

**Deferred to post-MVP**:
- Token budget enforcement (prioritize/truncate/reject strategies)
- Prompt caching (performance optimization)
- Module size validation (quality can be reviewed manually)

**See [dynamic-prompting-alternatives.md](./dynamic-prompting-alternatives.md)** for deferred optimization features

---

## Integration Points

**Phase 1** (Pydantic AI Native Toolsets):
- Create `toolsets.py` - wrap existing tools with `FunctionToolset`
- Update `simple_chat.py` to support multiple toolsets
- 100% backward compatible (existing behavior unchanged)

**Phase 2** (Schema Standardization):
- Update `prompt_generator.py` to read `synonym_mappings_heading` and `formal_terms` from schemas (domain-agnostic)
- Update `medical_professional.yaml`: rename `medical_specialties` → `formal_terms`, add `directory_purpose`
- Create `phone_directory.yaml` with standardized structure
- No backward compatibility code needed (nothing in production)

**Phase 3** (Multi-Tool + Caching):
- Wrap existing tools using Pydantic AI's `FunctionToolset`
- Update `simple_chat.py` to pass multiple toolsets: `toolsets=[directory_toolset, vector_toolset]`
- Add prompt caching markers to system prompt composition

**Phase 4** (Modular Prompts):
- Create `module_loader.py`, `module_selector.py`
- Create module library structure
- Add `prompting.modules` config parsing
- Use Pydantic AI's `prepare_tools` for dynamic module injection

**Phase 5** (MCP Integration):
- **Use native Pydantic AI support**: `from pydantic_ai.mcp import MCPServerStdio`
- Configure MCP servers in agent config

**Key Simplification**: Leveraging Pydantic AI's native `FunctionToolset`, `toolsets=[...]`, and `MCPServerStdio` eliminates custom abstraction code.

---

## Tool Extensibility & MCP Integration

### Simplified Approach: Use Pydantic AI Native Features

**Discovery**: Pydantic AI already provides:
- ✅ `FunctionToolset` - group related tools
- ✅ `toolsets=[...]` parameter - pass multiple toolsets to agent
- ✅ `MCPServerStdio` - native MCP integration (no custom client needed!)
- ✅ `@agent.toolset` - dynamic toolset selection
- ✅ `prepare_tools` - modify tool definitions at runtime

**Old Approach** (if we had built custom abstractions):
- Build `AgentTool` interface, `ToolRegistry`, custom wrappers for each tool type
- Research and build custom MCP client wrapper
- Result: ~500 lines of custom code

**New Approach** (using Pydantic AI native features):
- Phase 1: Use `FunctionToolset` to wrap existing tools
- Phase 5: Use `MCPServerStdio` directly
- Result: ~60 lines total

**Savings**: Significant reduction in custom abstraction code!

---

### Using Pydantic AI's Native FunctionToolset

**Core Principle**: Wrap existing tool functions using Pydantic AI's built-in `FunctionToolset` class.

**Example: Wrapping Existing Tools**:

```python
# backend/app/agents/tools/toolsets.py

from pydantic_ai import FunctionToolset
from .directory_tools import search_directory
from .vector_tools import vector_search

# Wrap existing directory search function
directory_toolset = FunctionToolset(tools=[search_directory])

# Wrap existing vector search function  
vector_toolset = FunctionToolset(tools=[vector_search])

# Use in agent:
agent = Agent(
    'openai:gpt-5',
    toolsets=[directory_toolset, vector_toolset]  # That's it!
)
```

**Key Benefits**:
- ✅ No custom abstractions needed
- ✅ Wraps existing `directory_tools.py` and `vector_tools.py` unchanged
- ✅ Pydantic AI automatically generates tool schemas from docstrings
- ✅ Tool documentation comes from function docstrings (already written!)

---

### MCP Integration (Native Support!)

**Pydantic AI has built-in MCP support** - no custom wrappers needed!

**Simple Usage Example**:

```python
# backend/app/agents/simple_chat.py

from pydantic_ai.mcp import MCPServerStdio

# Use native MCP support
agent = Agent(
    'openai:gpt-5',
    toolsets=[
        directory_toolset,  # Existing directory tools
        vector_toolset,     # Existing vector tools
        MCPServerStdio('github'),  # MCP server - built-in!
    ]
)
```

**Configuration Example** (Phase 5):

```yaml
# agent_configs/{account}/{instance}/config.yaml

tools:
  mcp:
    enabled: true
    servers:
      - "github"
      - "slack"
```

**That's it!** Pydantic AI handles MCP connection, tool discovery, and schema conversion automatically.

---

## Error Handling & Resilience

**Principle**: Failures are logged but user experience remains seamless. The LLM receives guidance to gracefully handle missing/failed tools.

### Directory Search Failures

**When directory search fails** (database unavailable, query error, schema issues):

1. **Logfire captures details**:
   ```python
   logfire.error("Directory search failed", 
       directory=list_name, 
       error=str(e), 
       account_id=account_id)
   ```

2. **LLM receives guidance in prompt**:
   ```markdown
   **IMPORTANT - Directory Tool Status**: 
   The directory search tool is temporarily unavailable. 
   Apologize to the user and suggest they:
   - Try again in a few moments
   - Call the main hospital number: [from base knowledge]
   - Visit the website: [from base knowledge]
   
   Do NOT make up directory information or phone numbers.
   ```

3. **User experience**: "I apologize, but I'm unable to search our directory right now. You can reach our main line at..."

### MCP Server Failures

**When MCP server is unavailable** (connection timeout, server down, auth failure):

1. **Logfire captures details**:
   ```python
   logfire.warning("MCP server unavailable", 
       server=server_name, 
       error=str(e),
       agent=agent_slug)
   ```

2. **Agent loads without MCP toolset**:
   ```python
   # Graceful degradation
   try:
       mcp_toolset = MCPServerStdio('github')
       toolsets.append(mcp_toolset)
   except Exception as e:
       logfire.warning(f"MCP server 'github' unavailable: {e}")
       # Continue without MCP - other tools still work
   ```

3. **LLM receives guidance in prompt**:
   ```markdown
   **NOTE**: External integrations (GitHub/Slack) are temporarily unavailable.
   If user requests code/repository actions, apologize and suggest:
   - Check back shortly
   - Visit GitHub directly at github.com
   ```

4. **User experience**: Transparent - other tools work, MCP-specific requests get polite explanation.

### Missing Module Files

**When module file is missing** (`emergency_protocols.md` doesn't exist):

1. **Logfire captures details**:
   ```python
   logfire.warning("Module not found", 
       module_path=module_path, 
       account=account_slug,
       agent=agent_slug)
   ```

2. **Module loading fails gracefully**:
   ```python
   try:
       module_content = load_module(module_path, account_slug)
   except ModuleNotFoundError:
       logfire.warning(f"Module not found: {module_path}")
       module_content = None  # Skip this module, continue with others
   ```

3. **Agent continues with remaining modules** - no prompt modification needed.

4. **User experience**: Seamless - they don't know the module was missing, base prompt + other modules still work.

### Partial Failures

**When some tools work but others fail**:

- ✅ **Directory works, vector search fails** → Directory results provided
- ✅ **Vector search works, directory fails** → Vector results provided
- ✅ **2 of 3 modules load** → Agent works with 2 modules
- ✅ **All tools fail** → Agent operates with base prompt only

**Key Principle**: **Degrade gracefully, never fail completely.** Always give the user *something* useful.

---

## Performance & Scalability

### Concurrent Agent Instances

**Multi-tenant isolation**: Multiple agent instances can run simultaneously without conflict.

**Example scenario**:
- **10 Wyckoff agents** handling patient queries simultaneously
- **5 AgroFresh agents** handling farmer questions simultaneously
- **3 PrepExcellence agents** handling student questions simultaneously

**Each instance**:
- ✅ Can search directories concurrently (JSONB queries are fast and isolated)
- ✅ Can search vector databases concurrently (Pinecone handles parallel requests)
- ✅ Can call MCP servers concurrently (independent HTTP connections)
- ✅ Shares nothing with other instances (session-isolated)

**Database performance**:
- Directory searches use JSONB GIN indexes (sub-millisecond queries)
- Read-only operations (no lock contention)
- PostgreSQL connection pooling handles concurrency

**Bottlenecks**:
- ❌ **LLM API rate limits** (OpenRouter, Anthropic quotas)
- ❌ **Vector database quotas** (Pinecone query limits)
- ⚠️ **MCP server capacity** (depends on external service)

**Mitigation**:
- Rate limiting at application level (not in this design - infrastructure concern)
- Queue-based load leveling for high-volume scenarios (future enhancement)
- Monitor via Logfire: response times, error rates, concurrent requests

**No conflicts**: Agent instances do NOT share:
- ❌ Conversation state (each session isolated)
- ❌ Prompt cache (cache is per-model, not per-agent)
- ❌ Tool execution context (stateless functions)

---

## Schema Creation Tasks (Phase 2)

**Schemas needed in `backend/config/directory_schemas/`**:

- [ ] **medical_professional.yaml** - Update in Phase 1
  - Add `synonym_mappings_heading` and `directory_purpose`
  - Rename `medical_specialties` → `formal_terms` (no backward compat needed)

- [ ] **phone_directory.yaml** - Create in Phase 2
  - For hospital departments (ER, billing, appointments)
  - Include: `directory_purpose`, `formal_terms`, search strategy

- [ ] **pharmaceutical.yaml** - Future
  - Mapper exists, needs schema

- [ ] **product_catalog.yaml** - Future
  - Mapper exists, needs schema

**Schema creation checklist**:
- Define `entry_type` and `schema_version`
- Add `directory_purpose` (description, use_for, example_queries, not_for)
- Define required/optional/searchable fields
- Add `search_strategy` with `synonym_mappings_heading` and `formal_terms`
- Create mapper in `DirectoryImporter` + register in `seed_directory.py`
- Test import and search

---

## Migration Path

**Simplified**: 5-phase incremental implementation. Each phase delivers value, backward compatible.

**Strategy**: Evolve `simple_chat` incrementally rather than building v2. Minimizes risk, maximizes code reuse (65% reuse ratio), enables continuous value delivery.

---

### Phase 1: Pydantic AI Native Toolsets (Foundation)

**Risk**: Low (100% backward compatible)  
**Value**: Foundation for multi-tool support using Pydantic AI's built-in features

**Why**: Use Pydantic AI's native `FunctionToolset` and `MCPServerStdio` instead of custom abstractions - simpler, less code, leverages framework features.

**Implementation**:

1. Create `backend/app/agents/tools/toolsets.py`:
   ```python
   from pydantic_ai import FunctionToolset
   from .directory_tools import search_directory
   from .vector_tools import vector_search
   
   # Wrap existing functions
   directory_toolset = FunctionToolset(tools=[search_directory])
   vector_toolset = FunctionToolset(tools=[vector_search])
   ```

2. Update `simple_chat.py` to support multiple toolsets:
   ```python
   # Read agent config to determine enabled tools
   toolsets = []
   if config.get("tools", {}).get("directory", {}).get("enabled"):
       toolsets.append(directory_toolset)
   if config.get("tools", {}).get("vector_search", {}).get("enabled"):
       toolsets.append(vector_toolset)
   
   agent = Agent(model, toolsets=toolsets)
   ```

**Testing**: 
- Verify directory-only agents work unchanged
- Verify vector-search-only agents work unchanged
- All existing tests pass without modification

**Deliverable**: 
- Multi-tool infrastructure ready using Pydantic AI native features
- No custom abstractions needed
- ~20 lines of code (vs. ~200 with custom approach)

---

### Phase 2: Schema Standardization (Domain-Agnostic Prompts)

**Risk**: Low (clean schema updates, nothing in production)  
**Value**: Support for multiple directory types (medical, phone, product, etc.)

**Why**: Make `prompt_generator.py` domain-agnostic so new directory types don't require code changes.

**Part A: Synonym Mapping Standardization**

1. Update `medical_professional.yaml`:
   - Add `synonym_mappings_heading` field: "Medical Term Mappings (Lay → Formal)"
   - Rename `medical_specialties` → `formal_terms` (clean migration)

2. Update `prompt_generator.py`:
   - Read `synonym_mappings_heading` from schema (fallback: "Term Mappings")
   - Use `formal_terms` key (standardized)
   - Remove hard-coded "Medical Term Mappings" heading

3. Test with existing medical directory

**Part B: Multi-Directory Selection**

1. Add `directory_purpose` section to ALL schemas:
   - `medical_professional.yaml`: Add `description`, `use_for`, `example_queries`, `not_for`
   - `phone_directory.yaml`: Add same fields (when created for Feature 0023-009)
   - Future schemas: Require `directory_purpose` as standard

2. Update `prompt_generator.py`:
   - Detect multiple accessible directories: `if len(lists_metadata) > 1`
   - Generate "Directory Selection Guide" section
   - Extract and format `directory_purpose` from each schema
   - Add multi-directory query guidance

3. Test:
   - Single directory: Skip selection guide (existing behavior)
   - Multiple directories: Show selection guide (new feature)

**Part C: Documentation**

1. Create "Schema Authoring Guide" in `memorybank/standards/`
2. Document `directory_purpose` convention
3. Document `formal_terms` convention
4. Update existing schema documentation

**Why Critical**: Dynamic prompting builds on schema-driven directory selection. If LLM can't pick the right directory, contextual modules won't help.

**Deliverable**: 
- Phone directory schema ready (Feature 0023-009)
- Product catalog, pharmaceutical schemas can be added trivially
- No domain-specific code in `prompt_generator.py`

---

### Phase 3: Multi-Tool Support + Prompt Caching

**Risk**: Low (single-tool agents unchanged)  
**Value**: Vector search support + 70% cost reduction + 30% latency improvement

**Why**: Enable directory + vector search working together (using Phase 1 toolsets). Add prompt caching for immediate cost/latency wins.

**Implementation**:

1. **Multi-tool agents already work** (from Phase 1):
   ```python
   # Agents can now use multiple toolsets
   agent = Agent(model, toolsets=[directory_toolset, vector_toolset])
   ```

2. **Add prompt caching** (High ROI Enhancement):

1. Structure prompt for caching:
   - **Static** (cached): Base prompt + directory docs + HIPAA + disclaimers (~8K tokens)
   - **Dynamic** (per-request): Selected modules + conversation history + user query (~2K tokens)

2. Add cache markers (Anthropic models):
   ```python
   messages = [{
       "role": "user",
       "content": [
           {"type": "text", "text": static_prompt, "cache_control": {"type": "ephemeral"}},
           {"type": "text", "text": dynamic_prompt}
       ]
   }]
   ```

3. Add version hash to cached content:
   - Invalidate cache on directory updates
   - Track cache hit rate in Logfire

**Testing**:
- Single-tool agents work as before
- Multi-tool agents show selection guide
- Cache hit rate >80% after warmup

**Deliverable**:
- Directory + vector search working together
- 70% cost reduction (cached reads 10x cheaper)
- 30% latency improvement (cached prompts instant)

**ROI**: For 1000 queries/day, saves ~$650/month in LLM costs.

**See Also**: `memorybank/analysis/advanced-agent-strategies.md` for prompt caching analysis.

---

### Phase 4: Modular Prompts (Context-Specific Enhancements)

**Risk**: Low (opt-in via config, backward compatible)  
**Value**: 40% quality improvement for complex queries (emergency, billing, HIPAA scenarios)

**Who needs this**: Agents requiring context-specific enhancements (emergency protocols, billing info, disclaimers)

**Who doesn't need this**: Simple agents and directory-only agents work fine without modules!

**Implementation**:

1. **Create module infrastructure**:
   - `module_loader.py`: Account→System resolution logic
   - `module_selector.py`: Keyword-based module selection
   - Reuse `config_loader.py` cascade logic

2. **Create initial module library**:
   - System-level modules (`backend/config/prompt_modules/`):
     - `shared/hipaa_compliance.md`: Federal law (universal)
     - `shared/tone_guidelines.md`: Best practices
     - `medical/clinical_disclaimers.md`: Standard disclaimers
   - Account-level modules (`backend/config/agent_configs/{account}/modules/`):
     - `medical/emergency_protocols.md`: Wyckoff ER numbers (account-specific)
     - `administrative/billing_policies.md`: Wyckoff insurance accepted
     - `administrative/appointment_scheduling.md`: Wyckoff hours

3. **Update `generate_full_prompt()`**:
   - Add module selection logic (keyword-based)
   - Load and compose selected modules
   - Account-first resolution (account override → system fallback)

4. **Add `prompting.modules` config section**:
   ```yaml
   prompting:
     modules:
       enabled: true  # Explicit opt-in
       keyword_mappings:
         - keywords: ["emergency", "urgent", "911"]
           module: "medical/emergency_protocols.md"
           priority: 10
         - keywords: ["billing", "insurance", "payment"]
           module: "administrative/billing_policies.md"
           priority: 1
   ```

5. **Pilot with Wyckoff**:
   - Enable for wyckoff_info_chat1
   - Test emergency query handling
   - Measure quality improvement (thumbs up/down)

**Testing**:
- Agents without `prompting.modules.enabled` work as before
- Module selection matches keywords correctly
- Account modules override system modules
- Emergency queries get appropriate protocols

**Deliverable**:
- Context-aware emergency handling
- Billing/insurance information injection
- HIPAA compliance disclaimers
- 40% quality improvement for complex queries

**Code Reuse**: Leverage `config_loader.py` cascade logic (200 lines), reuse prompt composition patterns (100 lines)

**See Also**: "Code Organization" section (lines 1427-1712) for detailed file structure and implementation strategy

**Backward compatibility**: Existing agents work unchanged. Modules are 100% opt-in.

---

### Phase 5: MCP Integration (External Tool Ecosystem)

**Risk**: Medium (depends on MCP server stability + Python client library availability)  
**Value**: Extensibility for GitHub, Slack, weather, custom integrations

**Prerequisites**: 
- **Research Python MCP client library** - official package needs investigation
  - Check PyPI for `mcp`, `model-context-protocol`, or similar
  - Review Anthropic's official documentation
  - May need custom HTTP+SSE implementation if no official client exists

**Why**: Enable dynamic integration with external services via MCP protocol. Agents can use GitHub for issue tracking, Slack for notifications, weather for patient travel advice, etc.

**Implementation**:

1. **Research & select MCP client library**:
   - Investigate available Python packages
   - Test connection to sample MCP server
   - Document installation and usage patterns

2. **Implement `MCPTool` class**:
   - `tool_type = f"mcp:{server_name}"`
   - `generate_documentation()`: Auto-generate from MCP JSON schemas
   - `get_module_hints()`: Suggest MCP-specific modules
   - Redis caching for tool schemas

3. **Add MCP server discovery** (`backend/app/main.py`):
   ```python
   async def initialize_mcp_tools():
       """Discover and register MCP servers at startup."""
       mcp_config = load_mcp_config()
       
       for server_name, server_config in mcp_config.items():
           client = await connect_to_mcp_server(server_name, server_config)  # Using researched library
           mcp_tool = MCPTool(server_name, client)
           tool_registry.register(mcp_tool)
   ```

4. **Add MCP configuration support**:
   ```yaml
   # agent_configs/{account}/{instance}/config.yaml
   tools:
     mcp:
       enabled: true
       servers:
         - name: "github"
           connection_string: "stdio://github-mcp-server"
         - name: "slack"
           connection_string: "sse://slack-mcp-server:3000"
   ```

5. **Create MCP module library**:
   - `backend/config/prompt_modules/mcp/`:
     - `github_best_practices.md`: When to create issues vs. PRs
     - `slack_messaging_guidelines.md`: Professional communication
     - `weather_context.md`: How to integrate weather into responses

6. **Add MCP-specific keyword mappings**:
   ```yaml
   prompting:
     modules:
       keyword_mappings:
         - keywords: ["code", "repository", "issue", "bug"]
           module: "mcp/github_best_practices.md"
           required_tool: "mcp:github"
         - keywords: ["notify", "alert", "message"]
           module: "mcp/slack_messaging_guidelines.md"
           required_tool: "mcp:slack"
   ```

7. **Pilot with 1-2 MCP servers**:
   - Start with GitHub (issue creation) or Slack (notifications)
   - Test auto-generated tool docs from MCP schemas
   - Verify graceful handling of MCP server unavailability

**Testing**:
- MCP servers register dynamically at startup
- Tool docs auto-generated from JSON schemas
- Agents without MCP config unchanged
- MCP server failures don't crash agent

**Deliverable**:
- GitHub integration (issue creation, repo search)
- Slack integration (notifications, alerts)
- Weather integration (patient travel advice)
- Extensible framework for custom MCP servers

**Challenges**:
- MCP server reliability (external dependencies)
- Tool documentation quality (depends on MCP schema quality)
- Latency overhead (external API calls)

**Mitigation**:
- Graceful degradation (agent works if MCP unavailable)
- Cache MCP tool schemas (reduce discovery overhead)
- Monitor MCP call latency/success rates in Logfire

**See Also**: "MCP Integration Strategy" section (lines 1602-1705) for detailed implementation

**Backward compatibility**: MCP optional. Non-MCP agents work as before.

---

## Implementation Summary

| Phase | Risk | Value | Dependencies |
|-------|------|-------|--------------|
| **1: Pydantic AI Native Toolsets** | Low | Foundation for multi-tool support | None |
| **2: Schema Standardization** | Low | Multi-directory support | Phase 1 |
| **3: Multi-Tool + Caching** | Low | Vector search + 70% cost savings | Phase 1-2 |
| **4: Modular Prompts** | Low | 40% quality improvement | Phase 1-3 |
| **5: MCP Integration** | Medium | External tool ecosystem | Phase 1 |

**Expected Results**: 50-60% overall quality gain

**Incremental Value Delivery**:
- After Phase 1: Multi-tool infrastructure ready (directory + vector + MCP support)
- After Phase 2: Phone directory ready (schema-driven multi-directory selection)
- After Phase 3: 70% cost reduction + vector search working
- After Phase 4: Emergency protocols + billing context working
- After Phase 5: GitHub/Slack integrations working

**Strategy Validation**: See `memorybank/analysis/advanced-agent-strategies.md` for alternative approaches evaluated (agent chaining, few-shot learning, query preprocessing) and why incremental evolution of `simple_chat` is recommended over building v2.

---

## Future Enhancements

**Note**: These enhancements are deferred post-MVP (after Phase 1-5). Implement only if data shows keyword-based approaches are insufficient.

---

### Dynamic Instructions (Message Prepending)

**Status**: Deferred - Evaluate after Phase 4 (Modular Prompts) deployed

**Problem**: Some context cannot be predetermined at agent creation time and needs runtime injection. Examples:
- Emergency/urgent queries requiring immediate priority handling
- Follow-up questions needing conversation history awareness
- Time-sensitive instructions (e.g., "Pharmacy closes in 30 minutes")

**Solution**: Inject context-specific instructions directly into the user message before agent processing, using **config-based approach** (same pattern as keyword_mappings).

---

**Configuration** (opt-in via agent config):

```yaml
prompting:
  dynamic_instructions:
    enabled: true
    
    # Config-based instruction mappings (NOT hardcoded in Python!)
    instruction_mappings:
      - keywords: ["emergency", "urgent", "911", "chest pain", "bleeding", "unconscious"]
        instruction: "[URGENT: Provide emergency contact first (911 + ER direct line)]"
        priority: 10
        condition: "keyword_match"
      
      - keywords: ["pharmacy", "medication", "prescription"]
        instruction: "[INFO: Check pharmacy hours before responding]"
        priority: 5
        condition: "keyword_match"
      
      # Special condition types (not keyword-based)
      - condition: "is_followup"        # Detects follow-up from history
        instruction: "[CONTEXT: User following up on previous answer]"
        priority: 1
      
      - condition: "message_count_gt_5" # Long conversation
        instruction: "[CONTEXT: Extended conversation, user may need summary]"
        priority: 1
```

---

**Implementation Approach** (simplified - keyword-only MVP):

```python
# backend/app/agents/simple_chat.py

async def simple_chat_stream(message: str, message_history: list, agent_config: dict, ...):
    """Apply dynamic instructions based on config."""
    
    # Read instruction mappings from config (not hardcoded!)
    dynamic_config = agent_config.get("prompting", {}).get("dynamic_instructions", {})
    
    if not dynamic_config.get("enabled"):
        result = await agent.run(message, ...)
        return result
    
    # Collect applicable instructions (keyword-based only for MVP)
    instructions = []
    instruction_mappings = dynamic_config.get("instruction_mappings", [])
    
    for mapping in instruction_mappings:
        keywords = mapping.get("keywords", [])
        instruction_text = mapping.get("instruction")
        priority = mapping.get("priority", 1)
        
        # Simple keyword match
        if any(kw in message.lower() for kw in keywords):
            instructions.append((instruction_text, priority))
    
    # Sort by priority and inject
    if instructions:
        instructions.sort(key=lambda x: x[1], reverse=True)
        instruction_text = "\n".join([inst[0] for inst in instructions])
        message = f"{instruction_text}\n\n{message}"
    
    result = await agent.run(message, ...)
```

---

**Simplified Approach Benefits**:
- ✅ **Keyword-only matching** - Simple, fast, deterministic (same as Phase 1)
- ✅ **Domain-agnostic code** - No hardcoded emergency/pharmacy logic
- ✅ **Multi-tenant flexibility** - Accounts customize instructions via config
- ✅ **No deployment needed** - Add/change instructions via config only
- ✅ **Consistent with Phase 1** - Same keyword pattern as module selection

**Deferred to post-MVP** (see [dynamic-prompting-alternatives.md](./dynamic-prompting-alternatives.md)):
- Complex condition types (is_followup, message_count_gt_N, time_based, custom)
- Conversation history analysis
- Time-of-day routing

**Why Optional**: Adds message length overhead and may conflict with base prompt if not carefully designed. Most agents don't need this level of runtime control.

**When to Reconsider**: If agents frequently miss critical context cues or need runtime priority adjustments based on query urgency.

**Key Difference from Modular Prompts (Phase 4)**:
- **Modular Prompts**: Adds content to system prompt (loaded once at agent creation)
- **Dynamic Instructions**: Injects directives into user message (applied per request, runtime context)

---

### Advanced Module Selection

**Status**: Deferred - Evaluate after Phase 4 if keyword matching insufficient

**Problem**: Simple keyword matching may miss nuanced queries or context that requires more sophisticated intent classification.

**Proposed Enhancements**:

1. **LLM-Based Intent Classifier**:
   - Use lightweight LLM call to classify query intent before module selection
   - More accurate than keyword matching for complex queries
   - Trade-off: Added latency and cost per request

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

## Code Organization

### Pythonic Design Principles

**1. Leverage Pydantic AI Native Features**:
```python
# ❌ DON'T: Custom abstractions
class DirectoryTool(AgentTool): ...
tool_registry.register(DirectoryTool())

# ✅ DO: Use FunctionToolset
from pydantic_ai import FunctionToolset
directory_toolset = FunctionToolset(tools=[search_directory])
```

**2. Functional Composition Over Classes**:
```python
# ❌ DON'T: Stateful classes for simple operations
class ModuleSelector:
    def __init__(self, config):
        self.config = config
    def select(self, query):
        ...

# ✅ DO: Pure functions
def select_modules(query: str, config: dict) -> list[str]:
    return [m for m in config["modules"] if matches(query, m)]
```

**3. Use Dataclasses for Structured Data**:
```python
from dataclasses import dataclass

@dataclass
class ModuleConfig:
    enabled: bool
    keyword_mappings: list[dict]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ModuleConfig':
        return cls(**data)  # Automatic validation
```

**4. Error Handling with Context Managers**:
```python
# ✅ Graceful degradation pattern
async def load_toolset_safe(name: str, factory) -> FunctionToolset | None:
    try:
        return factory()
    except Exception as e:
        logfire.warning(f"Toolset '{name}' unavailable: {e}")
        return None  # Continue without this tool

# Usage
toolsets = [
    t for t in [
        load_toolset_safe("directory", lambda: FunctionToolset([search_directory])),
        load_toolset_safe("vector", lambda: FunctionToolset([vector_search])),
        load_toolset_safe("mcp", lambda: MCPServerStdio('github')),
    ] if t is not None
]
```

**5. Config-Driven Behavior (Zero Hardcoding)**:
```python
# ✅ Generic, reusable
def load_modules_for_query(query: str, module_config: dict) -> list[str]:
    """Works for ANY domain - medical, legal, financial, etc."""
    q_lower = query.lower()
    mappings = module_config.get("keyword_mappings", [])
    
    return [
        m["module"] 
        for m in mappings 
        if any(kw in q_lower for kw in m.get("keywords", []))
    ]
```

---

### Files by Phase (Simplified Approach)

**Phase 1: Pydantic AI Native Toolsets**
- ✅ NEW: `backend/app/agents/tools/toolsets.py` (~20 lines)
  - Wraps existing `search_directory()` and `vector_search()`
- ✅ MODIFY: `backend/app/agents/simple_chat.py`
  - Add toolset loading logic based on config

**Phase 2: Schema Standardization**
- ✅ MODIFY: `backend/app/agents/tools/prompt_generator.py`
  - Domain-agnostic schema reading
- ✅ MODIFY: `backend/config/directory_schemas/medical_professional.yaml`
  - Add `directory_purpose`, rename keys
- ✅ NEW: `backend/config/directory_schemas/phone_directory.yaml`

**Phase 3: Multi-Tool + Caching**
- ✅ MODIFY: `backend/app/agents/simple_chat.py`
  - Add cache markers to prompt composition
- ⚠️ NO new files (Phase 1 toolsets already support multi-tool)

**Phase 4: Modular Prompts**
- ✅ NEW: `backend/app/agents/tools/module_loader.py` (~80 lines)
  - `load_module(path, account)` with account→system fallback
- ✅ NEW: `backend/app/agents/tools/module_selector.py` (~50 lines)
  - `select_modules(query, config)` - pure function, no state
- ✅ NEW: `backend/config/prompt_modules/` directory structure
- ✅ NEW: `backend/config/agent_configs/{account}/modules/` structure

**Phase 5: MCP Integration**
- ✅ MODIFY: `backend/app/agents/simple_chat.py`
  - Add `MCPServerStdio` to toolsets list
- ⚠️ NO new files (Pydantic AI handles everything)

**Total New Code**: ~150 lines (vs. ~900 with custom approach)

---

### Code Reuse Strategies

**1. Leverage Existing Infrastructure**:
- ✅ `config_loader.py` - parameter cascade (200 lines reused)
- ✅ `prompt_generator.py` - base prompt, directory docs (300 lines reused)
- ✅ `types.py` - Pydantic validation (100 lines reused)

**2. Functional Utilities**:
```python
# backend/app/agents/tools/utils.py

def safe_get(d: dict, *keys, default=None):
    """Safely traverse nested dicts."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, {})
        else:
            return default
    return d if d != {} else default

# Usage: No more try/except KeyError!
enabled = safe_get(config, "tools", "directory", "enabled", default=False)
```

**3. Decorator Pattern for Observability**:
```python
from functools import wraps

def observe_tool_call(func):
    """Auto-log tool executions to Logfire."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with logfire.span(f"tool.{func.__name__}"):
            try:
                result = await func(*args, **kwargs)
                logfire.info(f"{func.__name__} succeeded", result_count=len(result))
                return result
            except Exception as e:
                logfire.error(f"{func.__name__} failed", error=str(e))
                raise
    return wrapper

# Apply to tools
@observe_tool_call
async def search_directory(...): ...
```

---

### Error-Prone Patterns to Avoid

**❌ DON'T: Mutate config dictionaries**:
```python
config["tools"]["directory"]["enabled"] = True  # BAD: Side effects!
```

**✅ DO: Treat configs as immutable**:
```python
from copy import deepcopy
new_config = deepcopy(config)
new_config["tools"]["directory"]["enabled"] = True
```

**❌ DON'T: String concatenation for prompts**:
```python
prompt = base + "\n" + tools + "\n" + modules  # BAD: Error-prone
```

**✅ DO: Use structured composition**:
```python
components = [base, tools, modules]
prompt = "\n\n---\n\n".join(filter(None, components))  # Filters out None/empty
```

**❌ DON'T: Silent failures**:
```python
try:
    module = load_module(path)
except:
    pass  # BAD: Hides errors!
```

**✅ DO: Log and degrade gracefully**:
```python
try:
    module = load_module(path)
except ModuleNotFoundError as e:
    logfire.warning("Module not found", path=path, error=str(e))
    module = None  # Explicit None, continue
```

---

### Backward Compatibility

All existing agents work unchanged. Each phase is 100% opt-in via config.

---

### Design Principles

**1. Reusability Through Layered Architecture**
- Core utilities work across all agent types
- Configuration-driven behavior (no hardcoded domain logic)
- Shared components with progressive enhancement

**2. Incremental Implementation**
- Each phase builds on previous without breaking changes
- Minimal viable implementation first, optimizations later
- Feature flags for opt-in complexity

**3. Backward Compatibility**
- Existing agents in `agent_configs/` (wyckoff, windriver, agrofresh, prepexcellence, acme, default_account) work unchanged
- New features require explicit opt-in via config
- Graceful degradation when features not configured

---

### Configuration Organization Principle

**Infrastructure config** (how the app runs) → `app.yaml`:
- Database, Redis, sessions, logging, caching
- LLM provider defaults, embeddings
- Cross-cutting concerns (performance, monitoring)

**Domain-specific config** (how features work) → Separate YAML files:
- `directory_schemas/` - Directory type definitions
- `prompt_modules/` - Prompting rules (validation, token budgets, keyword mappings)

**Instance config** (per-agent settings) → `agent_configs/{account}/{instance}/config.yaml`:
- Agent-specific overrides (model, temperature, tools)
- Prompting config (keyword_mappings, module selection)

**Why separate?**
- Keeps `app.yaml` focused on infrastructure (easier operations)
- Makes domain features portable/modular (can extract prompting system)
- Follows same pattern as `directory_schemas/` (domain rules in separate files)

---

### File Structure

```
backend/app/agents/tools/
  # Existing files (no changes to underlying implementations)
  directory_tools.py            # Existing - search_directory() function
  vector_tools.py               # Existing - vector_search() function
  prompt_generator.py           # Existing
    - load_base_prompt()        
    - generate_directory_tool_docs()    # Update (Phase 1): make domain-agnostic
  
  # NEW: Simple wrapper file using Pydantic AI native features
  toolsets.py                   # NEW (Phase 1)
    - directory_toolset = FunctionToolset(tools=[search_directory])
    - vector_toolset = FunctionToolset(tools=[vector_search])
  
  # NEW: Module system for context-aware prompts
  module_loader.py              # NEW (Phase 4): Account→System resolution
  module_selector.py            # NEW (Phase 4): Keyword-based selection

backend/config/
  app.yaml                      # Add prompting.recommended_module_size_tokens
  
  prompt_modules/               # NEW (Phase 4): System-level modules
    shared/
      hipaa_compliance.md
      tone_guidelines.md
    medical/
      clinical_disclaimers.md
  
  directory_schemas/
    medical_professional.yaml   # Update (Phase 2): Add directory_purpose, rename to formal_terms
    phone_directory.yaml        # NEW (Phase 2): Hospital departments
  
  agent_configs/{account}/
    modules/                    # NEW (Phase 4): Account-specific modules
      medical/emergency_protocols.md
      administrative/billing_policies.md
    
    {instance}/
      system_prompt.md          # Existing
      config.yaml               # Update (Phase 4): Add prompting.modules section
```

**Key Simplifications**:
- ❌ NO base_tool.py, tool_registry.py (use Pydantic AI's native FunctionToolset)
- ❌ NO custom DirectoryTool, VectorTool wrappers (FunctionToolset does this)
- ❌ NO mcp_tool.py (use Pydantic AI's native MCPServerStdio)
- ✅ ONE simple toolsets.py file wraps existing tools
- ✅ Underlying directory_tools.py and vector_tools.py unchanged

**See "Migration Path" section (lines 1138-1405) for detailed phase-by-phase implementation plan.**

---

## Related Architecture

**Schema-Driven Directory System** (Foundation):
- `directory_schemas/*.yaml` - Domain knowledge for directory types
- `prompt_generator.py` - Schema-driven tool doc generation (MUST remain domain-agnostic)
- `directory_service.py` - Schema-driven search implementation

**Agent Infrastructure**:
- `agent_base.py` - Agent creation and initialization
- `simple_chat.py` - Agent execution and message handling
- `config_loader.py` - Configuration cascade and parameter resolution (reused for modules)

**Key Principle**: All domain knowledge lives in YAML files, never in Python code.

---

## Summary: Architecture Layers

```
┌───────────────────────────────────────────────────────────────────────┐
│ User Query: "Find a kidney doctor and research heart disease"        │
└───────────────────────────────────────────────────────────────────────┘
                                  ↓
┌───────────────────────────────────────────────────────────────────────┐
│ Dynamic Prompting (Proposed - Tool-Agnostic)                         │
│ • Base prompt (static)                                                │
│ • Tool documentation (ALL enabled tools via ToolRegistry)            │
│   - Directory tool docs (schema-driven)                              │
│   - Vector search docs (semantic search guidance)                    │
│   - MCP tool docs (GitHub, Slack, etc. - auto-generated)            │
│ • Tool selection guide (if multiple tools available)                 │
│ • Context modules (keyword + tool hints: billing, emergency, etc.)   │
│ • Dynamic instructions (optional - message prepending if urgent)     │
└───────────────────────────────────────────────────────────────────────┘
                                  ↓
┌───────────────────────────────────────────────────────────────────────┐
│ Tool Registry (NEW - Plugin Architecture)                            │
│ • DirectoryTool: Wraps EXISTING directory_tools.py                   │
│ • VectorTool: Wraps EXISTING vector_tools.py                         │
│ • MCPTool: Dynamic wrapper for MCP servers (GitHub, Slack, etc.)    │
│ • Custom tools: Extensible via AgentTool interface                   │
└───────────────────────────────────────────────────────────────────────┘
                                  ↓
┌───────────────────────────────────────────────────────────────────────┐
│ LLM Agent: Multi-Tool Execution                                      │
│ 1. Calls search_directory(filters={"specialty": "Nephrology"})      │
│    → Uses synonym mappings from medical_professional.yaml            │
│ 2. Calls search_knowledge_base(query="heart disease treatment")     │
│    → Vector search over hospital policies/procedures                 │
│ 3. Combines results with emergency protocols module (if detected)    │
└───────────────────────────────────────────────────────────────────────┘
                                  ↓
┌───────────────────────────────────────────────────────────────────────┐
│ Service Layer: Tool Execution                                        │
│ • Directory Service: JSONB search for specialists                    │
│ • Vector Service: Semantic retrieval from embeddings                 │
│ • MCP Clients: External tool calls (GitHub API, Slack API, etc.)    │
└───────────────────────────────────────────────────────────────────────┘
```

**Key Principles**:
- **Schemas** = Domain knowledge for specific tool types (directory, vector, MCP)
- **Modules** = Context enhancements that work across tools
- **Tool Registry** = Plugin architecture for extensibility (directory, vector, MCP, custom)
- **Progressive Enhancement** = Simple → Directory → Multi-Tool → Dynamic

---
