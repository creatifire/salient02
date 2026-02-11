<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Priority 6: Profile Capture - Clarifications & Design Decisions

This document records all design decisions and clarifications for Priority 6 (Profile Fields Configuration & Database Schema & Profile Capture).

## Questions Addressed

### 1. Profile.yaml File Location ✅

**Question**: Where should profile.yaml files be located?

**Answer**: `backend/config/agent_configs/{account_slug}/{agent_instance_slug}/profile.yaml`

**File-Level Cascade**:
1. **Instance level** (highest priority): `backend/config/agent_configs/{account}/{instance}/profile.yaml`
2. **System fallback** (default): `backend/config/prompt_modules/system/profile.yaml`

If instance-level file exists, use it. Otherwise, fall back to system default (basic email/phone capture).

---

### 2. Default Account Configuration ✅

**Question**: How should profile capture be configured for default_account?

**Answer**: 
- **simple_chat1**: `profile_capture.enabled: false` (explicitly disabled for testing/demo)
- Use system default profile.yaml as fallback template (email + phone capture)

**Config.yaml Switch Enhancement**:
```yaml
tools:
  profile_capture:
    enabled: true
    schema_file: "profile.yaml"  # NEW - allows custom naming
```

---

### 3. Task Reordering ✅

**Question**: Can we reorder and renumber tasks?

**Answer**: Yes, approved. Tasks have been restructured:
- **0017-006-001**: Profile Schema Infrastructure (7 chunks)
- **0017-006-002**: Migrate Profiles Table to JSONB (2 chunks)
- **0017-012-001**: Profile Capture Agent Tool Implementation (2 chunks)
- **0017-012-002**: Update User Guide in Memorybank (1 chunk)

---

### 4. Schema Structure Similarities ✅

**Question**: Should profile.yaml be literally identical to directory_schemas structure?

**Answer**: No - same **mechanism**, not identical **structure**. 

- **Same mechanism**: YAML-based configuration with field definitions, validation rules, and hints
- **Different structure**: Profile schemas have profile-specific sections (capture_hints, semantic_hints per field, etc.)
- **Key difference**: Profile schemas focus on LLM guidance for natural conversation capture, while directory schemas focus on structured data storage

---

### 5. Field Type Validation ✅

**Question**: How to validate fields? Use regex? Need separate class?

**Answer**: 
- **Use regex validation** for field types (email, phone, url, etc.)
- **Create separate ProfileSchemaLoader class** (`backend/app/services/profile_schema_loader.py`)
- **Class also assembles profile capture prompt** for system prompt integration
- **Methods**:
  - `load_schema()`: Load with file-level cascade
  - `validate_schema()`: Validate structure and field definitions
  - `generate_prompt_module()`: Generate markdown content for system prompt
  - `validate_field_value()`: Runtime validation of captured values

---

### 6. System Prompt Assembly Logic ✅

**Question**: How will profile capture hints be integrated into system prompt?

**Answer**: See detailed architecture in updated plan. Summary:

```
FINAL SYSTEM PROMPT = 
  [1. Critical Rules - tool_selection_hints.md]
  + [2. Base System Prompt - system_prompt.md]
  + [3. Directory Documentation - generate_directory_tool_docs()]
  + [4. Profile Capture Hints - ProfileSchemaLoader.generate_prompt_module()] ← NEW
  + [5. Other Prompt Modules - selected modules]
```

**Integration Code** (in `create_simple_chat_agent()`):
```python
profile_config = (instance_config or {}).get("tools", {}).get("profile_capture", {})
if profile_config.get("enabled", False):
    from app.services.profile_schema_loader import ProfileSchemaLoader
    
    schema_file = profile_config.get("schema_file", "profile.yaml")
    profile_schema = ProfileSchemaLoader.load_schema(
        account_slug=account_slug,
        instance_slug=instance_slug,
        schema_file=schema_file
    )
    
    if profile_schema:
        profile_hints = ProfileSchemaLoader.generate_prompt_module(profile_schema)
        system_prompt = system_prompt + "\n\n---\n\n" + profile_hints
```

---

### 7. Unit Tests ✅

**Question**: Should we add unit tests? What about test cleanup?

**Answer**: 
- **Yes, add unit tests** for each feature as part of the task breakdown
- **Test cleanup added as Priority 9A** - comprehensive test suite audit and maintenance
- Each chunk in Priority 6 now includes AUTOMATED-TESTS section specifying:
  - Test file location
  - Specific test methods
  - What each test validates

**Priority 9A - Test Suite Cleanup**:
- 0099-001-001: Audit and categorize all existing tests
- 0099-001-002: Remove obsolete and duplicate tests
- 0099-001-003: Add missing test coverage (including Priority 6)

---

### 8. Error Handling ✅

**Question**: How to handle malformed profile.yaml files?

**Answer**: 
- **Log to Logfire** with comprehensive error details (file path, YAML error, line number if available)
- **Eventually handled in UI** - future admin interface will validate configuration files before saving
- **Current behavior**: Agent creation continues with warning if profile.yaml is malformed (graceful degradation)

**Error Logging Example**:
```python
try:
    schema = yaml.safe_load(f)
except yaml.YAMLError as e:
    logfire.error(
        'service.profile_schema_loader.yaml_error',
        account=account_slug,
        instance=instance_slug,
        file_path=str(profile_path),
        error=str(e),
        error_line=getattr(e, 'problem_mark', {}).get('line')
    )
    return None
```

