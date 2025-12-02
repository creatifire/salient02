<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Epic 0017 - Simple Chat Agent (InfoBot - Pydantic AI Implementation)
> **Last Updated**: October 17, 2025

Implement Pydantic AI-powered InfoBot agent that shares information about products/services, captures profile data, and emails conversation summaries.

## Architecture Overview

```mermaid
flowchart TD
    %% External Components
    User["👤 User"] --> FastAPI["📡 FastAPI Endpoint"]
    
    %% Configuration System
    AgentConfig["🎛️ {account}/{instance}/config.yaml"] --> Agent["🤖 Pydantic AI Agent"]
    ProfileConfig["📋 {account}/{instance}/profile.yaml"] --> Agent
    SystemPromptFile["📝 system_prompt.md"] --> Agent
    GlobalConfig["⚙️ app.yaml (fallback)"] --> Agent
    
    %% Core Agent Structure
    FastAPI --> Agent
    
    %% Dependencies & Session Management
    Session["🔧 SessionDependencies"] --> Agent
    FastAPI --> Session
    
    %% Agent Workflow Components
    Agent --> History["💬 Message History"]
    Agent --> AgentTools["🛠️ Agent Tools"]
    
    %% Agent Tools (@agent.tool)
    AgentTools --> VectorTool["🔍 Vector Search Tool"]
    AgentTools --> ProfileTool["👤 Profile Capture Tool"]
    AgentTools --> SummaryTool["📧 Email Summary Tool"]
    
    %% Profile Management
    ProfileTool --> ProfileValidation["✅ Validate Against YAML"]
    ProfileValidation --> ProfileDB[("🗄️ Profiles Table (JSONB)")]
    ProfileDB --> RequiredFields["required_profile_fields JSONB"]
    ProfileDB --> CapturedFields["captured_profile_fields JSONB"]
    ProfileDB --> FieldsUpdated["required_fields_updated_at"]
    
    %% Email Summary Workflow
    SummaryTool --> CheckProfile{"Profile Complete?"}
    CheckProfile -->|No| RequestInfo["Request Missing Fields"]
    CheckProfile -->|Yes| GenerateSummary["Generate Summary"]
    GenerateSummary --> Mailgun["📧 Mailgun API"]
    Mailgun --> EmailSent["✉️ Email Sent"]
    
    %% Current LLM Integration
    Agent --> OpenRouter["🧠 OpenRouter + LLM"]
    
    %% Data Flow & Persistence
    FastAPI --> MessageService["💾 Message Service"]
    FastAPI --> LLMTracker["📈 LLM Request Tracker"]
    MessageService --> Database[("🗄️ PostgreSQL")]
    LLMTracker --> Database
    
    %% Vector Search Integration
    VectorTool --> VectorService["🔎 Vector Service"]
    VectorService --> Pinecone["📊 Pinecone"]
    
    %% Response Flow
    Agent --> Response["✨ Agent Response"]
    Response --> FastAPI
    FastAPI --> User
```

**Key Pydantic AI Patterns:**
- **Agent Creation**: `Agent(model_name, deps_type=SessionDependencies, output_type=StructuredOutput)`
- **Dependency Injection**: `RunContext[SessionDependencies]` for session, database, and configuration access
- **Tool Registration**: `@agent.tool` decorators for vector search, profile capture, email summary
- **Structured Output**: Pydantic models for validated, type-safe responses
- **Tool Workflow**: Agent determines when to call tools based on conversation context

## InfoBot Purpose
Simple Chat Agent serves as an information bot that:
- Answers questions about products/services using vector search
- Captures minimal profile data (email, phone)
- Emails conversation summaries on request
- Does NOT include web search capabilities

## 0017-001 - FEATURE - Cleanup Overengineered Code
- [x] 0017-001-001 - TASK - Pre-Cleanup Safety & Documentation
  - [x] 0017-001-001-01 - CHUNK - Backup branch and current state documentation
    - SUB-TASKS:
      - Create backup branch: `backup/overengineered-simple-chat-agent`
      - Document line counts, test results, dependencies (950 lines total)
      - Verify system functional baseline
    - STATUS: Completed — Backup branch created, 950+ lines documented, 98 tests baseline established
- [x] 0017-001-002 - TASK - Update Test Files
  - [x] 0017-001-002-01 - CHUNK - Comment out failing tests with TODO markers
    - SUB-TASKS:
      - Identify dependencies: `grep -r "SimpleChatAgent\|ChatResponse"`
      - Comment out 14 failing tests across 2 files
      - Add TODO comments for Phase 3 recreation
    - STATUS: Completed — Test failures reduced from 15 to 4, preserved working components
- [x] 0017-001-003 - TASK - Remove Overengineered Components
  - [x] 0017-001-003-01 - CHUNK - Delete files in dependency order
    - SUB-TASKS:
      - Delete factory system (389 lines)
      - Delete complex models (209 lines)  
      - Delete agent wrapper (305 lines)
      - Update `__init__.py` imports, clear cache
    - STATUS: Completed — 950+ lines removed, no import errors on startup
- [x] 0017-001-004 - TASK - Verify Clean Foundation
  - [x] 0017-001-004-01 - CHUNK - Test preserved components and endpoints
    - SUB-TASKS:
      - Import verification: SessionDependencies, get_agent_config
      - Application startup test
      - Legacy endpoints functional test
    - STATUS: Completed — All preserved components work, legacy endpoints functional

## 0017-002 - FEATURE - Foundation Setup  
- [x] 0017-002-001 - TASK - Legacy Agent Switch
  - [x] 0017-002-001-01 - CHUNK - Configuration-driven endpoint registration
    - SUB-TASKS:
      - Add `legacy.enabled` to app.yaml
      - Conditional endpoint registration in main.py
      - Parallel development capability
    - STATUS: Completed — Legacy endpoints can be toggled via configuration for parallel development

```yaml
# app.yaml
legacy:
  enabled: true                    # Can be toggled to false for parallel development
  endpoints:
    chat: "/chat"                  # Legacy chat endpoint
    stream: "/events/stream"       # Legacy SSE streaming
    main: "/"                      # Main chat page
```

```python
# main.py  
def _register_legacy_endpoints() -> None:
    config = load_config()
    legacy_config = config.get("legacy", {})
    
    if legacy_config.get("enabled", True):
        app.get("/", response_class=HTMLResponse)(serve_base_page)
        app.get("/events/stream")(sse_stream)
        app.post("/chat", response_class=PlainTextResponse)(chat_fallback)
```

## 0017-003 - FEATURE - Core Agent Implementation  
**Status**: 5 of 7 tasks completed

**Additional Enhancements Completed**: Chat history ordering fix, configurable history limits, cross-origin session sharing fix, UI list formatting fix

- [x] 0017-003-001 - TASK - Direct Pydantic AI Agent Implementation  
  - [x] 0017-003-001-01 - CHUNK - Agent creation with YAML configuration
    - SUB-TASKS:
      - Global agent instance with lazy loading
      - Dynamic model configuration: `openrouter:deepseek/deepseek-chat-v3.1`
      - SessionDependencies integration
      - System prompt loading from simple_chat.yaml
    - STATUS: Completed — Agent responds with YAML configuration, async patterns implemented

```python
async def create_simple_chat_agent() -> Agent:
    config = load_config()
    llm_config = config.get("llm", {})
    
    provider = llm_config.get("provider", "openrouter")
    model = llm_config.get("model", "deepseek/deepseek-chat-v3.1")
    model_name = f"{provider}:{model}"
    
    agent_config = await get_agent_config("simple_chat")
    
    return Agent(
        model_name,
        deps_type=SessionDependencies,
        system_prompt=agent_config.system_prompt
    )
```

- [x] 0017-003-002 - TASK - Conversation History Integration
  - [x] 0017-003-002-01 - CHUNK - Database message conversion to Pydantic AI format
    - SUB-TASKS:
      - Convert database messages to ModelRequest/ModelResponse
      - Auto-load conversation history when message_history=None  
      - Session continuity across multiple agent calls
    - STATUS: Completed — Multi-turn conversations maintain context, automatic history loading working

```python
# backend/app/agents/simple_chat.py - History loading function
async def load_conversation_history(session_id: str, max_messages: Optional[int] = None) -> List[ModelMessage]:
    """Load conversation history from database and convert to Pydantic AI format."""
    if max_messages is None:
        config = load_config()
        chat_config = config.get("chat", {})
        max_messages = chat_config.get("history_limit", 20)

    message_service = get_message_service()
    session_uuid = uuid.UUID(session_id)
    
    # Retrieve recent messages from database
    db_messages = await message_service.get_session_messages(
        session_id=session_uuid,
        limit=max_messages
    )

    # Convert database messages to Pydantic AI ModelMessage format
    pydantic_messages = []
    for msg in db_messages:
        if msg.role in ("human", "user"):
            # Create user request message
            pydantic_message = ModelRequest(
                parts=[UserPromptPart(
                    content=msg.content,
                    timestamp=msg.created_at or datetime.now()
                )]
            )
        elif msg.role == "assistant":
            # Create assistant response message
            pydantic_message = ModelResponse(
                parts=[TextPart(content=msg.content)],
                usage=None,
                model_name="simple-chat",
                timestamp=msg.created_at or datetime.now()
            )
        else:
            continue  # Skip system messages
            
        pydantic_messages.append(pydantic_message)

    return pydantic_messages
```

- [x] 0017-003-003 - TASK - FastAPI Endpoint Integration
  - [x] 0017-003-003-01 - CHUNK - `/agents/simple-chat/chat` POST endpoint
    - SUB-TASKS:
      - Session handling via get_current_session()
      - Message persistence before/after LLM call
      - Error handling with graceful degradation  
      - Comprehensive logging for monitoring
    - STATUS: Completed — Endpoint accessible, session handling, message persistence, error handling implemented

```python
# backend/app/api/agents.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from app.agents.simple_chat import simple_chat
from app.middleware.simple_session_middleware import get_current_session
from app.services.message_service import get_message_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    message_history: Optional[List[ModelMessage]] = None

@router.post("/agents/simple-chat/chat", response_class=PlainTextResponse)
async def simple_chat_endpoint(chat_request: ChatRequest, request: Request):
    # 1. SESSION HANDLING - Extract and validate session
    session = get_current_session(request)
    if not session:
        return PlainTextResponse("Session error", status_code=500)
    
    # 2. MESSAGE PERSISTENCE - Before LLM call
    message_service = get_message_service()
    user_message_id = await message_service.save_message(
        session_id=session.id,
        role="human",
        content=chat_request.message,
        metadata={"source": "simple_chat", "agent_type": "simple_chat"}
    )
    
    # 3. PYDANTIC AI AGENT CALL
    result = await simple_chat(
        message=chat_request.message, 
        session_id=str(session.id),
        message_history=chat_request.message_history
    )
    
    # 4. MESSAGE PERSISTENCE - After LLM completion  
    await message_service.save_message(
        session_id=session.id,
        role="assistant", 
        content=result['response'],
        metadata={"user_message_id": str(user_message_id), "usage": result.get('usage', {})}
    )
    
    return PlainTextResponse(result['response'])
```

- [x] 0017-003-004 - TASK - LLM Request Tracking & Cost Management  
  - [x] 0017-003-004-01 - CHUNK - OpenRouterProvider breakthrough solution
    - SUB-TASKS:
      - Single-call cost tracking with `OpenRouterProvider`
      - Direct client access: `provider.client` 
      - Real OpenRouter cost extraction via `extra_body={"usage": {"include": True}}`
      - Database storage with Decimal precision
    - STATUS: Completed — Production-ready billing with $0.0001801 precision, breakthrough single-call architecture

```python
# Breakthrough: Direct OpenRouter client with cost tracking
from pydantic_ai.providers.openrouter import OpenRouterProvider

provider = OpenRouterProvider(api_key=openrouter_api_key)
direct_client = provider.client

response = await direct_client.chat.completions.create(
    model="deepseek/deepseek-chat-v3.1",
    messages=api_messages,
    extra_body={"usage": {"include": True}},  # Critical for cost data
    max_tokens=1000,
    temperature=0.7
)

real_cost = float(response.usage.cost)  # Accurate to the penny
```

  - [x] 0017-003-004-02 - CHUNK - Testing UI for cost validation
    - SUB-TASKS:
      - Create `simple-chat.astro` based on htmx-chat.astro design
      - Cost tracking display (tokens, cost, latency)
      - JSON response handling with usage data
      - Session compatibility with existing history endpoint
    - STATUS: Completed — UI accessible at `/demo/simple-chat`, real-time cost tracking visible

- [x] 0017-003-005 - TASK - Agent Conversation Loading
  - [x] 0017-003-005-01 - CHUNK - Create agent session service
    - SUB-TASKS:
      - Create `load_agent_conversation(session_id) -> List[ModelMessage]`
      - Use `message_service.get_session_messages()` 
      - Convert DB roles: "user" → ModelRequest, "assistant" → ModelResponse
    - STATUS: Completed — Agent session service created with proper DB to Pydantic AI conversion
    - AUTOMATED-TESTS:
      - **Unit Tests**: `test_load_agent_conversation()` - Tests message loading and role conversion without database
      - **Integration Tests**: `test_load_agent_conversation_with_db()` - Tests full workflow with real database messages

```python
# backend/app/services/agent_session.py
from typing import List, Dict, Any
from app.services.message_service import get_message_service
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from datetime import datetime
import uuid

async def load_agent_conversation(session_id: str) -> List[ModelMessage]:
    """Load conversation history from database and convert to Pydantic AI format."""
    message_service = get_message_service()
    
    # Get all messages for this session (from any endpoint)
    db_messages = await message_service.get_session_messages(
        session_id=uuid.UUID(session_id),
        limit=50  # Configurable
    )
    
    if not db_messages:
        return []
    
    # Convert DB messages to Pydantic AI ModelMessage format
    pydantic_messages = []
    for msg in db_messages:
        if msg.role in ("human", "user"):
            pydantic_message = ModelRequest(
                parts=[UserPromptPart(
                    content=msg.content,
                    timestamp=msg.created_at or datetime.now()
                )]
            )
        elif msg.role == "assistant":
            pydantic_message = ModelResponse(
                parts=[TextPart(content=msg.content)],
                usage=None,  # Historical messages don't have usage data
                model_name="agent-session",
                timestamp=msg.created_at or datetime.now()
            )
        else:
            continue  # Skip system messages
            
        pydantic_messages.append(pydantic_message)
    
    return pydantic_messages

async def get_session_stats(session_id: str) -> Dict[str, Any]:
    """Get session statistics for monitoring conversation continuity."""
    message_service = get_message_service()
    
    total_messages = await message_service.count_messages(session_id)
    
    return {
        "total_messages": total_messages,
        "session_id": session_id,
        "cross_endpoint_continuity": total_messages > 0
    }
```

  - [x] 0017-003-005-02 - CHUNK - Integration with simple_chat function
    - SUB-TASKS:
      - Modify `simple_chat()` to auto-load history when `message_history=None`
      - Maintain all existing functionality (cost tracking)
      - Cross-endpoint conversation continuity
    - STATUS: Completed — Simple chat function auto-loads history, maintains cost tracking, includes session continuity stats
    - AUTOMATED-TESTS:
      - **Unit Tests**: `test_simple_chat_auto_load_history()` - Tests history loading logic in isolation
      - **Integration Tests**: `test_simple_chat_cross_endpoint_continuity()` - Tests complete cross-endpoint conversation flow

```python
# backend/app/agents/simple_chat.py - Enhanced simple_chat function
async def simple_chat(
    message: str, 
    session_id: str,
    message_history: Optional[List[ModelMessage]] = None
) -> dict:
    """Simple chat function with automatic conversation history loading."""
    
    # STEP 1: Load conversation history if not provided
    if message_history is None:
        from app.services.agent_session import load_agent_conversation
        message_history = await load_agent_conversation(session_id)
    
    # STEP 2: Create session dependencies
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,
        max_history_messages=20
    )
    
    # STEP 3: Get agent and run with full context
    agent = await get_chat_agent()
    result = await agent.run(
        message, 
        deps=session_deps,
        message_history=message_history  # Full conversation context
    )
    
    return {
        'response': result.output,
        'usage': result.usage(),
        'session_continuity': await get_session_stats(session_id)
    }
```

  - [x] 0017-003-005-03 - CHUNK - Session analytics and monitoring
    - SUB-TASKS:
      - Add session stats function (message counts, bridging status)
      - Log session bridging for analytics  
      - Return stats in response for debugging
    - STATUS: Completed — Enhanced session analytics with comprehensive stats, cross-endpoint detection, conversation metrics, and session bridging logging
    - AUTOMATED-TESTS:
      - **Unit Tests**: `test_get_session_stats()` - Tests stats calculation with various message scenarios
      - **Integration Tests**: `test_session_analytics_end_to_end()` - Tests analytics with real multi-source conversations

  AUTOMATED-TESTS:
  - **Integration Tests**: `test_agent_conversation_loading_workflow()` - Complete conversation loading and continuity across endpoints
  - **Performance Tests**: `test_conversation_loading_performance()` - Ensures history loading doesn't impact response times significantly  
  - **Error Handling Tests**: `test_conversation_loading_edge_cases()` - Invalid session IDs, empty sessions, malformed messages

## 0017-004 - FEATURE - Configuration Cascade & Consistency
**Status**: Task 0017-004-001 Completed ✅

**Problem**: Configuration parameter naming inconsistencies and incorrect cascade order
- **Naming Issue**: `app.yaml` uses `history_limit` while `simple_chat.yaml` uses `max_history_messages`  
- **Cascade Issue**: Current implementation checks `app.yaml` first, should check agent config first

**Solution**: Agent-specific → Global → Code fallback hierarchy with consistent naming

**Desired Cascade for Simple Chat Agent:**
1. **`simple_chat/config.yaml`** (agent-specific settings) — highest priority
2. **`app.yaml`** (global defaults) — fallback  
3. **Code constants** (safety fallback) — last resort

- [ ] 0017-004-001 - TASK - Configuration Parameter Standardization

  **NEW STRUCTURE OVERVIEW**:
  ```
  backend/config/agent_configs/
  ├── simple_chat/
  │   ├── config.yaml       # Agent-specific configuration
  │   └── system_prompt.md  # Agent system prompt
  └── app.yaml             # Global configuration defaults
  ```
  - [x] 0017-004-001-01 - CHUNK - Agent-specific folder structure and prompt separation  
    - SUB-TASKS:
      - Create `backend/config/agent_configs/simple_chat/` directory structure
      - Move and rename `simple_chat.yaml` → `simple_chat/config.yaml`
      - Extract system prompt to `simple_chat/system_prompt.md` file
      - Add prompt configuration section to config.yaml specifying prompt file paths
      - Update agent config loader to handle new folder structure and external prompt files
      - Update all code references to new config file path (`simple_chat/config.yaml`)
    - AUTOMATED-TESTS (3 tests):
      - `test_agent_config_loads_from_new_path()` - Verify config.yaml loads from simple_chat/ folder
      - `test_system_prompt_loads_from_md_file()` - Verify system_prompt.md loads correctly
      - `test_prompt_configuration_section()` - Verify config references external prompt file
    - MANUAL-TESTS:
      - Verify config.yaml loads from `backend/config/agent_configs/simple_chat/` folder
      - Confirm system_prompt.md file exists and contains expected prompt content
      - Test that agent config correctly references external prompt file path
    - STATUS: Completed — Agent-specific folder structure implemented with external prompt loading, backward compatibility maintained, all automated tests passing
    - PRIORITY: High — Enables scalable multi-agent architecture with better organization
  
  - [x] 0017-004-001-02 - CHUNK - Parameter name standardization in config.yaml
    - SUB-TASKS:
      - Change `context_management.max_history_messages: 50` → `context_management.history_limit: 50`
      - Verify all other parameter names follow app.yaml conventions
      - Update inline comments to reflect standardized naming
      - Ensure agent-specific overrides maintain consistent naming with global config
    - AUTOMATED-TESTS (2 tests):
      - `test_history_limit_parameter_exists()` - Verify history_limit parameter is read correctly
      - `test_old_max_history_messages_not_used()` - Verify old parameter name is no longer referenced
    - MANUAL-TESTS:
      - Verify config.yaml contains `context_management.history_limit` parameter
      - Confirm old `max_history_messages` parameter is completely removed from config
      - Test that agent uses the standardized parameter name in practice
    - STATUS: Completed — Parameter names standardized across configuration files and code, SessionDependencies updated to use history_limit, all automated and manual tests passing
    - PRIORITY: High — Required for proper configuration cascade implementation
  
  - [x] 0017-004-001-03 - CHUNK - Update SessionDependencies class for standardized parameters
    - SUB-TASKS:
      - Change `SessionDependencies.max_history_messages` → `SessionDependencies.history_limit` in `backend/app/agents/base/dependencies.py`
      - Update constructor parameters: `__init__(max_history_messages: int = 20)` → `__init__(history_limit: int = 20)`
      - Update all method signatures and docstrings
      - Update class factory methods to use new parameter names
    - AUTOMATED-TESTS (3 tests):
      - `test_session_dependencies_constructor()` - Verify constructor accepts history_limit parameter
      - `test_session_dependencies_no_old_params()` - Verify max_history_messages parameter is removed
      - `test_session_dependencies_method_signatures()` - Verify all method signatures use standardized parameters
    - MANUAL-TESTS:
      - Verify SessionDependencies class accepts history_limit parameter in constructor
      - Confirm max_history_messages parameter is no longer accepted
      - Test that all method signatures use standardized parameter names
    - STATUS: Completed — SessionDependencies class already properly implemented with history_limit parameter, all automated tests passing, comprehensive test coverage added
    - PRIORITY: High — Core infrastructure change affects all agents
  
  - [x] 0017-004-001-04 - CHUNK - Update simple_chat.py agent implementation
    - SUB-TASKS:
      - Update agent config loading to read `context_management.history_limit` instead of `max_history_messages`
      - Modify SessionDependencies instantiation: `max_history_messages=limit` → `history_limit=limit`
      - Update load_conversation_history function to use standardized parameter names
      - Verify agent-first configuration cascade logic works correctly
    - AUTOMATED-TESTS (2 tests):
      - `test_agent_reads_from_agent_config_first()` - Verify agent prioritizes agent-specific config
      - `test_agent_uses_history_limit_parameter()` - Verify agent uses standardized parameter name
    - MANUAL-TESTS:
      - Test that agent loads config from agent-specific folder first
      - Verify agent uses history_limit parameter instead of old max_history_messages
      - Confirm SessionDependencies instantiation uses new parameter names
    - STATUS: Completed — Implemented agent-first configuration cascade with get_agent_history_limit() function, updated simple_chat.py and load_conversation_history(), all automated tests passing, manual verification successful, proper logging shows cascade source
    - PRIORITY: High — Core agent functionality must use proper config cascade
  
  - [x] 0017-004-001-05 - CHUNK - Implement agent-first configuration cascade logic
    - SUB-TASKS:
      - Create `get_agent_history_limit(agent_name: str) -> int` function in config_loader.py
      - Implement cascade: agent_config.context_management.history_limit → app.yaml chat.history_limit → fallback (50)
      - Add logging to show which config source is used (agent/global/fallback)
      - Update agent_session.py to use new cascade function instead of direct app.yaml access
    - AUTOMATED-TESTS (4 tests):
      - `test_cascade_uses_agent_config_when_available()` - Agent config takes priority
      - `test_cascade_falls_back_to_global_config()` - Falls back to app.yaml when agent config missing
      - `test_cascade_uses_hardcoded_fallback()` - Uses code fallback when both configs missing
      - `test_cascade_logging_shows_source()` - Logging indicates which config source was used
    - MANUAL-TESTS:
      - Test configuration cascade with agent config present, should use agent value
      - Test cascade fallback when agent config missing, should use app.yaml value
      - Test cascade fallback when both configs missing, should use hardcoded fallback
      - Verify logging shows which configuration source was used for each test
    - STATUS: Completed — Implemented get_agent_history_limit() function in config_loader.py with proper agent→global→fallback cascade, added comprehensive logging with config source tracking, updated agent_session.py to use cascade, manual verification shows correct precedence and source logging working perfectly
    - PRIORITY: High — Core requirement for agent-specific configuration override
  
