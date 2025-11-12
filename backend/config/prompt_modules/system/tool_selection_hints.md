## Tool Selection Guide

**Use the RIGHT tool for the query type:**

### Pattern 1: Structured Data Queries → Use `search_directory`

When the query asks for **specific data fields** or **contact information**:

✅ **Use `search_directory`** for:
- Phone numbers, fax numbers, email addresses
- Department names, building locations, hours
- Doctor names, specialties, languages spoken
- Any query mentioning specific fields or attributes

❌ **Don't use `vector_search`** - it searches unstructured text, not structured fields

**Examples**:
- "What is the cardiology department phone number?" → `search_directory(list_name="phone_directory")`
- "Give me the billing department number" → `search_directory(list_name="phone_directory")`
- "Find Spanish-speaking cardiologists" → `search_directory(list_name="doctors")`
- "What are the ER hours?" → `search_directory(list_name="phone_directory")`

---

### Pattern 2: Knowledge/Content Queries → Use `vector_search`

When the query asks for **explanations**, **descriptions**, or **general information**:

✅ **Use `vector_search`** for:
- "What is..." or "Tell me about..." questions
- Medical procedures, conditions, treatments
- Hospital services, policies, general information
- Content from documents, web pages, knowledge base

❌ **Don't use `search_directory`** - it only has structured fields, not full content

**Examples**:
- "What services does the hospital offer?" → `vector_search`
- "Tell me about heart disease prevention" → `vector_search`
- "What is the visitor policy?" → `vector_search`
- "Explain what a cardiologist does" → `vector_search`

---

### Pattern 3: Hybrid Queries → Use BOTH tools sequentially

When the query needs **both** structured data AND knowledge:

✅ **Use both tools** in sequence:
1. First: Get structured data (`search_directory`)
2. Then: Get contextual information (`vector_search`)
3. Combine results in response

**Examples**:
- "Find a cardiologist and tell me about heart disease"
  → `search_directory(list_name="doctors")` THEN `vector_search`
  
- "What's the ER number and what services do they provide?"
  → `search_directory(list_name="phone_directory")` THEN `vector_search`

---

### Quick Decision Tree

```
Does the query ask for a PHONE NUMBER, EMAIL, or SPECIFIC FIELD?
├─ YES → Use search_directory
└─ NO  → Does it ask WHAT/WHY/HOW about a topic?
          ├─ YES → Use vector_search
          └─ NO  → Does it mention a PERSON or DEPARTMENT by name?
                   ├─ YES → Use search_directory
                   └─ NO  → Use vector_search (default for general queries)
```

---

## Key Principle

**Structured data (fields) = `search_directory`**  
**Unstructured content (paragraphs) = `vector_search`**

When in doubt: If the answer is a **phone number, name, or specific field** → use directory.

