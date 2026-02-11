# Container Deployment Architecture for Render.com

## Context

Deploying directory admin UI and chat API as separate Docker containers on render.com with shared PostgreSQL database. Local demo sites (Astro) remain development-only and won't be deployed to production.

## Render.com Deployment Model

**Key Features**:
- Monorepo support with per-service root directories
- Docker-based deploys from Dockerfiles
- Blueprint (render.yaml) for infrastructure-as-code
- Shared PostgreSQL database across services
- Private networking between services (internal hostnames)
- Connection pooling via PgBouncer for high-traffic

**Architecture Pattern**:
```
render.yaml (Blueprint)
├── Chat API (Docker container)
├── Admin API (Docker container)  
├── Admin UI (Docker container or Static Site)
└── PostgreSQL Database (shared)
```

## Code Organization Options

### Option 1: Monorepo with Service Subdirectories (Recommended)

**Structure**:
```
salient02/
├── services/
│   ├── chat-api/                    # Chat API service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py                  # Entry point
│   │   └── app/                     # Symlink to ../../backend/app
│   │
│   ├── admin-api/                   # Admin API service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py                  # Entry point
│   │   └── app/                     # Symlink to ../../backend/app
│   │
│   └── admin-ui/                    # Admin UI service
│       ├── Dockerfile
│       ├── package.json
│       ├── astro.config.mjs
│       └── src/                     # Admin-specific pages/components
│
├── backend/                         # Shared backend code
│   ├── app/
│   │   ├── api/                     # API endpoints
│   │   ├── auth/                    # Auth module
│   │   ├── models/                  # SQLAlchemy models
│   │   ├── services/                # Business logic
│   │   └── ...
│   ├── migrations/                  # Alembic migrations
│   └── config/
│       └── directory_schemas/       # YAML schemas
│
├── web/                             # Demo sites (local dev only)
│   └── src/
│       └── pages/
│           └── chat/                # Demo chat interface
│
├── render.yaml                      # Render blueprint
├── docker-compose.yml               # Local development
└── memorybank/                      # Documentation
```

**How It Works**:
- Each service has its own Dockerfile and dependencies
- Shared code in `backend/` is accessed via symlinks or COPY in Docker
- Render deploys each service independently from monorepo
- Services connect to shared PostgreSQL database via environment variables

**Pros**:
✅ Clean separation - each service is independently deployable
✅ Shared code stays DRY (single source of truth in `backend/`)
✅ Easy to split into polyrepo later (just copy service folder)
✅ Render.com monorepo support handles this pattern natively
✅ Local development stays simple (docker-compose)
✅ Clear ownership boundaries (different teams can own services)

**Cons**:
⚠️ Need symlinks or Docker COPY from parent directories
⚠️ Requires render.yaml root directory config per service

**Render Blueprint**:
```yaml
services:
  - type: web
    name: chat-api
    runtime: docker
    rootDir: services/chat-api
    dockerfilePath: ./Dockerfile
    dockerContext: ../../
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: salient-db
          property: connectionString
      - key: PYTHON_ENV
        value: production

  - type: web
    name: admin-api
    runtime: docker
    rootDir: services/admin-api
    dockerfilePath: ./Dockerfile
    dockerContext: ../../
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: salient-db
          property: connectionString
      - key: JWT_SECRET
        generateValue: true

  - type: web
    name: admin-ui
    runtime: docker
    rootDir: services/admin-ui
    dockerfilePath: ./Dockerfile
    envVars:
      - key: ADMIN_API_URL
        fromService:
          name: admin-api
          type: web
          property: host

databases:
  - name: salient-db
    databaseName: salient_production
    plan: starter
```

---

### Option 2: Monorepo with Workspace Root Dockerfiles

**Structure**:
```
salient02/
├── backend/
│   ├── chat_api/                    # Chat API app
│   │   └── main.py
│   ├── admin_api/                   # Admin API app
│   │   └── main.py
│   ├── app/                         # Shared code
│   │   ├── api/, auth/, models/, services/
│   └── migrations/
│
├── frontend/
│   └── admin-ui/                    # Admin UI (React/Astro)
│       └── src/
│
├── web/                             # Demo sites (local only)
│
├── docker/                          # Dockerfiles
│   ├── chat-api.Dockerfile
│   ├── admin-api.Dockerfile
│   └── admin-ui.Dockerfile
│
├── render.yaml
└── docker-compose.yml
```

