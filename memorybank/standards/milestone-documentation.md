# Milestone Documentation Standards

> Standards for creating clean, scannable milestone tracking documents

## Purpose

Milestone documents serve as high-level progress checklists that provide instant visibility into project status without implementation details. They complement epic documents by focusing purely on completion tracking.

## Structure Requirements

### 2-Level Hierarchy Only
```markdown
### **Priority N: Feature Name** [status emoji]
- [x] NNNN-NNN-NNN - Completed task description
- [ ] NNNN-NNN-NNN - Planned task description  
- [ ] NNNN-NNN-NNN - Another planned task
```

**Hierarchy Levels:**
- **Priority**: Major project phases (0-9)
- **Task**: Individual completable work items

**No Sub-Tasks**: Task breakdown belongs in epic documents, not milestones.

## Checkbox Notation

### Status Format
- `[x]` - Completed tasks
- `[ ]` - Planned/pending tasks

### Task Numbering
Use consistent hierarchical numbering: `EPIC-FEATURE-TASK`
- Example: `0017-003-005` = Epic 0017, Feature 003, Task 005

## Content Guidelines

### Include
- ✅ Executive summary (current state, approach)  
- ✅ Priority-level status with emoji indicators
- ✅ Task-level completion checkboxes
- ✅ Current progress summary at bottom
- ✅ Next action identification

### Exclude
- ❌ Time estimates ("~2 days", "0.5 day")
- ❌ Implementation details (code, architecture)
- ❌ Manual verification steps (covered in epics)
- ❌ Detailed acceptance criteria
- ❌ Risk mitigation (covered elsewhere)
- ❌ Success criteria (covered in epics)
- ❌ Boilerplate explanations

## Status Indicators

### Priority-Level Emojis
- ✅ **Completed** - All tasks finished
- 🔄 **In Progress** - Some tasks complete, some pending
- 📋 **Planned** - No tasks started yet

### Progress Format
```markdown
**Current Status**: Priority N in progress - X of Y tasks completed  
**Next**: NNNN-NNN-NNN (Task Name)
```

## Executive Summary Template

```markdown
## Executive Summary

**Current State**: ~X% project completion with foundational infrastructure complete:
- ✅ Epic NNNN (Name) - Brief description
- ✅ Feature NNNN-NNN (Name) - Brief description  
- ✅ Feature NNNN-NNN (Name) - Brief description

**Approach**: [Brief description of development strategy]
```

## Length Guidelines

### Target Metrics
- **Ideal Range**: 50-100 lines total
- **Maximum**: 150 lines (including executive summary)
- **Reduction Goal**: Eliminate 70-90% of verbose content from detailed planning

### Content Density
- **1 line per task** maximum
- **No multi-paragraph explanations**
- **Reference epic documents** for details

## Example Priority Section

**Good:**
```markdown
### **Priority 2: Simple Chat Agent Implementation** 🔄
- [x] 0017-003-001 - Direct Pydantic AI Agent Implementation
- [x] 0017-003-002 - Conversation History Integration  
- [x] 0017-003-003 - FastAPI Endpoint Integration
- [ ] 0017-003-004 - LLM Request Tracking & Cost Management
- [ ] 0017-003-005 - Agent Conversation Loading
```

**Bad:**
```markdown
### **Priority 2: Simple Chat Agent Implementation** 🔄
**Epic Reference**: [0017-simple-chat-agent.md](0017-simple-chat-agent.md)
**Goal**: Implement enhanced chat agent with vector search capabilities

**Implementation Strategy:**
- Direct Pydantic AI implementation following official documentation
- Full legacy feature parity with session handling and persistence
- Integrated vector search using existing Pinecone setup

**Manual Verification**: Agent responds correctly, sessions persist
```

## Quality Checklist

### Structure ✓
- [ ] 2-level hierarchy (Priority → Task)
- [ ] Consistent checkbox notation
- [ ] Hierarchical task numbering
- [ ] Clear emoji status indicators

### Content ✓  
- [ ] Executive summary present
- [ ] No time estimates
- [ ] No implementation details
- [ ] No manual verification steps
- [ ] Epic references for detailed planning

### Scannability ✓
- [ ] Tasks fit on single lines
- [ ] Clear completion status at glance
- [ ] Current progress summary at bottom
- [ ] Next action clearly identified

### Length ✓
- [ ] Under 100 lines total (ideal)
- [ ] Under 150 lines maximum
- [ ] 70%+ reduction from verbose planning

## Common Anti-Patterns

### Avoid These Mistakes
- **Epic Content Duplication**: Implementation details belong in epics
- **Estimates in Milestone**: Time planning belongs in epics
- **Multi-Level Nesting**: Keep flat task structure
- **Verbose Task Descriptions**: Single-line task names only
- **Missing Progress Summary**: Always include current status

### Red Flags
- Lines > 150: Too verbose
- Multi-paragraph task descriptions: Move to epics
- Missing checkboxes: Not functioning as checklist
- No current status: Can't track progress

## Integration with Epic Documents

### Clear Separation
- **Milestone**: What's done/planned (checklist)
- **Epic**: How to do it (implementation guide)

### Cross-References
- Milestone references epic documents for details
- Epic documents can reference milestone for status
- No content duplication between documents

### Maintenance
- Update milestone checkboxes as work completes
- Epic documents remain stable implementation guides
- Milestone provides real-time progress visibility

## File Naming

Use descriptive milestone names:
- `0000-approach-milestone-01.md` - Overall tactical approach
- `0001-baseline-milestone.md` - Infrastructure milestone
- `0002-agent-ecosystem-milestone.md` - Agent development phase

## Template

```markdown
# [Milestone Name] - Streamlined
> [Brief description of milestone scope]

## Executive Summary

**Current State**: ~X% project completion with foundational infrastructure complete:
- ✅ Epic NNNN (Name) - Brief description
- ✅ Feature NNNN-NNN (Name) - Brief description

**Approach**: [Brief development strategy]

## 🎯 DEVELOPMENT PRIORITIES

### **Priority 0: [Name]** ✅
- [x] NNNN-NNN-NNN - Task description
- [x] NNNN-NNN-NNN - Task description

### **Priority 1: [Name]** 🔄  
- [x] NNNN-NNN-NNN - Completed task
- [ ] NNNN-NNN-NNN - Pending task

### **Priority 2: [Name]** 📋
- [ ] NNNN-NNN-NNN - Planned task
- [ ] NNNN-NNN-NNN - Planned task

**Current Status**: Priority N in progress - X of Y tasks completed  
**Next**: NNNN-NNN-NNN (Task Name)
```

This template ensures milestones function as intended: clean, scannable checklists for tracking progress without implementation cruft.
