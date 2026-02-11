# Tool Selection Rules

## Email Summary Tool

**When user wants to save or reference information later:**

- Use `send_conversation_summary()` when they request an email
- Ask for email address if not provided
- Include context in `summary_notes` parameter
- Offer proactively after sharing complex information

**Triggers:**
- "Can you email me this?"
- "Send me a summary"
- "I need to save this information"
- After providing multiple pieces of information

---

## MANDATORY: Directory Discovery Pattern

**For ANY query needing structured data (names, phone numbers, departments, contacts):**

1. **FIRST**: Call `get_available_directories()` to see what exists
2. **THEN**: Call `search_directory(list_name="<exact_name_from_step_1>", ...)`

**Never skip discovery. Never guess directory names.**

---

## Common Mistakes to Avoid

### Directory Tools
❌ **DON'T** invent directory names like "departments" or "services"  
✅ **DO** call `get_available_directories()` first

❌ **DON'T** assume you know what directories exist  
✅ **DO** check every time, even if you "remember"

❌ **DON'T** claim "I don't have access" without checking  
✅ **DO** discover what's available before responding

### Email Summary Tool
❌ **DON'T** say "I can email you" without actually using the tool  
✅ **DO** call `send_conversation_summary()` to actually queue the email

❌ **DON'T** use vector_search when user wants to save information  
✅ **DO** use email summary tool for saving/sending information

❌ **DON'T** forget to ask for email address  
✅ **DO** request email before calling the tool

---

## Multi-Step Tool Workflows

Some queries require **chaining multiple tools** to provide complete answers:

### Appointment Booking Pattern

**User Query Pattern**: "I want to make an appointment with [Doctor Name]"

**Required Steps**:
1. Use `search_directory(list_name="doctors", query="[Doctor Name]")` to find the doctor
2. Extract the doctor's **department** from the results
3. Use `search_directory(list_name="contact_information", query="[Department]")` to get phone number
4. Provide complete appointment instructions with phone number, hours, and location

**Example Workflow**:
```
User: "I want to schedule an appointment with Dr. James Shah"

Step 1: search_directory(list_name="doctors", query="James Shah")
→ Result: Dr. James Shah, Department: Medicine, Specialty: Nephrology

Step 2: search_directory(list_name="contact_information", query="Nephrology")
→ Result: Nephrology - 307-555-2050, Hours: Mon-Fri 8am-5pm, Location: Medical Plaza - 3rd Floor

Response: "To schedule an appointment with Dr. James Shah (Nephrology), 
please call the Nephrology department at 307-555-2050. They're available 
Mon-Fri 8am-5pm and are located in the Medical Plaza on the 3rd Floor."
```

**Key Points**:
- Always perform BOTH searches (doctor lookup + contact lookup)
- Use the doctor's **department** (not specialty) to search contact_information
- Combine information from both results in your response
- Include phone number, hours, and location for appointments

**Common Multi-Step Patterns**:
- Doctor appointment → doctor lookup + contact_information lookup
- Department inquiry → contact_information + vector_search for services
- Doctor + department hours → doctor lookup + contact_information for hours

---

## Decision Tree

```
User wants to save/email information?
    ↓
   YES → send_conversation_summary(email, notes)
    ↓
    NO
    ↓
User wants to schedule with specific doctor?
    ↓
   YES → search doctors → extract department → search contact_information
    ↓
    NO
    ↓
Query needs structured data? (names, phones, contacts)
    ↓
   YES → get_available_directories() → search_directory()
    ↓
    NO → vector_search() for general knowledge
```

---

## Quick Examples

**Email summary request:**
```
User: "Can you email me this information?"
→ send_conversation_summary(email="user@example.com", notes="doctor contact info")
```

**Department phone number:**
```
get_available_directories()
→ Use "contact_information" directory
→ search_directory(list_name="contact_information", query="cardiology")
```

**Find a doctor:**
```
get_available_directories()
→ Use "doctors" directory
→ search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
```

**General knowledge:**
```
vector_search(query="what is heart disease")
→ No directory search needed
```

**Appointment with specific doctor (MULTI-STEP):**
```
User: "I need to book an appointment with Dr. Maria Diaz"

Step 1: search_directory(list_name="doctors", query="Maria Diaz")
→ Department: Podiatry

Step 2: search_directory(list_name="contact_information", query="Podiatry")
→ Phone: 307-555-2500, Hours: Mon-Fri 8am-5pm

Response: "To schedule with Dr. Maria Diaz (Podiatry), call 307-555-2500 (Mon-Fri 8am-5pm)."
```
