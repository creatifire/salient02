<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Directory Search Tool Architecture

> **Last Updated**: October 30, 2025  
> **Status**: Implemented  
> **Related**: [0023-directory-service.md](../project-management/0023-directory-service.md)

## Overview

The Directory Search Tool is a **generic, multi-tenant, schema-driven search system** that enables natural language queries across any type of structured directory list. It's designed to be highly flexible and configurable without requiring code changes.

## Goals

### Primary Goals

1. **Universal Search Interface**: Provide a single, consistent tool that works across diverse directory types (medical professionals, products, services, consultants, etc.)

2. **Minimal-Code Configuration**: Enable new directory types with one-time mapper function + YAML schema; subsequent data imports require no code changes

3. **Multi-Tenant Support**: Isolate data and searches by account, allowing each customer to maintain their own directory lists

4. **LLM-Friendly**: Guide AI agents to make intelligent searches using natural language mappings and search strategies

5. **Performance**: Fast queries even with large datasets (thousands of entries) using PostgreSQL full-text search and indexes

### Secondary Goals

- **Flexible Filtering**: Support name search, tag filtering, and JSONB field filters in a single query
- **Relevance Ranking**: Return most relevant results first using weighted full-text search
- **Type Safety**: Validate directory structure and searchable fields through schema definitions
- **Extensibility**: Easy to add new search modes, fields, or capabilities without breaking existing functionality

## Applications

### Current Use Cases

#### 1. Healthcare: Medical Professional Directory
**Scenario**: Wyckoff Hospital needs patients to find doctors by specialty, language, and location

**Directory Type**: `medical_professional`
- **Entries**: 124 doctors with specialties, departments, languages, certifications
- **Searchable Fields**: name, specialty, department, gender, education
- **Tags**: Languages spoken (English, Spanish, Hindi, Mandarin, etc.)
- **Natural Language**: "Find me a Spanish-speaking cardiologist" → Tool call with filters

**Configuration**: `backend/config/directory_schemas/medical_professional.yaml`

#### 2. Products: E-Commerce Catalog
**Scenario**: Online store needs customers to find products by category, brand, and features

**Directory Type**: `product` (example)
- **Entries**: Electronics, furniture, clothing
- **Searchable Fields**: name, category, brand, price_range, in_stock
- **Tags**: Product categories, features
- **Natural Language**: "Show me Dell laptops under $1000" → Tool call with filters

**Configuration**: `backend/config/directory_schemas/product.yaml` (to be created)

#### 3. Services: Professional Services Directory
**Scenario**: Business needs to match clients with consultants by expertise and availability

**Directory Type**: `consultant` (example)
- **Entries**: Contractors, experts, freelancers
- **Searchable Fields**: name, expertise, years_experience, hourly_rate
- **Tags**: Skills, certifications
- **Natural Language**: "Find a Python expert available next week" → Tool call with filters

**Configuration**: `backend/config/directory_schemas/consultant.yaml` (to be created)

#### 4. Education: Tutor Matching
**Scenario**: Tutoring service needs students to find tutors by subject and availability

**Directory Type**: `tutor` (example)
- **Entries**: Tutors with subjects, grade levels, availability
- **Searchable Fields**: name, subjects, grade_levels, availability
- **Tags**: Teaching methods, certifications
- **Natural Language**: "Find a math tutor for high school" → Tool call with filters

**Configuration**: `backend/config/directory_schemas/tutor.yaml` (to be created)

## Design Principles

### 1. Generic Tool Signature

The `search_directory` tool accepts generic parameters that work across all directory types:

```python
async def search_directory(
    ctx: RunContext[SessionDependencies],
    list_name: str,              # Which directory list to search
    query: Optional[str] = None,  # Name/text search (FTS or substring)
    tag: Optional[str] = None,    # Tag filter (language, category, etc.)
    filters: Optional[Dict[str, str]] = None,  # Type-specific JSONB filters
) -> str:
```

