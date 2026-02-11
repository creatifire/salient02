# Shared App with Dedicated Database Per Tenant

Architecture for running a single backend application instance with each customer getting their own PostgreSQL database on a shared PostgreSQL server.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend (Single Instance)                          │
│  - Tenant routing middleware                                │
│  - Dynamic engine management                                │
│  - Shared application code                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Route by tenant_id/account_slug
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Engine Pool Manager                                        │
│  - tenant_id → engine mapping                               │
│  - Dynamic engine creation                                  │
│  - Connection pool per tenant database                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─→ Engine 1 → Database: customer_a
                  ├─→ Engine 2 → Database: customer_b
                  └─→ Engine 3 → Database: customer_c
                  
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL Instance (Shared)                               │
│  ├── Database: customer_a (tenant A)                        │
│  │   ├── accounts, users, agent_instances                   │
│  │   ├── sessions, messages, llm_requests                   │
│  │   └── directory_lists, directory_entries                 │
│  ├── Database: customer_b (tenant B)                        │
│  │   └── [same schema structure]                            │
│  ├── Database: customer_c (tenant C)                        │
│  │   └── [same schema structure]                            │
│  └── Database: salient_admin (control plane)                │
│      ├── tenant_registry (tenant → database mapping)        │
│      └── tenant_config (connection strings, settings)       │
└─────────────────────────────────────────────────────────────┘
```

## Benefits vs Current Approach

**Current**: Shared database with `account_id` filtering

**Proposed**: Dedicated database per tenant

| Aspect | Current (Shared DB) | Proposed (Dedicated DB) |
|--------|---------------------|-------------------------|
| **Data Isolation** | ⚠️ Logical (filtering) | ✅ Physical (separate DB) |
| **Security** | ⚠️ Risk of cross-tenant leaks | ✅ Complete isolation |
| **Performance** | ⚠️ Noisy neighbor issues | ✅ Isolated performance |
| **Compliance** | ⚠️ Data commingling concerns | ✅ Regulatory compliance easier |
| **Backup/Restore** | ⚠️ All-or-nothing | ✅ Per-tenant granularity |
| **Schema Customization** | ❌ Not possible | ✅ Per-tenant customization |
| **Query Complexity** | ✅ Simple | ✅ Simple (no filtering) |
| **Connection Pooling** | ✅ Single pool | ⚠️ Pool per tenant |
| **Migration Complexity** | ✅ Single migration | ⚠️ Multi-tenant migrations |
| **Operational Complexity** | ✅ Low | ⚠️ Higher |

## SQLAlchemy 2.0 Implementation

### 1. Tenant Registry (Control Plane)

Store tenant → database mapping in admin database:

```python
# backend/app/models/tenant_registry.py
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from . import Base

class TenantRegistry(Base):
    """Control plane: Maps tenants to their dedicated databases."""
    __tablename__ = "tenant_registry"
    
    tenant_id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    database_name: Mapped[str] = mapped_column(String, nullable=False)
    connection_string: Mapped[str] = mapped_column(String, nullable=False)  # Encrypted
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=True)  # Pool settings, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

### 2. Engine Pool Manager

Dynamic engine creation and caching:

