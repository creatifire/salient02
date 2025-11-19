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

### Common Request Examples

#### `contact_information` Directory Examples

**1. "What's the cardiology department phone number?"**
```python
get_available_directories()
search_directory(list_name="contact_information", query="cardiology")
# Returns: department name, phone, email, hours, location
```

**2. "How do I reach the emergency room?"**
```python
get_available_directories()
search_directory(list_name="contact_information", query="emergency")
# Returns: emergency department contact info
```

**3. "What's the billing department number?"**
```python
get_available_directories()
search_directory(list_name="contact_information", filters={"service_type": "billing"})
# Returns: billing department contact details
```

**4. "Where is the radiology department located?"**
```python
get_available_directories()
search_directory(list_name="contact_information", query="radiology")
# Returns: location, phone, hours
```

**5. "What are the hours for the pharmacy?"**
```python
get_available_directories()
search_directory(list_name="contact_information", query="pharmacy")
# Returns: hours_of_operation, phone, location
```

#### `doctors` Directory Examples

**1. "Find me a cardiologist"**
```python
get_available_directories()
search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
# Returns: list of cardiologists with name, specialty, languages, contact info
```

**2. "Do you have Spanish-speaking doctors?"**
```python
get_available_directories()
search_directory(list_name="doctors", tag="Spanish")
# Returns: all doctors who speak Spanish, with their specialties
```

**3. "I need a gastroenterologist who speaks Hindi"**
```python
get_available_directories()
search_directory(list_name="doctors", filters={"specialty": "Gastroenterology"}, tag="Hindi")
# Returns: Hindi-speaking gastroenterologists
```

**4. "Find Dr. Patel"**
```python
get_available_directories()
search_directory(list_name="doctors", query="Patel")
# Returns: all doctors with "Patel" in their name
```

**5. "What heart doctors do you have?"**
```python
get_available_directories()
search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
# Returns: cardiologists with full details including languages spoken
```

### Multi-Directory Queries

If query involves multiple aspects, search the most specific directory first:
- "I need a cardiologist, what's the phone number?"
  → Search `doctors` first (doctor's contact info is in their profile)

