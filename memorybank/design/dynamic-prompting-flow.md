<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Dynamic Prompting Function Call Flow (Phases 1-3)

Mermaid diagrams showing the function calling flow for Phases 1-3 of the dynamic prompting architecture.

---

## Phase 1: Pydantic AI Native Toolsets

Foundation for multi-tool support using Pydantic AI's native features.

```mermaid
flowchart TD
    Start([User Query]) --> Init[Initialize Agent]
    Init --> LoadConfig[Load Agent Config]
    LoadConfig --> CheckTools{Check Enabled Tools}
    
    CheckTools -->|Directory Enabled| WrapDir[Wrap search_directory in FunctionToolset]
    CheckTools -->|Vector Enabled| WrapVec[Wrap vector_search in FunctionToolset]
    CheckTools -->|Both Disabled| PromptOnly[Base Prompt Only]
    
    WrapDir --> Toolsets[Collect Toolsets List]
    WrapVec --> Toolsets
    PromptOnly --> CreateAgent
    
    Toolsets --> CreateAgent[Create Agent with model, toolsets, prompt]
    CreateAgent --> ProcessQuery[LLM Processes Query]
    
    ProcessQuery --> Decision{Tool Call Needed?}
    Decision -->|Yes| SelectTool[LLM Selects Tool]
    Decision -->|No| DirectResponse[Direct Response]
    
    SelectTool --> ExecTool[Execute Tool Function]
    ExecTool --> ProcessQuery
    
    DirectResponse --> End([Return Response])
```

**Key Components**:
- `toolsets.py`: Wraps existing `directory_tools.py` and `vector_tools.py`
- `simple_chat.py`: Conditional toolset loading based on config
- Pydantic AI handles tool orchestration natively

---

## Phase 2: Multi-Directory Prerequisites

Adds phone directory as second directory type, creating real multi-directory scenario.

```mermaid
flowchart TD
    Start([User Query: Find cardiologist]) --> Init[Load Agent Config]
    Init --> CheckLists{Check accessible_lists}
    
    CheckLists -->|Single: doctors| SingleDir[Load doctors schema]
    CheckLists -->|Multi: doctors, phone_directory| MultiDir[Load Multiple Schemas]
    
    SingleDir --> GenPrompt1[Generate Standard Directory Tool Docs]
    MultiDir --> GenPrompt2[Generate Directory Docs + Selection Guide]
    
    GenPrompt1 --> CreateAgent[Create Agent with Directory Toolset]
    GenPrompt2 --> CreateAgent
    
    CreateAgent --> LLMProcess[LLM Processes Query with Directory Docs]
    
    LLMProcess --> ToolCall[LLM Calls search_directory with list_name=doctors, query=cardiology]
    
    ToolCall --> ExecSearch[Execute Directory Search]
    ExecSearch --> Results[Return 3 Cardiologists]
    Results --> Response([Formatted Response with Doctor Info])
```

**Key Changes**:
- Agent config has `accessible_lists: ["doctors", "phone_directory"]`
- Two schemas loaded: `medical_professional.yaml` + `phone_directory.yaml`
- Tool execution unchanged (same `search_directory` function)

---

## Phase 3: Schema Standardization + Multi-Directory Selection

Domain-agnostic prompt generation with intelligent directory selection guide.

```mermaid
flowchart TD
    Start([User Query: ER number]) --> Init[Load Agent Config]
    Init --> LoadSchemas[Load All Accessible Directory Schemas]
    
    LoadSchemas --> CheckCount{Schema Count}
    CheckCount -->|Single| GenDocs1[Generate Standard Tool Documentation]
    CheckCount -->|Multiple| GenSelGuide[Generate Directory Selection Guide]
    
    GenSelGuide --> ExtractPurpose[Extract from Each Schema: directory_purpose, use_for, example_queries, not_for]
    
    ExtractPurpose --> BuildGuide[Build Selection Guide with doctors and phone_directory options]
    
    BuildGuide --> AddMultiGuide[Add Multi-Directory Query Guidance]
    AddMultiGuide --> GenToolDocs[Generate Tool Documentation]
    
    GenDocs1 --> GenToolDocs
    GenToolDocs --> ComposePrompt[Compose Full Prompt: Base + Selection Guide + Tool Docs]
    
    ComposePrompt --> CreateAgent[Create Agent with Directory Toolset]
    CreateAgent --> LLMReason[LLM Reasons: User asking for phone not doctor, use phone_directory]
    
    LLMReason --> ToolCall[LLM Calls search_directory with list_name=phone_directory, query=emergency]
    
    ToolCall --> ExecSearch[Execute Search on phone_directory]
    ExecSearch --> Results[Return Emergency Dept 718-963-7272]
    Results --> Response([Response: Emergency Department 718-963-7272])
```

**Key Features**:
- Schema-driven selection guide generation
- Domain-agnostic `prompt_generator.py` (reads from schemas)
- LLM uses `directory_purpose` to choose correct directory
- Same tool execution (no code changes to `search_directory`)

---

## Phase 3: Multi-Tool Query Example

Complex query requiring both directory and vector search.

