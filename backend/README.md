# Backend (FastAPI + Jinja + HTMX + SSE)

Structure created per memorybank/architecture/code-organization.md.
Populate templates in backend/templates/ and config in backend/config/.

## Development Environment

### Docker Development Setup (Recommended)

For Epic 0004 (Chat Memory & Persistence), use Docker for the complete development environment:

```bash
# Start all services (PostgreSQL, Redis, Adminer)
./scripts/dev-setup.sh

# Reset database with fresh data
./scripts/dev-reset.sh

# Stop all services
docker-compose -f docker-compose.dev.yml down
```

**Available Services:**
- PostgreSQL: `localhost:5432` (Database: `salient_dev`, User: `salient_user`)
- Redis: `localhost:6379`
- Adminer (DB Admin): `http://localhost:8080`

### Manual Backend Startup

Once Docker services are running, start the FastAPI backend:

#### Without auto-reload
```bash
uvicorn backend.app.main:app
```

#### With auto-reload (code only)
```bash
uvicorn backend.app.main:app --reload
```

#### With auto-reload including YAML config
```bash
uvicorn backend.app.main:app \
  --reload \
  --reload-dir backend/config \
  --reload-include '*.yaml' \
  --reload-include '*.yml'
```

## Environment Variables

Required environment variables (set in `.env` at repo root):

### Core Services
- `OPENROUTER_API_KEY` - For LLM streaming via OpenRouter
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

### Optional Services
- `MAILGUN_API_KEY` & `MAILGUN_DOMAIN` - For email functionality
- `PINECONE_API_KEY` & `OPENAI_API_KEY` - For future RAG features

### Development Settings
- `ENV=development` - Enables development features
- `DEBUG=true` - Enhanced logging and debugging

## Database Migrations (Epic 0004)

When Alembic is configured:

```bash
# Create a new migration
cd backend && alembic revision --autogenerate -m "Description"

# Apply migrations
cd backend && alembic upgrade head

# View migration history
cd backend && alembic history
```
