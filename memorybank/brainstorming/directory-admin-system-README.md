# Directory Administration System - Documentation Index

## Overview

Complete documentation for the Directory Schema Administration UI - a multi-tenant, role-based admin interface for managing directory data in the SaaS platform.

## Core Documents

### 1. [Container Deployment Architecture](container-deployment-architecture.md) 🆕
**Purpose**: Production deployment strategy for Render.com
**Contents**:
- Service subdirectory structure (3 Docker containers)
- Dockerfile examples for each service
- render.yaml blueprint configuration
- Cost optimization and scaling strategies
- Migration path from current structure

**Read this for**: Production deployment, Docker setup, Render.com configuration

---

### 2. [UI Design](directory-schema-administration-ui.md)
**Purpose**: Technical design for the admin interface
**Contents**:
- Dynamic form generation from YAML schemas
- React/TypeScript component architecture
- API endpoints and data flow
- Field type mappings

**Read this for**: Implementation details, code examples, frontend architecture

---

### 3. [Architecture Decision Record](directory-admin-architecture-decision.md)
**Purpose**: Architectural decisions and rationale
**Contents**:
- Monorepo vs polyrepo decision
- Separate FastAPI apps strategy
- Permission hierarchy model
- Schema customization architecture
- Database schema design
- Migration path

**Read this for**: Understanding why we made these choices, overall system architecture

---

### 4. [Authentication Options Analysis](directory-admin-auth-options.md)
**Purpose**: Authentication strategy evaluation
**Contents**:
- JWT vs Session vs Hybrid comparison
- Detailed pros/cons for each option
- Code examples for each approach
- Recommendation: JWT-based auth
- Implementation roadmap

**Read this for**: Authentication implementation details, security considerations

---

## Quick Start

### For Product/Business

**What problem does this solve?**
- Account owners need to manage their directory data (doctors, classes, locations, etc.) without CSV files
- Multiple users per account need different permission levels
- Accounts want to customize schemas for their specific needs

**Key Features**:
- Self-service directory management
- Central schema library with account customizations
- Role-based access control (owner, admin, editor, viewer)
- Directory-level permission overrides

---

### For Developers

**Architecture Summary**:
- **Frontend**: Astro + React in `services/admin-ui/` (separate from demo sites)
- **Backend**: Three Docker containers (chat-api, admin-api, admin-ui)
- **Auth**: JWT tokens with RBAC
- **Database**: Shared PostgreSQL on Render.com
- **Deployment**: Render.com with render.yaml blueprint
- **Schemas**: YAML base schemas + database-stored customizations

**Key Files to Read**:
1. [Container Deployment Architecture](container-deployment-architecture.md) - Production setup
2. [Architecture Decision Record](directory-admin-architecture-decision.md) - System architecture
3. [UI Design](directory-schema-administration-ui.md) - Implementation details
4. [Auth Options](directory-admin-auth-options.md) - Authentication approach

**Implementation Phases**:
- Phase 1: Auth foundation (users, tokens, permissions) - 1 week
- Phase 2: Admin API endpoints - 1 week  
- Phase 3: Admin frontend UI - 1 week
- Phase 4: Schema customization - 1 week
- Phase 5: Polish & security - 1 week

---

### For DevOps

**Infrastructure** (see [Container Deployment Architecture](container-deployment-architecture.md)):
- **Three Docker Containers**: chat-api, admin-api, admin-ui (separate deployments)
- **Shared PostgreSQL Database**: Render.com managed Postgres
- **Deployment Platform**: Render.com with render.yaml blueprint
- **Private Networking**: Services communicate via internal hostnames
- **Cost**: Starting at ~$21-46/month (depending on static vs container for admin UI)

**Deployment Workflow**:
- Push to Git → Render auto-deploys via blueprint
- Build filters prevent unnecessary rebuilds
- Zero-downtime deployments
- Automated health checks

**Local Development**:
```bash
docker-compose -f docker-compose.dev.yml up
```

---

## Design Decisions Summary

### Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Repository Structure** | Monorepo with service subdirectories | Shared database, coordinated migrations, easy container extraction |
| **API Architecture** | Three separate Docker containers | Independent deployment, service isolation, production-ready |
| **Authentication** | JWT tokens | Stateless, multi-app support, industry standard |
| **Permission Model** | RBAC + directory overrides | Flexible without over-complicating |
| **Schema Storage** | Base YAML + DB customizations | Platform maintains quality, accounts get flexibility |
| **Deployment** | Render.com with Docker | Low-cost, managed Postgres, auto-scaling |

### Permission Hierarchy

```
Super Admin (platform staff)
  └─ Can access any account

Account Owner
  └─ Full access to all directories + user management

Account Admin  
  └─ Full access to all directories + user management (except owners)

Account Editor
  └─ Can edit all directories (unless overridden)
  └─ Directory Override: Specific directories → view only or edit

Account Viewer
  └─ View-only access to all directories
```

---

## Database Schema Overview

### New Tables

**Authentication & Users**:
```sql
users                    -- Platform users (email, password_hash)
account_users            -- User membership in accounts (with role)
directory_permissions    -- Optional directory-level overrides
```

