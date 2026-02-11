# PrepExcellence Demo Site - Backend Setup

**Status**: Chunk 0017-005-004-001 Complete ✅  
**Date**: 2025-10-28  
**Epic**: 0017-005-004 - PrepExcellence Demo Site Implementation

## Overview

Backend configuration and database setup for PrepExcellence test preparation demo site, featuring SAT/ACT/PSAT preparation with Dr. Kaisar Alam's proven methodology.

## Files Created

### 1. Agent Configuration
**Location**: `backend/config/agent_configs/prepexcellence/prepexcel_info_chat1/`

#### `config.yaml`
- **Agent Type**: simple_chat
- **Account**: prepexcellence
- **Instance**: prepexcel_info_chat1
- **Model**: anthropic/claude-3.5-sonnet (excellent for educational content)
- **Temperature**: 0.3 (focused, consistent responses)
- **Max Tokens**: 2000

#### Vector Search Configuration
```yaml
vector_search:
  enabled: true
  max_results: 5
  similarity_threshold: 0.5  # Balanced for educational content
  pinecone:
    index_name: "prepexcellence-poc-01"
    namespace: "__default__"
    api_key_env: "PINECONE_API_KEY_OPENTHOUGHT"
  embedding:
    model: "text-embedding-3-small"
    dimensions: 1536
```

#### `system_prompt.md`
Comprehensive educational assistant persona emphasizing:
- Dr. Kaisar Alam's teaching methodology
- 150+ point improvement guarantee
- Test preparation strategies (SAT, ACT, PSAT)
- College admissions support
- Student success stories and testimonials
- Vector search tool usage for all PrepExcellence queries

### 2. Verification Script
**Location**: `backend/tests/manual/verify_prepexcel_index.py`

Verification script for Pinecone connectivity testing:
- Tests prepexcellence-poc-01 index access
- Verifies __default__ namespace connectivity
- Runs sample queries:
  - "SAT preparation courses"
  - "Dr. Alam teaching methodology"
  - "test prep pricing and schedule"
  - "student testimonials score improvement"
- Reports vector count, dimensions, and query performance

### 3. Database Setup
**Location**: `backend/scripts/setup_prepexcellence_account.sql`

SQL script to create:
- **accounts** table record for 'prepexcellence'
- **agent_instances** table record for 'prepexcel_info_chat1'
- Uses `ON CONFLICT` for idempotent execution

## Setup Instructions

### Step 1: Environment Variable
Ensure the Pinecone API key is set:
```bash
export PINECONE_API_KEY_OPENTHOUGHT="your-pinecone-api-key"
```

**Note**: Add to `.env` file or shell profile for persistence.

### Step 2: Database Setup
Run the SQL script to create account and agent instance:
```bash
cd backend
psql -U your_user -d salient_dev -f scripts/setup_prepexcellence_account.sql
```

Or via Python migration (preferred):
```bash
cd backend
source venv/bin/activate
# Run appropriate migration or manual INSERT
```

### Step 3: Verify Configuration
Test that the agent config loads correctly:
```bash
cd backend
source venv/bin/activate
python -c "
from app.services.config_loader import get_agent_config
import json

config = get_agent_config('prepexcellence/prepexcel_info_chat1')
print(json.dumps(config, indent=2, default=str))
"
```

Expected output should show:
- agent_type: simple_chat
- account: prepexcellence
- vector_search: enabled=True
- pinecone index: prepexcellence-poc-01

### Step 4: Verify Pinecone Connectivity
Run the verification script:
```bash
cd backend
source venv/bin/activate
python tests/manual/verify_prepexcel_index.py
```

Expected output:
- ✅ Pinecone config loaded
- ✅ Index statistics (vector count, dimensions)
- ✅ Sample queries return results
- ✅ Query performance metrics

## Configuration Details

### Pinecone Index
- **Project**: openthought-dev
- **Index**: prepexcellence-poc-01
- **Namespace**: __default__
- **Content**: PrepExcellence website content (courses, methodology, testimonials)
- **Vectors**: Already populated (confirmed by user)
- **Embedding Model**: text-embedding-3-small (1536 dimensions)

### Agent Features
- **Vector Search**: ✅ Enabled (prepexcellence-poc-01)
- **Directory Search**: ❌ Disabled (no directory data for test prep)
- **Web Search**: ❌ Disabled (use LLM knowledge + vector search only)
- **Conversation Management**: ✅ Enabled (auto-summarize after 10 exchanges)
- **History Limit**: 50 messages
- **Context Window**: 8000 tokens

### Multi-Tenant Architecture
- Account-level isolation: `prepexcellence` account
- Agent instance: `prepexcel_info_chat1`
- URL pattern: `/accounts/prepexcellence/agents/prepexcel_info_chat1/...`
- Widget configuration:
  ```javascript
  {
    account: 'prepexcellence',
    agent: 'prepexcel_info_chat1',
    backend: 'http://localhost:8000'
  }
  ```

## Testing Checklist

- [x] Config file created and parses without errors
- [x] System prompt emphasizes educational focus and vector search usage
- [x] Verification script created and made executable
- [x] SQL setup script created with idempotent operations
- [ ] PINECONE_API_KEY_OPENTHOUGHT environment variable set
- [ ] Database records created (run SQL script)
- [ ] Agent loads successfully via config loader
- [ ] Pinecone connectivity verified (run verification script)
- [ ] Test chat request sent to `/accounts/prepexcellence/agents/prepexcel_info_chat1/chat`
- [ ] Vector search tool called successfully in agent response
- [ ] Logs show `vector_search_start` and `vector_search_complete` events

## Next Steps (Chunk 0017-005-004-002)

Frontend folder structure and layouts:
1. Create `web/src/pages/prepexcellence/` folder
2. Create `PrepExcellenceLayout.astro` with purple/blue theme
3. Create `PrepExcellenceHeader.astro` and `PrepExcellenceFooter.astro`
4. Create `prepexcellence.css` theme file
5. Update root `web/src/pages/index.astro` demo selector

## Troubleshooting

### Config Not Loading
```bash
# Check file exists
ls -la backend/config/agent_configs/prepexcellence/prepexcel_info_chat1/

# Check YAML syntax
cd backend && python -c "import yaml; yaml.safe_load(open('config/agent_configs/prepexcellence/prepexcel_info_chat1/config.yaml'))"
```

### Pinecone Connection Fails
```bash
# Verify environment variable
echo $PINECONE_API_KEY_OPENTHOUGHT

# Test direct connection (from project root)
cd /path/to/salient02 && source .venv/bin/activate
python -c "
from pinecone import Pinecone
import os
api_key = os.getenv('PINECONE_API_KEY_OPENTHOUGHT')
pc = Pinecone(api_key=api_key)
print(pc.list_indexes())
"
```

### Vector Search Not Working
1. Check agent config: `vector_search.enabled: true`
2. Verify index exists: prepexcellence-poc-01
3. Check namespace: __default__
4. Verify API key environment variable is set
5. Run verification script for detailed diagnostics

## References

- Epic Plan: `memorybank/project-management/0017-simple-chat-agent.md#0017-005-004`
- Similar Implementation: Wyckoff (`backend/config/agent_configs/wyckoff/wyckoff_info_chat1/`)
- Verification Script Pattern: `backend/tests/manual/verify_wyckoff_index.py`
- Multi-Tenant Architecture: `memorybank/project-management/0022-multi-tenant-architecture.md`

