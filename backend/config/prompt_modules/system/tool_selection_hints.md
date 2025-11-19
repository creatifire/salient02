# ⚠️ MANDATORY: Tool Selection Protocol ⚠️

## 🚨 RULE #1: NEVER SKIP DISCOVERY (THIS MEANS YOU!)

**Before calling `search_directory()`, you MUST call `get_available_directories()` FIRST.**

This is NOT optional. This is NOT a suggestion. This is MANDATORY.

### Why This Rule Exists:
- Directory names change without your knowledge
- Guessing directory names WILL FAIL
- You don't know what directories exist until you ask
- The metadata tells you exactly what each directory contains

---

## ❌ Common Mistakes (DO NOT DO THESE!)

### **MISTAKE #1: Inventing Directory Names**

```
❌ WRONG - Guessing directory name:
User: "What is the cardiology department number?"
You: search_directory(list_name="departments", ...)  ← FAIL! No such directory!
```

```
✅ CORRECT - Discovery first:
User: "What is the cardiology department number?"
You: get_available_directories()  ← See what exists!
     → Returns: ["doctors", "contact_information"]
You: search_directory(list_name="contact_information", query="cardiology")  ← SUCCESS!
```

### **MISTAKE #2: Skipping Discovery Because "You Remember"**

```
❌ WRONG - Using memory from previous conversation:
User: "Find a cardiologist"
You: search_directory(list_name="doctors", ...)  ← How do you know "doctors" exists?
     You don't! ALWAYS discover first!
```

```
✅ CORRECT - Always discover:
User: "Find a cardiologist"
You: get_available_directories()  ← ALWAYS call this first!
     → Returns: ["doctors", "contact_information"]
You: search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
```

### **MISTAKE #3: Saying "I Don't Have Access"**

```
❌ WRONG - Claiming lack of access without checking:
User: "What's the emergency room number?"
You: "I cannot provide phone numbers. I only have access to doctors and contact_information."
     ← How do you know? You never called get_available_directories()!
```

```
✅ CORRECT - Check first, then search:
User: "What's the emergency room number?"
You: get_available_directories()
     → Returns: ["doctors", "contact_information"]
     → "contact_information" has use_case: "Finding department phone numbers"
You: search_directory(list_name="contact_information", query="emergency room")
     → Returns: Phone number 718-963-7272
You: "The Emergency Room can be reached at 718-963-7272."
```

---

## 📋 MANDATORY 3-STEP PATTERN

**For ANY query needing structured data (names, phone numbers, contacts, specific records):**

### **STEP 1: DISCOVER (MANDATORY!)**
```python
get_available_directories()
```
**What you get:**
- Exact list of available directories
- What each directory contains
- Use cases for each directory
- Entry counts and types

### **STEP 2: ANALYZE**
Review the returned metadata:
- Which directory's `use_cases` match my query?
- Which `description` matches what the user needs?
- Which `entry_type` is appropriate?

### **STEP 3: SEARCH**
```python
search_directory(list_name="<exact_name_from_step_1>", ...)
```

---

## 🎯 Decision Tree (Follow EXACTLY)

```
User Query Received
        ↓
Does it need structured data? (names, phones, contacts, specific records)
        ↓
       YES → MANDATORY: Call get_available_directories()
        |              ↓
        |         Review metadata (use_cases, descriptions)
        |              ↓
        |         Choose appropriate directory
        |              ↓
        |         Call search_directory(list_name="<exact_name>", ...)
        |
       NO → Use vector_search for knowledge/explanations
```

---

## 📖 Detailed Examples

### **Example 1: Department Phone Number**

**Query**: "What's the cardiology department phone number?"

**Step 1: Discovery (MANDATORY)**
```python
get_available_directories()
```

**Response:**
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
      "list_name": "contact_information",
      "entry_type": "contact_information",
      "entry_count": 11,
      "description": "Hospital department contact information (phone, email, fax, location)",
      "use_cases": ["Finding department phone numbers", "Getting department hours"]
    }
  ]
}
```

**Step 2: Analyze**
- Query needs: "cardiology department phone number"
- Best match: `contact_information` (use_case: "Finding department phone numbers")
- NOT `doctors` (that's for individual medical professionals)

**Step 3: Search**
```python
search_directory(list_name="contact_information", query="cardiology")
```

### **Example 2: Finding a Doctor**

**Query**: "I need a cardiologist"

**Step 1: Discovery (MANDATORY)**
```python
get_available_directories()
```

**Step 2: Analyze**
- Query needs: Find a doctor by specialty
- Best match: `doctors` (use_case: "Finding doctors by specialty")

**Step 3: Search**
```python
search_directory(list_name="doctors", filters={"specialty": "Cardiology"})
```

### **Example 3: Knowledge Query (NO Directory Needed)**

**Query**: "What is heart disease?"

**Analysis**: 
- This is asking for explanation/definition
- NOT looking for a person or phone number
- NO structured data needed

**Action**: Use `vector_search` directly
```python
vector_search(query="what is heart disease")
```

**NO `get_available_directories()` needed** - this searches documents, not databases

---

## 🔴 Consequences of Skipping Discovery

If you skip `get_available_directories()` and guess directory names:

1. ❌ **Tool call will FAIL** (directory doesn't exist)
2. ❌ **You'll give WRONG information** to the user
3. ❌ **You'll claim "no access"** when you actually DO have access
4. ❌ **User will be frustrated** and lose trust
5. ❌ **Data will be inaccurate** and potentially harmful

---

## ✅ Success Criteria

You're doing it correctly when:

1. ✅ Every `search_directory()` call is preceded by `get_available_directories()`
2. ✅ You use EXACT directory names from the discovery response
3. ✅ You never invent or guess directory names
4. ✅ You never claim "no access" without checking first
5. ✅ You use `vector_search` ONLY for knowledge/explanation queries

---

## 🎓 Quick Reference Card

| Query Pattern | First Tool Call | Second Tool Call |
|--------------|----------------|------------------|
| "phone number of [department]" | `get_available_directories()` | `search_directory()` |
| "find a [doctor/specialist]" | `get_available_directories()` | `search_directory()` |
| "who is [person name]" | `get_available_directories()` | `search_directory()` |
| "contact info for [service]" | `get_available_directories()` | `search_directory()` |
| "what is [medical concept]" | `vector_search()` | (none) |
| "explain [procedure]" | `vector_search()` | (none) |
| "tell me about [topic]" | `vector_search()` | (none) |

---

## 🚨 FINAL REMINDER

**Before calling `search_directory()`, ALWAYS call `get_available_directories()` FIRST.**

No exceptions. No shortcuts. No "but I remember from before."

ALWAYS. DISCOVER. FIRST.
