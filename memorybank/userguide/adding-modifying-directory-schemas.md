# Adding and Modifying Directory Schemas

## Overview

This guide explains how to create new directory schemas or modify existing ones. Directory schemas define what types of structured information your AI agents can search through.

**When to add a new schema:**
- You have a new type of data that doesn't fit existing schemas
- You need specialized fields for a specific use case
- You're building a new vertical or industry application

**When to modify an existing schema:**
- You need additional optional fields
- You want to add search synonyms or examples
- You need to clarify the schema's purpose

---

## Part 1: Creating a Schema File

### Step 1: Choose Your Schema Name

Schema names should be:
- **Singular** (e.g., `service` not `services`)
- **Descriptive** (e.g., `medical_professional` not just `person`)
- **Lowercase with underscores** (e.g., `contact_information`)

### Step 2: Create the YAML File

**Location**: `backend/config/directory_schemas/{schema_name}.yaml`

**Template**:

```yaml
# Schema metadata
entry_type: "{schema_name}"
version: "1.0"
description: "Brief description of what this schema represents"

# Purpose and use cases
directory_purpose: |
  Detailed explanation of what this directory is for and when to use it.
  
  Example use cases:
  - Use case 1
  - Use case 2
  - Use case 3

# Searchable fields (for LLM guidance)
searchable_fields:
  - field_name_1  # Comment explaining what this field is
  - field_name_2
  - field_name_3

# Required fields (database schema - not actually enforced, but document intent)
required_fields:
  name:
    type: string
    description: "Primary name/title of the entry"
  
  {key_field}:
    type: string
    description: "Key identifying field for this entry type"

# Optional fields (document all available fields)
optional_fields:
  field_1:
    type: string
    description: "Description of field_1"
  
  field_2:
    type: array
    items: string
    description: "List of items"
  
  field_3:
    type: boolean
    description: "True/false flag"
  
  field_4:
    type: number
    description: "Numeric value"

# Contact information (available on all schemas)
contact_fields:
  phone:
    type: string
    description: "Phone number"
  email:
    type: string
    description: "Email address"
  fax:
    type: string
    description: "Fax number"
  location:
    type: string
    description: "Physical location"
  product_url:
    type: string
    description: "Website URL"

# Search strategy (helps LLM understand how to search this directory)
search_strategy:
  natural_language: |
    Guidance for the LLM on how to interpret natural language queries.
    
    Example mappings:
    - "lay term" → "technical term"
    - "common phrase" → "field value"
  
  synonym_mappings:
    lay_term:
      - "synonym 1"
      - "synonym 2"
    
    technical_term:
      - "formal name 1"
      - "formal name 2"
  
  example_queries:
    - "Example user question 1?"
    - "Example user question 2?"
    - "Example user question 3?"

# When NOT to use this schema (disambiguation)
not_for:
  - "Don't use for X (use {other_schema} instead)"
  - "Don't use for Y (use {another_schema} instead)"

# Examples (help users understand the structure)
examples:
  - name: "Example Entry 1"
    {key_field}: "Value"
    field_1: "Example value"
    field_2: ["Item 1", "Item 2"]
    contact_info:
      phone: "555-123-4567"
      location: "Building A"
  
  - name: "Example Entry 2"
    {key_field}: "Another value"
    field_1: "Different example"
    contact_info:
      email: "example@company.com"
```

### Step 3: Fill In Your Schema

**Example: Creating a `course.yaml` schema for educational courses**

