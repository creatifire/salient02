# Epic 0023 - Profile Search Tool (PostgreSQL + Pinecone + Pydantic AI)

Generic, multi-tenant profile search system enabling LLM agents to query professional profiles (doctors, nurses, sales reps, consultants, etc.) via natural language or structured filters.

**Architecture**: CSV Import → PostgreSQL (structured data) → Pinecone (semantic embeddings) → Pydantic AI Tool → Agent Response

**Integration**: 
- Pydantic AI agents (tool decorator)
- PostgreSQL (profile storage with JSONB flexibility)
- Pinecone (semantic search via embeddings)
- Multi-tenant isolation (account-level profile collections)

**Initial Use Case**: Hospital doctor profiles (320 records) from `backend/data/doctors_profile.csv`

## Architecture

```mermaid
graph TB
    CSV[CSV Data Source] -->|Import| PG[(PostgreSQL)]
    PG -->|Embed Profiles| EMB[Embedding Service]
    EMB -->|Store Vectors| PC[(Pinecone)]
    
    Agent[Pydantic AI Agent] -->|Tool Call| Tool[@search_profiles]
    Tool -->|Structured Query| PG
    Tool -->|Semantic Query| PC
    Tool -->|Merge Results| Agent
    
    PG -->|profile_type filter| Tool
    PC -->|metadata filter| Tool
    
    subgraph "Multi-Tenant Isolation"
        PG
        PC
    end
    
    style Agent fill:#e1f5ff
    style Tool fill:#fff4e1
    style PG fill:#f0f0f0
    style PC fill:#f0f0f0
```

## Design Principles

### Multi-List Architecture

**Challenge**: Support multiple profile lists per account with agent-level access control.

**Requirements**:
- ✅ Each account can have **zero or more** profile lists
- ✅ One account **cannot see** another account's profile lists
- ✅ Any agent associated with an account can access **one or more** of that account's profile lists
- ✅ Support multiple profile types (doctors, nurses, sales reps, consultants) without separate tables per type

**Solution**: Three-table architecture with access control

1. **`profile_lists`** - Collections of profiles per account
   - `id` (bigint, primary key)
   - `account_id` (bigint, foreign key to accounts)
   - `list_name` (text, e.g., "doctors", "nurses", "sales_team_east")
   - `list_description` (text)
   - `profile_type` (text, e.g., "doctor", "nurse", "sales_rep")
   - `created_at`, `updated_at`
   - **Unique constraint**: `(account_id, list_name)`

2. **`profiles`** - Individual profile records
   - `id` (UUID, primary key)
   - `profile_list_id` (bigint, foreign key to profile_lists)
   - `name` (text, indexed)
   - `status` (text: 'active', 'inactive')
   - `languages` (text[], array for multi-language support)
   - `contact_info` (JSONB: phone, email, location, facility)
   - `profile_data` (JSONB: type-specific fields)
   - `created_at`, `updated_at`

3. **`agent_profile_lists`** - Access control join table
   - `agent_instance_id` (bigint, foreign key to agent_instances)
   - `profile_list_id` (bigint, foreign key to profile_lists)
   - **Primary key**: `(agent_instance_id, profile_list_id)`

**Type-Specific Fields** (JSONB column `profile_data`):
- Doctors: `{department, specialty, board_certifications, education, residencies, fellowships, profile_pic}`
- Sales Reps: `{territory, quota, products, certifications, sales_rank}`
- Consultants: `{expertise_areas, hourly_rate, availability, certifications}`

**Benefits**:
- Multiple profile lists per account (e.g., "doctors", "nurses", "sales_east", "sales_west")
- Agent-level access control (agents only see authorized lists)
- Account isolation enforced at database level (profile_list → account)
- Fast filtering on common fields (indexed)
- Flexible schema evolution without migrations
- PostgreSQL JSONB indexing for type-specific queries

### Search Strategy

**1. Structured Queries** (PostgreSQL):
- Exact filters: `profile_type = 'doctor' AND 'Spanish' = ANY(languages)`
- JSONB queries: `profile_data->>'department' = 'Cardiology'`
- Fast, deterministic results

**2. Semantic Queries** (Pinecone):
- Natural language: "Find a Spanish-speaking heart specialist"
- Embed query → search vectors → return top-k with metadata
- Flexible, handles intent

**3. Hybrid** (Best of Both):
- Use structured filters as pre-filters (narrow search space)
- Use semantic search for final ranking
- Example: Filter to active cardiologists, then semantic rank by language/specialization match

## Features

