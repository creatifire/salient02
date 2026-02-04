# Directory Admin UI - Architecture Decision Record

## Context & Requirements

Building a directory schema administration UI for the SaaS platform with the following requirements:

### Functional Requirements
1. **Multi-User Accounts**: Multiple users per account with role-based permissions
2. **Self-Service**: Account owners manage their own directory data
3. **Schema Customization**: Accounts can customize schemas from a central library
4. **Granular Permissions**: Users can view/edit specific directories within their account
5. **Super Admin Access**: Internal staff can access any account for support

### Technical Constraints
1. **Shared Database**: Admin UI shares PostgreSQL database with chat API
2. **Multi-Tenant**: Strict account-level data isolation
3. **Existing System**: Must coexist with current chat API (no disruption)
4. **Auth Requirement**: Needs proper user authentication (not just API tokens)

### Users & Access Patterns
- **Account Owners**: Self-service schema + data management
- **Account Users**: View or edit specific directories (role-based)
- **Super Admins**: Internal staff helping with account setup
- **Chat API Clients**: Continue using API key authentication (unchanged)

## Decision: JWT Auth + Monorepo Architecture

### Authentication: JWT-Based with RBAC

**Chosen**: Option 1 - JWT tokens with role-based access control

**Rationale**:
- Supports multi-app architecture (admin UI + chat API can share tokens)
- Stateless scaling for production
- Fine-grained RBAC naturally fits in token claims
- Industry standard (easier to hire for, more libraries, known security patterns)

**Implementation**:
```
Auth Flow:
1. User logs in → JWT token issued (contains user_id, account_ids[], roles)
2. Token stored in HTTP-only cookie + localStorage (for API calls)
3. Admin API validates token on each request
4. Permissions checked against database (directory-level granularity)
```

**New Database Tables**:
```sql
users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name VARCHAR,
  is_super_admin BOOLEAN DEFAULT false,
  created_at TIMESTAMP
)

account_users (
  id UUID PRIMARY KEY,
  account_id UUID REFERENCES accounts(id),
  user_id UUID REFERENCES users(id),
  role VARCHAR NOT NULL,  -- 'owner', 'admin', 'editor', 'viewer'
  created_at TIMESTAMP,
  UNIQUE(account_id, user_id)
)

directory_permissions (
  id UUID PRIMARY KEY,
  account_user_id UUID REFERENCES account_users(id),
  directory_list_id UUID REFERENCES directory_lists(id),
  permission VARCHAR NOT NULL,  -- 'view', 'edit', 'admin'
  UNIQUE(account_user_id, directory_list_id)
)

account_schema_customizations (
  id UUID PRIMARY KEY,
  account_id UUID REFERENCES accounts(id),
  base_schema_file VARCHAR NOT NULL,  -- e.g., 'medical_professional.yaml'
  custom_schema_yaml TEXT,  -- YAML string with customizations
  is_active BOOLEAN DEFAULT true,
  version INTEGER DEFAULT 1,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

**Permission Model**:
- **Account-Level Roles**: owner, admin, editor, viewer
- **Directory-Level Permissions**: view, edit, admin (optional, defaults to account role)
- **Super Admin**: Bypass all checks (internal staff only)

**Token Claims**:
```json
{
  "sub": "user-uuid",
  "email": "jane@acme.com",
  "accounts": [
    {
      "account_id": "acme-uuid",
      "role": "owner"
    }
  ],
  "is_super_admin": false,
  "exp": 1234567890
}
```

### Repository Structure: Monorepo

**Chosen**: Keep admin UI in existing `salient02` monorepo

**Rationale**:
1. **Shared Database**: Both apps need coordinated migrations
2. **Shared Models**: DirectoryList, DirectoryEntry, Account models
3. **Shared Schemas**: YAML schema files accessed by both apps
4. **Team Size**: Small team benefits from single repo
5. **Can Split Later**: Monorepo doesn't prevent future extraction

**Directory Structure**:
```
salient02/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py                  # Existing chat endpoints (API key auth)
│   │   │   └── admin_legacy.py          # Existing admin (no auth, dev only)
│   │   ├── auth/                        # NEW: Shared auth module
│   │   │   ├── __init__.py
│   │   │   ├── models.py                # User, AccountUser, DirectoryPermission
│   │   │   ├── service.py               # Login, register, token generation
│   │   │   ├── dependencies.py          # get_current_user, require_permission
│   │   │   ├── jwt.py                   # JWT encode/decode utils
│   │   │   └── password.py              # Bcrypt hashing
│   │   ├── models/                      # Existing models
│   │   │   ├── directory.py             # DirectoryList, DirectoryEntry
│   │   │   ├── account.py               # Account
│   │   │   └── ...
│   │   └── services/
│   │       └── directory_service.py     # Existing service
│   │
│   ├── admin_api/                       # NEW: Separate FastAPI app for admin
│   │   ├── main.py                      # Admin API entry point (port 8001)
│   │   ├── routers/
│   │   │   ├── auth.py                  # /api/auth/login, /register
│   │   │   ├── directory_admin.py       # /api/admin/directory-lists
│   │   │   ├── schema_library.py        # /api/admin/schemas
│   │   │   └── user_management.py       # /api/admin/users
│   │   └── middleware/
│   │       └── auth_middleware.py       # JWT validation
│   │
│   ├── migrations/                      # Alembic migrations (shared)
│   │   └── versions/
│   │       └── xxx_add_auth_tables.py   # NEW migration
│   │
│   └── config/
│       └── directory_schemas/           # YAML schemas (shared)
│
├── web/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── chat/                    # Existing chat UI
│   │   │   │   └── [account]/[agent].astro
│   │   │   └── admin/                   # NEW: Admin UI
│   │   │       ├── login.astro          # Login page
│   │   │       ├── index.astro          # Admin dashboard
│   │   │       ├── directories.astro    # Directory management
│   │   │       ├── schemas.astro        # Schema library browser
│   │   │       └── users.astro          # User/role management
│   │   └── components/
│   │       └── admin/                   # NEW: Admin components
│   │           ├── DirectorySchemaForm.tsx
│   │           ├── SchemaLibrary.tsx
│   │           └── UserRoleManager.tsx
│   │
│   └── astro.config.mjs
│
├── docker-compose.dev.yml               # Updated to run both APIs
└── memorybank/
    ├── architecture/
    │   └── directory-admin-auth.md      # This document will move here
    └── brainstorming/
        ├── directory-schema-administration-ui.md  # Original design
        └── directory-admin-architecture-decision.md  # This file
