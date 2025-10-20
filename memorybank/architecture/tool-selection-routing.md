# Agent Tool Selection & Routing
> **Last Updated**: October 20, 2025

## Overview

This document outlines strategies for tool selection and routing in multi-tool Pydantic AI agents. While simple agents (like `simple_chat`) can handle 2-3 tools via direct LLM decision-making, more complex agents may require explicit routing logic.

## Current Approach: LLM-Driven Selection (Simple Agents)

**Pattern**: Register all tools with Pydantic AI agent, let LLM choose based on tool descriptions and conversation context.

```python
agent = Agent(model, deps_type=SessionDependencies, system_prompt=prompt)

# Register multiple tools - LLM decides which to use
agent.tool(vector_search)      # "Search knowledge base for hospital services"
agent.tool(search_profiles)     # "Find doctors, nurses, or medical staff"
agent.tool(schedule_appointment) # "Book appointments with providers"
```

**Strengths**:
- Simple implementation
- Natural conversation flow
- LLM handles ambiguous queries intelligently
- No hardcoded routing rules

**Limitations**:
- Works best with 2-5 tools
- LLM may make incorrect tool selections
- Higher token costs (all tool descriptions in every request)
- No explicit tool prioritization

**Recommended For**: InfoBot agents (2-3 tools), customer service bots, FAQ assistants

---

## Future Approaches: Explicit Routing (Complex Agents)

### **Option A: Intent Classification Router**

Pre-classify user intent, route to specialized sub-agents.

```python
class IntentRouter:
    """Route queries to specialized agents based on intent."""
    
    async def route(self, query: str) -> Agent:
        # Fast classification (< 50ms)
        intent = await self.classifier.classify(query)
        
        if intent == "doctor_search":
            return doctor_finder_agent  # Has profile_search only
        elif intent == "service_info":
            return info_agent           # Has vector_search only
        elif intent == "appointment":
            return scheduling_agent     # Has calendar_search + booking tools
        else:
            return general_agent        # Has all tools (fallback)
```

**Use Case**: Enterprise customer service with distinct workflows (billing, support, sales)

---

### **Option B: Tool Metadata Filtering**

Filter available tools based on conversation state or user context.

```python
def get_available_tools(ctx: RunContext) -> List[Tool]:
    """Dynamically filter tools based on context."""
    tools = []
    
    # Always available
    tools.append(vector_search)
    
    # Only for authenticated users
    if ctx.deps.user_authenticated:
        tools.append(search_profiles)
        tools.append(book_appointment)
    
    # Only during business hours
    if is_business_hours():
        tools.append(transfer_to_agent)
    
    return tools
```

**Use Case**: Multi-tenant SaaS with role-based tool access

---

### **Option C: Hierarchical Tool Chains**

Tools call other tools in predefined sequences.

```python
@agent.tool
async def find_and_book_doctor(
    ctx: RunContext,
    specialty: str,
    language: str | None = None
) -> str:
    """Find doctor and offer booking (composite tool)."""
    
    # Step 1: Search profiles
    doctors = await search_profiles(ctx, specialty=specialty, language=language)
    
    if not doctors:
        return "No doctors found"
    
    # Step 2: Check availability (calls another tool)
    available = await check_availability(ctx, doctor_ids=[d.id for d in doctors])
    
    # Step 3: Return formatted results with booking links
    return format_booking_options(doctors, available)
```

**Use Case**: Complex workflows (insurance verification → doctor search → appointment booking)

---

### **Option D: Prompt-Based Tool Guidance**

Guide LLM tool selection via system prompt instructions.

```python
system_prompt = """
You have access to 3 tools:

1. **vector_search**: Use for hospital services, facilities, departments, general info
   Example: "What cardiology services do you offer?"

2. **search_profiles**: Use ONLY for finding specific doctors/nurses by name, specialty, or language
   Example: "Find me a Spanish-speaking cardiologist"

3. **schedule_appointment**: Use ONLY after finding a specific doctor
   Example: "Book appointment with Dr. Smith"

RULES:
- ALWAYS use vector_search first for general questions
- ONLY use search_profiles when user asks for specific providers
- NEVER use schedule_appointment without a confirmed doctor
"""
```

**Use Case**: Preventing common LLM tool selection mistakes

---

## Hybrid Recommendation (Scalable Pattern)

**For 2-5 tools**: Use LLM-driven selection + prompt guidance (Option D)
**For 6-10 tools**: Add tool metadata filtering (Option B)
**For 10+ tools or complex workflows**: Implement intent router (Option A) or hierarchical chains (Option C)

---

## Configuration Schema (Future)

```yaml
# agent_configs/{account}/{instance}/config.yaml
tools:
  selection_strategy: "llm_driven"  # llm_driven | intent_router | filtered | hierarchical
  
  vector_search:
    enabled: true
    priority: 1  # Lower = higher priority (hint to LLM)
    
  profile_search:
    enabled: true
    priority: 2
    requires_auth: false
    
  schedule_appointment:
    enabled: true
    priority: 3
    requires_auth: true
    depends_on: ["profile_search"]  # Must be called after profile_search
```

---

## Performance Considerations

| Strategy | Latency | Token Cost | Accuracy | Complexity |
|----------|---------|------------|----------|------------|
| LLM-driven | +200ms | High (all tool descriptions) | 85-95% | Low |
| Intent Router | +50ms | Low (single classification) | 90-98% | Medium |
| Metadata Filtering | +0ms | Medium (fewer tools) | Same as LLM | Low |
| Hierarchical Chains | Variable | Medium | 95-99% | High |

---

## Current Implementation Status

- ✅ **LLM-driven selection**: Production-ready (wyckoff_info_chat1: vector_search + profile_search)
- ⏸️ **Intent router**: Planned for sales agents (Epic 0008)
- ⏸️ **Metadata filtering**: Planned for enterprise multi-tenant (Epic 0022-002)
- ⏸️ **Hierarchical chains**: Deferred (complex workflows)

---

## Testing Tool Selection

```python
# Manual test for multi-tool agent
async def test_tool_selection():
    queries = [
        ("What cardiology services do you offer?", "vector_search"),
        ("Find me a Spanish-speaking cardiologist", "profile_search"),
        ("Who is Dr. Smith?", "profile_search"),
        ("Book appointment with Dr. Smith", "schedule_appointment"),
    ]
    
    for query, expected_tool in queries:
        response = await agent.run(query, deps=deps)
        actual_tool = extract_tool_from_response(response)
        assert actual_tool == expected_tool, f"Expected {expected_tool}, got {actual_tool}"
```

---

## References

- Pydantic AI Tool Docs: https://ai.pydantic.dev/tools/
- Epic 0023: Profile Search Tool (2-tool simple_chat example)
- Epic 0008: Sales Agent (future intent router candidate)

