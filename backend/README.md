# Backend (FastAPI + Jinja + HTMX + SSE)

Structure created per memorybank/architecture/code-organization.md.
Populate templates in backend/templates/ and config in backend/config/.

## Run the app

### Without auto-reload
```bash
uvicorn backend.app.main:app
```

### With auto-reload (code only)
```bash
uvicorn backend.app.main:app --reload
```

### With auto-reload including YAML config
```bash
uvicorn backend.app.main:app \
  --reload \
  --reload-dir backend/config \
  --reload-include '*.yaml' \
  --reload-include '*.yml'
```

## Environment variables
- For LLM streaming via OpenRouter, set `OPENROUTER_API_KEY` in your shell or in `.env` at the repo root. The OpenRouter client loads `.env` without overriding existing env vars.