```yaml
entry_type: "course"
version: "1.0"
description: "Educational courses, training programs, and workshops"

directory_purpose: |
  This directory contains information about courses, training programs, workshops,
  and educational offerings.
  
  Use this directory when users ask about:
  - Available courses or training
  - Course schedules and duration
  - Prerequisites and requirements
  - Certification programs
  - Cost and enrollment information

searchable_fields:
  - course_code      # Unique course identifier (e.g., "CS101")
  - subject_area     # Subject or department (e.g., "Computer Science")
  - instructor_name  # Who teaches the course
  - skill_level      # Beginner, Intermediate, Advanced
  - format           # Online, In-person, Hybrid

required_fields:
  name:
    type: string
    description: "Course title"
  
  course_code:
    type: string
    description: "Unique course identifier"

optional_fields:
  subject_area:
    type: string
    description: "Subject or department"
  
  duration:
    type: string
    description: "How long the course takes (e.g., '6 weeks', '3 months')"
  
  skill_level:
    type: string
    description: "Beginner, Intermediate, or Advanced"
  
  format:
    type: string
    description: "Delivery format: Online, In-person, or Hybrid"
  
  instructor_name:
    type: string
    description: "Primary instructor"
  
  prerequisites:
    type: array
    items: string
    description: "Required prior courses or knowledge"
  
  cost:
    type: string
    description: "Course fee"
  
  credits:
    type: number
    description: "Academic or professional credits earned"
  
  schedule:
    type: string
    description: "When the course meets"
  
  enrollment_limit:
    type: number
    description: "Maximum number of students"
  
  certification:
    type: boolean
    description: "Whether completion provides a certificate"

contact_fields:
  phone:
    type: string
    description: "Registration phone number"
  email:
    type: string
    description: "Course coordinator email"
  location:
    type: string
    description: "Physical classroom location (for in-person)"
  product_url:
    type: string
    description: "Course registration or info URL"

search_strategy:
  natural_language: |
    When users ask about courses or training:
    
    1. Look for subject keywords → match against subject_area
    2. Look for skill level hints ("beginner", "advanced") → match skill_level
    3. Look for format preferences ("online", "in-person") → match format
    4. Look for instructor names → match instructor_name
  
  synonym_mappings:
    programming:
      - "Computer Science"
      - "Software Development"
      - "Coding"
    
    beginner:
      - "Introduction"
      - "Fundamentals"
      - "Basics"
    
    online:
      - "Remote"
      - "Virtual"
      - "Distance learning"
  
  example_queries:
    - "What programming courses do you offer?"
    - "Are there any beginner courses in data analysis?"
    - "Can I take courses online?"
    - "What are the prerequisites for advanced statistics?"

not_for:
  - "Don't use for finding instructors' contact info (use medical_professional or contact_information)"
  - "Don't use for school location info (use location)"
  - "Don't use for general FAQs (use faq)"

examples:
  - name: "Introduction to Python Programming"
    course_code: "CS101"
    subject_area: "Computer Science"
    duration: "8 weeks"
    skill_level: "Beginner"
    format: "Online"
    instructor_name: "Dr. Jane Smith"
    prerequisites: []
    cost: "$299"
    credits: 3
    schedule: "Tuesdays and Thursdays, 6-8 PM"
    certification: true
    contact_info:
      email: "cs101@university.edu"
      product_url: "https://university.edu/courses/cs101"
  
  - name: "Advanced Machine Learning"
    course_code: "CS401"
    subject_area: "Computer Science"
    duration: "12 weeks"
    skill_level: "Advanced"
    format: "Hybrid"
    instructor_name: "Dr. Robert Chen"
    prerequisites: ["CS301 - Intermediate ML", "MATH205 - Linear Algebra"]
    cost: "$599"
    credits: 4
    schedule: "Mondays 6-9 PM (online) + Saturday labs (in-person)"
    enrollment_limit: 20
    certification: true
    contact_info:
      email: "cs401@university.edu"
      location: "Tech Building, Room 305"
      product_url: "https://university.edu/courses/cs401"
```

---

## Part 2: Adding Code Support in directory_tools.py

### Step 4: Open directory_tools.py

**File**: `backend/app/agents/tools/directory_tools.py`

### Step 5: Locate the Schema Handler Section

Find the section that starts with:

```python
# Add type-specific fields from entry_data (flatten based on entry_type)
entry_type = entry.directory_list.entry_type
```

This is around **line 306** in the current file.

### Step 6: Add Your Schema Handler

Add an `elif` block for your new schema type:

```python
elif entry_type == "{your_schema_name}":
    if entry.entry_data.get('{field_1}'):
        result["{output_key_1}"] = entry.entry_data['{field_1}']
    if entry.entry_data.get('{field_2}'):
        result["{output_key_2}"] = entry.entry_data['{field_2}']
    # ... add all fields you want to return
```

**Rules**:
1. Use `if entry.entry_data.get('field_name')` for optional fields
2. Use `if entry.entry_data.get('field_name') is not None` for boolean/numeric fields (to handle `False` or `0`)
3. Output keys can be different from input keys (e.g., `manager_name` → `manager`)
4. Arrays and objects are passed through as-is (JSON handles them)

### Step 7: Example Implementation

**For our `course` schema:**