**Key Design Decisions**:
- **No Type-Specific Parameters**: Tool signature doesn't mention "specialty", "category", or "expertise"
- **Flexible Filters**: The `filters` dict can contain any fields defined in the schema
- **Tag Generalization**: Tags work for languages (medical), categories (products), or skills (consultants)

### 2. Schema-Driven Configuration

Each directory type is defined in a YAML schema file that contains:

1. **Entry Structure**: Required and optional fields
2. **Searchable Fields**: Which fields can be used in filters
3. **Tags Usage**: How tags are populated and what they represent
4. **Search Strategy**: Natural language mappings (lay terms → formal terms)
5. **Examples**: Concrete tool call examples for the LLM

**Example Structure**:
```yaml
entry_type: medical_professional  # Or product, consultant, tutor, etc.
required_fields:
  - department
  - specialty
searchable_fields:
  specialty:
    type: string
    description: "Medical specialty"
    examples: ["Cardiology", "Pediatrics"]
search_strategy:
  synonym_mappings:
    - lay_terms: ["heart doctor", "cardiac specialist"]
      formal_terms: ["Cardiology", "Interventional Cardiology"]
```

### 3. Multi-Tenant Data Isolation

Each directory list is scoped to an account:

```python
# Database structure ensures tenant isolation
DirectoryList(
    account_id=UUID,      # Tenant identifier
    list_name="doctors",  # Directory type
    schema_file="medical_professional.yaml"
)

DirectoryEntry(
    directory_list_id=UUID,  # Links to parent list (includes account_id)
    name="Dr. Smith",
    entry_data={"specialty": "Cardiology"}  # Type-specific data
)
```

**Benefits**:
- Each account sees only their data
- Same directory type (e.g., "doctors") can have different content per account
- Queries automatically filter by account

### 4. LLM Prompt Generation

The system automatically generates LLM-friendly documentation from the schema:

**Input** (Schema YAML):
```yaml
search_strategy:
  synonym_mappings:
    - lay_terms: ["heart doctor"]
      medical_specialties: ["Cardiology"]
```

**Output** (System Prompt):
```
**Medical Term Mappings (Lay → Formal):**
  • "heart doctor" → "Cardiology"

**Example:** "Find a heart doctor"
  → Call: search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
```

This teaches the LLM to translate natural language queries into correct tool calls.

## Flexibility: Adding New Directory Types

### Zero-Code Configuration Process

To add a new directory type (e.g., "barbers" for a barbershop):

#### Step 1: Create Schema File
**File**: `backend/config/directory_schemas/barber.yaml`

```yaml
entry_type: barber
schema_version: "1.0"
description: "Schema for barber shop professionals"

required_fields:
  - specialties  # e.g., "Men's cuts", "Coloring", "Beard trim"
  - years_experience

optional_fields:
  - certifications
  - availability
  - price_range

searchable_fields:
  specialties:
    type: string
    description: "Services offered"
    examples:
      - "Men's haircuts"
      - "Hair coloring"
      - "Beard styling"
  
  years_experience:
    type: integer
    description: "Years of professional experience"
    examples: [1, 5, 10, 15]
  
  price_range:
    type: string
    description: "Price tier"
    examples: ["$", "$$", "$$$"]

tags_usage:
  description: "Specializations or techniques"
  examples:
    - "Fade specialist"
    - "Color expert"
    - "Classic cuts"

search_strategy:
  guidance: |
    **BEFORE searching, think step-by-step:**
    1. What service does the user need?
    2. Use 'filters' for specialties, NOT 'query'
    3. Use 'query' only for barber names
  
  synonym_mappings:
    - lay_terms: ["haircut", "cut", "trim"]
      formal_terms: ["Men's haircuts", "Hair cutting"]
    
    - lay_terms: ["coloring", "dye", "highlights"]
      formal_terms: ["Hair coloring", "Color specialist"]
  
  examples:
    - user_query: "Find a barber who does fades"
      tool_calls:
        - 'search_directory(list_name="barbers", filters={"specialties": "Fade"})'
    
    - user_query: "Experienced colorist"
      tool_calls:
        - 'search_directory(list_name="barbers", filters={"specialties": "Hair coloring"}, tag="Color expert")'
```

