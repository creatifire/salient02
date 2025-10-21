<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Redis Usage Policy

## Purpose
- Cache: configuration fragments, vector lookups, and minor UI flags.
- Session auxiliaries only; no primary persistence in Redis.

## Eviction & Namespacing
- Eviction: LRU with per‑key TTLs.
- Key namespaces by concern, e.g., `cfg:*`, `vec:*`.

## TTLs
- Configuration: 60–300s
- Ephemeral lookups: 30–120s
- Never store secrets in Redis.

References: `architecture/production-deployment-config.md`, `design/open-questions.md`.