```python
elif entry_type == "course":
    if entry.entry_data.get('course_code'):
        result["course_code"] = entry.entry_data['course_code']
    if entry.entry_data.get('subject_area'):
        result["subject_area"] = entry.entry_data['subject_area']
    if entry.entry_data.get('duration'):
        result["duration"] = entry.entry_data['duration']
    if entry.entry_data.get('skill_level'):
        result["skill_level"] = entry.entry_data['skill_level']
    if entry.entry_data.get('format'):
        result["format"] = entry.entry_data['format']
    if entry.entry_data.get('instructor_name'):
        result["instructor"] = entry.entry_data['instructor_name']
    if entry.entry_data.get('prerequisites'):
        result["prerequisites"] = entry.entry_data['prerequisites']
    if entry.entry_data.get('cost'):
        result["cost"] = entry.entry_data['cost']
    if entry.entry_data.get('credits') is not None:
        result["credits"] = entry.entry_data['credits']
    if entry.entry_data.get('schedule'):
        result["schedule"] = entry.entry_data['schedule']
    if entry.entry_data.get('enrollment_limit') is not None:
        result["enrollment_limit"] = entry.entry_data['enrollment_limit']
    if entry.entry_data.get('certification') is not None:
        result["certification"] = entry.entry_data['certification']
```

### Step 8: Check Placement

Your new handler should be added **before the final line** that appends the result:

```python
elif entry_type == "your_new_schema":
    # Your handler code
    ...

results.append(result)  # This line stays at the end
```

---

## Part 3: Testing Your New Schema

### Step 9: Create Test Data

**Option A: Use the database directly**

Import your data using the existing directory import tools (see `backend/app/services/directory_importer.py`).

**Option B: Create a test script**

Create `backend/tests/manual/test_{schema_name}_search.py`:

```python
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import json
from uuid import UUID
from sqlalchemy import select
from app.agents.tools.directory_tools import get_available_directories, search_directory
from app.database import get_database_service
from app.models.account import Account
from pydantic_ai.models.test import TestModel
from pydantic_ai import RunContext
import yaml

class MockDeps:
    def __init__(self, account_id, agent_config):
        self.account_id = account_id
        self.agent_config = agent_config

async def get_account_id(account_slug: str) -> UUID:
    """Query database for account UUID."""
    db_service = get_database_service()
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        result = await session.execute(
            select(Account).where(Account.slug == account_slug)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise ValueError(f"Account '{account_slug}' not found in database")
        
        return account.id

async def test_schema_search():
    """Test new schema search functionality"""
    
    # Initialize database
    db_service = get_database_service()
    await db_service.initialize()
    
    # Get account UUID
    account_id = await get_account_id("your_account_name")
    print(f"Using account ID: {account_id}\n")
    
    # Load agent config
    config_path = Path(__file__).parent.parent.parent / "config" / "agent_configs" / "your_account" / "your_agent" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create mock context
    ctx = RunContext(
        deps=MockDeps(
            account_id=account_id,
            agent_config=config
        ),
        model=TestModel(),
        usage=None,
        prompt='test'
    )
    
    print("=" * 80)
    print("TEST 1: Get Available Directories")
    print("=" * 80)
    result1 = await get_available_directories(ctx)
    dirs_json = json.loads(result1)
    print(json.dumps(dirs_json, indent=2))
    print()
    
    print("=" * 80)
    print("TEST 2: Search by key field")
    print("=" * 80)
    result2 = await search_directory(ctx, list_name="courses", filters={"subject_area": "Computer Science"})
    courses_json = json.loads(result2)
    print(json.dumps(courses_json, indent=2))
    
    # Verify fields
    if courses_json['total'] > 0:
        first_entry = courses_json['entries'][0]
        print(f"\n✅ Entry type: {first_entry.get('entry_type', 'MISSING')}")
        print(f"✅ Fields returned: {', '.join(first_entry.keys())}")
    print()
    
    print("=" * 80)
    print("TEST 3: Search by query")
    print("=" * 80)
    result3 = await search_directory(ctx, list_name="courses", query="beginner")
    search_json = json.loads(result3)
    print(f"Found {search_json['total']} results for 'beginner'")
    if search_json['total'] > 0:
        print(json.dumps(search_json['entries'][0], indent=2))

if __name__ == "__main__":
    asyncio.run(test_schema_search())
```

### Step 10: Run Your Test

```bash
cd backend
python tests/manual/test_course_search.py
```

**Expected output:**
- ✅ JSON structure returned
- ✅ All your schema fields present
- ✅ Contact fields included if provided
- ✅ Search works with filters and query

---

## Part 4: Update Agent Configuration

### Step 11: Add Schema to Agent Config

