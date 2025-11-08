<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# UUID Standards
> **Last Updated**: February 1, 2025  
> **Python Version**: 3.14.0 (native UUID v7 support)

## Overview

This document defines UUID standards for the Salient project, including rationale, implementation patterns, and best practices.

## UUID Version Strategy

### Primary Keys: UUID v7 (Time-Ordered)

**All Python-generated primary keys use UUID v7** for optimal database performance and debugging.

**Models using UUID v7**:
- `Session` (`sessions.id`)
- `Profile` (`profiles.id`)
- `Message` (`messages.id`)
- `LLMRequest` (`llm_requests.id`)
- `DirectoryList` (`directory_lists.id`)
- `DirectoryEntry` (`directory_entries.id`)

**Implementation**:
```python
from uuid import UUID as UUID_Type
import uuid

class Session(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid7,  # ← UUID v7
        comment="Primary key (UUID v7 - time-ordered)"
    )
```

### PostgreSQL-Generated Keys: UUID v4

**Database-generated primary keys use PostgreSQL's `gen_random_uuid()`** (UUID v4).

**Models using UUID v4**:
- `Account` (`accounts.id`)
- `AgentInstance` (`agent_instances.id`)

**Implementation**:
```python
from sqlalchemy import func

class Account(Base):
    id: Mapped[UUID] = mapped_column(
        primary_key=True, 
        server_default=func.gen_random_uuid()  # ← PostgreSQL UUID v4
    )
```

**Rationale**: Mixed v4/v7 is acceptable. Future migration to UUID v7 can use `pg_uuidv7` extension if needed.

---

## UUID v7 Benefits

### 1. Time-Ordering
UUIDs are sortable by creation time:
```python
>>> uuid1 = uuid.uuid7()  # Created first
>>> time.sleep(0.01)
>>> uuid2 = uuid.uuid7()  # Created second
>>> uuid2 > uuid1
True  # ✅ Newer UUID is greater
```

**Use Case**: Natural ordering for messages, sessions, and requests without separate `created_at` indexes.

### 2. Database Performance
Sequential UUID inserts reduce index page splits and improve B-tree performance:
- **UUID v4 (random)**: Random inserts cause frequent page splits
- **UUID v7 (time-ordered)**: Sequential inserts optimize page usage

**Benefit**: Faster inserts, better cache locality, reduced database bloat.

### 3. Debugging
UUID v7 embeds a timestamp in the first 48 bits:
```
019a5c16-e192-75eb-bc0e-1652ed7529ca
└──────────────┘
   Timestamp (milliseconds since Unix epoch)
```

**Use Case**: Estimate record creation time directly from UUID for debugging.

### 4. Compatibility
UUID v7 is RFC 4122 compliant:
- Works with standard PostgreSQL `UUID` columns
- No schema changes needed (column type stays `UUID`)
- Compatible with UUID v4 in mixed environments

---

## Implementation Guide

### Migration from UUID v4 to UUID v7

**For Development Environments** (no production data):
1. Truncate all tables: `TRUNCATE sessions, profiles, messages, ... CASCADE;`
2. Update models: Change `uuid.uuid4` → `uuid.uuid7`
3. Restart application and verify UUID v7 generation

**For Production Environments** (with existing data):
1. Update models: Change `uuid.uuid4` → `uuid.uuid7`
2. Deploy code changes
3. **New records use UUID v7, existing records stay UUID v4** (mixed environment)
4. Optional: Migrate existing records if time-ordering needed for all data

**No database migration required** - the column type (`UUID`) doesn't change.

### Testing UUID v7

**Test time-ordering property**:
```python
import uuid
import time

def test_uuid7_ordering():
    uuid1 = uuid.uuid7()
    time.sleep(0.01)  # 10ms delay
    uuid2 = uuid.uuid7()
    
    assert uuid2 > uuid1, "UUID v7 should be time-ordered"
    assert sorted([uuid2, uuid1]) == [uuid1, uuid2], "Sorting should maintain time order"
```

**Test database compatibility**:
```python
from app.models.session import Session

def test_session_uuid7():
    session = Session(session_key="test", is_anonymous=True)
    # UUID is generated on database insert
    db.add(session)
    db.commit()
    
    assert session.id is not None
    # Verify UUID v7 version bits (version should be 7)
    version = (session.id.int >> 76) & 0xF
    assert version == 7, f"Expected UUID v7, got version {version}"
```

---

## Best Practices

### DO ✅

1. **Use UUID v7 for Python-side primary keys** - Better performance and debugging
2. **Keep `server_default=func.gen_random_uuid()` for PostgreSQL keys** - Simpler, no dependencies
3. **Test time-ordering in development** - Verify UUIDs sort correctly
4. **Update model docstrings** - Note time-ordering benefit

### DON'T ❌

1. **Don't rely on UUID timestamps for business logic** - UUIDs are IDs, not timestamps
2. **Don't assume sequential UUIDs across distributed systems** - Clock skew can occur
3. **Don't migrate UUID v4 → v7 in production without planning** - Mixed is fine
4. **Don't use `uuid.uuid1()` (MAC-based)** - Privacy and security concerns

---

## Python 3.14 Native Support

UUID v7 support was added in Python 3.14 (PEP 759):
```python
>>> import uuid
>>> uuid.uuid7()
UUID('019a5c16-e192-75eb-bc0e-1652ed7529ca')
```

**No third-party libraries needed** - `uuid.uuid7()` is built-in.

**Compatibility**: Projects on Python < 3.14 can use:
- `uuid6` library: `from uuid6 import uuid7`
- `uuid-utils` library: `from uuid_utils import uuid7`

---

## References

- **RFC 9562**: UUID Version 7 specification
- **PEP 759**: Adding `uuid.uuid7()` to Python 3.14
- **PostgreSQL pg_uuidv7**: Extension for database-side UUID v7 generation
- **datamodel.md**: Entity relationship diagram with UUID v7 notes

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-02-01 | Initial UUID v7 migration (5 Python models) | System |
| 2025-02-01 | Created uuid-standards.md documentation | System |

---

**Questions?** See the datamodel.md for schema details or consult Python 3.14 `uuid` documentation.

