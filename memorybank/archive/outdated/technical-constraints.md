<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Technical Constraints

- Transport/Rendering: SSE streaming with Jinja2-rendered snippets for HTMX swaps.
- No CORS for baseline; revisit when embedding in other origins.
- CDN: Load HTMX via CDN for baseline; retain ability to run fully local if overhead remains reasonable.
- Models: Do not hardcode model IDs in code paths; model is set via app YAML (`llm.model`).
- Secrets: Use `.env` with `OPENROUTER_API_KEY` (Bearer token per OpenRouter docs). Optionally set `HTTP-Referer` and `X-Title` headers.
- Future embedding: HTMX UI is designed to be embedded as a popup component in host pages (e.g., Astro mock in later phase).

