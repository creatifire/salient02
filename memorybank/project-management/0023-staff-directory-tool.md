# Epic 0023 - Staff Directory Tool
> **Last Updated**: October 20, 2025

Multi-tenant staff directory enabling agents to search professional profiles (doctors, nurses, sales reps, consultants) via natural language queries and structured filters.

**Stack**: PostgreSQL (structured) + Pinecone (semantic - deferred) + Pydantic AI tools

**Initial Use Case**: Wyckoff Hospital - 318 doctor profiles → Demo query: "Find me a Spanish-speaking cardiologist"

**Data Source**: `backend/data/wyckoff/doctors_profile.csv` (318 doctor records)

**Naming Convention**: "Staff Directory" distinguishes from Epic 0018 "Profile Builder" (customer/visitor profiles)

---

## Architecture

```mermaid
graph TB
    CSV[CSV Import] -->|Load| SL[(staff_lists)]
    SL -->|Contains| SM[(staff_members)]
    
    Agent[Pydantic AI Agent] -->|@tool| Tool[search_staff]
    Tool -->|Query| SM
    Tool -->|Check Access| Config[Agent Config YAML]
    Config -->|accessible_lists| SL
    
    Schema[staff_schemas/*.yaml] -.->|Defines Structure| SM
    
    style Agent fill:#e1f5ff
    style Tool fill:#fff4e1
    style Config fill:#e8f5e9
    style Schema fill:#fff3e0
```

---

## Multi-List Access Control

### **2-Table Design (Simplified)**

```sql
staff_lists        -- Collections per account (e.g., "doctors", "nurses")
├── id (UUID), account_id (UUID), list_name, staff_type, schema_file
│
staff_members      -- Individual staff records in lists
├── id (UUID), staff_list_id (UUID), name, languages[], contact_info{}, profile_data{}
```

**Access Control**: Config-based (not DB join table)

```yaml
# wyckoff/wyckoff_info_chat1/config.yaml
tools:
  staff_directory:
    enabled: true
    accessible_lists:
      - "doctors"
      - "nurse_practitioners"  # Optional: multiple lists
```

### **Access Rules**

- Account can have 0+ staff lists
- Account A cannot see Account B's lists (FK enforcement)
- Agent access configured in `config.yaml` (no join table for MVP)
- All queries filtered by agent's accessible lists (config → DB lookup)

---

## JSONB Schema Definitions

### **Schema Files Approach**

```
backend/config/staff_schemas/
├── doctor.yaml          # Medical doctor schema
├── nurse.yaml           # Registered nurse schema
├── sales_rep.yaml       # Sales representative schema
└── consultant.yaml      # Consultant schema
```

**Example - `doctor.yaml`:**

```yaml
staff_type: doctor
schema_version: "1.0"
description: "Medical doctor profile schema"

required_fields:
  - department
  - specialty

optional_fields:
  - board_certifications
  - education
  - residencies
  - fellowships
  - internship
  - gender
  - profile_pic

fields:
  department:
    type: string
    description: "Primary department"
    examples: ["Cardiology", "Emergency Medicine", "Surgery"]
  
  specialty:
    type: string
    description: "Medical specialty or sub-specialty"
    examples: ["Interventional Cardiology", "Plastic Surgery"]
  
  board_certifications:
    type: text
    description: "Board certifications with years (multiline)"
  
  education:
    type: string
    description: "Medical school and degree"
  
  residencies:
    type: text
    description: "Residency programs (multiline)"
  
  fellowships:
    type: text
    description: "Fellowship programs (multiline)"
  
  internship:
    type: string
    description: "Internship program"
  
  gender:
    type: string
    enum: ["male", "female", "non-binary", "prefer not to say"]
  
  profile_pic:
    type: url
    description: "URL to profile photo"
```

**Referenced in DB**:
```sql
staff_lists:
  staff_type: "doctor"
  schema_file: "doctor.yaml"  -- References config/staff_schemas/doctor.yaml
```

---

## Staff Types via JSONB

Different staff types have different `profile_data` structures:

- **Doctors**: `{department, specialty, board_certifications, education, residencies, fellowships}`
- **Nurses**: `{department, certifications, shift_type, years_experience}`
- **Sales Reps**: `{territory, quota, products, rank, years_with_company}`
- **Consultants**: `{expertise, hourly_rate, availability, certifications}`

---

## Database IDs (Wyckoff)

```
Account:
  ID: 481d3e72-c0f5-47dd-8d6e-291c5a44a5c7
  Slug: wyckoff
  Name: Wyckoff Hospital

Agent Instance:
  ID: 5dc7a769-bb5e-485b-9f19-093b95dd404d
  Slug: wyckoff_info_chat1
  Type: simple_chat
  Display: Wyckoff Hospital Assistant
```

---

## Features

- [ ] 0023-001 - Core Infrastructure (schema, data, service)
- [ ] 0023-002 - Search Tool (Pydantic AI tool + integration)
- [ ] 0023-003 - Semantic Search (Pinecone - deferred)

