# Backend (FastAPI + Jinja + HTMX + SSE)

Structure created per memorybank/architecture/code-organization.md.
Populate templates in backend/templates/ and config in backend/config/.

## 🚀 Quick Start

**TL;DR: Always run from PROJECT ROOT, never from backend directory!**

```bash
# Navigate to project root
cd /path/to/salient02

# Activate virtual environment  
source .venv/bin/activate

# Start backend server
uvicorn backend.app.main:app --reload
```

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

The project uses a virtual environment at the **PROJECT ROOT** level:

```bash
# From project root (salient02/)
cd /path/to/salient02

# Create virtual environment at root level (if not exists)
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Important**: Use `.venv` at the project root, NOT `backend/venv`.

### Manual Backend Startup

**⚠️ IMPORTANT: Always start the backend from the PROJECT ROOT directory, NOT the backend directory!**

Once Docker services are running, start the FastAPI backend **FROM THE PROJECT ROOT**:

#### From Project Root (Correct Method)
```bash
# Navigate to project root (salient02/)
cd /path/to/salient02

# Activate the main virtual environment
source .venv/bin/activate

# Verify you're in the right place
ls -la | grep backend  # Should see backend/ directory
ls backend/app/        # Should see main.py

# Start the backend server
uvicorn backend.app.main:app --reload

# With config watching (optional)
uvicorn backend.app.main:app \
  --reload \
  --reload-include '*.py' \
  --reload-include 'backend/config/*.yaml'

# Production mode
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

#### Alternative: Python Module Syntax
```bash
# From project root with .venv activated
python -m uvicorn backend.app.main:app --reload
```

#### Quick One-liner (From Anywhere)
```bash
# Complete command from any directory
cd /path/to/salient02 && source .venv/bin/activate && uvicorn backend.app.main:app --reload
```

#### ❌ DO NOT Run From Backend Directory
```bash
# DON'T DO THIS - will cause ModuleNotFoundError:
cd backend                    # ❌ Wrong directory
source venv/bin/activate      # ❌ Wrong virtual environment
uvicorn app.main:app --reload # ❌ Wrong module path
```

**Why this fails:**
- Wrong virtual environment (`backend/venv` instead of `.venv` at root)
- Wrong module path (`app.main:app` instead of `backend.app.main:app`)  
- Wrong working directory for config file paths

### Troubleshooting

**Common Issues:**

1. **ModuleNotFoundError: No module named 'backend'**: 
   - **YOU'RE RUNNING FROM THE WRONG DIRECTORY!** 
   - Must be in project root `/path/to/salient02/` (should see `backend/` folder)
   - Use `uvicorn backend.app.main:app --reload` from project root
   
2. **ModuleNotFoundError: No module named 'app'**: 
   - You're using the wrong module path
   - From project root, use `backend.app.main:app` not `app.main:app`

3. **Import errors**: Make sure you're using the `.venv` at project root, not `backend/venv`

4. **Port already in use**: Add `--port 8001` or kill existing uvicorn processes

5. **Database connection errors**: Ensure Docker services are running (`docker-compose -f docker-compose.dev.yml up -d`)

**Directory Verification:**
```bash
# You should be here (PROJECT ROOT):
pwd
# Output: /path/to/salient02

# You should see these directories:
ls -la | grep -E "(backend|\.venv|requirements\.txt)"
# Output should show: backend/, .venv/, requirements.txt

# Verify logs directory is in the correct location:
ls backend/logs/
# Should show log files (not backend/backend/logs/)
```

**Module Path Verification:**
```bash
# From project root with .venv activated
python -c "import backend.app.main; print('✅ Correct module path')"
```

**Working Commands (From Project Root):**
```bash
# Method 1: Standard uvicorn (recommended)
uvicorn backend.app.main:app --reload

# Method 2: Python module syntax
python -m uvicorn backend.app.main:app --reload

# Method 3: One-liner from anywhere
cd /path/to/salient02 && source .venv/bin/activate && uvicorn backend.app.main:app --reload
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
# From project root, activate virtual environment
cd /path/to/salient02
source .venv/bin/activate

# Navigate to backend for alembic operations
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
cd /path/to/salient02
./scripts/dev-reset.sh
```
