# Configuration Reference

## Overview

The system uses a two-tier YAML configuration approach:
- **Global configuration**: `backend/config/app.yaml` - Application-wide settings
- **Agent-specific configuration**: `backend/config/agent_configs/{agent_type}.yaml` - Agent behavior overrides

Agent-specific settings override global settings when both are present.

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
- **Override**: Can be overridden per agent via `context_management.max_history_messages`
- **Performance**: Higher values may slow page loads but provide more context

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

## Agent-Specific Configuration (`backend/config/agent_configs/{agent_type}.yaml`)

Agent configurations override global settings and define agent-specific behavior.

### Example: Simple Chat Agent (`simple_chat.yaml`)

```yaml
# Agent identification
agent_type: "simple_chat"
display_name: "Simple Chat Assistant"
description: "General-purpose conversational AI assistant"

# Model settings (overrides app.yaml defaults)
model_settings:
  model: "openai:gpt-4o"              # Override global model
  temperature: 0.3                    # Lower temperature for consistency
  max_tokens: 2000                    # Response length limit

# Context and memory management
context_management:
  max_history_messages: 50            # OVERRIDES app.yaml chat.history_limit
  context_window_tokens: 8000         # Token limit for conversation context
  
  # Conversation summarization
  summarization:
    enabled: true
    trigger_threshold: 10             # Summarize after N messages
    summary_length: 200               # Target summary length in words

# System prompts and personality
system_prompt: |
  You are a helpful AI assistant focused on providing clear, accurate, and concise responses.
  Always be professional yet friendly in your interactions.

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

### Configuration Hierarchy

When both global and agent-specific configurations exist:

1. **Agent config takes precedence** for overlapping settings
2. **Global config provides defaults** for missing agent settings
3. **Environment variables** override both YAML configurations

**Example hierarchy for chat history:**
```
Environment Variable: CHAT_HISTORY_LIMIT=75
├── Agent Config: context_management.max_history_messages: 50
├── Global Config: chat.history_limit: 50
└── Code Default: 20

Result: 75 (environment wins)
```

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
# backend/config/agent_configs/sales.yaml
context_management:
  max_history_messages: 100          # Sales agent uses 100 instead of 75
```

**Code usage:**
```python
# Automatic configuration loading in simple_chat.py
config = load_config()
chat_config = config.get("chat", {})
history_limit = chat_config.get("history_limit", 20)  # Fallback to 20
```

### Adding New Agent Types

1. **Create agent config**: `backend/config/agent_configs/my_agent.yaml`
2. **Set agent_type**: Must match filename (without .yaml)
3. **Override global settings**: Add agent-specific model, tools, etc.
4. **Implement agent class**: Reference config via `get_agent_config()`

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