---

## 0023-001 - FEATURE - Core Infrastructure

### 0023-001-001 - TASK - Database Schema

- [ ] **0023-001-001-01 - CHUNK - Alembic migration**

Create 2 tables with proper indexes and foreign keys:

```sql
CREATE TABLE staff_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    list_name TEXT NOT NULL,
    list_description TEXT,
    staff_type TEXT NOT NULL,          -- "doctor", "nurse", "sales_rep", etc.
    schema_file TEXT,                   -- Optional: "doctor.yaml" (schema reference)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, list_name),
    COMMENT ON COLUMN staff_type IS 'References schema in backend/config/staff_schemas/{staff_type}.yaml'
);
CREATE INDEX idx_staff_lists_account_id ON staff_lists(account_id);
CREATE INDEX idx_staff_lists_staff_type ON staff_lists(staff_type);

CREATE TABLE staff_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_list_id UUID NOT NULL REFERENCES staff_lists(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    languages TEXT[] DEFAULT '{}',
    contact_info JSONB DEFAULT '{}',        -- {phone, location, facility}
    profile_data JSONB DEFAULT '{}',        -- Structure defined by staff_lists.schema_file
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    COMMENT ON COLUMN profile_data IS 'JSONB structure defined by schema_file in staff_lists table'
);
CREATE INDEX idx_staff_members_list_id ON staff_members(staff_list_id);
CREATE INDEX idx_staff_members_name ON staff_members(name);
CREATE INDEX idx_staff_members_status ON staff_members(status);
CREATE INDEX idx_staff_members_languages ON staff_members USING GIN(languages);
CREATE INDEX idx_staff_members_profile_data ON staff_members USING GIN(profile_data);

-- NOTE: No agent_staff_lists join table - access control via agent config files
```

**Key Design Decisions**:
- **UUID Primary Keys**: All tables use UUIDs (gen_random_uuid())
- **Account-Level Isolation**: staff_lists.account_id FK ensures multi-tenant separation
- **Schema Reference**: staff_lists.schema_file points to YAML schema definition
- **JSONB Structure**: profile_data structure varies by staff_type (defined in schema files)
- **Empty Field Handling**: Skip empty fields in JSONB (only store meaningful data)
- **Field Normalization**: Use American spelling (e.g., "specialty" not "speciality")
- **Language Array**: Clean comma-separated values gracefully ("Hindi, English" → ["Hindi", "English"])

**Tests**: 
- Table structure verification
- Constraints and cascades
- Index creation
- FK relationships

**Verify**: 
```bash
alembic upgrade head  # → tables created
alembic downgrade -1  # → rollback works
```

**STATUS**: Planned

---

- [ ] **0023-001-001-02 - CHUNK - SQLAlchemy models**

```python
# backend/app/models/staff.py
from sqlalchemy import Column, String, ARRAY, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.database import Base
import uuid
from typing import Optional

class StaffList(Base):
    __tablename__ = "staff_lists"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("accounts.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    list_name: Mapped[str] = mapped_column(String, nullable=False)
    list_description: Mapped[Optional[str]] = mapped_column(Text)
    staff_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    schema_file: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    account = relationship("Account", back_populates="staff_lists")
    staff_members = relationship("StaffMember", back_populates="staff_list", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "list_name": self.list_name,
            "list_description": self.list_description,
            "staff_type": self.staff_type,
            "schema_file": self.schema_file,
            "member_count": len(self.staff_members) if self.staff_members else 0,
        }


class StaffMember(Base):
    __tablename__ = "staff_members"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("staff_lists.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active", index=True)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    contact_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    profile_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    staff_list = relationship("StaffList", back_populates="staff_members")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "staff_list_id": str(self.staff_list_id),
            "name": self.name,
            "status": self.status,
            "languages": self.languages,
            "contact_info": self.contact_info,
            "profile_data": self.profile_data,
        }
```

**Add to existing models**:

```python
# backend/app/models/account.py
class Account(Base):
    # ... existing fields ...
    staff_lists = relationship("StaffList", back_populates="account", cascade="all, delete-orphan")

# No changes needed to AgentInstance - access control via config, not DB
```

**Tests**: 
- Model instantiation
- to_dict() serialization
- Relationship loading
- Cascade deletes

**Verify**: 
```python
# Python shell test
from app.models.staff import StaffList, StaffMember
list = StaffList(account_id=uuid4(), list_name="doctors", staff_type="doctor")
member = StaffMember(staff_list_id=list.id, name="Dr. Smith")
print(list.to_dict())
```

**STATUS**: Planned

---

### 0023-001-002 - TASK - Schema Definitions

- [ ] **0023-001-002-01 - CHUNK - Create doctor schema file**