```python
# backend/app/database_multi_tenant.py
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker
import logfire

class TenantEngineManager:
    """Manages dynamic engine creation per tenant database."""
    
    def __init__(self):
        self._engines: Dict[str, AsyncEngine] = {}
        self._session_factories: Dict[str, async_sessionmaker[AsyncSession]] = {}
        self._admin_engine: AsyncEngine | None = None
    
    async def initialize_admin_engine(self, admin_db_url: str):
        """Initialize the admin/control plane database engine."""
        self._admin_engine = create_async_engine(
            admin_db_url,
            pool_size=10,
            max_overflow=5,
            pool_pre_ping=True
        )
        logfire.info('tenant_engine_manager.admin_initialized')
    
    async def get_engine(self, tenant_id: str) -> AsyncEngine:
        """Get or create engine for tenant database."""
        if tenant_id in self._engines:
            return self._engines[tenant_id]
        
        # Load tenant config from admin database
        tenant_config = await self._load_tenant_config(tenant_id)
        
        if not tenant_config:
            raise ValueError(f"Tenant not found: {tenant_id}")
        
        # Create new engine for tenant database
        engine = create_async_engine(
            tenant_config['connection_string'],
            pool_size=tenant_config.get('pool_size', 10),
            max_overflow=tenant_config.get('max_overflow', 5),
            pool_timeout=30,
            pool_pre_ping=True,
            echo=False
        )
        
        # Cache engine
        self._engines[tenant_id] = engine
        
        # Create session factory for this tenant
        self._session_factories[tenant_id] = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logfire.info(
            'tenant_engine_manager.engine_created',
            tenant_id=tenant_id,
            database=tenant_config['database_name']
        )
        
        return engine
    
    async def _load_tenant_config(self, tenant_id: str) -> dict | None:
        """Load tenant configuration from admin database."""
        from .models.tenant_registry import TenantRegistry
        
        async with self._admin_session() as session:
            result = await session.execute(
                select(TenantRegistry).where(
                    TenantRegistry.tenant_id == tenant_id,
                    TenantRegistry.is_active == True
                )
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                return None
            
            return {
                'tenant_id': tenant.tenant_id,
                'tenant_slug': tenant.tenant_slug,
                'database_name': tenant.database_name,
                'connection_string': tenant.connection_string,
                'pool_size': tenant.config.get('pool_size', 10) if tenant.config else 10,
                'max_overflow': tenant.config.get('max_overflow', 5) if tenant.config else 5
            }
    
    @asynccontextmanager
    async def _admin_session(self):
        """Get session for admin database."""
        if not self._admin_engine:
            raise RuntimeError("Admin engine not initialized")
        
        factory = async_sessionmaker(
            bind=self._admin_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        session = factory()
        try:
            yield session
        finally:
            await session.close()
    
    async def get_session_factory(self, tenant_id: str) -> async_sessionmaker[AsyncSession]:
        """Get session factory for tenant database."""
        if tenant_id not in self._session_factories:
            await self.get_engine(tenant_id)  # Creates engine + factory
        
        return self._session_factories[tenant_id]
    
    async def shutdown(self):
        """Dispose all tenant engines and admin engine."""
        for tenant_id, engine in self._engines.items():
            await engine.dispose()
            logfire.info('tenant_engine_manager.engine_disposed', tenant_id=tenant_id)
        
        if self._admin_engine:
            await self._admin_engine.dispose()
            logfire.info('tenant_engine_manager.admin_engine_disposed')
        
        self._engines.clear()
        self._session_factories.clear()

# Global manager instance
_tenant_engine_manager: TenantEngineManager | None = None

def get_tenant_engine_manager() -> TenantEngineManager:
    global _tenant_engine_manager
    if _tenant_engine_manager is None:
        _tenant_engine_manager = TenantEngineManager()
    return _tenant_engine_manager
```

### 3. Tenant Resolution Middleware

Extract tenant from request and inject into context:

```python
# backend/app/middleware/tenant_middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logfire

class TenantResolutionMiddleware(BaseHTTPMiddleware):
    """Extract tenant from request and inject into request state."""
    
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from URL path
        # Pattern: /accounts/{account_slug}/...
        path_parts = request.url.path.split('/')
        
        tenant_slug = None
        if len(path_parts) > 2 and path_parts[1] == 'accounts':
            tenant_slug = path_parts[2]
        
        # Or extract from header
        if not tenant_slug:
            tenant_slug = request.headers.get('X-Tenant-Slug')
        
        # Or extract from API token (after auth)
        if not tenant_slug and hasattr(request.state, 'api_token'):
            tenant_slug = request.state.api_token.tenant_slug
        
        if not tenant_slug:
            # Public endpoints (health check, etc.)
            return await call_next(request)
        
        # Store tenant info in request state
        request.state.tenant_slug = tenant_slug
        request.state.tenant_id = await self._resolve_tenant_id(tenant_slug)
        
        logfire.info(
            'tenant_middleware.resolved',
            tenant_slug=tenant_slug,
            tenant_id=request.state.tenant_id,
            path=request.url.path
        )
        
        return await call_next(request)
    
    async def _resolve_tenant_id(self, tenant_slug: str) -> str:
        """Resolve tenant slug to tenant ID from admin database."""
        # Cache this lookup (Redis or in-memory)
        # For now, lookup from admin database
        from ..database_multi_tenant import get_tenant_engine_manager
        from ..models.tenant_registry import TenantRegistry
        
        manager = get_tenant_engine_manager()
        async with manager._admin_session() as session:
            result = await session.execute(
                select(TenantRegistry).where(TenantRegistry.tenant_slug == tenant_slug)
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                raise HTTPException(404, f"Tenant not found: {tenant_slug}")
            
            return tenant.tenant_id
```

### 4. Tenant-Aware Database Dependency