```

**Why Not Polyrepo**:
- Shared database makes independent repos problematic (migration coordination nightmare)
- Model synchronization requires package publishing overhead
- Small team (1-3 people) doesn't need repo-level isolation
- Can extract to separate repo later when team grows or scaling needs diverge

**Production Deployment**: See [Container Deployment Architecture](container-deployment-architecture.md) for:
- Render.com deployment strategy with Docker containers
- render.yaml blueprint configuration
- Service isolation and communication patterns
- Cost optimization and scaling strategies

## API Separation Strategy

### Three Docker Containers (Same Monorepo)

**Chat API** (`services/chat-api/`) - Existing functionality
- Authentication: API key validation (existing pattern)
- Purpose: LLM chat endpoints for widgets/integrations
- Endpoints: `/accounts/{slug}/agents/{instance}/chat`
- Users: Programmatic clients (websites, apps, scripts)
- Deployment: Render.com Docker container

**Admin API** (`services/admin-api/`) - New admin backend
- Authentication: JWT tokens (new)
- Purpose: Human users managing directory data
- Endpoints: `/api/auth/...`, `/api/admin/...`
- Users: Account owners, account users, super admins
- Deployment: Render.com Docker container

**Admin UI** (`services/admin-ui/`) - New admin frontend
- Stack: Astro + React (separate from demo sites in `web/`)
- Purpose: Directory management interface
- Authentication: JWT tokens from Admin API
- Deployment: Render.com Docker container or static site

**Shared Code** (`backend/`):
- Database models (`backend/app/models/`)
- Auth module (`backend/app/auth/`)
- Services (`backend/app/services/`)
- YAML schemas (`backend/config/directory_schemas/`)
- Migrations (`backend/migrations/`)

**Development Setup**:
```bash
# Docker Compose (recommended)
docker-compose -f docker-compose.dev.yml up

# Access services:
# - Chat API: http://localhost:8000
# - Admin API: http://localhost:8001
# - Admin UI: http://localhost:4321
```

**Production Deployment** (Render.com):
- Three separate Docker containers deployed via `render.yaml` blueprint
- Shared PostgreSQL database (private network)
- Services communicate via internal hostnames
- Independent scaling and deployment
- See [Container Deployment Architecture](container-deployment-architecture.md)

## Schema Customization Architecture

### Central Schema Library + Account Customizations

**Base Schemas** (`backend/config/directory_schemas/`):
- Maintained by platform team
- Versioned (e.g., `medical_professional.v2.yaml`)
- Immutable after accounts adopt them

**Account Customizations** (Database):
- Stored in `account_schema_customizations` table
- YAML overlay that extends base schema
- Changes don't affect other accounts

**Customization Example**:
```yaml
# Base: medical_professional.yaml (shared)
entry_type: medical_professional
required_fields:
  - specialty
  - department
optional_fields:
  - board_certifications

