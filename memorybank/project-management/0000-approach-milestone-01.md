# Tactical Development Approach - Streamlined
> Sequential development approach focused on incremental enhancement and systematic scaling

## Executive Summary

**Current State**: ~70% project completion with core agent implementation complete:
- ✅ Epic 0004 (Chat Memory & Persistence) - Session management, database, message persistence
- ✅ Feature 0005-001 (Pydantic AI Framework) - Agent infrastructure ready  
- ✅ Feature 0011-001 (Vector Database Setup) - Pinecone integration working
- ✅ Feature 0017-003 (Core Agent Implementation) - Pydantic AI agent with conversation loading, cost tracking

- [ Note: Look for documents as a whole or sections of documents that can be used to provide context to LLMs (beyond Vector Databases) ]

**Approach**: Linear progression through priority items organized into phases, with manageable chunks and automated testing documented in epic files.

---

# PHASE 1: MVP Core Functionality

## 🎯 DEVELOPMENT PRIORITIES

### **Priority 0: Cleanup Overengineered Code** ✅
- [x] 0017-001-001 - Pre-Cleanup Safety & Documentation
- [x] 0017-001-002 - Update Test Files  
- [x] 0017-001-003 - Remove Overengineered Components
- [x] 0017-001-004 - Verify Clean Foundation

### **Priority 1: Legacy Agent Switch** ✅  
- [x] 0017-002-001 - Configuration-driven endpoint registration


### **Priority 2: Simple Chat Agent Implementation** ✅
- [x] 0017-003-001 - Direct Pydantic AI Agent Implementation
- [x] 0017-003-002 - Conversation History Integration  
- [x] 0017-003-003 - FastAPI Endpoint Integration
- [x] 0017-003-004 - LLM Request Tracking & Cost Management
- [x] 0017-003-005 - Agent Conversation Loading

### **Priority 2A: Configuration Cascade & Consistency** 🚧
- [x] 0017-004-001 - Configuration Parameter Standardization
- [x] 0017-004-002 - Agent-First Configuration Cascade
- [x] 0017-004-003-01 - Model settings cascade implementation (Generic infrastructure + model settings)
- [ ] 0017-004-003-02 - Tool configuration cascade
- [ ] 0017-004-003 - Update Agent Integration Points (1/2 chunks completed)

### **Priority 2B: Vector Search Tool** 📋 🎯 **NEXT PRIORITY**
- [ ] 0017-005-001 - Vector Search Tool Implementation
  - Core InfoBot functionality - answers questions using knowledge base

### **Priority 2C: Profile Fields Configuration & Database Schema** 📋
- [ ] 0017-006-001 - Profile Fields YAML Configuration
- [ ] 0017-006-002 - Migrate Profiles Table to JSONB

### **Priority 2D: Profile Capture Tool** 📋
- [ ] 0017-007-001 - Profile Capture Agent Tool
  - Conversational capture of email/phone using @agent.tool

### **Priority 2E: Email Summary Tool with Mailgun** 📋
- [ ] 0017-008-001 - Mailgun Integration
- [ ] 0017-008-002 - Email Summary Agent Tool
  - Completes user workflow: chat → capture → email summary

**Note**: Simple Chat Agent is now called "InfoBot" - information sharing bot (NO web search included)

**Phase 1 MVP Complete**: Priorities 2B through 2E complete the InfoBot MVP: vector search, profile capture, and email summaries.

---

## PHASE 2: Enhanced Functionality

Optional enhancements that extend InfoBot capabilities beyond core MVP.

### **Priority 2F: Email Capture & Consent (Optional)** 📋
- [ ] 0017-009-001 - Email Collection System
- [ ] 0017-009-002 - Consent and preferences management
  - UI-based alternative to conversational capture
  - May be superseded by Profile Capture Tool - review during implementation

### **Priority 2G: Periodic Summarization** 📋
- [ ] 0017-010-001 - Context Window Management System
  - Token counting and threshold monitoring
  - Conversation summarization engine
  - Automatic summarization triggers

### **Priority 2H: OTP Authentication** 📋
- [ ] 0017-011-001 - OTP Authentication System
  - Twilio Verify integration
  - Session upgrade and account creation
  - Cross-device session persistence

---

## PHASE 3: Multi-Agent Platform

### **Priority 3: Multi-Client Widget Foundation** 📋
- [ ] 0003-001-001 - Shadow DOM Widget
- [ ] 0003-001-002 - Preact Islands Integration  
- [ ] 0003-001-003 - HTMX UI Examples

### **Priority 4: Agent Type Plumbing** 📋
- [ ] 0005-002-001 - Agent type registration and discovery system
- [ ] 0005-002-002 - Configuration validation for different agent types
- [ ] 0005-002-003 - Routing enhancement for multiple agent types
- [ ] 0005-002-004 - Health checks and status monitoring

### **Priority 5: Sales Agent Addition** 📋
- [ ] 0008-001-001 - Sales agent foundation with business tools
- [ ] 0008-001-002 - RAG integration with business knowledge
- [ ] 0008-001-003 - Email integration (Mailgun)
- [ ] 0008-001-004 - Scheduling integration (Nylas/Calendly)
- [ ] 0008-001-005 - Profile data collection and lead qualification

### **Priority 6: Multi-Account Support** 📋
- [ ] 0005-003-001 - Account authentication and authorization
- [ ] 0005-003-002 - Account-scoped database isolation
- [ ] 0005-003-003 - Per-account configuration and billing
- [ ] 0005-003-004 - Account-specific vector database namespaces

### **Priority 7: Multi-Instance Per Account Support** 📋
- [ ] 0005-004-001 - Instance-specific configuration management
- [ ] 0005-004-002 - Multi-instance routing system
- [ ] 0005-004-003 - Instance isolation and resource management

### **Priority 8: React and Vue Chat Widgets** 📋
- [ ] 0003-002-001 - React Widget Component with TypeScript
- [ ] 0003-002-002 - Vue 3 Widget Component with Composition API
- [ ] 0003-002-003 - NPM Package Distribution (@salient/widget-react, @salient/widget-vue)

### **Priority 9: Advanced Widget Features** 📋
- [ ] 0003-003-001 - Iframe Adapter for security isolation
- [ ] 0003-003-002 - API-Only Mode for mobile integration
- [ ] 0003-003-003 - Advanced Theming with CSS variables
- [ ] 0003-003-004 - Widget Analytics and performance monitoring

**Current Status**: Priority 2A in progress 🚧 - Generic configuration cascade infrastructure implemented with model settings cascade (1/2 chunks of 0017-004-003 completed)  

**Next Steps (Phase 1 MVP):**
1. Complete Priority 2A: 0017-004-003-02 (Tool configuration cascade) - optional, can defer
2. **Priority 2B: 0017-005 (Vector Search Tool)** 🎯 - IMMEDIATE NEXT - Core InfoBot value
3. Priority 2C: 0017-006 (Profile Fields Config & JSONB Migration)
4. Priority 2D: 0017-007 (Profile Capture Tool)
5. Priority 2E: 0017-008 (Email Summary with Mailgun)
