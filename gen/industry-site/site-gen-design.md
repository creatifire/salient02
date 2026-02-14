# Industry Site Generator Design

## Overview

LLM-powered workflow that generates complete industry-specific demo sites with coherent product catalogs, directory data, and supporting content. Operates as a series of sequential scripts with validation checkpoints.

**Related Documentation:**
- [Code Organization](site-gen-code-org.md) - Module structure and interfaces
- [Implementation Plan](site-gen-plan.md) - Task breakdown with verification steps
- [Automated Testing](site-gen-auto-tests.md) - Testing conventions and best practices

## Architecture

### Configuration-Driven Approach

Central configuration file: `site-gen-config.yaml` in industry folder (e.g., `agtech/site-gen-config.yaml`)

**Core Settings:**
- Company profile (name, tagline, description)
- LLM configuration (models: sonnet-4.5 for tool calling, haiku-4.5 for generation)
- API tokens (OpenRouter, Exa, Jina)
- Generation parameters (product count, category count, relationship depth)
- Optional references to research files

**Generation Parameters:**
```yaml
products:
  count: 100  # Total products to generate
  categories: 10  # Number of product categories
  relationships: 3  # Max cross-sell/up-sell per product (0-3)
```

### Script Sequence

Scripts run sequentially, each producing output that feeds the next stage. Progress tracked through file existence.

## Workflow Steps

Scripts run sequentially, each producing output that feeds the next stage. Progress tracked through file existence.

### Script 1: Initialize Configuration
**File:** `01_init_config.py`
**Purpose:** Gather requirements and create site-gen-config.yaml

**Process:**
1. Interactive prompts or CLI args for company basics
2. Read research files from `{industry}/research/` folder
3. Generate company profile from research (LLM)
4. Write `{industry}/site-gen-config.yaml`

**Output:**
- `{industry}/site-gen-config.yaml`

**Validation:** Config file exists and is valid YAML

---

### Script 2: Research Industry
**File:** `02_research_industry.py`
**Purpose:** Research real companies and products in the industry

**Process:**
1. Read site-gen-config.yaml
2. Use Exa to search for top companies in industry
3. For each company, use Jina Reader to scrape product/service pages
4. Extract product names, descriptions, categories
5. LLM summarizes findings into structured data

**Output:**
- `{industry}/research/companies.json` - List of real companies
- `{industry}/research/products-catalog.json` - Real product examples
- `{industry}/research/research-summary.md` - Human-readable summary

**Validation:** 
- Minimum 20 real products found
- At least 5 distinct categories identified

---

### Script 3: Generate Product Schema
**File:** `03_generate_product_schema.py`
**Purpose:** Create product/service directory as foundation

**Process:**
1. Read research data (products-catalog.json)
2. Generate realistic product names based on research (LLM)
3. Create product directory entries following product.yaml schema
4. Generate categories and assign products
5. Write product directory CSV

**Output:**
- `{industry}/data/product.csv` - Product directory (master reference)

**Validation:**
- CSV validates against product.yaml schema
- Correct number of products generated
- All products have unique IDs and names
- Products distributed across categories

---

### Script 4: Analyze Directory Schemas
**File:** `04_analyze_schemas.py`
**Purpose:** Identify relevant directory schemas for the industry

**Process:**
1. Read all schemas from `backend/config/directory_schemas/`
2. Read product catalog from product.csv
3. Use LLM with tool-calling to evaluate each schema for relevance
4. Generate recommendations for new schemas specific to industry

**Output:**
- `{industry}/schemas/selected-schemas.json` - List of relevant existing schemas
- `{industry}/schemas/new-schema-proposals.md` - Suggested new schemas (checkpoint)

**Validation:**
- Product schema always included
- Cross-sell and up-sell included for product-heavy sites
- Checkpoint: Review new-schema-proposals.md before proceeding

---

### Script 5: Create New Schemas
**File:** `05_create_schemas.py`
**Purpose:** Generate new industry-specific schemas (if approved)

**Process:**
1. Read approved proposals from new-schema-proposals.md
2. LLM generates YAML schemas following existing patterns
3. Validate against existing schema structure
4. Write to `backend/config/directory_schemas/` (requires approval)

**Output:**
- `backend/config/directory_schemas/{new_schema}.yaml` (manual step)
- `{industry}/schemas/schema-validation-report.md`