```yaml
# backend/config/staff_schemas/doctor.yaml
staff_type: doctor
schema_version: "1.0"
description: "Medical doctor profile schema"

required_fields:
  - department
  - specialty

optional_fields:
  - board_certifications
  - education
  - residencies
  - fellowships
  - internship
  - gender
  - profile_pic

fields:
  department:
    type: string
    description: "Primary medical department"
    examples: ["Cardiology", "Emergency Medicine", "Surgery", "Medicine"]
  
  specialty:
    type: string
    description: "Medical specialty or sub-specialty"
    examples: ["Interventional Cardiology", "Plastic Surgery", "General Internal Medicine"]
  
  board_certifications:
    type: text
    description: "Board certifications with years (multiline format)"
    format: "Certification Name, Year"
    example: "Cardiology, 2015\nInternal Medicine, 2012"
  
  education:
    type: string
    description: "Medical school and degree"
    example: "Harvard Medical School, MD"
  
  residencies:
    type: text
    description: "Residency programs attended (multiline)"
    format: "Hospital, Specialty Year-Year"
  
  fellowships:
    type: text
    description: "Fellowship programs (multiline)"
    format: "Institution, Specialty Year-Year"
  
  internship:
    type: string
    description: "Internship program"
  
  gender:
    type: string
    enum: ["male", "female", "non-binary", "prefer not to say"]
  
  profile_pic:
    type: url
    description: "URL to profile photo"
    pattern: "^https?://.+"
```

**Tests**: YAML validation, schema loading
**Verify**: Load schema file, verify all fields present
**STATUS**: Planned

---

### 0023-001-003 - TASK - CSV Import

- [ ] **0023-001-003-01 - CHUNK - Generic CSV importer**

```python
# backend/app/services/staff_importer.py
import csv
from typing import List, Dict, Callable
from uuid import UUID
from pathlib import Path
from app.models.staff import StaffMember

class StaffImporter:
    """Generic CSV importer with configurable field mapping."""
    
    @staticmethod
    def parse_csv(
        csv_path: str,
        staff_list_id: UUID,
        field_mapper: Callable[[Dict], Dict]
    ) -> List[StaffMember]:
        """
        Parse CSV file → StaffMember objects.
        
        Args:
            csv_path: Path to CSV file
            staff_list_id: UUID of staff_list to associate members with
            field_mapper: Function that maps CSV row to StaffMember fields
        
        Returns:
            List of StaffMember objects (not yet saved to DB)
        """
        members = []
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    member_data = field_mapper(row)
                    member = StaffMember(
                        staff_list_id=staff_list_id,
                        **member_data
                    )
                    members.append(member)
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    # Skip invalid rows
                    continue
        
        return members
    
    @staticmethod
    def doctor_field_mapper(row: Dict) -> Dict:
        """Map Wyckoff doctor CSV columns to StaffMember fields."""
        # Parse languages (handle variations: "Hindi, English", "Punjabi,Hindi,English")
        languages_raw = row.get('language', '').strip()
        languages = [
            lang.strip() 
            for lang in languages_raw.split(',') 
            if lang.strip()
        ] if languages_raw else []
        
        # Parse status (is_active: "1" = active, "0" = inactive)
        status = 'active' if row.get('is_active') == '1' else 'inactive'
        
        # Build contact_info JSONB (skip empty fields)
        contact_info = {}
        if row.get('phone', '').strip():
            contact_info['phone'] = row['phone'].strip()
        if row.get('location', '').strip():
            contact_info['location'] = row['location'].strip()
        if row.get('facility', '').strip():
            contact_info['facility'] = row['facility'].strip()
        
        # Build profile_data JSONB (skip empty fields, normalize spelling)
        profile_data = {}
        
        # Core fields (always include if present)
        if row.get('department', '').strip():
            profile_data['department'] = row['department'].strip()
        
        # Normalize "speciality" → "specialty" (American spelling)
        specialty = row.get('speciality', '').strip()
        if specialty:
            profile_data['specialty'] = specialty
        
        # Optional fields (only include if non-empty)
        optional_fields = [
            'board_certifications',
            'education',
            'residencies',
            'fellowships',
            'internship',
            'gender',
            'profile_pic'
        ]
        
        for field in optional_fields:
            value = row.get(field, '').strip()
            if value:
                profile_data[field] = value
        
        return {
            'name': row.get('doctor_name', '').strip(),
            'status': status,
            'languages': languages,
            'contact_info': contact_info,
            'profile_data': profile_data
        }
```

**Key Design Decisions**:
- **Generic**: `parse_csv()` accepts any field mapper function
- **Language Parsing**: Handles variations ("Hindi, English", "Punjabi,Hindi,English")
- **Empty Field Handling**: Skip empty/whitespace-only fields in JSONB
- **Field Normalization**: "speciality" → "specialty" (American spelling)
- **Error Handling**: Skip invalid rows, continue processing

**Tests**: 
- Parse sample CSV
- Verify field mapping
- Language parsing variations
- Status conversion
- Empty field handling

