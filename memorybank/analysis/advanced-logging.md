<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Advanced Logging Analysis

> Analysis of local logging observability options for RAG chat application development

## Current State
- **Existing**: Loguru-based logging to files/console  
- **Context**: Local development environment
- **Goal**: Enhanced log analysis and observability

## Options Evaluated

### 1. Status Quo (Do Nothing)
- **Pros**: Zero complexity, fast startup, adequate for basic debugging
- **Cons**: Limited analysis capabilities, no visualizations, manual correlation
- **Best for**: Simple applications, individual developers

### 2. InfluxDB + Grafana (Proposed)
- **Pros**: Excellent time-series analysis, beautiful dashboards, performance correlation
- **Cons**: High resource usage (~1-2GB RAM), complex setup, InfluxDB learning curve
- **Best for**: Performance monitoring, teams familiar with time-series DBs

### 3. Elasticsearch + Kibana (ELK)
- **Pros**: Excellent full-text search, purpose-built for logs, industry standard
- **Cons**: Very resource intensive, complex setup, unstable in low-resource environments
- **Best for**: Heavy log analysis, debugging complex issues

### 4. Prometheus + Grafana
- **Pros**: Excellent for metrics, industry standard, good alerting
- **Cons**: Not designed for log analysis, requires code instrumentation
- **Best for**: Application performance monitoring, SRE practices

### 5. Enhanced Structured Logging
- **Pros**: Minimal overhead, JSON output, command-line analysis tools
- **Cons**: Limited visualization, manual analysis, no real-time dashboards
- **Best for**: Developers preferring CLI tools, minimal overhead needs

### 6. Hybrid Lightweight
- **Pros**: Low resource usage, custom-built, incremental evolution
- **Cons**: Development time investment, limited features, maintenance responsibility
- **Best for**: Learning exercise, specific custom needs

## High Value Use Cases for Enhanced Logging
- Vector search performance analysis (query times, relevance scores)
- RAG pipeline debugging (retrieval → generation correlation)  
- Agent tool usage patterns
- Session/conversation flow analysis
- Error correlation across vector DB, LLM, and chat components

## Recommendation: Graduated Approach

### Phase 1: Enhanced Structured Logging (Now)
- Add structured JSON logging to current Loguru setup
- Include performance metrics in logs (response times, vector scores)
- Create simple analysis scripts using jq/ripgrep
- **Investment**: ~1 day setup
- **Benefits**: Better debugging without resource overhead

#### Implementation Example

**Where**: Enhance existing Loguru configuration in key service files:

- **`backend/app/services/vector_service.py`** - Vector search performance
  - `query_similar()`: Log query text, embedding time, search time, result count, top similarity score
  - `upsert_document()`: Log document ID, embedding generation time, upsert success/failure
  - `get_document()`: Log document ID, retrieval time, found/not found status

- **`backend/app/agents/`** - Agent tool usage and performance  
  - Agent tool calls: Log tool name, execution time, success/failure, input/output sizes
  - Agent responses: Log response generation time, token count, structured output validation
  - Context switching: Log when agent switches between tools or conversation modes

- **`backend/app/main.py`** - Request/response timing
  - FastAPI endpoints: Log request path, method, response time, status code, session ID
  - SSE streaming: Log stream start/end, message count, total stream duration
  - Error handling: Log unhandled exceptions with request context

- **`backend/app/services/message_service.py`** - Chat flow tracking
  - `create_message()`: Log message creation, conversation ID, message type, length
  - `get_conversation_history()`: Log history retrieval time, message count, session context
  - Session management: Log session creation, resumption, conversation continuity events

**Enhanced Logging Format**:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "component": "vector_service",
  "event": "vector_query_completed",
  "session_id": "sess_123",
  "conversation_id": "conv_456", 
  "query_text": "What are the product features?",
  "metrics": {
    "query_time_ms": 245,
    "embedding_time_ms": 89,
    "vector_search_time_ms": 156,
    "results_count": 3,
    "top_similarity_score": 0.87,
    "namespace": "development"
  },
  "context": {
    "agent_type": "simple_chat",
    "tool_name": "vector_search",
    "vector_threshold": 0.7
  }
}
```

**Simple Analysis Examples**:
```bash
# Find slow vector queries (>500ms)
cat logs/app.log | jq 'select(.event == "vector_query_completed" and .metrics.query_time_ms > 500)'

# Average response times by component
cat logs/app.log | jq -r 'select(.metrics.query_time_ms) | "\(.component) \(.metrics.query_time_ms)"' | awk '{sum[$1]+=$2; count[$1]++} END {for(c in sum) print c, sum[c]/count[c]}'

# Top failing queries
cat logs/app.log | jq -r 'select(.level == "ERROR" and .component == "vector_service") | .query_text' | sort | uniq -c | sort -nr
```

**Loguru Configuration** (`backend/app/config.py`):
```python
import json
from loguru import logger

def structured_log_formatter(record):
    """Enhanced structured logging format"""
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "component": record.get("extra", {}).get("component", "unknown"),
        "message": record["message"]
    }
    
    # Add structured fields if present
    extra = record.get("extra", {})
    if "event" in extra:
        log_entry["event"] = extra["event"]
    if "metrics" in extra:
        log_entry["metrics"] = extra["metrics"]
    if "context" in extra:
        log_entry["context"] = extra["context"]
        
    return json.dumps(log_entry)

# Configure structured logging for development
logger.add(
    "logs/structured.log",
    format=structured_log_formatter,
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

### Phase 2: Evaluate Based on Pain Points (Later)
- **If frequent complex analysis needed** → InfluxDB + Grafana
- **If real-time monitoring required** → Prometheus + Grafana  
- **If complex log searching needed** → ELK Stack

### Phase 3: Production Solution (Future)
- Cloud-based observability (DataDog, New Relic)
- Or self-hosted based on Phase 2 learnings

## Final Assessment

**Recommended Action**: **Status Quo + Enhanced Structured Logging**

**Rationale**:
- Application still evolving - avoid premature optimization
- Current Loguru adequate for development debugging
- Resource overhead significant for local development (~50% memory increase)
- Better to identify actual observability needs through usage

**The "Do Nothing" approach is optimal unless experiencing specific pain points that enhanced logging would solve.**

## Resource Impact Summary

| Option | Memory | Setup Complexity | Maintenance | Best Use Case |
|--------|--------|------------------|-------------|---------------|
| Status Quo | 0MB | None | None | Current development |
| Enhanced Loguru | ~10MB | Low | Minimal | Structured debugging |
| InfluxDB + Grafana | ~1.5GB | High | Medium | Performance monitoring |
| ELK Stack | ~2GB | Very High | High | Log analysis |
| Prometheus + Grafana | ~800MB | Medium | Medium | Metrics monitoring |

**Decision Point**: Only invest in heavier solutions when current approach creates measurable developer friction or blocks important insights.
