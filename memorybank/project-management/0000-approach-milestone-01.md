<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Tactical Development Approach - Streamlined

## PHASE 1: MVP Core Functionality

### Priority 0: Cleanup Overengineered Code ✅
- ✅ 0017-001-001 - Pre-Cleanup Safety & Documentation
- ✅ 0017-001-002 - Update Test Files  
- ✅ 0017-001-003 - Remove Overengineered Components
- ✅ 0017-001-004 - Verify Clean Foundation

### Priority 1: Legacy Agent Switch ✅  
- ✅ 0017-002-001 - Configuration-driven endpoint registration

### Priority 2: Simple Chat Agent Implementation ✅
- ✅ 0017-003-001 - Direct Pydantic AI Agent Implementation
- ✅ 0017-003-002 - Conversation History Integration  
- ✅ 0017-003-003 - FastAPI Endpoint Integration
- ✅ 0017-003-004 - LLM Request Tracking & Cost Management
- ✅ 0017-003-005 - Agent Conversation Loading

### Priority 2A: Configuration Cascade & Consistency ✅
- ✅ 0017-004-001 - Configuration Parameter Standardization
- ✅ 0017-004-002 - Agent-First Configuration Cascade
- ✅ 0017-004-003 - Extend Configuration Cascade to Additional Parameters
  - ✅ 0017-004-003-01 - Model settings cascade implementation
  - ✅ 0017-004-003-02 - Tool configuration cascade

### Priority 2B: Multi-Tenant Account-Instance Architecture ✅
Epic 0022 - Foundational Infrastructure for Pydantic AI Migration

- ✅ 0022-001 - Core Multi-Tenancy Infrastructure
  - ✅ 0022-001-001 - Database & Configuration Infrastructure
    - ✅ 0022-001-001-01 - Test instance configuration files
    - ✅ 0022-001-001-02 - Multi-tenant database schema migration
    - ✅ 0022-001-001-03 - Agent instance loader implementation
    - ✅ 0022-001-001-04 - Instance discovery and listing
  - ✅ 0022-001-002 - Multi-Provider Infrastructure (Logfire complete)
    - ✅ 0022-001-002-00 - Logfire observability integration
    - ⏸️ 0022-001-002-01-06 - Provider factory, Together.ai (deferred to after Priority 6)
  - ✅ 0022-001-003 - API Endpoints
    - ✅ 0022-001-003-01 - Account agents router setup
    - ✅ 0022-001-003-01a - Session context migration (nullable fields)
    - ✅ 0022-001-003-02 - Non-streaming chat endpoint
    - ✅ 0022-001-003-03 - Streaming chat endpoint
    - ✅ 0022-001-003-04 - Instance listing endpoint
  - ✅ 0022-001-004 - Frontend Widget Migration
    - ✅ 0022-001-004-01 - Astro/Preact components
    - ⏸️ 0022-001-004-02 - Create iframe embedding option
    - ⏸️ 0022-001-004-03 - Multi-tenant showcase demo
  - ⏸️ 0022-001-005 - Cost Tracking & Observability (moved to Priority 3)
    - ✅ 0022-001-005-01 - LLM request tracker updates
    - ✅ 0022-001-005-02 - Link LLM requests to messages
  - ⏸️ 0022-001-006 - Testing & Validation
  - ⏸️ 0022-001-007 - Simple Admin UI
- ⏸️ 0022-002 - Authentication & Authorization

### Priority 3: Data Model Cleanup & Cost Attribution ✅
- ✅ 0022-001-005-01 - Populate denormalized fields in LLM requests (BUG-0017-005)
- ✅ 0022-001-005-02 - Link LLM requests to messages (1:many FK)
- ✅ BUG-0017-006 - Pinecone multi-project API key support
- ✅ 0022-001-005-03 - Add agent_instance_slug to sessions table
- ✅ 0017-005-003 - Multi-Agent Data Integrity Verification Script

### Priority 4: Vector Search Tool ✅
Epic 0017-005 - Vector Search Tool with Multi-Client Demo Architecture

