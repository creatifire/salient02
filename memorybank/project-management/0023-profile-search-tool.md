# Epic 0023 - Profile Search Tool
> **Last Updated**: October 09, 2025

Generic multi-tenant profile search enabling agents to query professional profiles (doctors, nurses, sales reps, consultants) via natural language or structured filters.

**Stack**: PostgreSQL (structured) + Pinecone (semantic) + Pydantic AI tools

**Initial Use Case**: 320 hospital doctor profiles → Demo query: "Find me a Spanish-speaking cardiologist"

## Architecture

```mermaid
graph TB
    CSV[CSV Import] -->|Load| PL[(profile_lists)]
    PL -->|Contains| P[(profiles)]
    AI[Agent Instance] -->|Access Via| APL[(agent_profile_lists)]
    APL -->|Grants Access To| PL
    
    Agent[Pydantic AI Agent] -->|@tool| Tool[search_profiles]
    Tool -->|Query| P
    Tool -->|Check Access| APL
    
    style Agent fill:#e1f5ff
    style Tool fill:#fff4e1
```

## Multi-List Access Control

**3-Table Design**:

```sql
profile_lists     -- Collections per account (e.g., "doctors", "sales_east")
├── id (UUID), account_id, list_name, profile_type
│
profiles          -- Individual records in lists  
├── id (UUID), profile_list_id (UUID), name, languages[], contact_info{}, profile_data{}
│
agent_profile_lists  -- Access control join table
├── agent_instance_id, profile_list_id (UUID)
```

**Access Rules**:
- Account can have 0+ profile lists
- Account A cannot see Account B's lists (FK enforcement)
- Agent can access 1+ lists from their account (join table)
- All queries filtered by agent's accessible lists

**Profile Types via JSONB**:
- Doctors: `{department, specialty, certifications, education}`
- Sales: `{territory, quota, products, rank}`
- Consultants: `{expertise, rate, availability}`

---

## Features

- [ ] 0023-001 - Core Infrastructure (schema, data, service)
- [ ] 0023-002 - Search Tool (Pydantic AI tool + integration)
- [ ] 0023-003 - Semantic Search (Pinecone - deferred)

---

## 0023-001 - FEATURE - Core Infrastructure

### 0023-001-001 - TASK - Database Schema

- [ ] **0023-001-001-01 - CHUNK - Alembic migration**

Create 3 tables with proper indexes and foreign keys:

```sql
CREATE TABLE profile_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    list_name TEXT NOT NULL,
    list_description TEXT,
    profile_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, list_name)
);
CREATE INDEX ON profile_lists(account_id);
CREATE INDEX ON profile_lists(profile_type);

CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_list_id UUID NOT NULL REFERENCES profile_lists(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    languages TEXT[] DEFAULT '{}',
    contact_info JSONB DEFAULT '{}',
    profile_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON profiles(profile_list_id);
CREATE INDEX ON profiles(name);
CREATE INDEX ON profiles(status);
CREATE INDEX ON profiles USING GIN(languages);
CREATE INDEX ON profiles USING GIN(profile_data);

CREATE TABLE agent_profile_lists (
    agent_instance_id BIGINT NOT NULL REFERENCES agent_instances(id) ON DELETE CASCADE,
    profile_list_id UUID NOT NULL REFERENCES profile_lists(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (agent_instance_id, profile_list_id)
);
CREATE INDEX ON agent_profile_lists(agent_instance_id);
CREATE INDEX ON agent_profile_lists(profile_list_id);
```

**Tests**: Table structure, constraints, indexes, cascades
**Verify**: `alembic upgrade head` → tables exist → `alembic downgrade -1` → rollback works

**STATUS**: Planned

---

- [ ] **0023-001-001-02 - CHUNK - SQLAlchemy models**