**Validation:**
- Schemas follow required_fields/optional_fields pattern
- No backend code changes required (DirectoryImporter is generic)

---

### Script 6: Generate Directory Data
**File:** `06_generate_directories.py`
**Purpose:** Create coherent CSV data for all selected schemas

**Process:**
1. Read selected-schemas.json
2. For each schema, call generic directory generator function
3. Pass product list for relationship consistency
4. LLM generates realistic data linked to products
5. Validate data consistency and relationships

**Modules:**
- `lib/generic_directory_generator.py` - Reusable generator functions
- One schema processed at a time
- Product IDs used for cross-references

**Output:**
- `{industry}/data/{schema_name}.csv` - One CSV per schema

**Validation:**
- All CSVs validate against their schemas
- Product references in cross-sell/up-sell exist in product.csv
- Relationships are valid and within configured limits
- No broken references

---

### Script 7: Generate Product Pages
**File:** `07_generate_product_pages.py`
**Purpose:** Create detailed markdown pages for each product

**Process:**
1. Read product.csv (master reference)
2. For each product, generate detailed markdown page
3. Include frontmatter with product metadata
4. LLM generates content based on real product research
5. Add internal links to related products (from cross-sell/up-sell)

**Output:**
- `{industry}/content/products/{product-slug}.md` - One page per product

**Validation:**
- All internal links resolve to existing product pages
- Frontmatter includes all required product fields
- Product slugs match entries in product.csv

---

### Script 8: Generate Category Pages
**File:** `08_generate_category_pages.py`
**Purpose:** Create category landing pages

**Process:**
1. Read product.csv to get all categories
2. For each category, generate landing page
3. List products in category with links
4. LLM generates category descriptions

**Output:**
- `{industry}/content/categories/{category-slug}.md`

**Validation:**
- All product links exist
- Categories cover all products

---

### Script 9: Generate Site Pages
**File:** `09_generate_site_pages.py`
**Purpose:** Create home, about, contact, and navigation pages

**Process:**
1. Read site-gen-config.yaml for company profile
2. LLM generates home page with category navigation
3. Generate about, contact pages based on company profile
4. Create site navigation structure

**Output:**
- `{industry}/content/index.md` - Home page
- `{industry}/content/about.md`
- `{industry}/content/contact.md`
- `{industry}/content/_navigation.json` - Site structure

**Validation:**
- All category links resolve
- Navigation is complete

---

### Script 10: Validate Site
**File:** `10_validate_site.py`
**Purpose:** Comprehensive validation of all generated content

**Process:**
1. Check all internal links resolve
2. Verify product references in directories match product pages
3. Validate CSV data consistency
4. Check for orphaned pages
5. Generate validation report

**Output:**
- `{industry}/validation-report.md` - Complete validation results

**Validation Checks:**
- Link integrity
- Data consistency
- Schema compliance
- Relationship validity

---

### Script 11: Convert to Astro
**File:** `11_convert_to_astro.py`
**Purpose:** Transform markdown site to Astro pages (separate phase)

**Process:**
1. Read markdown from `{industry}/content/`
2. Convert to Astro components
3. Add chatbot integration
4. Write to `web/src/pages/{industry}/`

**Output:**
- `web/src/pages/{industry}/` - Complete Astro site

**Note:** This is a checkpoint - markdown site should be validated before conversion

---

### Script 12: Generate Demo Features List
**File:** `12_generate_demo_features.py`
**Purpose:** Create comprehensive numbered list of demoable features

**Process:**
1. Read all generated content and data files
2. Analyze site structure, products, directories, relationships
3. LLM generates thorough numbered list of features
4. Organize by categories (content, functionality, chatbot, data)
5. Include specific examples from generated site

**Output:**
- `{industry}/demo-features.md` - Numbered list of all demoable features

**Features Documented:**
- Site structure and navigation
- Product catalog capabilities
- Category organization
- Directory integrations (cross-sell, up-sell, etc.)
- Chatbot integration points
- RAG-powered search capabilities
- Content relationships and linking
- Data consistency demonstrations
- Industry-specific features

**Validation:**
- All listed features exist in generated site
- Examples reference actual generated content
- Features are actionable for demos

---

## Data Flow