- [ ] 0023-001 - FEATURE - Core Profile Infrastructure
- [ ] 0023-002 - FEATURE - Profile Search Tool (Pydantic AI)
- [ ] 0023-003 - FEATURE - Semantic Search Enhancement (Pinecone)

---

## 0023-001 - FEATURE - Core Profile Infrastructure

Database schema, data loading, and profile management for generic multi-tenant profiles.

### Tasks

- [ ] 0023-001-001 - TASK - Database Schema Design & Migration
- [ ] 0023-001-002 - TASK - CSV Import & Data Seeding
- [ ] 0023-001-003 - TASK - Profile Service (CRUD Operations)

---

### 0023-001-001 - TASK - Database Schema Design & Migration

Create generic `profiles` table with multi-tenant isolation and type-specific JSONB storage.

#### Chunks

- [ ] 0023-001-001-01 - CHUNK - Create Alembic migration for profile tables

**SUB-TASKS:**
- Define `profile_lists` table (collections per account)
- Define `profiles` table (individual profiles in lists)
- Define `agent_profile_lists` table (access control)
- Add indexes for fast queries and foreign key lookups
- Create migration script with upgrade/downgrade

**Schema Design:**

```sql
-- Profile Lists: Collections of profiles per account
CREATE TABLE profile_lists (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    list_name TEXT NOT NULL,
    list_description TEXT,
    profile_type TEXT NOT NULL,  -- 'doctor', 'nurse', 'sales_rep', 'consultant'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique list names per account
    CONSTRAINT uq_account_list_name UNIQUE (account_id, list_name)
);

CREATE INDEX idx_profile_lists_account_id ON profile_lists(account_id);
CREATE INDEX idx_profile_lists_type ON profile_lists(profile_type);

-- Profiles: Individual profile records in lists
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_list_id BIGINT NOT NULL REFERENCES profile_lists(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'inactive'
    languages TEXT[] DEFAULT '{}',  -- Array for multi-language support
    contact_info JSONB DEFAULT '{}',  -- {phone, email, location, facility}
    profile_data JSONB DEFAULT '{}',  -- Type-specific fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_profiles_list_id ON profiles(profile_list_id);
CREATE INDEX idx_profiles_name ON profiles(name);
CREATE INDEX idx_profiles_status ON profiles(status);
CREATE INDEX idx_profiles_languages ON profiles USING GIN(languages);
CREATE INDEX idx_profiles_data ON profiles USING GIN(profile_data);

-- Agent Profile List Access: Which lists each agent can access
CREATE TABLE agent_profile_lists (
    agent_instance_id BIGINT NOT NULL REFERENCES agent_instances(id) ON DELETE CASCADE,
    profile_list_id BIGINT NOT NULL REFERENCES profile_lists(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (agent_instance_id, profile_list_id)
);

CREATE INDEX idx_agent_profile_lists_agent ON agent_profile_lists(agent_instance_id);
CREATE INDEX idx_agent_profile_lists_list ON agent_profile_lists(profile_list_id);
```

**AUTOMATED-TESTS:**
- **Unit Tests**: `test_profile_tables_schema()` - Verify all 3 tables structure, columns, constraints
- **Integration Tests**: `test_profile_migration()` - Run migration up/down, verify no data loss
- **Integration Tests**: `test_account_isolation()` - Verify foreign key cascades work correctly

**MANUAL-TESTS:**
- Run migration: `cd backend && alembic upgrade head`
- Verify tables exist: `psql -d salient_dev -c "\d profile_lists"`, `\d profiles`, `\d agent_profile_lists`
- Check indexes: `psql -d salient_dev -c "\di profile*"`
- Test rollback: `alembic downgrade -1` then `upgrade head`

**STATUS:** Planned

---

- [ ] 0023-001-001-02 - CHUNK - Create SQLAlchemy models for profile system

**SUB-TASKS:**
- Create `ProfileList`, `Profile`, `AgentProfileList` models in `backend/app/models/profile.py`
- Add type hints for all fields
- Define relationships between models and to existing tables
- Add helper methods: `to_dict()`, access control checks

**Model Implementation:**

