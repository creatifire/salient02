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

## Decision Tree

```
User wants to save/email information?
    ↓
   YES → send_conversation_summary(email, notes)
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
