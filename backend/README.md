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

### Virtual Environment Setup

Before starting the backend, ensure you have a Python virtual environment:

```bash
# Create virtual environment (if not exists)
cd backend
python -m venv venv

# Install dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### Manual Backend Startup

Once Docker services are running, start the FastAPI backend:

#### From Backend Directory (Recommended)
```bash
# IMPORTANT: Navigate to the backend directory (not backend/backend!)
# From project root:
cd backend
source venv/bin/activate

# Verify you're in the right place (should see 'app' directory)
ls -la | grep app

# Start with auto-reload (basic)
uvicorn app.main:app --reload

# With YAML config auto-reload (watches config changes)
uvicorn app.main:app \
  --reload \
  --reload-dir . \
  --reload-include '*.py' \
  --reload-include 'config/*.yaml' \
  --reload-include 'config/*.yml'

# Production mode (no auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Alternative: One-liner from Project Root
```bash
# Start backend from project root directory
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

#### Quick Development Restart
```bash
# If already in backend directory with venv activated
uvicorn app.main:app --reload
```

### Troubleshooting

**Common Issues:**

1. **ModuleNotFoundError: No module named 'app'**: 
   - You're in the wrong directory! 
   - Make sure you're in `/salient02/backend/` (should see `app` folder)
   - NOT in `/salient02/backend/backend/`
   
2. **Import errors**: Make sure you're in the `backend` directory and virtual environment is activated

3. **Config reload errors**: Use `--reload-dir .` instead of `--reload-dir config` 

4. **Port already in use**: Add `--port 8001` or kill existing uvicorn processes

5. **Database connection errors**: Ensure Docker services are running (`docker-compose -f docker-compose.dev.yml up -d`)

**Directory Verification:**
```bash
# You should be here:
pwd
# Output: /path/to/salient02/backend

# You should see these directories:
ls -la | grep -E "(app|config|venv)"
# Output should show: app, config, venv directories
```

**Quick Health Check:**
```bash
cd backend && source venv/bin/activate && python -c "import app.main; print('✅ Backend ready')"
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

Alembic is configured for database schema management:

```bash
# Activate virtual environment first
source backend/venv/bin/activate

# From project root
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# View migration history
alembic history

# Check current migration status
alembic current
```

### Quick Database Reset
```bash
# Reset database to clean state (from project root)
./scripts/dev-reset.sh
```