```python
# backend/app/models/profile.py
from sqlalchemy import Column, BigInteger, String, ARRAY, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid

class ProfileList(Base):
    """Collection of profiles belonging to an account."""
    __tablename__ = "profile_lists"
    
    id = Column(BigInteger, primary_key=True)
    account_id = Column(BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    list_name = Column(String, nullable=False)
    list_description = Column(Text)
    profile_type = Column(String, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="profile_lists")
    profiles = relationship("Profile", back_populates="profile_list", cascade="all, delete-orphan")
    agent_access = relationship("AgentProfileList", back_populates="profile_list", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """Convert profile list to dictionary."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "list_name": self.list_name,
            "list_description": self.list_description,
            "profile_type": self.profile_type,
            "profile_count": len(self.profiles) if self.profiles else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Profile(Base):
    """Individual profile record in a profile list."""
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_list_id = Column(BigInteger, ForeignKey("profile_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="active", index=True)
    languages = Column(ARRAY(String), default=list)
    contact_info = Column(JSONB, default=dict)
    profile_data = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile_list = relationship("ProfileList", back_populates="profiles")
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary for API responses."""
        return {
            "id": str(self.id),
            "profile_list_id": self.profile_list_id,
            "name": self.name,
            "status": self.status,
            "languages": self.languages,
            "contact_info": self.contact_info,
            "profile_data": self.profile_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentProfileList(Base):
    """Access control: which profile lists each agent can access."""
    __tablename__ = "agent_profile_lists"
    
    agent_instance_id = Column(BigInteger, ForeignKey("agent_instances.id", ondelete="CASCADE"), primary_key=True)
    profile_list_id = Column(BigInteger, ForeignKey("profile_lists.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    # Relationships
    agent_instance = relationship("AgentInstance", back_populates="profile_list_access")
    profile_list = relationship("ProfileList", back_populates="agent_access")
```

**Relationship Updates for Existing Models:**

```python
# backend/app/models/account.py - Add to Account model
profile_lists = relationship("ProfileList", back_populates="account", cascade="all, delete-orphan")

# backend/app/models/agent_instance.py - Add to AgentInstance model
profile_list_access = relationship("AgentProfileList", back_populates="agent_instance", cascade="all, delete-orphan")
```

**AUTOMATED-TESTS:**
- **Unit Tests**: `test_profile_models_creation()` - Test all 3 models instantiation
- **Unit Tests**: `test_profile_to_dict()` - Test dictionary conversion
- **Integration Tests**: `test_profile_relationships()` - Test relationships load correctly
- **Integration Tests**: `test_cascade_deletes()` - Verify cascade behavior (delete account → delete lists → delete profiles)
- **Integration Tests**: `test_agent_access_control()` - Verify access control join table works

**MANUAL-TESTS:**
- Import models in Python shell: `from app.models.profile import ProfileList, Profile, AgentProfileList`
- Create test profile list with profiles
- Create agent access control entries
- Verify relationships load correctly (list.profiles, profile.profile_list, etc.)

**STATUS:** Planned

---

### 0023-001-002 - TASK - CSV Import & Data Seeding

Load doctor profiles from CSV into PostgreSQL with proper type mapping.

#### Chunks

- [ ] 0023-001-002-01 - CHUNK - Doctor CSV parser and data transformer

**SUB-TASKS:**
- Create `ProfileImporter` service class
- Map CSV columns to generic profile schema
- Handle multi-line fields (certifications, residencies)
- Parse comma-separated languages
- Transform doctor-specific fields to JSONB `profile_data`
- Support profile list creation

**CSV to Profile Mapping (Doctor Type):**

```python
# backend/app/services/profile_importer.py
import csv
from typing import List
from app.models.profile import ProfileList, Profile

class ProfileImporter:
    """Import profiles from CSV files into generic profile schema."""
    
    @staticmethod
    def parse_doctor_csv(csv_path: str, profile_list_id: int) -> List[Profile]:
        """
        Parse doctors_profile.csv into Profile objects.
        
        Args:
            csv_path: Path to CSV file
            profile_list_id: ID of ProfileList to associate profiles with
            
        Returns:
            List of Profile objects (not yet added to session)
        """
        profiles = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Core fields
                languages = [
                    lang.strip() 
                    for lang in row.get('language', '').split(',') 
                    if lang.strip()
                ]
                
                # Contact info (JSONB)
                contact_info = {
                    'phone': row.get('phone', ''),
                    'location': row.get('location', ''),
                    'facility': row.get('facility', '')
                }
                
                # Doctor-specific fields (JSONB)
                profile_data = {
                    'department': row.get('department', ''),
                    'specialty': row.get('speciality', ''),  # Note: typo in CSV
                    'board_certifications': row.get('board_certifications', ''),
                    'education': row.get('education', ''),
                    'residencies': row.get('residencies', ''),
                    'fellowships': row.get('fellowships', ''),
                    'internship': row.get('internship', ''),
                    'gender': row.get('gender', ''),
                    'insurance': row.get('insurance', ''),
                    'profile_pic': row.get('profile_pic', ''),
                    'badge': row.get('badge', '')
                }
                
                profile = Profile(
                    profile_list_id=profile_list_id,
                    name=row.get('doctor_name', ''),
                    status='active' if row.get('is_active') == '1' else 'inactive',
                    languages=languages,
                    contact_info=contact_info,
                    profile_data=profile_data
                )
                
                profiles.append(profile)
        
        return profiles
```