```python
# backend/app/models/profile.py
from sqlalchemy import Column, BigInteger, String, ARRAY, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid

class ProfileList(Base):
    __tablename__ = "profile_lists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    list_name = Column(String, nullable=False)
    list_description = Column(Text)
    profile_type = Column(String, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("Account", back_populates="profile_lists")
    profiles = relationship("Profile", back_populates="profile_list", cascade="all, delete-orphan")
    agent_access = relationship("AgentProfileList", back_populates="profile_list", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "account_id": self.account_id,
            "list_name": self.list_name,
            "profile_type": self.profile_type,
            "profile_count": len(self.profiles) if self.profiles else 0,
        }

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_list_id = Column(UUID(as_uuid=True), ForeignKey("profile_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="active", index=True)
    languages = Column(ARRAY(String), default=list)
    contact_info = Column(JSONB, default=dict)
    profile_data = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile_list = relationship("ProfileList", back_populates="profiles")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "profile_list_id": str(self.profile_list_id),
            "name": self.name,
            "status": self.status,
            "languages": self.languages,
            "contact_info": self.contact_info,
            "profile_data": self.profile_data,
        }

class AgentProfileList(Base):
    __tablename__ = "agent_profile_lists"
    
    agent_instance_id = Column(BigInteger, ForeignKey("agent_instances.id", ondelete="CASCADE"), primary_key=True)
    profile_list_id = Column(UUID(as_uuid=True), ForeignKey("profile_lists.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    agent_instance = relationship("AgentInstance", back_populates="profile_list_access")
    profile_list = relationship("ProfileList", back_populates="agent_access")
```

**Add to existing models**:
- `Account.profile_lists = relationship("ProfileList", ...)`
- `AgentInstance.profile_list_access = relationship("AgentProfileList", ...)`

**Tests**: Model instantiation, to_dict(), relationships, cascade deletes
**Verify**: Python shell → create models → verify relationships load

**STATUS**: Planned

---

### 0023-001-002 - TASK - CSV Import

- [ ] **0023-001-002-01 - CHUNK - CSV parser**

```python
# backend/app/services/profile_importer.py
import csv
from typing import List
from uuid import UUID
from app.models.profile import Profile

class ProfileImporter:
    @staticmethod
    def parse_doctor_csv(csv_path: str, profile_list_id: UUID) -> List[Profile]:
        """Parse doctors_profile.csv → Profile objects."""
        profiles = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                languages = [lang.strip() for lang in row.get('language', '').split(',') if lang.strip()]
                
                profile = Profile(
                    profile_list_id=profile_list_id,
                    name=row.get('doctor_name', ''),
                    status='active' if row.get('is_active') == '1' else 'inactive',
                    languages=languages,
                    contact_info={
                        'phone': row.get('phone', ''),
                        'location': row.get('location', ''),
                        'facility': row.get('facility', '')
                    },
                    profile_data={
                        'department': row.get('department', ''),
                        'specialty': row.get('speciality', ''),
                        'board_certifications': row.get('board_certifications', ''),
                        'education': row.get('education', ''),
                        'residencies': row.get('residencies', ''),
                        'fellowships': row.get('fellowships', ''),
                        'internship': row.get('internship', ''),
                        'gender': row.get('gender', ''),
                        'profile_pic': row.get('profile_pic', ''),
                    }
                )
                profiles.append(profile)
        return profiles
```

**Tests**: Parse sample CSV, verify field mapping, language parsing, status conversion
**Verify**: Parse CSV → print first 3 profiles → check all fields populated

**STATUS**: Planned

---

- [ ] **0023-001-002-02 - CHUNK - Seeding script**