chara  - [x] 0017-004-001-06 - CHUNK - Update configuration loader to handle prompt files
    - SUB-TASKS:
      - Modify `get_agent_config()` in config_loader.py to handle `system_prompt_file` references
      - Add file reading logic with proper error handling for missing prompt files
      - Implement relative path resolution from agent_configs directory
      - Add validation for prompt file existence and readability
      - Cache loaded prompts for performance
    - AUTOMATED-TESTS (3 tests):
      - `test_prompt_file_loading_success()` - Verify external prompt file loads correctly
      - `test_prompt_file_missing_error_handling()` - Verify graceful error handling for missing files
      - `test_relative_path_resolution()` - Verify paths resolve correctly from agent_configs directory
    - MANUAL-TESTS:
      - Verify system_prompt.md loads correctly when referenced in config.yaml
      - Test error handling when prompt file is missing or unreadable
      - Confirm relative paths resolve correctly from agent_configs directory
    - STATUS: Completed — Enhanced config loader with external prompt file support, comprehensive error handling, relative path resolution, and performance caching. All automated tests passing with 100% success rate
    - PRIORITY: Medium — Supports system prompt separation
  
  - [x] 0017-004-001-07 - CHUNK - Update unit tests for parameter standardization
    - SUB-TASKS:
      - Update `test_simple_chat_agent.py` to use `history_limit` instead of `max_history_messages`
      - Update SessionDependencies test cases with new parameter names
      - Add tests for agent-first configuration cascade logic
      - Add tests for external prompt file loading
      - Verify all existing functionality still works with new parameter names
    - AUTOMATED-TESTS (2 tests):
      - `test_parameter_name_standardization()` - Verify old parameter names are completely removed from codebase
      - `test_end_to_end_configuration_behavior()` - Integration test verifying complete config cascade works
    - MANUAL-TESTS:
      - Run full test suite and verify all tests pass with new parameter names
      - Test end-to-end agent behavior to confirm configuration cascade works properly
    - STATUS: Completed — Updated test_simple_chat_agent.py with comprehensive parameter standardization tests, verified SessionDependencies tests use history_limit, confirmed agent-first configuration cascade tests pass, and validated external prompt file loading tests. All 17 unit tests passing with full coverage of parameter standardization requirements
    - PRIORITY: High — Tests must validate new configuration structure
  
  - [x] 0017-004-001-08 - CHUNK - Update documentation and README files (Documentation-focused)
    - SUB-TASKS:
      - Update `backend/README.md` to document agent-first configuration cascade
      - Update configuration examples in README to show standardized parameter names
      - Document system prompt file separation approach
      - Update inline YAML comments to reflect new parameter names
      - Add configuration troubleshooting section for cascade behavior
    - STATUS: Completed — Added comprehensive Configuration Management section to backend/README.md documenting agent-first cascade, standardized parameter names (history_limit), system prompt file separation, and configuration troubleshooting guide. Updated YAML comments and validated all examples work correctly
    - PRIORITY: Medium — Developers need clear configuration guidance
  
  - [x] 0017-004-001-09 - CHUNK - Update memorybank documentation (Documentation-focused)
    - SUB-TASKS:
      - Update `memorybank/architecture/agent-configuration.md` with standardized parameter names
      - Document agent-first configuration cascade in `memorybank/architecture/configuration-reference.md`
      - Update configuration examples in epic documentation to show new parameter names
      - Add system prompt file separation to architectural documentation
      - Update any other memorybank references to old parameter names
    - STATUS: Completed — Updated architectural documentation with agent-first cascade, standardized parameter names (history_limit), external system prompt files, and comprehensive configuration examples. Fixed all memorybank references to old parameter names
    - PRIORITY: Medium — Maintain accurate project documentation
  
  - [x] 0017-004-001-10 - CHUNK - Validation and integration testing
    - SUB-TASKS:
      - Run full test suite to ensure no regressions with parameter name changes
      - Test agent-first configuration cascade with various scenarios (agent override, global fallback, code fallback)
      - Test system prompt loading from external files
      - Verify legacy endpoints still work with app.yaml only (no agent config access)
      - Test error handling for missing/invalid configuration files
    - AUTOMATED-TESTS (8 tests implemented):
      - `test_full_configuration_regression_suite()` - Run complete test suite with new parameter names ✅
      - `test_configuration_cascade_scenarios()` - Test all cascade scenarios (agent->global->fallback) ✅
      - `test_legacy_endpoint_compatibility()` - Verify legacy endpoints unaffected by agent config changes ✅
      - `test_system_prompt_loads_from_external_file()` - Verify system prompt loading from .md files ✅
      - `test_missing_agent_config_graceful_fallback()` - Test graceful fallback for missing configs ✅
      - `test_corrupted_agent_config_fallback()` - Test error handling for corrupted configs ✅
      - `test_no_old_parameter_names_in_codebase()` - Verify old parameter names removed ✅
      - `test_config_files_use_standardized_names()` - Verify config files use standardized names ✅
    - MANUAL-TESTS:
      - Manually verify agent behavior matches expected configuration cascade in browser
      - Test error scenarios with missing/invalid configuration files
      - Confirm system remains stable under various configuration states
    - STATUS: Completed — Created comprehensive validation test suite (test_validation_integration.py) with 8 automated tests covering regression testing, cascade scenarios, legacy compatibility, system prompt loading, error handling, and parameter standardization. Fixed remaining max_history_messages references in simple_chat.py and config.yaml. All tests passing (23 passed, 2 skipped)
    - PRIORITY: High — Ensure system reliability with configuration changes

  - [x] 0017-004-001-11 - CHUNK - Configuration cascade verification tests
    - SUB-TASKS:
      - Create comprehensive test suite for config.yaml → app.yaml → hardcoded cascade
      - Test all configuration parameters that use cascade logic
      - Verify cascade works correctly when config files are missing/corrupted
      - Test cascade behavior with partial configuration files
      - Add performance tests for configuration loading
    - AUTOMATED-TESTS (12 tests implemented):
      - `test_history_limit_cascade_agent_priority()` - Agent config overrides global config ✅
      - `test_history_limit_cascade_global_fallback()` - Global config used when agent config missing ✅
      - `test_history_limit_cascade_hardcoded_fallback()` - Hardcoded fallback when both configs missing ✅
      - `test_model_settings_cascade_agent_priority()` - Agent model overrides global model ✅
      - `test_model_settings_cascade_global_fallback()` - Global model used when agent model missing ✅
      - `test_cascade_with_corrupted_agent_config()` - Graceful fallback when agent config corrupted ✅
      - `test_cascade_with_partial_configurations()` - Mixed scenarios with some values present ✅
      - `test_cascade_performance_benchmarks()` - Configuration loading performance under load ✅
      - `test_cascade_integration_with_real_config_files()` - Integration tests with real files ✅
      - `test_cascade_integration_missing_agent_config()` - Integration test with missing agent config ✅
      - `test_cascade_with_none_values()` - Error handling for None values ✅
      - `test_cascade_with_empty_configs()` - Error handling for empty configurations ✅
    - MANUAL-TESTS:
      - Test configuration cascade behavior in browser with real agent requests
      - Verify cascade works correctly when switching between different agent configurations
      - Test system stability when configuration files are modified during runtime
      - Confirm logging shows correct configuration source for each parameter
    - STATUS: Completed — Comprehensive configuration cascade test suite already implemented in test_configuration_cascade.py with 12 tests covering all cascade scenarios, error handling, performance benchmarks (avg <10ms per call), and integration testing with real config files. All tests passing
    - PRIORITY: High — Critical for reliable configuration behavior
    
**Configuration Standardization Completed:**
```yaml
# app.yaml (STANDARD)
chat:
  history_limit: 50          # ✅ Standard name

# simple_chat/config.yaml (FIXED) 
context_management:
  history_limit: 50          # ✅ Now standardized - matches app.yaml convention
```

- [x] 0017-004-002 - TASK - Agent-First Configuration Cascade
  
  **CURRENT STATE ANALYSIS**: The core cascade infrastructure is already implemented:
  - ✅ `get_agent_history_limit()` function exists in config_loader.py with proper agent→global→fallback cascade
  - ✅ `agent_session.py` uses the centralized cascade function
  - ❌ `simple_chat.py` has duplicate inline cascade logic instead of using the centralized function
  - ❌ Inconsistent cascade usage across codebase creates maintenance issues
  
  **PLAN UPDATE**: Focus on consolidation and consistency rather than initial implementation
  - [x] 0017-004-002-01 - CHUNK - Implement proper cascade logic in agent_session.py
    - SUB-TASKS:
      - Create `get_agent_history_limit(agent_name: str)` function ✅ (Already implemented in config_loader.py)
      - Check `{agent_name}.yaml` config first, then `app.yaml`, then code fallback ✅ (Implemented with proper cascade)
      - Update `load_agent_conversation()` to use agent-first cascade ✅ (Uses get_agent_history_limit)
      - Maintain backward compatibility for legacy endpoints (app.yaml first) ✅ (Legacy endpoints unchanged)
    - STATUS: Completed — Agent session service uses centralized cascade function
  
  - [x] 0017-004-002-02 - CHUNK - Consolidate cascade usage in simple_chat.py
    - SUB-TASKS:
      - ✅ Replace inline cascade logic with centralized `get_agent_history_limit("simple_chat")` calls
      - ✅ Remove duplicate cascade implementation in simple_chat function
      - ✅ Update SessionDependencies creation to use cascade function
      - ✅ Ensure consistent cascade behavior across all agent entry points
    - AUTOMATED-TESTS (5 tests implemented):
      - ✅ `test_simple_chat_uses_centralized_cascade()` - Verify simple_chat uses get_agent_history_limit
      - ✅ `test_cascade_consistency_across_entry_points()` - Verify all entry points use same cascade logic
      - ✅ `test_session_dependencies_cascade_integration()` - Test SessionDependencies uses cascade properly
      - ✅ `test_no_inline_cascade_logic_in_simple_chat()` - Ensure duplicate cascade implementations removed
      - ✅ `test_consistent_cascade_function_usage()` - Verify consistent cascade function usage patterns
    - MANUAL-TESTS:
      - ✅ Verified simple_chat behavior matches expected cascade (agent→global→fallback)
      - ✅ Tested cascade function returns correct value (50) from agent config
      - ✅ Confirmed logging shows cascade source for debugging ("source": "agent_config")
    - STATUS: Completed — Cascade usage consolidated, duplicate logic removed, 5 automated tests passing
    - PRIORITY: Medium — Code consistency and maintainability
  
  - [x] 0017-004-002-03 - CHUNK - Enhanced cascade logging and monitoring
    - SUB-TASKS:
      - ✅ Add comprehensive logging to show which config source was used for each parameter
      - ✅ Create cascade decision audit trail for debugging configuration issues
      - ✅ Add metrics/monitoring for cascade performance and fallback frequency
      - ✅ Document cascade behavior in logs for troubleshooting
    - AUTOMATED-TESTS (9 tests implemented):
      - ✅ `test_cascade_logging_shows_source()` - Verify logs indicate config source used with comprehensive details
      - ✅ `test_cascade_audit_trail()` - Test comprehensive decision logging with multiple attempts
      - ✅ `test_fallback_usage_monitoring()` - Test fallback usage monitoring and alerting
      - ✅ `test_cascade_audit_trail_performance_tracking()` - Test performance tracking and timing
      - ✅ `test_troubleshooting_guide_generation()` - Test troubleshooting guidance generation
      - ✅ `test_cascade_performance_logging()` - Test performance metrics collection
      - ✅ `test_cascade_health_monitoring()` - Test system health monitoring and reporting
      - ✅ `test_enhanced_logging_backward_compatibility()` - Verify enhanced logging maintains compatibility
      - ✅ `test_logging_level_appropriateness()` - Verify logging levels match scenario severity
    - MANUAL-TESTS:
      - ✅ Reviewed logs to confirm cascade decisions are clearly visible with comprehensive audit trails
      - ✅ Tested cascade logging with various configuration scenarios (agent success, global fallback, hardcoded fallback)
      - ✅ Verified performance monitoring and troubleshooting guidance in logs
    - STATUS: Completed — Comprehensive cascade observability with audit trails, performance monitoring, and troubleshooting guidance
    - PRIORITY: Low — Debugging and monitoring improvement

- [x] 0017-004-003 - TASK - Extend Configuration Cascade to Additional Parameters

  **PARAMETER INHERITANCE STRATEGY**:
  ```yaml
  # Generic Cascade Pattern for Any Parameter
  get_agent_parameter(agent_name, "model_settings.temperature", fallback=0.7) →
    1. Check: agent_configs/{agent_name}/config.yaml → model_settings.temperature
    2. Check: app.yaml → llm.temperature  
    3. Use: fallback value (0.7)
  
  # Mixed Inheritance Example (agent config partial)
  agent_configs/simple_chat/config.yaml:
    model_settings:
      model: "kimi-k2"        # Agent-specific override
      # temperature: missing  # Will inherit from global
  
  Result: {model: "kimi-k2", temperature: 0.3, max_tokens: 1024}
         # ↑agent        ↑global         ↑global
  
  # Tool Configuration Inheritance
  get_agent_tool_config("sales_agent", "vector_search") →
    1. Check: agent_configs/sales_agent/config.yaml → tools.vector_search
    2. Check: app.yaml → tools.vector_search (if exists)
    3. Use: tool-specific fallbacks {enabled: false}
  ```
  
  **COMPREHENSIVE MONITORING INTEGRATION**:
  - All cascade functions use CascadeAuditTrail for consistent logging
  - Performance tracking for multi-parameter operations
  - Troubleshooting guidance specific to each parameter type
  - Audit trails show exact inheritance path for debugging
  - [x] 0017-004-003-01 - CHUNK - Model settings cascade implementation
    - SUB-TASKS:
      - ✅ Create generic `get_agent_parameter(agent_name: str, parameter_path: str, fallback: Any)` function for reusable cascade pattern
      - ✅ Create `get_agent_model_settings(agent_name: str)` function using generic infrastructure
      - ✅ Implement cascade for temperature, max_tokens, and other model parameters with mixed inheritance support
      - ✅ Update simple_chat.py to use centralized model settings cascade
      - ✅ Refactor `get_agent_history_limit()` to use generic cascade infrastructure for consistency
      - ✅ Integrate with existing CascadeAuditTrail system for comprehensive logging and monitoring
      - ✅ Define parameter precedence rules and fallback values for each model parameter
      - ✅ Ensure consistent model configuration across all agent types
    - AUTOMATED-TESTS (9 tests implemented):
      - ✅ `test_generic_cascade_infrastructure()` - Verify reusable get_agent_parameter function works for any parameter
      - ✅ `test_generic_cascade_global_fallback()` - Test global config fallback with custom paths
      - ✅ `test_generic_cascade_hardcoded_fallback()` - Test hardcoded fallback when all sources fail
      - ✅ `test_model_settings_cascade_priority()` - Agent model overrides global model
      - ✅ `test_model_settings_cascade_fallback()` - Global model used when agent missing
      - ✅ `test_model_settings_parameter_inheritance()` - Individual parameters cascade independently with mixed inheritance
      - ✅ `test_model_settings_monitoring_integration()` - Verify CascadeAuditTrail integration for model parameters
      - ✅ `test_history_limit_uses_generic_infrastructure()` - Verify history_limit refactoring to generic infrastructure
      - ✅ `test_simple_chat_uses_centralized_model_cascade()` - Verify simple_chat integration with centralized cascade
    - MANUAL-TESTS:
      - ✅ Tested model settings cascade with agent configuration: {'model': 'moonshotai/kimi-k2-0905', 'temperature': 0.3, 'max_tokens': 2000}
      - ✅ Verified comprehensive cascade logging shows model source with full audit trail (3 separate audit logs per parameter)
      - ✅ Confirmed mixed inheritance support - each parameter resolved independently with agent-first priority
      - ✅ Verified performance tracking for multi-parameter cascade operations (sub-millisecond per parameter)
      - ✅ Tested generic infrastructure works for any parameter type (model_settings, tools, context_management)
    - STATUS: Completed — Generic cascade infrastructure implemented with model settings cascade, comprehensive monitoring, and mixed inheritance
    - PRIORITY: Medium — Consistent configuration pattern across all parameters with comprehensive monitoring
  
  - [x] 0017-004-003-02 - CHUNK - Tool configuration cascade
    - SUB-TASKS:
      - ✅ Implement cascade for vector_search, web_search, and other tool configurations using generic infrastructure
      - ✅ Create `get_agent_tool_config(agent_name: str, tool_name: str)` function using generic `get_agent_parameter()`
      - ✅ Update tool initialization to use cascaded configuration with comprehensive monitoring
      - ✅ Add per-agent tool enable/disable capability with audit trail support
      - ✅ Define tool configuration inheritance strategy (enabled/disabled state, parameter overrides)
      - ✅ Integrate with CascadeAuditTrail system for tool configuration decisions
      - ✅ Establish tool configuration precedence rules and fallback values
    - AUTOMATED-TESTS (6 tests - 100% pass):
      - ✅ `test_tool_configuration_cascade()` - Tool configs cascade properly using generic infrastructure
      - ✅ `test_per_agent_tool_enablement()` - Agents can have different tool sets with inheritance
      - ✅ `test_tool_config_monitoring_integration()` - Verify CascadeAuditTrail integration for tool decisions
      - ✅ `test_tool_config_mixed_inheritance()` - Test mixed tool parameter inheritance scenarios
      - ✅ `test_tool_config_fallback_behavior()` - Test fallback values when agent config missing
      - ✅ `test_tool_config_parameter_types()` - Test different parameter types (bool, int, float, string)
    - MANUAL-TESTS:
      - ✅ Verified tool configuration cascade using `get_agent_tool_config("simple_chat", "vector_search")`
      - ✅ Confirmed per-agent tool enable/disable works with comprehensive audit trail logging
      - ✅ Tested mixed tool inheritance - some tools from agent config, others use fallbacks
      - ✅ Verified tool configuration audit trails provide troubleshooting guidance via CascadeAuditTrail
      - ✅ Tested parameter type handling: boolean (enabled), integer (max_results), float (similarity_threshold), string (provider)
    - STATUS: Completed — Per-agent tool configuration control with generic cascade infrastructure, comprehensive monitoring, and mixed inheritance support
    - PRIORITY: Low — Future multi-agent tool differentiation with comprehensive monitoring

  AUTOMATED-TESTS:
  - **Unit Tests**: `test_comprehensive_config_cascade()` - Tests generic cascade infrastructure for all parameter types
  - **Integration Tests**: `test_multi_parameter_cascade_integration()` - Tests multiple parameters cascade together with mixed inheritance
  - **Performance Tests**: `test_cascade_performance_with_multiple_parameters()` - Ensure cascade scales with more parameters
  - **Monitoring Tests**: `test_cascade_audit_trail_integration()` - Verify CascadeAuditTrail system works for all parameter types
  - **Consistency Tests**: `test_cascade_pattern_consistency()` - Ensure all cascade functions use same generic infrastructure
  - **Troubleshooting Tests**: `test_parameter_troubleshooting_guidance()` - Verify troubleshooting guidance for all parameter types

---

# PHASE 1: MVP Core Functionality

Core features that deliver InfoBot's primary value: answering questions using knowledge base, capturing profile data, and emailing summaries.

## Priority 2B: Vector Search Tool 🎯 **IMMEDIATE NEXT PRIORITY**

### 0017-005 - FEATURE - Vector Search Tool
**Status**: Planned

Enable agent to search knowledge base using existing VectorService integration, demonstrated through multi-client demo sites.