FastAPI dependency that provides tenant-specific session:

```python
# backend/app/dependencies.py
from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def get_tenant_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: Provide database session for tenant's dedicated database.
    
    Extracts tenant ID from request state (set by TenantResolutionMiddleware),
    gets the appropriate engine from TenantEngineManager, and creates a session.
    """
    if not hasattr(request.state, 'tenant_id'):
        raise HTTPException(400, "Tenant not identified in request")
    
    tenant_id = request.state.tenant_id
    
    from .database_multi_tenant import get_tenant_engine_manager
    manager = get_tenant_engine_manager()
    
    # Get session factory for this tenant's database
    session_factory = await manager.get_session_factory(tenant_id)
    
    # Create session from tenant-specific factory
    session = session_factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

### 5. Using Tenant Database in Endpoints

```python
# backend/app/api/account_agents.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_tenant_db_session
from ..models.agent_instance import AgentInstanceModel

router = APIRouter(prefix="/accounts")

@router.get("/{account_slug}/agents")
async def list_agents(
    account_slug: str,
    session: AsyncSession = Depends(get_tenant_db_session)
):
    """
    List agent instances for tenant.
    
    Session is automatically routed to tenant's dedicated database.
    No need for account_id filtering - database is already tenant-specific.
    """
    result = await session.execute(
        select(AgentInstanceModel)
        # No WHERE account_id = ... needed!
    )
    agents = result.scalars().all()
    return {"agents": agents}

@router.post("/{account_slug}/agents/{instance_slug}/chat")
async def chat_endpoint(
    account_slug: str,
    instance_slug: str,
    message: str,
    session: AsyncSession = Depends(get_tenant_db_session)
):
    """
    Chat with agent instance.
    
    Database operations automatically isolated to tenant's database.
    """
    # Load agent instance (from tenant's database)
    result = await session.execute(
        select(AgentInstanceModel).where(
            AgentInstanceModel.instance_slug == instance_slug
        )
    )
    agent_instance = result.scalar_one_or_none()
    
    if not agent_instance:
        raise HTTPException(404, "Agent instance not found")
    
    # Process chat...
    # All database writes go to tenant's dedicated database
```

## Database Schema Management

### Schema Consistency

All tenant databases must have identical schema structure:

```sql
-- Each tenant database has the same tables:
CREATE TABLE accounts (...);
CREATE TABLE users (...);
CREATE TABLE agent_instances (...);
CREATE TABLE sessions (...);
CREATE TABLE messages (...);
CREATE TABLE llm_requests (...);
CREATE TABLE directory_lists (...);
CREATE TABLE directory_entries (...);
CREATE TABLE api_tokens (...);
-- etc.
```

### Migration Strategy

**Option A: Sequential Migrations (Alembic)**

```python
# migrations/run_tenant_migrations.py
from alembic import command
from alembic.config import Config

async def migrate_all_tenants():
    """Run migrations on all tenant databases."""
    manager = get_tenant_engine_manager()
    
    # Get all active tenants from admin database
    async with manager._admin_session() as session:
        tenants = await session.execute(
            select(TenantRegistry).where(TenantRegistry.is_active == True)
        )
        tenant_list = tenants.scalars().all()
    
    for tenant in tenant_list:
        try:
            # Configure Alembic for this tenant's database
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option(
                "sqlalchemy.url", 
                tenant.connection_string
            )
            
            # Run migration
            command.upgrade(alembic_cfg, "head")
            
            logfire.info(
                'tenant_migration.success',
                tenant_id=tenant.tenant_id,
                database=tenant.database_name
            )
        except Exception as e:
            logfire.error(
                'tenant_migration.failed',
                tenant_id=tenant.tenant_id,
                error=str(e)
            )
            # Continue with other tenants
```

**Option B: Parallel Migrations (Faster)**

```python
async def migrate_all_tenants_parallel():
    """Run migrations in parallel (careful with database load)."""
    manager = get_tenant_engine_manager()
    
    async with manager._admin_session() as session:
        tenants = await session.execute(
            select(TenantRegistry).where(TenantRegistry.is_active == True)
        )
        tenant_list = tenants.scalars().all()
    
    # Run migrations concurrently (limit concurrency to avoid overload)
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent migrations
    
    async def migrate_one(tenant):
        async with semaphore:
            # Run migration for this tenant
            await run_alembic_migration(tenant)
    
    await asyncio.gather(*[migrate_one(t) for t in tenant_list])