**Schema Customization**:
```sql
account_schema_customizations  -- Account-specific schema extensions
```

### Existing Tables (Used, Not Modified)

```sql
accounts                 -- Tenant accounts
directory_lists          -- Directory collections per account
directory_entries        -- Individual entries (doctors, classes, etc.)
sessions                 -- Session tracking (extended with user_id)
```

---

## API Structure

### Admin API (New) - Port 8001

**Authentication Endpoints**:
- `POST /api/auth/login` - User login (returns JWT)
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (revoke tokens)

**Directory Management**:
- `GET /api/admin/directory-lists` - List account's directories
- `GET /api/admin/directory-lists/{id}/entries` - List entries with pagination
- `POST /api/admin/directory-lists/{id}/entries` - Create entry
- `PUT /api/admin/directory-lists/{id}/entries/{entry_id}` - Update entry
- `DELETE /api/admin/directory-lists/{id}/entries/{entry_id}` - Delete entry

**Schema Library**:
- `GET /api/admin/schemas` - List available base schemas
- `GET /api/admin/schemas/{entry_type}` - Get schema definition
- `GET /api/admin/accounts/{id}/schemas` - List account customizations
- `POST /api/admin/accounts/{id}/schemas` - Create schema customization
- `PUT /api/admin/accounts/{id}/schemas/{schema_id}` - Update customization

**User Management**:
- `GET /api/admin/accounts/{id}/users` - List account users
- `POST /api/admin/accounts/{id}/users` - Invite user
- `PUT /api/admin/accounts/{id}/users/{user_id}` - Update role
- `DELETE /api/admin/accounts/{id}/users/{user_id}` - Remove user

### Chat API (Existing) - Port 8000

- Unchanged - continues using API key authentication
- No breaking changes to existing clients

---

## Frontend Structure

### Admin Pages

```
/admin/
├── login                  # Login/register page
├── index                  # Admin dashboard (directory list)
├── directories            # Directory management UI
│   └── [listId]          # Edit specific directory
├── schemas               # Schema library browser
└── users                 # User/role management
```

### Key Components

```
DirectorySchemaForm.tsx    # Dynamic form generator
SchemaLibrary.tsx          # Browse and adopt schemas
UserRoleManager.tsx        # Manage account users
DirectoryAdmin.tsx         # Main admin interface
```

---

## Security Highlights

### Authentication
- JWT tokens (15-minute access, 7-day refresh)
- Bcrypt password hashing (cost 12)
- Rate limiting on login (5 attempts per 15 minutes)
- HTTP-only cookies for refresh tokens

### Authorization
- Every request validates JWT signature
- Permission checks on every admin API call
- Account isolation via `account_id` filtering
- Directory-level permissions for fine-grained control

### Data Protection
- Schema validation on all inputs
- SQL injection prevention (parameterized queries)
- CSRF protection (SameSite cookies)
- Audit logging for all admin actions

---

## Migration Strategy

### Phase 1: Non-Breaking (Week 1)
- Add auth tables (migration)
- Create auth module (no endpoints yet)
- Generate API keys for existing accounts

### Phase 2: Soft Launch (Week 2-3)
- Deploy admin API (separate port)
- Enable for internal testing only
- Collect feedback, iterate

### Phase 3: Customer Beta (Week 4)
- Invite select customers to test
- Document setup process
- Support migration from CSV imports

### Phase 4: General Availability (Week 5-6)
- Full production rollout
- Update documentation
- Training materials for customers

---

## Open Questions & Future Work

### Open Questions

1. **Self-Service Account Creation**: Allow public signup or invitation-only?
2. **Email Verification**: Required for new users?
3. **Password Reset Flow**: Self-service or support-assisted?
4. **Schema Version Migration**: How do accounts upgrade when base schemas change?
5. **Audit Log Retention**: 90 days? 1 year? Configurable per account?

### Future Enhancements

- **Schema Version Control**: Track changes to account customizations
- **Bulk Import UI**: CSV upload with preview/validation
- **Data Quality Checks**: Duplicate detection, completeness scoring
- **Audit Trail UI**: View who changed what and when
- **API Documentation**: Auto-generated OpenAPI docs
- **Mobile App**: Native iOS/Android admin app

---

## Related Documentation

### Architecture
- [Multi-Tenant Security](../architecture/multi-tenant-security.md)
- [Directory Search Tool](../architecture/directory-search-tool.md)
- [Agent and Tool Design](../architecture/agent-and-tool-design.md)

### User Guides
- [Loading Directories](../userguide/loading-directories.md)
- [Adding/Modifying Directory Schemas](../userguide/adding-modifying-directory-schemas.md)

### Project Management
- [Epic 0023: Directory Service](../project-management/0023-directory-service.md)
- [Epic 0026: Simple Admin Frontend](../project-management/0026-simple-admin-frontend.md)

---

## Contact & Feedback

For questions or suggestions about this design:
- Review the three core documents linked at the top
- Check open questions in [Architecture Decision Record](directory-admin-architecture-decision.md)
- Submit feedback via project management channels

---

**Last Updated**: February 3, 2026  
**Status**: Design Complete, Ready for Implementation  
**Owner**: Platform Team
