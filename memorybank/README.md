<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Memorybank - Project Documentation

This folder contains comprehensive documentation for the Salient02 AI chat system project.

## 🚀 Quick Start - Project Context

### Primary Documents (Start Here)
1. **[Project Brief](./project-brief.md)** - High-level project overview and goals
2. **[Milestone 1 Tactical Approach](./project-management/0000-approach-milestone-01.md)** - Current development plan with API endpoint evolution
3. **[Master Epic List](./project-management/0000-epics.md)** - All project epics and their status

### Current Development Focus (Milestone 1)
- **Phase 1**: [Simple Chat Agent](./project-management/0017-simple-chat-agent.md) (Config-based, single account)
- **Phase 2**: [Sales Agent](./project-management/0008-sales-agent.md) (RAG + business tools)
- **Transition Strategy**: [Agent Endpoint Transition](./design/agent-endpoint-transition.md) (Legacy → Agent endpoints)

## 📁 Folder Structure

### `/architecture/` - Technical Architecture
- **[Code Organization](./architecture/code-organization.md)** - Project structure and development patterns
- **[Data Model](./architecture/datamodel.md)** - Database schema and relationships
- **[Multi-Account Support](./architecture/multi-account-support.md)** - Multi-tenant architecture
- Technology stack, constraints, and deployment configurations

### `/design/` - Design Documents
- **[Simple Chat Agent Design](./design/simple-chat.md)** - Pydantic AI agent architecture
- **[Agent Endpoint Transition Strategy](./design/agent-endpoint-transition.md)** - API evolution plan

### `/project-management/` - Planning & Epics
- **Strategic Planning**: Milestone 1 & 2 tactical approaches
- **Core Epics**: Chat memory, multi-agent support, sales agent, simple chat agent
- **Infrastructure Epics**: Vector DB, content ingestion, email, scheduling
- **All 19 Epic Documents**: Complete feature specifications

### `/standards/` - Development Standards
- Coding standards (Python, JavaScript, TypeScript)
- Documentation standards (commit messages, code comments)

## 🎯 Current Architecture

### Agent Types (5 Total)
1. **Simple Chat** (0017) - Multi-tool foundation agent
2. **Sales** (0008) - CRM integration and lead qualification
3. **Digital Expert** (0009) - Content modeling and persona
4. **Simple Research** (0015) - Document intelligence and web search
5. **Deep Research** (0016) - Multi-step investigation

### API Endpoint Evolution
```
Phase 1: /agents/simple-chat/chat (+ legacy /chat)
Phase 2: /agents/sales/chat (+ simple-chat + legacy)
Phase 3: /accounts/{slug}/agents/{type}/chat (multi-account)
Phase 4: /accounts/{slug}/chat (router agent)
```

### Technology Stack
- **Backend**: Python + FastAPI + Pydantic AI + PostgreSQL
- **Frontend**: Astro + HTMX + Tailwind + SSE
- **AI**: OpenRouter (LLM) + Pinecone (Vector DB)
- **Tools**: MCP servers, web search, CRM integrations

## 🔗 Key Dependencies & References

### Database Schema
All tables documented in [datamodel.md](./architecture/datamodel.md):
- Core: `accounts`, `sessions`, `messages`, `llm_requests`
- Agents: `agent_instances`, `agent_templates`, `mcp_servers`, `vector_db_configs`
- Multi-account isolation with subscription tiers

### Multi-Agent Architecture
- Config file-based setup (Phase 1-2)
- Database-driven instances (Phase 3+)
- Router agent with intent classification (Phase 4)
- Complete backward compatibility throughout transition

This documentation structure ensures complete project context for development, onboarding, and future maintenance.