- ✅ 0017-005-001 - Multi-Client Demo Site Architecture
  - ✅ 0017-005-001-01 - Multi-client folder structure and layouts
  - ✅ 0017-005-001-02 - Wyckoff Hospital demo pages
  - ✅ 0017-005-001-03 - Agent configurations (agrofresh, wyckoff)
- ✅ 0017-005-002 - Vector Search Tool Implementation
  - ✅ 0017-005-002-01 - Per-agent Pinecone configuration loader
  - ✅ 0017-005-002-02 - Pydantic AI @agent.tool for vector search
  - ✅ 0017-005-002-03 - End-to-end testing with real Pinecone data
- ✅ 0003-010 - Chat Widget Maximize/Minimize Toggle

### Priority 5: Directory Search Tool 📋
Epic 0023 - Multi-Purpose Directory Service
Dependencies: Epic 0022 (complete)

- ✅ 0023-001 - Core Infrastructure
  - ✅ 0023-001-001 - Database Schema (directory_lists, directory_entries)
  - ✅ 0023-001-002 - Schema Definitions (medical_professional.yaml)
  - ✅ 0023-001-003 - CSV Import (DirectoryImporter)
  - ✅ 0023-001-004 - DirectoryService (SQLAlchemy queries)
- ✅ 0023-002 - Search Tool
  - ✅ 0023-002-001 - search_directory Pydantic AI tool
  - ✅ 0023-002-002 - Wyckoff integration & testing
- ✅ 0023-008 - Multi-Tenant Dependencies
  - ✅ 0023-008-001 - SessionDependencies
- ✅ 0017-005-004 - PrepExcellence Demo Site Implementation
  - ✅ 0017-005-004-001 - Database and backend agent configuration
  - ✅ 0017-005-004-002 - Frontend folder structure and layouts
  - ✅ 0017-005-004-003 - Create PrepExcellence demo pages
  - ✅ 0017-005-004-004 - Demo selector integration and testing
  - ✅ 0017-005-004-005 - Vector search end-to-end testing
- ✅ 0023-007-002 - PostgreSQL Full-Text Search
- ✅ 0023-004-001 - Schema-Driven Generic Filters

### Priority 5A: Bug Fixes & Production Readiness ✅
Epic 0023 Bug Fixes + Critical Library Migrations

- ✅ BUG-0023-002 - Configuration Cascade Path Error
- ✅ BUG-0023-003 - Connection Pool Sizing
- ✅ FastAPI Lifespan Migration
- ✅ SQLAlchemy selectinload() Migration
- ✅ Pydantic AI RunContext Verification
- ✅ Alembic Async Migration Verification
- 📋 0023-004-003 - Centralized Tool Registry (Optional)
- 📋 0023-005-001 - Incremental CSV Updates (Optional)
- ⏸️ 0023-003 - Semantic Search (Pinecone)
  - ⏸️ 0023-003-001 - directory_embeddings table
  - ⏸️ 0023-003-002 - Embedding generation pipeline
  - ⏸️ 0023-003-003 - Hybrid search (exact + semantic)

### Priority 5B: Chat Widget Color Customization ✅
- ✅ 5B-001 - Widget Color Configuration Support
  - ✅ 5B-001-001 - Add color config parameters to widget
  - ✅ 5B-001-002 - Update widget CSS to use config colors
- ✅ 5B-002 - Demo Site Color Configuration
  - ✅ 5B-002-001 - Update Wyckoff site colors
  - ✅ 5B-002-002 - Update AgroFresh site colors
  - ✅ 5B-002-003 - Update Windriver site colors and display name
  - ✅ 5B-002-004 - Update PrepExcellence site colors
- ✅ 5B-003 - Documentation & Testing
  - ✅ 5B-003-001 - Update widget demo page documentation
  - ✅ 5B-003-002 - Cross-site visual verification