**AUTOMATED-TESTS:**
- **Unit Tests**: `test_parse_doctor_csv()` - Parse sample CSV, verify field mapping
- **Unit Tests**: `test_language_parsing()` - Test comma-separated language parsing
- **Unit Tests**: `test_status_mapping()` - Test is_active to status conversion

**MANUAL-TESTS:**
- Run parser on `backend/data/doctors_profile.csv`
- Print first 3 profiles, verify all fields populated
- Check JSONB fields contain correct doctor-specific data

**STATUS:** Planned

---

- [ ] 0023-001-002-02 - CHUNK - Database seeding script with profile list creation and agent access

**SUB-TASKS:**
- Create seeding script: `backend/scripts/seed_profiles.py`
- Use ACME account or create if missing
- Create "doctors" profile list
- Bulk insert profiles into the list
- Grant access to `acme/simple_chat` agent instance
- Add error handling and progress logging
- Make script idempotent (clear existing profile lists first)

**Seeding Script:**

```python
# backend/scripts/seed_profiles.py
import asyncio
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models.profile import ProfileList, Profile, AgentProfileList
from app.models.account import Account
from app.models.agent_instance import AgentInstance
from app.services.profile_importer import ProfileImporter

async def seed_doctor_profiles():
    """Seed doctor profiles from CSV into ACME account with agent access."""
    async for session in get_async_session():
        # Get or create ACME account
        result = await session.execute(
            select(Account).where(Account.account_slug == 'acme')
        )
        account = result.scalar_one_or_none()
        
        if not account:
            print("Creating ACME account...")
            account = Account(account_slug='acme', account_name='ACME Corporation')
            session.add(account)
            await session.commit()
            await session.refresh(account)
        
        print(f"Using account: {account.account_slug} (ID: {account.id})")
        
        # Clear existing profile lists for this account (cascades to profiles and access)
        await session.execute(
            delete(ProfileList).where(ProfileList.account_id == account.id)
        )
        await session.commit()
        
        # Create "doctors" profile list
        doctors_list = ProfileList(
            account_id=account.id,
            list_name='doctors',
            list_description='Hospital medical staff directory',
            profile_type='doctor'
        )
        session.add(doctors_list)
        await session.commit()
        await session.refresh(doctors_list)
        
        print(f"Created profile list: '{doctors_list.list_name}' (ID: {doctors_list.id})")
        
        # Import profiles from CSV
        csv_path = "backend/data/doctors_profile.csv"
        profiles = ProfileImporter.parse_doctor_csv(csv_path, doctors_list.id)
        
        print(f"Importing {len(profiles)} doctor profiles...")
        session.add_all(profiles)
        await session.commit()
        
        print(f"✅ Imported {len(profiles)} profiles into list '{doctors_list.list_name}'")
        
        # Grant access to acme/simple_chat agent
        result = await session.execute(
            select(AgentInstance).where(
                AgentInstance.account_id == account.id,
                AgentInstance.agent_instance_path == 'acme/simple_chat'
            )
        )
        agent_instance = result.scalar_one_or_none()
        
        if agent_instance:
            agent_access = AgentProfileList(
                agent_instance_id=agent_instance.id,
                profile_list_id=doctors_list.id
            )
            session.add(agent_access)
            await session.commit()
            print(f"✅ Granted access to agent '{agent_instance.agent_instance_path}'")
        else:
            print(f"⚠️  Agent 'acme/simple_chat' not found - access not granted")
            print(f"   Run after agent instances are created, or manually grant access later")

if __name__ == "__main__":
    asyncio.run(seed_doctor_profiles())
```

**AUTOMATED-TESTS:**
- **Integration Tests**: `test_seed_profiles()` - Run seeding, verify count in database
- **Integration Tests**: `test_seeding_idempotent()` - Run twice, verify no duplicates
- **Integration Tests**: `test_agent_access_granted()` - Verify agent_profile_lists entry created

**MANUAL-TESTS:**
- Run: `cd backend && python scripts/seed_profiles.py`
- Verify list: `psql -d salient_dev -c "SELECT * FROM profile_lists;"`
- Verify count: `psql -d salient_dev -c "SELECT COUNT(*) FROM profiles;"`
- Check sample: `psql -d salient_dev -c "SELECT name, status, languages FROM profiles LIMIT 5;"`
- Query JSONB: `psql -d salient_dev -c "SELECT name, profile_data->>'department' as dept FROM profiles LIMIT 5;"`
- Check access: `psql -d salient_dev -c "SELECT agent_instance_id, profile_list_id FROM agent_profile_lists;"`

