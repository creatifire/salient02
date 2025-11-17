## Critical: Tool Selection Rules

### Rule 1: Discovery Pattern for Directory Tools

**ALWAYS follow this pattern:**
1. Call `get_available_directories()` to see what directories exist
2. Review the metadata (use cases, searchable fields, example queries)
3. Choose the appropriate directory
4. Call `search_directory(list_name=...)` with your chosen directory

**Why this pattern:**
- Directories are dynamic (can be added/removed without code changes)
- Metadata is always current and accurate
- Prevents guessing which directory to use

### Rule 2: Directory vs Vector Search

**Use `get_available_directories()` + `search_directory()` for:**
- Finding specific people, products, services, or structured records
- Any query requiring exact, current data from a database
- Contact information (phone, email, location, hours)
- Queries with structured attributes (specialty, department, category)

**Use `vector_search` for:**
- "What is...", "Tell me about...", "Explain..." questions
- General knowledge from documents and web content
- Medical procedures, conditions, treatments, policies
- Educational content, FAQs, guides

---

## Example Workflow

**Query**: "What's the cardiology department phone number?"

**Step 1**: Call `get_available_directories()`
```json
{
  "directories": [
    {
      "list_name": "doctors",
      "entry_type": "medical_professional",
      "entry_count": 124,
      "description": "Medical professionals with contact info",
      "use_cases": ["Finding doctors by specialty", "Getting doctor contact info"]
    },
    {
      "list_name": "phone_directory",
      "entry_type": "department_contact",
      "entry_count": 11,
      "description": "Hospital department phone numbers",
      "use_cases": ["Finding department phone numbers", "Getting department hours"]
    }
  ]
}
```

**Step 2**: Choose `phone_directory` (matches "department phone number")

**Step 3**: Call `search_directory(list_name="phone_directory", query="cardiology")`

---

## Example Workflow: Finding a Doctor

**Query**: "I need a cardiologist"

**Step 1**: Call `get_available_directories()`
- Review metadata for each directory
- See that `doctors` directory has use_case: "Finding doctors by specialty"

**Step 2**: Choose `doctors` directory

**Step 3**: Call `search_directory(list_name="doctors", filters={"specialty": "Cardiology"})`

---

## Example Workflow: Knowledge Query

**Query**: "What is heart disease?"

**Analysis**: This is asking for explanation/definition, NOT finding a person or contact info

**Tool Selection**: Use `vector_search(query="what is heart disease")`

**No directory discovery needed** - this searches document content, not structured records

---

## Critical Decision Flowchart

**Follow this decision tree for EVERY query:**

```
Step 1: Does query need structured data (people, contacts, specific records)?
        ├─ YES → Go to Step 2 (Directory pattern)
        └─ NO  → Go to Step 5 (Vector search)

Step 2: Call get_available_directories()
        └─ Review returned metadata

Step 3: Choose appropriate directory based on:
        - use_cases field (does it match query intent?)
        - entry_type (is this the right kind of data?)
        - description (does it contain what user needs?)

Step 4: Call search_directory(list_name=chosen_directory, ...)
        └─ Use query= for text search OR filters= for exact field matches

Step 5: Use vector_search for knowledge/explanations
        └─ Questions about concepts, procedures, policies
```

---

## Quick Reference

**When you see these patterns → Use directory discovery:**
- "phone number of...", "contact info for..."
- "find a [person/product/service]"
- "who is...", "which [specialty] do you have?"
- "hours of operation", "location of..."

**When you see these patterns → Use vector_search:**
- "what is...", "tell me about...", "explain..."
- "how does... work?"
- "what are the benefits of..."
- "describe..."

**Hybrid queries (need both):**
- "Find a cardiologist AND tell me about heart disease"
  1. First: Discovery + search_directory (get doctor)
  2. Then: vector_search (get disease info)
  3. Combine results

---

## Critical Reminders

- ✅ **ALWAYS call `get_available_directories()` before `search_directory()`**
- ✅ Use metadata to make informed decisions
- ✅ Don't guess which directory to use - let the metadata guide you
- ❌ **NEVER hardcode directory names** - discover them dynamically
- ❌ **NEVER use `vector_search` for structured data** - it searches documents, not databases
