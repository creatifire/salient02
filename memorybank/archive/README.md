# Architecture Documentation Archive

> **Created**: January 12, 2025  
> This archive contains historical, planning, and superseded architecture documentation.

## Purpose

This folder preserves documentation that is no longer current or relevant to active development, but may provide valuable historical context or future reference.

## Archive Structure

### 📋 `planning/` - Future Plans Not Yet Implemented

Documents describing planned features, infrastructure, or configurations that have not been implemented. These may be revisited in future development phases.

**Files:**
- `api-gateway-kong-policies.md` - Kong API Gateway policies (Kong not implemented)
- `redis-usage-policy.md` - Redis caching strategy (Redis not currently used)
- `deploying-on-render.md` - Render deployment configuration (deployment platform TBD)
- `chat-widget-architecture.md` - Elaborate Preact/React/Vue adapter system (only Shadow DOM implemented)
- `production-cross-origin-plan.md` - Comprehensive production cross-origin setup (deployment-specific, not current)
- `production-deployment-config.md` - Production environment variables (deployment-specific)
- `agent-configuration-storage.md` - Brief Phase 1-3 transition notes (info covered in other docs)

### 📚 `outdated/` - Superseded Documentation

Documents that described systems, architectures, or approaches that have been superseded by current implementations or have significant gaps between documented and actual code.

**Files:**
- `salesbot-integration.md` - Multiple integration options (only Shadow DOM widget implemented)
- `technical-constraints.md` - Early constraints (outdated: described Jinja2-rendered HTMX swaps, now using JSON)
- `demo-integrations.md` - Mix of current and planned demos (references non-existent tasks)

**Note:** `code-organization.md` remains in active documentation despite describing aspirational structure, as it provides valuable organizational guidance for future development.

### ✅ `solved-issues/` - Historical Problem-Solution Documentation

Documents that described problems, challenges, or issues that have since been resolved. These provide valuable context for understanding why certain architectural decisions were made.

**Files:**
- `cross-origin-session-handling.md` - localhost:8000 vs localhost:4321 CORS issues (resolved via CORS middleware and credentials)

## Current Architecture Documentation

For current, accurate architecture documentation, see:

- **Cost Tracking**: `/memorybank/architecture/pydantic-ai-cost-tracking.md` (authoritative)
- **API Endpoints**: `/memorybank/architecture/endpoints.md`
- **Pydantic AI Integration**: `/memorybank/architecture/endpoint-pydantic-ai-matrix.md`
- **Database Schema**: `/memorybank/architecture/datamodel.md`
- **Configuration**: `/memorybank/architecture/configuration-reference.md`
- **Agent Configuration**: `/memorybank/architecture/agent-configuration.md`
- **Technology Stack**: `/memorybank/architecture/technology-stack.md`
- **Code Organization**: `/memorybank/architecture/code-organization.md` (aspirational but valuable)

## When to Archive Documentation

Documentation should be moved to this archive when:

1. **Planning**: Describes planned features not yet implemented and not actively being worked on
2. **Outdated**: Describes systems significantly different from current implementation
3. **Superseded**: Replaced by newer, more accurate documentation
4. **Solved**: Documents issues or challenges that have been resolved

## Retrieval

If you need to reference archived documentation:
1. Check the current documentation first - it may have incorporated relevant parts
2. Search this README for the topic you're interested in
3. Review the specific archived file with historical context in mind

## Maintenance

- Archive documents should NOT be updated - they are historical snapshots
- If archived content becomes relevant again, create NEW current documentation
- Update this README when adding new archived documents

