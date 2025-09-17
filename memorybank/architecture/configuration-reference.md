# Configuration Reference

## Overview

The system uses an **agent-first configuration cascade** with YAML files:
- **Agent-specific configuration**: `backend/config/agent_configs/{agent_type}/config.yaml` - **Highest Priority**
- **Global configuration**: `backend/config/app.yaml` - **Fallback for missing agent settings**
- **Code constants**: **Last resort** (e.g., `history_limit: 50`)

**NEW**: Agent configurations now support:
- **Folder structure**: `simple_chat/config.yaml` + `simple_chat/system_prompt.md`
- **External system prompts**: Separated into `.md` files for better editing
- **Standardized parameter names**: `history_limit` (not `max_history_messages`)

---

## Global Configuration (`backend/config/app.yaml`)

### Core Application Settings

```yaml
# Application metadata
app:
  name: "SalesBot Backend"
  version: "1.0.0"
  debug: false                        # Enable debug mode (development only)

# Large Language Model configuration
llm:
  provider: "openrouter"              # openrouter (primary)
  model: "deepseek/deepseek-chat-v3.1" # Default model for legacy endpoints
  api_key: "${OPENROUTER_API_KEY}"    # Environment variable reference
  temperature: 0.7                    # Default creativity/randomness (0.0-1.0)
  max_tokens: 2000                    # Default response length limit
  timeout_seconds: 30                 # Request timeout
```

### Chat Configuration

```yaml
chat:
  inactivity_minutes: 30              # Session timeout after inactivity
  history_limit: 50                   # Maximum messages to load from history (NEW)
  input:
    debounce_ms: 1000                 # Input debounce delay
    submit_shortcut: "ctrl+enter"     # Keyboard shortcut for message submission
    enter_inserts_newline: true       # Whether Enter key inserts newline vs submits
```

**New Attribute: `history_limit`**
- **Purpose**: Controls how many recent messages are loaded from the database for chat history display
- **Default**: 50 messages
- **Override**: Can be overridden per agent via `context_management.history_limit` (STANDARDIZED)
- **Performance**: Higher values may slow page loads but provide more context
- **Cascade**: Agent config takes priority over global config

### Session Management

```yaml
session:
  cookie_name: "salient_session"      # Session cookie identifier
  cookie_max_age: 604800              # Cookie lifetime (7 days in seconds)
  cookie_secure: false                # HTTPS only (true in production)
  cookie_httponly: true               # Prevent JavaScript access
  cookie_samesite: "none"             # Cross-origin policy ("strict", "lax", "none")
  cookie_domain: "localhost"          # Cookie domain (for development)
  inactivity_minutes: 30              # Session inactivity timeout
  production_cross_origin: true       # Enable cross-origin in production
```

### Legacy Endpoint Configuration

```yaml
legacy:
  enabled: true                       # Toggle legacy endpoints on/off
  endpoints:
    chat: "/chat"                     # Legacy chat endpoint
    stream: "/events/stream"          # Legacy Server-Sent Events endpoint
    main: "/"                         # Main chat interface endpoint
```

### Database Configuration

```yaml
database:
  url: "${DATABASE_URL}"              # PostgreSQL connection string
  pool_size: 10                       # Connection pool size
  max_overflow: 20                    # Additional connections beyond pool
  echo: false                         # Log SQL queries (development)
  
  # Connection retry settings
  retry_attempts: 3
  retry_delay_seconds: 1
```

### Vector Database Configuration

```yaml
vector_database:
  provider: "pinecone"                # pinecone | pgvector
  
  # Pinecone settings
  pinecone:
    api_key: "${PINECONE_API_KEY}"
    environment: "us-west1-gcp"
    index_name: "salient-content"
    namespace: "default"              # Namespace for content isolation
    
  # Future: pgvector settings
  # pgvector:
  #   dimensions: 1536
  #   similarity_function: "cosine"
```

### Logging Configuration

```yaml
logging:
  level: "INFO"                       # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "json"                      # json | text
  file_path: "backend/logs/app.log"   # Log file location
  rotation: "1 day"                   # Log rotation interval
  retention: "30 days"                # Log retention period
  
  # Component-specific logging levels
  components:
    agents: "INFO"
    database: "WARNING"
    llm_requests: "INFO"
```

---

## Agent-Specific Configuration (`backend/config/agent_configs/{agent_type}/config.yaml`)

Agent configurations override global settings and define agent-specific behavior using the **agent-first cascade**.

### Example: Simple Chat Agent (`simple_chat/config.yaml`)

