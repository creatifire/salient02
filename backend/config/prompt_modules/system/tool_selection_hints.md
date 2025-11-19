# Tool Selection Rules

## MANDATORY: Directory Discovery Pattern

**For ANY query needing structured data (names, phone numbers, departments, contacts):**

1. **FIRST**: Call `get_available_directories()` to see what exists
2. **THEN**: Call `search_directory(list_name="<exact_name_from_step_1>", ...)`

**Never skip discovery. Never guess directory names.**

---

## Common Mistakes to Avoid

❌ **DON'T** invent directory names like "departments" or "services"  
✅ **DO** call `get_available_directories()` first

❌ **DON'T** assume you know what directories exist  
✅ **DO** check every time, even if you "remember"

❌ **DON'T** claim "I don't have access" without checking  
✅ **DO** discover what's available before responding

---

## Decision Tree

```
Query needs structured data? (names, phones, contacts)
    ↓
   YES → get_available_directories() → search_directory()
    ↓
    NO → vector_search() for general knowledge
```

---

## Quick Examples

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
