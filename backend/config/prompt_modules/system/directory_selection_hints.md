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

---

## Multi-Directory Orchestration

### When to Chain Directory Searches

Some queries require searching **multiple directories in sequence**:

#### Pattern 1: Doctor Appointment Booking (MOST COMMON)

**Query**: "I want to make an appointment with Dr. [Name]"

**Workflow**:
1. Search `doctors` to find doctor and extract their **department**
2. Search `contact_information` using that department name to get phone/hours/location
3. Combine both results in response with complete booking instructions

**Example**:
```
User: "I want to schedule with Dr. Maria Diaz"

Step 1: search_directory(list_name="doctors", query="Maria Diaz")
→ Result: Dr. Maria Diaz, DO
   Department: "Podiatry"
   Specialty: "Podiatric Surgery"

Step 2: search_directory(list_name="contact_information", query="Podiatry")
→ Result: Podiatry Department
   Phone: 307-555-2500
   Hours: Mon-Fri 8am-5pm
   Location: Medical Plaza - 1st Floor

Response: "To schedule an appointment with Dr. Maria Diaz (Podiatric Surgery), 
please call the Podiatry department at 307-555-2500. They're available 
Mon-Fri 8am-5pm and are located in the Medical Plaza on the 1st Floor."
```

#### Pattern 2: Department + Doctor Lookup

**Query**: "Who are the cardiologists and what's their phone number?"

**Workflow**:
1. Search `doctors` with filters for Cardiology
2. Search `contact_information` for Cardiology department contact info
3. Combine doctor names + department contact details

**Example**:
```
search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
→ List of cardiologists

search_directory(list_name="contact_information", query="Cardiology")
→ Phone: 307-555-2000, Hours: Mon-Fri 8am-6pm

Response: List doctors + "To schedule with any of our cardiologists, 
call the Cardiology department at 307-555-2000 (Mon-Fri 8am-6pm)."
```

### Department Name Mapping (CRITICAL!)

**When chaining from doctors → contact_information**:

1. Extract the **exact department name** from doctor results (NOT specialty)
2. Use that department name to search contact_information
3. If department name is generic (like "Medicine"), try the specialty first

**Common Mappings**:
- Doctor department: "Cardiology" → Contact: "Cardiology" ✅
- Doctor department: "Pediatrics" → Contact: "Pediatrics" ✅
- Doctor department: "OB/GYN" → Contact: "OB/GYN" ✅
- Doctor department: "Medicine" + Specialty: "Nephrology" → Try: "Nephrology" first, fallback to "Medicine" ✅
- Doctor department: "Surgery" + Specialty: "Cardiothoracic Surgery" → Try: "Surgery" ✅

**Best Practice**:
- Always use the **department** field from doctor results
- If department is too generic (Medicine, Surgery), try specialty name first
- Include hours and location in your appointment instructions