# Account Customization (stored in DB)
base_schema: medical_professional.yaml
base_version: 2
customizations:
  required_fields:
    - npi_number              # Acme requires this
  optional_fields:
    - telemedicine_available  # Acme-specific field
  fields:
    npi_number:
      type: string
      description: "National Provider Identifier"
    telemedicine_available:
      type: boolean
      description: "Offers virtual appointments"
```

**Schema Resolution**:
1. Load base schema from YAML file
2. Check for account customization in database
3. Merge customizations (add fields, change required/optional)
4. Cache merged schema per account
5. Use merged schema for form generation and validation

**Benefits**:
- Accounts get platform updates (new base schema versions)
- Accounts can add custom fields without forking
- Platform maintains schema quality standards
- Migration path when base schemas change

## Permission Hierarchy

### Account-Level Roles

| Role | Directory View | Directory Edit | Schema Customize | User Manage |
|------|---------------|----------------|------------------|-------------|
| **Owner** | All | All | Yes | Yes |
| **Admin** | All | All | Yes | Users only |
| **Editor** | All | All | No | No |
| **Viewer** | All | None | No | No |

### Directory-Level Permissions (Optional Overrides)

If an account wants finer control, they can set per-directory permissions:

```
Example: User "Bob" in Acme account
- Account Role: Editor (default: can edit all directories)
- Directory Override: medical_professionals → View only
- Directory Override: faq → Edit

Result:
- Can view medical_professionals (override applied)
- Can edit faq (override applied)
- Can edit all other directories (account role applies)
```

### Super Admin (Platform Staff)

- Bypass all permission checks
- Can access any account's data
- Audit logged for all actions
- Used only for customer support

## Migration Path

### Phase 1: Auth Foundation (Week 1-2)
- [ ] Add auth tables (users, account_users, directory_permissions)
- [ ] Create `backend/app/auth/` module
- [ ] Implement JWT service (login, register, token validation)
- [ ] Add password hashing (bcrypt)

### Phase 2: Admin API Endpoints (Week 2-3)
- [ ] Create `backend/admin_api/main.py`
- [ ] Auth endpoints: `/api/auth/login`, `/api/auth/register`
- [ ] Directory CRUD endpoints (from design doc)
- [ ] Schema library endpoints
- [ ] Permission checking middleware

### Phase 3: Admin Frontend (Week 3-4)
- [ ] Login page (`/admin/login`)
- [ ] Directory admin UI (from design doc)
- [ ] Schema library browser
- [ ] User/role management UI

### Phase 4: Schema Customization (Week 4-5)
- [ ] Account schema customization table
- [ ] Schema merge logic
- [ ] UI for customizing schemas
- [ ] Validation against customized schemas

### Phase 5: Polish & Security (Week 5-6)
- [ ] Refresh token flow
- [ ] Rate limiting per user
- [ ] Audit logging
- [ ] Security testing
- [ ] Documentation

## Security Considerations

### Password Security
- Bcrypt hashing (cost factor 12)
- Minimum password requirements (8 chars, complexity)
- Rate limit login attempts (5 per 15 minutes)

### Token Security
- Short-lived access tokens (15 minutes)
- Refresh tokens (7 days, HTTP-only cookie)
- Tokens signed with secret key (rotate quarterly)
- Token revocation via blacklist (Redis)

### Permission Validation
- Check on every admin API request
- Validate directory_list belongs to user's account
- Super admin access audit logged
- SQL queries filter by account_id (defense in depth)

### Account Isolation
- User can only access accounts they're linked to (account_users table)
- Directory queries join through account_id
- Schema customizations scoped to account_id
- No cross-account data leakage

## Open Questions

1. **User Signup Flow**: Self-service account creation or invitation-only?
   - Suggestion: Start with invitation-only (owner invites users)
   - Add self-service account creation later

2. **Email Verification**: Required for new users?
   - Suggestion: Yes, send verification email (prevents abuse)

3. **Password Reset**: Self-service or admin-assisted?
   - Suggestion: Self-service via email link

4. **Session Duration**: How long should users stay logged in?
   - Suggestion: 7-day refresh token, 15-minute access token

5. **Schema Version Migration**: When base schema updates, how do accounts migrate?
   - Suggestion: Opt-in migration with preview + validation

6. **Audit Log Retention**: How long to keep audit logs?
   - Suggestion: 90 days for regular accounts, 1 year for super admin actions

## References

- [Directory Schema Administration UI Design](directory-schema-administration-ui.md)
- [Multi-Tenant Security Architecture](../architecture/multi-tenant-security.md)
- [Directory Search Tool Architecture](../architecture/directory-search-tool.md)

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-03 | JWT auth over session-based | Multi-app support, stateless scaling |
| 2026-02-03 | Monorepo over polyrepo | Shared database, small team, easier migrations |
| 2026-02-03 | Separate FastAPI apps | Different auth patterns, independent scaling later |
| 2026-02-03 | Account schema customization in DB | Flexibility without forking base schemas |
