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

**Important**: Always use `.venv` at the project root.

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
source backend/venv/bin/activate      # ❌ Wrong - no venv here
uvicorn app.main:app --reload # ❌ Wrong module path
```

**Why this fails:**
- Wrong virtual environment (only `.venv` at project root exists)
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

3. **Import errors**: Make sure you're using the `.venv` at project root

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

## Configuration Management

### Agent Configuration Architecture

The backend uses a **hierarchical configuration cascade** that prioritizes agent-specific settings over global defaults:

```
Agent Config → Global Config (app.yaml) → Code Defaults
```

**Priority Order:**
1. **Agent-specific config**: `backend/config/agent_configs/{agent_type}/config.yaml` (Highest Priority)
2. **Global config**: `backend/config/app.yaml` (Middle Priority) 
3. **Code defaults**: Hardcoded fallback values (Lowest Priority)

### Agent Configuration Structure

Agent configurations are organized in dedicated folders under `backend/config/agent_configs/`:

```
backend/config/agent_configs/
└── simple_chat/
    ├── config.yaml          # Agent-specific configuration
    └── system_prompt.md     # External system prompt file
```

#### Agent Config Example (`simple_chat/config.yaml`)

```yaml
agent_type: "simple_chat"
name: "Simple Chat Agent"
description: "General-purpose conversational agent with RAG capabilities"

# System prompt configuration
prompts:
  system_prompt_file: "./system_prompt.md"  # External prompt file

model_settings:
  model: "openai:gpt-4o"  # Overrides global default
  temperature: 0.3
  max_tokens: 2000

# Standardized parameter names  
context_management:
  history_limit: 50        # Agent-specific override (was max_history_messages)
  context_window_tokens: 8000
  
tools:
  vector_search:
    enabled: true
    max_results: 5
  web_search:
    enabled: true
    provider: "exa"
```

#### System Prompt Files

System prompts are stored in separate `.md` files for better maintainability:

```markdown
<!-- simple_chat/system_prompt.md -->
You are a helpful AI assistant with access to knowledge base search and web search tools.
Always provide accurate, helpful responses with proper citations.

Guidelines:
- Use vector_search for stored knowledge queries
- Use web_search for current information
- Be conversational and helpful while remaining accurate
```

### Global Configuration (`app.yaml`)

Global configuration provides defaults for all agents:

```yaml
chat:
  history_limit: 50         # Global default (standardized parameter name)
  inactivity_minutes: 30

llm:
  provider: openrouter
  model: deepseek/deepseek-chat-v3.1  # Global default model
  temperature: 0.3
  max_tokens: 1024

agents:
  default_agent: simple_chat
  configs_directory: ./config/agent_configs/
```

### Configuration Cascade Examples

**Example 1: Agent Override**
- Agent config: `history_limit: 75`
- Global config: `history_limit: 50` 
- **Result**: Uses `75` (agent-specific value)

**Example 2: Global Fallback**
- Agent config: *(no history_limit specified)*
- Global config: `history_limit: 50`
- **Result**: Uses `50` (global default)

**Example 3: Code Fallback**
- Agent config: *(no history_limit specified)*
- Global config: *(no history_limit specified)*
- **Result**: Uses `50` (hardcoded fallback)

### Configuration Troubleshooting

**Common Issues:**

1. **Agent not using custom configuration:**
   - Verify agent folder exists: `backend/config/agent_configs/{agent_type}/`
   - Check `config.yaml` file syntax and indentation
   - Ensure parameter names use standardized conventions

2. **System prompt not loading:**
   - Check `prompts.system_prompt_file` path in agent config
   - Verify `.md` file exists and is readable
   - Paths are resolved relative to agent config directory

3. **Configuration cascade not working:**
   - Test configuration loading: `python -c "from app.agents.config_loader import get_agent_history_limit; import asyncio; print(asyncio.run(get_agent_history_limit('simple_chat')))"`
   - Check logs for `config_cascade_source` debug messages
   - Verify no typos in parameter names (use `history_limit`, not `max_history_messages`)

4. **Legacy parameter names:**
   - **DEPRECATED**: `max_history_messages` → **USE**: `history_limit`
   - Update all YAML files to use standardized parameter names
   - Run tests to verify parameter standardization: `pytest tests/unit/test_simple_chat_agent.py -v`

**Configuration Validation:**
```bash
# Test agent configuration loading
cd /path/to/salient02
source .venv/bin/activate
python -c "
import asyncio
from backend.app.agents.config_loader import get_agent_config, get_agent_history_limit

async def test_config():
    config = await get_agent_config('simple_chat')
    limit = await get_agent_history_limit('simple_chat')
    print(f'✅ Agent config loaded: {config.name}')
    print(f'✅ History limit: {limit}')
    print(f'✅ System prompt: {len(config.system_prompt)} chars')

asyncio.run(test_config())
"
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