**How It Works**:
- All Dockerfiles at repo root or in `docker/` folder
- Each Dockerfile builds from repo root (access to all shared code)
- Render uses different Dockerfile paths for each service

**Pros**:
✅ Simpler Docker builds (no symlinks needed)
✅ All Dockerfiles in one place
✅ Less directory nesting

**Cons**:
❌ Harder to extract service to separate repo later
❌ Less clear ownership boundaries
❌ All services share same dependencies in images (bloat)

**Render Blueprint**:
```yaml
services:
  - type: web
    name: chat-api
    runtime: docker
    dockerfilePath: ./docker/chat-api.Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: salient-db
          property: connectionString

  - type: web
    name: admin-api
    runtime: docker
    dockerfilePath: ./docker/admin-api.Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: salient-db
          property: connectionString
```

---

### Option 3: Hybrid Monorepo (Best for Gradual Migration)

**Structure**:
```
salient02/
├── backend/                         # Existing structure (unchanged)
│   ├── app/
│   │   ├── main.py                  # Chat API entry point
│   │   └── ...
│   └── migrations/
│
├── admin/                           # New admin system
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── main.py                  # Admin API entry point
│   │
│   └── frontend/
│       ├── Dockerfile
│       ├── package.json
│       └── src/                     # Admin UI
│
├── web/                             # Demo sites (local only)
├── Dockerfile.chat-api              # Chat API container
├── render.yaml
└── docker-compose.yml
```

**How It Works**:
- Existing chat API stays in `backend/` (minimal changes)
- New admin system in separate `admin/` folder
- Shared code (models, migrations) accessed from both

**Pros**:
✅ Non-disruptive to existing chat API
✅ Clear separation between old and new systems
✅ Admin can be extracted to separate repo easily
✅ Gradual migration path

**Cons**:
⚠️ Some code duplication (or need shared package)
⚠️ Two different organizational patterns in one repo
⚠️ Migrations need coordination

---

## Recommendation: Option 1 (Service Subdirectories)

### Why Option 1

1. **Production-Ready**: Clear service boundaries from day one
2. **Render.com Native**: Matches their monorepo best practices
3. **Easy Split**: Can extract to polyrepo without refactoring
4. **Independent Scaling**: Each service has own dependencies
5. **Clear Ownership**: Teams can own specific services

### Implementation Details

#### Directory Structure
```
salient02/
├── services/
│   ├── chat-api/
│   │   ├── Dockerfile
│   │   ├── requirements.txt         # Only chat API deps
│   │   ├── main.py
│   │   └── app -> ../../backend/app # Symlink to shared code
│   │
│   ├── admin-api/
│   │   ├── Dockerfile
│   │   ├── requirements.txt         # Admin API + auth deps
│   │   ├── main.py
│   │   └── app -> ../../backend/app # Symlink to shared code
│   │
│   └── admin-ui/
│       ├── Dockerfile
│       ├── package.json
│       ├── astro.config.mjs
│       ├── tsconfig.json
│       └── src/
│           ├── pages/
│           │   ├── login.astro
│           │   ├── index.astro
│           │   └── directories.astro
│           ├── components/
│           │   └── admin/
│           └── lib/
│               └── api-client.ts
│
├── backend/                         # Shared backend code
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── auth/                    # NEW: Auth module
│   │   ├── models/                  # Shared models
│   │   ├── services/                # Shared services
│   │   └── config.py
│   ├── migrations/                  # Shared migrations
│   │   └── versions/
│   └── config/
│       └── directory_schemas/
│
├── web/                             # Demo sites (local dev only)
│   └── src/
│       └── pages/
│           └── chat/
│
├── render.yaml                      # Render blueprint
├── docker-compose.dev.yml           # Local development
└── .dockerignore
```

#### Dockerfile Examples

**Chat API** (`services/chat-api/Dockerfile`):
```dockerfile
FROM python:3.14-slim

WORKDIR /app

# Copy shared backend code
COPY backend/ /app/backend/

# Copy service-specific files
COPY services/chat-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/chat-api/main.py .

# Run migrations on startup (or use separate job)
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
```

