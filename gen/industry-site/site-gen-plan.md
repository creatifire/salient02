# Industry Site Generator - Implementation Plan

LLM-powered workflow to generate industry-specific demo sites with product catalogs, directory data, and chatbot integration.

**Architecture**: Research → Config → Product Schema → Directory Data → Content Generation → Validation → Astro Conversion

**Integration**: Salient chat API, Directory schemas, RAG/Pinecone, Backend logger

**Documentation**:
- [Workflow Design](site-gen-design.md) - 12-script sequence, data flow, validation
- [Code Architecture](site-gen-code-org.md) - Classes, modules, interfaces
- [Automated Testing](site-gen-auto-tests.md) - Testing conventions and best practices

## Testing Approach

Each task includes **both manual and automated tests**:

### Manual Verification
- Quick verification commands using Python REPL
- Immediate feedback during development
- Listed under "Manual Verification" in each task

### Automated Tests
- pytest-based test suite following [testing conventions](site-gen-auto-tests.md)
- Unit tests for each module (`tests/unit/`)
- Integration tests for multi-module workflows (`tests/integration/`)
- Run with: `pytest tests/unit/test_<module>.py`
- Each task should add corresponding automated tests

**Best Practice**: Write automated tests alongside implementation, verify with manual commands during development.

## Development Approaches

### Sequential Development
Execute features in order. Each script uses actual output from previous scripts.

**Workflow**: F01 → F02 → F03 → F04 → F05 → F06 → S01 → S02 → S03 → ... → S12

**Test Case**: AgTech vertical with existing research files

### Parallel Development
Develop scripts independently using sample data.

**Requirements**: Create sample input data for each script (tasks included below)

**Workflow**: Foundation features (F01-F06) first, then scripts (S01-S12) in parallel

## Foundation Work

### Feature F01: Core Infrastructure

**Purpose**: Configuration, state management, error handling, logging

**Dependencies**: None