#### Step 2: Create Field Mapper (One-Time Code Change)
**File**: `backend/app/services/directory_importer.py`

Add a mapper function that transforms CSV columns to DirectoryEntry structure:

```python
@staticmethod
def barber_mapper(row: Dict) -> Dict:
    """Map barber CSV columns to DirectoryEntry fields.
    
    Expected CSV columns:
    - barber_name (required)
    - specialties (comma-separated for entry_data)
    - years_experience, price_range (for entry_data)
    - language (comma-separated for tags)
    - phone, location (for contact_info)
    """
    tags_raw = row.get('language', '').strip()
    tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []
    
    return {
        'name': row.get('barber_name', '').strip(),
        'tags': tags,
        'contact_info': {
            'phone': row.get('phone', ''),
            'location': row.get('location', '')
        },
        'entry_data': {
            'specialties': row.get('specialties', ''),
            'years_experience': int(row.get('years_experience', 0)),
            'price_range': row.get('price_range', ''),
            'certifications': row.get('certifications', '')
        }
    }
```

Then register it in `backend/scripts/seed_directory.py`:
```python
MAPPERS = {
    'medical_professional': DirectoryImporter.medical_professional_mapper,
    'pharmaceutical': DirectoryImporter.pharmaceutical_mapper,
    'product': DirectoryImporter.product_mapper,
    'barber': DirectoryImporter.barber_mapper,  # Add this
}
```

#### Step 3: Prepare CSV Data
**File**: `data/barbers.csv`

```csv
barber_name,specialties,years_experience,price_range,language,certifications,phone,location
John Smith,"Men's haircuts,Beard styling",10,$$,English,Master Barber,555-0123,Main St Shop
Maria Garcia,"Hair coloring,Women's cuts",8,$$$,"English,Spanish",Color Specialist,555-0124,Downtown
```

#### Step 4: Import Data
**Command**:
```bash
python backend/scripts/seed_directory.py \
  --account barbershop-downtown \
  --list barbers \
  --entry-type barber \
  --schema-file barber.yaml \
  --csv data/barbers.csv \
  --mapper barber \
  --description "Downtown Barbershop - Professional Staff"
```

**Delete-and-Replace Strategy**: The script deletes any existing list with the same name before importing, making it idempotent (safe to re-run).

#### Step 5: Configure Agent
**File**: `backend/config/agent_configs/barbershop/main_chat/config.yaml`

```yaml
tools:
  directory:
    enabled: true
    accessible_lists:
      - barbers  # Now accessible to this agent
    search_mode: fts
    max_results: 5
```

**That's it! After the initial mapper is created, importing new data of the same type requires no code changes.**

### Code Changes Required

**One-Time Per Directory Type**:
1. ✏️ Create mapper function in `directory_importer.py` (~20 lines of code)
2. ✏️ Register mapper in `seed_directory.py` MAPPERS dict (1 line)

**Zero Code Changes**:
- ✅ Creating schema YAML files
- ✅ Preparing CSV data files
- ✅ Importing data (run script with different parameters)
- ✅ Configuring agents (YAML only)
- ✅ Updating schemas (YAML only)

**Example**: After creating the `barber_mapper`, you can:
- Import 100 barbers for "Downtown Barbershop" account → No code
- Import 50 barbers for "West Side Cuts" account → No code
- Re-import updated data for any account → No code
- Add new fields to schema → No code (YAML only)

### What Gets Auto-Generated

When the agent loads, the system automatically:

1. **Reads the schema**: `barber.yaml`
2. **Generates prompt docs**: Synonym mappings, examples, searchable fields
3. **Registers the tool**: `search_directory` works with `list_name="barbers"`
4. **Enables queries**: "Find a fade specialist" → `filters={"specialties": "Fade"}`

## File Structure

### Core Files

These files implement the generic directory system:

```
backend/app/
├── services/
│   ├── directory_service.py       # Core search logic (generic - no changes)
│   └── directory_importer.py      # CSV mappers (add new mapper per type)
├── agents/
│   └── tools/
│       ├── directory_tools.py     # Pydantic AI tool (generic - no changes)
│       └── prompt_generator.py    # Auto-generates docs from schema (generic - no changes)
├── models/
│   └── directory.py                # Database models (generic - no changes)
└── scripts/
    └── seed_directory.py           # Import script (register new mapper in MAPPERS dict)
```

**Available Mappers** (as of current implementation):
- `medical_professional`: Doctors, nurses, therapists
- `pharmaceutical`: Prescription drugs, OTC medications
- `product`: E-commerce products, catalog items

### Configuration Files (Update These)

These files define specific directory types:

```
backend/config/
├── directory_schemas/              # Schema definitions
│   ├── medical_professional.yaml   # Doctors, nurses, therapists
│   ├── product.yaml                # E-commerce products (example)
│   ├── consultant.yaml             # Professional services (example)
│   └── barber.yaml                 # Barbershop staff (example)
│
└── agent_configs/
    └── {account}/
        └── {agent}/
            └── config.yaml         # Enables directory tool
```

### Data Files (Import Once)

```
data/
└── {account}/
    ├── doctors.csv      # Medical professionals
    ├── products.csv     # E-commerce catalog
    └── barbers.csv      # Barbershop staff
```

## Adding a New Directory Type: Checklist

- [ ] **Step 1: Create Schema** - `backend/config/directory_schemas/{type}.yaml`
  - Define `entry_type`, `required_fields`, `optional_fields`
  - Define `searchable_fields` with descriptions and examples
  - Define `tags_usage` (what tags represent)
  - Create `search_strategy` with synonym mappings
  - Add concrete `examples` for LLM guidance

- [ ] **Step 2: Create Field Mapper** - `backend/app/services/directory_importer.py` (one-time code)
  - Add `@staticmethod` mapper function (e.g., `barber_mapper`)
  - Map CSV columns to `name`, `tags`, `contact_info`, `entry_data`
  - Register in `backend/scripts/seed_directory.py` MAPPERS dict
  - **Note**: This is a one-time code change per directory type

- [ ] **Step 3: Prepare CSV Data** - CSV file with entries
  - Column names must match what your mapper expects
  - Required fields must be present
  - Tags column (if used) should be comma-separated

- [ ] **Step 4: Import Data** - Run seed script
  ```bash
  python backend/scripts/seed_directory.py \
    --account {account_slug} \
    --list {list_name} \
    --entry-type {entry_type} \
    --csv {path/to/data.csv} \
    --mapper {mapper_name} \
    --description "Optional description"
  ```
  - Verify data in database (`directory_lists`, `directory_entries`)
  - Script uses delete-and-replace strategy (idempotent)

- [ ] **Step 5: Configure Agent** - Update agent config YAML
  - Add list name to `tools.directory.accessible_lists`
  - Set `search_mode` (fts, substring, or exact)
  - Set `max_results` limit

- [ ] **Step 6: Test** - Verify searches work
  - Agent loads without errors
  - Natural language queries translate correctly
  - Results are relevant and properly formatted
  - Filters work as expected

## Advanced Configuration

> **📘 Deep Dive**: See [directory-search-fts-guide.md](directory-search-fts-guide.md) for comprehensive FTS examples, testing queries, performance benchmarks, and troubleshooting tips.

### Search Modes

Configure per agent in `config.yaml`:

```yaml
tools:
  directory:
    search_mode: fts  # Options: exact, substring, fts
```