**File**: `backend/config/agent_configs/{account}/{agent}/config.yaml`

Add your new directory to the `accessible_lists`:

```yaml
tools:
  directory:
    enabled: true
    accessible_lists:
      - doctors
      - contact_information
      - courses  # <-- Add your new schema here
```

### Step 12: Test with Real Agent

Start your application and test queries:

```
"What programming courses do you offer?"
"Are there any beginner courses available?"
"What are the prerequisites for advanced courses?"
```

---

## Part 5: Modifying Existing Schemas

### To Add a New Optional Field

1. **Update the schema YAML**: Add field to `optional_fields` section
2. **Update directory_tools.py**: Add `if` check for the new field
3. **Update data**: Import entries with the new field
4. **Test**: Verify field appears in JSON output

**Example**: Adding `accreditation` to `course.yaml`:

```yaml
# In course.yaml
optional_fields:
  # ... existing fields ...
  accreditation:
    type: string
    description: "Accrediting body (e.g., ABET, AACSB)"
```

```python
# In directory_tools.py, in the "course" handler
if entry.entry_data.get('accreditation'):
    result["accreditation"] = entry.entry_data['accreditation']
```

### To Update Search Strategy

1. **Update schema YAML**: Modify `search_strategy` section
2. **No code changes needed**: Search strategy is guidance for the LLM
3. **Test**: Try queries using new synonyms/examples

### To Change Required Fields

⚠️ **Warning**: Changing required fields affects existing data.

1. Update schema YAML
2. Update database entries to comply
3. Update validation if implemented
4. Test thoroughly

---

## Checklist

When adding a new schema, ensure:

- [ ] Schema YAML created in `backend/config/directory_schemas/`
- [ ] All required fields documented
- [ ] All optional fields documented
- [ ] Search strategy includes examples and synonyms
- [ ] `not_for` section disambiguates from other schemas
- [ ] Handler added to `directory_tools.py`
- [ ] All important fields included in handler
- [ ] Boolean/numeric fields use `is not None` check
- [ ] Test script created and passes
- [ ] Agent config updated to include new directory
- [ ] Real queries tested with agent
- [ ] User guide updated if public-facing

---

## Common Pitfalls

### 1. Missing Fields in Output

**Problem**: Added field to schema but doesn't appear in results

**Solution**: Check that you added the handler code in `directory_tools.py`

### 2. Boolean False Not Returned

**Problem**: Boolean field with `False` value doesn't appear in output

**Solution**: Use `is not None` instead of truthiness check:

```python
# ❌ Wrong
if entry.entry_data.get('certification'):
    result["certification"] = entry.entry_data['certification']

# ✅ Correct
if entry.entry_data.get('certification') is not None:
    result["certification"] = entry.entry_data['certification']
```

### 3. Agent Can't Find Directory

**Problem**: Agent says directory not available

**Solutions**:
- Check spelling in `accessible_lists` matches schema `entry_type`
- Verify directory has entries in database
- Check account_id matches in agent config

### 4. Search Returns Empty Results

**Problem**: Directory exists but searches return nothing

**Solutions**:
- Verify data imported with correct `entry_type`
- Check `list_name` parameter matches `entry_type`
- Confirm account_id association in database

### 5. Schema Handler Not Running

**Problem**: Added handler but it's not being used

**Solutions**:
- Check `elif` block placement (should be before `results.append(result)`)
- Verify `entry_type` in database matches schema name
- Check indentation (Python-sensitive)

---

## Advanced: Schema Versioning

If you need to make breaking changes to a schema:

1. **Create a new version**: `course_v2.yaml`
2. **Update entry_type**: `course_v2`
3. **Keep old handler**: Don't remove `course` handler
4. **Add new handler**: Add `course_v2` handler
5. **Migrate data**: Gradually move entries to new version
6. **Deprecate old**: Remove old schema when migration complete

---

## Getting Help

**Questions about**:
- **Schema design**: Review existing schemas in `backend/config/directory_schemas/`
- **Code changes**: See `directory_tools.py` for examples of all 11 current schemas
- **Testing**: Look at `backend/investigate/tool-calling/test_direct_search.py`
- **Data import**: Check `backend/app/services/directory_importer.py`

**Documentation**:
- Schema field reference: `memorybank/userguide/agent-configuration-guide.md`
- Architecture: `memorybank/architecture/directory-search-tool.md`
- Data model: `memorybank/architecture/datamodel.md`

---

## Version History

- **v1.0** (2025-01-18): Initial guide covering schema creation and modification