**Verify**: 
```python
from app.services.staff_importer import StaffImporter
members = StaffImporter.parse_csv(
    "backend/data/wyckoff/doctors_profile.csv",
    staff_list_id=uuid4(),
    field_mapper=StaffImporter.doctor_field_mapper
)
print(f"Parsed {len(members)} doctors")
print(members[0].to_dict())
```

**STATUS**: Planned

---

- [ ] **0023-001-003-02 - CHUNK - Seeding script for Wyckoff doctors**

```python
# backend/scripts/seed_wyckoff_staff.py
"""
Seed Wyckoff Hospital staff directory with doctor profiles.

Usage:
    python backend/scripts/seed_wyckoff_staff.py
    python backend/scripts/seed_wyckoff_staff.py --account wyckoff --list doctors
"""
import asyncio
import argparse
from pathlib import Path
from sqlalchemy import select, delete
from app.database import get_database_service
from app.models.account import Account
from app.models.staff import StaffList, StaffMember
from app.services.staff_importer import StaffImporter


async def seed_staff(account_slug: str, list_name: str, csv_path: str):
    """Seed staff directory for account."""
    db = get_database_service()
    await db.initialize()
    
    async with db.get_session() as session:
        # Get account
        result = await session.execute(
            select(Account).where(Account.slug == account_slug)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            print(f"❌ Account not found: {account_slug}")
            return
        
        print(f"✅ Account: {account.name} ({account.slug})")
        
        # Clear existing staff list (cascades to staff_members)
        await session.execute(
            delete(StaffList).where(
                StaffList.account_id == account.id,
                StaffList.list_name == list_name
            )
        )
        await session.commit()
        print(f"🗑️  Cleared existing list: {list_name}")
        
        # Create staff list
        staff_list = StaffList(
            account_id=account.id,
            list_name=list_name,
            list_description=f"Hospital medical staff - {list_name}",
            staff_type="doctor",
            schema_file="doctor.yaml"
        )
        session.add(staff_list)
        await session.commit()
        await session.refresh(staff_list)
        print(f"📋 Created staff list: {staff_list.list_name} (ID: {staff_list.id})")
        
        # Import staff members from CSV
        csv_file = Path(csv_path)
        if not csv_file.exists():
            print(f"❌ CSV file not found: {csv_path}")
            return
        
        members = StaffImporter.parse_csv(
            csv_path=str(csv_file),
            staff_list_id=staff_list.id,
            field_mapper=StaffImporter.doctor_field_mapper
        )
        
        session.add_all(members)
        await session.commit()
        
        print(f"✅ Imported {len(members)} staff members")
        print(f"📊 Total: {len(members)} doctors in '{list_name}' list")
        
        # Sample output
        if members:
            sample = members[0]
            print(f"\n📝 Sample record:")
            print(f"   Name: {sample.name}")
            print(f"   Languages: {sample.languages}")
            print(f"   Department: {sample.profile_data.get('department', 'N/A')}")
            print(f"   Specialty: {sample.profile_data.get('specialty', 'N/A')}")


async def main():
    parser = argparse.ArgumentParser(description="Seed staff directory with CSV data")
    parser.add_argument(
        '--account',
        default='wyckoff',
        help='Account slug (default: wyckoff)'
    )
    parser.add_argument(
        '--list',
        default='doctors',
        help='List name (default: doctors)'
    )
    parser.add_argument(
        '--csv',
        default='backend/data/wyckoff/doctors_profile.csv',
        help='CSV file path (default: backend/data/wyckoff/doctors_profile.csv)'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Starting staff directory seeding...")
    print(f"   Account: {args.account}")
    print(f"   List: {args.list}")
    print(f"   CSV: {args.csv}\n")
    
    await seed_staff(args.account, args.list, args.csv)
    
    print(f"\n✅ Seeding complete!")
    print(f"💡 Next: Update agent config to enable staff_directory tool")


if __name__ == "__main__":
    asyncio.run(main())
```

**Tests**: 
- Seeding creates records
- Idempotent (run twice = same result)
- Error handling

**Verify**: 
```bash
python backend/scripts/seed_wyckoff_staff.py
# Check database
psql salient_dev -c "SELECT COUNT(*) FROM staff_members;"
```

**STATUS**: Planned

---

### 0023-001-004 - TASK - Staff Directory Service

- [ ] **0023-001-004-01 - CHUNK - StaffDirectoryService with config-based access control**

