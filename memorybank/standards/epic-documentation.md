# Epic Documentation Standards

Document epics for implementation clarity and progress tracking. Based on proven patterns from Epic 0002 (Baseline Connectivity) and Epic 0017 (Simple Chat Agent).

## Structure Hierarchy

```
Epic NNNN - Title
├── NNNN-001 - FEATURE - Name
│   ├── NNNN-001-001 - TASK - Name
│   │   ├── NNNN-001-001-01 - CHUNK - Name
│   │   │   └── SUB-TASKS: Specific deliverables
│   │   │   └── STATUS: What was accomplished
```

## Required Sections

### Epic Header
```markdown
# Epic NNNN - Title (Technology/Approach)

Brief description of what you're building and why.

**Architecture**: High-level flow (A → B → C → D)
**Integration**: What existing systems connect to this
```

### Architecture Diagram (When Complex)
- Include Mermaid diagram for multi-component systems
- Show data flow, dependencies, external services
- Use consistent styling with color-coded component types

### Features (NNNN-001)
- Group related tasks under features
- Use `- [x]` for completed, `- [ ]` for planned
- Each feature should have clear business value

### Tasks (NNNN-001-001)
- Specific implementation units
- Should be completable in 1-3 development sessions
- Dependencies clearly noted

### Chunks (NNNN-001-001-01)
- Manually verifiable units of work
- Each chunk must have clear deliverable
- Include essential code snippets when needed

## Content Guidelines

### ✅ Include
- **SUB-TASKS**: Specific, actionable items
- **STATUS**: What was actually accomplished (not what was planned)
- **Code Snippets**: Essential implementation patterns only
- **Manual Verification**: How to test/verify the work
- **Dependencies**: What must be completed first

### ❌ Exclude  
- "Acceptance Criteria" sections
- "Manual Verification Results" sections
- Repetitive boilerplate text
- Verbose explanations that restate the title
- Time estimates
- Multiple descriptions of the same concept

## Code Snippet Guidelines

### When to Include Code
- New patterns being introduced
- Complex implementation details
- Integration points with existing systems
- Configuration examples
- Critical breakthrough solutions

### Code Format
```python
# Context: Where this code goes
def example_function():
    """Brief description of what this does."""
    # Key implementation details
    return result
```

## Status Reporting

### STATUS Format
```
STATUS: Completed — Brief description of what was accomplished
STATUS: Planned — Brief description of what will be done  
```

### Good STATUS Examples
```
STATUS: Completed — Agent responds with YAML configuration, async patterns implemented
STATUS: Completed — Endpoint accessible, session handling, message persistence implemented
STATUS: Planned — Load DB messages and convert to Pydantic AI format
```

### Bad STATUS Examples
```
STATUS: All acceptance criteria met ❌ (too vague)
STATUS: Task completed successfully ❌ (no substance)
STATUS: In progress, working on implementation ❌ (not a status)
```

## Epic Size Guidelines

### Simple Epics (like 0002)
- ~125 lines total
- Minimal architecture diagrams
- Focus on SUB-TASKS and STATUS lines
- Light on code snippets

### Complex Epics (like 0017) 
- ~470 lines maximum
- Include architecture diagram
- Essential code snippets for guidance
- Detailed implementation plans for future work

## Checklist for Epic Quality

### Structure
- [ ] Hierarchical numbering consistent
- [ ] Checkbox notation used throughout
- [ ] Clear feature/task/chunk breakdown
- [ ] Dependencies noted where relevant

### Content
- [ ] No repetitive boilerplate sections
- [ ] Each concept explained only once
- [ ] Essential code snippets included
- [ ] Manual verification steps clear

### Readability  
- [ ] Easy to scan for progress
- [ ] Implementation details findable
- [ ] Next steps obvious
- [ ] Technical depth appropriate for complexity

### Completion
- [ ] Definition of Done section
- [ ] All completed items marked with [x]
- [ ] STATUS lines describe actual accomplishments
- [ ] Future work clearly planned with code examples

## Examples from Proven Epics

### Minimal Task (from Epic 0002)
```markdown
- [x] 0002-001-001 - TASK - Serve Base Page
  - [x] 0002-001-001-01 - CHUNK - Route `GET /` renders minimal Jinja2 page
    - SUB-TASKS:
      - Include HTMX via CDN
      - Message textarea + Submit + Clear buttons
      - Append-only chat pane container
    - STATUS: Completed — Implemented `GET /` rendering `templates/index.html` with HTMX CDN, textarea, Send/Clear buttons, and append-only chat pane
```

### Complex Task with Code (from Epic 0017)
```markdown
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
```

## Definition of Done Template

```markdown
## Definition of Done
- Primary functionality working as specified
- Integration points with existing systems functional  
- Manual verification steps completed
- Essential error handling implemented
- [Additional criteria specific to epic]
```

Epic documentation should enable implementation, not impede it. Focus on clarity, actionability, and progress tracking over comprehensive coverage.