```

### Schema Validation

Ensure all tenant databases have correct schema:

```python
async def validate_tenant_schema(tenant_id: str) -> bool:
    """Validate that tenant database has correct schema."""
    manager = get_tenant_engine_manager()
    engine = await manager.get_engine(tenant_id)
    
    async with engine.begin() as conn:
        # Check critical tables exist
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tables = {row[0] for row in result}
        
        required_tables = {
            'accounts', 'users', 'agent_instances', 
            'sessions', 'messages', 'llm_requests',
            'directory_lists', 'directory_entries'
        }
        
        missing = required_tables - tables
        if missing:
            logfire.error(
                'tenant_schema.validation_failed',
                tenant_id=tenant_id,
                missing_tables=list(missing)
            )
            return False
        
        return True
```

## Tenant Provisioning

### New Tenant Setup

```python
async def provision_new_tenant(
    tenant_slug: str,
    tenant_name: str,
    database_name: str | None = None
) -> str:
    """
    Provision a new tenant with dedicated database.
    
    Steps:
    1. Create database on PostgreSQL instance
    2. Run schema migrations on new database
    3. Register tenant in control plane
    4. Create initial admin user
    """
    import uuid
    
    # Generate tenant ID
    tenant_id = str(uuid.uuid4())
    
    # Generate database name if not provided
    if not database_name:
        database_name = f"tenant_{tenant_slug.replace('-', '_')}"
    
    # Build connection string for new database
    base_url = os.getenv('POSTGRES_BASE_URL')  # postgresql://user:pass@host:5432/
    connection_string = f"{base_url}{database_name}"
    
    manager = get_tenant_engine_manager()
    
    try:
        # 1. Create database
        await create_database(database_name)
        
        # 2. Run migrations on new database
        await run_schema_migration(connection_string)
        
        # 3. Register in control plane
        async with manager._admin_session() as session:
            tenant_registry = TenantRegistry(
                tenant_id=tenant_id,
                tenant_slug=tenant_slug,
                database_name=database_name,
                connection_string=connection_string,
                is_active=True,
                config={'pool_size': 10, 'max_overflow': 5}
            )
            session.add(tenant_registry)
            await session.commit()
        
        # 4. Seed initial data (create Account record, admin user, etc.)
        await seed_tenant_database(tenant_id, tenant_name)
        
        logfire.info(
            'tenant_provisioning.success',
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            database=database_name
        )
        
        return tenant_id
        
    except Exception as e:
        logfire.error(
            'tenant_provisioning.failed',
            tenant_slug=tenant_slug,
            error=str(e)
        )
        # Rollback: Drop database if created
        await cleanup_failed_provisioning(database_name)
        raise

async def create_database(database_name: str):
    """Create new database on PostgreSQL instance."""
    # Connect to postgres database (not tenant database)
    postgres_url = os.getenv('POSTGRES_URL')  # postgresql://user:pass@host:5432/postgres
    
    engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE DATABASE {database_name}"))
    
    await engine.dispose()
```

## Connection Pooling Considerations

### Pool Size per Tenant

With dedicated databases, each tenant gets its own connection pool:

```
PostgreSQL max_connections = 100 (default)

Tenants:
- Tenant A: pool_size=10, max_overflow=5 (15 max connections)
- Tenant B: pool_size=10, max_overflow=5 (15 max connections)
- Tenant C: pool_size=10, max_overflow=5 (15 max connections)

Total potential: 45 connections (with 3 tenants)
```

**Scaling concerns**:
- With 10 tenants: 150 connections
- With 50 tenants: 750 connections (exceeds default `max_connections`)

**Solutions**:
1. **PgBouncer**: Connection pooler at database level
2. **Lower pool sizes**: pool_size=5 per tenant for many tenants
3. **Lazy engine creation**: Only create engines for active tenants
4. **Engine disposal**: Drop engines for inactive tenants

### PgBouncer Integration

```ini
# pgbouncer.ini
[databases]
customer_a = host=localhost dbname=customer_a
customer_b = host=localhost dbname=customer_b
customer_c = host=localhost dbname=customer_c

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

With PgBouncer, application can have larger pool_size without exhausting PostgreSQL connections.

## Monitoring & Observability

### Per-Tenant Metrics