**STATUS:** Planned

---

### 0023-001-003 - TASK - Profile Service (CRUD Operations)

Service layer for profile queries and management.

#### Chunks

- [ ] 0023-001-003-01 - CHUNK - ProfileService with agent access control

**SUB-TASKS:**
- Create `ProfileService` in `backend/app/services/profile_service.py`
- Implement search with agent-level access control (only search lists agent has access to)
- Add structured search methods (by type, languages, JSONB fields)
- Add pagination support
- Query builder for flexible filtering with access control

**Service Implementation:**

```python
# backend/app/services/profile_service.py
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.profile import Profile, ProfileList, AgentProfileList

class ProfileService:
    """Service for querying and managing profiles with agent access control."""
    
    @staticmethod
    async def get_agent_accessible_lists(
        session: AsyncSession,
        agent_instance_id: int
    ) -> List[int]:
        """
        Get list of profile_list_ids that this agent instance can access.
        
        Args:
            session: Database session
            agent_instance_id: ID of agent instance
            
        Returns:
            List of profile_list_ids accessible to this agent
        """
        result = await session.execute(
            select(AgentProfileList.profile_list_id).where(
                AgentProfileList.agent_instance_id == agent_instance_id
            )
        )
        return [row[0] for row in result.fetchall()]
    
    @staticmethod
    async def search_profiles(
        session: AsyncSession,
        agent_instance_id: int,
        languages: Optional[List[str]] = None,
        status: str = "active",
        jsonb_filters: Optional[dict] = None,  # e.g., {"department": "Cardiology"}
        limit: int = 10
    ) -> List[Profile]:
        """
        Search profiles accessible to the agent with structured filters.
        
        Only searches profiles in lists that the agent has access to.
        """
        # Get accessible list IDs for this agent
        accessible_lists = await ProfileService.get_agent_accessible_lists(
            session, agent_instance_id
        )
        
        if not accessible_lists:
            # Agent has no access to any profile lists
            return []
        
        # Build query with access control
        query = select(Profile).where(
            and_(
                Profile.profile_list_id.in_(accessible_lists),
                Profile.status == status
            )
        )
        
        if languages:
            # Match any language in the list
            query = query.where(Profile.languages.overlap(languages))
        
        if jsonb_filters:
            for key, value in jsonb_filters.items():
                query = query.where(
                    Profile.profile_data[key].astext == value
                )
        
        query = query.limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_profile_by_id(
        session: AsyncSession,
        profile_id: str,
        agent_instance_id: int
    ) -> Optional[Profile]:
        """
        Get single profile by ID (with agent access control).
        
        Returns profile only if agent has access to its list.
        """
        # Get accessible lists
        accessible_lists = await ProfileService.get_agent_accessible_lists(
            session, agent_instance_id
        )
        
        if not accessible_lists:
            return None
        
        result = await session.execute(
            select(Profile).where(
                and_(
                    Profile.id == profile_id,
                    Profile.profile_list_id.in_(accessible_lists)
                )
            )
        )
        return result.scalar_one_or_none()
```

**AUTOMATED-TESTS:**
- **Unit Tests**: `test_profile_service_get_accessible_lists()` - Get agent's accessible lists
- **Unit Tests**: `test_profile_service_search_by_languages()` - Filter by languages array
- **Unit Tests**: `test_profile_service_jsonb_filters()` - Filter by JSONB fields
- **Integration Tests**: `test_profile_service_agent_access_control()` - Verify agent can only see authorized lists
- **Integration Tests**: `test_profile_service_multi_agent_isolation()` - Verify different agents see different lists

**MANUAL-TESTS:**
- Test in Python shell with sample queries
- Create two agents with access to different lists, verify isolation
- Verify language filtering returns correct doctors
- Test JSONB queries (e.g., department, specialty)

**STATUS:** Planned

---

## 0023-002 - FEATURE - Profile Search Tool (Pydantic AI)

Pydantic AI tool that agents can call to search profiles using structured queries.

### Tasks

- [ ] 0023-002-001 - TASK - Pydantic AI Tool Implementation
- [ ] 0023-002-002 - TASK - Tool Integration & Testing

---

### 0023-002-001 - TASK - Pydantic AI Tool Implementation

Create `@agent.tool` decorated function for profile search.

#### Chunks

- [ ] 0023-002-001-01 - CHUNK - search_profiles tool with dependency injection

**SUB-TASKS:**
- Create tool in `backend/app/agents/tools/profile_tools.py`
- Use `RunContext[SessionDependencies]` for database access
- Parse natural language query hints (department, specialty, language)
- Return formatted results for LLM consumption

