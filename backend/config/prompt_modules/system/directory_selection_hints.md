## Directory Selection Guide

### Discovery Pattern (REQUIRED)

**Always call `get_available_directories()` first** before searching:
```python
# Step 1: Discover what's available
get_available_directories()
# Returns: ["doctors", "contact_information"] with descriptions

# Step 2: Search the appropriate directory
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

