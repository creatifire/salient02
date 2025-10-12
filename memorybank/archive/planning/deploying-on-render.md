# Deploying on Render

This document captures a minimal Render setup for the multi-account agent platform.

## Example render.yaml

```yaml
# render.yaml for multi-account agent platform
services:
  - type: web
    name: agent-platform-api
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    scaling:
      minInstances: 2
      maxInstances: 20
      targetCPUPercent: 70
    envVars:
      - key: DATABASE_URL
        from: render-postgres:platform-db
      - key: PINECONE_API_KEY
        from: render-secret:pinecone-key

  - type: backgroundWorker
    name: agent-orchestrator
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python -m app.workers.agent_orchestrator"
    instances: 3

  - type: postgres
    name: platform-db
    plan: standard-2gb
    
  - type: redis
    name: platform-cache
    plan: starter
```