**Tool Implementation:**

```python
# backend/app/agents/tools/profile_tools.py
from pydantic_ai import RunContext
from app.agents.models.dependencies import SessionDependencies
from app.services.profile_service import ProfileService
from typing import List

async def search_profiles(
    ctx: RunContext[SessionDependencies],
    query: str,
    language: str | None = None,
    department: str | None = None,
    specialty: str | None = None,
    limit: int = 5
) -> str:
    """
    Search for professional profiles (doctors, nurses, sales reps, etc.).
    
    This tool searches profile lists that the current agent has access to.
    Access control is handled automatically based on agent_instance_id.
    
    Args:
        query: Natural language description of search (for context)
        language: Preferred language (e.g., "Spanish", "English")
        department: Department filter (e.g., "Cardiology", "Surgery")
        specialty: Specialty filter (e.g., "Orthopedic Surgery")
        limit: Maximum number of results (default 5)
    
    Returns:
        Formatted list of matching profiles with key details
    """
    session = ctx.deps.db_session
    agent_instance_id = ctx.deps.agent_instance_id
    
    if not agent_instance_id:
        return "Error: Agent instance not identified. Cannot search profiles."
    
    # Build JSONB filters for doctor-specific fields
    jsonb_filters = {}
    if department:
        jsonb_filters['department'] = department
    if specialty:
        jsonb_filters['specialty'] = specialty
    
    # Build language filter
    languages = [language] if language else None
    
    # Search profiles (access control enforced in service)
    profiles = await ProfileService.search_profiles(
        session=session,
        agent_instance_id=agent_instance_id,
        languages=languages,
        jsonb_filters=jsonb_filters,
        limit=limit
    )
    
    # Format results for LLM
    if not profiles:
        return "No profiles found matching your criteria in your accessible lists."
    
    result_lines = [f"Found {len(profiles)} matching profile(s):\n"]
    
    for i, profile in enumerate(profiles, 1):
        lines = [f"{i}. **{profile.name}**"]
        
        # Add doctor-specific details if available
        if profile.profile_data.get('department'):
            dept = profile.profile_data.get('department', 'N/A')
            spec = profile.profile_data.get('specialty', 'N/A')
            lines.append(f"   - Department: {dept}")
            lines.append(f"   - Specialty: {spec}")
        
        # Add common details
        if profile.languages:
            lines.append(f"   - Languages: {', '.join(profile.languages)}")
        
        contact = profile.contact_info
        if contact.get('location'):
            lines.append(f"   - Location: {contact['location']}")
        if contact.get('phone'):
            lines.append(f"   - Phone: {contact['phone']}")
        
        result_lines.append('\n'.join(lines))
    
    return '\n\n'.join(result_lines)
```

**AUTOMATED-TESTS:**
- **Unit Tests**: `test_search_profiles_tool_basic()` - Test with minimal parameters
- **Unit Tests**: `test_search_profiles_tool_language_filter()` - Test language filtering
- **Unit Tests**: `test_search_profiles_tool_jsonb_filters()` - Test department/specialty filters
- **Integration Tests**: `test_search_profiles_tool_with_agent()` - Test tool call from agent

**MANUAL-TESTS:**
- Register tool with test agent
- Send query: "Find a Spanish-speaking cardiologist"
- Verify tool is called with correct parameters
- Check formatted response contains relevant doctors

**STATUS:** Planned

---

- [ ] 0023-002-001-02 - CHUNK - Register tool with existing agents

**SUB-TASKS:**
- Add `search_profiles` to Simple Chat agent tools
- Add to Sales Agent tools (for customer service reps, etc.)
- Update agent configurations in YAML if needed
- Test tool availability in agent responses

**Agent Registration:**

```python
# backend/app/agents/simple_chat.py (example)
from app.agents.tools.profile_tools import search_profiles

def create_simple_chat_agent(model_name: str, instance_config: dict):
    """Create simple chat agent with profile search tool."""
    agent = Agent(
        model=model_name,
        deps_type=SessionDependencies,
        system_prompt=instance_config.get('system_prompt', 'You are a helpful assistant.')
    )
    
    # Register profile search tool
    agent.tool(search_profiles)
    
    return agent
```

**AUTOMATED-TESTS:**
- **Integration Tests**: `test_agent_has_profile_tool()` - Verify tool is registered
- **Integration Tests**: `test_agent_calls_profile_tool()` - Test end-to-end tool invocation

**MANUAL-TESTS:**
- Start agent conversation
- Ask: "Can you find me a Spanish-speaking heart doctor?"
- Verify agent calls `search_profiles` tool
- Check response includes doctor names and details

