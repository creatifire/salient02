# Installation Guide

## Prerequisites
- Python 3.13+ (or 3.9+)
- Docker & Docker Compose
- Node.js & pnpm (optional, for web frontend)

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd salient02
```

### 2. Setup Python Environment
```bash
# Create virtual environment at project root
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create `.env` file at project root:
```bash
# Required
OPENROUTER_API_KEY=your-key-here
DATABASE_URL=postgresql+asyncpg://salient_user:salient_pass@localhost:5432/salient_dev

# Optional (for vector search)
PINECONE_API_KEY_OPENTHOUGHT=your-key-here
OPENAI_API_KEY=your-key-here

# Optional (for Logfire observability)
LOGFIRE_TOKEN=your-token-here
```

### 4. Start Database Services
```bash
# Start PostgreSQL (removed Redis requirement)
docker-compose -f docker-compose.dev.yml up -d

# Verify services
docker-compose -f docker-compose.dev.yml ps
```

### 5. Database Setup
```bash
# Run migrations
cd backend
alembic upgrade head
cd ..

# Initialize accounts and agent instances
psql $DATABASE_URL -f backend/scripts/init_accounts_agents.sql

# Or using Python
python -c "import asyncio; from app.database import get_database_service; asyncio.run(get_database_service().execute_sql_file('backend/scripts/init_accounts_agents.sql'))"
```

### 6. Seed Directory Data (Optional)
```bash
# Example: Load Wyckoff doctors
python backend/scripts/seed_directory.py \
    --account wyckoff \
    --list doctors \
    --entry-type medical_professional \
    --csv backend/data/wyckoff/wyckoff_doctors_profiles.csv \
    --mapper medical_professional

# Example: Load Windriver doctors
python backend/scripts/seed_directory.py \
    --account windriver \
    --list doctors \
    --entry-type medical_professional \
    --csv backend/data/windriver/windriver_doctors_profiles.csv \
    --mapper medical_professional
```

### 7. Start Backend Server
```bash
# From project root (IMPORTANT: always run from root, not backend/)
uvicorn backend.app.main:app --reload

# Backend available at: http://localhost:8000
```

### 8. Start Web Frontend (Optional)
```bash
cd web
pnpm install
pnpm dev

# Frontend available at: http://localhost:4321
```

## Verification

### Test Backend
```bash
curl http://localhost:8000/api/health
```

### Test Agent Endpoint
```bash
curl -X POST http://localhost:8000/accounts/default_account/agents/simple_chat1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### Verify Database
```bash
# Check accounts
psql $DATABASE_URL -c "SELECT slug, name FROM accounts;"

# Check agent instances
psql $DATABASE_URL -c "SELECT ai.instance_slug, a.slug FROM agent_instances ai JOIN accounts a ON ai.account_id = a.id;"
```

## Quick Reset (Development)
```bash
# Reset database and reload all data
./scripts/dev-reset.sh
```

## Troubleshooting

**ModuleNotFoundError**: Ensure you're running from project root, not `backend/` directory.

**Database Connection Error**: Verify Docker services are running and `DATABASE_URL` is correct.

**Migration Errors**: Run `alembic upgrade head` from `backend/` directory.

**Port Already in Use**: Change port: `uvicorn backend.app.main:app --reload --port 8001`