---

### 9. Module Design Clarity ✅

**Question**: Need clear order, sequence, and classes+methods for system prompt assembly.

**Answer**: Documented in updated plan. Key components:

**1. ProfileSchemaLoader** (`backend/app/services/profile_schema_loader.py`):
- `load_schema(account, instance, schema_file)` → Dict | None
- `validate_schema(schema)` → tuple[bool, List[str]]
- `generate_prompt_module(schema)` → str
- `validate_field_value(field_name, value, schema)` → tuple[bool, str | None]

**2. Profile Capture Tool** (`backend/app/agents/tools/profile_tools.py`):
- `capture_profile_field(ctx, field_name, field_value)` → str

**3. System Prompt Assembly** (`backend/app/agents/simple_chat.py`):
- Existing: Steps 1-5 (critical rules, base prompt, directory docs, other modules)
- New: Step 4 inserts profile hints after directory docs

**4. File Cascade** (in ProfileSchemaLoader.load_schema()):
- Check instance path first
- Fall back to system path
- Return None if neither exists

**5. Error Handling** (throughout):
- Logfire logging with context
- Graceful fallbacks
- Clear error messages

---

## Field Types Specification ✅

**Question**: Complete list of supported field types?

**Answer**: 

| Type | Validation | Required Metadata | Optional Metadata |
|------|-----------|-------------------|-------------------|
| `email` | Regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` | type, required, description, validation, examples, semantic_hints | min_length, max_length, default |
| `phone` | Regex: `^\+?[1-9]\d{1,14}$` | type, required, description, validation, examples, semantic_hints | min_length, max_length, default |
| `url` | Regex: `^https?://` | type, required, description, validation, examples, semantic_hints | default |
| `string` | None (free-form) | type, required, description, examples, semantic_hints | min_length, max_length, default |
| `text` | None (multi-line) | type, required, description, examples, semantic_hints | min_length, max_length, default |
| `enum` | Must be in enum_values | type, required, description, examples, semantic_hints, **enum_values** | default |
| `date` | ISO 8601 (YYYY-MM-DD) | type, required, description, validation, examples, semantic_hints | min_value, max_value, default |
| `number` | Numeric validation | type, required, description, examples, semantic_hints | min_value, max_value, default |
| `boolean` | true/false | type, required, description, examples, semantic_hints | default |
| `address` | Structured (TBD) | type, required, description, examples, semantic_hints | default |

**Required Metadata (all fields)**:
- `type`: Field type from table above
- `required`: true/false
- `description`: Human-readable description
- `examples`: List of example values
- `semantic_hints`: LLM guidance on when to capture

**Conditionally Required**:
- `validation`: Regex pattern (required for email, phone, url, date)
- `enum_values`: List of allowed values (required if type=enum)

**Optional Metadata**:
- `min_length`, `max_length`: String length constraints
- `min_value`, `max_value`: Numeric value constraints  
- `default`: Default value if not provided

---

## Outstanding Issues: NONE ✅

All questions have been addressed:
1. ✅ Path structure confirmed
2. ✅ Default account configuration clarified
3. ✅ Task reordering approved
4. ✅ Schema structure differences explained
5. ✅ Field validation approach defined (regex + ProfileSchemaLoader)
6. ✅ System prompt assembly logic documented
7. ✅ Unit tests added + test cleanup priority created
8. ✅ Error handling defined (Logfire + graceful degradation)
9. ✅ Module design documented with clear classes and methods
10. ✅ ProfileSchemaLoader location confirmed (Option A: separate file)
11. ✅ Missing profile.yaml handling defined (file-level cascade with system fallback)
12. ✅ Field type specification completed (10 types with metadata requirements)

---

## Next Steps

1. **Review updated plan** in `0017-simple-chat-agent.md` (Priority 6 section)
2. **Review updated milestone** in `0000-approach-milestone-01.md` (Priority 6 renumbered/expanded)
3. **Begin implementation** starting with:
   - 0017-006-001-01: Add profile_capture config to agent config.yaml
   - 0017-006-001-02: Create ProfileSchemaLoader class
   - 0017-006-001-03: Create system default profile.yaml

---

## Files Updated

1. `memorybank/project-management/0017-simple-chat-agent.md` - Priority 6 section completely rewritten with:
   - System prompt assembly architecture diagram
   - File-level cascade specification
   - Field types specification table
   - Complete class design for ProfileSchemaLoader
   - Detailed implementation plan for all chunks
   - Automated and manual tests for each chunk
   - Clear integration with existing modular prompt system

2. `memorybank/project-management/0000-approach-milestone-01.md` - Priority 6 updated with:
   - Expanded task breakdown (0017-006-001 now has 7 chunks)
   - New task: 0017-012-002 (User Guide documentation)
   - Priority 9A added: Test Suite Cleanup & Maintenance

3. `memorybank/project-management/PRIORITY-6-CLARIFICATIONS.md` - This document (NEW)
   - Records all design decisions
   - Answers to all 12 questions
   - Field types specification
   - No outstanding issues

---

**Status**: All ambiguities resolved. Ready for implementation.