```python
# backend/app/services/staff_directory_service.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.staff import StaffList, StaffMember
import logging

logger = logging.getLogger(__name__)


class StaffDirectoryService:
    """Service for querying staff directory with multi-tenant access control."""
    
    @staticmethod
    async def get_accessible_lists(
        session: AsyncSession,
        account_id: UUID,
        list_names: List[str]
    ) -> List[UUID]:
        """
        Get staff_list_ids for given list names (account-scoped).
        
        Args:
            session: Database session
            account_id: Account UUID
            list_names: List of list names from agent config (e.g., ["doctors", "nurses"])
        
        Returns:
            List of staff_list UUIDs accessible to agent
        """
        if not list_names:
            return []
        
        result = await session.execute(
            select(StaffList.id).where(
                and_(
                    StaffList.account_id == account_id,
                    StaffList.list_name.in_(list_names)
                )
            )
        )
        return [row[0] for row in result.fetchall()]
    
    @staticmethod
    async def search_staff(
        session: AsyncSession,
        accessible_list_ids: List[UUID],
        name_query: Optional[str] = None,
        languages: Optional[List[str]] = None,
        status: str = "active",
        jsonb_filters: Optional[dict] = None,
        limit: int = 10
    ) -> List[StaffMember]:
        """
        Search staff members (only in accessible lists).
        
        Args:
            session: Database session
            accessible_list_ids: List UUIDs agent can access
            name_query: Partial name search (case-insensitive)
            languages: Filter by languages (e.g., ["Spanish", "English"])
            status: Status filter (default: "active")
            jsonb_filters: Filters for profile_data fields (e.g., {"department": "Cardiology"})
            limit: Max results to return
        
        Returns:
            List of matching StaffMember objects
        """
        if not accessible_list_ids:
            logger.warning("No accessible lists - returning empty results")
            return []
        
        # Base query
        query = select(StaffMember).where(
            and_(
                StaffMember.staff_list_id.in_(accessible_list_ids),
                StaffMember.status == status
            )
        )
        
        # Name search (partial, case-insensitive)
        if name_query:
            query = query.where(StaffMember.name.ilike(f"%{name_query}%"))
        
        # Language filter (array overlap)
        if languages:
            query = query.where(StaffMember.languages.overlap(languages))
        
        # JSONB filters (profile_data fields)
        if jsonb_filters:
            for key, value in jsonb_filters.items():
                # Case-insensitive JSONB field match
                query = query.where(
                    StaffMember.profile_data[key].astext.ilike(f"%{value}%")
                )
        
        query = query.limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
```

**Tests**: 
- Get accessible lists
- Search by name
- Search by language
- JSONB filters (department, specialty)
- Access control enforcement
- Multi-tenant isolation

**Verify**: 
```python
# Python shell test
service = StaffDirectoryService()
lists = await service.get_accessible_lists(session, account_id, ["doctors"])
staff = await service.search_staff(session, lists, languages=["Spanish"], jsonb_filters={"specialty": "Cardiology"})
```

**STATUS**: Planned

---

## 0023-002 - FEATURE - Search Tool

### 0023-002-001 - TASK - Pydantic AI Tool Implementation

- [ ] **0023-002-001-01 - CHUNK - search_staff tool**

```python
# backend/app/agents/tools/staff_directory_tools.py
from pydantic_ai import RunContext
from app.agents.models.dependencies import SessionDependencies
from app.services.staff_directory_service import StaffDirectoryService
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def search_staff(
    ctx: RunContext[SessionDependencies],
    query: Optional[str] = None,
    language: Optional[str] = None,
    department: Optional[str] = None,
    specialty: Optional[str] = None,
    limit: int = 5
) -> str:
    """
    Search staff directory for doctors, nurses, or other medical professionals.
    
    Use this tool when user asks about finding specific staff members by:
    - Name (e.g., "Find Dr. Smith")
    - Language (e.g., "Spanish-speaking doctors")
    - Department (e.g., "Cardiology department staff")
    - Specialty (e.g., "plastic surgeons")
    
    Args:
        query: Name to search for (partial match)
        language: Language requirement (e.g., "Spanish", "English")
        department: Medical department (e.g., "Cardiology", "Emergency Medicine")
        specialty: Medical specialty (e.g., "Plastic Surgery", "Internal Medicine")
        limit: Max results to return (default: 5)
    
    Returns:
        Formatted list of matching staff members with details
    """
    session = ctx.deps.db_session
    agent_config = ctx.deps.agent_config
    account_id = ctx.deps.account_id
    
    if not account_id:
        return "Error: Account context not available"
    
    # Get accessible lists from agent config
    staff_config = agent_config.get("tools", {}).get("staff_directory", {})
    accessible_lists = staff_config.get("accessible_lists", [])
    
    if not accessible_lists:
        return "Staff directory not configured for this agent"
    
    # Resolve list names to UUIDs
    service = StaffDirectoryService()
    list_ids = await service.get_accessible_lists(session, account_id, accessible_lists)
    
    if not list_ids:
        logger.warning(f"No staff lists found for account {account_id}, lists: {accessible_lists}")
        return "No staff directory available"
    
    # Build filters
    languages = [language] if language else None
    jsonb_filters = {}
    if department:
        jsonb_filters['department'] = department
    if specialty:
        jsonb_filters['specialty'] = specialty
    
    # Search staff
    logger.info(f"Searching staff: query={query}, language={language}, filters={jsonb_filters}")
    
    staff_members = await service.search_staff(
        session=session,
        accessible_list_ids=list_ids,
        name_query=query,
        languages=languages,
        jsonb_filters=jsonb_filters,
        limit=limit
    )
    
    if not staff_members:
        return "No staff members found matching your criteria"
    
    # Format results
    result_lines = [f"Found {len(staff_members)} staff member(s):\n"]
    
    for i, member in enumerate(staff_members, 1):
        lines = [f"{i}. **{member.name}**"]
        
        # Department and specialty
        dept = member.profile_data.get('department', '')
        spec = member.profile_data.get('specialty', '')
        if dept or spec:
            dept_spec = f"   {dept}" + (f" - {spec}" if spec else "")
            lines.append(dept_spec)
        
        # Languages
        if member.languages:
            lines.append(f"   Languages: {', '.join(member.languages)}")
        
        # Location
        location = member.contact_info.get('location', '')
        if location:
            lines.append(f"   Location: {location}")
        
        # Education (for doctors)
        education = member.profile_data.get('education', '')
        if education:
            lines.append(f"   Education: {education}")
        
        result_lines.append('\n'.join(lines))
    
    return '\n\n'.join(result_lines)
```