**exact**: Case-sensitive exact name match
- Use for: Finding specific entries by exact name
- Example: "Dr. John Smith" only matches exact name

**substring** (default): Case-insensitive partial match
- Use for: Backward compatibility, simple name contains
- Example: "smith" matches "John Smith", "Smithson"

**fts**: Full-text search with relevance ranking
- Use for: Natural language queries, word variations
- Example: "cardio" matches "cardiologist", "cardiology"
- Performance: Fastest (GIN index), best relevance

### Custom Fields Per Directory Type

Each schema can define unique fields:

**Medical**:
```yaml
searchable_fields:
  specialty: {type: string}
  board_certifications: {type: text}
```

**Products**:
```yaml
searchable_fields:
  category: {type: string}
  brand: {type: string}
  in_stock: {type: boolean}
```

**Consultants**:
```yaml
searchable_fields:
  expertise: {type: string}
  hourly_rate: {type: integer}
  years_experience: {type: integer}
```

The tool automatically validates filters against the schema and provides helpful error messages.

### Tag Usage Patterns

Tags are flexible arrays that can represent different concepts:

**Medical**: Languages spoken
```yaml
tags: ["English", "Spanish", "Hindi"]
```

**Products**: Categories/features
```yaml
tags: ["Electronics", "Laptop", "Gaming"]
```

**Services**: Skills/certifications
```yaml
tags: ["Python", "AWS", "React"]
```

**Query Example**:
```python
# Find Spanish-speaking doctor
search_directory(list_name="doctors", tag="Spanish")

# Find Python consultant
search_directory(list_name="consultants", tag="Python")

# Find gaming laptops
search_directory(list_name="products", tag="Gaming")
```

## Benefits of This Architecture

### For Developers
- **Minimal coding for new types**: One-time mapper function + YAML schema
- **Reusable after setup**: Import new data with same type without code changes
- **Consistent API**: Same tool signature for all directory types
- **Type safety**: Schema validation prevents errors
- **Easy testing**: Test one search function, works for all types

### For Users (LLM Agents)
- **Natural language works**: Synonym mappings teach correct queries
- **Consistent behavior**: Same search patterns across all directories
- **Smart results**: Full-text search finds relevant matches
- **Fast responses**: Optimized database queries

### For Business
- **Quick deployment**: New directory types in hours (initial setup), minutes (subsequent imports)
- **Multi-tenant**: Serve multiple customers with isolated data
- **Scalable**: Handles thousands of entries per directory
- **Flexible**: Support any structured data (medical, products, services, etc.)
- **Idempotent**: Safe to re-import data (delete-and-replace strategy)

## Common Patterns

### Pattern 1: Specialty/Category Search
**Use Case**: Find entries by their primary classification

**Schema**:
```yaml
searchable_fields:
  specialty:  # Or category, expertise, service_type
    type: string
    examples: ["Cardiology", "Laptops", "Python"]
```

**Query**:
```python
search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
search_directory(list_name="products", filters={"category": "Laptops"})
```

### Pattern 2: Attribute Filtering
**Use Case**: Narrow results by secondary attributes

**Schema**:
```yaml
searchable_fields:
  gender: {type: string}  # Or size, color, experience_level
  price_range: {type: string}
```

**Query**:
```python
search_directory(list_name="doctors", 
                filters={"specialty": "Cardiology", "gender": "female"})
search_directory(list_name="products",
                filters={"category": "Laptops", "price_range": "under_1000"})
```

### Pattern 3: Language/Tag Filtering
**Use Case**: Find entries with specific tags

**Schema**:
```yaml
tags_usage:
  description: "Languages spoken"  # Or skills, certifications, features
  examples: ["English", "Spanish"]
```

**Query**:
```python
search_directory(list_name="doctors", tag="Spanish")
search_directory(list_name="consultants", tag="AWS Certified")
```

