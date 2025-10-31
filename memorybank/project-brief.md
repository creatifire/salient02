<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Project Brief
> **Last Updated**: January 31, 2025  
> **Updates**: Added multi-tenant-security.md design document, updated architecture document links

## Core Architectural Principles

### 🎯 Pydantic AI is Mandatory for ALL LLM Interactions

**ALL interactions with LLMs MUST use Pydantic AI.** This is non-negotiable and fundamental to the project architecture.

- ✅ **ALL agents**: Simple Chat, Sales Agent, InfoBot, etc.
- ✅ **ALL endpoints**: No direct OpenRouter/LLM API calls
- ✅ **ALL cost tracking**: Via Pydantic AI usage data (see [Pydantic AI Cost Tracking](./architecture/pydantic-ai-cost-tracking.md))
- ✅ **ALL future agents**: Built on Pydantic AI framework

**Why Pydantic AI?**
- Unified agent development framework
- Standardized tool registration (`@agent.tool`)
- Consistent dependency injection (`RunContext[SessionDependencies]`)
- Automatic usage tracking for billing
- Type-safe structured outputs
- Multi-agent orchestration support

**No Exceptions:**
- Legacy direct API calls are being deprecated
- All endpoints will migrate to Pydantic AI agents
- Building a library of Pydantic AI agents is core to this project

**Reference Documentation:**
- [Pydantic AI Cost Tracking](./architecture/pydantic-ai-cost-tracking.md) - Complete guide for streaming and non-streaming cost tracking
- [Agent and Tool Design](./architecture/agent-and-tool-design.md) - Architectural patterns and conventions
- [API Endpoints](./architecture/endpoints.md) - Complete endpoint documentation with Pydantic AI implementation status

---

## Purpose
Multi-tenant AI agent platform for customer engagement, information retrieval, and profile building:
- Answer questions using RAG (website content, PDFs, documentation)
- Search structured data directories (medical staff, products, pharmaceuticals, services)
- Build customer profiles (preferences, contact info, interests)
- Maintain conversation history with session persistence
- Connect customers to sales representatives
- Automated conversation summaries via email

## Core Capabilities
**Knowledge Sources:**
- Website content (HTML), PDFs (whitepapers, datasheets)
- Vector database indexed content (Pinecone)
- Structured data directories via Directory Service

**Directory Service:**
- Account-level lists (doctors, products, pharmaceuticals, services, etc.)
- Flexible JSONB schema per entry type
- Agent-configurable access control
- Schema definitions: `backend/config/directory_schemas/*.yaml`
- Tables: `directory_lists`, `directory_entries`
- Tool: `search_directory()` for Pydantic AI agents

**Customer Profiles:**
- Contact information (name, email, phone, address)
- Product/service interests
- Conversation history and summaries

## Development Environment

**Backend Execution Convention:**
- Backend is **always run from project root** (where venv is located)
- Command: `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`
- All imports must use `from backend.app...` not `from app...`
- Virtual environment: `backend/venv/` activated from project root

**Logging Standards:**
- **Logfire is the standard** - All logging MUST use Logfire (phasing out loguru over time)
- **Dual output** - Console logs (screen) + Logfire cloud dashboard (when token present)
- **Structured logging** - Use `logfire.info('event.name', key=value)` format
- **Event naming** - Dot notation: `module.action` (e.g., `agent.created`, `session.loaded`)
- **No visibility loss** - Console output always enabled for local development

**Diagnostic Logging Principles:**
- **NEVER disable diagnostic logging to hide problems** - Fix root causes, not symptoms
- `logfire.instrument_pydantic()` must remain enabled - verbose logs reveal issues
- Excessive log messages indicate underlying problems (tool loops, large histories)
- When logs are noisy: identify and fix the root cause (prompt issues, validation frequency)
- Diagnostic tools exist to help us see problems - removing them is counterproductive

## Configuration
**Agent-Level** (`agent_configs/{account}/{agent}/config.yaml`):
- LLM model selection
- Tool enablement (vector search, directory search, web search)
- Directory access: `accessible_lists: ["doctors", "products"]`
- Vector database namespace and API keys

**System-Level** (`app.yaml`, `.env`):
- Default LLM models
- API keys (OpenRouter, Pinecone, OpenAI)
- Database connections

