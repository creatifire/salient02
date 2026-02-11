# BUG: Phone Directory Search Returns No Results

## **Problem**

Session `019a83e2-60a1-777b-871b-4fc7ec88beb0` called the `search_directory` tool with:

```json
{
  "tool_name": "search_directory",
  "args": {
    "list_name": "phone_directory",
    "filters": {"department_name": "Cardiology"}
  }
}
```

**Result**: No results returned (tool had to resort to other methods)

---

## **Root Cause Analysis**

### **Database Investigation**

Query showing "Cardiology" entry EXISTS in database:

```sql
SELECT de.name, de.entry_data, de.contact_info
FROM directory_entries de
JOIN directory_lists dl ON de.directory_list_id = dl.id
JOIN accounts a ON dl.account_id = a.id
WHERE a.slug = 'wyckoff' 
  AND dl.list_name = 'phone_directory'
  AND de.name = 'Cardiology';
```

**Result**:
```json
{
  "name": "Cardiology",
  "entry_data": {
    "description": "Cardiology department direct line",
    "service_type": "Clinical Departments",
    "hours_of_operation": "Mon-Fri 8am-6pm"
  },
  "contact_info": {
    "phone": "718-963-2000",
    "fax": "718-963-2001",
    "email": "cardiology@wyckoffhospital.org",
    "location": "Building A - 3rd Floor"
  }
}
```

**Key Finding**: The `entry_data` JSONB does NOT contain a `department_name` field!

---

### **Code Analysis**

**File**: `backend/app/services/directory_importer.py` (lines 332-374)

The `phone_directory_mapper` function:

1. **CSV column**: `department_name`
2. **Maps to**: `name` field in `DirectoryEntry` (line 370)
3. **NOT stored in**: `entry_data` JSONB

```python
return {
    'name': row.get('department_name', '').strip(),  # <- department_name becomes 'name'
    'tags': tags,
    'contact_info': contact_info,
    'entry_data': entry_data  # <- does NOT include department_name
}
```

**File**: `backend/app/services/directory_service.py` (lines 316-324)

The `search()` method filters JSONB fields:

```python
for key, value in jsonb_filters.items():
    escaped_value = re.escape(value)
    word_boundary_pattern = f"\\m{escaped_value}"
    query = query.where(
        DirectoryEntry.entry_data[key].astext.op('~*')(word_boundary_pattern)
    )
```

**Problem**: When `filters={"department_name": "Cardiology"}` is passed, it searches for `entry_data->>'department_name'` which **doesn't exist**!

---

### **Schema Documentation Analysis**

**File**: `backend/config/directory_schemas/phone_directory.yaml` (lines 114-119)

The schema provides **incorrect examples** that instruct the LLM to use `filters`:

```yaml
examples:
  - user_query: "What's the emergency room number?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", filters={"department_name": "Emergency Department"})'
  - user_query: "How do I schedule an appointment?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", filters={"department_name": "Appointments"})'
```

**This is where the LLM learns the incorrect pattern!**

---

## **Solution Options**

### **Option 1: Fix Schema Examples (RECOMMENDED)**

Update `phone_directory.yaml` examples to use the `query` parameter instead of `filters`:

```yaml
examples:
  - user_query: "What's the emergency room number?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", query="Emergency Department")'
  - user_query: "How do I schedule an appointment?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", query="Appointments")'
  - user_query: "Cardiology phone number?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", query="Cardiology")'
```

**Rationale**:
- The `query` parameter searches the `name` field using FTS
- This is the correct way to search for department names
- Minimal code changes required

---

### **Option 2: Store department_name in entry_data** (NOT RECOMMENDED)

Modify `phone_directory_mapper` to also store `department_name` in `entry_data`:

```python
entry_data = {}
if service_type:
    entry_data['service_type'] = service_type

# Add department_name to entry_data for filter searches
department_name = row.get('department_name', '').strip()
if department_name:
    entry_data['department_name'] = department_name  # NEW
```

**Downsides**:
- Redundant storage (already in `name` column)
- Requires re-importing all phone directory data
- More complex data model

---

## **Recommended Fix**

**File to modify**: `backend/config/directory_schemas/phone_directory.yaml`

**Lines to change**: 114-119 (examples section)

**Change FROM**:
```yaml
examples:
  - user_query: "What's the emergency room number?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", filters={"department_name": "Emergency Department"})'
  - user_query: "How do I schedule an appointment?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", filters={"department_name": "Appointments"})'
```

**Change TO**:
```yaml
examples:
  - user_query: "What's the emergency room number?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", query="Emergency Department")'
  - user_query: "How do I schedule an appointment?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", query="Appointments")'
  - user_query: "What's the cardiology phone number?"
    tool_calls:
      - 'search_directory(list_name="phone_directory", query="Cardiology")'
```

---

## **Testing After Fix**

1. **Clear LLM cache** (if applicable)
2. **Send test message**: "What's the cardiology phone number?"
3. **Expected tool call**:
   ```json
   {
     "tool_name": "search_directory",
     "args": {
       "list_name": "phone_directory",
       "query": "Cardiology"
     }
   }
   ```
4. **Expected result**: Returns Cardiology entry with phone: 718-963-2000

---

## **Additional Considerations**

### **Update search_strategy guidance section**

Also update the `search_strategy.guidance` section (lines 99-104) to clarify the correct usage:

```yaml
search_strategy:
  guidance: |
    **When users ask about contacting departments:**
    1. Search by department NAME using the `query` parameter (not filters!)
       Example: search_directory(list_name="phone_directory", query="Cardiology")
    2. Search by service_type using filters ONLY if needed
       Example: search_directory(list_name="phone_directory", filters={"service_type": "Emergency Services"})
    3. Always include hours_of_operation in response
```

---

## **Files Involved**

- ❌ **Bug source**: `backend/config/directory_schemas/phone_directory.yaml` (incorrect examples)
- ✅ **Code works correctly**: `backend/app/services/directory_service.py` (search logic)
- ✅ **Code works correctly**: `backend/app/services/directory_importer.py` (mapper logic)
- ✅ **Data imported correctly**: Database has correct structure

**Status**: Schema documentation bug (not a code bug)