```python
# backend/scripts/seed_profiles.py
import asyncio
from sqlalchemy import select, delete
from app.database import get_async_session
from app.models.profile import ProfileList, Profile, AgentProfileList
from app.models.account import Account
from app.models.agent_instance import AgentInstance
from app.services.profile_importer import ProfileImporter

async def seed_doctor_profiles():
    async for session in get_async_session():
        # Get/create ACME account
        result = await session.execute(select(Account).where(Account.account_slug == 'acme'))
        account = result.scalar_one_or_none()
        if not account:
            account = Account(account_slug='acme', account_name='ACME Corporation')
            session.add(account)
            await session.commit()
            await session.refresh(account)
        
        # Clear existing profile lists (cascades)
        await session.execute(delete(ProfileList).where(ProfileList.account_id == account.id))
        await session.commit()
        
        # Create "doctors" list
        doctors_list = ProfileList(
            account_id=account.id,
            list_name='doctors',
            list_description='Hospital medical staff',
            profile_type='doctor'
        )
        session.add(doctors_list)
        await session.commit()
        await session.refresh(doctors_list)
        
        # Import profiles
        profiles = ProfileImporter.parse_doctor_csv("backend/data/doctors_profile.csv", doctors_list.id)
        session.add_all(profiles)
        await session.commit()
        
        # Grant access to acme/simple_chat
        result = await session.execute(
            select(AgentInstance).where(
                AgentInstance.account_id == account.id,
                AgentInstance.agent_instance_path == 'acme/simple_chat'
            )
        )
        agent = result.scalar_one_or_none()
        if agent:
            session.add(AgentProfileList(agent_instance_id=agent.id, profile_list_id=doctors_list.id))
            await session.commit()
            print(f"✅ {len(profiles)} profiles → {doctors_list.list_name} → {agent.agent_instance_path}")

if __name__ == "__main__":
    asyncio.run(seed_doctor_profiles())
```

**Tests**: Seeding creates records, idempotent (run twice), agent access granted
**Verify**: `python backend/scripts/seed_profiles.py` → check DB tables

**STATUS**: Planned

---

### 0023-001-003 - TASK - Profile Service

- [ ] **0023-001-003-01 - CHUNK - ProfileService with access control**

```python
# backend/app/services/profile_service.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.profile import Profile, AgentProfileList

class ProfileService:
    @staticmethod
    async def get_agent_accessible_lists(session: AsyncSession, agent_instance_id: int) -> List[UUID]:
        """Get profile_list_ids (UUIDs) accessible to agent."""
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
        jsonb_filters: Optional[dict] = None,
        limit: int = 10
    ) -> List[Profile]:
        """Search profiles (only in agent's accessible lists)."""
        accessible = await ProfileService.get_agent_accessible_lists(session, agent_instance_id)
        if not accessible:
            return []
        
        query = select(Profile).where(
            and_(
                Profile.profile_list_id.in_(accessible),
                Profile.status == status
            )
        )
        
        if languages:
            query = query.where(Profile.languages.overlap(languages))
        
        if jsonb_filters:
            for key, value in jsonb_filters.items():
                query = query.where(Profile.profile_data[key].astext == value)
        
        query = query.limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
```

**Tests**: Get accessible lists, search by language, JSONB filters, access control enforcement, multi-agent isolation
**Verify**: Python shell → create test queries → verify results

**STATUS**: Planned

---

## 0023-002 - FEATURE - Search Tool

### 0023-002-001 - TASK - Tool Implementation

- [ ] **0023-002-001-01 - CHUNK - search_profiles tool**

```python
# backend/app/agents/tools/profile_tools.py
from pydantic_ai import RunContext
from app.agents.models.dependencies import SessionDependencies
from app.services.profile_service import ProfileService

async def search_profiles(
    ctx: RunContext[SessionDependencies],
    query: str,
    language: str | None = None,
    department: str | None = None,
    specialty: str | None = None,
    limit: int = 5
) -> str:
    """Search profiles in agent's accessible lists."""
    session = ctx.deps.db_session
    agent_instance_id = ctx.deps.agent_instance_id
    
    if not agent_instance_id:
        return "Error: Agent not identified"
    
    jsonb_filters = {}
    if department:
        jsonb_filters['department'] = department
    if specialty:
        jsonb_filters['specialty'] = specialty
    
    languages = [language] if language else None
    
    profiles = await ProfileService.search_profiles(
        session=session,
        agent_instance_id=agent_instance_id,
        languages=languages,
        jsonb_filters=jsonb_filters,
        limit=limit
    )
    
    if not profiles:
        return "No profiles found"
    
    result = [f"Found {len(profiles)} profile(s):\n"]
    for i, p in enumerate(profiles, 1):
        lines = [f"{i}. **{p.name}**"]
        if p.profile_data.get('department'):
            lines.append(f"   Dept: {p.profile_data['department']}, Spec: {p.profile_data.get('specialty', 'N/A')}")
        if p.languages:
            lines.append(f"   Languages: {', '.join(p.languages)}")
        if p.contact_info.get('location'):
            lines.append(f"   Location: {p.contact_info['location']}")
        result.append('\n'.join(lines))
    
    return '\n\n'.join(result)
```