```mermaid
flowchart TD
    Start([User Query: Find Spanish-speaking cardiologist and heart disease info]) --> Init[Load Config]
    
    Init --> LoadTools{Load Enabled Toolsets}
    LoadTools --> DirTool[Directory Toolset: doctors, phone_directory]
    LoadTools --> VecTool[Vector Search Toolset: hospital knowledge base]
    
    DirTool --> ComposePrompt[Compose Prompt: Base + Directory Guide + Vector Docs]
    VecTool --> ComposePrompt
    
    ComposePrompt --> CreateAgent[Create Agent with Multiple Toolsets]
    CreateAgent --> LLMAnalyze[LLM Analyzes: Need doctor search plus medical information]
    
    LLMAnalyze --> ToolCall1[Tool Call 1: search_directory with doctors, Cardiology, Spanish]
    
    ToolCall1 --> ExecDir[Execute Directory Search]
    ExecDir --> Results1[Return: Dr. Maria Garcia, Cardiologist, Spanish]
    
    Results1 --> ToolCall2[Tool Call 2: vector_search with heart disease query]
    
    ToolCall2 --> ExecVec[Execute Vector Search]
    ExecVec --> Results2[Return: Heart disease docs, prevention tips, warning signs]
    
    Results2 --> Synthesize[LLM Synthesizes: Doctor info plus medical information]
    
    Synthesize --> Response([Combined Response with doctor and heart disease info])
```

**Key Capabilities**:
- Multiple toolsets work together
- LLM decides which tools to call based on query
- Sequential tool calls (directory → vector)
- Response synthesis combines results

---

## Detailed Prompt Generation Flow (Phase 3)

How `prompt_generator.py` creates domain-agnostic prompts from schemas.

```mermaid
flowchart TD
    Start([generate_directory_tool_docs]) --> LoadConfig[Load Agent Config: accessible_lists]
    
    LoadConfig --> LoadSchemas[Load Each Schema: medical_professional.yaml, phone_directory.yaml]
    
    LoadSchemas --> CheckMulti{Multiple Directories?}
    
    CheckMulti -->|No| SkipGuide[Skip Selection Guide]
    CheckMulti -->|Yes| GenGuide[Generate Selection Guide]
    
    GenGuide --> ForEachSchema[For Each Schema]
    ForEachSchema --> ExtractFields[Extract Schema Fields: directory_purpose fields]
    
    ExtractFields --> FormatCard[Format Directory Card with description, use_for, examples]
    
    FormatCard --> NextSchema{More Schemas?}
    NextSchema -->|Yes| ForEachSchema
    NextSchema -->|No| AddGuidance[Add Multi-Directory Query Guidance]
    
    AddGuidance --> GenToolDocs[Generate Tool Documentation]
    SkipGuide --> GenToolDocs
    
    GenToolDocs --> ReadStrategy[Read search_strategy: synonym_mappings_heading, formal_terms, guidance]
    
    ReadStrategy --> FormatStrategy[Format Search Strategy with lay terms to formal terms mapping]
    
    FormatStrategy --> GenFieldDocs[Generate Field Documentation: required, optional, searchable]
    
    GenFieldDocs --> Return([Return Complete Directory Tool Docs])
```

**Key Design Principles**:
- All domain knowledge in schemas (not Python code)
- `directory_purpose` drives selection guide
- `formal_terms` standardized across all schemas
- `prompt_generator.py` is purely domain-agnostic

---

## Error Handling Flow (Phase 3)

Graceful degradation when tools fail.

```mermaid
flowchart TD
    Start([User Query]) --> InitAgent[Initialize Agent]
    InitAgent --> LoadTools[Load Toolsets]
    
    LoadTools --> TryDir{Try Load Directory Toolset}
    TryDir -->|Success| AddDir[Add to Toolsets]
    TryDir -->|Fail| LogDirError[Log to Logfire: Directory unavailable]
    
    LogDirError --> TryVec{Try Load Vector Toolset}
    AddDir --> TryVec
    
    TryVec -->|Success| AddVec[Add to Toolsets]
    TryVec -->|Fail| LogVecError[Log to Logfire: Vector search unavailable]
    
    AddVec --> CreateAgent[Create Agent: Base prompt + Available tools]
    LogVecError --> CreateAgent
    
    CreateAgent --> HasTools{Any Tools Available?}
    HasTools -->|Yes| NormalFlow[Normal Tool Selection Flow]
    HasTools -->|No| BaseOnly[Base Prompt Only + Fallback Guidance]
    
    NormalFlow --> ToolExec{Tool Execution}
    ToolExec -->|Success| ReturnResults[Return Tool Results]
    ToolExec -->|Fail| LogToolError[Log Error to Logfire]
    
    LogToolError --> GuideLLM[Add Guidance: Tool unavailable, suggest alternative]
    
    GuideLLM --> LLMResponse[LLM Generates Graceful Response]
    BaseOnly --> LLMResponse
    ReturnResults --> LLMResponse
    
    LLMResponse --> End([User Receives Seamless Response])
```

**Graceful Degradation**:
- Tool failures logged but don't crash agent
- LLM receives guidance on how to handle unavailable tools
- User experience remains seamless
- Partial failures handled (some tools work, others don't)

---

## Summary: Phases 1-3 Flow

```mermaid
flowchart LR
    subgraph Phase1[Phase 1: Foundation]
        P1A[Wrap Existing Tools in FunctionToolset]
        P1B[Multi-Toolset Support in simple_chat.py]
    end
    
    subgraph Phase2[Phase 2: Multi-Directory]
        P2A[Create phone_directory.yaml plus data seeding]
        P2B[Agent Config: accessible_lists array]
    end
    
    subgraph Phase3[Phase 3: Standardization]
        P3A[Add directory_purpose to schemas]
        P3B[Domain-agnostic prompt_generator.py]
        P3C[Multi-directory selection guide]
    end
    
    Phase1 --> Phase2
    Phase2 --> Phase3
    
    Phase3 --> Result[Result: LLM intelligently selects correct directory]
```

**Value Delivered**:
- **Phase 1**: Multi-tool infrastructure (testable immediately)
- **Phase 2**: Real multi-directory scenario (doctors + phone_directory)
- **Phase 3**: Schema-driven selection (unlimited directory types)

**Backward Compatibility**: All phases are incremental, existing agents work unchanged.

