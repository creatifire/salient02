## Directory Selection Hints

### Multi-Directory Orchestration

**If a query involves multiple aspects**:
1. Search the most specific directory first
2. Combine results if relevant to the query
3. Example: 'I need a cardiologist, what's the phone number?'
   - First: Search `doctors` for cardiologists → Get doctor's contact info
   - Then: If scheduling mentioned, check `phone_directory` for appointments

---

**Pattern: Department/Service + Phone/Number**

When the query mentions BOTH a department/service name AND phone/number/contact:
- ✅ Use `phone_directory` (contains department contact information)
- ❌ Don't use `doctors` (contains individual medical professionals)

Examples:
- "pediatrics department phone" → search `phone_directory` for "Pediatrics"
- "emergency department number" → search `phone_directory` for "Emergency Department"
- "billing department contact" → search `phone_directory` for "Billing"

**Pattern: Doctor/Specialty Name**

When the query mentions a doctor's name OR medical specialty:
- ✅ Use `doctors` (contains medical professional info)
- ❌ Don't use `phone_directory`

Examples:
- "find a cardiologist" → search `doctors` for specialty
- "Dr. Smith" → search `doctors` for name

**Pattern: Doctor's Contact Info**

When the query asks for a specific doctor's phone/contact:
- ✅ Use `doctors` (doctor records include contact_info)
- ❌ Don't search `phone_directory` (doesn't list individual doctors)

Example:
- "cardiologist phone number" → search `doctors` for cardiology, return contact_info