- [x] 0017-005-001 - TASK - Multi-Client Demo Site Architecture (3/3 complete)
  
  **RATIONALE**: Create realistic client demo sites to showcase **true multi-tenant architecture** with separate accounts per client. Each client site demonstrates different use cases and data (AgroFresh = agricultural products, Wyckoff Hospital = doctor profiles). This validates Epic 0022's account-level isolation and provides sales-ready demos.
  
  **KEY DECISION**: Use **separate accounts** per client (not just different agents within same account) to properly demonstrate multi-tenant SaaS architecture:
  - ✅ Authentic account-level isolation
  - ✅ Professional client-branded URLs (`/accounts/agrofresh/...`)
  - ✅ Sales-ready demos showcasing tenant separation
  - ✅ Validates multi-tenant code paths thoroughly
  
  - [x] 0017-005-001-01 - CHUNK - Create multi-client folder structure and layouts
    - **PURPOSE**: Establish scalable architecture for multiple client demo sites with separate accounts and client-specific branding
    - **DESIGN**:
      ```
      web/src/
      ├── pages/
      │   ├── index.astro                      # NEW - Demo selector landing page
      │   ├── agrofresh/                       # MOVED - AgroFresh client (existing pages)
      │   │   ├── index.astro                  # MOVED from pages/index.astro
      │   │   ├── about.astro                  # MOVED from pages/about.astro
      │   │   ├── contact.astro                # MOVED from pages/contact.astro
      │   │   ├── crops/                       # MOVED from pages/crops/
      │   │   ├── digital/                     # MOVED from pages/digital/
      │   │   ├── markets/                     # MOVED from pages/markets/
      │   │   ├── products/                    # MOVED from pages/products/
      │   │   ├── resources/                   # MOVED from pages/resources/
      │   │   └── solutions/                   # MOVED from pages/solutions/
      │   │
      │   ├── wyckoff/                         # NEW - Wyckoff Hospital client
      │   │   ├── index.astro                  # NEW - Hospital homepage
      │   │   ├── departments/                 # NEW - Department pages
      │   │   ├── find-a-doctor.astro          # NEW - Doctor search
      │   │   ├── services.astro               # NEW - Medical services
      │   │   └── contact.astro                # NEW - Contact info
      │   │
      │   └── demo/                            # UNCHANGED - Technical demos stay here
      │       ├── simple-chat.astro            # UNCHANGED - Keep in demo/
      │       ├── widget.astro                 # UNCHANGED - Keep in demo/
      │       ├── iframe.astro                 # UNCHANGED - Keep in demo/
      │       └── htmx-chat.html (public/)     # UNCHANGED - Keep in demo/
      │
      ├── layouts/
      │   ├── Layout.astro                     # EXISTING - Base layout (reuse)
      │   ├── AgroFreshLayout.astro           # NEW - AgroFresh branding
      │   └── WyckoffLayout.astro             # NEW - Hospital branding
      │
      ├── components/
      │   ├── shared/                          # NEW FOLDER - Shared components
      │   ├── agrofresh/                       # NEW FOLDER - AgroFresh-specific
      │   │   ├── AgroFreshHeader.astro        # NEW
      │   │   └── AgroFreshFooter.astro        # NEW (includes widget config)
      │   └── wyckoff/                         # NEW FOLDER - Hospital-specific
      │       ├── WyckoffHeader.astro          # NEW
      │       └── WyckoffFooter.astro          # NEW (includes widget config)
      │
      └── styles/
          ├── global.css                       # EXISTING - Base styles (reuse)
          ├── agrofresh.css                   # NEW - Green/orange theme
          └── wyckoff.css                     # NEW - Blue/teal healthcare theme
      ```
    
    - **MULTI-TENANT ARCHITECTURE** (Separate Accounts):
      ```
      ACCOUNT           AGENT INSTANCE           WEBSITE PAGES        VECTOR SEARCH
      ──────────────────────────────────────────────────────────────────────────────────
      agrofresh      →  agro_info_chat1      →  /agrofresh/*      →  Disabled (no data yet)
      wyckoff        →  wyckoff_info_chat1   →  /wyckoff/*        →  Enabled (doctor profiles)
      default_account→  simple_chat1         →  /demo/*           →  Unchanged (technical demos)
      ```
    
    - **WIDGET INTEGRATION VIA FOOTERS**:
      ```astro
      <!-- components/agrofresh/AgroFreshFooter.astro -->
      <footer><!-- Footer content --></footer>
      <script is:inline>
        window.__SALIENT_WIDGET_CONFIG = {
          account: 'agrofresh',
          agent: 'agro_info_chat1',
          backend: 'http://localhost:8000',
          allowCross: true,
          debug: import.meta.env.DEV
        };
      </script>
      <script src="/widget/chat-widget.js"></script>
      
      <!-- components/wyckoff/WyckoffFooter.astro -->
      <footer><!-- Footer content --></footer>
      <script is:inline>
        window.__SALIENT_WIDGET_CONFIG = {
          account: 'wyckoff',
          agent: 'wyckoff_info_chat1',
          backend: 'http://localhost:8000',
          allowCross: true,
          debug: import.meta.env.DEV
        };
      </script>
      <script src="/widget/chat-widget.js"></script>
      ```
    
    - **FILE ORGANIZATION SUMMARY**:
      - **MOVE**: All existing pages from `pages/*.astro` → `pages/agrofresh/*.astro`
      - **STAY UNCHANGED**: `pages/demo/` folder and all contents (technical demos)
      - **CREATE NEW**: `pages/wyckoff/` folder (hospital pages in next chunk)
      - **CREATE NEW**: Client-specific layouts, components, styles
      - **CREATE NEW**: Root `pages/index.astro` (demo selector)
    
    - SUB-TASKS:
      - **DATABASE SETUP**:
        - Create `agrofresh` account record in database: `INSERT INTO accounts (slug, name) VALUES ('agrofresh', 'AgroFresh Solutions');`
        - Create `wyckoff` account record in database: `INSERT INTO accounts (slug, name) VALUES ('wyckoff', 'Wyckoff Hospital');`
        - Verify `default_account` already exists for `/demo/` pages
      
      - **FOLDER STRUCTURE**:
        - Create `pages/agrofresh/` folder
        - Create `pages/wyckoff/` folder (empty for now)
        - Create `components/shared/` folder
        - Create `components/agrofresh/` folder
        - Create `components/wyckoff/` folder
      
      - **MOVE EXISTING PAGES** (AgroFresh):
        - Move `pages/index.astro` → `pages/agrofresh/index.astro`
        - Move `pages/about.astro` → `pages/agrofresh/about.astro`
        - Move `pages/contact.astro` → `pages/agrofresh/contact.astro`
        - Move `pages/crops/` folder → `pages/agrofresh/crops/`
        - Move `pages/digital/` folder → `pages/agrofresh/digital/`
        - Move `pages/markets/` folder → `pages/agrofresh/markets/`
        - Move `pages/products/` folder → `pages/agrofresh/products/`
        - Move `pages/resources/` folder → `pages/agrofresh/resources/`
        - Move `pages/solutions/` folder → `pages/agrofresh/solutions/`
        - **IMPORTANT**: Do NOT move `pages/demo/` folder - it stays in place
      
      - **UPDATE MOVED PAGES**:
        - Update internal navigation links in moved pages (e.g., `/about` → `/agrofresh/about`)
        - Update layout imports to use `AgroFreshLayout` instead of `Layout`
        - Verify all relative asset paths still work after move
      
      - **CREATE NEW LAYOUTS**:
        - Create `layouts/AgroFreshLayout.astro` with AgroFresh branding (uses AgroFreshHeader/Footer)
        - Create `layouts/WyckoffLayout.astro` with hospital branding (uses WyckoffHeader/Footer)
      
      - **CREATE NEW COMPONENTS**:
        - Create `components/agrofresh/AgroFreshHeader.astro` with AgroFresh navigation
        - Create `components/agrofresh/AgroFreshFooter.astro` with widget config (agrofresh/agro_info_chat1)
        - Create `components/wyckoff/WyckoffHeader.astro` with hospital navigation
        - Create `components/wyckoff/WyckoffFooter.astro` with widget config (wyckoff/wyckoff_info_chat1)
      
      - **CREATE NEW STYLES**:
        - Create `styles/agrofresh.css` with green/orange theme (#2E7D32, #FF6F00)
        - Create `styles/wyckoff.css` with blue/teal healthcare theme (#0277BD, #00838F)
      
      - **CREATE DEMO SELECTOR**:
        - Create root `pages/index.astro` as demo selector landing page
        - Add cards/links for "AgroFresh Solutions" → `/agrofresh/`
        - Add cards/links for "Wyckoff Hospital" → `/wyckoff/`
        - Add link to "Technical Demos" → `/demo/simple-chat`
        - Include branding logos and descriptions for each client
    
    - AUTOMATED-TESTS: `web/tests/test_multi_client_structure.spec.ts` (Playwright)
      - `test_demo_selector_page_loads()` - Root index loads with 3 demo options (AgroFresh, Wyckoff, Technical)
      - `test_agrofresh_site_accessible()` - All AgroFresh pages load correctly
      - `test_agrofresh_navigation_links()` - Internal links use `/agrofresh/` prefix
      - `test_wyckoff_site_accessible()` - Wyckoff site accessible (empty until chunk 02)
      - `test_demo_folder_unchanged()` - All `/demo/*` pages still work unchanged
      - `test_layouts_apply_correctly()` - Client-specific layouts render with correct headers/footers
      - `test_styles_isolated()` - AgroFresh uses green/orange, Wyckoff uses blue/teal
      - `test_widget_on_agrofresh_pages()` - Widget configured with agrofresh/agro_info_chat1
    
    - MANUAL-TESTS:
      - Navigate to `http://localhost:4321/` and verify demo selector shows 3 options
      - Click "AgroFresh Solutions", verify redirects to `/agrofresh/` with green/orange branding
      - Test AgroFresh navigation: verify all links work with `/agrofresh/` prefix
      - Open chat widget on AgroFresh page, verify backend URL uses `/accounts/agrofresh/agents/agro_info_chat1/...`
      - Click "Wyckoff Hospital", verify redirects to `/wyckoff/` (placeholder page)
      - Click "Technical Demos", verify redirects to `/demo/simple-chat` (unchanged)
      - Test `/demo/widget`, `/demo/htmx-chat.html` still work unchanged
      - Verify styles are isolated: AgroFresh ≠ Wyckoff ≠ Demo pages
      - Test responsive design on all client sites
    
    - STATUS: Completed — Multi-client folder structure implemented with separate accounts (agrofresh, wyckoff), client-specific layouts/components, widget integration via footers, and demo selector landing page
    - PRIORITY: High — Required before implementing Wyckoff hospital pages
  
  - [x] 0017-005-001-02 - CHUNK - Create Wyckoff Hospital demo pages
    - **PURPOSE**: Build realistic hospital demo site with pages showcasing vector search for doctor profiles
    - **PAGES TO CREATE** (all NEW):
      - `wyckoff/index.astro` - Hospital homepage with services overview
      - `wyckoff/departments/index.astro` - Department directory
      - `wyckoff/departments/cardiology.astro` - Cardiology department info
      - `wyckoff/departments/neurology.astro` - Neurology department info
      - `wyckoff/departments/emergency.astro` - Emergency services info
      - `wyckoff/find-a-doctor.astro` - Doctor search page (primary vector search demo)
      - `wyckoff/services.astro` - Medical services overview
      - `wyckoff/contact.astro` - Contact information
    
    - **CHAT WIDGET INTEGRATION**:
      - All pages inherit widget from `WyckoffFooter.astro` component
      - Widget configured with `wyckoff/wyckoff_info_chat1` agent (separate account)
      - Widget uses shadow DOM (production-ready from 0022-001-004-01)
      - Configuration in footer: `{ account: 'wyckoff', agent: 'wyckoff_info_chat1', backend: 'http://localhost:8000' }`
    
    - **SUGGESTED QUESTIONS** (displayed on relevant pages):
      - Find a Doctor page: "Find me a Spanish-speaking cardiologist", "Show me neurology specialists", "Which doctors accept Medicare?"
      - Departments: "Tell me about your cardiology department", "What services does neurology offer?"
      - Services: "What imaging services do you offer?", "Do you have an urgent care center?"
    
    - SUB-TASKS:
      - Create 8 Wyckoff hospital pages using `WyckoffLayout`
      - Add hospital-themed content (services, departments, contact info)
      - Widget automatically included via `WyckoffFooter` (configured with wyckoff/wyckoff_info_chat1)
      - Add "Suggested Questions" UI component with clickable example queries
      - Add hospital imagery (stock photos or placeholders from Unsplash)
      - Create department-specific navigation menus in `WyckoffHeader`
      - Add "Find a Doctor" search interface mockup (to complement chat widget)
      - Test chat widget on all pages with example questions
    
    - AUTOMATED-TESTS: `web/tests/test_wyckoff_site.spec.ts` (Playwright)
      - `test_all_wyckoff_pages_load()` - All 8 pages load without errors
      - `test_chat_widget_on_all_pages()` - Chat widget present on all pages
      - `test_widget_configured_correctly()` - Widget uses wyckoff/wyckoff_info_chat1 agent
      - `test_widget_backend_urls()` - Widget hits `/accounts/wyckoff/agents/wyckoff_info_chat1/...` endpoints
      - `test_suggested_questions_clickable()` - Example questions trigger chat
      - `test_navigation_between_pages()` - All internal links work with `/wyckoff/` prefix
      - `test_department_pages_unique()` - Each department has unique content
    
    - MANUAL-TESTS:
      - Navigate through all 8 Wyckoff pages, verify content and branding
      - Test chat widget on each page: send example questions
      - Verify suggested questions appear on relevant pages
      - Click suggested questions, verify chat widget pre-fills and sends
      - Test "Find a Doctor" page: ask "Find a Spanish-speaking cardiologist"
      - Verify backend hits correct endpoint: `/accounts/wyckoff/agents/wyckoff_info_chat1/stream`
      - Verify hospital theme (blue/teal colors, medical imagery) consistent across pages
      - Test responsive design on mobile/tablet viewports
      - Verify chat history persists across page navigation within Wyckoff site
    
    - STATUS: Completed — 8 hospital pages created with SuggestedQuestions component, Find a Doctor page designed for vector search demo, all pages integrated with wyckoff/wyckoff_info_chat1 agent via WyckoffFooter
    - PRIORITY: High — Primary demo for vector search tool
  
  - [x] 0017-005-001-03 - CHUNK - Configure agent instances for multi-client demos
    - **PURPOSE**: Create separate account configs and agent instances matching client contexts, enabling proper multi-tenant isolation
    
    - **BACKEND CONFIGURATION STRUCTURE**:
      ```
      backend/config/agent_configs/
      ├── agrofresh/                           # NEW ACCOUNT
      │   └── agro_info_chat1/                 # NEW AGENT INSTANCE
      │       ├── config.yaml
      │       └── system_prompt.md
      ├── wyckoff/                             # NEW ACCOUNT
      │   └── wyckoff_info_chat1/              # NEW AGENT INSTANCE
      │       ├── config.yaml
      │       └── system_prompt.md
      └── default_account/                     # EXISTING (unchanged for /demo/)
          └── simple_chat1/
              ├── config.yaml
              └── system_prompt.md
      ```
    
    - **AGENT CONFIGURATIONS**:
      ```yaml
      # agrofresh/agro_info_chat1/config.yaml (NEW)
      agent_type: "simple_chat"
      account: "agrofresh"
      instance_name: "agro_info_chat1"
      display_name: "AgroFresh Assistant"
      system_prompt: "agrofresh-focused prompt"
      tools:
        vector_search:
          enabled: false    # No vector data for AgroFresh yet
        web_search:
          enabled: false
      
      # wyckoff/wyckoff_info_chat1/config.yaml (NEW)
      agent_type: "simple_chat"
      account: "wyckoff"
      instance_name: "wyckoff_info_chat1"
      display_name: "Wyckoff Hospital Assistant"
      system_prompt: "hospital-focused prompt"
      tools:
        vector_search:
          enabled: true     # Hospital doctor profiles in Pinecone
          max_results: 5
          similarity_threshold: 0.7
        web_search:
          enabled: false
      
      # default_account/simple_chat1/config.yaml (UNCHANGED)
      # Keep existing config for /demo/ technical demos
      ```
    
    - SUB-TASKS:
      - **CREATE AGENT CONFIGS**:
        - Create `backend/config/agent_configs/agrofresh/agro_info_chat1/config.yaml`
        - Create `backend/config/agent_configs/agrofresh/agro_info_chat1/system_prompt.md` (agricultural context)
        - Create `backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml`
        - Create `backend/config/agent_configs/wyckoff/wyckoff_info_chat1/system_prompt.md` (healthcare context)
      
      - **VERIFY DATABASE**:
        - Verify `agrofresh` and `wyckoff` account records exist (created in chunk 01)
        - Verify `default_account` still exists for `/demo/` pages
      
      - **VECTOR SEARCH SETUP**:
        - Verify Pinecone has hospital doctor profile data loaded (from `doctors_profile.csv`)
        - Test vector search query returns relevant doctor profiles for wyckoff/hospital_chat1
        - Verify agro_chat1 has vector_search disabled (no data loaded yet)
      
      - **SYSTEM PROMPTS**:
        - Write AgroFresh-focused system prompt (agricultural products, crop management context)
        - Write hospital-focused system prompt (medical services, doctor referrals, healthcare information)
      
      - **LOGGING & ATTRIBUTION**:
        - Add logging to show which account/agent is being used per request
        - Verify LLM request tracking includes account_id and agent_instance_id
        - Verify session/message attribution to correct account
    
    - AUTOMATED-TESTS: `backend/tests/integration/test_multi_client_agents.py`
      - `test_agrofresh_agent_loads()` - agrofresh/agro_info_chat1 config loads successfully
      - `test_wyckoff_agent_loads()` - wyckoff/wyckoff_info_chat1 config loads successfully
      - `test_demo_agent_unchanged()` - default_account/simple_chat1 still works for /demo/
      - `test_agrofresh_vector_disabled()` - agro_info_chat1 has vector_search disabled
      - `test_wyckoff_vector_enabled()` - wyckoff_info_chat1 has vector_search enabled
      - `test_agent_display_names()` - Correct display names for each agent
      - `test_system_prompts_differ()` - Each agent has appropriate context-specific system prompt
      - `test_account_isolation()` - Sessions/messages properly attributed to correct accounts
    
    - MANUAL-TESTS:
      - Send request to `/accounts/agrofresh/agents/agro_info_chat1/chat`: verify agent loads, vector search not used
      - Send request to `/accounts/wyckoff/agents/wyckoff_info_chat1/chat`: verify agent loads, vector search works
      - Ask wyckoff_info_chat1: "Find a Spanish-speaking cardiologist", verify uses vector search
      - Check logs: verify account and agent instance attribution appears correctly
      - Verify Pinecone contains hospital doctor data (query manually)
      - Check `llm_requests` table: verify account_id and agent_instance_id populated correctly
      - Test chat widget on `/agrofresh/`: verify hits correct backend endpoints
      - Test chat widget on `/wyckoff/`: verify hits correct backend endpoints
      - Verify `/demo/` pages still use default_account/simple_chat1 unchanged
    
    - STATUS: Completed — Agent configurations created for agrofresh/agro_info_chat1 (vector search disabled) and wyckoff/wyckoff_info_chat1 (vector search enabled), system prompts tailored to client contexts, database accounts verified
    - PRIORITY: High — Required for vector search to work correctly per client and demonstrate true multi-tenant isolation

### Multi-Model Configuration Summary

**Purpose**: Each agent instance is configured with a different LLM model to demonstrate multi-model support and enable comparative testing across different model families and providers.

**Agent Model Assignments**:

| Account | Agent Instance | Model | Provider | Purpose |
|---------|----------------|-------|----------|---------|
| **agrofresh** | agro_info_chat1 | `deepseek/deepseek-chat-v3-0324` | DeepSeek | Agricultural products info, cost-effective reasoning |
| **wyckoff** | wyckoff_info_chat1 | `qwen/qwen3-235b-a22b-thinking-2507` | Qwen/Alibaba | Healthcare info with advanced reasoning, doctor search |
| **default_account** | simple_chat1 | `moonshotai/kimi-k2-0905` | Moonshot AI | General testing, reliable baseline |
| **default_account** | simple_chat2 | `openai/gpt-oss-120b` | OpenAI | Alternative testing instance |
| **acme** | acme_chat1 | `mistralai/mistral-small-3.2-24b-instruct` | Mistral AI | Efficient multilingual model (higher temp: 0.5) |
| **legacy** | simple_chat | `meta-llama/llama-4-scout` | Meta | Legacy non-multi-tenant agent |

**Key Benefits**:
- ✅ **Model diversity**: Tests across 6 different model families (DeepSeek, Qwen, Moonshot, OpenAI, Mistral, Meta)
- ✅ **Provider diversity**: Tests multiple LLM providers via OpenRouter
- ✅ **Cost optimization**: Different models for different use cases (e.g., DeepSeek for cost-sensitive agricultural info)
- ✅ **Performance comparison**: Each client can evaluate which model works best for their domain
- ✅ **Regression testing**: Multi-model configuration ensures agent code works across different LLM capabilities
- ✅ **Fallback options**: If one model has issues, can quickly switch agents to different model

**Configuration Notes**:
- All models use `temperature: 0.3` (except acme_chat1: 0.5) for consistent, focused responses
- All models use `max_tokens: 2000` for cost control
- Models accessed via OpenRouter for unified API and cost tracking
- Each agent's system prompt tailored to model strengths and use case

This multi-model architecture validates that the Pydantic AI implementation is model-agnostic and works reliably across different LLM providers and capabilities.

---

- [x] 0017-005-002 - TASK - Vector Search Tool Implementation
  
  **TESTING CONFIGURATION**:
  - **Agent**: `wyckoff/wyckoff_info_chat1` (vector search enabled)
  - **Pinecone Index**: `wyckoff-poc-01`
  - **Namespace**: `__default__` (Pinecone's default namespace identifier)
  - **Model**: `qwen/qwen3-235b-a22b-thinking-2507` (advanced reasoning for medical queries)
  - **Frontend**: `http://localhost:4321/wyckoff/find-a-doctor` (dedicated vector search demo page)
  
  **ARCHITECTURE DECISIONS**:
  - **Per-Agent-Instance Pinecone Settings**: Each agent instance can have its own `index_name` + `namespace` (optionally `api_key` for true isolation)
  - **Simplified Scope**: Use index + namespace for multi-tenancy; reserve multiple Pinecone projects for prod/dev environment separation only
  - **Connection Strategy**: Single PineconeClient instance per unique (api_key, index_host) pair - **no connection pooling issues**
  - **Fallback**: If agent has no vector_search config, skip tool registration entirely (tool won't be available to LLM)
  
  **RATIONALE**:
  - Wyckoff agent config already has `vector_search.enabled: true` but settings are placeholders
  - Current global config (`pinecone_config.py`) doesn't support per-agent settings
  - Need to make VectorService agent-instance-aware by passing config from agent's YAML
  - **Vector search queries WordPress content** (hospital services, departments, general info) already loaded in `wyckoff-poc-01` index
  - **NOTE**: Doctor profile search is separate (Epic 0023, PostgreSQL-based, different `@agent.tool`)

  - [ ] 0017-005-002-01 - CHUNK - Per-agent Pinecone configuration loader
    - **PURPOSE**: Load agent-specific Pinecone settings from agent config YAML, enable per-agent index/namespace isolation
    
    - SUB-TASKS:
      
      **Step 1**: Update `backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml`
      ```yaml
      # Existing settings...
      tools:
        vector_search:
          enabled: true
          max_results: 5
          similarity_threshold: 0.7
          # NEW: Per-agent Pinecone settings
          pinecone:
            index_name: "wyckoff-poc-01"          # Agent-specific index
            namespace: "__default__"               # Pinecone's default namespace
            api_key_env: "PINECONE_API_KEY"       # Optional: agent-specific API key via env var
            # index_host will be auto-discovered via Pinecone.list_indexes() or can be explicit:
            # index_host: "https://wyckoff-poc-01-xyz.svc.region.pinecone.io"
          # Model/embedding settings (use same as global for now)
          embedding:
            model: "text-embedding-3-small"       # OpenAI embedding model
            dimensions: 1536
      ```
      
      **Step 2**: Create `backend/app/services/agent_pinecone_config.py`
```python
      from typing import Optional, Dict, Any
      from dataclasses import dataclass
      import os
      from pinecone import Pinecone
      
      @dataclass
      class AgentPineconeConfig:
          """Per-agent Pinecone configuration"""
          api_key: str
          index_name: str
          index_host: str  # Auto-discovered or explicit
          namespace: str
          embedding_model: str
          dimensions: int
          
      def load_agent_pinecone_config(
          instance_config: Dict[str, Any]
      ) -> Optional[AgentPineconeConfig]:
          """
          Load Pinecone config from agent's config.yaml.
          Returns None if vector_search is disabled or missing pinecone settings.
          """
          vector_config = instance_config.get("tools", {}).get("vector_search", {})
          
          if not vector_config.get("enabled", False):
              return None
          
          pinecone_config = vector_config.get("pinecone", {})
          if not pinecone_config:
              logger.warning("vector_search enabled but no pinecone config found")
              return None
          
          # Get API key from env var (supports per-agent keys)
          api_key_env = pinecone_config.get("api_key_env", "PINECONE_API_KEY")
          api_key = os.getenv(api_key_env)
          if not api_key:
              raise ValueError(f"Pinecone API key not found in env: {api_key_env}")
          
          index_name = pinecone_config["index_name"]
          namespace = pinecone_config.get("namespace", "__default__")
          
          # Auto-discover index host if not explicit
          index_host = pinecone_config.get("index_host")
          if not index_host:
              pc = Pinecone(api_key=api_key)
              index_info = pc.describe_index(index_name)
              index_host = index_info.host
          
          embedding_config = vector_config.get("embedding", {})
          
          return AgentPineconeConfig(
              api_key=api_key,
              index_name=index_name,
              index_host=index_host,
              namespace=namespace,
              embedding_model=embedding_config.get("model", "text-embedding-3-small"),
              dimensions=embedding_config.get("dimensions", 1536)
          )
      ```
      
      **Step 3**: Update `backend/app/services/vector_service.py`
      - Add optional `agent_pinecone_config` parameter to `VectorService.__init__()`
      - If provided, create a separate PineconeClient with agent-specific settings
      - Otherwise, fall back to global config (backward compatible)
      - Update `query_similar()` to use agent's namespace from config
      
      **Step 4**: Update `backend/app/services/pinecone_client.py`
      - Add factory method: `create_from_agent_config(agent_config: AgentPineconeConfig)`
      - Enables multiple PineconeClient instances for different agents
      - Each client manages its own connection to (api_key, index_host) pair
      
    - AUTOMATED-TESTS: `backend/tests/unit/test_agent_pinecone_config.py`
      - `test_load_config_enabled()` - Load valid config with all fields
      - `test_load_config_disabled()` - Returns None when vector_search disabled
      - `test_load_config_missing()` - Returns None when pinecone section missing
      - `test_load_config_auto_discover_host()` - Host auto-discovery works
      - `test_load_config_explicit_host()` - Uses explicit host when provided
      - `test_load_config_custom_api_key_env()` - Custom API key env var works
      - `test_vector_service_with_agent_config()` - VectorService uses agent config
    
    - MANUAL-TESTS:
      - Update wyckoff config.yaml with correct settings
      - Run: `python -c "from app.services.agent_pinecone_config import load_agent_pinecone_config; import yaml; cfg = yaml.safe_load(open('backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml')); print(load_agent_pinecone_config(cfg))"`
      - Verify: Prints AgentPineconeConfig with correct index_name=wyckoff-poc-01, namespace=__default__
      - Check logs: Should show index host auto-discovered if not explicit
    
    - STATUS: ✅ COMPLETE — Agent-specific Pinecone configuration loading (Commits: da887ae, 379e59b)
    - PRIORITY: High — Foundation for all vector search functionality
  
  - [x] 0017-005-002-02 - CHUNK - Pydantic AI @agent.tool for vector search
    - **PURPOSE**: Register vector search as a Pydantic AI tool, enable LLM to search knowledge base when needed
    
    - SUB-TASKS:
      
      **Step 1**: Create `backend/app/agents/tools/vector_tools.py`
      ```python
      from pydantic_ai import RunContext
      from typing import Optional
      import logging
      
      from app.agents.models.dependencies import SessionDependencies
      from app.services.vector_service import VectorService, VectorQueryResponse
      from app.services.agent_pinecone_config import AgentPineconeConfig
      
      logger = logging.getLogger(__name__)
      
      async def vector_search(
          ctx: RunContext[SessionDependencies],
          query: str,
          max_results: Optional[int] = None
      ) -> str:
          """
          Search the knowledge base for relevant information using vector similarity.
          
          Args:
              query: Natural language query to search for
              max_results: Maximum number of results (defaults to agent config)
          
          Returns:
              Formatted search results or message if no results found
          """
          agent_config = ctx.deps.agent_config
          session_id = ctx.deps.session_id
          
          # Get vector search config
          vector_config = agent_config.get("tools", {}).get("vector_search", {})
          if not vector_config.get("enabled", False):
              return "Vector search is not enabled for this agent."
          
          # Load agent's Pinecone config
          from app.services.agent_pinecone_config import load_agent_pinecone_config
          pinecone_config = load_agent_pinecone_config(agent_config)
          if not pinecone_config:
              logger.error(f"Vector search enabled but config missing: session={session_id}")
              return "Vector search configuration error."
          
          # Create agent-specific VectorService
          from app.services.pinecone_client import PineconeClient
          pinecone_client = PineconeClient.create_from_agent_config(pinecone_config)
          vector_service = VectorService(pinecone_client=pinecone_client)
          
          # Query parameters: Configuration cascade (agent → app.yaml → code)
          # 1. Check if LLM explicitly passed max_results parameter
          # 2. Fall back to agent config
          # 3. Fall back to app.yaml global config
          # 4. Fall back to hardcoded default
          from app.config import app_config
          global_vector_config = app_config.get("vector", {}).get("search", {})
          
          top_k = (
              max_results or  # LLM parameter (highest priority)
              vector_config.get("max_results") or  # Agent config
              global_vector_config.get("max_results", 5)  # app.yaml → code default
          )
          similarity_threshold = (
              vector_config.get("similarity_threshold") or  # Agent config
              global_vector_config.get("similarity_threshold", 0.7)  # app.yaml → code default
          )
          
          logger.info({
              "event": "vector_search_start",
              "session_id": session_id,
              "query": query,
              "index": pinecone_config.index_name,
              "namespace": pinecone_config.namespace,
              "top_k": top_k,
              "threshold": similarity_threshold
          })
          
          # Perform search
          try:
              response: VectorQueryResponse = await vector_service.query_similar(
                  query_text=query,
                  top_k=top_k,
                  similarity_threshold=similarity_threshold,
                  namespace=pinecone_config.namespace
              )
              
              logger.info({
                  "event": "vector_search_complete",
                  "session_id": session_id,
                  "results_count": response.total_results,
                  "query_time_ms": response.query_time_ms
              })
              
              # Format results for LLM consumption
              if not response.results:
                  return f"No relevant information found in knowledge base for query: '{query}'"
              
              formatted_lines = [
                  f"Found {response.total_results} relevant result(s) in knowledge base:\n"
              ]
              
              for i, result in enumerate(response.results, 1):
                  formatted_lines.append(f"{i}. {result.text}")
                  formatted_lines.append(f"   Relevance Score: {result.score:.3f}")
                  
                  # Include metadata if present (e.g., page title, URL, category from WordPress)
                  if result.metadata:
                      metadata_str = ", ".join(
                          f"{k}: {v}" for k, v in result.metadata.items() 
                          if k not in ["text", "created_at", "embedding_model"]
                      )
                      if metadata_str:
                          formatted_lines.append(f"   Details: {metadata_str}")
                  
                  formatted_lines.append("")  # Blank line between results
              
              return "\n".join(formatted_lines)
              
          except Exception as e:
              logger.error({
                  "event": "vector_search_error",
                  "session_id": session_id,
                  "error": str(e)
              })
              return f"Vector search encountered an error. Please try rephrasing your query."
      ```
      
      **Step 2**: Update `backend/app/agents/simple_chat.py`
      - Import `vector_tools.vector_search`
      - In `create_agent()` function (or equivalent), conditionally register tool:
        ```python
        from app.agents.tools import vector_tools
        
        # After agent creation...
        vector_config = instance_config.get("tools", {}).get("vector_search", {})
        if vector_config.get("enabled", False):
            agent.tool(vector_tools.vector_search)
            logger.info(f"Vector search tool registered for {instance_config['instance_name']}")
        ```
      
      **Step 3**: Update `SessionDependencies` in `backend/app/agents/models/dependencies.py`
      - Add `agent_config: Dict[str, Any]` field (pass full config for tool access)
      - Update all `SessionDependencies` instantiations in `account_agents.py` to include `agent_config=instance_config`
      
      **Step 4**: Update wyckoff system prompt
      - Add guidance: "You have access to a vector search tool to search hospital information from our website. Use it when users ask about hospital services, departments, facilities, or general information. For finding specific doctors, use the profile_search tool (separate tool, Epic 0023)."
      
    - AUTOMATED-TESTS: `backend/tests/integration/test_vector_search_tool.py`
      - `test_vector_search_tool_enabled()` - Tool registered when enabled
      - `test_vector_search_tool_disabled()` - Tool NOT registered when disabled
      - `test_vector_search_query()` - Mock VectorService, verify formatted output
      - `test_vector_search_empty_results()` - Handles no results gracefully
      - `test_vector_search_uses_agent_config()` - Uses agent's index/namespace
      - `test_vector_search_error_handling()` - Catches and logs Pinecone errors
    
    - MANUAL-TESTS:
      - Navigate to `http://localhost:4321/wyckoff/find-a-doctor`
      - Send query: "What cardiology services does Wyckoff offer?"
      - Verify: Agent calls vector_search tool (check logs)
      - Verify: Response includes formatted WordPress content results with relevance scores
      - Send query: "Tell me about the emergency department" (test department info)
      - Send query: "What are visiting hours?" (test general hospital info)
      - Send query not in knowledge base: "What's the weather?" (test no results)
      - Check Logfire: Verify `vector_search_start` and `vector_search_complete` events
      - Check `llm_requests` table: Verify tool calls tracked in request_body
      - **NOTE**: Doctor profile queries ("Find Spanish-speaking cardiologist") will use Epic 0023's profile_search tool (separate, PostgreSQL-based)
    
    - STATUS: ✅ COMPLETE — Pydantic AI tool integration (Commit: 379e59b)
    - PRIORITY: High — Core functionality for vector search demo
  
  - [x] 0017-005-002-03 - CHUNK - End-to-end testing with real Pinecone data
    - **PURPOSE**: Verify vector search works with actual Pinecone index (already populated with WordPress content), test multi-agent isolation
    
    - **DATA SOURCE**: 
      - **Index `wyckoff-poc-01`** already populated with Wyckoff Hospital WordPress site content
      - **Separate process** (not part of this epic) handles WordPress → Pinecone ingestion
      - **Project documentation**: `/Users/arifsufi/Documents/GitHub/OpenThought/siphon/siphon-wp-xml-to-md-vdb/memorybank`
      - **NOTE**: Doctor profile data is in PostgreSQL (Epic 0023), NOT in this Pinecone index
    
    - SUB-TASKS:
      
      **Step 1**: Verify index connectivity and content
      ```python
      # backend/scripts/verify_wyckoff_index.py
      import asyncio
      from app.services.agent_pinecone_config import load_agent_pinecone_config
      from app.services.pinecone_client import PineconeClient
      import yaml
      
      async def verify_index():
          # Load wyckoff agent config
          with open("backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml") as f:
              agent_config = yaml.safe_load(f)
          
          pinecone_config = load_agent_pinecone_config(agent_config)
          pinecone_client = PineconeClient.create_from_agent_config(pinecone_config)
          
          # Check index stats
          stats = await pinecone_client.index.describe_index_stats()
          print(f"Index: {pinecone_config.index_name}")
          print(f"Namespace: {pinecone_config.namespace}")
          print(f"Total vectors: {stats.total_vector_count}")
          print(f"Dimension: {stats.dimension}")
          
          # Sample query to verify connectivity
          from app.services.vector_service import VectorService
          vector_service = VectorService(pinecone_client=pinecone_client)
          
          test_query = "cardiology services"
          results = await vector_service.query_similar(
              query_text=test_query,
              top_k=3,
              namespace=pinecone_config.namespace
          )
          
          print(f"\nTest query: '{test_query}'")
          print(f"Results found: {results.total_results}")
          for i, result in enumerate(results.results, 1):
              print(f"{i}. Score: {result.score:.3f}")
              print(f"   Text: {result.text[:100]}...")
      
      if __name__ == "__main__":
          asyncio.run(verify_index())
      ```
      
      **Step 2**: Create comprehensive test suite
      - `backend/tests/integration/test_wyckoff_vector_search_e2e.py`
      - Test queries: "cardiology services", "emergency department", "visiting hours", "maternity ward"
      - Verify: Results are WordPress content (not doctor profiles)
      - Verify: Similarity scores are reasonable (> 0.7 for good matches)
      - Verify: Metadata (page title, URL, category) is preserved from WordPress
      - **NOTE**: Doctor profile queries will fail in this index (by design - they use Epic 0023)
      
      **Step 3**: Test multi-agent isolation
      - Verify agrofresh agent (vector_search disabled) does NOT have tool
      - Verify default_account/simple_chat1 (no vector config) does NOT have tool
      - Verify wyckoff agent (enabled) HAS tool and queries correct index
      - Attempt to query from wrong agent, verify graceful failure
      
      **Step 4**: Performance testing
      - Measure query latency (should be < 500ms for 5 results)
      - Test with existing WordPress content vectors in index
      - Verify no memory leaks with repeated queries
      - Check Pinecone request logs for errors
    
    - AUTOMATED-TESTS: `backend/tests/integration/test_wyckoff_vector_search_e2e.py`
      - `test_wyckoff_agent_has_vector_tool()` - Tool registered
      - `test_vector_search_cardiology_services()` - Find cardiology department info
      - `test_vector_search_emergency_dept()` - Find emergency department info
      - `test_vector_search_visiting_hours()` - Find general hospital info
      - `test_vector_search_no_match()` - Handles no results (e.g., "weather")
      - `test_agrofresh_no_vector_tool()` - Other agents isolated (no vector search)
      - `test_query_latency()` - Performance < 500ms
    
    - MANUAL-TESTS:
      - Run verification script: `python backend/scripts/verify_wyckoff_index.py` (check connectivity & content)
      - Verify Pinecone console shows vectors in wyckoff-poc-01 index (should already be populated)
      - Open `http://localhost:4321/wyckoff/find-a-doctor`
      - Test queries with hospital/service keywords:
        - "What cardiology services do you offer?"
        - "Tell me about your emergency department"
        - "Do you have a maternity ward?"
        - "What are visiting hours?"
        - "Information about surgical services"
      - Verify suggested questions on page trigger vector search
      - Verify responses contain WordPress content (not doctor profiles)
      - Open `http://localhost:4321/agrofresh/` - verify no vector search (tool not available)
      - Check Logfire for all vector_search events (start/complete/error)
      - Verify `llm_requests` table has tool calls in request_body
      - **NOTE**: Doctor profile queries ("Find Spanish-speaking cardiologist") should gracefully indicate they're not available in this tool (Epic 0023 will handle those)
    
    - STATUS: ✅ COMPLETE — Production-ready validation (Commit: c0499d3, Test: verify_wyckoff_index.py ✅ PASSED)
    - PRIORITY: High — Confirms MVP readiness

## Priority 2B+: PrepExcellence Demo Site

### 0017-005-004 - TASK - PrepExcellence Demo Site Implementation
**Status**: ✅ COMPLETE

Create PrepExcellence test prep demo site following established multi-client patterns from AgroFresh and Wyckoff implementations.

**Client Context**: [PrepExcellence](https://prepexcellence.com) - SAT/ACT/PSAT test preparation with Dr. Kaisar Alam, offering winter courses, tutoring, and college admissions support.

**Reference Implementations**: 
- Pattern established in 0017-005-001 (Multi-Client Demo Site Architecture)
- AgroFresh: `/web/src/pages/agrofresh` (agricultural products, simple structure)
- Wyckoff: `/web/src/pages/wyckoff` (healthcare services, doctor search, departments)

**Architecture Decision**: Follow same multi-tenant pattern with separate account, agent instance, and PrepExcellence-specific branding (purple/blue academic theme).

**SCOPE**: Complete demo site creation including folder structure, layouts, components, pages, backend configuration, and chat widget integration.

**KEY DESIGN PRINCIPLES** (from established patterns):
- Separate account (`prepexcellence`) for true multi-tenant isolation
- Client-specific layout and components (PrepExcellenceLayout, PrepExcellenceHeader, PrepExcellenceFooter)
- Chat widget integrated via footer with account/agent configuration
- Academic theme colors (purple/blue palette: #6A1B9A, #1976D2)
- Responsive design with mobile-first approach
- Suggested questions UI for user engagement

- [x] 0017-005-004-001 - CHUNK - Database and backend agent configuration ✅ **COMPLETE**
  - **PURPOSE**: Create PrepExcellence account, agent instance, and backend configuration files
  
  - **DATABASE SETUP**:
      ```sql
      -- Create prepexcellence account
      INSERT INTO accounts (slug, name) VALUES ('prepexcellence', 'PrepExcellence');
      
      -- Create agent instance (will be referenced by UUID after creation)
      INSERT INTO agent_instances (account_id, instance_slug, agent_type, display_name, status)
      VALUES (
        (SELECT id FROM accounts WHERE slug = 'prepexcellence'),
        'prepexcel_info_chat1',
        'simple_chat',
        'PrepExcellence Assistant',
        'active'
      );
      ```
  
  - **AGENT CONFIGURATION STRUCTURE**:
    ```
    backend/config/agent_configs/
    └── prepexcellence/
        └── prepexcel_info_chat1/
            ├── config.yaml          # NEW - Agent settings
            └── system_prompt.md     # NEW - Education-focused prompt
    ```
  
  - **CONFIG.YAML EXAMPLE**:
      ```yaml
      agent_type: "simple_chat"
      account: "prepexcellence"
      instance_name: "prepexcel_info_chat1"
      display_name: "PrepExcellence Assistant"
      
      model_settings:
        model: "anthropic/claude-3.5-sonnet"  # Good for educational content
        temperature: 0.3
        max_tokens: 2000
      
      tools:
        vector_search:
          enabled: true
          max_results: 5
          similarity_threshold: 0.5
          pinecone:
            index_name: "prepexcellence-poc-01"
            namespace: "__default__"
            api_key_env: "PINECONE_API_KEY_OPENTHOUGHT"
          embedding:
            model: "text-embedding-3-small"
            dimensions: 1536
        directory:
          enabled: false    # No directory data for test prep
      
      context_management:
        history_limit: 50
      ```
  
  - **SYSTEM PROMPT FOCUS**:
    - Test preparation specialist (SAT, ACT, PSAT)
    - Dr. Kaisar Alam's teaching methodology and success stories
    - Course information (winter courses, summer enrichment, tutoring)
    - College admissions guidance
    - Student testimonials and score improvement guarantees
    - Professional, encouraging, educational tone
    - **Vector Search Tool Usage**: You have access to a vector search tool to search PrepExcellence's knowledge base. Use it when users ask about courses, test preparation strategies, Dr. Alam's teaching methods, pricing, schedules, or general information about PrepExcellence services. The knowledge base contains website content, course details, and educational resources
  
  - SUB-TASKS:
      - Create `prepexcellence` account in database (INSERT statement)
      - Create `prepexcel_info_chat1` agent instance in database
      - Create directory: `backend/config/agent_configs/prepexcellence/prepexcel_info_chat1/`
      - Create `config.yaml` with vector search enabled (index: prepexcellence-poc-01, namespace: __default__, api_key_env: PINECONE_API_KEY_OPENTHOUGHT)
      - Create `system_prompt.md` with test prep/education focus and vector search tool guidance
      - Document PrepExcellence-specific system prompt guidelines (emphasize Dr. Alam's teaching style, score improvement, student success, vector search usage)
      - Verify `PINECONE_API_KEY_OPENTHOUGHT` environment variable is set
      - Test Pinecone connectivity: `python backend/scripts/verify_prepexcel_index.py` (create verification script similar to verify_wyckoff_index.py)
      - Test agent loads via: `python -c "from app.services.config_loader import get_agent_config; print(get_agent_config('prepexcellence/prepexcel_info_chat1'))"`
  
  - AUTOMATED-TESTS: `backend/tests/integration/test_prepexcel_agent.py`
    - `test_prepexcel_agent_loads()` - Agent config loads successfully
    - `test_prepexcel_account_exists()` - Database account record exists
    - `test_prepexcel_agent_instance_exists()` - Database agent instance record exists
    - `test_prepexcel_vector_enabled()` - Vector search enabled and configured correctly
    - `test_prepexcel_pinecone_config()` - Pinecone settings correct (index, namespace, api_key_env)
    - `test_prepexcel_system_prompt()` - System prompt contains education keywords and vector search guidance
  
  - MANUAL-TESTS:
      - Verify database records: `SELECT * FROM accounts WHERE slug = 'prepexcellence';`
      - Verify agent instance: `SELECT * FROM agent_instances WHERE instance_slug = 'prepexcel_info_chat1';`
      - Load config: Verify YAML parses without errors and vector_search enabled
      - Check Pinecone config: Verify index name, namespace, and api_key_env are correct
      - Verify environment variable: `echo $PINECONE_API_KEY_OPENTHOUGHT` (should not be empty)
      - Run Pinecone verification script: `python backend/scripts/verify_prepexcel_index.py`
      - Check system prompt: Review for educational tone, PrepExcellence context, and vector search tool guidance
      - Test backend endpoint with vector search query: `curl -X POST http://localhost:8000/accounts/prepexcellence/agents/prepexcel_info_chat1/chat -H "Content-Type: application/json" -d '{"message": "What SAT courses do you offer?"}'`
      - Verify agent uses vector search tool in response (check logs for vector_search_start/vector_search_complete events)
    
  - STATUS: ✅ COMPLETE — Backend configuration, database records, Pinecone connectivity verified, agent tested with vector search (Commit: 68fb83a)
  - PRIORITY: High — Foundation for all frontend work

- [x] 0017-005-004-002 - CHUNK - Frontend folder structure and layouts ✅ **COMPLETE**
  - **PURPOSE**: Create PrepExcellence-specific layouts, components, and styling following established patterns
  
  - **FOLDER STRUCTURE** (following AgroFresh/Wyckoff pattern):
      ```
      web/src/
      ├── pages/
      │   └── prepexcellence/              # NEW - PrepExcellence client
      │       ├── index.astro              # Homepage
      │       ├── about.astro              # About Dr. Alam and teaching methodology
      │       ├── courses/                 # Course pages
      │       │   ├── index.astro          # All courses overview
      │       │   ├── sat.astro            # SAT preparation
      │       │   ├── act.astro            # ACT preparation
      │       │   ├── psat.astro           # PSAT preparation
      │       │   └── summer.astro         # Summer enrichment
      │       ├── tutoring.astro           # 1-on-1 tutoring information
      │       ├── admissions.astro         # College admissions support
      │       └── contact.astro            # Contact information
      │
      ├── layouts/
      │   └── PrepExcellenceLayout.astro   # NEW - PrepExcellence layout
      │
      ├── components/
      │   └── prepexcellence/              # NEW - PrepExcellence components
      │       ├── PrepExcellenceHeader.astro
      │       ├── PrepExcellenceFooter.astro
      │       └── SuggestedQuestions.astro  # Reuse from Wyckoff or adapt
      │
      └── styles/
          └── prepexcellence.css           # NEW - Purple/blue academic theme
      ```
  
  - **LAYOUT EXAMPLE** (`PrepExcellenceLayout.astro`):
      ```astro
      ---
      import PrepExcellenceHeader from "../components/prepexcellence/PrepExcellenceHeader.astro";
      import PrepExcellenceFooter from "../components/prepexcellence/PrepExcellenceFooter.astro";
      import "../styles/global.css";
      import "../styles/prepexcellence.css";
      
      interface Props {
        title?: string;
      }
      
      const { title = "PrepExcellence - SAT & ACT Test Prep" } = Astro.props;
      ---
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width" />
          <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
          <meta name="generator" content={Astro.generator} />
          <title>{title}</title>
        </head>
        <body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0;">
          <a href="#main" style="position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden;">Skip to content</a>
          <header role="banner">
            <PrepExcellenceHeader />
          </header>
          <main id="main" role="main" style="max-width: 1200px; margin: 0 auto; padding: 1rem;">
            <slot />
          </main>
          <footer role="contentinfo">
            <PrepExcellenceFooter />
          </footer>
        </body>
      </html>
      ```
  
  - **FOOTER WITH WIDGET** (`PrepExcellenceFooter.astro`):
      ```astro
      ---
      // PrepExcellence Footer with integrated chat widget
      ---
      <footer class="footer-bg" style="padding:2rem 1rem;margin-top:4rem;text-align:center;">
        <div style="max-width:1200px;margin:0 auto;">
          <p style="margin:0;opacity:.8;">© 2025 PrepExcellence. All rights reserved.</p>
        </div>
      </footer>
      
      <!-- Chat Widget Configuration for PrepExcellence -->
      <script is:inline define:vars={{ isDev: import.meta.env.DEV }}>
        window.__SALIENT_WIDGET_CONFIG = {
          account: 'prepexcellence',
          agent: 'prepexcel_info_chat1',
          backend: 'http://localhost:8000',
          allowCross: true,
          debug: isDev
        };
      </script>
      <script is:inline src="/widget/chat-widget.js"></script>
      ```
  
  - **THEME COLORS** (`prepexcellence.css`):
      ```css
      /* PrepExcellence Academic Theme - Purple/Blue Palette */
      :root {
        --prepexcel-primary: #6A1B9A;      /* Deep Purple */
        --prepexcel-secondary: #1976D2;    /* Blue */
        --prepexcel-accent: #9C27B0;       /* Medium Purple */
        --prepexcel-light: #E1BEE7;        /* Light Purple */
        --prepexcel-bg: #F3E5F5;           /* Very Light Purple */
      }
      
      .footer-bg {
        background: linear-gradient(135deg, var(--prepexcel-primary), var(--prepexcel-secondary));
        color: white;
      }
      ```
  
  - SUB-TASKS:
      - Create `web/src/pages/prepexcellence/` folder
      - Create `PrepExcellenceLayout.astro` with academic theme
      - Create `PrepExcellenceHeader.astro` with navigation (Courses, Tutoring, Admissions, Contact)
      - Create `PrepExcellenceFooter.astro` with widget config (`prepexcellence/prepexcel_info_chat1`)
      - Create `prepexcellence.css` with purple/blue color scheme (#6A1B9A, #1976D2)
      - Adapt `SuggestedQuestions.astro` component for PrepExcellence use
      - Update root `web/src/pages/index.astro` demo selector to include PrepExcellence card
  
  - AUTOMATED-TESTS: `web/tests/test_prepexcel_structure.spec.ts` (Playwright)
      - `test_prepexcel_folder_exists()` - Folder structure created
      - `test_layout_exists()` - PrepExcellenceLayout.astro exists and parses
      - `test_components_exist()` - Header and Footer components exist
      - `test_styles_exist()` - prepexcellence.css exists with theme variables
      - `test_demo_selector_updated()` - Root index.astro includes PrepExcellence option
  
  - MANUAL-TESTS:
      - Verify folder structure matches design
      - Review layout file for completeness
      - Check header navigation structure
      - Verify footer includes widget configuration
      - Review CSS theme colors (purple/blue academic palette)
      - Test demo selector shows PrepExcellence card
    
  - STATUS: ✅ COMPLETE — Layout, components, styles, homepage created and integrated into demo selector (Commit: 68fb83a)
  - PRIORITY: High — Required before creating pages

- [x] 0017-005-004-003 - CHUNK - Create PrepExcellence demo pages ✅ **COMPLETE**
  - **PURPOSE**: Build realistic test prep demo site with pages showcasing courses, tutoring, and admissions
  
  - **PAGES TO CREATE** (8 pages total):
      
      **1. Homepage** (`index.astro`):
      - Hero section: "Achieve Your Best SAT/ACT Scores"
      - Feature cards: Expert Instruction, Proven Results, Personalized Support
      - Student testimonials (from website: Rick S, Areeq H, Malia A, etc.)
      - Call-to-action: "View Courses" button
      - Winter courses highlight
      - Suggested questions: "What SAT courses do you offer?", "Tell me about Dr. Alam's teaching method", "What is your score improvement guarantee?" (these will trigger vector search)
      
      **2. About Page** (`about.astro`):
      - Dr. Kaisar Alam biography and credentials
      - Teaching methodology and philosophy
      - Success statistics (150+ point improvement guarantee)
      - Student testimonials with score improvements
      - Suggested questions: "Who is Dr. Alam?", "What makes your teaching unique?", "What are your success rates?"
      
      **3. Courses Overview** (`courses/index.astro`):
      - SAT, ACT, PSAT course listings
      - Summer enrichment programs
      - Computer Science/Coding courses
      - Course schedules and pricing (if applicable)
      - Registration information
      - Suggested questions: "What courses are available?", "When do winter courses start?", "How do I register?"
      
      **4. SAT Course** (`courses/sat.astro`):
      - SAT Strategies Prep details
      - SAT Weekend Review options
      - Curriculum overview
      - Scoring strategies and time-saving techniques
      - Suggested questions: "What's covered in SAT prep?", "How long are the courses?", "What materials are included?"
      
      **5. ACT Course** (`courses/act.astro`):
      - ACT preparation program details
      - Test strategies specific to ACT format
      - Score improvement focus areas
      - Suggested questions: "How is ACT different from SAT?", "What ACT prep do you offer?", "Which test should I take?"
      
      **6. PSAT Course** (`courses/psat.astro`):
      - PSAT preparation and National Merit Scholarship
      - Foundational test-taking skills
      - Transition to SAT preparation
      - Suggested questions: "Why is PSAT important?", "How do I qualify for National Merit?", "Should I take PSAT prep?"
      
      **7. Tutoring** (`tutoring.astro`):
      - 1-to-1 personalized tutoring
      - Custom lesson plans
      - Flexible scheduling
      - Subject areas (SAT Math, Reading, Writing, ACT sections)
      - Suggested questions: "Do you offer private tutoring?", "How does 1-on-1 tutoring work?", "What's the tutoring schedule?"
      
      **8. College Admissions** (`admissions.astro`):
      - College admissions consulting
      - Essay review and editing
      - Application strategy
      - College selection guidance
      - Suggested questions: "Do you help with college essays?", "What admissions support do you provide?", "How do I choose the right college?"
      
      **9. Contact** (`contact.astro`):
      - Contact information (phone: +1 214-603-2254, +1 848-448-3331)
      - Email: info@prepexcellence.com
      - Location/office hours (if applicable)
      - Contact form or chat encouragement
      - Suggested questions: "How do I get in touch?", "What are your office hours?", "Can I schedule a consultation?"
  
  - **CONTENT GUIDELINES**:
      - Professional, encouraging, educational tone
      - Emphasize Dr. Alam's expertise and personalized approach
      - Highlight score improvement guarantees (150+ points)
      - Include student testimonials throughout
      - Use academic imagery (books, studying, test materials)
      - Mobile-responsive design
      - Accessibility (ARIA labels, semantic HTML, keyboard navigation)
  
  - **SUGGESTED QUESTIONS INTEGRATION**:
      - Each page includes `<SuggestedQuestions questions={[...]} />` component
      - Questions contextual to page content
      - Clicking question opens chat widget with pre-filled message
  
  - SUB-TASKS:
      - Create 9 page files in `web/src/pages/prepexcellence/`
      - Write content for each page (minimal placeholder or detailed based on prepexcellence.com)
      - Add suggested questions UI to relevant pages
      - Include student testimonials on homepage and about page
      - Add course cards with navigation to course detail pages
      - Create responsive layouts for mobile/tablet/desktop
      - Add call-to-action buttons (Register, Contact, Learn More)
      - Integrate PrepExcellenceLayout on all pages
      - Test navigation between pages
      - Add accessibility features (skip links, ARIA labels, semantic HTML)
  
  - AUTOMATED-TESTS: `web/tests/test_prepexcel_pages.spec.ts` (Playwright)
      - `test_all_prepexcel_pages_load()` - All 9 pages load without errors
      - `test_chat_widget_on_all_pages()` - Chat widget present on all pages
      - `test_widget_configured_correctly()` - Widget uses prepexcellence/prepexcel_info_chat1
      - `test_widget_backend_urls()` - Widget hits `/accounts/prepexcellence/agents/prepexcel_info_chat1/...`
      - `test_suggested_questions_clickable()` - Example questions trigger chat
      - `test_vector_search_integration()` - Questions trigger vector search (check for knowledge base responses)
      - `test_navigation_between_pages()` - All internal links work with `/prepexcellence/` prefix
      - `test_responsive_design()` - Pages render correctly on mobile/tablet/desktop
      - `test_testimonials_display()` - Student testimonials appear on homepage
  
  - MANUAL-TESTS:
      - Navigate through all 9 PrepExcellence pages
      - Test chat widget on each page: send example questions
      - **Test vector search queries**: Ask "What SAT courses are available?", "Tell me about your teaching methodology", "What are your course prices?"
      - Verify agent responses contain knowledge base content (not just general responses)
      - Check browser console/network tab: verify vector_search tool is called
      - Check backend logs: verify `vector_search_start` and `vector_search_complete` events appear
      - Verify suggested questions appear on relevant pages
      - Click suggested questions, verify chat widget pre-fills and sends, and uses vector search
      - Test homepage: verify hero section, feature cards, testimonials display
      - Test courses pages: verify course information and navigation
      - Verify backend hits correct endpoint: `/accounts/prepexcellence/agents/prepexcel_info_chat1/stream`
      - Verify purple/blue academic theme consistent across pages
      - Test responsive design on mobile (iPhone), tablet (iPad), desktop viewports
      - Test accessibility: keyboard navigation, screen reader compatibility, semantic HTML
      - Verify chat history persists across page navigation within PrepExcellence site
    
  - STATUS: ✅ COMPLETE — All 9 pages created: Homepage, About, Courses (Index, SAT, ACT, PSAT), Tutoring, Admissions, Contact with SuggestedQuestions integration and vector search support
  - PRIORITY: High — User-facing demo showcase

- [x] 0017-005-004-004 - CHUNK - Demo selector integration and testing ✅ **COMPLETE**
  - **PURPOSE**: Update root demo selector page and perform end-to-end validation
  
  - **DEMO SELECTOR UPDATE** (`web/src/pages/index.astro`):
      ```astro
      ---
      import Layout from '../layouts/Layout.astro';
      ---
      <Layout title="Salient Multi-Client Demos">
        <section style="padding:3rem 0;text-align:center;">
          <h1 style="font-size:2.5rem;margin:0 0 2rem;">Demo Client Sites</h1>
          
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:2rem;max-width:1200px;margin:0 auto;">
            
            <!-- AgroFresh -->
            <a href="/agrofresh/" style="display:block;padding:2rem;background:#f0f9f0;border-radius:12px;text-decoration:none;border:2px solid #2E7D32;transition:transform 0.2s;">
              <h2 style="font-size:1.5rem;color:#2E7D32;margin:0 0 1rem;">🌾 AgroFresh Solutions</h2>
              <p style="margin:0;color:#555;">Agricultural produce freshness and quality solutions</p>
            </a>
            
            <!-- Wyckoff -->
            <a href="/wyckoff/" style="display:block;padding:2rem;background:#e3f2fd;border-radius:12px;text-decoration:none;border:2px solid #0277BD;transition:transform 0.2s;">
              <h2 style="font-size:1.5rem;color:#0277BD;margin:0 0 1rem;">🏥 Wyckoff Hospital</h2>
              <p style="margin:0;color:#555;">Healthcare services with doctor profiles and departments</p>
            </a>
            
            <!-- PrepExcellence - NEW -->
            <a href="/prepexcellence/" style="display:block;padding:2rem;background:#f3e5f5;border-radius:12px;text-decoration:none;border:2px solid #6A1B9A;transition:transform 0.2s;">
              <h2 style="font-size:1.5rem;color:#6A1B9A;margin:0 0 1rem;">📚 PrepExcellence</h2>
              <p style="margin:0;color:#555;">SAT, ACT, PSAT test preparation and college admissions</p>
            </a>
            
          </div>
          
          <div style="margin:3rem 0;">
            <a href="/demo/simple-chat" style="display:inline-block;padding:1rem 2rem;background:#333;color:white;border-radius:8px;text-decoration:none;">Technical Demos →</a>
          </div>
        </section>
      </Layout>
      
      <style>
        a[href^="/agrofresh/"]:hover,
        a[href^="/wyckoff/"]:hover,
        a[href^="/prepexcellence/"]:hover {
          transform: translateY(-4px);
        }
      </style>
      ```
  
  - **END-TO-END VALIDATION**:
      - All 3 demo sites accessible from selector
      - Each demo uses correct account/agent configuration
      - Chat widgets work independently per client
      - Session isolation between clients
      - Cost tracking attributes to correct accounts
  
  - SUB-TASKS:
      - Update `web/src/pages/index.astro` to include PrepExcellence card
      - Add purple/blue themed card matching PrepExcellence branding
      - Test all 3 demo site links from selector
      - Verify chat widget works on all PrepExcellence pages
      - Test cross-client isolation (agrofresh session ≠ prepexcellence session)
      - Verify database tracking: `SELECT * FROM sessions WHERE account_slug = 'prepexcellence';`
      - Check LLM request attribution: `SELECT * FROM llm_requests WHERE account_slug = 'prepexcellence';`
      - Run data integrity test: `python backend/tests/manual/test_data_integrity.py --agent prepexcellence/prepexcel_info_chat1`
  
  - AUTOMATED-TESTS: `web/tests/test_demo_selector.spec.ts` (Playwright)
      - `test_demo_selector_loads()` - Root page loads with 3 client cards
      - `test_all_demo_links_work()` - All 3 client links navigate correctly
      - `test_prepexcel_card_visible()` - PrepExcellence card displays with correct styling
      - `test_technical_demos_link()` - Technical demos link still works
      - `test_cross_client_isolation()` - Sessions don't leak between clients
  
  - MANUAL-TESTS:
      - Navigate to `http://localhost:4321/`
      - Verify 3 client cards displayed: AgroFresh (green), Wyckoff (blue), PrepExcellence (purple)
      - Click PrepExcellence card, verify redirects to `/prepexcellence/`
      - Open chat on PrepExcellence site, send message
      - Verify backend logs show correct account: `prepexcellence`
      - Check database: `SELECT account_slug, agent_instance_slug FROM llm_requests ORDER BY created_at DESC LIMIT 5;`
      - Navigate to AgroFresh, verify separate chat session
      - Test suggested questions on PrepExcellence pages
      - Verify responsive design on all viewports
    
  - STATUS: ✅ COMPLETE — Demo selector updated with PrepExcellence card, multi-client isolation verified (Commit: 68fb83a)
  - PRIORITY: Medium — Completion and polish

- [x] 0017-005-004-005 - CHUNK - Vector search end-to-end testing ✅ **TESTED**
  - **PURPOSE**: Verify vector search works correctly with prepexcellence-poc-01 index
  - **STATUS**: ✅ TESTED — Vector search tool working with Gemini 2.5 Flash model. Test query "what sat classes do you offer" successfully retrieved PrepExcellence course information from Pinecone. See LLM Tool Calling Evaluation for model selection rationale (Commit: 68fb83a)
  - **PRIORITY**: High — Required for functional demo

**TESTING SUMMARY**:

**AUTOMATED-TESTS** (Integration - all chunks):
- **Backend**: `backend/tests/integration/test_prepexcel_agent.py` (6 tests - includes vector search config)
- **Frontend Structure**: `web/tests/test_prepexcel_structure.spec.ts` (5 tests)
- **Frontend Pages**: `web/tests/test_prepexcel_pages.spec.ts` (9 tests - includes vector search integration)
- **Demo Selector**: `web/tests/test_demo_selector.spec.ts` (5 tests)
- **Vector Search**: `backend/tests/integration/test_prepexcel_vector.py` (5 tests - end-to-end vector search validation)
- **Total**: 30 automated tests

**MANUAL-TESTS** (End-to-End Validation):
- Backend configuration verification (database, config files, agent loading)
- Frontend structure validation (layouts, components, styles)
- Page content and navigation testing (9 pages)
- Chat widget integration on all pages
- Cross-client isolation verification
- Responsive design testing (mobile/tablet/desktop)
- Accessibility testing (keyboard navigation, screen reader)
- Demo selector integration

**DOCUMENTATION UPDATES**:
- Update multi-model configuration summary table (add PrepExcellence row with vector search enabled)
- Update multi-tenant architecture diagram (add prepexcellence account)
- Document PrepExcellence system prompt guidelines (including vector search tool usage)
- Create `backend/scripts/verify_prepexcel_index.py` (Pinecone connectivity verification script)

## Priority 2B+: Multi-Agent Data Integrity Testing

### 0017-005-003 - FEATURE - Data Integrity Verification Infrastructure
**Status**: ✅ COMPLETE (2025-10-20)

Comprehensive test infrastructure to verify database integrity across all agent instances after data model cleanup (Priority 3).

- [x] 0017-005-003 - TASK - Multi-Agent Data Integrity Verification Script ✅ **COMPLETE 2025-10-20**
  - [x] 0017-005-003-001 - CHUNK - Create comprehensive test script ✅ **COMPLETE 2025-10-20**
    - **PURPOSE**: Verify all database tables (sessions, messages, llm_requests) are populated correctly after Priority 3 denormalization work
    - **SCOPE**: Test all 5 multi-tenant agent instances across 3 accounts
    - **LOCATION**: `backend/tests/manual/test_data_integrity.py`
    - **EXCLUSIONS**: Legacy non-multi-tenant endpoints (`/`, `/chat`, `/events/stream`, `/agents/simple-chat/chat`) excluded from testing (see BUG-0017-007)
    
    - **AGENT COVERAGE** (5 multi-tenant agents only):
      ```
      ACCOUNT           AGENT INSTANCE           MODEL                                 VECTOR SEARCH
      ────────────────────────────────────────────────────────────────────────────────────────────
      agrofresh      →  agro_info_chat1      →  deepseek/deepseek-v3.2-exp        →  Enabled (agrofresh01)
      wyckoff        →  wyckoff_info_chat1   →  qwen/qwen3-235b-a22b-thinking    →  Enabled (wyckoff-poc-01)
      default_account→  simple_chat1         →  moonshotai/kimi-k2-0905           →  Disabled
      default_account→  simple_chat2         →  openai/gpt-oss-120b               →  Disabled
      acme           →  acme_chat1           →  mistralai/mistral-small-3.2       →  Disabled
      
      NOTE: Legacy "simple_chat" endpoint (non-multi-tenant) is NOT tested - it bypasses
            the multi-tenant data model and doesn't populate account_id/agent_instance_id.
            See BUG-0017-007 for legacy endpoint cleanup plan.
      ```
    
    - **VERIFICATION CHECKS** (per agent):
      1. **Sessions Table**:
         - `account_id` populated (FK to accounts table)
         - `agent_instance_id` populated (FK to agent_instances table)
         - `agent_instance_slug` populated (denormalized for fast queries)
         - Session cookie valid and persistent
      
      2. **Messages Table**:
         - `session_id` populated (FK to sessions table)
         - `llm_request_id` populated (nullable FK to llm_requests table)
         - `role` correct (user/assistant)
         - `content` matches request/response
         - Timestamps populated
      
      3. **LLM_requests Table**:
         - `account_id` populated (denormalized)
         - `account_slug` populated (denormalized)
         - `agent_instance_slug` populated (denormalized)
         - `agent_type` populated (e.g., "simple_chat")
         - `completion_status` populated (e.g., "success", "error")
         - `prompt_cost` > 0 (non-zero for successful requests)
         - `completion_cost` > 0 (non-zero for successful requests)
         - `total_cost` = prompt_cost + completion_cost
         - `request_body` and `response_body` populated
         - `model` matches agent config
      
      4. **Cross-Table Relationships**:
         - Messages.llm_request_id references valid llm_requests.id
         - Messages.session_id references valid sessions.id
         - Sessions.account_id references valid accounts.id
         - Sessions.agent_instance_id references valid agent_instances.id
      
      5. **Multi-Tenant Isolation** (All 3 scenarios tested):
         - **Scenario 1: Session-Level Isolation**
           - Same agent, different sessions → messages/llm_requests don't leak between sessions
           - Query: Messages from session A don't appear in queries for session B
         - **Scenario 2: Agent-Level Isolation** 
           - Same account, different agents → sessions/messages properly attributed
           - Query: simple_chat1 data separate from simple_chat2 data
         - **Scenario 3: Account-Level Isolation**
           - Different accounts → complete data isolation
           - Query: agrofresh data never appears in wyckoff queries
         - **LLM Request Isolation**: llm_requests properly scoped by account/agent
         - **FK Integrity**: No orphaned records, all foreign keys valid
      
      6. **Cost Tracking Validation**:
         - All costs use NUMERIC(12, 8) precision
         - Costs match expected ranges for each model
         - No NULL costs for successful completions
         - `genai-prices` or `fallback_pricing.yaml` used correctly
    
    - **CONFIGURATION** (YAML file: `backend/tests/manual/test_data_integrity_config.yaml`):
      ```yaml
      test_prompts:
        agrofresh/agro_info_chat1:
          prompt: "What products do you offer for apples?"
          expected_keywords: ["AgroFresh", "SmartFresh", "coating"]
        
        wyckoff/wyckoff_info_chat1:
          prompt: "What cardiology services do you offer?"
          expected_keywords: ["cardiology", "heart", "services"]
        
        default_account/simple_chat1:
          prompt: "What is your knowledge cutoff date?"
          expected_keywords: ["2023", "2024", "cutoff"]
        
        default_account/simple_chat2:
          prompt: "Tell me about yourself"
          expected_keywords: ["assistant", "help"]
        
        acme/acme_chat1:
          prompt: "What can you do?"
          expected_keywords: ["assist", "help", "answer"]
      
      backend:
        url: "http://localhost:8000"
        timeout_seconds: 30
      
      database:
        connection_string: "${DATABASE_URL}"  # From .env
      
      verification:
        check_costs: true
        check_relationships: true
        check_denormalization: true
        strict_mode: true  # Fail on any issue
      ```
    
    - **IMPLEMENTATION APPROACH** (Chosen: Option 1 - Sequential Database Queries):
      
      **Selected Implementation**:
      ```python
      # CHOSEN: Simple, debuggable, no external dependencies
      # Data preservation: Test data preserved by default for manual inspection
      # Cleanup: Separate script (cleanup_test_data.py) handles data deletion
      
      async def test_agent_data_integrity(account: str, agent: str, prompt: str):
          # 1. Send HTTP request to multi-tenant endpoint
          response = await client.post(f"/accounts/{account}/agents/{agent}/chat", ...)
          
          # 2. Query database directly (SQLAlchemy)
          session_record = await db.query(Session).filter(...).first()
          messages = await db.query(Message).filter(...).all()
          llm_request = await db.query(LLMRequest).filter(...).first()
          
          # 3. Verify all fields (database integrity)
          assert session_record.account_id is not None
          assert session_record.agent_instance_slug == agent
          assert llm_request.prompt_cost > 0
          
          # 4. Verify multi-tenant isolation (all 3 scenarios)
          await verify_multi_tenant_isolation(session_record, account, agent)
          
          # 5. Return results for formatting
          return {
              'account': account,
              'agent': agent,
              'database_checks': 'PASS',
              'isolation_checks': {'session': 'PASS', 'agent': 'PASS', 'account': 'PASS'}
          }
      
      # Run sequentially for all 5 agents
      results = []
      for agent_config in test_configs:
          result = await test_agent_data_integrity(**agent_config)
          results.append(result)
      
      # Format output based on --format flag
      if args.format == 'rich':
          format_rich(results)  # ASCII tables with box-drawing
      elif args.format == 'simple':
          format_simple(results)  # Plain text (grep-friendly)
      elif args.format == 'json':
          format_json(results)  # JSON for CI/CD
      
      # Data preserved by default - run cleanup_test_data.py separately
      ```
      
      **Output Format Examples**:
      
      **Rich Format** (default - ASCII tables):
      ```
      ╔════════════════════════════════════════════════════════════════════════════════╗
      ║               MULTI-AGENT DATA INTEGRITY VERIFICATION REPORT                    ║
      ╚════════════════════════════════════════════════════════════════════════════════╝
      
      AGENT                          STATUS  SESSION  MESSAGES  LLM_REQ  COSTS  ISOLATION
      ───────────────────────────────────────────────────────────────────────────────────
      agrofresh/agro_info_chat1      ✅ PASS    ✅       ✅        ✅       ✅      ✅
      wyckoff/wyckoff_info_chat1     ✅ PASS    ✅       ✅        ✅       ✅      ✅
      default_account/simple_chat1   ✅ PASS    ✅       ✅        ✅       ✅      ✅
      default_account/simple_chat2   ✅ PASS    ✅       ✅        ✅       ✅      ✅
      acme/acme_chat1                ✅ PASS    ✅       ✅        ✅       ✅      ✅
      
      ISOLATION VERIFICATION (3 scenarios)
      ┌────────────────────────────┬────────────────────────────────────────────────┐
      │ Scenario                   │ Result                                         │
      ├────────────────────────────┼────────────────────────────────────────────────┤
      │ Session-level isolation    │ ✅ PASS - No cross-session data leakage       │
      │ Agent-level isolation      │ ✅ PASS - Agents within account isolated      │
      │ Account-level isolation    │ ✅ PASS - Complete account separation         │
      └────────────────────────────┴────────────────────────────────────────────────┘
      
      ✅ ALL CHECKS PASSED (5/5 agents verified)
      💾 Test data preserved for manual inspection
      🧹 Run cleanup_test_data.py to delete test data
      ```
      
      **Simple Format** (`--format simple` - grep-friendly):
      ```
      MULTI-AGENT DATA INTEGRITY REPORT
      ==================================
      Agent: agrofresh/agro_info_chat1 - PASS
      Agent: wyckoff/wyckoff_info_chat1 - PASS
      Agent: default_account/simple_chat1 - PASS
      Agent: default_account/simple_chat2 - PASS
      Agent: acme/acme_chat1 - PASS
      
      Isolation: Session-level - PASS
      Isolation: Agent-level - PASS
      Isolation: Account-level - PASS
      
      Summary: 5/5 PASS
      ```
      
      **JSON Format** (`--format json` - CI/CD integration):
      ```json
      {
        "test_run": "2025-10-19T15:42:31Z",
        "backend_url": "http://localhost:8000",
        "results": [
          {
            "account": "agrofresh",
            "agent": "agro_info_chat1",
            "database_checks": "PASS",
            "isolation_checks": {
              "session": "PASS",
              "agent": "PASS",
              "account": "PASS"
            }
          }
        ],
        "summary": {
          "total_agents": 5,
          "passed": 5,
          "failed": 0
        }
      }
      ```
      
      **Rejected Options** (for reference):
      
      **Option 2: LLM-Assisted Verification**:
      ```python
      # Pros: Smart validation, catches semantic issues, generates test prompts
      # Cons: Costs money, slower, adds complexity
      
      async def llm_verify_data_integrity(agent_config):
          # 1. Use LLM to generate contextual test prompt
          test_prompt = await llm.generate_test_prompt(
              agent_type="info_bot",
              domain=agent_config.domain,  # "agriculture" vs "healthcare"
              purpose="test vector search for hospital services"
          )
          
          # 2. Send request and get response
          response = await send_chat_request(agent_config, test_prompt)
          
          # 3. Use LLM to verify response quality
          verification = await llm.verify_response(
              prompt=test_prompt,
              response=response,
              expected_behavior="Should answer about {domain} using knowledge base"
          )
          
          # 4. Check database integrity (same as Option 1)
          db_checks = await verify_database_records(agent_config)
          
          # 5. LLM semantic checks
          semantic_issues = await llm.check_for_issues(
              agent="wyckoff/hospital_chat1",
              response=response,
              issues_to_check=[
                  "Is agent answering AgroFresh questions when configured for Wyckoff?",
                  "Is agent hallucinating contact info not in knowledge base?",
                  "Is response using correct domain terminology?"
              ]
          )
          
          return {
              "database_integrity": db_checks,
              "response_quality": verification,
              "semantic_issues": semantic_issues
          }
      ```
      
      **Option 3: Pytest Parametrized Suite**:
      ```python
      # NOT CHOSEN - Too complex for manual verification
      # Pros: Professional, parallel execution, reusable in CI/CD, proper fixtures
      # Cons: More complex setup, pytest overhead, harder to read output
      # Decision: Rejected in favor of simple sequential approach (Option 1)
      ```
    
    - **FINAL DECISION**: 
      - ✅ **Option 1 chosen** - Sequential Database Queries with multiple output formats
      - ❌ **Option 2 rejected** - LLM-assisted adds unnecessary cost/complexity
      - ❌ **Option 3 rejected** - Pytest overhead not needed for manual testing
      
    - **KEY FEATURES**:
      - **Data Preservation**: Test data kept by default for manual inspection
      - **Separate Cleanup**: `cleanup_test_data.py` script handles deletion
      - **Flexible Output**: `--format` flag (rich/simple/json) for different use cases
      - **Multi-Tenant Isolation**: All 3 isolation scenarios tested
      - **Multi-Tenant Only**: Legacy endpoints excluded (BUG-0017-007)
    
    - **OUTPUT FORMAT**:
      ```
      ╔════════════════════════════════════════════════════════════════════════════════╗
      ║               MULTI-AGENT DATA INTEGRITY VERIFICATION REPORT                    ║
      ╠════════════════════════════════════════════════════════════════════════════════╣
      ║ Test Run: 2025-10-18 15:42:31 UTC                                              ║
      ║ Backend: http://localhost:8000                                                  ║
      ║ Database: salient_dev (PostgreSQL 14.2)                                         ║
      ╚════════════════════════════════════════════════════════════════════════════════╝
      
      AGENT VERIFICATION RESULTS
      ┌─────────────────────────────────┬────────┬─────────┬──────────┬─────────┬───────┐
      │ Agent                           │ Status │ Session │ Messages │ LLM_Req │ Costs │
      ├─────────────────────────────────┼────────┼─────────┼──────────┼─────────┼───────┤
      │ agrofresh/agro_info_chat1       │ ✅ PASS│   ✅    │    ✅    │   ✅    │  ✅   │
      │ wyckoff/wyckoff_info_chat1      │ ✅ PASS│   ✅    │    ✅    │   ✅    │  ✅   │
      │ default_account/simple_chat1    │ ✅ PASS│   ✅    │    ✅    │   ✅    │  ✅   │
      │ default_account/simple_chat2    │ ✅ PASS│   ✅    │    ✅    │   ✅    │  ✅   │
      │ acme/acme_chat1                 │ ✅ PASS│   ✅    │    ✅    │   ✅    │  ✅   │
      └─────────────────────────────────┴────────┴─────────┴──────────┴─────────┴───────┘
      
      DETAILED VERIFICATION
      ┌─────────────────────────────────┬──────────────────────────────────────────────┐
      │ Check                           │ Result                                        │
      ├─────────────────────────────────┼──────────────────────────────────────────────┤
      │ Sessions.account_id             │ ✅ All populated (5/5)                       │
      │ Sessions.agent_instance_slug    │ ✅ All populated (5/5)                       │
      │ Messages.llm_request_id (FK)    │ ✅ All populated (10/10)                     │
      │ LLM_requests.account_slug       │ ✅ All populated (5/5)                       │
      │ LLM_requests.agent_type         │ ✅ All populated (5/5)                       │
      │ LLM_requests.completion_status  │ ✅ All "success" (5/5)                       │
      │ Cost tracking (non-zero)        │ ✅ All > 0 (5/5)                             │
      │ Cost precision (12,8)           │ ✅ All valid NUMERIC (5/5)                   │
      │ Cross-table FK relationships    │ ✅ All valid (0 orphaned records)            │
      └─────────────────────────────────┴──────────────────────────────────────────────┘
      
      SUMMARY
      ═══════════════════════════════════════════════════════════════════════════════════
      ✅ ALL CHECKS PASSED (5/5 agents verified)
      
      Total execution time: 42.3 seconds
      Database queries: 75
      HTTP requests: 5
      LLM requests: 5
      Total cost: $0.0234
      
      Next Steps:
      1. ✅ Data model cleanup complete - safe to proceed with vector search testing
      2. 📋 Run regression tests: pytest backend/tests/
      3. 📋 Deploy to staging environment
      ```
    
    - SUB-TASKS:
      
      **File 1: `backend/tests/manual/test_data_integrity.py`** (Main test script)
      - Implement sequential database queries approach (Option 1)
      - Test all 5 multi-tenant agents (exclude legacy endpoints)
      - Verify database integrity (sessions, messages, llm_requests)
      - Test multi-tenant isolation (all 3 scenarios: session, agent, account)
      - Add `verify_multi_tenant_isolation()` function
      - CLI argument parsing with argparse
      - Three output formatters: `format_rich()`, `format_simple()`, `format_json()`
      - `--format` flag: rich (default), simple, json
      - `--strict` flag: Exit 1 on any failure (CI/CD mode)
      - Preserve test data by default (no automatic cleanup)
      - Comprehensive logging for each verification step
      - Error handling for network/database issues
      - Timing metrics and cost tracking
      
      **File 2: `backend/tests/manual/cleanup_test_data.py`** (Separate cleanup script)
      - Delete test data from sessions, messages, llm_requests tables
      - Confirmation prompt before deletion ("Are you sure? [y/N]")
      - `--dry-run` flag: Show what would be deleted without actually deleting
      - `--agent` flag: Clean specific agent data only (e.g., `--agent agrofresh/agro_info_chat1`)
      - `--all` flag: Skip confirmation, delete immediately (dangerous!)
      - Summary of deleted records (counts per table)
      - Safety checks (don't delete production data)
      
      **File 3: `backend/tests/manual/test_data_integrity_config.yaml`** (Test configuration)
      - Test prompts for each of the 5 agents
      - Expected keywords for validation
      - Backend URL and timeouts
      - Database connection string reference
    
    - AUTOMATED-TESTS: `backend/tests/unit/test_data_integrity_script.py`
      - `test_verification_logic()` - Test verification checks with mock data
      - `test_config_loading()` - Test YAML config parsing
      - `test_summary_formatting()` - Test ASCII table output
      - `test_error_handling()` - Test network/DB error scenarios
    
    - MANUAL-TESTS:
      
      **Test Execution**:
      ```bash
      # 1. Run test with default rich output (ASCII tables)
      python backend/tests/manual/test_data_integrity.py
      
      # 2. Run with simple output (grep-friendly)
      python backend/tests/manual/test_data_integrity.py --format simple
      
      # 3. Run with JSON output (CI/CD integration)
      python backend/tests/manual/test_data_integrity.py --format json > results.json
      
      # 4. Run in strict mode (exit 1 on failure)
      python backend/tests/manual/test_data_integrity.py --strict
      ```
      
      **Verification Checklist**:
      - ✅ All 5 agents show ✅ PASS in summary table
      - ✅ Session-level isolation: PASS
      - ✅ Agent-level isolation: PASS
      - ✅ Account-level isolation: PASS
      - ✅ Database fields: All denormalized fields populated
      - ✅ FK relationships: All foreign keys valid
      - ✅ Cost tracking: All costs non-zero and correctly calculated
      - ✅ Test data preserved after script completes
      
      **Manual Database Inspection** (after test run):
      ```sql
      -- Verify test data was created and preserved
      SELECT account_slug, agent_instance_slug, COUNT(*) 
      FROM llm_requests 
      WHERE created_at > NOW() - INTERVAL '5 minutes'
      GROUP BY account_slug, agent_instance_slug;
      
      -- Check session isolation
      SELECT session_id, COUNT(*) FROM messages GROUP BY session_id;
      ```
      
      **Cleanup After Testing**:
      ```bash
      # 1. Dry-run: Show what would be deleted
      python backend/tests/manual/cleanup_test_data.py --dry-run
      
      # 2. Delete specific agent's test data
      python backend/tests/manual/cleanup_test_data.py --agent wyckoff/wyckoff_info_chat1
      
      # 3. Delete all test data (with confirmation)
      python backend/tests/manual/cleanup_test_data.py
      
      # 4. Delete all test data (skip confirmation - dangerous!)
      python backend/tests/manual/cleanup_test_data.py --all
      ```
    
    - STATUS: ✅ COMPLETE (2025-10-20) — Comprehensive test infrastructure fully implemented and tested
      - **Files Created**: test_data_integrity.py, cleanup_test_data.py, test_data_integrity_config.yaml
      - **Testing**: All 5 multi-tenant agents verified with proper isolation and cost tracking
      - **Output Formats**: Rich (ASCII tables), Simple (grep-friendly), JSON (CI/CD)
      - **Features**: Timing tracking, 3 isolation scenarios, data preservation by default
    - PRIORITY: High — Required to verify data model cleanup is working correctly

## Priority 2C: Per-Agent Session Management

### 0017-007 - FEATURE - Per-Agent Cookie Configuration
**Status**: 📋 Planned — Ready for Implementation

Implement backend-controlled per-agent cookie naming to ensure proper session isolation between agent instances.

**RATIONALE**: Currently all agents share a single session cookie name, which can cause session conflicts when users interact with multiple agents. Per-agent cookie names ensure complete session isolation at the browser level.

**COOKIE NAME FORMAT**: `<account_slug>_<agent_instance_slug>_sk`
- Example: `prepexcellence_prepexcel_info_chat1_sk`
- Example: `wyckoff_wyckoff_info_chat1_sk`
- Example: `agrofresh_agro_info_chat1_sk`

**BREAKING CHANGE**: This implementation has no backwards compatibility. All existing sessions will be invalidated when deployed. This is acceptable since there are no production deployments yet.

**SECURITY CONSIDERATIONS**:
- ✅ Cookie names are predictable (session ID is the secret, not the cookie name)
- ✅ Per-agent isolation prevents session leakage between agents
- ✅ SameSite, Secure, and Domain attributes must be properly configured for embedded widgets
- ✅ HttpOnly flag prevents JavaScript access to session tokens
- ✅ Cookie name length: ~37 chars + session ID (~32 chars) = ~69 chars (well within 4KB browser limit)

- [ ] 0017-007-001 - TASK - Backend Session Cookie Configuration

  - [ ] 0017-007-001-001 - CHUNK - Add cookie configuration to agent config.yaml
    - **PURPOSE**: Define per-agent cookie naming in agent configuration files
    
    - **CONFIGURATION STRUCTURE**:
      ```yaml
      # backend/config/agent_configs/prepexcellence/prepexcel_info_chat1/config.yaml
      
      agent_type: "simple_chat"
      account: "prepexcellence"
      instance_name: "prepexcel_info_chat1"
      
      # NEW: Session cookie configuration
      session:
        cookie_name: "prepexcellence_prepexcel_info_chat1_sk"  # Format: {account}_{instance}_sk
        cookie_max_age: 2592000  # 30 days in seconds (optional, defaults to 30 days)
        cookie_domain: null  # null = current domain only (optional, defaults to null)
        cookie_secure: true  # Require HTTPS (optional, defaults to true in production)
        cookie_samesite: "lax"  # "strict", "lax", or "none" (optional, defaults to "lax")
        cookie_httponly: true  # Prevent JavaScript access (optional, defaults to true)
      ```
    
    - **VALIDATION RULES**:
      - `cookie_name` must match pattern: `^[a-z0-9]+_[a-z0-9_]+_sk$`
      - `cookie_name` length must be ≤ 50 characters
      - `cookie_name` must be unique across all agents (no duplicates)
      - `cookie_secure` must be `true` if `cookie_samesite` is `"none"`
    
    - SUB-TASKS:
      - Update all existing agent config.yaml files (5 agents: agrofresh, wyckoff, prepexcellence, simple_chat1, simple_chat2)
      - Add session.cookie_name for each agent using format: `{account}_{instance}_sk`
      - Add cookie configuration validation to `config_loader.py`
      - Create `get_agent_cookie_config()` function in `config_loader.py`
      - Add uniqueness check: verify no duplicate cookie names across agents
      - Document cookie configuration in `backend/README.md`
    
    - AUTOMATED-TESTS: `backend/tests/unit/test_cookie_config.py`
      - `test_cookie_config_loads()` - Verify cookie config loads from agent YAML
      - `test_cookie_name_validation()` - Test pattern validation (alphanumeric + underscores + "_sk" suffix)
      - `test_cookie_name_length_limit()` - Verify 50 character limit enforced
      - `test_cookie_name_uniqueness()` - Verify no duplicate names across agents
      - `test_cookie_defaults()` - Verify default values (max_age=30 days, secure=true, etc.)
      - `test_invalid_cookie_configs()` - Test error handling for malformed configs
    
    - MANUAL-TESTS:
      - Review all 5 agent config.yaml files for correct cookie_name values
      - Verify each cookie_name matches format: `{account}_{instance}_sk`
      - Check for duplicate cookie names: `grep -r "cookie_name:" backend/config/agent_configs/`
      - Test config loader: `python -c "from app.services.config_loader import get_agent_cookie_config; print(get_agent_cookie_config('prepexcellence/prepexcel_info_chat1'))"`
      - Verify validation errors for invalid cookie names
    
    - STATUS: Planned — Configuration structure defined
    - PRIORITY: High — Foundation for session isolation

  - [ ] 0017-007-001-002 - CHUNK - Update session middleware for per-agent cookies
    - **PURPOSE**: Modify backend session middleware to use agent-specific cookie names
    
    - **IMPLEMENTATION APPROACH**:
      ```python
      # backend/app/middleware/session_middleware.py
      
      from app.services.config_loader import get_agent_cookie_config
      
      async def get_or_create_session(request: Request, account: str, agent: str) -> Session:
          """
          Get or create session using agent-specific cookie name.
          
          Args:
              request: FastAPI request object
              account: Account slug (e.g., "prepexcellence")
              agent: Agent instance slug (e.g., "prepexcel_info_chat1")
          
          Returns:
              Session object with proper cookie configuration
          """
          # 1. Load agent cookie config
          cookie_config = get_agent_cookie_config(f"{account}/{agent}")
          cookie_name = cookie_config["cookie_name"]
          
          # 2. Check for existing session via agent-specific cookie
          session_id = request.cookies.get(cookie_name)
          
          if session_id:
              # Retrieve existing session from database
              session = await get_session_by_id(session_id)
              if session:
                  return session
          
          # 3. Create new session with agent context
          new_session = await create_session(
              account_id=get_account_id(account),
              agent_instance_id=get_agent_instance_id(account, agent)
          )
          
          return new_session
      
      def set_session_cookie(response: Response, session: Session, cookie_config: dict):
          """
          Set session cookie with agent-specific name and attributes.
          
          Args:
              response: FastAPI response object
              session: Session object
              cookie_config: Cookie configuration from agent config.yaml
          """
          response.set_cookie(
              key=cookie_config["cookie_name"],
              value=str(session.id),
              max_age=cookie_config.get("cookie_max_age", 2592000),  # 30 days default
              domain=cookie_config.get("cookie_domain"),  # None = current domain
              secure=cookie_config.get("cookie_secure", True),
              httponly=cookie_config.get("cookie_httponly", True),
              samesite=cookie_config.get("cookie_samesite", "lax")
          )
      ```
    
    - **SECURITY ENHANCEMENTS**:
      - Validate session ID format (UUID4) before database lookup
      - Add session expiry check (delete expired sessions)
      - Implement CSRF token validation for state-changing operations
      - Add rate limiting per session ID (prevent session enumeration)
    
    - SUB-TASKS:
      - Update `session_middleware.py` to accept `account` and `agent` parameters
      - Modify `get_or_create_session()` to load agent cookie config
      - Update cookie reading logic to use agent-specific cookie name
      - Update cookie writing logic in response with agent-specific name and attributes
      - Remove old global cookie name constants (breaking change)
      - Update all endpoint handlers to pass account/agent to session middleware
      - Add session ID validation (must be valid UUID4)
      - Implement session expiry cleanup (delete sessions older than max_age)
      - Add logging for cookie operations (set, read, errors)
    
    - AUTOMATED-TESTS: `backend/tests/integration/test_session_middleware_cookies.py`
      - `test_session_cookie_created_with_agent_name()` - Verify agent-specific cookie name used
      - `test_session_cookie_attributes()` - Test secure, httponly, samesite attributes
      - `test_session_cookie_isolation()` - Multiple agents create separate cookies
      - `test_session_retrieval_by_cookie()` - Verify session lookup by agent-specific cookie
      - `test_invalid_session_id_format()` - Test rejection of malformed session IDs
      - `test_expired_session_cleanup()` - Verify expired sessions are deleted
      - `test_missing_cookie_creates_new_session()` - Test new session creation flow
    
    - MANUAL-TESTS:
      - Start backend, navigate to `http://localhost:4321/prepexcellence/`
      - Open DevTools → Application → Cookies
      - Send chat message, verify cookie created: `prepexcellence_prepexcel_info_chat1_sk`
      - Check cookie attributes: Secure=true, HttpOnly=true, SameSite=Lax
      - Navigate to `http://localhost:4321/wyckoff/`
      - Send chat message, verify separate cookie: `wyckoff_wyckoff_info_chat1_sk`
      - Verify both cookies coexist with different session IDs
      - Test session persistence: Refresh page, verify same session ID used
      - Clear cookies, verify new session created on next message
    
    - STATUS: Planned — Session middleware updated
    - PRIORITY: High — Core backend functionality

  - [ ] 0017-007-001-003 - CHUNK - Update chat widget for per-agent cookies
    - **PURPOSE**: Modify frontend chat widget to read/write agent-specific cookies
    
    - **WIDGET COOKIE HANDLING**:
      ```javascript
      // public/widget/chat-widget.js
      
      class SalientChatWidget {
          constructor(config) {
              this.config = config;
              // Generate agent-specific cookie name from config
              this.cookieName = `${config.account}_${config.agent}_sk`;
          }
          
          /**
           * Get session ID from agent-specific cookie
           * @returns {string|null} Session ID or null if not found
           */
          getSessionId() {
              const cookies = document.cookie.split(';');
              for (let cookie of cookies) {
                  const [name, value] = cookie.trim().split('=');
                  if (name === this.cookieName) {
                      return value;
                  }
              }
              return null;
          }
          
          /**
           * Set session ID in agent-specific cookie (if needed)
           * Note: Backend sets the cookie, widget only reads it
           * @param {string} sessionId - Session ID from backend response
           */
          setSessionId(sessionId) {
              // Widget primarily READS cookies set by backend
              // Only sets cookie if backend didn't (edge case)
              if (!this.getSessionId()) {
                  document.cookie = `${this.cookieName}=${sessionId}; path=/; max-age=2592000; SameSite=Lax; Secure`;
              }
          }
          
          /**
           * Include session ID in API requests
           */
          async sendMessage(message) {
              const sessionId = this.getSessionId();
              
              const response = await fetch(`${this.config.backend}/accounts/${this.config.account}/agents/${this.config.agent}/chat`, {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json'
                  },
                  credentials: 'include',  // Send cookies with request
                  body: JSON.stringify({
                      message: message,
                      session_id: sessionId  // Optional: can also rely on cookie
                  })
              });
              
              return response;
          }
      }
      ```
    
    - **CROSS-ORIGIN CONSIDERATIONS**:
      - Widget embedded in `prepexcellence.com` must send cookies to `localhost:8000`
      - Backend must set `Access-Control-Allow-Credentials: true`
      - Backend must set `Access-Control-Allow-Origin` to specific origin (not `*`)
      - Cookie must have `SameSite=None; Secure` for cross-origin (if needed)
    
    - SUB-TASKS:
      - Update widget constructor to generate cookie name from `config.account` and `config.agent`
      - Modify `getSessionId()` to read agent-specific cookie name
      - Update `sendMessage()` to include `credentials: 'include'` for cookie transmission
      - Add cookie name validation in widget (match backend pattern)
      - Update widget initialization to log cookie name for debugging
      - Test cross-origin cookie handling (embedded widget scenarios)
      - Add error handling for missing/invalid cookies
      - Document widget cookie behavior in `web/README.md`
    
    - AUTOMATED-TESTS: `web/tests/test_widget_cookies.spec.ts` (Playwright)
      - `test_widget_reads_agent_cookie()` - Verify widget reads correct cookie name
      - `test_widget_sends_credentials()` - Verify cookies sent with API requests
      - `test_multiple_widgets_different_cookies()` - Test widget isolation (multiple agents on same page)
      - `test_cross_origin_cookie_handling()` - Test embedded widget cookie behavior
      - `test_missing_cookie_creates_new_session()` - Verify new session flow when cookie absent
    
    - MANUAL-TESTS:
      - Navigate to `http://localhost:4321/prepexcellence/`
      - Open DevTools Console, check for cookie name log: "Using cookie: prepexcellence_prepexcel_info_chat1_sk"
      - Send chat message, verify Network tab shows cookie sent with request
      - Navigate to `http://localhost:4321/wyckoff/`
      - Verify different cookie name logged: "Using cookie: wyckoff_wyckoff_info_chat1_sk"
      - Open two different agent pages in separate tabs
      - Verify each tab uses its own cookie (check DevTools → Application → Cookies)
      - Test conversation persistence: Send messages, refresh page, verify history loads
      - Test cross-origin: Embed widget in external site (if applicable), verify cookies work
    
    - STATUS: Planned — Widget cookie handling updated
    - PRIORITY: High — Frontend integration required

  - [ ] 0017-007-001-004 - CHUNK - Database cleanup and migration
    - **PURPOSE**: Clean up old session data and verify no legacy cookie dependencies
    
    - **CLEANUP STRATEGY**:
      - Delete all existing sessions (breaking change, no backwards compatibility)
      - Verify no hardcoded cookie names remain in codebase
      - Update session creation to always use agent-specific cookies
      - Add database indexes for efficient session lookup by account/agent
    
    - **MIGRATION SCRIPT**:
      ```python
      # backend/scripts/cleanup_legacy_sessions.py
      
      async def cleanup_legacy_sessions():
          """
          Delete all existing sessions (breaking change).
          No migration needed since there's no backwards compatibility.
          """
          async with get_db_session() as db:
              # Count existing sessions
              count = await db.execute("SELECT COUNT(*) FROM sessions")
              total = count.scalar()
              
              print(f"Found {total} existing sessions")
              print("Deleting all sessions (breaking change)...")
              
              # Delete all sessions
              await db.execute("DELETE FROM sessions")
              await db.commit()
              
              print(f"✅ Deleted {total} sessions")
              print("All users will need to start new sessions with agent-specific cookies")
      ```
    
    - SUB-TASKS:
      - Create cleanup script: `backend/scripts/cleanup_legacy_sessions.py`
      - Add confirmation prompt before deletion ("Are you sure? [y/N]")
      - Delete all records from `sessions` table
      - Delete orphaned records from `messages` table (if foreign key not set to CASCADE)
      - Verify no hardcoded cookie names in codebase: `grep -r "salient_session" backend/`
      - Add database index: `CREATE INDEX idx_sessions_account_agent ON sessions(account_id, agent_instance_id);`
      - Document breaking change in `CHANGELOG.md`
      - Update deployment documentation with cleanup steps
    
    - AUTOMATED-TESTS: `backend/tests/integration/test_session_cleanup.py`
      - `test_cleanup_script_deletes_all_sessions()` - Verify all sessions deleted
      - `test_no_orphaned_messages()` - Verify foreign key CASCADE or manual cleanup works
      - `test_fresh_session_creation()` - Verify new sessions work after cleanup
    
    - MANUAL-TESTS:
      - Backup database before running cleanup: `pg_dump salient_dev > backup_before_cookie_migration.sql`
      - Check existing session count: `SELECT COUNT(*) FROM sessions;`
      - Run cleanup script: `python backend/scripts/cleanup_legacy_sessions.py`
      - Verify sessions deleted: `SELECT COUNT(*) FROM sessions;` (should be 0)
      - Test new session creation: Send chat message via widget
      - Verify new session created with agent-specific cookie: `SELECT * FROM sessions ORDER BY created_at DESC LIMIT 5;`
      - Check no hardcoded cookie names: `grep -rn "salient_session[^_]" backend/`
      - Verify database indexes: `\d sessions` in psql
    
    - STATUS: Planned — Database cleanup and verification
    - PRIORITY: Medium — Cleanup before deployment

  - [ ] 0017-007-001-005 - CHUNK - End-to-end testing and documentation
    - **PURPOSE**: Comprehensive testing of per-agent cookie isolation and user documentation
    
    - **END-TO-END TEST SCENARIOS**:
      1. **Single Agent Conversation**:
         - User visits PrepExcellence site
         - Sends messages, verify correct cookie created
         - Refresh page, verify session persists
         - Clear cookie, verify new session created
      
      2. **Multi-Agent Isolation**:
         - User opens PrepExcellence tab (tab A)
         - User opens Wyckoff tab (tab B)
         - Send messages in both tabs
         - Verify separate cookies and sessions for each
         - Verify conversation history doesn't leak between tabs
      
      3. **Cross-Origin Widget**:
         - Embed widget in external site (if applicable)
         - Verify cookies work across origins
         - Test SameSite and Secure attributes
      
      4. **Session Expiry**:
         - Create session, wait for max_age to expire (or manually age session in DB)
         - Verify expired session deleted
         - Verify new session created on next request
      
      5. **Security Testing**:
         - Attempt session hijacking with wrong cookie name
         - Verify CSRF protection (if implemented)
         - Test malformed session IDs rejected
    
    - **DOCUMENTATION UPDATES**:
      - Update `backend/README.md` with cookie configuration guide
      - Update `web/README.md` with widget cookie behavior
      - Document cookie name format and validation rules
      - Add troubleshooting guide for cookie issues
      - Update API documentation with cookie requirements
      - Document breaking change in `CHANGELOG.md`
      - Add migration guide for future deployments
    
    - SUB-TASKS:
      - Create comprehensive E2E test suite: `web/tests/e2e_cookie_isolation.spec.ts`
      - Test all 5 scenarios listed above
      - Add session expiry testing (manual or time-mocked)
      - Security testing: malformed cookies, session hijacking attempts
      - Update `backend/README.md` with cookie configuration section
      - Update `web/README.md` with widget cookie documentation
      - Create troubleshooting guide: `docs/troubleshooting-cookies.md`
      - Document breaking change in `CHANGELOG.md`
      - Add cookie migration guide for future deployments
    
    - AUTOMATED-TESTS: `web/tests/e2e_cookie_isolation.spec.ts` (Playwright)
      - `test_single_agent_session_persistence()` - Single agent conversation flow
      - `test_multi_agent_cookie_isolation()` - Multiple agents, separate sessions
      - `test_cross_origin_widget_cookies()` - Cross-origin cookie handling (if applicable)
      - `test_session_expiry_and_renewal()` - Expired session cleanup and new session creation
      - `test_malformed_cookie_rejection()` - Security: reject invalid session IDs
      - `test_cross_account_session_isolation()` - Verify agrofresh session ≠ wyckoff session
    
    - MANUAL-TESTS:
      - **Scenario 1: Single Agent**
        - Navigate to `http://localhost:4321/prepexcellence/`
        - Send 3-5 messages, verify conversation builds up
        - Refresh page, verify history persists (same cookie)
        - Clear cookies in DevTools, send new message
        - Verify new cookie created with different session ID
      
      - **Scenario 2: Multi-Agent Isolation**
        - Open `http://localhost:4321/prepexcellence/` in tab 1
        - Open `http://localhost:4321/wyckoff/` in tab 2
        - Send messages in both tabs
        - Verify DevTools shows different cookies (prepexcellence_* vs wyckoff_*)
        - Verify conversation history doesn't appear in wrong tab
      
      - **Scenario 3: Database Verification**
        - Query sessions: `SELECT account_slug, agent_instance_slug, session_id FROM sessions JOIN accounts ON sessions.account_id = accounts.id;`
        - Verify each session tied to correct account and agent
        - Check messages: `SELECT session_id, role, content FROM messages ORDER BY created_at DESC LIMIT 10;`
        - Verify no cross-session message leakage
      
      - **Scenario 4: Security Testing**
        - Manually edit cookie in DevTools to invalid UUID
        - Send message, verify backend rejects and creates new session
        - Try cookie from one agent on another agent's endpoint
        - Verify backend creates new session (no hijacking)
      
      - **Scenario 5: Documentation Review**
        - Read `backend/README.md` cookie configuration section
        - Follow steps to configure new agent
        - Verify documentation is clear and complete
        - Check troubleshooting guide covers common issues
    
    - STATUS: Planned — Final validation and documentation
    - PRIORITY: High — Required for release

**TESTING SUMMARY**:

**AUTOMATED-TESTS** (25 tests total):
- **Unit Tests**: `test_cookie_config.py` (6 tests - config validation)
- **Integration Tests**: `test_session_middleware_cookies.py` (7 tests - backend session handling)
- **Integration Tests**: `test_session_cleanup.py` (3 tests - database cleanup)
- **Widget Tests**: `test_widget_cookies.spec.ts` (5 tests - frontend cookie handling)
- **E2E Tests**: `e2e_cookie_isolation.spec.ts` (6 tests - full stack validation)

**MANUAL-TESTS**:
- Configuration verification (5 agents, cookie names, uniqueness)
- Backend session middleware testing (cookie creation, attributes, isolation)
- Widget integration testing (cookie reading, API requests, cross-origin)
- Database cleanup verification (session deletion, fresh start)
- End-to-end scenarios (5 scenarios covering all use cases)
- Security testing (malformed cookies, session hijacking)

**DOCUMENTATION UPDATES**:
- `backend/README.md` - Cookie configuration guide
- `web/README.md` - Widget cookie behavior
- `docs/troubleshooting-cookies.md` - Troubleshooting guide (NEW)
- `CHANGELOG.md` - Breaking change documentation
- API documentation - Cookie requirements

## Priority 2D: Profile Configuration & Schema

### 0017-006 - FEATURE - Profile Fields Configuration & Database Schema
**Status**: Planned

Configure dynamic profile fields per agent instance via separate profile.yaml file (following directory_schemas pattern) and migrate profiles table to JSONB storage.

**Pattern**: Similar to how directory schemas are defined in `backend/config/directory_schemas/*.yaml`, profile schemas are defined per-instance in `backend/config/agent_configs/{account}/{instance}/profile.yaml`.

- [ ] 0017-006-001 - TASK - Profile Tool Enable/Disable in Agent Config
  - [ ] 0017-006-001-01 - CHUNK - Add profile_capture enable switch to config.yaml
    - SUB-TASKS:
      - Add `tools.profile_capture.enabled` boolean to agent instance config.yaml
      - Follow same pattern as other tools (vector_search, directory, web_search)
      - Configuration loaded via agent config loader (per-agent-instance)
    - STATUS: Planned — Profile tool enabled/disabled per agent instance
    - LOCATION: `backend/config/agent_configs/{account_slug}/{instance_slug}/config.yaml`
    - EXAMPLE CONFIG STRUCTURE:
      ```yaml
      tools:
        profile_capture:
          enabled: true
      
  - [ ] 0017-006-001-02 - CHUNK - Create profile schema loader helper (following DirectoryImporter pattern)
    - SUB-TASKS:
      - Create ProfileSchemaLoader class similar to DirectoryImporter.load_schema()
      - Load profile.yaml from agent instance folder
      - Validate YAML structure and required fields
      - Return structured profile schema dict
      - Handle missing file gracefully (if profile_capture disabled)
    - STATUS: Planned — Profile schema loader following directory schema pattern
  
  - [ ] 0017-006-001-03 - CHUNK - Create profile.yaml file structure (following directory_schemas pattern)
    - SUB-TASKS:
      - Create profile.yaml file in agent instance folder
      - Follow same structural pattern as directory_schemas/*.yaml files
      - Include metadata (profile_version, description)
      - Define required_fields and optional_fields lists
      - Define fields section with type, validation, description, examples
      - Add semantic_hints per field (what to look for)
      - Add capture_hints section for modular prompt integration
      - Add examples showing when/how to capture each field
    - STATUS: Planned — Profile fields defined in separate file following directory schema pattern
    - LOCATION: `backend/config/agent_configs/{account_slug}/{instance_slug}/profile.yaml`
    - PATTERN: Similar to `backend/config/directory_schemas/*.yaml` structure
    - EXAMPLE PROFILE.YAML STRUCTURE:
      ```yaml
      profile_version: "1.0"
      description: "Profile fields for simple-chat agent - contact information capture"
      
      # Required fields that must be captured
      required_fields:
        - email
      
      # Optional fields that may be captured
      optional_fields:
        - phone
      
      # Field definitions with validation and semantic guidance
      fields:
        email:
          type: email
          required: true
          validation: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
          description: "User's email address for follow-up communication"
          examples:
            - "user@example.com"
            - "john.doe@company.org"
          semantic_hints: |
            Look for email addresses when user mentions:
            - Wanting to receive information via email
            - Requesting email summaries or follow-ups
            - Providing contact information
            - Asking about email notifications
            - Saying "send it to me" or "email me"
        
        phone:
          type: phone
          required: false
          validation: "^\\+?[1-9]\\d{1,14}$"
          description: "User's phone number (optional)"
          examples:
            - "718-963-7272"
            - "+1-718-963-7272"
          semantic_hints: |
            Look for phone numbers when user mentions:
            - Appointment scheduling needs
            - Urgent contact requirements
            - Phone call preferences
            - Contact information sharing
            - Saying "call me" or "text me"
      
      # Guidance for LLM on when/how to capture profile information
      capture_hints: |
        Capture user contact information naturally during conversation.
        
        **When to capture email:**
        - User requests follow-up information or email summaries
        - User asks to be notified about something
        - User provides email address voluntarily
        - Conversation context suggests email would be useful
        
        **When to capture phone:**
        - User needs appointment scheduling
        - User requests urgent contact
        - User provides phone number voluntarily
        - Conversation context suggests phone contact would be useful
        
        **How to capture:**
        - Be conversational and explain why the information is needed
        - Don't be pushy - only ask when contextually relevant
        - Validate format before storing
        - Confirm captured information back to user
      
      # Example scenarios for LLM guidance
      examples:
        - user_query: "Can you email me more information?"
          action: "Capture email address - user explicitly requested email"
          tool_call: 'capture_profile_field(field="email", value="user@example.com")'
        
        - user_query: "I'd like to schedule an appointment"
          action: "Capture phone number - needed for appointment scheduling"
          tool_call: 'capture_profile_field(field="phone", value="718-963-7272")'
        
        - user_query: "My email is john@example.com"
          action: "Capture email - user provided voluntarily"
          tool_call: 'capture_profile_field(field="email", value="john@example.com")'
  
  - [ ] 0017-006-001-04 - CHUNK - Create profile.yaml for hospital sites (Wyckoff & Wind River)
    - SUB-TASKS:
      - Create profile.yaml for `wyckoff/wyckoff_info_chat1/`
      - Create profile.yaml for `windriver/windriver_info_chat1/`
      - Define fields: relationship_to_patient, health_issue, mailing_address, email, phone
      - Add semantic hints for each field (when to capture)
      - Add capture_hints specific to hospital visitor context
      - Include examples for hospital visitor scenarios
    - STATUS: Planned — Hospital visitor profile capture
    - LOCATIONS:
      - `backend/config/agent_configs/wyckoff/wyckoff_info_chat1/profile.yaml`
      - `backend/config/agent_configs/windriver/windriver_info_chat1/profile.yaml`
    - EXAMPLE FIELDS:
      - `relationship_to_patient`: Self, Parent, Guardian, Spouse, Other
      - `health_issue`: Primary health concern or reason for visit
      - `mailing_address`: Full address for mailings/appointments
      - `email`: Contact email (required)
      - `phone`: Contact phone (required)
      - `preferred_contact_method`: Email, Phone, Text
      - `insurance_provider`: Optional - for appointment scheduling
      - `preferred_appointment_time`: Morning, Afternoon, Evening
  
  - [ ] 0017-006-001-05 - CHUNK - Create profile.yaml for Prepexcellence (student prep site)
    - SUB-TASKS:
      - Create profile.yaml for `prepexcellence/prepexcel_info_chat1/`
      - Define fields: relationship_to_student, mailing_address, email, phone, current_grade, colleges_interested_in
      - Add semantic hints for each field (when to capture)
      - Add capture_hints specific to student prep/college counseling context
      - Include examples for student intake scenarios
    - STATUS: Planned — Student prep profile capture
    - LOCATION: `backend/config/agent_configs/prepexcellence/prepexcel_info_chat1/profile.yaml`
    - EXAMPLE FIELDS:
      - `relationship_to_student`: Parent, Guardian, Student (self), Other
      - `mailing_address`: Full address for materials/communications
      - `email`: Contact email (required)
      - `phone`: Contact phone (required)
      - `current_grade`: Current grade level (9, 10, 11, 12, etc.)
      - `colleges_interested_in`: List of colleges/universities student is considering
      - `student_name`: Name of the student
      - `test_prep_needs`: SAT, ACT, AP exams, etc.
      - `college_major_interest`: Intended major or field of study
      - `application_deadline_urgency`: Timeline for college applications
      - `budget_range`: Optional - for program recommendations
  
  - [ ] 0017-006-001-06 - CHUNK - Create profile.yaml for Agrofresh (agrotech company)
    - SUB-TASKS:
      - Create profile.yaml for `agrofresh/agro_info_chat1/`
      - Define fields: name, email, phone, products_interested_in, produce_types, delivery_location, urgency
      - Add semantic hints for each field (when to capture)
      - Add capture_hints specific to agrotech/agricultural product inquiries
      - Include examples for product inquiry and order scenarios
    - STATUS: Planned — Agrotech customer profile capture
    - LOCATION: `backend/config/agent_configs/agrofresh/agro_info_chat1/profile.yaml`
    - EXAMPLE FIELDS:
      - `name`: Full name (required)
      - `email`: Contact email (required)
      - `phone`: Contact phone (required)
      - `products_interested_in`: Specific products or product categories
      - `produce_types`: Types of produce (fruits, vegetables, grains, etc.)
      - `delivery_location`: Full address for product delivery
      - `urgency`: Immediate, Within week, Within month, Just browsing
      - `business_type`: Farm, Restaurant, Retail, Distributor, Individual
      - `order_quantity`: Estimated quantity needed
      - `growing_season`: Current season or planned growing season
      - `organic_preference`: Organic, Conventional, Either
      - `contact_preference`: Email, Phone, Text, In-person visit
  
- [ ] 0017-006-002 - TASK - Migrate Profiles Table to JSONB
  - [ ] 0017-006-002-01 - CHUNK - Add JSONB fields to profiles table
    - SUB-TASKS:
      - Add `required_profile_fields` JSONB column
      - Add `captured_profile_fields` JSONB column  
      - Add `required_fields_updated_at` timestamp column
    - STATUS: Planned — JSONB storage for flexible profiles
    - NOTE: Review and elaborate when implementing migration from hardcoded columns
  
  - [ ] 0017-006-002-02 - CHUNK - Remove hardcoded profile columns
    - SUB-TASKS:
      - Migrate existing data to JSONB fields
      - Remove email, phone, and other hardcoded columns
      - Update SQLAlchemy ORM models
    - STATUS: Planned — Clean schema using JSONB
    - NOTE: Review and elaborate migration strategy before implementing

## Priority 2D: Profile Capture Tool

### 0017-012 - FEATURE - Profile Capture Tool
**Status**: Planned

Implement agent tool to capture and validate profile information during conversation.

**Note**: Renumbered from 0017-007 to 0017-012 to avoid conflict with Per-Agent Cookie Configuration (Priority 10).

- [ ] 0017-012-001 - TASK - Profile Capture Agent Tool
  - [ ] 0017-012-001-01 - CHUNK - Implement @agent.tool for profile capture
    - SUB-TASKS:
      - Check if profile_capture tool is enabled in agent instance config.yaml
      - Load profile.yaml file from agent instance folder (similar to DirectoryImporter.load_schema pattern)
      - Path: `backend/config/agent_configs/{account_slug}/{instance_slug}/profile.yaml`
      - Tool reads field definitions from profile.yaml (required_fields, optional_fields, fields section)
      - Tool validates captured data against configured field definitions (validation regex)
      - Stores data in captured_profile_fields JSONB
      - Checks required_fields_updated_at and refreshes if stale (24h)
      - Returns validation results to agent
    - STATUS: Planned — Agent captures profile during conversation
    - PATTERN: Follows same loading pattern as directory schemas (DirectoryImporter.load_schema)
  
  - [ ] 0017-012-001-02 - CHUNK - Integrate Profile Capture Hints into Modular Prompts
    - SUB-TASKS:
      - Load capture_hints and semantic_hints from agent instance profile.yaml
      - Create profile_capture_hints.md module file (or inject directly)
      - Integrate hints into prompt assembly via PromptBreakdownService
      - Include semantic hints per field to guide LLM on what to look for
      - Include capture_hints to guide LLM on when/how to use profile capture tool
      - Follow same pattern as tool_selection_hints.md and directory_selection_hints.md
    - STATUS: Planned — Hints guide LLM profile capture behavior

## Priority 2E: Email Summary with Mailgun

### 0017-008 - FEATURE - Email Summary Tool with Mailgun
**Status**: Planned

Implement agent tool to generate conversation summary and email via Mailgun.

- [ ] 0017-008-001 - TASK - Mailgun Integration
  - [ ] 0017-008-001-01 - CHUNK - Mailgun service setup
    - SUB-TASKS:
      - Configure Mailgun API credentials
      - Email template for conversation summaries
      - Error handling and delivery tracking
    - STATUS: Planned — Mailgun email service

- [ ] 0017-008-002 - TASK - Email Summary Agent Tool  
  - [ ] 0017-008-002-01 - CHUNK - Implement @agent.tool for email summary
    - SUB-TASKS:
      - Check profile completeness before sending
      - Request missing required fields if needed
      - Generate conversation summary using LLM
      - Send email via Mailgun when profile complete
      - Configuration setting for auto-send behavior
    - STATUS: Planned — Agent emails summaries when requested

---

# PHASE 2: Enhanced Functionality

Optional enhancements that extend InfoBot capabilities beyond core MVP.

## Priority 2F: Email Capture & Consent (Optional)

### 0017-009 - FEATURE - Email Capture & User Consent
**Status**: Planned
**NOTE**: May be superseded by Profile Capture Tool (0017-007) - review requirements during implementation.

Capture user email addresses and manage email-related permissions and approvals with standard email validation.

- [ ] 0017-009-001 - TASK - Email Collection System
  - [ ] 0017-009-001-01 - CHUNK - Email capture UI and API
    - SUB-TASKS:
      - Create email input component for web interface
      - Add `/api/capture-email` endpoint with HTML5 email validation
      - Email format validation and domain verification (no external API needed)
      - Integration with session management for email association
    - AUTOMATED-TESTS:
      - `test_email_validation()` - Test email format and domain validation
      - `test_email_session_association()` - Verify email tied to session correctly
    - MANUAL-TESTS:
      - Test email capture UI flow in browser
      - Verify email validation works with various formats
    - STATUS: Planned — Email collection mechanism
    - PRIORITY: High — Required for authentication and email features

  - [ ] 0017-009-001-02 - CHUNK - Consent and preferences management
    - SUB-TASKS:
      - Create consent tracking database schema (email_consents table)
      - Implement consent checkbox UI with clear privacy messaging
      - Email preferences system (summary frequency, content type)
      - GDPR compliance features (consent withdrawal, data deletion)
    - AUTOMATED-TESTS:
      - `test_consent_tracking()` - Test consent storage and retrieval
      - `test_consent_withdrawal()` - Test GDPR compliance features
    - MANUAL-TESTS:
      - Test consent flow UI experience
      - Verify consent withdrawal works correctly
    - STATUS: Planned — User consent and privacy compliance
    - PRIORITY: High — Legal compliance requirement

## Priority 2G: Periodic Summarization

### 0017-010 - FEATURE - Periodic Conversation Summarization
**Status**: Planned

Automatically summarize older conversation parts to prevent context window overflow and maintain conversation continuity.

- [ ] 0017-010-001 - TASK - Context Window Management System
  - [ ] 0017-010-001-01 - CHUNK - Token counting and threshold monitoring
    - SUB-TASKS:
      - Create token counting service using tiktoken or similar for accurate LLM token estimation
      - Configure context window thresholds per model (GPT-4: 8K, DeepSeek: 32K, etc.)
      - Add conversation monitoring to track approaching context limits
      - Integration with existing message history loading system
    - AUTOMATED-TESTS:
      - `test_token_counting_accuracy()` - Verify token counts match LLM expectations
      - `test_threshold_detection()` - Test context limit detection triggers correctly
    - MANUAL-TESTS:
      - Test token counting with various conversation lengths and message types
      - Verify threshold monitoring triggers at expected conversation lengths
    - STATUS: Planned — Foundation for context management
    - PRIORITY: Critical — Prevents conversation failures

  - [ ] 0017-010-001-02 - CHUNK - Conversation summarization engine
    - SUB-TASKS:
      - Create conversation summarization logic using existing OpenAI/OpenRouter LLM
      - Implement sliding window approach (keep recent N messages, summarize older ones)
      - Smart summarization that preserves key context, decisions, and user preferences
      - Configurable summarization strategies (aggressive vs conservative compression)
    - AUTOMATED-TESTS:
      - `test_conversation_summarization_quality()` - Test summary preserves key information
      - `test_sliding_window_logic()` - Verify correct messages selected for summarization
    - MANUAL-TESTS:
      - Review generated summaries for quality and context preservation
      - Test different conversation types (technical, casual, decision-making)
    - STATUS: Planned — Core summarization functionality
    - PRIORITY: High — Essential for context preservation

  - [ ] 0017-010-001-03 - CHUNK - Automatic summarization triggers
    - SUB-TASKS:
      - Implement automatic triggers when approaching context limits (80% threshold)
      - Background summarization process that doesn't interrupt user conversations
      - Message replacement strategy that maintains conversation flow
      - Logging and monitoring for summarization events and effectiveness
    - AUTOMATED-TESTS:
      - `test_automatic_trigger_timing()` - Test triggers activate at correct thresholds
      - `test_conversation_continuity()` - Verify seamless user experience during summarization
    - MANUAL-TESTS:
      - Test automatic summarization during long conversations
      - Verify conversation quality maintained after summarization events
    - STATUS: Planned — Seamless user experience
    - PRIORITY: High — User-facing functionality

## Priority 2H: OTP Authentication

### 0017-011 - FEATURE - OTP Authentication & Email-based Accounts  
**Status**: Planned

Implement OTP (One-Time Password) authentication system with email-based account creation using Twilio Verify.

- [ ] 0017-011-001 - TASK - OTP Authentication System
  - [ ] 0017-011-001-01 - CHUNK - Twilio Verify OTP integration
    - SUB-TASKS:
      - Create Twilio Verify service integration with API credentials
      - Configure OTP generation via Twilio Verify API (email channel)
      - Implement Twilio Verify verification checks with fraud protection
      - Rate limiting handled by Twilio Verify (built-in abuse prevention)
    - AUTOMATED-TESTS:
      - `test_twilio_verify_service_setup()` - Test Twilio Verify service initialization
      - `test_otp_verification_flow()` - Test OTP creation and verification via Twilio
    - MANUAL-TESTS:
      - Test OTP email delivery via Twilio Verify
      - Verify Twilio's built-in rate limiting and fraud protection
    - STATUS: Planned — OTP generation and delivery via Twilio Verify
    - PRIORITY: High — Core authentication security

  - [ ] 0017-011-001-02 - CHUNK - OTP verification and session upgrade
    - SUB-TASKS:
      - Create `/api/verify-otp` endpoint using Twilio Verify check API
      - Upgrade anonymous sessions to authenticated sessions after successful verification
      - Account creation for new emails, login for existing (post-verification)
      - Session persistence across browser restarts with secure tokens
    - AUTOMATED-TESTS:
      - `test_twilio_verify_check()` - Test Twilio Verify OTP validation
      - `test_session_upgrade()` - Verify anonymous → authenticated transition
    - MANUAL-TESTS:
      - Test complete OTP verification flow with Twilio Verify
      - Verify session persistence works correctly
    - STATUS: Planned — Authentication verification system via Twilio
    - PRIORITY: High — User authentication flow

  - [ ] 0017-011-001-03 - CHUNK - Account and session association
    - SUB-TASKS:
      - Create accounts database schema (users, user_sessions tables)
      - Link conversations to user accounts via email
      - Account profile management (email, preferences, created_at)
      - Cross-device session synchronization
    - AUTOMATED-TESTS:
      - `test_account_creation()` - Test user account creation flow
      - `test_conversation_association()` - Verify conversations tied to accounts
    - MANUAL-TESTS:
      - Test account creation and login flow end-to-end
      - Verify conversation history persists across devices
    - STATUS: Planned — Account management foundation
    - PRIORITY: Medium — User data persistence

## Priority 2I: Logging Infrastructure Consolidation

### 0017-013 - FEATURE - Migrate from Loguru to Logfire Logging
**Status**: Planned

Consolidate all logging to use Logfire for consistent observability, structured logging, and distributed tracing across the entire application.

**RATIONALE**: Currently the codebase uses mixed logging approaches (standard `logging`, `loguru`, and `logfire`). This creates inconsistency, makes troubleshooting harder, and prevents full utilization of Logfire's observability features. Standardizing on Logfire enables:
- Structured logging by default (queryable JSON)
- Distributed tracing across services
- Automatic Pydantic model instrumentation
- Production observability dashboard
- Consistent logging patterns across all modules

**CURRENT STATE**:
- ✅ `logfire` used in: `vector_service.py`, `directory_tools.py`, `prompt_generator.py`
- ⚠️ `loguru` used extensively in: `simple_chat.py`, most services
- ❌ Standard `logging` used in: some legacy modules

**TARGET STATE**: All modules use `logfire` exclusively with structured event naming.

**OUTPUT CONFIGURATION**: Logfire provides dual output for development and production:
- ✅ **Console output** (stdout/stderr) - Always enabled for local development visibility
- ✅ **Logfire cloud dashboard** - Enabled when `LOGFIRE_TOKEN` environment variable present
- ✅ **File output** (optional) - Can be added via standard Python logging handlers if needed

**DEFAULT BEHAVIOR**:
```python
import logfire

# Logfire configuration (already in simple_chat.py)
logfire.configure(
    send_to_logfire='if-token-present',  # Cloud only if token exists
    console=True  # ← Screen output always enabled (default)
)

logfire.info('agent.created', model='gpt-4')
# Output appears on screen (formatted, readable)
# AND in Logfire dashboard (structured, queryable)
```

This means **no loss of visibility** during development - you'll still see all logs on screen while gaining cloud observability.

- [ ] 0017-013-001 - TASK - Migrate Simple Chat Agent to Logfire
  - [ ] 0017-013-001-01 - CHUNK - Replace loguru imports with logfire in simple_chat.py
    - **PURPOSE**: Convert primary agent module to use Logfire for consistent observability
    
    - **MIGRATION PATTERN**:
      ```python
      # BEFORE (loguru)
      from loguru import logger
      
      logger.info({
          "event": "agent_creation_debug",
          "model_name": model_name,
          "has_api_key": bool(api_key)
      })
      
      # AFTER (logfire)
      import logfire
      
      logfire.info(
          'agent.creation_debug',
          model_name=model_name,
          has_api_key=bool(api_key)
      )
      ```
    
    - **EVENT NAMING CONVENTION**:
      - Use dot notation: `module.action` (e.g., `agent.creation_debug`, `session.load_history`)
      - Past tense for completed actions: `agent.created`, `session.loaded`
      - Present tense for ongoing: `agent.creating`, `session.loading`
      - Error events: `agent.error`, `session.load_error`
    
    - SUB-TASKS:
      - Replace `from loguru import logger` with `import logfire` in `simple_chat.py`
      - Convert all `logger.info()` calls to `logfire.info()` with structured event names
      - Convert all `logger.warning()` calls to `logfire.warn()`
      - Convert all `logger.error()` calls to `logfire.error()`
      - Convert all `logger.debug()` calls to `logfire.debug()`
      - Update log message format: dict syntax → keyword arguments
      - Add event name as first parameter to each log call
      - Verify `logfire.instrument_pydantic()` remains enabled (line 44)
      - Test all logging paths trigger correctly
    
    - AUTOMATED-TESTS: `backend/tests/unit/test_simple_chat_logging.py`
      - `test_no_loguru_imports()` - Verify no loguru imports remain
      - `test_all_logs_use_logfire()` - Verify all logging uses logfire
      - `test_event_naming_convention()` - Verify event names follow dot notation
      - `test_pydantic_instrumentation_enabled()` - Verify logfire.instrument_pydantic() present
    
    - MANUAL-TESTS:
      - Run backend, send chat message
      - **Verify console output**: Confirm logs appear on screen (terminal) with structured format
      - **Check Logfire dashboard**: Verify events appear with structured names and are queryable
      - **Verify dual output**: Confirm same events visible in BOTH console and Logfire dashboard
      - Check for any missed loguru calls: `grep -rn "logger\." backend/app/agents/simple_chat.py`
      - Compare console readability: loguru vs logfire output (both should be readable)
    
    - STATUS: Planned — Core agent logging migration
    - PRIORITY: High — Primary module for observability

  - [ ] 0017-013-001-02 - CHUNK - Migrate services to Logfire
    - **PURPOSE**: Convert all service modules to use Logfire for consistent observability
    
    - **MODULES TO MIGRATE**:
      ```
      backend/app/services/
      ├── message_service.py           # MIGRATE - Uses loguru
      ├── session_service.py           # MIGRATE - Uses loguru
      ├── llm_request_tracker.py       # MIGRATE - Uses loguru
      ├── agent_session.py             # MIGRATE - Uses loguru
      ├── embedding_service.py         # MIGRATE - Uses loguru (if applicable)
      ├── vector_service.py            # ✅ ALREADY USES LOGFIRE
      └── pinecone_client.py           # VERIFY - Check current logging
      ```
    
    - SUB-TASKS:
      - Audit all files in `backend/app/services/` for logging approach
      - Migrate each service module using same pattern as simple_chat.py
      - Create service-specific event naming (e.g., `message.saved`, `session.created`)
      - Update all log calls to structured format with keyword arguments
      - Add logfire spans for long-running operations (database queries, API calls)
      - Document service logging patterns in `backend/README.md`
    
    - AUTOMATED-TESTS: `backend/tests/unit/test_services_logging.py`
      - `test_no_loguru_in_services()` - Verify no loguru imports in services/
      - `test_all_services_use_logfire()` - Verify all services use logfire
      - `test_service_event_naming()` - Verify consistent event naming across services
    
    - MANUAL-TESTS:
      - Run backend, perform operations that trigger each service
      - Check Logfire dashboard: verify all service events appear
      - Verify service-specific events are properly structured
      - Test error logging: trigger errors, verify error events in Logfire
    
    - STATUS: Planned — Service layer logging consolidation
    - PRIORITY: High — Core infrastructure

  - [ ] 0017-013-001-03 - CHUNK - Add Logfire spans for performance tracking
    - **PURPOSE**: Enhance observability with distributed tracing spans for key operations
    
    - **SPAN TARGETS**:
      ```python
      # Agent execution
      with logfire.span('agent.run', message_length=len(message), session_id=session_id):
          result = await agent.run(message, deps=session_deps, message_history=message_history)
      
      # Database queries
      with logfire.span('database.query', table='messages', operation='load_history'):
          messages = await message_service.get_session_messages(session_id, limit=max_messages)
      
      # LLM requests
      with logfire.span('llm.request', model=model_name, provider='openrouter'):
          response = await client.chat.completions.create(...)
      
      # Vector search
      with logfire.span('vector.search', query_length=len(query), index=index_name):
          results = await vector_service.query_similar(...)
      ```
    
    - SUB-TASKS:
      - Add spans around agent.run() calls in simple_chat.py
      - Add spans around database operations in service modules
      - Add spans around LLM API calls (already present in vector_service.py)
      - Add spans around vector search operations
      - Nest spans appropriately (agent → llm → tool → database)
      - Include timing metrics in span attributes
      - Test span visibility in Logfire dashboard
    
    - AUTOMATED-TESTS: `backend/tests/integration/test_logfire_spans.py`
      - `test_agent_execution_span()` - Verify agent.run spans created
      - `test_database_query_spans()` - Verify database operation spans
      - `test_nested_span_hierarchy()` - Verify span nesting structure
      - `test_span_timing_metrics()` - Verify timing data captured
    
    - MANUAL-TESTS:
      - Run backend, send chat message
      - Open Logfire dashboard → Traces view
      - Verify complete trace: agent → database → llm → vector_search
      - Check span timing: identify slow operations
      - Test error spans: trigger errors, verify error spans appear
    
    - STATUS: Planned — Performance observability enhancement
    - PRIORITY: Medium — Advanced observability features

  - [ ] 0017-013-001-04 - CHUNK - Remove all loguru dependencies
    - **PURPOSE**: Complete migration by removing loguru from codebase and dependencies
    
    - **CLEANUP CHECKLIST**:
      - Remove `loguru` from `requirements.txt`
      - Remove `loguru` from `requirements-dev.txt` (if present)
      - Search codebase for any remaining loguru imports: `grep -r "from loguru import" backend/`
      - Search for logger pattern: `grep -r "logger\." backend/ | grep -v logfire`
      - Update CI/CD pipelines if loguru-specific configuration exists
      - Remove any loguru configuration files
      - Update documentation to reference Logfire only
    
    - SUB-TASKS:
      - Remove loguru from requirements.txt
      - Verify no remaining loguru imports in codebase
      - Update backend/README.md to remove loguru references
      - Update logging documentation to show Logfire examples only
      - Test application starts without loguru installed
      - Verify all tests pass without loguru
      - Update project-brief.md logging standards section
    
    - AUTOMATED-TESTS: `backend/tests/unit/test_no_loguru.py`
      - `test_loguru_not_in_requirements()` - Verify loguru removed from requirements.txt
      - `test_no_loguru_imports_in_codebase()` - Scan all Python files for loguru imports
      - `test_application_starts_without_loguru()` - Verify app runs without loguru installed
    
    - MANUAL-TESTS:
      - Uninstall loguru: `pip uninstall loguru`
      - Start backend: `uvicorn backend.app.main:app`
      - Verify application starts successfully
      - Send test requests, verify no import errors
      - Check logs: confirm all logging works via Logfire
      - Reinstall dependencies: `pip install -r requirements.txt`
      - Verify loguru NOT installed: `pip list | grep loguru`
    
    - STATUS: Planned — Complete migration cleanup
    - PRIORITY: Medium — Final cleanup step

**TESTING SUMMARY**:

**AUTOMATED-TESTS** (12 tests total):
- **Unit Tests**: `test_simple_chat_logging.py` (4 tests - agent logging migration)
- **Unit Tests**: `test_services_logging.py` (3 tests - service logging migration)
- **Integration Tests**: `test_logfire_spans.py` (4 tests - span tracking)
- **Unit Tests**: `test_no_loguru.py` (3 tests - cleanup verification)

**MANUAL-TESTS**:
- Simple chat agent logging verification (Logfire dashboard, file logs)
- Service module logging verification (all services tested)
- Span visibility and nesting in Logfire dashboard
- Application functionality without loguru installed

**DOCUMENTATION UPDATES**:
- `backend/README.md` - Update logging examples to use Logfire
- `memorybank/project-brief.md` - Already updated with Logfire standards
- `.cursor/rules/persona.mdc` - Already updated with diagnostic logging principles
- Remove any loguru-specific configuration documentation

**BENEFITS**:
- ✅ **Consistent observability** - Single logging approach across entire codebase
- ✅ **Structured logging** - All logs queryable in Logfire dashboard
- ✅ **Dual output** - Console logs for development + cloud dashboard for production (no loss of visibility)
- ✅ **Distributed tracing** - Full request flow visibility with spans
- ✅ **Production-ready** - Professional observability platform
- ✅ **Automatic instrumentation** - Pydantic models auto-logged
- ✅ **Better debugging** - Trace tool loops, LLM behavior, performance issues
- ✅ **Reduced complexity** - One logging library instead of three

## Definition of Done
- Agent implements Pydantic AI patterns with SessionDependencies integration
- `/agents/simple-chat/chat` endpoint functional with cost tracking
- Conversation history continuity across endpoints
- Vector search tool integrated (web search NOT included)
- Profile capture tool with JSONB storage
- Email summary tool with Mailgun integration
- Profile fields configured via YAML with validation
- Production-ready customer billing with accurate OpenRouter costs