**Admin API** (`services/admin-api/Dockerfile`):
```dockerfile
FROM python:3.14-slim

WORKDIR /app

# Copy shared backend code
COPY backend/ /app/backend/

# Copy service-specific files
COPY services/admin-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/admin-api/main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Admin UI** (`services/admin-ui/Dockerfile`):
```dockerfile
FROM node:20-slim AS builder

WORKDIR /app

COPY services/admin-ui/package*.json ./
RUN npm ci

COPY services/admin-ui/ .
RUN npm run build

# Production image
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY services/admin-ui/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Service Entry Points

**Chat API** (`services/chat-api/main.py`):
```python
import sys
sys.path.insert(0, '/app/backend')

from app.main import app as chat_app

app = chat_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Admin API** (`services/admin-api/main.py`):
```python
import sys
sys.path.insert(0, '/app/backend')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import shared modules
from app.auth.routers import auth_router
from app.database import get_database_service

app = FastAPI(title="Salient Admin API")

# CORS for admin UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin.salient.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
# ... other admin routers

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Render Blueprint (render.yaml)

```yaml
services:
  # Chat API - existing functionality
  - type: web
    name: salient-chat-api
    runtime: docker
    rootDir: services/chat-api
    dockerfilePath: ./Dockerfile
    dockerContext: ../../
    plan: starter
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: salient-db
          property: connectionString
      - key: PYTHON_ENV
        value: production
      - key: LOG_LEVEL
        value: info
    
  # Admin API - new JWT-based admin backend
  - type: web
    name: salient-admin-api
    runtime: docker
    rootDir: services/admin-api
    dockerfilePath: ./Dockerfile
    dockerContext: ../../
    plan: starter
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: salient-db
          property: connectionString
      - key: JWT_SECRET
        generateValue: true
      - key: JWT_ALGORITHM
        value: HS256
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: 15
      - key: REFRESH_TOKEN_EXPIRE_DAYS
        value: 7
      - key: PYTHON_ENV
        value: production
  
  # Admin UI - React/Astro frontend
  - type: web
    name: salient-admin-ui
    runtime: docker
    rootDir: services/admin-ui
    dockerfilePath: ./Dockerfile
    plan: starter
    envVars:
      - key: PUBLIC_ADMIN_API_URL
        fromService:
          name: salient-admin-api
          type: web
          property: host
      - key: PUBLIC_ENV
        value: production

databases:
  - name: salient-db
    databaseName: salient_production
    plan: starter
    ipAllowList: []  # Private network only
```

#### Local Development (docker-compose.dev.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: salient_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  chat-api:
    build:
      context: .
      dockerfile: services/chat-api/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/salient_dev
      PYTHON_ENV: development
    volumes:
      - ./backend:/app/backend
      - ./services/chat-api:/app/services/chat-api
    depends_on:
      - postgres

  admin-api:
    build:
      context: .
      dockerfile: services/admin-api/Dockerfile
    ports:
      - "8001:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/salient_dev
      JWT_SECRET: dev-secret-key-change-in-production
      JWT_ALGORITHM: HS256
      PYTHON_ENV: development
    volumes:
      - ./backend:/app/backend
      - ./services/admin-api:/app/services/admin-api
    depends_on:
      - postgres

  admin-ui:
    build:
      context: .
      dockerfile: services/admin-ui/Dockerfile
    ports:
      - "4321:80"
    environment:
      PUBLIC_ADMIN_API_URL: http://localhost:8001
    depends_on:
      - admin-api

volumes:
  postgres_data:
```

## Migration Path

### Phase 1: Restructure (Week 1)
- [ ] Create `services/` directory structure
- [ ] Move existing `backend/app/main.py` to `services/chat-api/`
- [ ] Create `services/admin-api/` skeleton
- [ ] Create `services/admin-ui/` skeleton
- [ ] Update docker-compose.dev.yml
- [ ] Test local development setup

### Phase 2: Chat API Container (Week 1)
- [ ] Create `services/chat-api/Dockerfile`
- [ ] Create `services/chat-api/requirements.txt`
- [ ] Test chat API container locally
- [ ] Deploy to Render.com as single service
- [ ] Verify existing clients still work

### Phase 3: Admin API Container (Week 2-3)
- [ ] Implement auth module in `backend/app/auth/`
- [ ] Create `services/admin-api/Dockerfile`
- [ ] Create admin API entry point
- [ ] Test locally with docker-compose
- [ ] Deploy to Render.com
- [ ] Test private network connectivity

### Phase 4: Admin UI Container (Week 3-4)
- [ ] Build admin UI in `services/admin-ui/`
- [ ] Create production Dockerfile with nginx
- [ ] Test locally
- [ ] Deploy to Render.com
- [ ] Configure domain and SSL

### Phase 5: Blueprint & Automation (Week 4)
- [ ] Create complete `render.yaml`
- [ ] Test blueprint deployment
- [ ] Set up environment variable management
- [ ] Configure build filters for monorepo
- [ ] Document deployment process

## Render.com Best Practices

### Monorepo Build Filters
```yaml
services:
  - type: web
    name: chat-api
    rootDir: services/chat-api
    buildFilter:
      paths:
        - services/chat-api/**
        - backend/**  # Rebuild if shared code changes
        - migrations/**
```

### Environment Variable Management
- Use `generateValue: true` for secrets (JWT_SECRET)
- Use `fromDatabase` for database URLs
- Use `fromService` for service-to-service URLs
- Use Render's Environment Groups for shared config

### Private Networking
- Services in same region use internal hostnames
- Format: `{service-name}:10000` (Render internal port)
- No public internet traffic for service-to-service calls
- Database connections use private network

### Connection Pooling
For high traffic, add PgBouncer:
```yaml
services:
  - type: pserv
    name: pgbouncer
    runtime: docker
    dockerfilePath: ./docker/pgbouncer.Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: salient-db
          property: connectionString
```

## Deployment Workflow

### Development
```bash
# Terminal 1: Run all services
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Run migrations
docker-compose exec chat-api alembic upgrade head

# Access services:
# - Chat API: http://localhost:8000
# - Admin API: http://localhost:8001
# - Admin UI: http://localhost:4321
```

### Production (Render.com)
```bash
# Deploy via Blueprint
git push origin main

# Render automatically:
# 1. Detects changes via build filters
# 2. Builds affected Docker containers
# 3. Runs health checks
# 4. Switches traffic to new containers
# 5. Keeps old containers during rollout
```

### Manual Deployment
```bash
# Via Render CLI
render services deploy salient-chat-api
render services deploy salient-admin-api
render services deploy salient-admin-ui
```

## Cost Optimization on Render

### Instance Sizing
- **Starter Plan**: $7/month per service (512MB RAM, 0.5 CPU)
- **Standard Plan**: $25/month per service (2GB RAM, 1 CPU)
- **Pro Plan**: $85/month per service (4GB RAM, 2 CPU)

### Recommended Starting Point
- Chat API: Standard (handles concurrent requests)
- Admin API: Starter (lower traffic)
- Admin UI: Static Site ($0, if using static build)
- Database: Starter ($7/month, 1GB storage)

**Total**: ~$46/month (2 APIs + DB) or ~$21/month (if admin UI is static)

### Scale-Up Triggers
- Chat API: > 100 concurrent users → Standard plan
- Admin API: > 50 admin users → Standard plan
- Database: > 500MB data → upgrade storage

## Security Considerations

### Container Isolation
- Each service runs in isolated container
- No shared filesystem between services
- Services communicate via network only

### Secrets Management
- Never commit secrets to render.yaml
- Use `generateValue: true` for auto-generated secrets
- Use Render's secret management for manual secrets
- Rotate secrets via Render dashboard

### Database Security
- Database on private network only
- No public IP (use `ipAllowList: []`)
- Connection pooling reduces attack surface
- Automated backups (daily on Starter+)

## Troubleshooting

### Build Failures
- Check Dockerfile paths relative to rootDir
- Verify dockerContext includes all necessary files
- Check build logs in Render dashboard

### Service Communication
- Verify services in same region
- Use internal hostnames (not public URLs)
- Check environment variables are set correctly

### Database Connections
- Check connection string format
- Verify connection pool settings
- Monitor connection count in dashboard

## References

- [Render Monorepo Support](https://render.com/docs/monorepo-support)
- [Render Docker Docs](https://render.com/docs/docker)
- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [Shared Database Pattern](https://render.com/articles/connecting-multiple-services-to-a-shared-database)