### Priority 5C: Library Dependency Updates ✅
- ✅ 5C-001 - Research & Documentation
  - ✅ 5C-001-001 - Document Pydantic AI Breaking Changes
    - ✅ 5C-001-001-001 - Review pydantic-ai 0.8 → 1.11 migration documentation
    - ✅ 5C-001-001-002 - Audit codebase for affected Pydantic AI APIs
  - ✅ 5C-001-002 - Document OpenAI Breaking Changes
    - ✅ 5C-001-002-001 - Review OpenAI 1.x → 2.x migration guide
    - ✅ 5C-001-002-002 - Audit codebase for direct OpenAI usage
  - ✅ 5C-001-003 - Python 3.14 Compatibility Check
    - ✅ 5C-001-003-001 - Verify Python 3.14 support for all packages
- ✅ 5C-002 - Minor/Patch Version Updates
  - ✅ 5C-002-001 - Update Low-Risk Packages
    - ✅ 5C-002-001-001 - Update fastapi, uvicorn, pydantic, genai-prices
- ✅ 5C-003 - OpenAI SDK Major Upgrade
  - ✅ 5C-003-001 - Upgrade OpenAI to 2.7.1
    - ✅ 5C-003-001-001 - Update OpenAI package
    - ✅ 5C-003-001-002 - Update direct OpenAI usage
    - ✅ 5C-003-001-003 - Verify Pydantic AI compatibility
- ✅ 5C-004 - Pydantic AI Major Upgrade
  - ✅ 5C-004-001 - Upgrade Pydantic AI to 1.11.1
    - ✅ 5C-004-001-001 - Update Pydantic AI package and fix breaking change
    - ✅ 5C-004-001-002 - Test all agents end-to-end

Dependencies: 5C-004 depends on 5C-003

Refactoring Tasks:
- ✅ BUG-0017-007 Phase 1 - Legacy Endpoints Disable
- ✅ BUG-0017-008 - config_loader.py refactoring (694→504 lines, 27%)
- ✅ BUG-0017-009 - simple_chat.py refactoring (1326→1184 lines, 11%)
- ✅ BUG-0017-010 - llm_request_tracker.py refactoring (576→484 lines, 16%)
- ✅ BUG-0017-007 Phase 3 - Legacy Endpoints Complete Removal (2108 lines deleted)

### Priority 5D: Transition to UUID v7 ✅
- ✅ 5D-001 - Code Changes (5 Python models: Session, Profile, Message, LLMRequest, Directory)
- ✅ 5D-002 - Database Reset
- ✅ 5D-003 - Testing & Verification
- ✅ 5D-004 - Documentation
## Epic 0025 - Dynamic Prompting Implementation
Reference: `memorybank/project-management/0025-dynamic-prompting-plan.md`

- ✅ 0025-001 - Pydantic AI Native Toolsets (Phase 1)
- ✅ 0025-002 - Phone Directory Prerequisites (Phase 2)
- ✅ 0025-003 - Schema Standardization + Multi-Directory Selection (Phase 3)
- 🔄 0025-004 - Multi-Tool Testing + Tool Calling Improvements (Phase 4A)

**>> You are here <<**
- 🔄 0025-004-004 - Implement Tool Calling Improvements (via Modular Prompts)
  - ✅ 0025-004-004-001 - Diagnostic Test with Alternative Model
  - ✅ 0025-004-004-002 - Quick Fix - Keyword Hints Module
  - ✅ 0025-004-004-003 - Create Prompt Module Infrastructure
  - 📋 0025-004-004-004 - Create Research-Backed Module Files
  - ✅ 0025-004-004-005 - Integrate Module Loading into simple_chat
  - 📋 0025-004-004-006 - Measure and Validate Improvements

### Priority 6: Profile Fields Configuration & Database Schema 📋
- 📋 0017-006-001 - Profile Fields YAML Configuration
- 📋 0017-006-002 - Migrate Profiles Table to JSONB

### Priority 7: Profile Capture Tool 📋
Epic 0017-012
- 📋 0017-012-001 - Profile Capture Agent Tool

### Priority 8: Email Summary Tool with Mailgun 📋
- 📋 0017-008-001 - Mailgun Integration
- 📋 0017-008-002 - Email Summary Agent Tool

