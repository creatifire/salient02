# Open Questions

> Consolidated technical and product questions for upcoming phases. Numbered for tracking.

## Technical Architecture
1. Load Balancing: How do we distribute load across multiple instances of the same agent? (per‑agent stickiness vs request hashing)
2. Circuit Breakers: How do we handle agent failures and implement fallbacks? (Kong vs app‑level; retry/backoff policies)
3. Streaming: Should all agents support streaming responses or only specific ones? (SSE vs POST policy per endpoint)
4. Configuration Architecture: Any remaining cases where agent config should be centralized in `app.yaml` instead of per‑agent config? (edge flags)

## Business Logic
5. Agent Specialization: What’s the optimal level of agent specialization vs generalization per tier?
6. User Experience: Should agent switching be explicit to users or transparent via router?
7. Training Data: How will we manage fine‑tuning or long‑term knowledge per agent type?
8. Cost Optimization: How do we balance cost vs capability across tiers and agents?

## Integration Patterns
9. Tool Orchestration: Should agents orchestrate tools directly or via a separate service later?
10. External APIs: Rate limiting and authentication strategy for outbound tools (per‑account credentials?)
11. Database Access: Direct DB access by agents vs internal service APIs?
12. Event Streaming: Should agent actions emit events for analytics/monitoring? (topic schema, retention)

## Vector Database & Data Management
13. Pinecone sharing model for Standard/Professional: single shared index with namespaces vs segmented shared indexes?
14. Namespace conventions and retention/cleanup policies; backup/export requirements.

## Observability & SRE
15. Logs/metrics/traces: OpenTelemetry scope, per‑tenant dashboards, SLOs.
16. Secrets management and rotation policy (K8s secrets vs external vault).
17. Deployment strategy: blue/green vs rolling; migration orchestration.
18. Usage tracking: LLM and vector usage attribution; per‑tier quotas and alerts.
19. Security: CORS/Kong policies, request size limits, PII handling, data residency/backup.