**Tests**: 
- Basic tool call
- Language filter
- JSONB filters (department, specialty)
- Agent config integration
- Access control enforcement

**Verify**: 
```python
# Mock RunContext and test tool
result = await search_staff(ctx, language="Spanish", specialty="Cardiology")
print(result)
```

**STATUS**: Planned

---

- [ ] **0023-002-001-02 - CHUNK - Register tool with wyckoff_info_chat1**

**Update agent config**:

```yaml
# backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml

# Add to existing config:
tools:
  vector_search:
    enabled: true
    # ... existing config ...
  
  staff_directory:
    enabled: true
    accessible_lists:
      - "doctors"  # Can add more: ["doctors", "nurse_practitioners", "nurses"]
    max_results: 5
    default_status: "active"
```

**Update system prompt**:

```markdown
# backend/config/agent_configs/wyckoff/wyckoff_info_chat1/system_prompt.md

## Your Tools

You have access to two search tools:

1. **vector_search**: Search hospital services, facilities, departments, and general medical information
   - Use for: "What cardiology services do you offer?", "Tell me about your ER", "Do you have a maternity ward?"
   - Searches: Website content, service descriptions, facility information

2. **search_staff**: Find specific medical professionals (doctors, nurses, specialists)
   - Use for: "Find a cardiologist", "Spanish-speaking doctors", "Dr. Smith's information"
   - Searches: Staff directory with specialties, languages, departments

**Decision Rule**: 
- Person queries (names, languages, specialties) → **search_staff**
- Service/facility queries (departments, services, locations) → **vector_search**

## Examples

User: "What cardiology services do you offer?"
→ Use **vector_search**

User: "Find me a Spanish-speaking cardiologist"
→ Use **search_staff** with language="Spanish", specialty="Cardiology"

User: "Who is Dr. Nawaiz Ahmad?"
→ Use **search_staff** with query="Nawaiz Ahmad"
```

**Register tool in agent code**:

```python
# backend/app/agents/simple_chat.py

from app.agents.tools.staff_directory_tools import search_staff

async def create_simple_chat_agent(model_name: str, instance_config: dict):
    agent = Agent(
        model=model_name,
        deps_type=SessionDependencies,
        system_prompt=instance_config.get('system_prompt', '')
    )
    
    # Register vector_search (existing)
    vector_config = instance_config.get("tools", {}).get("vector_search", {})
    if vector_config.get("enabled", False):
        from app.agents.tools import vector_tools
        agent.tool(vector_tools.vector_search)
    
    # Register staff_directory (NEW)
    staff_config = instance_config.get("tools", {}).get("staff_directory", {})
    if staff_config.get("enabled", False):
        agent.tool(search_staff)
        logger.info(f"Staff directory tool registered for {instance_config['instance_name']}")
    
    return agent
```

**Tests**: 
- Tool registered correctly
- Agent calls tool with correct params
- Response includes formatted results

**Verify**: 
```bash
# Manual test via chat
curl -X POST http://localhost:8000/accounts/wyckoff/agents/wyckoff_info_chat1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find me a Spanish-speaking cardiologist"}'
```

**STATUS**: Planned

---

### 0023-002-002 - TASK - Testing

- [ ] **0023-002-002-01 - CHUNK - Manual test script**

