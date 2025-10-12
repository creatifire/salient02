# Project Management Archive

> **Created**: January 12, 2025  
> This archive contains superseded epic and task documentation from active development.

## Purpose

This folder preserves project management documents (epics, tasks, features) that have been:
- **Superseded by newer epics**: Replaced by consolidated or improved approaches
- **Completed and archived**: Finished work preserved for historical reference
- **Fundamentally changed**: Implementation approach evolved significantly

These documents provide valuable historical context for understanding project evolution and architectural decisions.

## Archive Contents

### Superseded Epics

**Epic 0017 - Simple Chat Agent (Original)**
- **File**: `0017-simple-chat-agent-old.md` (35KB, 734 lines)
- **Date Archived**: September 2025
- **Status**: Superseded by Epic 0022 (Multi-Tenant Architecture)
- **Reason**: Epic 0022 consolidated the multi-tenant architecture and simplified the implementation approach. The original Epic 0017 described a more complex, phase-based implementation that was streamlined in the actual development.
- **Key Changes**:
  - Original: Multi-phase agent factory, complex routing, registry system
  - New Approach: Explicit URL structure, hybrid DB + config files, no complex routing
  - Consolidation: Multi-tenant features integrated directly into Epic 0022
- **Value**: Shows the evolution from complex over-engineered approach to simple, explicit architecture

## Current Project Management Documentation

For active project management documentation, see:

- **Development Approach**: `/memorybank/project-management/0000-approach-milestone-01.md`
- **Master Epic List**: `/memorybank/project-management/0000-epics.md`
- **Active Epics**: `/memorybank/project-management/00XX-*.md` (all numbered epic files)
- **Multi-Tenant Architecture**: `/memorybank/project-management/0022-multi-tenant-architecture.md` (current implementation)

## Related Archives

**Architecture Documentation Archive**: `/memorybank/archive/`
- Contains archived architecture and design documents (not epics)
- See `/memorybank/archive/README.md` for architecture archive contents

## When to Archive Project Management Documents

Epic or task files should be moved to this archive when:

1. **Superseded**: A new epic replaces or consolidates the old approach
2. **Completed**: Epic finished and implementation stable (optional - some teams prefer to keep completed epics in main folder)
3. **Approach Changed**: Fundamental shift in implementation strategy makes old planning obsolete
4. **Historical Reference Only**: Document no longer guides active development but provides valuable context

## Archive Guidelines

- **Don't Update**: Archived documents are historical snapshots - don't modify them
- **Cross-Reference**: Link from current epics to archived ones when relevant (e.g., "See archived Epic 0017 for original approach")
- **Preserve Context**: Keep commit history and file metadata intact
- **Update This README**: Add entries when archiving new documents

## Retrieval

If you need to reference archived epics:
1. Check current epics first - they may reference or incorporate archived content
2. Review this README for quick overview and supersession notes
3. Read archived files with historical context in mind
4. Consider whether archived approach has relevant ideas for current challenges

