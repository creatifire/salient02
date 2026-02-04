# Authentication Options for Directory Admin UI

## Context

Building admin UI for multi-tenant SaaS platform with:
- Multiple users per account with RBAC
- Self-service schema + data management
- Account-level schema customization
- Shared database with chat API
- Super admin access for support

## Option 1: JWT-Based Authentication (✅ RECOMMENDED)

### Architecture

**Pattern**: Stateless JWT tokens with claims containing user identity and permissions

**Flow**:
```
1. User enters email/password → POST /api/auth/login
2. Backend validates credentials → issues JWT access token + refresh token
3. Access token (15min) stored in memory, refresh token (7d) in HTTP-only cookie
4. Every admin API request includes access token in Authorization header
5. Backend validates JWT signature, extracts user_id, account_ids, roles
6. Check permissions against database for directory-specific access
7. Token expires → frontend uses refresh token to get new access token
```

**Database Schema**:
```sql
users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,  -- bcrypt
  name VARCHAR,
  is_super_admin BOOLEAN DEFAULT false,
  created_at TIMESTAMP
)

account_users (
  id UUID PRIMARY KEY,
  account_id UUID REFERENCES accounts,
  user_id UUID REFERENCES users,
  role VARCHAR NOT NULL,  -- 'owner', 'admin', 'editor', 'viewer'
  UNIQUE(account_id, user_id)
)

directory_permissions (
  id UUID PRIMARY KEY,
  account_user_id UUID REFERENCES account_users,
  directory_list_id UUID REFERENCES directory_lists,
  permission VARCHAR NOT NULL,  -- 'view', 'edit', 'admin'
  UNIQUE(account_user_id, directory_list_id)
)
```

**JWT Token Claims**:
```json
{
  "sub": "user-uuid",
  "email": "jane@acme.com",
  "accounts": [
    {
      "account_id": "acme-uuid",
      "role": "owner"
    },
    {
      "account_id": "beta-corp-uuid",
      "role": "editor"
    }
  ],
  "is_super_admin": false,
  "exp": 1234567890
}
```

**Code Example**:
```python
# backend/app/auth/dependencies.py
from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt
from .models import User, AccountUser

async def get_current_user(
    authorization: str = Header(...)
) -> User:
    """Extract and validate JWT token, return User."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        
        # Load user from DB (or cache)
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(401, "User not found")
        
        return user
    except JWTError:
        raise HTTPException(401, "Invalid token")

async def require_account_access(
    account_id: str,
    user: User = Depends(get_current_user),
    min_role: str = "viewer"
) -> AccountUser:
    """Verify user has access to account with minimum role."""
    account_user = await get_account_user(account_id, user.id)
    
    if not account_user:
        raise HTTPException(403, "Access denied to account")
    
    # Check role hierarchy
    role_hierarchy = {"owner": 4, "admin": 3, "editor": 2, "viewer": 1}
    if role_hierarchy[account_user.role] < role_hierarchy[min_role]:
        raise HTTPException(403, f"Requires {min_role} role")
    
    return account_user

async def require_directory_permission(
    directory_list_id: str,
    permission: str,  # 'view', 'edit', 'admin'
    account_user: AccountUser = Depends(require_account_access)
):
    """Check directory-level permission (overrides account role)."""
    # Check for directory-specific override
    dir_perm = await get_directory_permission(account_user.id, directory_list_id)
    
    if dir_perm:
        # Use directory-specific permission
        allowed = check_permission_level(dir_perm.permission, permission)
    else:
        # Fall back to account role
        allowed = check_account_role_permission(account_user.role, permission)
    
    if not allowed:
        raise HTTPException(403, f"Insufficient permissions: {permission} required")
```

**Usage in Endpoints**:
```python
# backend/admin_api/routers/directory_admin.py
@router.get("/directory-lists/{list_id}/entries")
async def list_entries(
    list_id: str,
    user: User = Depends(get_current_user),
    account_user: AccountUser = Depends(require_account_access)
):
    """List directory entries (requires view permission)."""
    await require_directory_permission(list_id, "view", account_user)
    
    # User has access, fetch entries
    entries = await DirectoryService.search(...)
    return {"entries": entries}

@router.post("/directory-lists/{list_id}/entries")
async def create_entry(
    list_id: str,
    entry_data: dict,
    user: User = Depends(get_current_user),
    account_user: AccountUser = Depends(require_account_access)
):
    """Create entry (requires edit permission)."""
    await require_directory_permission(list_id, "edit", account_user)
    
    # Create entry...
    return {"entry": entry}
```

### Pros

✅ **Stateless Scaling**: No server-side session storage, horizontal scaling easy

✅ **Multi-App Support**: Same tokens work for admin UI, chat API, future apps

✅ **Standard Protocol**: Well-understood, many libraries (PyJWT, jose)

