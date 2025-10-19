# Pinecone Multi-Project API Key Architecture

> **Last Updated**: October 19, 2025

## Problem

Each Pinecone project requires its own API key. Multi-tenant agents may use different Pinecone projects:
- Wyckoff agent → `openthought-dev` project → `wyckoff-poc-01` index
- AgroFresh agent → `Agrobot` project → `agrofresh01` index

Single global `PINECONE_API_KEY` causes 401 Unauthorized errors for agents in different projects.

## Solution

**Two-part architecture:**

1. **Per-Agent API Keys**: Each agent specifies its own API key via `api_key_env` in config
2. **Lazy Singleton Pattern**: Services initialize only when needed (not at module import)

## Configuration

### Agent Config (`config.yaml`)

```yaml
tools:
  vector_search:
    enabled: true
    pinecone:
      index_name: "wyckoff-poc-01"
      namespace: "__default__"
      api_key_env: "PINECONE_API_KEY_OPENTHOUGHT"  # Project-specific key
```

### Environment Variables (`.env`)

```bash
PINECONE_API_KEY_OPENTHOUGHT=<key-for-openthought-dev>
PINECONE_API_KEY_AGROBOT=<key-for-agrobot-project>
# No global PINECONE_API_KEY needed
```

## Implementation

### Flow

```
1. Agent config specifies api_key_env parameter
2. load_agent_pinecone_config() reads env var → AgentPineconeConfig
3. get_cached_pinecone_client() creates/reuses PineconeClient
   - Cache key: {api_key[:8]}_{index_name}
   - Agents with same project share client
4. VectorService receives agent-specific client
```

### Key Files

**`backend/app/services/agent_pinecone_config.py`:**
```python
# Load agent's Pinecone config from agent config.yaml
api_key_env = pinecone_config.get("api_key_env", "PINECONE_API_KEY")
api_key = os.getenv(api_key_env)

# Cache clients by API key + index
cache_key = f"{agent_config.api_key[:8]}_{agent_config.index_name}"
_pinecone_client_cache[cache_key] = PineconeClient.create_from_agent_config(agent_config)
```

**`backend/app/agents/tools/vector_tools.py`:**
```python
async def vector_search(ctx: RunContext[SessionDependencies], query: str) -> str:
    pinecone_config = load_agent_pinecone_config(agent_config)
    pinecone_client = get_cached_pinecone_client(pinecone_config)  # Cached!
    vector_service = VectorService(pinecone_client=pinecone_client)
```

### Lazy Singleton Pattern

**Problem**: Module-level singletons initialized at import time blocked agent-specific keys:
```python
# OLD (broken)
pinecone_client = PineconeClient()  # Required PINECONE_API_KEY at import
```

**Solution**: Lazy initialization:
```python
# NEW (working)
_pinecone_client: Optional[PineconeClient] = None

def get_default_pinecone_client() -> PineconeClient:
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient()
    return _pinecone_client
```

Applied to:
- `backend/app/services/pinecone_client.py`
- `backend/app/services/embedding_service.py`
- `backend/app/services/vector_service.py`

## Benefits

- ✅ Multi-tenant: Each agent uses its own Pinecone project
- ✅ Connection pooling: Pinecone client reuse per Pinecone best practices
- ✅ Isolation: Different projects can't access each other's indexes
- ✅ No global dependency: Agents work without global `PINECONE_API_KEY`
- ✅ Efficient caching: Agents in same project share client instance

## Cache Behavior

**First request per project:**
```
Creating new PineconeClient for cache_key: pcsk-123_wyckoff-poc-01
Cache size: 1
```

**Subsequent requests (same project):**
```
Reusing cached PineconeClient for: pcsk-123_wyckoff-poc-01
```

**Different project:**
```
Creating new PineconeClient for cache_key: pcsk-456_agrofresh01
Cache size: 2
```

## Related

- Bug report: [bugs-0017.md](../project-management/bugs-0017.md#bug-0017-006)
- Implementation: [0000-approach-milestone-01.md](../project-management/0000-approach-milestone-01.md) Priority 3
- Commits: `3186ef5` (config), `30b50b9` (caching), `9984e99` (lazy init)