**STATUS:** Planned

---

### 0023-002-002 - TASK - Tool Integration & Testing

End-to-end testing with real agent conversations.

#### Chunks

- [ ] 0023-002-002-01 - CHUNK - Integration tests with mock and real data

**SUB-TASKS:**
- Write tests for various query patterns
- Test multi-tenant isolation (different accounts)
- Test edge cases (no results, invalid filters)
- Performance testing (query latency)

**AUTOMATED-TESTS:**
- **Integration Tests**: `test_profile_search_e2e()` - Full conversation with tool calls
- **Integration Tests**: `test_profile_search_multi_tenant()` - Verify account isolation
- **Performance Tests**: `test_profile_search_latency()` - Query performance < 100ms

**MANUAL-TESTS:**
- Test various natural language queries
- Verify results are accurate and well-formatted
- Test with different profile types (if data available)

**STATUS:** Planned

---

- [ ] 0023-002-002-02 - CHUNK - Manual test script for profile search

**SUB-TASKS:**
- Create `backend/tests/manual/test_profile_search.py`
- Test script similar to `test_chat_endpoint.py`
- Various query scenarios with expected results
- Documentation for running manual tests

**Manual Test Script:**

```python
# backend/tests/manual/test_profile_search.py
"""Manual test script for profile search tool."""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_profile_search():
    """Test profile search via chat endpoint."""
    
    queries = [
        "Find me a Spanish-speaking cardiologist",
        "I need a surgeon who speaks English",
        "Show me doctors in the Emergency Medicine department",
        "Find a doctor who specializes in Orthopedic Surgery",
        "List gastroenterology doctors"
    ]
    
    async with httpx.AsyncClient() as client:
        for query in queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print('='*60)
            
            response = await client.post(
                f"{BASE_URL}/api/acme/simple_chat/chat",
                json={"message": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data['response']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
            
            await asyncio.sleep(1)  # Rate limiting

if __name__ == "__main__":
    print("Testing Profile Search Tool")
    print("Ensure backend is running: cd backend && uvicorn app.main:app --reload")
    print()
    asyncio.run(test_profile_search())
```

**MANUAL-TESTS:**
- Run: `cd backend && python tests/manual/test_profile_search.py`
- Verify each query returns relevant doctors
- Check response formatting is clear and useful
- Test error handling (invalid profile type, etc.)

**STATUS:** Planned

---

## 0023-003 - FEATURE - Semantic Search Enhancement (Pinecone)

Add semantic search capability for natural language profile queries.

**Note**: This feature can be implemented after Phase 1 demo if time permits. PostgreSQL structured search (Feature 0023-002) is sufficient for initial demo.

### Tasks

- [ ] 0023-003-001 - TASK - Profile Embedding Generation
- [ ] 0023-003-002 - TASK - Pinecone Index Setup & Ingestion
- [ ] 0023-003-003 - TASK - Hybrid Search Implementation

---

### 0023-003-001 - TASK - Profile Embedding Generation

Generate vector embeddings for profile text (name + department + specialty + languages).

#### Chunks

- [ ] 0023-003-001-01 - CHUNK - Embedding service for profiles

**SUB-TASKS:**
- Use existing `EmbeddingService` from codebase
- Create profile text representation for embedding
- Batch embed all profiles
- Store embedding vectors

**STATUS:** Planned - Deferred to post-demo enhancement

---

### 0023-003-002 - TASK - Pinecone Index Setup & Ingestion

Create Pinecone index and upload profile embeddings with metadata.

**STATUS:** Planned - Deferred to post-demo enhancement

---

### 0023-003-003 - TASK - Hybrid Search Implementation

Combine PostgreSQL filters with Pinecone semantic ranking.

**STATUS:** Planned - Deferred to post-demo enhancement

---

## Definition of Done

**Feature 0023-001 (Core Infrastructure) Complete When:**
- [ ] `profiles` table exists with proper schema and indexes
- [ ] Doctor profiles loaded from CSV (320+ records)
- [ ] `ProfileService` can query by type, language, and JSONB fields
- [ ] Multi-tenant isolation verified (account-level separation)
- [ ] All integration tests passing

**Feature 0023-002 (Search Tool) Complete When:**
- [ ] `search_profiles` tool registered with Pydantic AI agents
- [ ] Agents can find profiles via natural language queries
- [ ] Tool returns formatted, useful results
- [ ] Manual test script demonstrates 5+ query scenarios
- [ ] Performance acceptable (< 100ms per search)