```python
# backend/tests/manual/test_staff_directory.py
"""
Manual test script for staff directory tool.

Usage:
    python backend/tests/manual/test_staff_directory.py
"""
import asyncio
import httpx
from rich.console import Console
from rich.panel import Panel

console = Console()

BACKEND_URL = "http://localhost:8000"
AGENT_PATH = "accounts/wyckoff/agents/wyckoff_info_chat1"

TEST_QUERIES = [
    {
        "query": "Find me a Spanish-speaking cardiologist",
        "expected_tool": "search_staff",
        "expected_keywords": ["Spanish", "Cardiology", "Cardio"]
    },
    {
        "query": "Show me doctors in Emergency Medicine",
        "expected_tool": "search_staff",
        "expected_keywords": ["Emergency Medicine"]
    },
    {
        "query": "Who is Dr. Nawaiz Ahmad?",
        "expected_tool": "search_staff",
        "expected_keywords": ["Nawaiz Ahmad"]
    },
    {
        "query": "Find a plastic surgeon",
        "expected_tool": "search_staff",
        "expected_keywords": ["Plastic Surgery", "Surgery"]
    },
    {
        "query": "What cardiology services do you offer?",
        "expected_tool": "vector_search",
        "expected_keywords": ["cardiology", "services"]
    },
]


async def test_query(client: httpx.AsyncClient, query_data: dict):
    """Test single query."""
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query_data['query']}")
    console.print(f"[dim]Expected tool: {query_data['expected_tool']}[/dim]")
    
    try:
        response = await client.post(
            f"{BACKEND_URL}/{AGENT_PATH}/chat",
            json={"message": query_data['query']},
            timeout=30.0
        )
        
        if response.status_code != 200:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            console.print(response.text)
            return
        
        result = response.json()
        answer = result.get('response', '')
        
        # Check for expected keywords
        found_keywords = [
            kw for kw in query_data.get('expected_keywords', [])
            if kw.lower() in answer.lower()
        ]
        
        if found_keywords:
            console.print(f"[green]✓ Keywords found: {', '.join(found_keywords)}[/green]")
        else:
            console.print(f"[yellow]⚠ No expected keywords found[/yellow]")
        
        console.print(Panel(answer, title="Response", border_style="green"))
        
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


async def main():
    console.print("[bold]Staff Directory Tool - Manual Test[/bold]\n")
    console.print(f"Backend: {BACKEND_URL}")
    console.print(f"Agent: {AGENT_PATH}\n")
    
    async with httpx.AsyncClient() as client:
        for i, query_data in enumerate(TEST_QUERIES, 1):
            console.print(f"[bold]Test {i}/{len(TEST_QUERIES)}[/bold]")
            await test_query(client, query_data)
            
            if i < len(TEST_QUERIES):
                console.print("\n" + "─" * 80)
    
    console.print("\n[bold green]✓ Manual testing complete![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
```

**Verify**: 
```bash
python backend/tests/manual/test_staff_directory.py
```

**STATUS**: Planned

---

- [ ] **0023-002-002-02 - CHUNK - Integration tests**

```python
# backend/tests/integration/test_staff_directory_integration.py
import pytest
from uuid import uuid4
from app.services.staff_directory_service import StaffDirectoryService
from app.models.staff import StaffList, StaffMember

@pytest.mark.asyncio
async def test_search_staff_by_language(async_session, test_account):
    """Test searching staff by language."""
    # Setup: Create staff list + members
    staff_list = StaffList(
        account_id=test_account.id,
        list_name="doctors",
        staff_type="doctor"
    )
    async_session.add(staff_list)
    await async_session.commit()
    
    # Add test doctors
    doctor1 = StaffMember(
        staff_list_id=staff_list.id,
        name="Dr. Spanish Speaker",
        languages=["Spanish", "English"],
        profile_data={"specialty": "Cardiology"}
    )
    doctor2 = StaffMember(
        staff_list_id=staff_list.id,
        name="Dr. English Only",
        languages=["English"],
        profile_data={"specialty": "Surgery"}
    )
    async_session.add_all([doctor1, doctor2])
    await async_session.commit()
    
    # Test: Search for Spanish-speaking doctors
    service = StaffDirectoryService()
    results = await service.search_staff(
        session=async_session,
        accessible_list_ids=[staff_list.id],
        languages=["Spanish"]
    )
    
    assert len(results) == 1
    assert results[0].name == "Dr. Spanish Speaker"


@pytest.mark.asyncio
async def test_multi_tenant_isolation(async_session, test_account_a, test_account_b):
    """Test that account A cannot access account B's staff."""
    # Account A staff
    list_a = StaffList(account_id=test_account_a.id, list_name="doctors", staff_type="doctor")
    async_session.add(list_a)
    await async_session.commit()
    
    member_a = StaffMember(staff_list_id=list_a.id, name="Dr. Account A")
    async_session.add(member_a)
    
    # Account B staff
    list_b = StaffList(account_id=test_account_b.id, list_name="doctors", staff_type="doctor")
    async_session.add(list_b)
    await async_session.commit()
    
    member_b = StaffMember(staff_list_id=list_b.id, name="Dr. Account B")
    async_session.add(member_b)
    await async_session.commit()
    
    # Test: Account A's accessible lists should NOT include list_b
    service = StaffDirectoryService()
    lists_a = await service.get_accessible_lists(
        session=async_session,
        account_id=test_account_a.id,
        list_names=["doctors"]
    )
    
    results = await service.search_staff(
        session=async_session,
        accessible_list_ids=lists_a
    )
    
    assert len(results) == 1
    assert results[0].name == "Dr. Account A"


@pytest.mark.asyncio
async def test_search_performance(async_session, test_account):
    """Test search performance with larger dataset."""
    import time
    
    # Create 100 staff members
    staff_list = StaffList(account_id=test_account.id, list_name="doctors", staff_type="doctor")
    async_session.add(staff_list)
    await async_session.commit()
    
    members = [
        StaffMember(
            staff_list_id=staff_list.id,
            name=f"Dr. Test {i}",
            languages=["English"],
            profile_data={"specialty": "General"}
        )
        for i in range(100)
    ]
    async_session.add_all(members)
    await async_session.commit()
    
    # Test: Search should complete < 100ms
    service = StaffDirectoryService()
    start = time.time()
    results = await service.search_staff(
        session=async_session,
        accessible_list_ids=[staff_list.id],
        limit=10
    )
    elapsed = (time.time() - start) * 1000  # ms
    
    assert len(results) == 10
    assert elapsed < 100, f"Search took {elapsed}ms (expected < 100ms)"
```