```
Research Files → Config → Research → Product Schema (CSV)
                                           ↓
                            Schema Analysis → Selected Schemas
                                           ↓
                            Directory Data (CSVs) ← Product References
                                           ↓
                            Product Pages (MD) ← Product + Directory Data
                                           ↓
                            Category Pages (MD) ← Products by Category
                                           ↓
                            Site Pages (MD) ← Company Profile
                                           ↓
                            Validation → Validation Report
                                           ↓
                            Astro Conversion → Live Site
                                           ↓
                            Demo Features List → Feature Documentation
```

## File Organization

```
gen/industry-site/
├── README.md                          # Workflow documentation
├── industry-site-gen-design.md        # This file
├── site-gen-config.yaml               # Default template
├── lib/
│   ├── config/                        # Config and state management
│   ├── llm/
│   │   ├── client.py                  # OpenRouter client
│   │   ├── retry.py                   # Retry logic
│   │   └── prompts/                   # External prompt files
│   │       ├── loader.py              # Prompt loader utility
│   │       ├── research/              # Research prompts
│   │       ├── generation/            # Generation prompts
│   │       ├── analysis/              # Analysis prompts
│   │       ├── validation/            # Validation prompts
│   │       └── system/                # System prompts
│   ├── research/                      # Exa + Jina integration
│   ├── generation/                    # Generator functions
│   ├── validation/                    # Validators
│   ├── io/                            # File operations
│   ├── errors/                        # Error handling
│   └── logging/                       # Logger integration
├── 01_init_config.py
├── 02_research_industry.py
├── 03_generate_product_schema.py
├── 04_analyze_schemas.py
├── 05_create_schemas.py
├── 06_generate_directories.py
├── 07_generate_product_pages.py
├── 08_generate_category_pages.py
├── 09_generate_site_pages.py
├── 10_validate_site.py
├── 11_convert_to_astro.py
├── 12_generate_demo_features.py
└── agtech/
    ├── site-gen-config.yaml
    ├── research/
    │   ├── agtech-case-study.md
    │   ├── agtech-chatbot-pain-points.md
    │   ├── agtech-marketing-strategy.md
    │   ├── agtech-strategic-brief.md
    │   ├── companies.json
    │   ├── products-catalog.json
    │   └── research-summary.md
    ├── schemas/
    │   ├── selected-schemas.json
    │   ├── new-schema-proposals.md
    │   └── schema-validation-report.md
    ├── data/
    │   ├── product.csv
    │   ├── cross_sell.csv
    │   ├── up_sell.csv
    │   └── {other_schemas}.csv
    ├── content/
    │   ├── index.md
    │   ├── about.md
    │   ├── contact.md
    │   ├── _navigation.json
    │   ├── products/
    │   │   └── {product-slug}.md
    │   └── categories/
    │       └── {category-slug}.md
    ├── validation-report.md
    └── demo-features.md
```

## Technical Implementation

### Prompt Storage

**External Markdown Files**: Prompts stored in `lib/llm/prompts/` organized by function.

**Structure:**
```
lib/llm/prompts/
├── loader.py              # Prompt loading utility
├── research/
│   ├── search_companies.md
│   ├── analyze_website.md
│   ├── extract_products.md
│   └── categorize_products.md
├── generation/
│   ├── product_names.md
│   ├── product_page.md
│   ├── category_page.md
│   ├── home_page.md
│   ├── directory_entries.md
│   └── new_schema.md
├── analysis/
│   ├── schema_relevance.md
│   └── propose_schemas.md
├── validation/
│   └── demo_features.md
└── system/
    ├── researcher.md
    ├── generator.md
    └── analyst.md
```

**Loader Utility:**
```python
# lib/llm/prompts/loader.py
def load_prompt(category: str, name: str, variables: dict = None) -> str:
    """Load and format prompt from markdown file."""
    prompt_path = PROMPTS_DIR / category / f"{name}.md"
    template = prompt_path.read_text(encoding='utf-8')
    
    if variables:
        return template.format(**variables)
    return template

def load_system_prompt(role: str) -> str:
    """Load system prompt for role (researcher, generator, analyst)."""
    return load_prompt('system', role)
```

**Benefits:**
- Matches backend pattern (`backend/config/prompt_modules/`)
- Easy to iterate without code changes
- Version controlled
- Organized by function

### LLM Integration

**Client Setup:**
```python
# lib/llm/client.py
from openai import OpenAI
from .prompts.loader import load_prompt, load_system_prompt

# See code organization doc for full LLMClient implementation
```

