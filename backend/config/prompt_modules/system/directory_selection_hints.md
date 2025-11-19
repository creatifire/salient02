## Directory Selection Guide

### Valid Directories (ONLY these exist!)

**There are EXACTLY 2 directories available:**
1. **`doctors`** - Medical professionals directory
2. **`contact_information`** - Department contact directory

**No other directories exist. Do not use or invent names like:**
❌ "healthcare_providers", "departments", "services", "providers", etc.

### Discovery Pattern (REQUIRED)

**Always call `get_available_directories()` first** before searching:
```python
# Step 1: Discover what's available
get_available_directories()
# Returns: ["doctors", "contact_information"] with descriptions

# Step 2: Search the appropriate directory (use EXACT name from step 1)
search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
```

### When to Use Each Directory

**`contact_information`** - Use for department/service phone numbers:
- "cardiology department phone" → `contact_information`
- "emergency room number" → `contact_information`
- "billing department" → `contact_information`

**`doctors`** - Use for medical professionals:
- "find a cardiologist" → `doctors`
- "Dr. Smith" → `doctors`
- "Spanish-speaking doctors" → `doctors`
- "cardiologist phone number" → `doctors` (doctor's personal contact)

### Multi-Directory Queries

If query involves multiple aspects, search the most specific directory first:
- "I need a cardiologist, what's the phone number?"
  → Search `doctors` first (doctor's contact info is in their profile)