### Priority 9: Multi-Provider Infrastructure 📋
- 📋 0022-001-002-01 - Provider factory and base infrastructure
- 📋 0022-001-002-02 - Config schema and validation
- 📋 0022-001-002-03 - Update simple_chat agent to use factory
- 📋 0022-001-002-04 - Update test instance configs (Together.ai)
- 📋 0022-001-002-05 - Provider-specific cost tracking
- 📋 0022-001-002-06 - Integration testing and validation

### Priority 10: Per-Agent Cookie Configuration 📋
Epic 0017-007 - Per-Agent Session Management
Dependencies: Epic 0022 (complete)

- 📋 0017-007-001 - Backend Session Cookie Configuration
  - 📋 0017-007-001-001 - Add cookie configuration to agent config.yaml
  - 📋 0017-007-001-002 - Update session middleware for per-agent cookies
  - 📋 0017-007-001-003 - Update chat widget for per-agent cookies
  - 📋 0017-007-001-004 - Database cleanup and migration
  - 📋 0017-007-001-005 - End-to-end testing and documentation

### Priority 11: Logging Infrastructure Consolidation ✅
Epic 0017-013 - Complete Migration from Loguru to Logfire

- ✅ Phase 1 - Core Agent & Tools (4 files)
- ✅ Phase 2 - Services (8 files)
- ✅ Phase 3 - Middleware (2 files)
- ✅ Phase 4 - API Routes (2 files)
- ✅ Phase 5 - Infrastructure & Cleanup (6 files)
- ✅ Phase 6 - Library Integrations & Final Cleanup
  - ✅ 6.1 - HTTPX instrumentation
  - ✅ 6.2 - Pydantic instrumentation
  - ✅ 6.3 - SQLAlchemy async instrumentation
  - ✅ 6.4 - Update logging-implementation.md
  - ✅ 6.5 - Remove loguru from dependencies
  - ✅ 6.6 - Remove standard logging remnants
  - ✅ 6.7 - Documentation audit

## PHASE 2: Enhanced Functionality

### Priority 12: Email Capture & Consent ⚠️
Status: DEPRECATED - Superseded by Priority 7

### Priority 13: Periodic Summarization 📋
- 📋 0017-010-001 - Context Window Management System

### Priority 14: OTP Authentication 📋
- 📋 0017-011-001 - OTP Authentication System

## PHASE 3: Multi-Agent Platform

### Priority 15: Multi-Client Widget Foundation ✅
- ✅ 0003-001-001 - Shadow DOM Widget
- ✅ 0003-001-002 - Preact Islands Integration
- ✅ 0003-001-003 - HTMX UI Examples

### Priority 16: Agent Type Plumbing ✅
Epic 0005-002 (superseded by Epic 0022)
- ✅ 0005-002-001 - Agent type registration and discovery (superseded by 0022-001-001-04)
- ✅ 0005-002-002 - Configuration validation (superseded by 0022-001-001-03)
- ✅ 0005-002-003 - Routing enhancement (superseded by Epic 0022)
- 📋 0005-002-004 - Health checks and status monitoring

### Priority 17: Sales Agent Addition 📋
- 📋 0008-001-001 - Sales agent foundation with business tools
- 📋 0008-001-002 - RAG integration with business knowledge
- 📋 0008-001-003 - Email integration (Mailgun)
- 📋 0008-001-004 - Scheduling integration (Nylas/Calendly)
- 📋 0008-001-005 - Profile data collection and lead qualification

### Priority 18: React and Vue Chat Widgets 📋
- 📋 0003-002-001 - React Widget Component with TypeScript
- 📋 0003-002-002 - Vue 3 Widget Component with Composition API
- 📋 0003-002-003 - NPM Package Distribution

### Priority 19: Advanced Widget Features 📋
- 📋 0003-003-001 - Iframe Adapter for security isolation
- 📋 0003-003-002 - API-Only Mode for mobile integration
- 📋 0003-003-003 - Advanced Theming with CSS variables
- 📋 0003-003-004 - Widget Analytics and performance monitoring