**Usage Example:**
```python
from lib.llm.client import LLMClient
from lib.llm.prompts.loader import load_prompt, load_system_prompt

llm = LLMClient(api_key=config['llm']['api_key'])

# Load prompt with variables
prompt = load_prompt('generation', 'product_names', {
    'count': 100,
    'industry': 'agtech',
    'real_products': product_list_text,
    'categories': category_list_text
})

system_prompt = load_system_prompt('generator')

response = llm.generate_text(prompt, system_prompt=system_prompt)
```

**Model Selection:**
- Tool calling: `anthropic/claude-sonnet-4.5`
- Text generation: `anthropic/claude-haiku-4.5`
- Configured in site-gen-config.yaml

### Research Tools

**Exa Search:**
```python
# lib/research_tools.py
from exa_py import Exa

def search_industry_companies(industry, exa_key):
    exa = Exa(exa_key)
    results = exa.search(
        f"top {industry} companies products",
        num_results=20,
        use_autoprompt=True
    )
    return results
```

**Jina Reader:**
```python
def scrape_with_jina(url, jina_key):
    response = requests.get(
        f"https://r.jina.ai/{url}",
        headers={"Authorization": f"Bearer {jina_key}"}
    )
    return response.text  # Clean markdown
```

### Directory Generator

**Generic Function:**
```python
# lib/generic_directory_generator.py
def generate_directory_csv(
    schema_path,
    product_list,
    llm_client,
    output_path,
    config
):
    """
    Generate coherent CSV data for any schema.
    
    Args:
        schema_path: Path to schema YAML
        product_list: List of products for references
        llm_client: OpenAI client
        output_path: Where to write CSV
        config: site-gen-config.yaml content
    """
    schema = load_schema(schema_path)
    
    # LLM generates entries based on schema structure
    # Uses product_list for valid cross-references
    # Validates against schema
    # Writes CSV
    pass
```

### Validation

**Link Validation:**
```python
# lib/link_validator.py
def validate_all_links(content_dir):
    """Check all markdown links resolve to existing pages."""
    pass

def validate_product_references(csv_dir, content_dir):
    """Verify directory CSVs reference real products."""
    pass
```

**Schema Validation:**
```python
# lib/schema_validator.py
def validate_csv_against_schema(csv_path, schema_path):
    """Ensure CSV conforms to schema requirements."""
    pass
```

### Logging

Leverage existing backend logger:
```python
# lib/logger.py
import sys
sys.path.append('../../backend')
from backend.app.services import logger

# Use structured logging
logger.info('step_started', step='02_research_industry')
logger.error('validation_failed', error=details)
```

## Checkpoints and Validation

**Human Review Required:**
1. After step 1: Review site-gen-config.yaml
2. After step 4: Approve new-schema-proposals.md
3. After step 10: Review validation-report.md before Astro conversion

**Automatic Validation:**
- Schema compliance at each CSV generation
- Link integrity after page generation
- Data consistency across all outputs
- Relationship validity in directory data

## Error Handling

**Graceful Degradation:**
- If research finds < 20 products, flag warning but continue
- If LLM fails, retry with exponential backoff
- Log all errors with context for debugging
- Each script can be re-run independently

**Resume Capability:**
- Check for existing output files
- Skip completed steps
- Allow running specific script by number

## Configuration Template

**site-gen-config.yaml:**
```yaml
company:
  name: "AgriTech Solutions"
  industry: "agtech"
  tagline: "Smart farming for sustainable growth"
  description: "Leading provider of agricultural technology solutions"
  
research:
  reference_files:
    - "research/agtech-strategic-brief.md"
    - "research/agtech-case-study.md"

llm:
  api_key: "${OPENROUTER_API_KEY}"
  models:
    tool_calling: "anthropic/claude-sonnet-4.5"
    generation: "anthropic/claude-haiku-4.5"

research_tools:
  exa_api_key: "${EXA_API_KEY}"
  jina_api_key: "${JINA_API_KEY}"

generation:
  products:
    count: 100
    categories: 10
  relationships:
    max_per_product: 3
  validation:
    strict: true
```

## Next Steps

1. Review this design
2. Iterate on any ambiguities
3. Implement scripts sequentially (01-12)
4. Test complete workflow on agtech vertical
5. Review generated demo-features.md for demo preparation
6. Refine based on results
7. Extend to other industries