```yaml
# Agent identification
agent_type: "simple_chat"
name: "Simple Chat Assistant"
description: "General-purpose conversational AI assistant"

# System prompt configuration (NEW)
prompts:
  system_prompt_file: "./system_prompt.md"  # External prompt file

# Model settings (overrides app.yaml defaults)
model_settings:
  model: "moonshotai/kimi-k2-0905"    # Override global model
  temperature: 0.3                    # Lower temperature for consistency
  max_tokens: 2000                    # Response length limit

# Context and memory management
context_management:
  history_limit: 50                   # STANDARDIZED: Overrides app.yaml chat.history_limit
  context_window_tokens: 8000         # Token limit for conversation context
  
  # Conversation summarization
  summarization:
    enabled: true
    trigger_threshold: 10             # Summarize after N messages
    summary_length: 200               # Target summary length in words

# Tool configurations
tools:
  vector_search:
    enabled: true
    max_results: 5
    relevance_threshold: 0.7
    
  web_search:
    enabled: false                    # Disabled for simple chat
    
  conversation_management:
    enabled: true
    auto_summarize_threshold: 10
```

### Configuration Cascade (Agent-First Priority)

**Cascade Order**: Agent Config → Global Config → Code Fallback

1. **Agent-specific config** (`simple_chat/config.yaml`) - **Highest Priority**
2. **Global config** (`app.yaml`) - **Fallback for missing agent settings**  
3. **Code constants** - **Last resort** (e.g., `history_limit: 50`)

**Example cascade for `history_limit`:**
```
Agent Config: context_management.history_limit: 75     ← WINS (Highest Priority)
Global Config: chat.history_limit: 50                  ← Ignored when agent config present
Code Fallback: 50                                      ← Used only when both configs missing

Result: 75 (agent config wins)
```

**Implementation:**
- `get_agent_history_limit("simple_chat")` function implements cascade logic
- Comprehensive logging shows which config source was used
- Graceful fallback for corrupted/missing configuration files

---

## Configuration Loading Process

### Startup Sequence

1. **Load global config** from `backend/config/app.yaml`
2. **Apply environment overrides** using `${VAR_NAME}` syntax
3. **Scan agent configs** from `backend/config/agent_configs/`
4. **Merge configurations** per agent instance
5. **Validate required settings** and fail fast on errors

### Environment Variable Overrides

```bash
# Override global settings
export LLM_TEMPERATURE=0.5
export CHAT_HISTORY_LIMIT=100

# Override agent settings (format: AGENT_TYPE_SETTING_PATH)
export SIMPLE_CHAT_MAX_HISTORY_MESSAGES=75
export SALES_AGENT_TEMPERATURE=0.2
```

### Hot Reloading

- **Development**: Configuration changes reload automatically via `--reload-include "config/*.yaml"`
- **Production**: Requires application restart for security

---

## Usage Examples

### Configuring Chat History Limits

**Global default (affects all agents):**
```yaml
# backend/config/app.yaml
chat:
  history_limit: 75                   # All agents use 75 unless overridden
```

**Agent-specific override:**
```yaml
# backend/config/agent_configs/sales/config.yaml
context_management:
  history_limit: 100                 # STANDARDIZED: Sales agent uses 100 instead of 75
```

**Code usage:**
```python
# Agent-first cascade implementation
from app.agents.config_loader import get_agent_history_limit

# This function implements the full cascade: agent → global → fallback (50)
history_limit = await get_agent_history_limit("simple_chat")
```

### Adding New Agent Types

1. **Create agent folder**: `backend/config/agent_configs/my_agent/`
2. **Create config file**: `my_agent/config.yaml` with `agent_type: "my_agent"`
3. **Create system prompt**: `my_agent/system_prompt.md` with agent personality
4. **Reference prompt**: Set `prompts.system_prompt_file: "./system_prompt.md"` in config
5. **Override global settings**: Add agent-specific model, tools, etc.
6. **Implement agent class**: Reference config via `get_agent_config("my_agent")`

---

## Migration Notes

### Phase 1-2: File-Based Configuration
- Current implementation using YAML files
- Simple single-account, single-instance setup
- Direct file system access for configuration loading

### Phase 3+: Database Configuration Migration
- Configurations will move to database tables
- Agent templates (`agent_templates`) + account instances (`agent_instances`)
- Hot-reload via Redis caching with explicit invalidation
- Backward compatibility maintained during transition

---

## Related Documentation

- **[Agent Configuration](./agent-configuration.md)** - Detailed agent config schemas
- **[Code Organization](./code-organization.md)** - File structure and loading patterns
- **[Multi-Account Support](./multi-account-support.md)** - Future database-backed configuration
