"""
Direct Pydantic AI Agent Implementation for Simple Chat.

This module implements a simple chat agent using Pydantic AI with:
- YAML configuration loading
- Session dependency injection  
- Dynamic model configuration from app.yaml and agent config
- Proper async/await patterns following Pydantic AI conventions

Key Components:
- create_simple_chat_agent(): Creates agent with YAML config
- get_chat_agent(): Lazy-loaded global agent instance
- simple_chat(): Main chat function with session handling

Dependencies:
- SessionDependencies from base.dependencies
- get_agent_config from config_loader
- load_config from app.config
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from .openrouter import OpenRouterModel, create_openrouter_provider_with_cost_tracking
from .base.dependencies import SessionDependencies
from ..config import load_config
from .config_loader import get_agent_config  # Fixed: correct function name
from ..services.message_service import get_message_service
from ..services.llm_request_tracker import LLMRequestTracker
from ..services.prompt_breakdown_service import PromptBreakdownService
from .chat_helpers import build_request_messages, build_response_body, extract_session_account_info, save_message_pair
from .cost_calculator import calculate_streaming_costs, track_chat_request
from .tools.toolsets import get_enabled_toolsets
from .tools.directory_tools import get_available_directories, search_directory
from .tools.vector_tools import vector_search
from typing import List, Optional
import uuid
from uuid import UUID
from datetime import datetime, UTC
import time
import os
import logfire

# Global agent instance (lazy loaded)
# Global caching disabled for production reliability
# _chat_agent = None  # Removed: Always create fresh agents

async def load_conversation_history(session_id: str, max_messages: Optional[int] = None) -> List[ModelMessage]:
    """
    Load conversation history from database and convert to Pydantic AI format.
    
    Retrieves recent messages for the session and converts them to Pydantic AI
    ModelMessage objects that can be passed to agent.run() for context continuation.
    
    Args:
        session_id: Session ID to load history for
        max_messages: Maximum number of recent messages to load (None to use config)
    
    Returns:
        List of Pydantic AI ModelMessage objects in chronological order
    """
    # Get max_messages from config if not provided
    if max_messages is None:
        from ..agents.config_loader import get_agent_history_limit
        max_messages = await get_agent_history_limit("simple_chat")
    
    message_service = get_message_service()
    
    # Convert string session_id to UUID
    try:
        session_uuid = uuid.UUID(session_id)
    except (ValueError, TypeError):
        # If session_id is not a valid UUID, return empty history
        return []
    
    # Retrieve recent messages from database
    db_messages = await message_service.get_session_messages(
        session_id=session_uuid,
        limit=max_messages
    )
    
    if not db_messages:
        return []
    
    # Convert database messages to Pydantic AI ModelMessage format
    pydantic_messages = []
    for msg in db_messages:
        # Convert based on role
        if msg.role in ("human", "user"):
            # Create user request message
            pydantic_message = ModelRequest(
                parts=[UserPromptPart(
                    content=msg.content,
                    timestamp=msg.created_at or datetime.now(UTC)
                )]
            )
        elif msg.role == "assistant":
            # Create assistant response message  
            pydantic_message = ModelResponse(
                parts=[TextPart(content=msg.content)],
                usage=None,  # Historical messages don't have usage data
                model_name="simple-chat",  # Agent name for historical messages
                timestamp=msg.created_at or datetime.now(UTC)
            )
        else:
            # Skip system messages and unknown roles (Pydantic AI handles system messages)
            continue
            
        pydantic_messages.append(pydantic_message)
    
    return pydantic_messages

async def create_simple_chat_agent(
    instance_config: Optional[dict] = None,
    account_id: Optional[UUID] = None
) -> tuple[Agent, dict, str]:  # Return agent, prompt_breakdown, and assembled system_prompt
    """
    Create a simple chat agent with OpenRouter provider for cost tracking.
    
    Args:
        instance_config: Optional instance-specific configuration. If provided, uses this
        account_id: Optional account ID for multi-tenant directory documentation generation
                        instead of loading the global config. This enables multi-tenant
                        support where each instance can have different model settings.
    
    Returns:
        tuple: (agent, prompt_breakdown, system_prompt)
    """
    config = instance_config if instance_config is not None else load_config()
    llm_config = config.get("model_settings", {})
    
    # Get OpenRouter configuration
    model_name = llm_config.get("model", "anthropic/claude-3.5-sonnet")
    api_key = llm_config.get("api_key") or os.getenv('OPENROUTER_API_KEY')
    
    # DEBUG: Log API key status
    logfire.info(
        'agent.creation.debug',
        model_name=model_name,
        has_api_key_in_config=bool(llm_config.get("api_key")),
        has_api_key_in_env=bool(os.getenv('OPENROUTER_API_KEY')),
        final_api_key_found=bool(api_key),
        api_key_source="config" if llm_config.get("api_key") else ("env" if os.getenv('OPENROUTER_API_KEY') else "none")
    )
    
    if not api_key:
        # Fallback to simple model name for development without API key
        model_name_simple = f"openrouter:{model_name}"
        
        # Get system_prompt from instance_config (multi-tenant) or fallback config (single-tenant)
        if instance_config is not None and 'system_prompt' in instance_config:
            system_prompt = instance_config['system_prompt']
        else:
            agent_config = await get_agent_config("simple_chat")
            system_prompt = agent_config.system_prompt
        
        logfire.warn(
            'agent.fallback_mode',
            reason="no_api_key",
            model_used=model_name_simple,
            cost_tracking="disabled"
        )
        
        # Build tools list based on agent configuration
        tools_list = []
        tools_config = (instance_config or {}).get("tools", {})
        
        # Add directory tools if enabled
        if tools_config.get("directory", {}).get("enabled", False):
            tools_list.extend([get_available_directories, search_directory])
        
        # Add vector search tool if enabled
        if tools_config.get("vector_search", {}).get("enabled", False):
            tools_list.append(vector_search)
        
        logfire.info(
            'agent.creation',
            agent_name=instance_config.get('instance_name', 'unknown') if instance_config else 'unknown',
            tools_count=len(tools_list),
            tool_names=[t.__name__ for t in tools_list],
            mode='fallback'
        )
        
        # Create minimal prompt breakdown for fallback mode
        prompt_breakdown = PromptBreakdownService.capture_breakdown(
            base_prompt=system_prompt,
            account_slug=None,
            agent_instance_slug=None
        )
        
        agent = Agent(
            model_name_simple,
            deps_type=SessionDependencies,
            system_prompt=system_prompt,
            tools=tools_list  # Direct tool functions
        )
        
        return agent, prompt_breakdown, system_prompt
    
    # PHASE 4A: Load critical tool selection rules FIRST (before everything else)
    # This ensures LLM sees tool selection guidance before tool descriptions
    from .tools.prompt_modules import load_prompt_module
    
    account_slug = None
    if instance_config:
        account_slug = instance_config.get("account")
    
    # Load tool selection hints at the very top of the prompt
    critical_rules = ""
    prompting_config = (instance_config or {}).get('prompting', {}).get('modules', {})
    if prompting_config.get('enabled', False):
        tool_selection_content = load_prompt_module("tool_selection_hints", account_slug)
        if tool_selection_content:
            critical_rules = tool_selection_content + "\n\n---\n\n"
            logfire.info(
                'agent.critical_rules.injected',
                module='tool_selection_hints',
                position='top_of_prompt',
                length=len(tool_selection_content)
            )
    
    # Load system prompt from instance_config (multi-tenant) or agent config (single-tenant)
    if instance_config is not None and 'system_prompt' in instance_config:
        # Multi-tenant mode: use the instance-specific system prompt
        base_system_prompt = instance_config['system_prompt']
        logfire.info(
            'agent.system_prompt.loaded',
            source='instance_config',
            length=len(base_system_prompt)
        )
    else:
        # Single-tenant mode: load from agent config file
        agent_config = await get_agent_config("simple_chat")
        base_system_prompt = agent_config.system_prompt
        logfire.info(
            'agent.system_prompt.loaded',
            source='agent_config',
            length=len(base_system_prompt)
        )
    
    # Construct prompt with critical rules at the top
    system_prompt = critical_rules + base_system_prompt
    
    # Initialize variables for prompt breakdown tracking
    directory_docs = ""
    directory_result = None  # Will hold DirectoryDocsResult if directory tools enabled
    
    # Auto-generate directory tool documentation if enabled
    directory_config = (instance_config or {}).get("tools", {}).get("directory", {})
    if directory_config.get("enabled", False) and account_id is not None:
        logfire.info('agent.directory.docs.generating')
        
        from ..database import get_database_service
        from .tools.prompt_generator import generate_directory_tool_docs
        
        db_service = get_database_service()
        async with db_service.get_session() as db_session:
            directory_result = await generate_directory_tool_docs(
                agent_config=instance_config or {},
                account_id=account_id,
                db_session=db_session
            )
            
            # Extract full_text from DirectoryDocsResult for prompt assembly
            directory_docs = directory_result.full_text if directory_result else ""
            
            if directory_docs:
                system_prompt = system_prompt + "\n\n" + directory_docs
                logfire.info(
                    'agent.system_prompt.enhanced',
                    account_id=str(account_id),
                    original_length=len(system_prompt) - len(directory_docs) - 2,
                    directory_docs_length=len(directory_docs),
                    final_length=len(system_prompt)
                )
                # Log the actual enhanced prompt for debugging
                logfire.debug(
                    'agent.system_prompt.final',
                    prompt_preview=system_prompt[:200],
                    total_length=len(system_prompt)
                )
            else:
                logfire.warn('agent.directory.docs.empty')
    elif directory_config.get("enabled", False) and account_id is None:
        logfire.warn(
            'agent.directory.docs.skipped',
            reason='no_account_id'
        )
    
    # Load remaining prompt modules (Phase 4A) - skip tool_selection_hints (already loaded at top)
    from .tools.prompt_modules import load_modules_for_agent, load_prompt_module
    
    # Initialize module tracking for prompt breakdown
    other_modules = []
    
    # Load other modules (excluding tool_selection_hints which is already at the top)
    prompting_config = (instance_config or {}).get('prompting', {}).get('modules', {})
    if prompting_config.get('enabled', False):
        selected_modules = prompting_config.get('selected', [])
        other_modules = [m for m in selected_modules if m != 'tool_selection_hints']
        
        if other_modules:
            other_module_contents = []
            for module_name in other_modules:
                module_content = load_prompt_module(module_name, account_slug)
                if module_content:
                    other_module_contents.append(module_content)
            
            if other_module_contents:
                combined = "\n\n---\n\n".join(other_module_contents)
                system_prompt = system_prompt + "\n\n" + combined
                logfire.info(
                    'agent.prompt_modules.loaded',
                    module_count=len(other_modules),
                    modules=other_modules,
                    content_length=len(combined),
                    final_prompt_length=len(system_prompt),
                    note='tool_selection_hints loaded at top'
                )
    
    # Capture prompt breakdown for admin debugging
    prompt_breakdown = PromptBreakdownService.capture_breakdown(
        base_prompt=base_system_prompt,
        critical_rules=critical_rules if critical_rules else None,
        directory_result=directory_result if directory_config.get("enabled", False) and account_id is not None else None,
        modules={name: load_prompt_module(name, account_slug) 
                 for name in other_modules} if prompting_config.get('enabled') and other_modules else None,
        account_slug=account_slug,
        agent_instance_slug=instance_config.get('slug') if instance_config else None
    )
    
    # Use centralized model settings cascade with comprehensive monitoring
    # BUT: if instance_config was provided, use that instead of loading global config
    if instance_config is not None:
        # Multi-tenant mode: use the instance-specific config that was already extracted
        model_settings = llm_config
        model_name = llm_config.get("model", "anthropic/claude-3.5-sonnet")
        logfire.info(
            'agent.model_config.loaded',
            source='instance_config',
            selected_model=model_name
        )
    else:
        # Single-tenant mode: use the centralized cascade
        from .config_loader import get_agent_model_settings
        model_settings = await get_agent_model_settings("simple_chat")
        model_name = model_settings["model"]
        logfire.info(
            'agent.model_config.loaded',
            source='global_config',
            selected_model=model_name
        )
    
    # Use OpenRouterModel with cost-tracking provider
    provider = create_openrouter_provider_with_cost_tracking(api_key)
    model = OpenRouterModel(
        model_name,  # Now properly uses agent-first cascade
        provider=provider
    )
    
    logfire.info(
        'agent.openrouter.provider_created',
        model_name=model_name,
        provider_type="OpenRouterProvider_CustomClient", 
        api_key_masked=f"{api_key[:10]}..." if api_key else "none",
        cost_tracking="enabled_via_custom_asyncopenai_client",
        usage_tracking="always_included"
    )
    
    # Build tools list based on agent configuration
    tools_list = []
    tools_config = (instance_config or {}).get("tools", {})
    
    # Add directory tools if enabled
    if tools_config.get("directory", {}).get("enabled", False):
        tools_list.extend([get_available_directories, search_directory])
    
    # Add vector search tool if enabled
    if tools_config.get("vector_search", {}).get("enabled", False):
        tools_list.append(vector_search)
    
    logfire.info(
        'agent.creation',
        agent_name=instance_config.get('instance_name', 'unknown') if instance_config else 'unknown',
        tools_count=len(tools_list),
        tool_names=[t.__name__ for t in tools_list],
        mode='normal'
    )
    
    # Create agent with OpenRouterProvider (official pattern)
    # Pass tools directly - NOT toolsets
    agent = Agent(
        model,
        deps_type=SessionDependencies,
        system_prompt=system_prompt,
        tools=tools_list  # Direct tool functions, not toolsets
    )
    
    return agent, prompt_breakdown, system_prompt

async def get_chat_agent(
    instance_config: Optional[dict] = None,
    account_id: Optional[UUID] = None
) -> tuple[Agent, dict, str]:  # Return agent, prompt_breakdown, and system_prompt
    """
    Create a fresh chat agent instance.
    
    Note: Global caching disabled for production reliability.
    Configuration changes take effect immediately after server restart
    without requiring session cookie clearing or cache invalidation.
    
    Args:
        instance_config: Optional instance-specific configuration for multi-tenant support
        account_id: Optional account ID for multi-tenant directory documentation generation
    """
    # Always create fresh agent to pick up latest configuration
    # This ensures config changes work reliably in production
    agent, prompt_breakdown, system_prompt = await create_simple_chat_agent(
        instance_config=instance_config,
        account_id=account_id
    )
    return agent, prompt_breakdown, system_prompt

async def simple_chat(
    message: str, 
    session_id: str,  # Fixed: simplified interface - create SessionDependencies internally
    agent_instance_id: Optional[int] = None,  # Multi-tenant: agent instance ID for message attribution
    account_id: Optional[UUID] = None,  # Multi-tenant: account ID for data isolation
    message_history: Optional[List[ModelMessage]] = None,  # Fixed: proper type annotation
    instance_config: Optional[dict] = None  # Multi-tenant: instance-specific configuration
) -> dict:
    """
    Simple chat function using Pydantic AI agent with YAML configuration.
    
    Automatically loads conversation history from database if not provided,
    enabling multi-turn conversations with context continuity.
    
    Args:
        message: User message to process
        session_id: Session ID for conversation context
        agent_instance_id: Agent instance ID for multi-tenant message attribution
        message_history: Optional pre-loaded message history
        instance_config: Optional instance-specific config for multi-tenant support
    
    Returns:
        dict with response, messages, new_messages, and usage data
    """
    # Get history_limit from agent-first configuration cascade
    from .config_loader import get_agent_history_limit
    default_history_limit = await get_agent_history_limit("simple_chat")
    
    # Create session dependencies with agent config for tools
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,  # Optional for simple chat
        history_limit=default_history_limit
    )
    # Add agent-specific fields for tool access
    session_deps.agent_config = instance_config
    session_deps.agent_instance_id = agent_instance_id
    
    # CRITICAL: Ensure account_id is a Python primitive (not SQLAlchemy expression)
    # This prevents Logfire serialization errors when Pydantic AI instruments tool calls
    if account_id is not None:
        # Convert to Python UUID (simplified)
        session_deps.account_id = UUID(str(account_id)) if account_id and not isinstance(account_id, UUID) else account_id
    else:
        session_deps.account_id = None
    
    # Load model settings using centralized cascade (Fixed: comprehensive cascade)
    from .config_loader import get_agent_model_settings
    model_settings = await get_agent_model_settings("simple_chat")
    
    # Load conversation history if not provided (TASK 0017-003)
    if message_history is None:
        # Use centralized cascade function for consistent behavior
        message_history = await load_conversation_history(
            session_id=session_id,
            max_messages=None  # load_conversation_history will use get_agent_history_limit internally
        )
    
    # Get the agent (Fixed: await async function)
    # Pass instance_config and account_id for multi-tenant support and directory docs generation
    agent, prompt_breakdown, system_prompt = await get_chat_agent(instance_config=instance_config, account_id=account_id)
    
    # Extract requested model for debugging
    config_to_use = instance_config if instance_config is not None else load_config()
    requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
    
    # Get database session for tools (directory_search, etc.) - wrap execution in context manager
    from ..database import get_database_service
    db_service = get_database_service()
    
    async with db_service.get_session() as db_session:
        # BUG-0023-001: db_session no longer assigned to dependencies
        # Tools create their own sessions via get_db_session() to eliminate concurrent operation errors
        # This db_session is still used for non-tool operations (session loading, directory docs generation)
        
        # Pure Pydantic AI agent execution
        start_time = datetime.now(UTC)
        
        try:
            # Execute agent with Pydantic AI
            result = await agent.run(message, deps=session_deps, message_history=message_history)
            end_time = datetime.now(UTC)
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Extract response and usage data
            try:
                response_text = result.output
            except Exception as output_error:
                logfire.error(
                    'failed_to_extract_output',
                    error_type=type(output_error).__name__,
                    error_message=str(output_error),
                    result_type=type(result).__name__,
                    has_output=hasattr(result, 'output'),
                    model=requested_model
                )
                raise  # Re-raise to be caught by outer exception handler
            
            usage_data = result.usage() if hasattr(result, 'usage') else None
            
            if usage_data:
                prompt_tokens = getattr(usage_data, 'input_tokens', 0)
                completion_tokens = getattr(usage_data, 'output_tokens', 0)
                total_tokens = getattr(usage_data, 'total_tokens', prompt_tokens + completion_tokens)
                
                # Extract costs from OpenRouter provider_details
                prompt_cost = 0.0
                completion_cost = 0.0
                real_cost = 0.0
                
                # Get the latest message response with OpenRouter metadata
                new_messages = result.new_messages()
                if new_messages:
                    latest_message = new_messages[-1]  # Last message (assistant response)
                    if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
                        # DEBUG: Log provider_details for cost tracking verification (info level)
                        logfire.info(
                            'openrouter_provider_details_debug',
                            provider_details=latest_message.provider_details,
                            requested_model=requested_model
                        )
                    
                        # Extract total cost
                        vendor_cost = latest_message.provider_details.get('cost')
                        if vendor_cost is not None:
                            real_cost = float(vendor_cost)
                    
                        # Extract detailed costs from cost_details
                        cost_details = latest_message.provider_details.get('cost_details', {})
                        if cost_details:
                            prompt_cost = float(cost_details.get('upstream_inference_prompt_cost', 0.0))
                            completion_cost = float(cost_details.get('upstream_inference_completions_cost', 0.0))
                            logfire.info(
                                'openrouter_cost_extracted',
                                total_cost=real_cost,
                                prompt_cost=prompt_cost,
                                completion_cost=completion_cost,
                                model=requested_model
                            )
            else:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                prompt_cost = 0.0
                completion_cost = 0.0
                real_cost = 0.0
            
            # Log OpenRouterModel results
            logfire.info(
                'agent.openrouter.execution',
                session_id=session_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                real_cost=real_cost,
                method="openrouter_model_vendor_details",
                cost_tracking="enabled",
                cost_found=real_cost > 0,
                latency_ms=latency_ms
            )
        
            # Store cost data using LLMRequestTracker
            llm_request_id = None  # Initialize to None for cases where tracking is skipped
            if prompt_tokens > 0 or completion_tokens > 0:
                from decimal import Decimal
                tracker = LLMRequestTracker()
            
                # Get tracking model from instance_config (multi-tenant) or cascade (single-tenant)
                if instance_config is not None:
                    # Multi-tenant mode: use the instance-specific config
                    tracking_model = instance_config.get("model_settings", {}).get("model", requested_model)
                    logfire.debug(
                        'agent.cost_tracking.model_selected',
                        source='instance_config',
                        tracking_model=tracking_model
                    )
                else:
                    # Single-tenant mode: use the centralized cascade
                    tracking_model = model_settings["model"]
                    logfire.debug(
                        'agent.cost_tracking.model_selected',
                        source='cascade',
                        tracking_model=tracking_model
                    )
            
                # Build full request body with actual messages sent to LLM (using helper)
                request_messages = build_request_messages(message_history or [], message)
            
                # Build full response body with actual LLM response (using helper)
                response_body_full = build_response_body(
                    response_text=response_text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    requested_model=requested_model,
                    result=result
                )
            
                # Load session to extract denormalized fields for cost attribution (using helper)
                account_id, account_slug = await extract_session_account_info(UUID(session_id))
                
                # Validate session exists (account_id/account_slug will be None if session not found)
                if account_id is None and account_slug is None:
                    from ..database import get_database_service
                    from ..models.session import Session
                    db_service = get_database_service()
                    async with db_service.get_session() as db_session:
                        session_record = await db_session.get(Session, UUID(session_id))
                        if not session_record:
                            logfire.error(
                                'agent.session.not_found',
                                session_id=session_id
                            )
                            raise ValueError(f"Session not found: {session_id}")
                    
                    # Validate required fields are present (may be None for legacy sessions)
                    if account_id is None or account_slug is None:
                        logfire.warn(
                            'agent.session.missing_account_fields',
                            session_id=session_id,
                            has_account_id=account_id is not None,
                            has_account_slug=account_slug is not None
                        )
                        # Don't fail - allow None values to be passed (tracker handles nullable fields)
                
                # Get agent config values outside session context (don't need DB)
                agent_instance_slug = instance_config.get("instance_name", "unknown") if instance_config else "simple_chat"
                agent_type = instance_config.get("agent_type", "simple_chat") if instance_config else "simple_chat"
            
                # Diagnostic logging: Log values BEFORE calling track_llm_request to identify SQLAlchemy expressions
                # Safe logging: Wrap ALL operations in try/except to avoid triggering SQLAlchemy expression evaluation
                # Debug logging for cost tracking (simplified - removed defensive wrappers)
                logfire.debug(
                    'agent.cost_tracking.before_track_call',
                    session_id=session_id,
                    agent_instance_id=str(agent_instance_id) if agent_instance_id else None,
                    account_id=str(account_id) if account_id else None,
                    account_slug=account_slug,
                    agent_instance_slug=agent_instance_slug,
                    agent_type=agent_type
                )
            
                llm_request_id = await tracker.track_llm_request(
                    session_id=UUID(session_id),
                    provider="openrouter",
                    model=tracking_model,
                    request_body={
                        "messages": request_messages,
                        "model": requested_model,
                        "temperature": model_settings.get("temperature"),
                        "max_tokens": model_settings.get("max_tokens")
                    },
                    response_body=response_body_full,
                    tokens={"prompt": prompt_tokens, "completion": completion_tokens, "total": total_tokens},
                    cost_data={
                        "prompt_cost": prompt_cost,
                        "completion_cost": completion_cost,
                        "total_cost": Decimal(str(real_cost))
                    },
                    latency_ms=latency_ms,
                    agent_instance_id=agent_instance_id,  # Multi-tenant: pass agent instance ID
                    # Denormalized fields for fast billing queries (no JOINs)
                    account_id=account_id,
                    account_slug=account_slug,
                    agent_instance_slug=agent_instance_slug,
                    agent_type=agent_type,
                    completion_status="complete",
                    meta={"prompt_breakdown": prompt_breakdown},  # Admin debugging
                    assembled_prompt=system_prompt  # Complete assembled prompt as sent to LLM
                )
        
            # Save messages to database for multi-tenant message attribution
            if agent_instance_id is not None:
                from ..services.message_service import MessageService
                message_service = MessageService()
            
                try:
                    # Save user message (link to LLM request for cost attribution)
                    await message_service.save_message(
                        session_id=UUID(session_id),
                        agent_instance_id=agent_instance_id,
                        llm_request_id=llm_request_id,
                        role="human",
                        content=message
                    )
                
                    # Extract tool calls from result for admin debugging
                    tool_calls_meta = []
                    if result.all_messages():
                        from pydantic_ai.messages import ToolCallPart, ToolReturnPart
                        for msg in result.all_messages():
                            if hasattr(msg, 'parts'):
                                for part in msg.parts:
                                    if isinstance(part, ToolCallPart):
                                        tool_calls_meta.append({
                                            "tool_name": part.tool_name,
                                            "args": part.args
                                        })
                
                    # Save assistant response (link to same LLM request) with tool calls
                    await message_service.save_message(
                        session_id=UUID(session_id),
                        agent_instance_id=agent_instance_id,
                        llm_request_id=llm_request_id,
                        role="assistant",
                        content=response_text,
                        metadata={"tool_calls": tool_calls_meta} if tool_calls_meta else None
                    )
                
                    logfire.info(
                        'agent.messages.saved',
                        session_id=session_id,
                        agent_instance_id=agent_instance_id,
                        user_message_length=len(message),
                        assistant_message_length=len(response_text)
                    )
                except Exception as msg_error:
                    logfire.exception(
                        'agent.messages.save_failed',
                        session_id=session_id,
                        agent_instance_id=agent_instance_id
                    )
                    # Don't fail the request if message saving fails
                
        except Exception as e:
            # Log tracking errors but don't break the response
            # Log cost tracking failure (simplified - removed defensive wrappers)
            import traceback
            logfire.error(
                'cost_tracking_failed',
                error_type=type(e).__name__,
                error_message=str(e),
                traceback_details=traceback.format_exc(),
                requested_model=str(requested_model) if 'requested_model' in locals() else 'unknown',
                result_type=type(result).__name__ if 'result' in locals() else 'not_available',
                has_usage=hasattr(result, 'usage') if 'result' in locals() else False,
                session_id=str(session_id) if session_id else None,
                agent_instance_id=str(agent_instance_id) if agent_instance_id else None
            )
            llm_request_id = None
            prompt_cost = 0.0
            completion_cost = 0.0
            real_cost = 0.0
            response_text = "Error processing request"
            prompt_tokens = 0.0
            completion_tokens = 0
            total_tokens = 0
            latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
    
        # Create usage data object for compatibility
        class UsageData:
            def __init__(self, prompt_tokens, completion_tokens, total_tokens):
                self.input_tokens = prompt_tokens
                self.output_tokens = completion_tokens
                self.total_tokens = total_tokens
                self.requests = 1
                self.details = {}
    
        usage_obj = UsageData(prompt_tokens, completion_tokens, total_tokens)
    
        # Get session stats for continuity monitoring
        from ..services.agent_session import get_session_stats
        session_stats = await get_session_stats(session_id)
    
        return {
            'response': response_text,  # Response from Pydantic AI
            'usage': usage_obj,  # Compatible usage object
            'llm_request_id': str(llm_request_id) if llm_request_id else None,
            # Cost tracking data (via OpenRouterModel)
            'cost_tracking': {
                'real_cost': real_cost,
                'method': 'openrouter_model_vendor_details',
                'provider': 'OpenRouterProvider',
                'cost_found': real_cost > 0,
                'status': 'enabled'
            },
            # Session continuity monitoring
            'session_continuity': session_stats
        }


async def simple_chat_stream(
    message: str,
    session_id: str,
    agent_instance_id: UUID,
    account_id: UUID,  # Multi-tenant: account ID for data isolation
    message_history: Optional[List[ModelMessage]] = None,
    instance_config: Optional[dict] = None
):
    """
    Streaming version of simple_chat using Pydantic AI agent.run_stream().
    
    Yields SSE-formatted events with incremental text chunks.
    
    Args:
        message: User message to process
        session_id: Session ID for conversation context
        agent_instance_id: Agent instance ID for message attribution
        message_history: Optional pre-loaded message history
        instance_config: Optional instance-specific config for multi-tenant support
        
    Yields:
        dict: SSE events with format:
            - {"event": "message", "data": chunk} - Text chunks
            - {"event": "done", "data": ""} - Completion
            - {"event": "error", "data": json.dumps({"message": "..."})} - Errors
    """
    import json
    
    # Get history_limit from agent-first configuration cascade
    from .config_loader import get_agent_history_limit
    default_history_limit = await get_agent_history_limit("simple_chat")
    
    # Create session dependencies with agent config for tools
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,
        history_limit=default_history_limit
    )
    # Add agent-specific fields for tool access
    session_deps.agent_config = instance_config
    session_deps.agent_instance_id = agent_instance_id
    session_deps.account_id = account_id  # Multi-tenant: for directory tool data isolation
    
    # Load conversation history if not provided
    if message_history is None:
        message_history = await load_conversation_history(
            session_id=session_id,
            max_messages=None
        )
    
    # Get the agent (pass instance_config and account_id for multi-tenant support and directory docs generation)
    agent, prompt_breakdown, system_prompt = await get_chat_agent(instance_config=instance_config, account_id=account_id)
    
    # Extract requested model for logging
    config_to_use = instance_config if instance_config is not None else load_config()
    requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
    
    chunks = []
    start_time = datetime.now(UTC)
    
    try:
        # Execute agent with streaming
        logfire.info(
            'agent.streaming.start',
            session_id=session_id,
            model=requested_model,
            message_length=len(message)
        )
        
        async with agent.run_stream(message, deps=session_deps, message_history=message_history) as result:
            logfire.info(
                'agent.streaming.context_entered',
                session_id=session_id,
                result_type=type(result).__name__
            )
            
            # Stream with delta=True for incremental chunks only
            chunk_count = 0
            async for chunk in result.stream_text(delta=True):
                chunk_count += 1
                logfire.debug(
                    'agent.streaming.chunk_received',
                    session_id=session_id,
                    chunk_number=chunk_count,
                    chunk_length=len(chunk) if chunk else 0,
                    chunk_preview=chunk[:50] if chunk else None,
                    chunk_is_empty=not bool(chunk)
                )
                if chunk:  # Only append and yield non-empty chunks
                    chunks.append(chunk)
                    yield {"event": "message", "data": chunk}
            
            end_time = datetime.now(UTC)
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logfire.info(
                'agent.streaming.loop_complete',
                session_id=session_id,
                total_chunks=chunk_count,
                chunks_sent=len(chunks),
                model=requested_model
            )
            
            # Get full response text
            response_text = "".join(chunks).strip()
            
            # Handle empty response - LLM returned tokens but no actual text content
            if not response_text:
                logfire.error(
                    'agent.streaming.empty_response',
                    session_id=session_id,
                    model=requested_model,
                    total_chunks_iterated=chunk_count,
                    chunks_with_content=len(chunks),
                    message="LLM completed but returned no text content"
                )
                # Return error to client instead of trying to save empty message
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": "Model returned no content",
                        "retry": True,
                        "chunks_received": chunk_count
                    })
                }
                return  # Exit early, don't try to save messages
            
            # Track cost after stream completes
            usage_data = result.usage()
            
            if usage_data:
                prompt_tokens = getattr(usage_data, 'input_tokens', 0)
                completion_tokens = getattr(usage_data, 'output_tokens', 0)
                total_tokens = getattr(usage_data, 'total_tokens', prompt_tokens + completion_tokens)
                
                # Calculate costs using genai-prices
                # Pydantic AI doesn't populate provider_details for streaming responses,
                # so we use genai-prices to calculate costs from token usage
                # See: memorybank/lessons-learned/pydantic-ai-streaming-cost-tracking.md
                prompt_cost = 0.0
                completion_cost = 0.0
                total_cost = 0.0
                
                try:
                    from genai_prices import calc_price
                    
                    # Calculate price using the actual model from agent config
                    # Model name extracted from instance_config or global config (line 549)
                    # Strip provider prefix (e.g., "google/gemini-2.5-flash" → "gemini-2.5-flash")
                    # genai-prices expects models without provider prefix
                    model_for_pricing = requested_model.split('/')[-1] if '/' in requested_model else requested_model
                    
                    price = calc_price(
                        usage=usage_data,
                        model_ref=model_for_pricing,
                        provider_id="openrouter"
                    )
                    
                    # Extract individual costs
                    prompt_cost = float(price.input_price)
                    completion_cost = float(price.output_price)
                    total_cost = float(price.total_price)
                    
                    logfire.info(
                        'agent.streaming.cost_calculated',
                        session_id=session_id,
                        model=requested_model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        prompt_cost=prompt_cost,
                        completion_cost=completion_cost,
                        total_cost=total_cost,
                        method="genai-prices"
                    )
                    
                except LookupError as e:
                    # Model not in genai-prices database - use fallback pricing from config
                    import yaml
                    import os
                    from pathlib import Path
                    
                    # Load fallback pricing from config file
                    # __file__ = backend/app/agents/simple_chat.py
                    # .parent = backend/app/agents/
                    # .parent = backend/app/
                    # .parent = backend/
                    config_dir = Path(__file__).parent.parent.parent / "config"
                    fallback_pricing_path = config_dir / "fallback_pricing.yaml"
                    
                    fallback_pricing_models = {}
                    if fallback_pricing_path.exists():
                        with open(fallback_pricing_path, 'r') as f:
                            fallback_config = yaml.safe_load(f)
                            fallback_pricing_models = fallback_config.get('models', {})
                    
                    if requested_model in fallback_pricing_models:
                        pricing = fallback_pricing_models[requested_model]
                        prompt_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
                        completion_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
                        total_cost = prompt_cost + completion_cost
                        
                        logfire.info(
                            'agent.streaming.cost_calculated',
                            session_id=session_id,
                            model=requested_model,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            prompt_cost=prompt_cost,
                            completion_cost=completion_cost,
                            total_cost=total_cost,
                            method="fallback_pricing",
                            source=pricing.get("source", "unknown"),
                            config_file=str(fallback_pricing_path)
                        )
                    else:
                        logfire.warn(
                            'agent.streaming.cost_calculation_failed',
                            session_id=session_id,
                            model=requested_model,
                            error=f"Model not in genai-prices or fallback pricing: {e}",
                            error_type="LookupError",
                            fallback="zero_cost",
                            suggestion=f"Add model to {fallback_pricing_path}"
                        )
                        
                except Exception as e:
                    logfire.warn(
                        'agent.streaming.cost_calculation_failed',
                        session_id=session_id,
                        model=requested_model,
                        error=str(e),
                        error_type=type(e).__name__,
                        fallback="zero_cost"
                    )
                
                # Prepare cost_data dict for LLMRequestTracker
                cost_data = {
                    "prompt_cost": prompt_cost,
                    "completion_cost": completion_cost,
                    "total_cost": total_cost
                }
            else:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                prompt_cost = 0.0
                completion_cost = 0.0
                real_cost = 0.0
                cost_data = {
                    "prompt_cost": 0.0,
                    "completion_cost": 0.0,
                    "total_cost": 0.0
                }
            
            # Log streaming execution
            logfire.info(
                'agent.openrouter.streaming',
                session_id=session_id,
                chunks_sent=len(chunks),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                real_cost=cost_data["total_cost"],
                latency_ms=latency_ms,
                completion_status="complete"
            )
            
            # Store cost data using LLMRequestTracker
            llm_request_id = None
            if prompt_tokens > 0 or completion_tokens > 0:
                from decimal import Decimal
                
                tracker = LLMRequestTracker()
                
                # Get tracking model from instance_config (multi-tenant) or cascade (single-tenant)
                if instance_config is not None:
                    # Multi-tenant mode: use the instance-specific config
                    model_settings = instance_config.get("model_settings", {})
                    tracking_model = model_settings.get("model", requested_model)
                    logfire.info(
                        'agent.streaming.model_config_loaded',
                        source="instance_config",
                        tracking_model=tracking_model,
                        temperature=model_settings.get("temperature"),
                        max_tokens=model_settings.get("max_tokens"),
                        session_id=session_id
                    )
                else:
                    # Single-tenant mode: use the centralized cascade
                    from .config_loader import get_agent_model_settings
                    model_settings = await get_agent_model_settings("simple_chat")
                    tracking_model = model_settings["model"]
                    logfire.info(
                        'agent.streaming.model_config_loaded',
                        source="cascade",
                        tracking_model=tracking_model,
                        temperature=model_settings.get("temperature"),
                        max_tokens=model_settings.get("max_tokens"),
                        session_id=session_id
                    )
                
                # Build full request body with actual messages sent to LLM (using helper)
                request_messages = build_request_messages(message_history or [], message)
                
                # Build full response body with actual LLM response (using helper)
                response_body_full = build_response_body(
                    response_text=response_text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    requested_model=requested_model,
                    result=result,
                    streaming_chunks=len(chunks)
                )
                
                # Load session to extract denormalized fields for cost attribution (using helper)
                account_id, account_slug = await extract_session_account_info(UUID(session_id))
                
                # Validate session exists (account_id/account_slug will be None if session not found)
                if account_id is None and account_slug is None:
                    from ..database import get_database_service
                    from ..models.session import Session
                    db_service = get_database_service()
                    async with db_service.get_session() as db_session:
                        session_record = await db_session.get(Session, UUID(session_id))
                        if not session_record:
                            logfire.error(
                                'agent.streaming.session_not_found',
                                session_id=session_id
                            )
                            raise ValueError(f"Session not found: {session_id}")
                
                agent_instance_slug = instance_config.get("instance_name", "unknown") if instance_config else "simple_chat"
                agent_type = instance_config.get("agent_type", "simple_chat") if instance_config else "simple_chat"
                
                # Log tracking attempt for debugging
                # All values are now Python primitives (no SQLAlchemy expressions)
                logfire.debug(
                    'agent.streaming.llm_tracking_start',
                    session_id=session_id,
                    tracking_model=tracking_model,
                    requested_model=requested_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost=cost_data.get("total_cost", 0.0),
                    has_model_settings=model_settings is not None,
                    model_settings_keys=list(model_settings.keys()) if model_settings else [],
                    account_slug=account_slug,
                    agent_instance_slug=agent_instance_slug,
                    agent_type=agent_type
                )
                
                llm_request_id = await tracker.track_llm_request(
                    session_id=UUID(session_id),
                    provider="openrouter",
                    model=tracking_model,
                    request_body={
                        "messages": request_messages,
                        "model": requested_model,
                        "temperature": model_settings.get("temperature"),
                        "max_tokens": model_settings.get("max_tokens"),
                        "stream": True
                    },
                    response_body=response_body_full,
                    tokens={
                        "prompt": prompt_tokens,
                        "completion": completion_tokens,
                        "total": total_tokens
                    },
                    cost_data=cost_data,
                    latency_ms=latency_ms,
                    agent_instance_id=agent_instance_id,
                    # Denormalized fields for fast billing queries (no JOINs)
                    account_id=account_id,
                    account_slug=account_slug,
                    agent_instance_slug=agent_instance_slug,
                    agent_type=agent_type,
                    completion_status="complete",
                    meta={"prompt_breakdown": prompt_breakdown},  # Admin debugging
                    assembled_prompt=system_prompt  # Complete assembled prompt as sent to LLM
                )
                
                logfire.info(
                    'agent.streaming.llm_tracked',
                    session_id=session_id,
                    llm_request_id=str(llm_request_id),
                    model=tracking_model,
                    total_cost=cost_data.get("total_cost", 0.0)
                )
            
            # Save messages to database
            logfire.info(
                'agent.streaming.messages_saving',
                session_id=session_id,
                agent_instance_id=str(agent_instance_id),
                user_message_length=len(message),
                assistant_message_length=len(response_text),
                completion_status="complete"
            )
            
            message_service = get_message_service()
            
            # Save user message (link to LLM request for cost attribution)
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                llm_request_id=llm_request_id,
                role="human",
                content=message
            )
            
            # Extract tool calls from result for admin debugging
            tool_calls_meta = []
            if result.all_messages():
                from pydantic_ai.messages import ToolCallPart, ToolReturnPart
                for msg in result.all_messages():
                    if hasattr(msg, 'parts'):
                        for part in msg.parts:
                            if isinstance(part, ToolCallPart):
                                tool_calls_meta.append({
                                    "tool_name": part.tool_name,
                                    "args": part.args
                                })
            
            # Save assistant response (link to same LLM request) with tool calls
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                llm_request_id=llm_request_id,
                role="assistant",
                content=response_text,
                metadata={"tool_calls": tool_calls_meta} if tool_calls_meta else None
            )
            
            logfire.info(
                'agent.streaming.messages_saved',
                session_id=session_id,
                completion_status="complete"
            )
            
            # Yield completion event
            yield {"event": "done", "data": ""}
            
    except Exception as e:
        import traceback
        logfire.exception(
            'agent.streaming.error',
            session_id=session_id,
            error_type=type(e).__name__,
            chunks_sent=len(chunks),
            has_instance_config=instance_config is not None
        )
        
        # Save partial response if any chunks were sent
        if chunks:
            logfire.info(
                'agent.streaming.partial_messages_saving',
                session_id=session_id,
                partial_response_length=len("".join(chunks)),
                chunks_sent=len(chunks),
                completion_status="partial"
            )
            message_service = get_message_service()
            partial_response = "".join(chunks)
            
            # Get llm_request_id if it was created before the error (might be None if error happened early)
            request_id = locals().get('llm_request_id', None)
            
            # Save user message (link to LLM request if available)
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                llm_request_id=request_id,
                role="human",
                content=message
            )
            
            # Save partial assistant response with metadata (link to same LLM request if available)
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                llm_request_id=request_id,
                role="assistant",
                content=partial_response,
                metadata={
                    "partial": True,
                    "error": str(e),
                    "completion_status": "partial",
                    "chunks_received": len(chunks)
                }
            )
            
            logfire.info(
                'agent.streaming.partial_messages_saved',
                session_id=session_id,
                completion_status="partial",
                error_type=type(e).__name__
            )
            
            # Note: Not tracking partial LLM requests since token counts are unavailable in error cases
        
        # Yield error event
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