### Pattern 4: Name Search + Filters
**Use Case**: Combine text search with filters

**Schema**:
```yaml
# Name column always searchable
searchable_fields:
  department: {type: string}
```

**Query**:
```python
search_directory(list_name="doctors", 
                query="smith",  # Name contains "smith"
                filters={"department": "Surgery"})
```

## Migration Path

If you have an existing directory system and want to migrate:

### Step 1: Analyze Current Data
- What fields do you have?
- What searches do users perform?
- What natural language queries are common?

### Step 2: Create Schema
- Map current fields to schema `searchable_fields`
- Document synonym mappings in `search_strategy`
- Add concrete examples for LLM guidance

### Step 3: Export to CSV
- Export current data to CSV format
- Ensure column names match schema fields
- Handle multi-value fields (comma-separated for tags)

### Step 4: Import and Test
- Import using directory importer
- Test searches against old and new system
- Verify results match expectations

### Step 5: Update Agents
- Enable directory tool in agent configs
- Add list names to `accessible_lists`
- Test natural language queries

## Troubleshooting

### Issue: LLM Uses Wrong Parameter
**Symptom**: Agent uses `query="Cardiology"` instead of `filters={"specialty": "Cardiology"}`

**Solution**: Update `search_strategy.examples` in schema with clear thought process:
```yaml
examples:
  - user_query: "Find a cardiologist"
    thought_process: |
      1. "cardiologist" is a specialty, not a name
      2. I should use filters, not query
      3. Search: filters={"specialty": "Cardiology"}
    tool_calls:
      - 'search_directory(list_name="doctors", filters={"specialty": "Cardiology"})'
```

### Issue: No Results Found
**Symptom**: Search returns "No entries found" for valid queries

**Diagnosis**:
1. Check if data was imported: `SELECT * FROM directory_entries WHERE directory_list_id = ?`
2. Verify filter values match exactly: `SELECT DISTINCT entry_data->>'specialty' FROM directory_entries`
3. Check account isolation: Ensure agent's account_id matches directory_list's account_id

**Solution**: Re-import data or update agent account configuration

### Issue: Slow Searches
**Symptom**: Queries take > 500ms

**Diagnosis**:
1. Check search mode: FTS is fastest for large datasets
2. Verify GIN index exists: `\d directory_entries` in psql
3. Check result limit: Lower `max_results` if returning too many

**Solution**: 
```yaml
tools:
  directory:
    search_mode: fts  # Use full-text search
    max_results: 5    # Limit results
```

## Future Enhancements

### Planned
- [ ] **Fuzzy matching**: Handle typos and misspellings
- [ ] **Range filters**: Support `price: {min: 100, max: 500}`
- [ ] **Sorting options**: Order by relevance, name, date, etc.
- [ ] **Pagination**: Return large result sets in chunks
- [ ] **Cached counts**: Show "Found 47 results" before showing top 5

### Under Consideration
- [ ] **Schema validation**: Validate entry_data against schema on import
- [ ] **Auto-complete**: Suggest completions for partial queries
- [ ] **Related searches**: "People who searched X also searched Y"
- [ ] **Usage analytics**: Track popular searches and optimize

## References

- **Implementation**: [0023-directory-service.md](../project-management/0023-directory-service.md)
- **FTS Guide**: [directory-search-fts-guide.md](directory-search-fts-guide.md) - Testing, performance, troubleshooting
- **Example Schema**: `backend/config/directory_schemas/medical_professional.yaml`
- **Database Models**: `backend/app/models/directory.py`
- **Service Layer**: `backend/app/services/directory_service.py`
- **Pydantic AI Tool**: `backend/app/agents/tools/directory_tools.py`

---

**Key Takeaway**: The Directory Search Tool is designed as a universal, configuration-driven system. Adding new directory types requires only YAML configuration and data import - no code changes needed. This makes it suitable for any business vertical (healthcare, retail, services, education) while maintaining consistency and performance.