**STATUS**: Planned

---

## 0023-003 - FEATURE - Semantic Search (Pinecone)

Embedding generation + Pinecone index + hybrid search. **DEFERRED to post-demo**.

---

## Definition of Done

**Feature 0023-001** (Infrastructure):
- [x] 2 tables created with indexes and FK constraints
- [x] 318 Wyckoff doctor profiles loaded
- [x] StaffDirectoryService queries with config-based access control
- [x] Multi-tenant isolation verified
- [x] Tests passing

**Feature 0023-002** (Search Tool):
- [x] Tool registered with wyckoff_info_chat1
- [x] Agent finds doctors via natural language
- [x] Manual script demonstrates 5+ queries
- [x] Performance < 100ms

**Epic Complete**:
- [x] Demo: "Find Spanish-speaking cardiologist" works
- [x] Schema supports multiple staff types (via schema files)
- [x] All automated tests passing
- [x] Documentation complete

---

## Architecture Decisions Summary

### **Naming Convention**
- **Epic**: Staff Directory Tool (not "Profile Search" - avoids confusion with Epic 0018 "Profile Builder")
- **Tool**: `search_staff()` (not `search_profiles()`)
- **Tables**: `staff_lists`, `staff_members` (not `profile_lists`, `profiles`)
- **Service**: `StaffDirectoryService` (not `ProfileService`)

### **Access Control**
- **Config-based**: Agent config file lists `accessible_lists` (no DB join table for MVP)
- **Future Migration**: Can add `agent_staff_lists` join table for dynamic access control (enterprise feature)

### **JSONB Schema**
- **Schema Files**: Define structure in `backend/config/staff_schemas/{type}.yaml`
- **Reference**: `staff_lists.schema_file` points to schema definition
- **Flexibility**: Different staff types have different profile_data structures

### **Data Handling**
- **Empty Fields**: Skip in JSONB (only store meaningful data)
- **Field Normalization**: Use American spelling (`specialty` not `speciality`)
- **Language Parsing**: Handle variations gracefully (`"Hindi, English"` → `["Hindi", "English"]`)

### **Database Design**
- **2 Tables**: `staff_lists` + `staff_members` (no join table)
- **UUID PKs**: All tables use UUID primary keys
- **Account-Level**: `staff_lists.account_id` FK ensures multi-tenant isolation

---

## Use Cases

**Hospital - Multiple Departments**:
- Account: `wyckoff`
- Lists: `doctors`, `nurses`, `nurse_practitioners`, `physical_therapists`
- Agent: `wyckoff_info_chat1` → access `doctors` initially, can add more lists later

**Sales - Regional Teams**:
- Account: `acme_sales`
- Lists: `sales_east`, `sales_west`, `consultants`
- Agent: `east_bot` → access `["sales_east", "consultants"]`

**Multi-Tenant SaaS**:
- Accounts: `hospital_a`, `hospital_b`, `company_c`
- Enforcement: FK isolation (account-level) + config-based access (agent-level)
- No cross-account data leakage possible

---

## Design Rationale

**Why config-based access vs join table**:
- ✅ Simpler for MVP (fewer tables, no seeding complexity)
- ✅ Version controlled (git history shows access changes)
- ✅ Faster queries (no JOIN needed)
- ⏸️ Dynamic access control deferred to enterprise features

**Why schema files vs inline JSONB**:
- ✅ Reusable across accounts
- ✅ Version controlled
- ✅ Self-documenting
- ✅ Can generate forms/validation from schema

**Why account-level lists**:
- ✅ True multi-tenancy (complete data isolation)
- ✅ Privacy/compliance (HIPAA, healthcare data)
- ✅ Customization (each account can have different structures)
- ✅ Aligns with existing architecture

**Why 2 tables vs 3**:
- ✅ YAGNI principle (don't need dynamic access control yet)
- ✅ Simpler implementation
- ✅ Can add join table later when needed

