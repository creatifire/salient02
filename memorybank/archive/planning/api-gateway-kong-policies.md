<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# API Gateway (Kong) Policies

## Authentication & Authorization
- OIDC/JWT validation for first‑party apps; API keys for dev/internal tools.
- Tier‑based scopes for agent endpoints (Budget/Standard/Professional/Enterprise).

## Rate Limits & Quotas
- Per‑tier quotas (per‑minute and per‑day caps). Burst control enabled.
- Exact numbers TBD in pricing; enforced at Kong to protect upstreams.

## Size/Time Limits
- Request body max size configured at Kong.
- Response streaming timeouts set; SSE endpoints explicitly allowed.

References: see `production-deployment-config.md` for environment defaults and `design/open-questions.md` for remaining decisions.