✅ **Token Contains Context**: User ID, accounts, roles in token (no DB lookup per request)

✅ **Flexible Permissions**: RBAC + directory-level overrides naturally fit

✅ **Refresh Token Flow**: Long-lived sessions without security compromise

✅ **Social Login Ready**: Easy to add OAuth providers later (Google, Microsoft)

✅ **Mobile Friendly**: Works for future mobile apps

### Cons

⚠️ **More Initial Code**: ~400 lines (auth service, JWT utils, dependencies)

⚠️ **Token Revocation**: Requires blacklist (Redis) or short expiry times

⚠️ **Refresh Token Management**: Need secure storage (HTTP-only cookies) and rotation logic

⚠️ **Token Size**: Large tokens if user has many accounts (mitigated with short expiry)

⚠️ **Clock Sync**: Servers need synchronized time for exp validation

### Implementation Effort

- **Database**: 3 new tables + migration (4 hours)
- **Auth Service**: Login, register, token generation (8 hours)
- **Middleware**: JWT validation, permission checking (6 hours)
- **Frontend**: Login page, token storage, API client (6 hours)
- **Testing**: Unit + integration tests (8 hours)

**Total**: ~32 hours (4 days)

### Security Notes

- Use bcrypt for password hashing (cost 12)
- Access token: 15 minutes expiry
- Refresh token: 7 days, HTTP-only cookie, SameSite=strict
- Rate limit login endpoint (5 attempts per 15 minutes)
- Token secret rotation quarterly
- Audit log all authentication events

---

## Option 2: Session-Based Authentication

### Architecture

**Pattern**: Server-side sessions with database-backed user and permission lookup

**Flow**:
```
1. User enters email/password → POST /api/auth/login
2. Backend validates credentials → creates session in database
3. Session ID stored in HTTP-only cookie
4. Every request includes session cookie
5. Backend loads session from DB, checks user_id
6. Load user's account_users records, verify account access
7. Check directory permissions from database
```

**Database Schema**:
```sql
-- Extend existing sessions table
ALTER TABLE sessions ADD COLUMN user_id UUID REFERENCES users(id);

-- Same users, account_users, directory_permissions as JWT option
```

**Code Example**:
```python
# backend/app/auth/dependencies.py
from fastapi import Depends, Request, HTTPException
from .models import User, Session

async def get_current_user(request: Request) -> User:
    """Load user from session cookie."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(401, "Not authenticated")
    
    # Load session from DB
    session = await get_session(session_id)
    if not session or not session.user_id:
        raise HTTPException(401, "Invalid session")
    
    # Load user
    user = await get_user_by_id(session.user_id)
    if not user:
        raise HTTPException(401, "User not found")
    
    return user

# Same require_account_access and require_directory_permission as JWT
```

### Pros

✅ **Simpler Implementation**: ~250 lines (builds on existing session middleware)

✅ **Easy Revocation**: Delete session row → user logged out immediately

✅ **Immediate Permission Changes**: User role changed → takes effect next request

✅ **Familiar Pattern**: Django/Rails style (more developers know it)

✅ **No Token Expiry Logic**: Session stays valid until explicitly revoked

✅ **Smaller Cookies**: Just session ID, not full JWT

### Cons

❌ **Stateful**: Requires database lookup on every request (performance impact)

❌ **Scaling Harder**: Need sticky sessions or shared session store (Redis)

❌ **Multi-App Complexity**: Hard to share sessions across admin UI + chat API

❌ **Database Load**: Every request queries sessions table

❌ **Not Mobile Friendly**: Cookie-based auth problematic for native apps

### Implementation Effort

- **Database**: Extend sessions table, add 3 new tables (3 hours)
- **Auth Service**: Login, register (6 hours)
- **Middleware**: Session validation, permission checking (5 hours)
- **Frontend**: Login page, API client (5 hours)
- **Testing**: Unit + integration tests (6 hours)

**Total**: ~25 hours (3 days)

### Best For

- Monolithic applications
- Early stage (< 10k users)
- Single deployment (admin UI only)
- Team familiar with session-based auth

---

## Option 3: Hybrid (JWT for Admin + API Keys for Chat)

### Architecture

**Pattern**: Two separate auth systems optimized for different use cases

**Admin UI**: JWT tokens (Option 1) for human users
**Chat API**: API keys (existing pattern) for programmatic access

**Why Separate**:
- Human users need interactive login → JWT
- Chat widgets need simple auth → API key
- Different security requirements
- Independent evolution

### Database Schema

```sql
-- JWT auth tables (from Option 1)
users, account_users, directory_permissions

-- API key tables (for chat API)
api_keys (
  id UUID PRIMARY KEY,
  account_id UUID REFERENCES accounts,
  key_hash TEXT NOT NULL,
  name VARCHAR,  -- "Widget Key", "Production Key"
  created_at TIMESTAMP,
  last_used_at TIMESTAMP
)
```