**Reference**: [Core Classes](site-gen-code-org.md#core-classes) in code architecture

#### Tasks

**[x] F01-T1: Implement ConfigLoader Class**

Create configuration loader with environment variable substitution and validation.

- Implementation per [ConfigLoader](site-gen-code-org.md#configloader) specification
- Load YAML configuration
- Substitute environment variables from `.env`
- Validate configuration structure
- Provide dot-notation access to config values

**Manual Verification**:
```bash
cd gen/industry-site
python -c "from lib.config.config_loader import ConfigLoader; \
config = ConfigLoader('agtech/site-gen-config.yaml').load(); \
print(config['company']['name'])"
```
- Verify: Prints company name from config
- Verify: Environment variables substituted (check `llm.api_key`)
- Verify: Invalid config raises `ConfigValidationError`

**Automated Tests**:
Create `tests/unit/test_config_loader.py` with:
- `test_loads_valid_config()` - Load valid config successfully
- `test_env_var_substitution()` - Environment variables substituted
- `test_missing_required_field_raises_error()` - Validation errors caught
- `test_dot_notation_access()` - Dot notation access works
- `test_property_accessors()` - Property methods work
- Run: `pytest tests/unit/test_config_loader.py -v`

See [testing conventions](site-gen-auto-tests.md) for details.

---

**[x] F01-T2: Implement StateManager Class**

Create state manager for tracking progress across scripts.

- Implementation per [StateManager](site-gen-code-org.md#statemanager) specification
- Load/create site-gen-state.yaml
- Track script completion
- Store/retrieve state data
- Save state with timestamps

**Manual Verification**:
```bash
python -c "from lib.config.state_manager import StateManager; \
state = StateManager('agtech/site-gen-state.yaml'); \
state.load(); \
state.set('test', 'value'); \
state.mark_script_complete('test_script'); \
print(state.get('test')); \
print(state.is_script_complete('test_script'))"
```
- Verify: state.yaml created/updated
- Verify: State values persisted
- Verify: Script completion tracked
- Verify: Timestamps updated

**Automated Tests**:
Create `tests/unit/test_state_manager.py` with:
- `test_creates_new_state_file()` - Creates state file if missing
- `test_loads_existing_state()` - Loads existing state correctly
- `test_set_and_get_values()` - Store and retrieve state values
- `test_mark_script_complete()` - Track script completion
- `test_is_script_complete()` - Check completion status
- `test_timestamps_updated()` - Verify timestamps on save
- Run: `pytest tests/unit/test_state_manager.py -v`

---

**[x] F01-T3: Implement Error Handling**

Create custom exceptions and error handling utilities.

- Implementation per [Custom Exceptions](site-gen-code-org.md#custom-exceptions) specification
- Define exception hierarchy
- Implement error handling decorator
- Configure logging for errors

**Manual Verification**:
```bash
python -c "from lib.errors.exceptions import *; \
from lib.errors.handlers import handle_errors; \
@handle_errors(reraise=False, default_return='handled'); \
def test_func(): raise ConfigError('test'); \
print(test_func())"
```
- Verify: Custom exceptions defined
- Verify: Error decorator catches and logs errors
- Verify: Error messages clear and actionable

**Automated Tests**:
Create `tests/unit/test_exceptions.py` with:
- `test_exception_hierarchy()` - All exceptions inherit from SiteGenError
- `test_config_error_raised()` - ConfigError can be raised and caught
- `test_validation_error_message()` - ConfigValidationError has clear message
- `test_llm_error_types()` - LLMError and LLMRetryExhausted work correctly
- Run: `pytest tests/unit/test_exceptions.py -v`

---

**[CANCELLED] F01-T4: Integrate Backend Logger**

**Status**: Cancelled in favor of F01-T5 (industry-specific file logging)

**Rationale**:
- Standard Python logging (F01-T5) provides sufficient functionality
- Console + file logging meets all requirements without backend dependencies
- Simpler architecture - scripts operate independently
- No Logfire configuration or setup required
- Can add Logfire integration later if distributed tracing needed

**Original Plan** (preserved for reference):
- Leverage existing backend logfire for structured logging
- Implementation per [Logging](site-gen-code-org.md#logging) specification
- Import backend logger, configure for site generator, test structured logging

---

**[x] F01-T5: Implement File-Based Logging**

Configure industry-specific file logging with dual output (console + file).

- Create `IndustryLogger` class for file + console logging
- Auto-create `<industry>/logs/` directory
- Filename format: `<industry>_<script_num>_<timestamp>.log`
- Timestamp format: `YYYYMMDD_HHMMSS`
- Dual output: console (INFO+) and file (DEBUG+)
- Structured log format with timestamps

**Manual Verification**:
```bash
python -c "from lib.logging.logger import setup_industry_logger; \
logger = setup_industry_logger('agtech', '01_init_config'); \
logger.info('Test info message'); \
logger.error('Test error message'); \
import os; \
print('Log file created:', os.path.exists('agtech/logs'))"
```
- Verify: Log file created in `agtech/logs/` directory
- Verify: Filename matches pattern `agtech_01_init_config_YYYYMMDD_HHMMSS.log`
- Verify: Messages appear in both console and file
- Verify: File contains timestamps and log levels

**Automated Tests**:
Create `tests/unit/test_industry_logger.py` with:
- `test_creates_log_directory()` - Creates industry logs directory
- `test_log_file_naming()` - Filename matches expected pattern
- `test_dual_output()` - Logs to both console and file
- `test_multiple_loggers()` - Multiple script loggers work independently
- `test_log_levels()` - Different log levels (DEBUG, INFO, ERROR) work
- Run: `pytest tests/unit/test_industry_logger.py -v`

---

**Feature F01 Verification**:
1. Load config from `agtech/site-gen-config.yaml`
2. Initialize state manager
3. Trigger and catch custom exception
4. Setup industry logger and write log messages
5. Verify all logs appear in console and file
6. All five modules work together without errors

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- No integration errors

---

### Feature F02: LLM Client & Retry Logic

**Purpose**: Unified LLM interface with exponential backoff retry

**Dependencies**: F01 (Core Infrastructure)

**Reference**: [LLM Integration](site-gen-code-org.md#llm-integration) in code architecture

#### Tasks

**[x] F02-T1: Implement Retry Logic**

Create exponential backoff decorator for LLM calls.

- Implementation per [Retry Logic](site-gen-code-org.md#retry-logic) specification
- Exponential backoff with configurable parameters
- Log retry attempts
- Raise LLMRetryExhausted after max attempts

**Manual Verification**:
```bash
python -c "from lib.llm.retry import exponential_backoff; \
import time; \
@exponential_backoff(max_retries=2, base_delay=0.1); \
def flaky_func(): \
    if not hasattr(flaky_func, 'count'): flaky_func.count = 0; \
    flaky_func.count += 1; \
    if flaky_func.count < 3: raise Exception('fail'); \
    return 'success'; \
print(flaky_func())"
```
- Verify: Function retries on failure
- Verify: Exponential delay between retries
- Verify: Success after retries
- Verify: Exhausted exception after max retries

**Automated Tests**:
Create `tests/unit/test_retry.py` with:
- `test_retry_succeeds_on_first_attempt()` - No retry if successful
- `test_retry_succeeds_after_failures()` - Retry until success
- `test_exponential_backoff_delays()` - Verify exponential delay timing
- `test_max_retries_exhausted()` - Raises LLMRetryExhausted after max
- `test_retry_with_custom_params()` - Custom retry parameters work
- Run: `pytest tests/unit/test_retry.py -v`

---

**[x] F02-T2: Implement LLMClient Class**

Create unified LLM client for OpenRouter API.

- Implementation per [LLMClient](site-gen-code-org.md#llmclient) specification
- Initialize OpenAI client with OpenRouter base URL
- Implement chat() method with retry logic
- Handle tool calling responses
- Track usage statistics
- Provide convenience methods

**Manual Verification**:
```bash
# Requires OPENROUTER_API_KEY in .env
python -c "from lib.llm.client import LLMClient; \
client = LLMClient(api_key='${OPENROUTER_API_KEY}'); \
response = client.generate_text('Say hello', model='anthropic/claude-haiku-4.5'); \
print(response)"
```
- Verify: Successful API call to OpenRouter
- Verify: Response content returned
- Verify: Usage statistics logged
- Verify: Retry on transient failures

**Automated Tests**:
Create `tests/unit/test_llm_client.py` with:
- `test_client_initialization()` - Client initializes with API key
- `test_generate_text_mocked()` - Mock API call returns text (use pytest-mock)
- `test_chat_with_messages()` - Chat method processes messages correctly
- `test_usage_tracking()` - Usage statistics tracked
- `test_retry_on_api_error()` - Retry logic invoked on API errors
- `test_tool_calling_response()` - Tool calling responses handled
- Run: `pytest tests/unit/test_llm_client.py -v`

Mark with `@pytest.mark.llm` for tests requiring real API calls.

---

**[ ] F02-T3: Create Prompt Management System**

Implement external prompt storage and loading.

- Create `lib/llm/prompts/` directory structure
- Implement `loader.py` per [Prompt Management](site-gen-code-org.md#prompt-management) specification
- Create subdirectories: research, generation, analysis, validation, system
- Create placeholder prompt files for all categories

**Manual Verification**:
```bash
# Test prompt loader
python -c "from lib.llm.prompts.loader import load_prompt; \
from pathlib import Path; \
# Create test prompt first
test_dir = Path('lib/llm/prompts/test'); \
test_dir.mkdir(exist_ok=True); \
(test_dir / 'sample.md').write_text('Hello {name}!'); \
result = load_prompt('test', 'sample', {'name': 'World'}); \
print(result)"
```
- Verify: Prompt loads from file
- Verify: Variable substitution works
- Verify: Missing file raises FileNotFoundError
- Verify: Missing variable raises KeyError

**Manual Verification - System Prompts**:
```bash
python -c "from lib.llm.prompts.loader import load_system_prompt; \
from pathlib import Path; \
# Create test system prompt
sys_dir = Path('lib/llm/prompts/system'); \
sys_dir.mkdir(parents=True, exist_ok=True); \
(sys_dir / 'researcher.md').write_text('You are a research assistant.'); \
result = load_system_prompt('researcher'); \
print(result)"
```
- Verify: System prompt loads correctly
- Verify: No variables needed for system prompts

**Automated Tests**:
Create `tests/unit/test_prompt_loader.py` with:
- `test_load_prompt_with_variables()` - Variable substitution works
- `test_load_prompt_without_variables()` - Load without substitution
- `test_missing_prompt_file_raises_error()` - FileNotFoundError for missing
- `test_missing_variable_raises_error()` - KeyError for missing variable
- `test_load_system_prompt()` - System prompts load correctly
- `test_prompt_directory_structure()` - All prompt directories exist
- Run: `pytest tests/unit/test_prompt_loader.py -v`

---

**Feature F02 Verification**:
1. Make real LLM call with retry enabled
2. Load a test prompt with variables
3. Use loaded prompt in LLM call
4. Verify successful response
5. Check logs for call tracking
6. Test with invalid API key (should retry and fail)
7. Verify error handling works

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Real LLM calls work with retry
- Prompt loading and substitution working
- All prompt directories created

---

### Feature F03: Research Tools

**Purpose**: Exa search and Jina Reader integration for industry research

**Dependencies**: F01 (Core Infrastructure), F02 (LLM Client)

**Reference**: [Research Tools](site-gen-design.md#research-tools) in design document

#### Tasks

**[ ] F03-T1: Implement Exa Search Client**

Create Exa API integration for company/product search.

- Refer to [Exa Search](site-gen-design.md#research-tools) implementation
- Initialize Exa client
- Search for industry companies
- Extract and structure results
- Handle API errors

**Manual Verification**:
```bash
# Requires EXA_API_KEY in .env
python -c "from lib.research.exa_client import search_companies; \
results = search_companies('agtech', '${EXA_API_KEY}'); \
print(f'Found {len(results)} companies'); \
print(results[0])"
```
- Verify: Returns company list
- Verify: At least 10 results
- Verify: Results contain URLs
- Verify: Error handling for rate limits

**Automated Tests**:
Create `tests/unit/test_exa_client.py` with:
- `test_search_companies_mocked()` - Mock API returns structured results
- `test_search_companies_error_handling()` - Handles API errors gracefully
- `test_result_structure()` - Results have required fields (name, url)
- Mark with `@pytest.mark.llm` for real API tests
- Run: `pytest tests/unit/test_exa_client.py -v`

---

**[ ] F03-T2: Implement Jina Reader**

Create Jina Reader API integration for web scraping.

- Refer to [Jina Reader](site-gen-design.md#research-tools) implementation
- Make requests to Jina API
- Extract clean markdown content
- Handle authentication
- Parse product information

**Manual Verification**:
```bash
# Requires JINA_API_KEY in .env (optional, has free tier)
python -c "from lib.research.jina_reader import scrape_url; \
content = scrape_url('https://www.deere.com/en/products/', '${JINA_API_KEY}'); \
print(f'Content length: {len(content)}'); \
print(content[:500])"
```
- Verify: Returns markdown content
- Verify: Content is clean (no HTML tags)
- Verify: Works without API key (free tier)
- Verify: Error handling for invalid URLs

**Automated Tests**:
Create `tests/unit/test_jina_reader.py` with:
- `test_scrape_url_mocked()` - Mock API returns markdown content
- `test_clean_markdown_output()` - No HTML tags in output
- `test_invalid_url_handling()` - Handles bad URLs gracefully
- `test_empty_content_handling()` - Handles empty pages
- Mark with `@pytest.mark.llm` for real API tests
- Run: `pytest tests/unit/test_jina_reader.py -v`

---

**[ ] F03-T3: Implement Research Analyzer**

Create functions to analyze and structure research data.

- Parse scraped content for products
- Extract product names and descriptions
- Categorize products
- Generate structured JSON output
- Use LLM for analysis

**Manual Verification**:
```bash
python -c "from lib.research.analyzer import analyze_products; \
from lib.llm.client import LLMClient; \
llm = LLMClient(api_key='${OPENROUTER_API_KEY}'); \
sample_content = 'Products: Tractor X1, Harvester Y2, Drone Z3'; \
products = analyze_products(sample_content, llm); \
print(products)"
```
- Verify: Extracts product information
- Verify: Returns structured data
- Verify: LLM enhances extraction
- Verify: Handles empty/invalid content

**Automated Tests**:
Create `tests/unit/test_research_analyzer.py` with:
- `test_analyze_products_with_mocked_llm()` - Mock LLM extraction
- `test_extract_product_names()` - Basic extraction works
- `test_categorize_products()` - Products categorized correctly
- `test_empty_content_handling()` - Handles empty input gracefully
- `test_structured_json_output()` - Output format correct
- Run: `pytest tests/unit/test_research_analyzer.py -v`

---

**Feature F03 Verification**:
1. Search for "agtech companies" with Exa
2. Scrape top 3 company URLs with Jina
3. Analyze content to extract products
4. Verify at least 20 products found
5. Check product data structure is valid

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Real research pipeline works end-to-end

---

### Feature F04: I/O Utilities

**Purpose**: File, CSV, YAML, markdown operations

**Dependencies**: F01 (Core Infrastructure)

**Reference**: [Shared Utilities](site-gen-code-org.md#shared-utilities) in code architecture

#### Tasks

**[ ] F04-T1: Implement File Operations**

Create file read/write and directory utilities.

- Implementation per [File Operations](site-gen-code-org.md#file-operations) specification
- Ensure directory creation
- Read/write text files
- List files with glob patterns
- Handle encoding properly

**Manual Verification**:
```bash
python -c "from lib.io.file_ops import *; \
ensure_dir('test_output'); \
write_text('test_output/test.txt', 'Hello World'); \
content = read_text('test_output/test.txt'); \
files = list_files('test_output', '*.txt'); \
print(f'Content: {content}'); \
print(f'Files: {files}')"
```
- Verify: Directory created
- Verify: File written and read correctly
- Verify: Glob patterns work
- Verify: UTF-8 encoding handled

**Automated Tests**:
Create `tests/unit/test_file_ops.py` with:
- `test_ensure_dir_creates_directory()` - Directory creation
- `test_write_and_read_text()` - File write/read cycle
- `test_list_files_glob()` - Glob pattern matching
- `test_utf8_encoding()` - UTF-8 handling with special chars
- `test_read_nonexistent_file()` - Error handling for missing files
- Run: `pytest tests/unit/test_file_ops.py -v`

---

**[ ] F04-T2: Implement CSV Operations**

Create CSV read/write and validation functions.

- Implementation per [CSV Operations](site-gen-code-org.md#csv-operations) specification
- Read CSV to list of dicts
- Write list of dicts to CSV
- Validate CSV structure
- Handle headers properly

**Manual Verification**:
```bash
python -c "from lib.io.csv_ops import *; \
data = [{'name': 'Product1', 'price': '100'}, {'name': 'Product2', 'price': '200'}]; \
write_csv('test_output/products.csv', data, ['name', 'price']); \
loaded = read_csv('test_output/products.csv'); \
print(loaded); \
validate_csv_structure('test_output/products.csv', ['name', 'price'])"
```
- Verify: CSV file created
- Verify: Data round-trips correctly
- Verify: Headers included
- Verify: Validation detects missing fields

**Automated Tests**:
Create `tests/unit/test_csv_ops.py` with:
- `test_write_and_read_csv()` - Write/read cycle preserves data
- `test_csv_headers()` - Headers written correctly
- `test_empty_csv()` - Handles empty data
- `test_special_characters_in_csv()` - Handles commas, quotes in data
- `test_validate_csv_structure()` - Validation function works
- Run: `pytest tests/unit/test_csv_ops.py -v`

---

**[ ] F04-T3: Implement YAML Operations**

Create YAML read/write functions.

- Implementation per [YAML Operations](site-gen-code-org.md#yaml-operations) specification
- Read YAML to dict
- Write dict to YAML
- Handle nested structures
- Pretty formatting

**Manual Verification**:
```bash
python -c "from lib.io.yaml_ops import *; \
data = {'company': {'name': 'Test', 'industry': 'agtech'}, 'count': 100}; \
write_yaml('test_output/config.yaml', data); \
loaded = read_yaml('test_output/config.yaml'); \
print(loaded)"
```
- Verify: YAML file created
- Verify: Data round-trips correctly
- Verify: Nested structures preserved
- Verify: Human-readable formatting

**Automated Tests**:
Create `tests/unit/test_yaml_ops.py` with:
- `test_write_and_read_yaml()` - Write/read cycle preserves data
- `test_nested_structures()` - Nested dicts/lists work
- `test_empty_yaml()` - Handles empty data
- `test_yaml_formatting()` - Output is human-readable
- `test_read_invalid_yaml()` - Error handling for malformed YAML
- Run: `pytest tests/unit/test_yaml_ops.py -v`

---

**Feature F04 Verification**:
1. Create test directory
2. Write and read files, CSVs, YAML
3. Validate all operations work
4. Clean up test directory
5. No errors encountered

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- All I/O operations functional

---

### Feature F05: Validation Modules

**Purpose**: Schema, link, data consistency validation

**Dependencies**: F01 (Core Infrastructure), F04 (I/O Utilities)

**Reference**: [Validation](site-gen-design.md#validation) in design document

#### Tasks

**[ ] F05-T1: Implement Schema Validator**

Create CSV-to-schema validation functions.

- Implementation per [Schema Validator](site-gen-code-org.md#schema-validator) specification
- Load schema YAML
- Validate CSV against schema
- Check required/optional fields
- Generate validation report

**Manual Verification**:
```bash
python -c "from lib.validation.schema_validator import validate_csv_against_schema; \
from pathlib import Path; \
report = validate_csv_against_schema( \
    Path('../../backend/config/directory_schemas/product.yaml'), \
    Path('test_output/products.csv')); \
print(report)"
```
- Verify: Validation report generated
- Verify: Required fields checked
- Verify: Errors detected for invalid data
- Verify: Report is actionable

**Automated Tests**:
Create `tests/unit/test_schema_validator.py` with:
- `test_validate_valid_csv()` - Valid CSV passes validation
- `test_missing_required_field()` - Detects missing required fields
- `test_extra_fields_allowed()` - Extra fields don't fail validation
- `test_validation_report_structure()` - Report has correct structure
- `test_multiple_errors()` - Reports all errors, not just first
- Run: `pytest tests/unit/test_schema_validator.py -v`

---

**[ ] F05-T2: Implement Link Validator**

Create markdown link validation functions.

- Implementation per [Link Validator](site-gen-code-org.md#link-validator) specification
- Extract markdown links
- Check link targets exist
- Report broken links
- Skip external URLs

**Manual Verification**:
```bash
# Create test markdown files first
python -c "from lib.validation.link_validator import validate_all_links; \
from lib.io.file_ops import write_text, ensure_dir; \
ensure_dir('test_output/content'); \
write_text('test_output/content/page1.md', '[Link](page2.md)'); \
write_text('test_output/content/page2.md', 'Content'); \
report = validate_all_links(Path('test_output/content')); \
print(report)"
```
- Verify: Links validated
- Verify: Broken links detected
- Verify: Valid links pass
- Verify: Report lists all issues

**Automated Tests**:
Create `tests/unit/test_link_validator.py` with:
- `test_validate_valid_links()` - Valid links pass
- `test_detect_broken_links()` - Broken links reported
- `test_extract_markdown_links()` - Link extraction works
- `test_skip_external_urls()` - External URLs skipped
- `test_relative_path_resolution()` - Relative paths resolved correctly
- Run: `pytest tests/unit/test_link_validator.py -v`

---

**[ ] F05-T3: Implement Data Validator**

Create data consistency validation functions.

- Check product references in CSVs
- Validate relationships
- Verify data integrity
- Generate consistency report

**Manual Verification**:
```bash
python -c "from lib.validation.data_validator import validate_product_references; \
report = validate_product_references( \
    products_csv='test_output/products.csv', \
    cross_sell_csv='test_output/cross_sell.csv'); \
print(report)"
```
- Verify: Product IDs validated
- Verify: Broken references detected
- Verify: Valid references pass
- Verify: Report is comprehensive

**Automated Tests**:
Create `tests/unit/test_data_validator.py` with:
- `test_validate_valid_references()` - Valid references pass
- `test_detect_invalid_references()` - Invalid product IDs detected
- `test_relationship_count_limits()` - Relationship counts validated
- `test_referential_integrity()` - All references resolve
- `test_empty_data_handling()` - Handles empty CSVs gracefully
- Run: `pytest tests/unit/test_data_validator.py -v`

---

**Feature F05 Verification**:
1. Create sample product CSV
2. Create sample cross-sell CSV with valid/invalid refs
3. Create sample markdown with valid/broken links
4. Run all validators
5. Verify all validation reports accurate

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- All validation functions work

---

### Feature F06: Generation Modules

**Purpose**: Product, directory, page, schema generation functions

**Dependencies**: F01 (Core Infrastructure), F02 (LLM Client), F04 (I/O Utilities)

**Reference**: [Generation Module Examples](site-gen-code-org.md#generation-module-examples) in code architecture

#### Tasks

**[ ] F06-T1: Implement Product Generator**

Create product name and description generation functions.

- Implementation per [Product Generator](site-gen-code-org.md#product-generator) specification
- Generate realistic product names
- Distribute across categories
- Create descriptions
- Return structured data

**Manual Verification**:
```bash
python -c "from lib.generation.product_generator import generate_product_names; \
from lib.llm.client import LLMClient; \
llm = LLMClient(api_key='${OPENROUTER_API_KEY}'); \
real_products = ['Tractor X', 'Harvester Y']; \
categories = ['Equipment', 'Software']; \
products = generate_product_names(real_products, categories, 10, llm); \
print(f'Generated {len(products)} products'); \
print(products[0])"
```
- Verify: Generates requested count
- Verify: Products have name, category, description
- Verify: Distributed across categories
- Verify: Names sound realistic

**Automated Tests**:
Create `tests/unit/test_product_generator.py` with:
- `test_generate_product_names_mocked()` - Mock LLM generates products
- `test_product_count()` - Generates correct number
- `test_product_structure()` - Products have required fields
- `test_category_distribution()` - Products distributed across categories
- `test_realistic_names()` - Names follow pattern of real products
- Run: `pytest tests/unit/test_product_generator.py -v`

---

**[ ] F06-T2: Implement Directory Generator**

Create generic directory CSV generation function.

- Implementation per [Directory Generator](site-gen-code-org.md#directory-generator) specification
- Load schema dynamically
- Generate coherent entries
- Maintain product references
- Write valid CSV

**Manual Verification**:
```bash
python -c "from lib.generation.directory_generator import generate_directory_csv; \
from lib.llm.client import LLMClient; \
from pathlib import Path; \
llm = LLMClient(api_key='${OPENROUTER_API_KEY}'); \
products = [{'id': 'p1', 'name': 'Product1', 'category': 'Cat1'}]; \
config = {'company': {'name': 'Test Co'}}; \
result = generate_directory_csv( \
    Path('../../backend/config/directory_schemas/cross_sell.yaml'), \
    products, llm, Path('test_output/cross_sell.csv'), config); \
print(result)"
```
- Verify: CSV generated
- Verify: Follows schema structure
- Verify: Product references valid
- Verify: Data is coherent

**Automated Tests**:
Create `tests/unit/test_directory_generator.py` with:
- `test_generate_directory_csv_mocked()` - Mock LLM generates CSV
- `test_schema_loading()` - Loads schema correctly
- `test_product_references()` - Product references valid
- `test_csv_structure()` - Follows schema structure
- `test_entry_count()` - Generates requested number of entries
- Run: `pytest tests/unit/test_directory_generator.py -v`

---

**[ ] F06-T3: Implement Page Generator**

Create markdown page generation functions.

- Generate product pages with frontmatter
- Generate category pages
- Generate site pages (home, about, contact)
- Include internal links

**Manual Verification**:
```bash
python -c "from lib.generation.page_generator import generate_product_page; \
from lib.llm.client import LLMClient; \
llm = LLMClient(api_key='${OPENROUTER_API_KEY}'); \
product = {'name': 'Test Product', 'category': 'Equipment', 'description': 'A test'}; \
page_content = generate_product_page(product, llm); \
print(page_content[:500])"
```
- Verify: Markdown with frontmatter generated
- Verify: Content includes product details
- Verify: Links formatted correctly
- Verify: Frontmatter is valid YAML

**Automated Tests**:
Create `tests/unit/test_page_generator.py` with:
- `test_generate_product_page_mocked()` - Mock LLM generates page
- `test_frontmatter_structure()` - Frontmatter is valid YAML
- `test_markdown_formatting()` - Content is valid markdown
- `test_internal_links()` - Links formatted correctly
- `test_category_page_generation()` - Category pages generated
- `test_site_page_generation()` - Home/about/contact pages generated
- Run: `pytest tests/unit/test_page_generator.py -v`

---

**Feature F06 Verification**:
1. Generate 10 products with LLM
2. Generate cross_sell CSV for those products
3. Generate markdown page for first product
4. Verify all outputs valid and coherent
5. Check product references maintained

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- All generation functions work
- LLM integration successful

---

## Script Implementation

### Feature S01: Initialize Configuration (Script 01)

**Purpose**: Gather requirements and create site-gen-config.yaml

**Dependencies**: F01 (Core Infrastructure)

**Reference**: [Script 1](site-gen-design.md#script-1-initialize-configuration) in design document

#### Tasks

**[ ] S01-T1: Create Sample Data (Optional for Parallel Development)**

Create sample research files for testing without real data.

- Create sample agtech-case-study.md
- Create sample agtech-strategic-brief.md
- Provides test data for independent development

**Manual Verification**:
```bash
ls agtech/research/*.md
```
- Verify: Sample research files exist
- Verify: Files contain meaningful content
- Note: Skip if using real AgTech research files

**Automated Tests**:
Create `tests/functional/test_script_01.py` with:
- `test_config_file_creation()` - Script creates valid config file
- `test_state_file_initialization()` - State file created correctly
- `test_config_validation()` - Generated config passes validation
- `test_env_var_substitution()` - Environment variables in config
- Mark with `@pytest.mark.functional` and `@pytest.mark.slow`
- Run: `pytest tests/functional/test_script_01.py -v`

---

**[ ] S01-T2: Implement Interactive Prompts**

Create CLI interface to gather configuration requirements.

- Prompt for company name, tagline, description
- Prompt for product count, categories
- Prompt for relationship depth
- Collect all required config values

**Manual Verification**:
```bash
python 01_init_config.py agtech
# Enter test values when prompted
```
- Verify: Prompts appear for all required fields
- Verify: Input validation works
- Verify: Can provide values via CLI args (optional)

---

**[ ] S01-T3: Generate Company Profile from Research**

Use LLM to analyze research files and generate company profile.

- Read research markdown files
- Send to LLM for analysis
- Extract company name, tagline, description
- Return structured profile

**Manual Verification**:
```bash
python -c "from lib.llm.client import LLMClient; \
from lib.io.file_ops import read_text; \
llm = LLMClient(api_key='${OPENROUTER_API_KEY}'); \
research = read_text('agtech/research/agtech-strategic-brief.md'); \
# (Profile generation function call here)
print('Profile generated from research')"
```
- Verify: Reads all research files
- Verify: LLM generates appropriate company profile
- Verify: Profile matches research content

---

**[ ] S01-T4: Write Configuration File**

Create and write site-gen-config.yaml with all settings.

- Combine prompts and generated profile
- Structure per [Configuration Template](site-gen-design.md#configuration-template)
- Include LLM model settings
- Include generation parameters
- Write to agtech/site-gen-config.yaml

**Manual Verification**:
```bash
cat agtech/site-gen-config.yaml
python -c "from lib.config.config_loader import ConfigLoader; \
config = ConfigLoader('agtech/site-gen-config.yaml').load(); \
print('Config loaded successfully'); \
print(f\"Company: {config['company']['name']}\")"
```
- Verify: File created with proper structure
- Verify: All sections present
- Verify: ConfigLoader can load it
- Verify: Values match inputs

---

**[ ] S01-T5: Initialize State Tracking**

Create site-gen-state.yaml and mark script complete.

- Initialize StateManager
- Create new state file
- Mark script 01 as complete
- Store initial metadata

**Manual Verification**:
```bash
cat agtech/site-gen-state.yaml
python -c "from lib.config.state_manager import StateManager; \
state = StateManager('agtech/site-gen-state.yaml'); \
state.load(); \
print(state.is_script_complete('01_init_config'))"
```
- Verify: State file created
- Verify: Timestamps present
- Verify: Script marked complete
- Verify: Can load and query state

---

**[ ] S01-T6: Integration - Complete Script**

Implement main() function following [Script Structure Template](site-gen-code-org.md#script-structure-template).

- Load dependencies
- Execute all tasks in sequence
- Handle errors gracefully
- Log progress
- Mark complete

**Manual Verification**:
```bash
python 01_init_config.py agtech
# Follow prompts or provide CLI args
```
- Verify: Script runs without errors
- Verify: site-gen-config.yaml created
- Verify: site-gen-state.yaml created
- Verify: Logs show progress
- Verify: Can run script multiple times (skips if complete)

---

**Feature S01 Verification**:
1. Delete agtech/site-gen-config.yaml and site-gen-state.yaml
2. Run `python 01_init_config.py agtech`
3. Verify config file created with valid structure
4. Verify state file tracks completion
5. Run script again - verify it skips (already complete)
6. Review configuration values - checkpoint passed

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Configuration file reviewed and approved (checkpoint)
- Ready for Script 02

---

### Feature S02: Research Industry (Script 02)

**Purpose**: Research real companies and products using Exa and Jina

**Dependencies**: F01, F02, F03, F04, S01

**Reference**: [Script 2](site-gen-design.md#script-2-research-industry) in design document

#### Tasks

**[ ] S02-T1: Create Sample Data (Optional for Parallel Development)**

Create sample site-gen-config.yaml for testing without Script 01.

- Copy template config
- Fill with test values
- Allows independent development

**Manual Verification**:
```bash
cat agtech/site-gen-config.yaml
```
- Verify: Config file exists with valid structure
- Note: Skip if using real output from Script 01

---

**[ ] S02-T2: Search Companies with Exa**

Use Exa API to find top companies in industry.

- Read industry from config
- Load search prompt from `lib/llm/prompts/research/search_companies.md`
- Call Exa search with industry-specific query
- Extract company list with URLs
- Store results

**Manual Verification**:
```bash
python -c "from lib.research.exa_client import search_companies; \
companies = search_companies('agtech', '${EXA_API_KEY}'); \
print(f'Found {len(companies)} companies')"
```
- Verify: At least 10 companies found
- Verify: Each has name and URL
- Verify: Results relevant to agtech

---

**[ ] S02-T3: Scrape Company Pages with Jina**

Use Jina Reader to scrape product pages.

- For each company URL
- Call Jina Reader API
- Extract clean markdown
- Store scraped content

**Manual Verification**:
```bash
# Uses first company from Exa results
python -c "# Scrape logic here
print('Scraped content length:', len(content))"
```
- Verify: Content extracted for each company
- Verify: Markdown is clean (no HTML)
- Verify: Content contains product information

---

**[ ] S02-T4: Extract Products with LLM**

Analyze scraped content to extract product information.

- For each company's content
- Load extraction prompts from `lib/llm/prompts/research/` (extract_products, categorize_products)
- Load system prompt from `lib/llm/prompts/system/researcher.md`
- Send to LLM for analysis
- Extract product names, descriptions, categories
- Structure as JSON
- Deduplicate products

**Manual Verification**:
```bash
python -c "# Product extraction logic
print(f'Extracted {len(products)} products')"
```
- Verify: At least 20 products extracted
- Verify: Products have name, description, category
- Verify: At least 5 distinct categories
- Verify: No obvious duplicates

---

**[ ] S02-T5: Write Research Outputs**

Write companies.json, products-catalog.json, research-summary.md.

- Write structured JSON files
- Generate human-readable summary
- Store in agtech/research/

**Manual Verification**:
```bash
cat agtech/research/companies.json
cat agtech/research/products-catalog.json
cat agtech/research/research-summary.md
python -c "import json; \
data = json.load(open('agtech/research/products-catalog.json')); \
print(f'Products: {len(data)}'); \
print(f'Categories: {len(set(p[\"category\"] for p in data))}')"
```
- Verify: companies.json has list of companies
- Verify: products-catalog.json has 20+ products
- Verify: research-summary.md is readable
- Verify: At least 5 categories identified

---

**[ ] S02-T6: Integration - Complete Script**

Implement main() following script template.

- Load config and state
- Execute research pipeline
- Write all outputs
- Mark complete

**Manual Verification**:
```bash
python 02_research_industry.py agtech
```
- Verify: Script runs without errors
- Verify: All three output files created
- Verify: Minimum validation criteria met (20 products, 5 categories)
- Verify: State updated
- Verify: Logs show progress

---

**Feature S02 Verification**:
1. Delete agtech/research/companies.json, products-catalog.json, research-summary.md
2. Run `python 02_research_industry.py agtech`
3. Verify companies.json has 10+ companies
4. Verify products-catalog.json has 20+ products across 5+ categories
5. Review research-summary.md for quality
6. Check all product data is realistic

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Research outputs meet minimum criteria
- Ready for Script 03

**Automated Tests**:
Create `tests/functional/test_script_02.py` with:
- `test_company_search_and_scraping()` - Companies found and scraped
- `test_product_extraction()` - Products extracted from content
- `test_output_file_creation()` - All output files created
- `test_minimum_data_requirements()` - 20+ products, 5+ categories
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_02.py -v`

---

### Feature S03: Generate Product Schema (Script 03)

**Purpose**: Create product directory CSV as foundation

**Dependencies**: F01, F02, F04, F06, S01, S02

**Reference**: [Script 3](site-gen-design.md#script-3-generate-product-schema) in design document

#### Tasks

**[ ] S03-T1: Create Sample Data (Optional for Parallel Development)**

Create sample products-catalog.json for testing.

- Create sample JSON with 20 products
- Include name, description, category
- Allows independent development

**Manual Verification**:
```bash
cat agtech/research/products-catalog.json
```
- Verify: File exists with valid JSON
- Note: Skip if using real output from Script 02

---

**[ ] S03-T2: Generate Product Categories**

Analyze research and generate category list.

- Read products-catalog.json
- Extract unique categories
- Load categorization prompt from `lib/llm/prompts/research/categorize_products.md`
- Use LLM to organize/refine
- Generate final category list (10 categories)

**Manual Verification**:
```bash
python -c "# Category generation logic
print('Categories:', categories)"
```
- Verify: Exactly 10 categories generated
- Verify: Categories cover all product types
- Verify: Category names clear and professional

---

**[ ] S03-T3: Generate Product Names**

Create realistic product names based on research.

- Read real product names from catalog
- Load product name generation prompt from `lib/llm/prompts/generation/product_names.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- Use LLM to generate similar names
- Generate configured count (default 100)
- Assign to categories
- Create unique IDs

**Manual Verification**:
```bash
python -c "from lib.generation.product_generator import generate_product_names; \
# Generate products
print(f'Generated {len(products)} products')"
```
- Verify: Correct number of products generated
- Verify: Products distributed across all 10 categories
- Verify: All products have unique IDs
- Verify: Names sound realistic

---

**[ ] S03-T4: Write Product CSV**

Write product directory following product.yaml schema.

- Structure per backend/config/directory_schemas/product.yaml
- Include all required fields
- Add tags (optional)
- Write to agtech/data/product.csv

**Manual Verification**:
```bash
cat agtech/data/product.csv
python -c "from lib.io.csv_ops import read_csv; \
from lib.validation.schema_validator import validate_csv_against_schema; \
products = read_csv('agtech/data/product.csv'); \
print(f'Products: {len(products)}'); \
report = validate_csv_against_schema( \
    'agtech/data/product.csv', \
    '../../backend/config/directory_schemas/product.yaml'); \
print('Valid:', report['valid'])"
```
- Verify: CSV file created
- Verify: Correct number of rows
- Verify: All required fields present
- Verify: Validates against product.yaml schema

---

**[ ] S03-T5: Integration - Complete Script**

Implement main() following script template.

- Load config, state, research data
- Generate categories
- Generate products
- Write CSV
- Mark complete

**Manual Verification**:
```bash
python 03_generate_product_schema.py agtech
```
- Verify: Script runs without errors
- Verify: product.csv created and valid
- Verify: All validation checks pass
- Verify: State updated

---

**Feature S03 Verification**:
1. Delete agtech/data/product.csv
2. Run `python 03_generate_product_schema.py agtech`
3. Verify CSV has 100 products (or configured count)
4. Verify 10 categories with products distributed
5. Verify all product IDs unique
6. Verify schema validation passes
7. Product catalog reviewed - checkpoint passed

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Product CSV validated against schema
- Product catalog is foundation for all subsequent scripts

**Automated Tests**:
Create `tests/functional/test_script_03.py` with:
- `test_product_csv_creation()` - CSV created with correct count
- `test_category_distribution()` - Products distributed across categories
- `test_unique_product_ids()` - All IDs unique
- `test_schema_validation()` - CSV validates against product.yaml
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_03.py -v`

---

### Feature S04: Analyze Directory Schemas (Script 04)

**Purpose**: Identify relevant schemas and propose new ones

**Dependencies**: F01, F02, F04, S01, S03

**Reference**: [Script 4](site-gen-design.md#script-4-analyze-directory-schemas) in design document

#### Tasks

**[ ] S04-T1: Create Sample Data (Optional for Parallel Development)**

Create sample product.csv for testing.

- Copy sample products from Script 03
- Allows independent development

**Manual Verification**:
```bash
cat agtech/data/product.csv
```
- Note: Skip if using real output from Script 03

---

**[ ] S04-T2: Load All Available Schemas**

Read all schema files from backend/config/directory_schemas/.

- List all .yaml files in directory
- Load each schema
- Extract schema metadata
- Build schema catalog

**Manual Verification**:
```bash
python -c "from pathlib import Path; \
from lib.io.yaml_ops import read_yaml; \
schemas_dir = Path('../../backend/config/directory_schemas'); \
schemas = list(schemas_dir.glob('*.yaml')); \
print(f'Found {len(schemas)} schemas'); \
for s in schemas[:5]: print(s.name)"
```
- Verify: All schema files loaded
- Verify: Schemas have entry_type and fields
- Verify: At least 10+ schemas available

---

**[ ] S04-T3: Analyze Schema Relevance**

Use LLM with tool calling to evaluate each schema.

- For each schema, describe purpose
- Load analysis prompt from `lib/llm/prompts/analysis/schema_relevance.md`
- Load system prompt from `lib/llm/prompts/system/analyst.md`
- Ask LLM if relevant for agtech products
- Consider product types and use cases
- Generate relevance scores
- Select relevant schemas

**Manual Verification**:
```bash
python -c "# Schema analysis logic
print('Relevant schemas:', selected_schemas)"
```
- Verify: Product schema always included
- Verify: Cross_sell and up_sell included
- Verify: At least 5 relevant schemas selected
- Verify: Irrelevant schemas excluded

---

**[ ] S04-T4: Generate New Schema Proposals**

Use LLM to propose industry-specific schemas.

- Analyze agtech products
- Load proposal prompt from `lib/llm/prompts/analysis/propose_schemas.md`
- Load system prompt from `lib/llm/prompts/system/analyst.md`
- Identify gaps in existing schemas
- Generate 2-3 new schema proposals
- Follow existing schema patterns
- Write proposals to markdown

**Manual Verification**:
```bash
cat agtech/schemas/new-schema-proposals.md
```
- Verify: 2-3 new schemas proposed
- Verify: Each has clear purpose
- Verify: Follows existing schema structure
- Verify: Relevant to agtech industry

---

**[ ] S04-T5: Write Outputs**

Write selected-schemas.json and new-schema-proposals.md.

- Write selected schema list as JSON
- Write proposals as markdown with details
- Include rationale for selections

**Manual Verification**:
```bash
cat agtech/schemas/selected-schemas.json
cat agtech/schemas/new-schema-proposals.md
python -c "import json; \
data = json.load(open('agtech/schemas/selected-schemas.json')); \
print(f'Selected {len(data)} schemas'); \
assert 'product' in data; \
assert 'cross_sell' in data"
```
- Verify: JSON has list of schema names
- Verify: Markdown has detailed proposals
- Verify: Product and cross_sell included
- Verify: Proposals are actionable

---

**[ ] S04-T6: Integration - Complete Script**

Implement main() following script template.

- Load config, state, schemas
- Analyze relevance
- Generate proposals
- Write outputs
- Mark complete

**Manual Verification**:
```bash
python 04_analyze_schemas.py agtech
```
- Verify: Script runs without errors
- Verify: Both output files created
- Verify: Selected schemas appropriate
- Verify: State updated

---

**Feature S04 Verification**:
1. Delete agtech/schemas/ directory
2. Run `python 04_analyze_schemas.py agtech`
3. Verify selected-schemas.json has 5+ relevant schemas
4. Review new-schema-proposals.md
5. Approve or modify proposals (checkpoint)
6. Verify all selections justified

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Schema proposals reviewed and approved (checkpoint)
- Ready to create new schemas or proceed with existing

**Automated Tests**:
Create `tests/functional/test_script_04.py` with:
- `test_schema_analysis()` - Schemas analyzed correctly
- `test_relevant_schema_selection()` - Relevant schemas selected
- `test_new_schema_proposals()` - Proposals generated
- `test_output_file_creation()` - Both output files created
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_04.py -v`

---

### Feature S05: Create New Schemas (Script 05)

**Purpose**: Generate approved industry-specific schemas

**Dependencies**: F01, F02, F04, F06, S01, S04

**Reference**: [Script 5](site-gen-design.md#script-5-create-new-schemas) in design document

#### Tasks

**[ ] S05-T1: Create Sample Data (Optional for Parallel Development)**

Create sample new-schema-proposals.md for testing.

- Write sample proposals with 2 schemas
- Allows independent development

**Manual Verification**:
```bash
cat agtech/schemas/new-schema-proposals.md
```
- Note: Skip if using real output from Script 04

---

**[ ] S05-T2: Parse Approved Proposals**

Read and parse new-schema-proposals.md.

- Extract schema names
- Extract field definitions
- Extract required/optional classifications
- Structure for generation

**Manual Verification**:
```bash
python -c "# Proposal parsing logic
print('Schemas to create:', schema_names)"
```
- Verify: Extracts all proposed schemas
- Verify: Field definitions captured
- Verify: Required vs optional identified

---

**[ ] S05-T3: Generate YAML Schemas**

Use LLM to generate schema YAML files.

- For each approved proposal
- Load schema generation prompt from `lib/llm/prompts/generation/new_schema.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- Generate YAML following existing patterns
- Include entry_type, required_fields, optional_fields
- Include field definitions with types
- Follow product.yaml structure

**Manual Verification**:
```bash
python -c "from lib.generation.schema_generator import generate_schema; \
# Generate schema YAML
print('Generated schema YAML')"
```
- Verify: Valid YAML generated
- Verify: Follows existing schema pattern
- Verify: All sections present

---

**[ ] S05-T4: Validate Generated Schemas**

Check schemas against existing patterns.

- Verify required sections present
- Check field definitions complete
- Ensure no DirectoryImporter code changes needed
- Generate validation report

**Manual Verification**:
```bash
python -c "from lib.io.yaml_ops import read_yaml; \
schema = read_yaml('agtech/schemas/equipment_rental.yaml'); \
assert 'entry_type' in schema; \
assert 'required_fields' in schema; \
assert 'optional_fields' in schema; \
print('Schema valid')"
```
- Verify: Schema structure correct
- Verify: No backend code changes required
- Verify: Validation report shows no issues

---

**[ ] S05-T5: Write Schema Files**

Write schemas and validation report.

- Write YAML to agtech/schemas/ (temporary)
- Write validation report
- Note: Manual step to copy to backend/config/directory_schemas/

**Manual Verification**:
```bash
ls agtech/schemas/*.yaml
cat agtech/schemas/schema-validation-report.md
```
- Verify: YAML files created
- Verify: Validation report generated
- Verify: Report indicates schemas are valid
- Note: Do NOT copy to backend yet (manual approval step)

---

**[ ] S05-T6: Integration - Complete Script**

Implement main() following script template.

- Load config, state, proposals
- Generate schemas
- Validate
- Write outputs
- Mark complete

**Manual Verification**:
```bash
python 05_create_schemas.py agtech
```
- Verify: Script runs without errors
- Verify: Schema files and report created
- Verify: All schemas validated
- Verify: State updated

---

**Feature S05 Verification**:
1. Delete agtech/schemas/*.yaml and schema-validation-report.md
2. Run `python 05_create_schemas.py agtech`
3. Review generated schema files
4. Review validation report
5. If approved, manually copy schemas to backend/config/directory_schemas/
6. Checkpoint: Schema review and approval completed

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Schemas validated successfully
- Manual approval and copy completed (if new schemas created)
- Note: Can skip if no new schemas approved in S04

**Automated Tests**:
Create `tests/functional/test_script_05.py` with:
- `test_schema_generation()` - YAML schemas generated
- `test_schema_validation()` - Schemas valid against pattern
- `test_validation_report()` - Report created with results
- `test_schema_structure()` - Schemas have required sections
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_05.py -v`

---

### Feature S06: Generate Directory Data (Script 06)

**Purpose**: Create CSV data for all selected schemas

**Dependencies**: F01, F02, F04, F05, F06, S01, S03, S04

**Reference**: [Script 6](site-gen-design.md#script-6-generate-directory-data) in design document

#### Tasks

**[ ] S06-T1: Create Sample Data (Optional for Parallel Development)**

Create sample selected-schemas.json and product.csv.

- List schemas to generate
- Create sample products
- Allows independent development

**Manual Verification**:
```bash
cat agtech/schemas/selected-schemas.json
cat agtech/data/product.csv
```
- Note: Skip if using real outputs from previous scripts

---

**[ ] S06-T2: Load Products and Schemas**

Read product.csv and selected schemas.

- Load product catalog
- Load selected-schemas.json
- Load each schema YAML
- Prepare for generation

**Manual Verification**:
```bash
python -c "from lib.io.csv_ops import read_csv; \
import json; \
products = read_csv('agtech/data/product.csv'); \
schemas = json.load(open('agtech/schemas/selected-schemas.json')); \
print(f'Products: {len(products)}, Schemas: {len(schemas)}')"
```
- Verify: Products loaded
- Verify: Schemas loaded
- Verify: All referenced schemas exist

---

**[ ] S06-T3: Generate Directory CSVs**

For each schema, generate coherent CSV data.

- Call generic directory generator
- Load directory entry generation prompt from `lib/llm/prompts/generation/directory_entries.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- Pass product list for references
- Generate 20-30 entries per schema
- Maintain referential integrity
- Write CSV for each schema

**Manual Verification**:
```bash
# After generating cross_sell.csv
python -c "from lib.io.csv_ops import read_csv; \
from lib.validation.schema_validator import validate_csv_against_schema; \
data = read_csv('agtech/data/cross_sell.csv'); \
print(f'Entries: {len(data)}'); \
report = validate_csv_against_schema( \
    'agtech/data/cross_sell.csv', \
    '../../backend/config/directory_schemas/cross_sell.yaml'); \
print('Valid:', report['valid'])"
```
- Verify: CSV created for each schema
- Verify: 20-30 entries per CSV
- Verify: Each CSV validates against schema
- Verify: Product references are valid

---

**[ ] S06-T4: Validate Data Consistency**

Check all product references and relationships.

- Verify product IDs in cross_sell exist
- Verify up_sell references valid
- Check relationship counts within limits
- Generate consistency report

**Manual Verification**:
```bash
python -c "from lib.validation.data_validator import validate_product_references; \
# Validate all CSVs
print('Validation complete')"
```
- Verify: All product references valid
- Verify: No broken references
- Verify: Relationship counts within config limits (0-3)
- Verify: Validation report shows no errors

---

**[ ] S06-T5: Integration - Complete Script**

Implement main() following script template.

- Load config, state, products, schemas
- Generate all directory CSVs
- Validate consistency
- Mark complete

**Manual Verification**:
```bash
python 06_generate_directories.py agtech
```
- Verify: Script runs without errors
- Verify: CSV created for each selected schema
- Verify: All validations pass
- Verify: State updated
- Verify: Logs show progress for each schema

---

**Feature S06 Verification**:
1. Delete agtech/data/*.csv (except product.csv)
2. Run `python 06_generate_directories.py agtech`
3. Verify CSV for each schema in selected-schemas.json
4. Run validation checks on all CSVs
5. Verify all product references valid
6. Check sample entries for quality and coherence

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- All CSVs validated against schemas
- Data consistency checks passed
- Directory data ready for content generation

**Automated Tests**:
Create `tests/functional/test_script_06.py` with:
- `test_directory_csv_generation()` - CSVs generated for all schemas
- `test_schema_compliance()` - Each CSV validates against its schema
- `test_product_references()` - All product references valid
- `test_data_consistency()` - Consistency checks pass
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_06.py -v`

---

### Feature S07: Generate Product Pages (Script 07)

**Purpose**: Create detailed markdown pages for each product

**Dependencies**: F01, F02, F04, F06, S01, S03, S06

**Reference**: [Script 7](site-gen-design.md#script-7-generate-product-pages) in design document

#### Tasks

**[ ] S07-T1: Create Sample Data (Optional for Parallel Development)**

Create sample product.csv and directory CSVs.

- Minimal product data
- Sample cross-sell/up-sell data
- Allows independent development

**Manual Verification**:
```bash
cat agtech/data/product.csv
cat agtech/data/cross_sell.csv
```
- Note: Skip if using real outputs from previous scripts

---

**[ ] S07-T2: Load Products and Directories**

Read product.csv and all directory CSVs.

- Load product catalog
- Load cross-sell, up-sell data
- Build relationship map
- Prepare for page generation

**Manual Verification**:
```bash
python -c "from lib.io.csv_ops import read_csv; \
products = read_csv('agtech/data/product.csv'); \
cross_sell = read_csv('agtech/data/cross_sell.csv'); \
print(f'Products: {len(products)}, Cross-sells: {len(cross_sell)}')"
```
- Verify: All CSVs loaded
- Verify: Relationships mapped
- Verify: Product IDs match

---

**[ ] S07-T3: Generate Product Page Content**

For each product, generate detailed markdown page.

- Load product page generation prompt from `lib/llm/prompts/generation/product_page.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- Use LLM to generate content
- Include product details
- Add related product links (cross-sell/up-sell)
- Create product slug
- Include frontmatter

**Manual Verification**:
```bash
cat agtech/content/products/precision-planter-pro.md
python -c "from lib.io.file_ops import read_text; \
import yaml; \
content = read_text('agtech/content/products/precision-planter-pro.md'); \
# Extract frontmatter
print('Page generated with frontmatter')"
```
- Verify: Markdown file created
- Verify: Frontmatter is valid YAML
- Verify: Content is detailed and relevant
- Verify: Links to related products included

---

**[ ] S07-T4: Generate All Product Pages**

Loop through all products and generate pages.

- For each product in CSV
- Generate markdown page
- Write to content/products/
- Track progress

**Manual Verification**:
```bash
ls agtech/content/products/*.md | wc -l
# Should match product count
python -c "from lib.io.csv_ops import read_csv; \
products = read_csv('agtech/data/product.csv'); \
print(f'Expected {len(products)} pages')"
```
- Verify: One page per product
- Verify: All filenames are valid slugs
- Verify: No duplicate filenames

---

**[ ] S07-T5: Validate Product Links**

Check all internal links in product pages.

- Extract links from markdown
- Verify linked products exist
- Check frontmatter completeness
- Generate validation report

**Manual Verification**:
```bash
python -c "from lib.validation.link_validator import validate_all_links; \
from pathlib import Path; \
report = validate_all_links(Path('agtech/content/products')); \
print('Valid links:', report['valid']); \
print('Broken links:', len(report.get('broken_links', [])))"
```
- Verify: All internal links valid
- Verify: No broken product references
- Verify: Frontmatter complete on all pages

---

**[ ] S07-T6: Integration - Complete Script**

Implement main() following script template.

- Load config, state, products
- Generate all product pages
- Validate links
- Mark complete

**Manual Verification**:
```bash
python 07_generate_product_pages.py agtech
```
- Verify: Script runs without errors
- Verify: All product pages generated
- Verify: Link validation passes
- Verify: State updated

---

**Feature S07 Verification**:
1. Delete agtech/content/products/ directory
2. Run `python 07_generate_product_pages.py agtech`
3. Verify 100 product pages created (or configured count)
4. Review 3-5 sample pages for quality
5. Verify all internal links valid
6. Check frontmatter structure consistent

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- One page per product
- All links validated
- Content quality acceptable

**Automated Tests**:
Create `tests/functional/test_script_07.py` with:
- `test_product_page_generation()` - All product pages created
- `test_frontmatter_valid()` - Frontmatter is valid YAML
- `test_internal_links()` - All links valid
- `test_page_count_matches_products()` - Count matches product.csv
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_07.py -v`

---

### Feature S08: Generate Category Pages (Script 08)

**Purpose**: Create category landing pages with product listings

**Dependencies**: F01, F02, F04, F06, S01, S03, S07

**Reference**: [Script 8](site-gen-design.md#script-8-generate-category-pages) in design document

#### Tasks

**[ ] S08-T1: Create Sample Data (Optional for Parallel Development)**

Create sample product.csv for testing.

- Minimal products with categories
- Allows independent development

**Manual Verification**:
```bash
cat agtech/data/product.csv
```
- Note: Skip if using real output from Script 03

---

**[ ] S08-T2: Extract Categories**

Read products and extract unique categories.

- Load product.csv
- Get unique category list
- Count products per category
- Sort categories

**Manual Verification**:
```bash
python -c "from lib.io.csv_ops import read_csv; \
products = read_csv('agtech/data/product.csv'); \
categories = set(p['category'] for p in products); \
print(f'Categories: {len(categories)}'); \
print(list(categories))"
```
- Verify: 10 categories extracted
- Verify: All products assigned to categories
- Verify: No missing/empty categories

---

**[ ] S08-T3: Generate Category Pages**

For each category, create landing page.

- Load category page generation prompt from `lib/llm/prompts/generation/category_page.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- Use LLM to generate category description
- List all products in category
- Link to product pages
- Create category slug
- Include frontmatter

**Manual Verification**:
```bash
cat agtech/content/categories/precision-equipment.md
```
- Verify: Category description generated
- Verify: Product list included
- Verify: Links to product pages
- Verify: Frontmatter valid

---

**[ ] S08-T4: Validate Category Links**

Check all product links in category pages.

- Extract product links
- Verify linked pages exist
- Check all products represented
- Generate validation report

**Manual Verification**:
```bash
python -c "from lib.validation.link_validator import validate_all_links; \
from pathlib import Path; \
report = validate_all_links(Path('agtech/content/categories')); \
print('Valid:', report['valid'])"
```
- Verify: All product links valid
- Verify: No broken links
- Verify: All products appear in a category

---

**[ ] S08-T5: Integration - Complete Script**

Implement main() following script template.

- Load config, state, products
- Generate all category pages
- Validate links
- Mark complete

**Manual Verification**:
```bash
python 08_generate_category_pages.py agtech
```
- Verify: Script runs without errors
- Verify: 10 category pages created
- Verify: Link validation passes
- Verify: State updated

---

**Feature S08 Verification**:
1. Delete agtech/content/categories/ directory
2. Run `python 08_generate_category_pages.py agtech`
3. Verify 10 category pages created
4. Review all pages for completeness
5. Verify every product appears on a category page
6. Verify all links to products valid

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- One page per category
- All product links valid
- Categories cover all products

**Automated Tests**:
Create `tests/functional/test_script_08.py` with:
- `test_category_page_generation()` - All category pages created
- `test_category_count()` - Correct number of categories
- `test_product_links()` - All product links valid
- `test_product_coverage()` - Every product appears on a category page
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_08.py -v`

---

### Feature S09: Generate Site Pages (Script 09)

**Purpose**: Create home, about, contact, and navigation pages

**Dependencies**: F01, F02, F04, F06, S01, S03, S08

**Reference**: [Script 9](site-gen-design.md#script-9-generate-site-pages) in design document

#### Tasks

**[ ] S09-T1: Create Sample Data (Optional for Parallel Development)**

Create sample site-gen-config.yaml with company profile.

- Company name, tagline, description
- Allows independent development

**Manual Verification**:
```bash
cat agtech/site-gen-config.yaml
```
- Note: Skip if using real output from Script 01

---

**[ ] S09-T2: Generate Home Page**

Create index.md with category navigation.

- Use company profile from config
- Load home page generation prompt from `lib/llm/prompts/generation/home_page.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- List all categories with descriptions
- Link to category pages
- LLM generates compelling content
- Include frontmatter

**Manual Verification**:
```bash
cat agtech/content/index.md
```
- Verify: Company information prominent
- Verify: All categories listed
- Verify: Links to category pages
- Verify: Professional and engaging content

---

**[ ] S09-T3: Generate About Page**

Create about.md with company story.

- Use company profile
- Load about page generation prompt from `lib/llm/prompts/generation/about_page.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- LLM expands into full about page
- Include mission, vision, values
- Professional tone

**Manual Verification**:
```bash
cat agtech/content/about.md
```
- Verify: Company story compelling
- Verify: Content aligns with config
- Verify: Professional presentation

---

**[ ] S09-T4: Generate Contact Page**

Create contact.md with contact information.

- Use company profile
- Load contact page generation prompt from `lib/llm/prompts/generation/contact_page.md`
- Load system prompt from `lib/llm/prompts/system/generator.md`
- Include contact form placeholder
- Add company details
- Professional layout

**Manual Verification**:
```bash
cat agtech/content/contact.md
```
- Verify: Contact information present
- Verify: Form placeholder included
- Verify: Professional presentation

---

**[ ] S09-T5: Generate Navigation Structure**

Create _navigation.json with site structure.

- List all pages
- Organize into sections
- Include product categories
- Provide menu structure

**Manual Verification**:
```bash
cat agtech/content/_navigation.json
python -c "import json; \
nav = json.load(open('agtech/content/_navigation.json')); \
print('Navigation sections:', len(nav))"
```
- Verify: All pages included
- Verify: Logical structure
- Verify: Valid JSON

---

**[ ] S09-T6: Validate Site Links**

Check all links in site pages.

- Verify category links
- Check internal navigation
- Ensure no broken links

**Manual Verification**:
```bash
python -c "from lib.validation.link_validator import validate_all_links; \
from pathlib import Path; \
report = validate_all_links(Path('agtech/content')); \
print('Valid:', report['valid']); \
print('Total files:', report['files_checked'])"
```
- Verify: All links valid
- Verify: Navigation complete
- Verify: No broken references

---

**[ ] S09-T7: Integration - Complete Script**

Implement main() following script template.

- Load config, state
- Generate all site pages
- Create navigation
- Validate
- Mark complete

**Manual Verification**:
```bash
python 09_generate_site_pages.py agtech
```
- Verify: Script runs without errors
- Verify: All pages created
- Verify: Navigation structure valid
- Verify: State updated

---

**Feature S09 Verification**:
1. Delete agtech/content/{index,about,contact,_navigation}.md/json
2. Run `python 09_generate_site_pages.py agtech`
3. Verify home, about, contact pages created
4. Verify navigation.json complete
5. Review pages for quality and branding
6. Verify all category links work

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- All site pages created
- Navigation complete
- All links validated

**Automated Tests**:
Create `tests/functional/test_script_09.py` with:
- `test_site_page_generation()` - Home, about, contact pages created
- `test_navigation_structure()` - Navigation JSON valid
- `test_category_links()` - All category links work
- `test_content_quality()` - Pages have substantial content
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_09.py -v`

---

### Feature S10: Validate Site (Script 10)

**Purpose**: Comprehensive validation of all generated content

**Dependencies**: F01, F04, F05, S01, S03, S06, S07, S08, S09

**Reference**: [Script 10](site-gen-design.md#script-10-validate-site) in design document

#### Tasks

**[ ] S10-T1: Validate All Links**

Check every internal link across all markdown files.

- Load all markdown files
- Extract all links
- Verify targets exist
- Report broken links

**Manual Verification**:
```bash
python -c "from lib.validation.link_validator import validate_all_links; \
from pathlib import Path; \
report = validate_all_links(Path('agtech/content')); \
print(report)"
```
- Verify: All links checked
- Verify: No broken links
- Verify: External links skipped

---

**[ ] S10-T2: Validate Product References**

Check CSV directories reference valid products.

- Load all directory CSVs
- Check product ID references
- Verify all products still exist
- Report broken references

**Manual Verification**:
```bash
python -c "from lib.validation.data_validator import validate_product_references; \
# Check all directory CSVs
print('Product references validated')"
```
- Verify: All product IDs valid
- Verify: No orphaned references
- Verify: Bidirectional relationships consistent

---

**[ ] S10-T3: Validate CSV Schemas**

Revalidate all CSVs against schemas.

- For each CSV in data/
- Validate against corresponding schema
- Check required fields
- Report any errors

**Manual Verification**:
```bash
python -c "from lib.validation.schema_validator import validate_csv_against_schema; \
from pathlib import Path; \
# Validate each CSV
print('Schema validation complete')"
```
- Verify: All CSVs valid
- Verify: No schema violations
- Verify: Required fields present

---

**[ ] S10-T4: Check for Orphaned Content**

Find any unreferenced pages or data.

- List all product pages
- Check all referenced in categories
- Find any unreachable pages
- Report orphans

**Manual Verification**:
```bash
python -c "# Orphan check logic
print('Orphan check complete')"
```
- Verify: No orphaned product pages
- Verify: All products linked from categories
- Verify: All categories linked from home

---

**[ ] S10-T5: Generate Validation Report**

Create comprehensive validation-report.md.

- Summarize all validation results
- List any issues found
- Provide statistics
- Include pass/fail for each check

**Manual Verification**:
```bash
cat agtech/validation-report.md
```
- Verify: Report generated
- Verify: All checks documented
- Verify: Clear pass/fail status
- Verify: Any issues detailed

---

**[ ] S10-T6: Integration - Complete Script**

Implement main() following script template.

- Load config, state
- Run all validation checks
- Generate report
- Mark complete

**Manual Verification**:
```bash
python 10_validate_site.py agtech
```
- Verify: Script runs without errors
- Verify: Validation report created
- Verify: All checks pass (or issues documented)
- Verify: State updated

---

**Feature S10 Verification**:
1. Delete agtech/validation-report.md
2. Run `python 10_validate_site.py agtech`
3. Review validation-report.md thoroughly
4. Verify all validation checks passed
5. If issues found, address them before proceeding
6. Checkpoint: Validation report reviewed and approved

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Validation report comprehensive
- All checks passing (or issues resolved)
- Validation report reviewed (checkpoint)
- Ready for Astro conversion

**Automated Tests**:
Create `tests/functional/test_script_10.py` with:
- `test_validation_report_generation()` - Report created
- `test_schema_validation()` - All CSVs validate
- `test_link_validation()` - All links checked
- `test_data_consistency()` - Consistency checks pass
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`
- Run: `pytest tests/functional/test_script_10.py -v`

---

### Feature S11: Convert to Astro (Script 11)

**Purpose**: Transform markdown site to Astro pages

**Dependencies**: F01, F04, S01, S07, S08, S09, S10

**Reference**: [Script 11](site-gen-design.md#script-11-convert-to-astro) in design document

#### Tasks

**[ ] S11-T1: Create Astro Project Structure**

Set up Astro directory in web/src/pages/.

- Create web/src/pages/agtech/
- Set up subdirectories (products, categories)
- Copy or reference existing Astro layouts

**Manual Verification**:
```bash
ls web/src/pages/agtech/
```
- Verify: Directory structure created
- Verify: Ready for Astro files

---

**[ ] S11-T2: Convert Product Pages**

Transform product markdown to Astro components.

- Read each product.md
- Extract frontmatter
- Convert markdown body
- Create .astro files
- Add chatbot integration placeholder

**Manual Verification**:
```bash
cat web/src/pages/agtech/products/precision-planter-pro.astro
```
- Verify: Astro file created
- Verify: Frontmatter converted to Astro props
- Verify: Content rendered
- Verify: Chatbot placeholder present

---

**[ ] S11-T3: Convert Category Pages**

Transform category markdown to Astro components.

- Read each category.md
- Convert to Astro format
- Maintain product links
- Add navigation

**Manual Verification**:
```bash
cat web/src/pages/agtech/categories/precision-equipment.astro
```
- Verify: Astro file created
- Verify: Product links work
- Verify: Layout consistent

---

**[ ] S11-T4: Convert Site Pages**

Transform home, about, contact to Astro.

- Convert index.md to index.astro
- Convert about.md, contact.md
- Add Astro layout integration
- Include navigation

**Manual Verification**:
```bash
cat web/src/pages/agtech/index.astro
cat web/src/pages/agtech/about.astro
cat web/src/pages/agtech/contact.astro
```
- Verify: All pages converted
- Verify: Layout applied
- Verify: Navigation works

---

**[ ] S11-T5: Add Chatbot Integration**

Integrate Salient chat API into pages.

- Add chatbot component
- Configure for agtech account
- Add API token handling
- Test integration points

**Manual Verification**:
```bash
# Start Astro dev server
cd web && npm run dev
# Visit http://localhost:4321/agtech/
# Check chatbot loads
```
- Verify: Chatbot component added
- Verify: Configuration correct
- Verify: Ready for API token setup

---

**[ ] S11-T6: Integration - Complete Script**

Implement main() following script template.

- Load config, state
- Convert all markdown files
- Add chatbot integration
- Mark complete

**Manual Verification**:
```bash
python 11_convert_to_astro.py agtech
# Then test in browser
cd web && npm run dev
```
- Verify: Script runs without errors
- Verify: All files converted
- Verify: Astro site works
- Verify: State updated

---

**Feature S11 Verification**:
1. Delete web/src/pages/agtech/ directory
2. Run `python 11_convert_to_astro.py agtech`
3. Start Astro dev server
4. Visit http://localhost:4321/agtech/
5. Navigate through all pages
6. Verify navigation works
7. Verify content displays correctly
8. Check chatbot integration points

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- All markdown converted to Astro
- Site functional in browser
- Chatbot integration ready

**Automated Tests**:
Create `tests/functional/test_script_11.py` with:
- `test_markdown_to_astro_conversion()` - All files converted
- `test_frontmatter_preserved()` - Frontmatter converted correctly
- `test_astro_file_count()` - Count matches markdown files
- `test_chatbot_integration()` - Chatbot component added
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`
- Run: `pytest tests/functional/test_script_11.py -v`
- Ready for final feature documentation

---

### Feature S12: Generate Demo Features List (Script 12)

**Purpose**: Document all demoable features with examples

**Dependencies**: F01, F02, F04, S01-S11

**Reference**: [Script 12](site-gen-design.md#script-12-generate-demo-features-list) in design document

#### Tasks

**[ ] S12-T1: Analyze Generated Content**

Read and analyze all generated files.

- Read all markdown/Astro files
- Read all CSV files
- Read configuration and state
- Extract key features
- Count products, categories, directories

**Manual Verification**:
```bash
python -c "# Analysis logic
print(f'Products: {product_count}'); \
print(f'Categories: {category_count}'); \
print(f'Directories: {directory_count}')"
```
- Verify: All files analyzed
- Verify: Statistics accurate
- Verify: Features identified

---

**[ ] S12-T2: Generate Feature List**

Use LLM to create comprehensive numbered feature list.

- Load demo features generation prompt from `lib/llm/prompts/validation/demo_features.md`
- Load system prompt from `lib/llm/prompts/system/analyst.md`
- Organize by categories
- Include specific examples
- Add demo instructions
- Make it actionable
- Format as markdown

**Manual Verification**:
```bash
cat agtech/demo-features.md
```
- Verify: Numbered list created
- Verify: Organized by categories
- Verify: Specific examples included
- Verify: Actionable for demos

---

**[ ] S12-T3: Validate Feature Claims**

Check all listed features actually exist.

- For each feature claim
- Verify file/data exists
- Check examples are accurate
- Ensure no hallucinations

**Manual Verification**:
```bash
python -c "# Feature validation logic
print('All features validated')"
```
- Verify: All features exist
- Verify: Examples are real
- Verify: No false claims

---

**[ ] S12-T4: Integration - Complete Script**

Implement main() following script template.

- Load config, state
- Analyze all content
- Generate feature list
- Validate
- Mark complete

**Manual Verification**:
```bash
python 12_generate_demo_features.py agtech
```
- Verify: Script runs without errors
- Verify: demo-features.md created
- Verify: All features validated
- Verify: State updated

---

**Feature S12 Verification**:
1. Delete agtech/demo-features.md
2. Run `python 12_generate_demo_features.py agtech`
3. Review demo-features.md
4. Verify all claims by checking actual site
5. Use list to perform actual demo
6. Confirm all features are demoable

**Completion Criteria**:
- All tasks completed
- Feature verification passed
- Demo features list comprehensive
- All features verified to exist
- Ready for demo presentation

**Automated Tests**:
Create `tests/functional/test_script_12.py` with:
- `test_demo_features_generation()` - demo-features.md created
- `test_feature_categories()` - Features organized by category
- `test_feature_validation()` - All claimed features exist
- `test_numbered_list_format()` - Proper markdown formatting
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_script_12.py -v`

---

## Completion

All features complete when:
1. Foundation libraries (F01-F06) functional
2. All 12 scripts (S01-S12) implemented
3. AgTech site generated end-to-end
4. All validations passing
5. Astro site functional
6. Demo features documented

**Success Criteria**:
- Run complete workflow: `python 01_init_config.py agtech` through `python 12_generate_demo_features.py agtech`
- Visit http://localhost:4321/agtech/
- Navigate entire site
- All links work
- 100 products across 10 categories
- Directory data coherent
- Chatbot integration ready
- Demo features list comprehensive

**AgTech Test Case**: Complete industry site generator proof of concept, ready to extend to other industries.

**Automated Test Suite**:
Create `tests/functional/test_end_to_end.py` with:
- `test_full_workflow_execution()` - All 12 scripts run successfully
- `test_output_completeness()` - All expected files generated
- `test_site_functionality()` - Astro site works correctly
- `test_data_integrity()` - All data consistent across files
- Mark with `@pytest.mark.functional`, `@pytest.mark.slow`, `@pytest.mark.llm`
- Run: `pytest tests/functional/test_end_to_end.py -v`

**Run All Tests**:
```bash
# Run all unit tests (fast)
pytest tests/unit -v

# Run all integration tests
pytest tests/integration -v

# Run all functional tests (slow)
pytest tests/functional -v

# Run with coverage report
pytest --cov=lib --cov-report=html --cov-report=term-missing

# Run excluding expensive LLM tests
pytest -m "not llm" -v
```
