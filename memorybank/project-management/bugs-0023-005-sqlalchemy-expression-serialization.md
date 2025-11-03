# BUG-0023-005: SQLAlchemy Expression Serialization Error

**Status**: 🔍 **INVESTIGATING**

**Priority**: HIGH (blocks cost tracking for Wyckoff agent)

**Error**: `TypeError: "Boolean value of this clause is not defined"`

**Location**: Multiple - Logfire serialization during:
- `cost_tracking_failed` logging (line 742 in `simple_chat.py`)
- Pydantic AI tool execution spans (`running tool`, `agent run`)
- Cost tracking function calls

---

## Root Cause Analysis

### Problem

SQLAlchemy column expressions (ClauseElements) cannot be evaluated in a boolean context. When Logfire tries to serialize attributes containing SQLAlchemy expressions, it triggers:

```
TypeError: Boolean value of this clause is not defined
```

### Why This Happens

1. **SQLAlchemy Documentation** (from Context7):
   - SQLAlchemy expressions raise `TypeError` when converted to boolean (e.g., `bool(expression)`, `if expression:`, or when passed to functions that check truthiness)
   - This is **by design** to prevent ambiguous SQL query generation
   - Expression objects are meant for SQL building, not Python evaluation

2. **Logfire Automatic Instrumentation**:
   - `logfire.instrument_pydantic_ai()` automatically captures span attributes
   - When attributes contain SQLAlchemy expressions, Logfire tries to serialize them
   - Serialization requires evaluating expressions, triggering the error

3. **Our Code Flow**:
   ```
   simple_chat() 
     → Load session_record from DB
     → Extract account_id, account_slug (might be lazy-loaded SQLAlchemy expressions)
     → Convert to primitives (UUID(str(...)) triggers error if value is expression)
     → Pass to track_llm_request() 
     → Logfire tries to serialize attributes
     → ERROR: Boolean value of this clause is not defined
   ```

### Where Expressions Come From

1. **Lazy-Loaded Attributes**: Accessing `session_record.account_id` outside session context can return an expression
2. **Direct Column Access**: `session_record.account_id` might be a `ColumnElement` if not fully loaded
3. **Query Results**: Values from SQLAlchemy queries might be expressions if not explicitly evaluated

### Evidence from Logfire Traces

- Error occurs in multiple spans: `cost_tracking_failed`, `running tool`, `agent run`
- Only affects Wyckoff agent (specific to its usage pattern)
- Error happens DURING serialization, not after
- Line 742 is the exception handler itself, meaning error occurs BEFORE logging

---

## Solution Approach

### Option A: Convert at Source (Recommended)

Convert SQLAlchemy expressions to Python primitives **immediately** after extracting from models, using safe detection:

1. **Detect SQLAlchemy expressions** using module path and attributes (no evaluation required)
2. **Skip conversion** if detected (return None or raise descriptive error)
3. **Convert only primitives** to target types (UUID, str)

**Implementation**:
```python
def safe_extract_uuid(value) -> Optional[UUID]:
    """Extract UUID from value, handling SQLAlchemy expressions safely."""
    if value is None:
        return None
    
    # Detect SQLAlchemy expressions BEFORE any conversion
    if _is_sqlalchemy_expression(value):
        # Should have been loaded - this indicates a bug
        raise ValueError("SQLAlchemy expression passed where primitive expected")
    
    # Safe to convert - value is not an expression
    if isinstance(value, UUID):
        return value
    return UUID(str(value))

# Use in simple_chat.py:
account_id = safe_extract_uuid(session_record.account_id)
account_slug = safe_extract_str(session_record.account_slug)
```

**Pros**:
- Catches problem at source
- Clear error messages
- Prevents passing expressions downstream

**Cons**:
- Requires changes in multiple places
- Need helper functions

### Option B: Eager Load Values

Ensure all values are eager-loaded within the session context:

```python
async with db_service.get_session() as db_session:
    session_record = await db_session.get(Session, UUID(session_id))
    
    # Eager load all needed attributes
    # Access all attributes INSIDE session to force evaluation
    account_id_val = session_record.account_id  # Forces load
    account_slug_val = session_record.account_slug  # Forces load
    
    # Convert immediately while still in session
    account_id = UUID(str(account_id_val)) if account_id_val else None
    account_slug = str(account_slug_val) if account_slug_val else None
```

**Pros**:
- Ensures values are loaded
- No special detection needed

**Cons**:
- Might not work if attributes are actually column expressions
- Doesn't handle cases where conversion itself triggers error

### Option C: Wrap Logfire Calls

Wrap all Logfire calls with serialization safety:

```python
def safe_logfire_error(event_name, **kwargs):
    """Safely log to Logfire, converting SQLAlchemy expressions."""
    safe_kwargs = {}
    for key, value in kwargs.items():
        if _is_sqlalchemy_expression(value):
            safe_kwargs[key] = None  # or "<sqlalchemy_expression>"
        else:
            safe_kwargs[key] = value
    logfire.error(event_name, **safe_kwargs)
```

**Pros**:
- Centralized safety
- Works for all Logfire calls

**Cons**:
- Doesn't fix root cause
- Might hide real issues

---

## Recommended Fix

**Implement Option A + Option B** (hybrid approach):

1. **Eager load + immediate conversion** in `simple_chat.py`:
   - Access all needed attributes INSIDE session context
   - Convert to primitives immediately (while still in session)
   - Store as local Python variables

2. **Add safety checks** in `llm_request_tracker.py`:
   - Detect SQLAlchemy expressions before conversion
   - Raise clear error if expression detected (should never happen with step 1)

3. **Update all call sites** to follow same pattern:
   - `simple_chat.py` (lines 570-610)
   - `simple_chat_stream.py` (lines 1142-1176)

---

## Files to Modify

1. `backend/app/agents/simple_chat.py`:
   - Improve eager loading and conversion (lines 570-610)
   - Add `safe_extract_uuid()` and `safe_extract_str()` helpers
   - Apply same pattern in streaming path

2. `backend/app/services/llm_request_tracker.py`:
   - Keep `_is_sqlalchemy_expression()` detection
   - Improve error messages if expression detected
   - Should never trigger if step 1 works correctly

3. **Testing**:
   - Test with Wyckoff agent specifically
   - Verify Logfire traces show no SQLAlchemy expressions
   - Confirm cost tracking works end-to-end

---

## Related Documentation

- SQLAlchemy: Boolean Evaluation Migration Guide
- Logfire: Serialization and Instrumentation
- [Critical Libraries Review - SQLAlchemy](../../analysis/critical-libraries-review.md#sqlalchemy-20)

---

## Status Updates

- 🔍 **2025-10-31**: Root cause identified - SQLAlchemy expression serialization by Logfire
- 🔍 **2025-10-31**: Reviewed SQLAlchemy and Logfire documentation via Context7
- 🔍 **2025-10-31**: Documented solution approach