```python
@router.get("/admin/tenant-stats/{tenant_id}")
async def get_tenant_stats(tenant_id: str):
    """Get database stats for tenant."""
    manager = get_tenant_engine_manager()
    engine = await manager.get_engine(tenant_id)
    
    async with engine.begin() as conn:
        # Database size
        size_result = await conn.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """))
        db_size = size_result.scalar()
        
        # Connection count
        conn_result = await conn.execute(text("""
            SELECT count(*) FROM pg_stat_activity 
            WHERE datname = current_database()
        """))
        active_connections = conn_result.scalar()
        
        # Table sizes
        tables_result = await conn.execute(text("""
            SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
            FROM pg_tables WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """))
        largest_tables = [dict(row) for row in tables_result]
    
    # Pool stats from SQLAlchemy engine
    pool = engine.pool
    pool_stats = {
        'size': pool.size(),
        'checked_in': pool.checkedin(),
        'overflow': pool.overflow(),
        'checked_out': pool.checkedout()
    }
    
    return {
        'tenant_id': tenant_id,
        'database_size': db_size,
        'active_connections': active_connections,
        'pool_stats': pool_stats,
        'largest_tables': largest_tables
    }
```

## Backup & Recovery

### Per-Tenant Backups

```bash
# Backup single tenant database
pg_dump -h localhost -U postgres -Fc customer_a > customer_a_backup.dump

# Restore single tenant database
pg_restore -h localhost -U postgres -d customer_a customer_a_backup.dump
```

### Automated Backup Strategy

```python
async def backup_tenant_database(tenant_id: str, backup_path: str):
    """Run pg_dump for tenant database."""
    manager = get_tenant_engine_manager()
    
    async with manager._admin_session() as session:
        result = await session.execute(
            select(TenantRegistry).where(TenantRegistry.tenant_id == tenant_id)
        )
        tenant = result.scalar_one()
    
    # Run pg_dump
    cmd = [
        'pg_dump',
        '-h', 'localhost',
        '-U', 'postgres',
        '-Fc',  # Custom format
        '-f', f"{backup_path}/{ tenant.database_name}_{datetime.now().isoformat()}.dump",
        tenant.database_name
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode != 0:
        raise Exception(f"Backup failed: {result.stderr}")
    
    logfire.info(
        'tenant_backup.success',
        tenant_id=tenant_id,
        database=tenant.database_name
    )
```

## Migration from Current Architecture

### Phase 1: Dual-Write Mode

Write to both shared database and tenant databases:

```python
async def save_message_dual_write(session_id: UUID, message: str):
    """Write to both databases during migration."""
    
    # Write to current shared database
    db_service = get_database_service()
    async with db_service.get_session() as session:
        msg = Message(session_id=session_id, content=message)
        session.add(msg)
        await session.commit()
    
    # Also write to tenant database
    tenant_manager = get_tenant_engine_manager()
    tenant_session_factory = await tenant_manager.get_session_factory(tenant_id)
    async with tenant_session_factory() as tenant_session:
        msg_copy = Message(session_id=session_id, content=message)
        tenant_session.add(msg_copy)
        await tenant_session.commit()
```

### Phase 2: Verify Data Consistency

```python
async def verify_data_consistency(tenant_id: str):
    """Compare shared DB and tenant DB for consistency."""
    # Query both databases
    # Compare record counts, sample records
    # Log discrepancies
```

### Phase 3: Switch Reads to Tenant DB

Update code to read from tenant database while still dual-writing.

### Phase 4: Stop Writing to Shared DB

Once confident, remove dual-write logic.

### Phase 5: Archive Shared DB Data

Export tenant data from shared database for archival.

## Limitations & Trade-offs

**Limitations**:
- More complex than shared database
- Higher connection pool overhead
- Migration complexity (must run on all tenant DBs)
- Can't easily query across tenants
- Backup/restore more complex

**When NOT to use**:
- Small number of tenants (< 10)
- Low data volume per tenant
- Frequent cross-tenant analytics needed
- Limited operational resources

**When to use**:
- Regulatory compliance requirements
- Large enterprise customers
- Performance isolation critical
- Per-tenant customization needed
- Geographic data residency requirements

## Summary

Dedicated database per tenant provides the strongest isolation model at the cost of increased operational complexity. SQLAlchemy 2.0 supports this pattern through dynamic engine creation and routing.

**Key components**:
1. TenantEngineManager - Dynamic engine pool
2. TenantResolutionMiddleware - Extract tenant from request
3. get_tenant_db_session - Tenant-aware FastAPI dependency
4. TenantRegistry - Control plane mapping
5. Migration tooling - Multi-tenant schema management

**Best for**: SaaS platforms with enterprise customers requiring strong data isolation, compliance, or performance guarantees.
