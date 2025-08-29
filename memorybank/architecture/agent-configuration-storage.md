# Agent Configuration Storage (Files → Database)

## Phase 1–2 (Files)
- One YAML per agent type in `backend/config/agent_configs/` following the schema in `architecture/agent-configuration.md`.
- Values define model settings, memory thresholds, tools, and vector DB policy (Pinecone/pgvector).

## Phase 3+ (Database)
- Tables: `agent_templates` and `agent_instances` (see `architecture/datamodel.md`).
- Migration plan: import existing YAML → templates; bind per‑account overrides as instances.
- Hot‑reload: cached reads with Redis (key `cfg:agent:{account}:{type}`) and explicit invalidation on updates.
- Validation & versioning: enforce JSON schema on write; track template/instance versions.

References: `architecture/datamodel.md`, `architecture/agent-configuration.md`.