**Feature 0023-003 (Semantic Search) Complete When:**
- [ ] Profile embeddings generated and stored in Pinecone
- [ ] Semantic search returns relevant results for natural language queries
- [ ] Hybrid search combines structured + semantic ranking
- [ ] Performance acceptable (< 200ms including embedding + search)

**Epic 0023 Complete When:**
- [ ] Demo-ready: Agent can answer "Find me a Spanish-speaking cardiologist" accurately
- [ ] Schema is generic enough to support other profile types (nurses, sales reps, consultants)
- [ ] Documentation updated with design decisions and trade-offs
- [ ] All automated tests passing
- [ ] Manual verification complete

---

## Design Trade-offs & Decisions

### Why Hybrid Schema (Core + JSONB)?

**Alternatives Considered:**
1. **Separate tables per type** (doctors, nurses, sales_reps)
   - ❌ Schema duplication, harder to query across types
   - ❌ Requires migrations for new types
   
2. **EAV (Entity-Attribute-Value) pattern**
   - ❌ Complex queries, poor performance
   - ❌ Harder to maintain referential integrity

3. **Pure JSONB (everything in JSON)**
   - ❌ Slower queries on common fields
   - ❌ Harder to enforce constraints

4. **Hybrid (Core + JSONB)** ✅ CHOSEN
   - ✅ Fast queries on common fields (indexed)
   - ✅ Flexible for type-specific data
   - ✅ Single table for all types
   - ✅ PostgreSQL JSONB indexing for nested queries

### Why PostgreSQL First, Pinecone Second?

**Rationale:**
- PostgreSQL provides deterministic, accurate results for structured queries
- 320 records is small enough for SQL queries to be fast (< 10ms)
- Pinecone adds complexity (embedding generation, index management, latency)
- Demo needs accuracy over semantic "fuzziness"
- Can add semantic search later for scale/UX enhancement

### Multi-Tenant Strategy

**Decision:** Account-level isolation via `account_id` foreign key
- Each account has separate profile collections
- Queries always filter by `account_id`
- Future: Could add Pinecone namespaces per account for semantic search isolation

---

## Use Case Scenarios

### Example 1: Hospital with Multiple Departments

**Account**: `hospital_mercy`

**Profile Lists**:
- `doctors` (320 profiles)
- `nurses` (150 profiles)
- `therapists` (45 profiles)

**Agents & Access**:
- `hospital_mercy/patient_chat` → Access to: `doctors`, `nurses`, `therapists` (all lists)
- `hospital_mercy/doctor_finder` → Access to: `doctors` (only)
- `hospital_mercy/nursing_scheduler` → Access to: `nurses` (only)

**Queries**:
- Patient: "Find me a Spanish-speaking cardiologist" → `patient_chat` searches `doctors` list
- Admin: "Show me available nurses for night shift" → `nursing_scheduler` searches `nurses` list

### Example 2: Sales Organization with Regional Teams

**Account**: `acme_sales`

**Profile Lists**:
- `sales_east` (25 profiles)
- `sales_west` (30 profiles)
- `sales_central` (20 profiles)
- `consultants` (10 profiles)

**Agents & Access**:
- `acme_sales/east_bot` → Access to: `sales_east`, `consultants`
- `acme_sales/west_bot` → Access to: `sales_west`, `consultants`
- `acme_sales/admin_bot` → Access to: all lists

**Queries**:
- East customer: "Who's my account rep?" → `east_bot` searches `sales_east` only
- Admin: "Find a consultant with cloud expertise" → `admin_bot` searches `consultants`

### Example 3: Multi-Tenant SaaS

**Accounts**: `hospital_a`, `hospital_b`, `company_c`

**Isolation**:
- `hospital_a/chat` → Can only access `hospital_a` profile lists (never sees `hospital_b` data)
- `hospital_b/finder` → Can only access `hospital_b` profile lists
- `company_c/sales_bot` → Can only access `company_c` profile lists

**Enforcement**:
- Database foreign keys enforce account-level isolation (`profile_lists.account_id`)
- Agent access control enforces list-level isolation (`agent_profile_lists` join table)
- No cross-account data leakage possible

---

## Future Enhancements

- [ ] Profile image storage (S3/CloudFlare R2)
- [ ] Profile versioning/history
- [ ] Bulk profile updates (CSV upload endpoint)
- [ ] Profile analytics (search patterns, popular profiles)
- [ ] Advanced filtering (availability schedules, ratings, reviews)
- [ ] Recommendation engine (suggest similar profiles)
- [ ] Profile list cloning (duplicate lists across accounts)
- [ ] Bulk agent access management (grant/revoke access to multiple agents)
- [ ] Profile list API endpoints (CRUD operations)