## Architecture
- **RAG Application**: Pydantic AI multi-agent system
- **Memory**: PostgreSQL (sessions, messages, profiles, LLM requests)
- **Knowledge**: Pinecone vector database
- **Structured Data**: Directory Service (multi-tenant, flexible schema)
- **Multi-Tenancy**: Account → Agent Instance → Configuration cascade

### Core Architecture Documents
- [Agent and Tool Design](./architecture/agent-and-tool-design.md) - **Architecture patterns and conventions**
- [Simple Chat Agent Design](./architecture/simple-chat-agent-design.md) - **Template example** (follows agent-and-tool-design.md)
- [Multi-Tenant Security](./architecture/multi-tenant-security.md) - **Account isolation and API security** 🔴 CRITICAL
- [Code Organization](./architecture/code-organization.md) - File structure and technology stack
- [Configuration Reference](./architecture/configuration-reference.md) - Complete config documentation
- [API Endpoints](./architecture/endpoints.md) - All endpoints including Pydantic AI implementation status
- [Pydantic AI Cost Tracking](./architecture/pydantic-ai-cost-tracking.md) - Complete cost tracking guide
- [Data Model & ER Diagram](./architecture/datamodel.md) - Database schema
- [Tool Selection & Routing](./architecture/tool-selection-routing.md) - Tool routing strategies
- [Directory Search Tool](./architecture/directory-search-tool.md) - Directory service architecture
- [Directory Search FTS Guide](./architecture/directory-search-fts-guide.md) - Full-text search guide
- [Vector Query Tool](./architecture/vector-query-tool.md) - Vector search architecture
- [LLM Tool Calling Performance](./architecture/llm-tool-calling-performance.md) - Performance analysis
- [Open Questions](./architecture/open-questions.md) - Technical and product questions

### Research & Analysis
- [🎯 OpenRouter Cost Tracking Research](../backend/explore/openrouter-cost-tracking/README.md) - **COMPREHENSIVE ANALYSIS** of OpenRouter integration with Python agent frameworks, including breakthrough discovery of perfect hybrid solution
- [Advanced Logging](./analysis/advanced-logging.md)
- [Epic 0022 Library Review](./analysis/epic-0022-library-review.md)
- [Logging & Monitoring](./analysis/logging-monitoring.md)
- [Test Suite Analysis](./analysis/test_suite_analysis.md)

## Planning

### Strategic Planning
- [Milestone 1 Tactical Approach](./project-management/0000-approach-milestone-01.md)
- [Master Epic List](./project-management/0000-epics.md)

### Active Epics (Milestone 1 Focus)
- [Website HTMX Chatbot](./project-management/0003-website-htmx-chatbot.md)
- [Chat Memory & Persistence](./project-management/0004-chat-memory.md) - ✅ Completed
- [Multi-Account and Agent Support](./project-management/0005-multi-account-and-agent-support.md)
- [Sales Agent](./project-management/0008-sales-agent.md)
- [Vector Database Integration](./project-management/0011-vector-db-integration.md) - ✅ Completed
- [Outbound Email Integration](./project-management/0012-outbound-email.md)
- [Simple Chat Agent](./project-management/0017-simple-chat-agent.md) - 🚧 In Progress
- [Profile Builder](./project-management/0018-profile-builder.md)
- [Multi-Tenant Account-Instance Architecture](./project-management/0022-multi-tenant-architecture.md) - 🚧 In Progress
- [Multi-Purpose Directory Service](./project-management/0023-directory-service.md)
- [Bugs - Simple Chat Agent](./project-management/bugs-0017.md)

### Archived Epics
For completed early-phase work, superseded approaches, Milestone 2 planning, and future/aspirational capabilities, see:
- [Architecture Archive](./archive/README.md) - Archived architecture, design, and lessons learned documents
- [Project Management Archive](./project-management/archive/README.md) - Completed, superseded, and future epics

## Project Standards

### Coding Standards
- [Python Coding Standards](./standards/coding-standards-py.md)
- [JavaScript Coding Standards](./standards/coding-standards-js.md)
- [TypeScript Coding Standards](./standards/coding-standards-ts.md)

### Documentation Standards
- [Commit Message Conventions](./standards/commit-messages.md)
- [Epic Documentation Standards](./standards/epic-documentation.md)
- [Milestone Documentation Standards](./standards/milestone-documentation.md)
- [Python Code Commenting Best Practices](./standards/code-comments-py.md)
- [JavaScript/TypeScript Code Commenting Best Practices](./standards/code-comments-ts.md)

### Testing Standards
- [Automated Testing Guidelines](./standards/automated-testing.md)