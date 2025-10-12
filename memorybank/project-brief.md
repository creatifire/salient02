# Project Brief
> **Last Updated**: January 12, 2025

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
- [Endpoint Pydantic AI Matrix](./architecture/endpoint-pydantic-ai-matrix.md) - Complete status of all endpoints and migration plan

---

## Purpose of System
    - Answer questions about a company's products and services, based on:
        - Company's Website Content (HTML)
        - Other Website Content (HTML)
        - Company provided white papers (PDF)
        - Company provided data sheets (PDF)
    - Collect preferences and build a profile of the customer
    - Maintain session history
    - Maintain Chat history
    - Connect the customer to the local sales rep
    - Send a conversation summary to the customer after:
        - a period of inactivity
        - when the conversation ends

## A Sales Bot powered by:
    - Large Language Model (LLM)
        - OpenRouter
    - Memory
        - Chat History
        - Chat Summary
        - Customer Profile
            - Products of Interest
            - Services of Interest
            - Customer Name
            - Customer Contact Information
                - Phone Number
                - Email Address
                - Physical Address
                    - Street Address
                    - City
                    - State
                    - Zip
        - Past emails
    - Knowledge
        - Indexed from Vector Database

## Config File
    - YAML
        - Which LLM to use
            - Legacy endpoints: configured in `app.yaml`
            - Agent endpoints: configured in `agent_configs/{agent_type}.yaml` (overrides app.yaml)
        - Which Agent to Use
        - Which Vector Database
            - Pinecone
            - Which Pinecone Database
    - Environment Variables
        - OpenRouter API Key
        - Pinecone API Key

## Architecture
    - RAG Application
    - Memories in a Relational Database (Postgres)
    - Knowledge Indexed in a Vector Database (Pinecone)
    - Pydantic AI Multi-Agent System

### Core Architecture Documents
- [Technology Stack](./architecture/technology-stack.md)
- [Technical Constraints](./architecture/technical-constraints.md)
- [Code Organization](./architecture/code-organization.md)
- [Configuration Reference](./architecture/configuration-reference.md)
- [Agent Configuration](./architecture/agent-configuration.md)
- [Agent Configuration Storage](./architecture/agent-configuration-storage.md)
- [API Endpoints](./architecture/endpoints.md)
- [Pydantic AI Cost Tracking](./architecture/pydantic-ai-cost-tracking.md)
- [Chat Widget Architecture](./architecture/chat-widget-architecture.md)
- [Data Model & ER Diagram](./architecture/datamodel.md)
- [Multi-Account Support](./architecture/multi-account-support.md)

### Research & Analysis
- [🎯 OpenRouter Cost Tracking Research](../backend/explore/openrouter-cost-tracking/README.md) - **COMPREHENSIVE ANALYSIS** of OpenRouter integration with Python agent frameworks, including breakthrough discovery of perfect hybrid solution

### Integration & Deployment
- [SalesBot Integration Options](./architecture/salesbot-integration.md)
- [Demo Integration Strategy](./architecture/demo-integrations.md)
- [Cross-Origin Session Handling](./architecture/cross-origin-session-handling.md)
- [Production Cross-Origin Plan](./architecture/production-cross-origin-plan.md)
- [Production Deployment Configuration](./architecture/production-deployment-config.md)
- [Deploying on Render](./architecture/deploying-on-render.md)
- [API Gateway Kong Policies](./architecture/api-gateway-kong-policies.md)
- [Redis Usage Policy](./architecture/redis-usage-policy.md)

## Planning

### Strategic Planning
- [Milestone 1 Tactical Approach](./project-management/0000-approach-milestone-01.md)
- [Master Epic List](./project-management/0000-epics.md)

### Active Epics (Milestone 1 Focus)
- [Chat Memory & Persistence](./project-management/0004-chat-memory.md) - ✅ Completed
- [Multi-Account and Agent Support](./project-management/0005-multi-account-and-agent-support.md)
- [Sales Agent](./project-management/0008-sales-agent.md)
- [Vector Database Integration](./project-management/0011-vector-db-integration.md) - ✅ Completed
- [Outbound Email Integration](./project-management/0012-outbound-email.md)
- [Simple Chat Agent](./project-management/0017-simple-chat-agent.md) - 🚧 In Progress
- [Multi-Tenant Account-Instance Architecture](./project-management/0022-multi-tenant-architecture.md) - 🚧 In Progress
- [Profile Search Tool](./project-management/0023-profile-search-tool.md)

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
- [Python Code Commenting Best Practices](./standards/code-comments-py.md)
- [JavaScript/TypeScript Code Commenting Best Practices](./standards/code-comments-ts.md)