**Tests**: Basic call, language filter, JSONB filters, agent integration
**Verify**: Register tool → send query → check tool called with correct params

**STATUS**: Planned

---

- [ ] **0023-002-001-02 - CHUNK - Register with agents**

```python
# backend/app/agents/simple_chat.py
from app.agents.tools.profile_tools import search_profiles

def create_simple_chat_agent(model_name: str, instance_config: dict):
    agent = Agent(
        model=model_name,
        deps_type=SessionDependencies,
        system_prompt=instance_config.get('system_prompt', 'Helpful assistant')
    )
    agent.tool(search_profiles)  # Register tool
    return agent
```

**Tests**: Tool registered, agent calls tool, response includes results
**Verify**: Chat → "Find Spanish-speaking cardiologist" → agent calls tool → returns doctors

**STATUS**: Planned

---

### 0023-002-002 - TASK - Testing

- [ ] **0023-002-002-01 - CHUNK - Integration tests**

**Tests**: E2E conversation with tool calls, multi-tenant isolation, edge cases (no results), performance < 100ms

**STATUS**: Planned

---

- [ ] **0023-002-002-02 - CHUNK - Manual test script**

```python
# backend/tests/manual/test_profile_search.py
import asyncio
import httpx

async def test():
    queries = [
        "Find a Spanish-speaking cardiologist",
        "Show me surgeons",
        "Emergency Medicine doctors",
        "Orthopedic Surgery specialists",
    ]
    async with httpx.AsyncClient() as client:
        for q in queries:
            r = await client.post("http://localhost:8000/api/acme/simple_chat/chat", json={"message": q})
            print(f"\n{q}\n{r.json()['response']}\n")

asyncio.run(test())
```

**Verify**: `python backend/tests/manual/test_profile_search.py` → check results

**STATUS**: Planned

---

## 0023-003 - FEATURE - Semantic Search (Pinecone)

Embedding generation + Pinecone index + hybrid search. **DEFERRED to post-demo**.

---

## Definition of Done

**Feature 0023-001** (Infrastructure):
- [ ] 3 tables exist with indexes
- [ ] 320 doctor profiles loaded
- [ ] ProfileService queries with access control
- [ ] Multi-tenant isolation verified
- [ ] Tests passing

**Feature 0023-002** (Search Tool):
- [ ] Tool registered with agents
- [ ] Agents find profiles via natural language
- [ ] Manual script demonstrates 5+ queries
- [ ] Performance < 100ms

**Epic Complete**:
- [ ] Demo: "Find Spanish-speaking cardiologist" works
- [ ] Schema supports multiple profile types
- [ ] All automated tests passing

---

## Use Cases

**Hospital - Multiple Departments**:
- Account: `hospital_mercy`
- Lists: `doctors`, `nurses`, `therapists`
- Agent: `patient_chat` → access all | `doctor_finder` → doctors only

**Sales - Regional Teams**:
- Account: `acme_sales`
- Lists: `sales_east`, `sales_west`, `consultants`
- Agent: `east_bot` → east + consultants | `west_bot` → west + consultants

**Multi-Tenant SaaS**:
- Accounts: `hospital_a`, `hospital_b`, `company_c`
- Enforcement: FK isolation (account-level) + join table (agent-level)
- No cross-account data leakage possible

---

## Design Rationale

**Why 3 tables vs alternatives**:
- ❌ Separate tables per type → duplication, hard to query across
- ❌ EAV pattern → complex queries, poor performance
- ❌ Pure JSONB → slow on common fields
- ✅ Hybrid (core + JSONB) → fast indexed queries + flexible schema

**Why PostgreSQL first**:
- 320 records = fast SQL (< 10ms)
- Deterministic, accurate results for demo
- Pinecone adds complexity (can enhance later)