### Pros

✅ **Separation of Concerns**: Human auth vs service auth are different problems

✅ **Optimized for Each Use Case**: JWT for users, simple keys for services

✅ **Chat API Unchanged**: Existing clients continue working

✅ **Independent Evolution**: Can change admin auth without affecting chat API

✅ **Security Boundaries**: Compromise of one doesn't affect other

### Cons

⚠️ **Two Auth Systems**: More code to maintain (~600 lines total)

⚠️ **Account Sync**: User management affects both systems

⚠️ **More Complex**: Team needs to understand both patterns

⚠️ **Potential Confusion**: "Which auth do I use?" questions

### Implementation Effort

- Option 1 implementation (32 hours)
- API key system (already exists or 12 hours)
- Coordination logic (4 hours)

**Total**: ~36-48 hours (5-6 days)

### Best For

- Clear separation between user-facing and programmatic APIs
- Long-term architecture with multiple client types
- Team comfortable with complexity

---

## Comparison Matrix

| Factor | JWT (Option 1) | Session (Option 2) | Hybrid (Option 3) |
|--------|---------------|-------------------|-------------------|
| **Scalability** | ⭐⭐⭐⭐⭐ Stateless | ⭐⭐⭐ DB lookups | ⭐⭐⭐⭐⭐ Stateless (admin) |
| **Multi-App Support** | ⭐⭐⭐⭐⭐ Same tokens | ⭐⭐ Cookie sharing hard | ⭐⭐⭐⭐⭐ Best of both |
| **Implementation Time** | ⭐⭐⭐ 4 days | ⭐⭐⭐⭐ 3 days | ⭐⭐ 6 days |
| **Security** | ⭐⭐⭐⭐ Standard | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Layered |
| **Mobile Ready** | ⭐⭐⭐⭐⭐ Yes | ⭐⭐ Cookie issues | ⭐⭐⭐⭐⭐ JWT side ready |
| **Immediate Revocation** | ⭐⭐⭐ Need blacklist | ⭐⭐⭐⭐⭐ Delete row | ⭐⭐⭐⭐ Per system |
| **Performance** | ⭐⭐⭐⭐⭐ No DB lookup | ⭐⭐⭐ DB per request | ⭐⭐⭐⭐⭐ No DB (JWT) |
| **Simplicity** | ⭐⭐⭐⭐ Standard | ⭐⭐⭐⭐⭐ Simple | ⭐⭐ Complex |
| **Future-Proof** | ⭐⭐⭐⭐⭐ Industry std | ⭐⭐⭐ May need migration | ⭐⭐⭐⭐⭐ Flexible |

---

## Recommendation: JWT (Option 1)

### Why JWT

1. **Multi-App Future**: Admin UI is first, but you'll likely build more apps (mobile, analytics dashboard, etc.)

2. **Scalability**: Stateless auth means you can scale horizontally without session store complexity

3. **Standard Pattern**: JWT is industry standard for SaaS - easier hiring, more libraries, known security patterns

4. **Schema Customization**: Your requirement for account-specific schema customizations suggests this will grow into a complex platform. Start with scalable architecture.

5. **Your Team Size Will Grow**: When you hire more developers, JWT is more familiar than custom session systems

### Why Not Session

- Database lookup on every request becomes bottleneck at scale
- Multi-app sharing is painful (need Redis, cookie domain tricks)
- Not mobile-friendly (you mentioned this might become separate app)

### Why Not Hybrid (Yet)

- Adds complexity before you need it
- Can always add API keys to JWT system later
- JWT works for both humans and services (if needed)

### Implementation Roadmap

**Week 1**: Auth foundation
- Database schema (users, account_users, directory_permissions)
- JWT service (encode/decode, validation)
- Password hashing (bcrypt)

**Week 2**: Backend integration
- Auth endpoints (login, register, logout)
- JWT validation middleware
- Permission checking dependencies
- Admin API endpoints (from original design doc)

**Week 3**: Frontend
- Login/register pages
- Token storage (memory + HTTP-only cookie for refresh)
- API client with auto-retry on 401
- Directory admin UI (from original design doc)

**Week 4**: Polish
- Refresh token rotation
- Rate limiting
- Audit logging
- Security testing
- Documentation

---

## Next Steps

1. **Review & Approve**: Confirm JWT approach meets your needs
2. **Database Design**: Review schema in [Architecture Decision doc](directory-admin-architecture-decision.md)
3. **Create Epic**: Break down into tasks in project management
4. **Migration Plan**: Ensure backward compatibility with existing chat API

## References

- [Architecture Decision Record](directory-admin-architecture-decision.md) - Full architectural decisions
- [Original UI Design](directory-schema-administration-ui.md) - Frontend implementation
- [Multi-Tenant Security](../architecture/multi-tenant-security.md) - Platform-wide security discussion
