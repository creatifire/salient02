## Priority 6: Profile Fields Configuration & Database Schema & Profile Capture 📋

**📋 Related Documents**:
- **Design Decisions & Clarifications**: [`PRIORITY-6-CLARIFICATIONS.md`](PRIORITY-6-CLARIFICATIONS.md) - All design decisions, Q&A, and rationale
- **Main Epic Document**: [`0017-simple-chat-agent.md`](0017-simple-chat-agent.md#priority-2d-profile-configuration--schema) - Priority 2D & 2F sections
- **Milestone Plan**: [`0000-approach-milestone-01.md`](0000-approach-milestone-01.md) - Priority 6 task list

---

FEATURE 0017-006 - Profile Configuration Infrastructure

**System Prompt Assembly Architecture:**

```
FINAL SYSTEM PROMPT = 
  [1. Critical Rules - tool_selection_hints.md]
  + [2. Base System Prompt - system_prompt.md]
  + [3. Directory Documentation - generate_directory_tool_docs()]
  + [4. Profile Capture Hints - profile_capture_hints.md] ← NEW
  + [5. Other Prompt Modules - selected modules]
```

**Profile Capture Prompt Integration:**
When `tools.profile_capture.enabled: true`, ProfileSchemaLoader generates a `profile_capture_hints.md` module containing:
- Required/optional fields from profile.yaml
- Semantic hints per field (when to capture)
- Capture guidelines (how to ask naturally)
- Validation rules

This module is injected into system prompt via the existing modular prompt mechanism.

**File-Level Cascade for profile.yaml:**
*(See [CLARIFICATIONS.md - Question 1](PRIORITY-6-CLARIFICATIONS.md#1-profileyaml-file-location-) for design rationale)*

1. **Agent instance level** (highest priority): `backend/config/agent_configs/{account}/{instance}/profile.yaml`
2. **System fallback** (default): `backend/config/prompt_modules/system/profile.yaml`

If instance-level profile.yaml exists, use it. Otherwise, fall back to system default (basic email/phone capture).

**Field Types Specification:**
*(See [CLARIFICATIONS.md - Field Types Table](PRIORITY-6-CLARIFICATIONS.md#field-types-specification-) for complete specification)*

- `email`: Email address validation (regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
- `phone`: Phone number validation (regex: `^\+?[1-9]\d{1,14}$`)
- `string`: Free-form text (single line)
- `text`: Multi-line text
- `enum`: Select from predefined values
- `date`: ISO 8601 date format (YYYY-MM-DD)
- `address`: Structured address fields
- `url`: URL validation (regex: `^https?://`)
- `number`: Numeric value
- `boolean`: true/false

**Required Metadata per Field:**
- `type`: Field type (required)
- `required`: true/false (required)
- `description`: Human-readable description (required)
- `validation`: Regex pattern for validation (required for email, phone, url)
- `examples`: List of example values (required)
- `semantic_hints`: LLM guidance on when to capture (required)

**Optional Metadata:**
- `enum_values`: List of allowed values (required if type=enum)
- `min_length`, `max_length`: String length constraints
- `min_value`, `max_value`: Numeric value constraints
- `default`: Default value if not provided

---

- [ ] 0017-006-001 - TASK - Profile Schema Infrastructure
  - [x] 0017-006-001-01 - CHUNK - Add profile_capture config to agent config.yaml
    - SUB-TASKS:
      - Add `tools.profile_capture.enabled` boolean to agent config.yaml
      - Add `tools.profile_capture.schema_file` (default: "profile.yaml")
      - Follow same pattern as other tools (vector_search, directory)
      - Configuration loaded via agent config loader (per-agent-instance)
    - AUTOMATED-TESTS:
      - `test_profile_config_loads()` - Verify profile config loads from agent YAML ✅
      - `test_profile_config_defaults()` - Verify default schema_file is "profile.yaml" ✅
      - `test_profile_disabled_by_default()` - Verify tool disabled unless explicitly enabled ✅
    - MANUAL-TESTS:
      - Review config.yaml structure for all agent instances ✅
      - Test config loading: `python -c "from app.services.config_loader import get_agent_config; print(get_agent_config('wyckoff/wyckoff_info_chat1'))"` ✅
    - STATUS: ✅ Complete (commit d8252e2) — Profile tool enabled/disabled per agent instance
    - LOCATION: `backend/config/agent_configs/{account_slug}/{instance_slug}/config.yaml`
    - EXAMPLE CONFIG:
      ```yaml
      tools:
        profile_capture:
          enabled: true
          schema_file: "profile.yaml"  # Default - can be customized
      ```
  
  - [ ] 0017-006-001-02 - CHUNK - Create ProfileSchemaLoader class
    - **PURPOSE**: Load and validate profile.yaml with file-level cascade
    - **DESIGN RATIONALE**: See [CLARIFICATIONS.md - Question 5](PRIORITY-6-CLARIFICATIONS.md#5-field-type-validation-) for validation approach and class design decisions
    
    - **CLASS DESIGN**:
      ```python
      # backend/app/services/profile_schema_loader.py
      
      class ProfileSchemaLoader:
          """
          Load and validate profile schemas from YAML files.
          
          Follows DirectoryImporter pattern but with profile-specific logic:
          - File-level cascade: instance → system fallback
          - Field type validation with regex support
          - Prompt module generation for system prompt integration
          """
          
          @staticmethod
          def load_schema(
              account_slug: str,
              instance_slug: str,
              schema_file: str = "profile.yaml"
          ) -> Optional[Dict]:
              """
              Load profile schema with file-level cascade.
              
              Cascade order:
              1. backend/config/agent_configs/{account}/{instance}/{schema_file}
              2. backend/config/prompt_modules/system/{schema_file}
              
              Returns None if neither file exists.
              """
          
          @staticmethod
          def validate_schema(schema: Dict) -> tuple[bool, List[str]]:
              """
              Validate profile schema structure and field definitions.
              
              Checks:
              - Required top-level keys: profile_version, fields
              - Required field metadata: type, required, description, validation, examples, semantic_hints
              - Field type validity (email, phone, string, text, enum, date, address, url, number, boolean)
              - Regex pattern validity for validation rules
              - Enum values presence when type=enum
              
              Returns: (is_valid, error_messages)
              """
          
          @staticmethod
          def generate_prompt_module(schema: Dict) -> str:
              """
              Generate profile_capture_hints.md content from schema.
              
              Creates a markdown module containing:
              - Required/optional fields list
              - Semantic hints per field
              - Capture guidelines
              - Example scenarios
              - Validation rules summary
              
              Returns: Markdown content as string
              """
          
          @staticmethod
          def validate_field_value(
              field_name: str,
              field_value: str,
              field_schema: Dict
          ) -> tuple[bool, Optional[str]]:
              """
              Validate a captured field value against schema.
              
              Applies:
              - Regex validation (if specified)
              - Length constraints (min_length, max_length)
              - Value constraints (min_value, max_value)
              - Enum validation (if type=enum)
              
              Returns: (is_valid, error_message)
              """
      ```
    
    - SUB-TASKS:
      - Create `backend/app/services/profile_schema_loader.py`
      - Implement `load_schema()` with file-level cascade
      - Implement `validate_schema()` with comprehensive checks
      - Implement `generate_prompt_module()` for system prompt integration
      - Implement `validate_field_value()` for runtime validation
      - Add error handling with Logfire logging for malformed YAML
      - Handle missing files gracefully (if profile_capture disabled)
      - Add path resolution utilities (similar to DirectoryImporter)
    - AUTOMATED-TESTS: `backend/tests/unit/test_profile_schema_loader.py`
      - `test_load_schema_instance_level()` - Load from agent instance folder
      - `test_load_schema_system_fallback()` - Fall back to system default
      - `test_load_schema_missing_both()` - Returns None when both missing
      - `test_validate_schema_valid()` - Valid schema passes validation
      - `test_validate_schema_missing_fields()` - Detect missing required metadata
      - `test_validate_schema_invalid_field_type()` - Reject invalid field types
      - `test_validate_schema_invalid_regex()` - Detect malformed regex patterns
      - `test_generate_prompt_module()` - Generate valid markdown content
      - `test_validate_field_value_email()` - Test email validation
      - `test_validate_field_value_phone()` - Test phone validation
      - `test_validate_field_value_enum()` - Test enum validation
      - `test_malformed_yaml_logging()` - Verify Logfire error logging
    - MANUAL-TESTS:
      - Create test profile.yaml with all field types
      - Test loading: `python -c "from app.services.profile_schema_loader import ProfileSchemaLoader; print(ProfileSchemaLoader.load_schema('wyckoff', 'wyckoff_info_chat1'))"`
      - Verify cascade: rename instance file, confirm system fallback works
      - Test malformed YAML: check Logfire logs for error details
      - Verify generated prompt module is valid markdown
    - STATUS: Planned — Profile schema loading following DirectoryImporter pattern
    - LOCATION: `backend/app/services/profile_schema_loader.py`
  
  - [ ] 0017-006-001-03 - CHUNK - Create system default profile.yaml
    - SUB-TASKS:
      - Create `backend/config/prompt_modules/system/profile.yaml`
      - Define basic email + phone capture schema
      - Add semantic_hints for each field
      - Add capture_hints section
      - Add validation regex patterns
      - Add examples for both fields
      - Document as fallback template for all agents
    - AUTOMATED-TESTS:
      - `test_system_profile_loads()` - System default loads correctly
      - `test_system_profile_validates()` - Schema passes validation
    - MANUAL-TESTS:
      - Verify file exists and is valid YAML
      - Test loading as fallback when instance file missing
    - STATUS: Planned — System-level default profile schema
    - LOCATION: `backend/config/prompt_modules/system/profile.yaml`
  
  - [ ] 0017-006-001-04 - CHUNK - Create profile.yaml for hospital sites
    - SUB-TASKS:
      - Create `backend/config/agent_configs/wyckoff/wyckoff_info_chat1/profile.yaml`
      - Create `backend/config/agent_configs/windriver/windriver_info_chat1/profile.yaml`
      - Define fields: relationship_to_patient, health_issue, mailing_address, email, phone
      - Add semantic_hints for each field (hospital visitor context)
      - Add capture_hints specific to healthcare interactions
      - Add validation patterns for all fields
      - Include examples for hospital visitor scenarios
    - AUTOMATED-TESTS:
      - `test_hospital_profile_loads()` - Schema loads correctly
      - `test_hospital_fields_valid()` - All field definitions valid
      - `test_hospital_validation_patterns()` - Regex patterns compile
    - MANUAL-TESTS:
      - Load each hospital profile, verify structure
      - Test field validation with sample data
    - STATUS: Planned — Hospital visitor profile capture
  
  - [ ] 0017-006-001-05 - CHUNK - Create profile.yaml for PrepExcellence
    - SUB-TASKS:
      - Create `backend/config/agent_configs/prepexcellence/prepexcel_info_chat1/profile.yaml`
      - Define fields: relationship_to_student, student_name, mailing_address, email, phone, current_grade, colleges_interested_in
      - Add semantic_hints for student prep/college counseling context
      - Add capture_hints specific to educational consultations
      - Add validation patterns and examples
    - AUTOMATED-TESTS:
      - `test_prepexcel_profile_loads()` - Schema loads correctly
      - `test_prepexcel_fields_valid()` - All field definitions valid
    - MANUAL-TESTS:
      - Load PrepExcellence profile, verify structure
      - Test field validation with sample data
    - STATUS: Planned — Student prep profile capture
  
  - [ ] 0017-006-001-06 - CHUNK - Create profile.yaml for AgroFresh
    - SUB-TASKS:
      - Create `backend/config/agent_configs/agrofresh/agro_info_chat1/profile.yaml`
      - Define fields: name, email, phone, products_interested_in, produce_types, delivery_location
      - Add semantic_hints for agricultural product inquiries
      - Add capture_hints specific to agrotech customer interactions
      - Add validation patterns and examples
    - AUTOMATED-TESTS:
      - `test_agrofresh_profile_loads()` - Schema loads correctly
      - `test_agrofresh_fields_valid()` - All field definitions valid
    - MANUAL-TESTS:
      - Load AgroFresh profile, verify structure
      - Test field validation with sample data
    - STATUS: Planned — Agrotech customer profile capture
  
  - [ ] 0017-006-001-07 - CHUNK - Disable profile capture for default_account/simple_chat1
    - SUB-TASKS:
      - Set `tools.profile_capture.enabled: false` in simple_chat1 config.yaml
      - Add comment explaining this is intentional (testing/demo without profile capture)
      - Verify agent works without profile_capture tool registered
    - AUTOMATED-TESTS:
      - `test_simple_chat1_no_profile_tool()` - Verify tool not registered when disabled
    - MANUAL-TESTS:
      - Send messages to simple_chat1, verify no profile capture prompts appear
    - STATUS: Planned — Selective profile capture enablement

- [ ] 0017-006-002 - TASK - Migrate Profiles Table to JSONB
  - [ ] 0017-006-002-01 - CHUNK - Add JSONB fields to profiles table
    - SUB-TASKS:
      - Add `required_profile_fields` JSONB column (stores schema's required fields)
      - Add `captured_profile_fields` JSONB column (stores actual captured data)
      - Add `required_fields_updated_at` timestamp column (tracks schema freshness)
      - Create Alembic migration script
      - Update SQLAlchemy ORM model (Profile class)
    - AUTOMATED-TESTS:
      - `test_profile_jsonb_fields()` - Verify JSONB columns work
      - `test_profile_migration()` - Test migration runs successfully
    - MANUAL-TESTS:
      - Run migration on dev database
      - Verify columns created correctly
    - STATUS: Planned — JSONB storage for flexible profiles
  
  - [ ] 0017-006-002-02 - CHUNK - Remove hardcoded profile columns
    - SUB-TASKS:
      - Migrate existing data to JSONB fields (data preservation script)
      - Remove email, phone, and other hardcoded columns via Alembic migration
      - Update SQLAlchemy ORM models to only use JSONB fields
      - Update all Profile queries in codebase to use JSONB accessors
      - Test backward compatibility (if needed)
    - AUTOMATED-TESTS:
      - `test_profile_data_preserved()` - Verify no data loss during migration
      - `test_profile_queries_work()` - All existing queries updated correctly
    - MANUAL-TESTS:
      - Run migration, verify no data loss
      - Test all profile-related queries
    - STATUS: Planned — Clean schema using JSONB

---

FEATURE 0017-012 - Profile Capture Tool & Prompt Integration

**System Prompt Assembly with Profile Hints:**

The profile capture prompt module is generated dynamically by ProfileSchemaLoader and injected into the system prompt via the existing modular prompt mechanism.

**DESIGN RATIONALE**: See [CLARIFICATIONS.md - Question 6](PRIORITY-6-CLARIFICATIONS.md#6-system-prompt-assembly-logic-) for complete system prompt assembly logic and integration approach.

**Classes & Methods for System Prompt Assembly:**

```python
# STEP 1-5: Existing prompt assembly (see simple_chat.py lines 118-250)
# - Load critical rules
# - Load base system prompt
# - Append directory documentation

# STEP 6: Append profile capture hints (NEW - position 4)
# Location: backend/app/agents/simple_chat.py (in create_simple_chat_agent function)

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
        # Generate prompt module from schema
        profile_hints = ProfileSchemaLoader.generate_prompt_module(profile_schema)
        system_prompt = system_prompt + "\n\n---\n\n" + profile_hints
        
        logfire.info(
            'agent.profile_hints.injected',
            account=account_slug,
            instance=instance_slug,
            fields_count=len(profile_schema.get('fields', {}))
        )

# STEP 7: Append other prompt modules (existing)
# STEP 8: Create Agent with assembled prompt
```

**Modular Design Summary:**

1. **ProfileSchemaLoader** (`backend/app/services/profile_schema_loader.py`):
   - `load_schema()`: Loads schema with file-level cascade (instance → system)
   - `validate_schema()`: Validates schema structure and field definitions
   - `generate_prompt_module()`: Generates markdown prompt content from schema
   - `validate_field_value()`: Validates captured field values at runtime

2. **Profile Capture Tool** (`backend/app/agents/tools/profile_tools.py`):
   - `capture_profile_field()`: Registered as `@agent.tool` when enabled
   - Uses ProfileSchemaLoader for validation
   - Stores data in captured_profile_fields JSONB
   - Returns validation results to LLM

3. **System Prompt Assembly** (`backend/app/agents/simple_chat.py`):
   - Detects profile_capture enabled in agent config
   - Calls ProfileSchemaLoader.load_schema() + generate_prompt_module()
   - Injects generated prompt at position 4 (after directory docs)
   - Maintains existing modular prompt flow

4. **File Cascade** (in ProfileSchemaLoader.load_schema()):
   - Checks `backend/config/agent_configs/{account}/{instance}/profile.yaml` first
   - Falls back to `backend/config/prompt_modules/system/profile.yaml`
   - Returns None if neither exists (graceful handling)

5. **Error Handling** (throughout):
   *(See [CLARIFICATIONS.md - Question 8](PRIORITY-6-CLARIFICATIONS.md#8-error-handling-) for error handling strategy)*
   - Malformed YAML logged to Logfire with file path and error details
   - Missing files handled gracefully (warning logged, no crash)
   - Invalid schemas prevent tool registration with clear error messages
   - Future: UI will handle configuration validation

---

- [ ] 0017-012-001 - TASK - Profile Capture Agent Tool Implementation
  - [ ] 0017-012-001-01 - CHUNK - Implement @agent.tool for profile capture
    - **PURPOSE**: Register profile capture tool that validates and stores user data
    
    - SUB-TASKS:
      - Create `backend/app/agents/tools/profile_tools.py`
      - Implement `capture_profile_field(ctx, field_name, field_value)` tool function
      - Load profile schema from ProfileSchemaLoader
      - Validate field exists in schema
      - Validate field value using ProfileSchemaLoader.validate_field_value()
      - Store validated data in captured_profile_fields JSONB column
      - Check required_fields_updated_at and refresh if stale (24h threshold)
      - Return success/error message to LLM
      - Add comprehensive Logfire logging
      - Register tool conditionally (only when profile_capture enabled)
    - AUTOMATED-TESTS: `backend/tests/integration/test_profile_capture_tool.py`
      - `test_profile_tool_registered_when_enabled()` - Tool present when enabled
      - `test_profile_tool_not_registered_when_disabled()` - Tool absent when disabled
      - `test_capture_valid_email()` - Successful email capture and storage
      - `test_capture_invalid_email()` - Validation error returned to LLM
      - `test_capture_valid_phone()` - Successful phone capture
      - `test_capture_unknown_field()` - Error for undefined field name
      - `test_profile_data_stored_jsonb()` - Verify database JSONB storage
      - `test_profile_schema_refresh()` - Test stale schema refresh logic
    - MANUAL-TESTS:
      - Enable profile_capture for wyckoff agent
      - Send message: "My email is john@example.com"
      - Verify LLM calls capture_profile_field tool (check logs)
      - Check database: `SELECT captured_profile_fields FROM profiles WHERE session_id='...'`
      - Verify JSONB contains: `{"email": "john@example.com"}`
      - Test invalid email: "My email is invalid"
      - Verify LLM receives validation error message
      - Check Logfire logs for capture events and validation results
    - STATUS: Planned — Agent captures profile during conversation
    - LOCATION: `backend/app/agents/tools/profile_tools.py`
  
  - [ ] 0017-012-001-02 - CHUNK - Integrate profile hints into system prompt assembly
    - **PURPOSE**: Automatically inject profile capture guidance into system prompt
    
    - SUB-TASKS:
      - Modify `create_simple_chat_agent()` in simple_chat.py
      - After directory docs section, check if profile_capture enabled
      - Load profile schema via ProfileSchemaLoader.load_schema()
      - Generate prompt module via ProfileSchemaLoader.generate_prompt_module()
      - Inject generated content at position 4 (after directory, before other modules)
      - Add Logfire logging for profile hints injection (module name, size, fields count)
      - Handle missing schema gracefully (log warning, continue without hints)
      - Update PromptBreakdownService to track profile_hints section
    - AUTOMATED-TESTS: `backend/tests/unit/test_profile_prompt_integration.py`
      - `test_profile_hints_injected_when_enabled()` - Hints appear in assembled prompt
      - `test_profile_hints_absent_when_disabled()` - No hints when disabled
      - `test_profile_hints_position_correct()` - Verify position 4 in prompt
      - `test_missing_schema_graceful()` - Missing schema doesn't crash creation
      - `test_prompt_breakdown_includes_profile()` - Tracking service updated
    - MANUAL-TESTS:
      - Create agent with profile_capture enabled
      - Print assembled system_prompt to console
      - Verify profile_capture_hints section appears after directory docs
      - Verify semantic_hints per field are present in output
      - Verify capture_hints section is present
      - Test with missing profile.yaml, verify agent still created
      - Check Logfire logs for injection events with field count
    - STATUS: Planned — Profile hints guide LLM behavior
    - LOCATION: `backend/app/agents/simple_chat.py` (modify create_simple_chat_agent)

- [ ] 0017-012-002 - TASK - Update User Guide in Memorybank
  - [ ] 0017-012-002-01 - CHUNK - Document profile capture feature
    - SUB-TASKS:
      - Create `memorybank/userguide/profile-capture.md`
      - Explain profile.yaml structure and all field types
      - Document file-level cascade (instance → system fallback)
      - Provide complete examples for each field type
      - Explain semantic_hints and capture_hints purpose
      - Document all validation rules and regex patterns
      - Add troubleshooting section (common errors, solutions)
      - Include configuration examples for different use cases
      - Add migration guide from hardcoded fields to JSONB
    - MANUAL-TESTS:
      - Review documentation for completeness and accuracy
      - Verify all code examples are correct
      - Test troubleshooting steps actually solve problems
      - Get feedback from team on clarity
    - STATUS: Planned — User-facing documentation
    - LOCATION: `memorybank/userguide/profile-capture.md`

