# Industry Site Generator

## Overview

LLM-powered workflow that generates industry-specific demo sites for the Salient platform through automated research and content generation. Creates complete Astro-based websites with product catalogs, directory data, and chatbot integration.

## Documentation

- **[Site Generation Design](site-gen-design.md)** - Complete workflow design with 12 sequential scripts, data flow, validation checkpoints, and configuration templates
- **[Code Organization](site-gen-code-org.md)** - Detailed code architecture, module structure, class interfaces, and implementation examples
- **[Implementation Plan](site-gen-plan.md)** - Feature-by-feature implementation tasks with manual verification steps and completion criteria
- **[Automated Testing](site-gen-auto-tests.md)** - Testing conventions, framework setup, and best practices for automated tests

## Quick Start

1. Review the [design document](site-gen-design.md) to understand the workflow
2. Check the [code organization](site-gen-code-org.md) for implementation details
3. Run scripts sequentially (01-12) for each industry vertical

## Current Status

**Status tracking is maintained in [site-gen-plan.md](site-gen-plan.md)** - see individual feature completion criteria and task checkboxes.

**Design Complete**: Workflow and code architecture fully documented  
**First Industry**: AgTech vertical with initial research completed

## Project Structure

```
industry-site/
├── README.md                 # This file - navigation hub
├── site-gen-design.md        # Workflow design
├── site-gen-code-org.md      # Code architecture  
├── site-gen-plan.md          # Implementation plan
├── lib/                      # Shared modules (in progress)
│   ├── config/              # ✓ ConfigLoader implemented
│   ├── errors/              # ✓ Exception classes
│   └── ...                  # Other modules to be created
├── 01-12_*.py               # Generation scripts (to be created)
├── test_config_loader.py    # ConfigLoader tests
└── agtech/                  # AgTech vertical
    ├── site-gen-config.yaml # Sample configuration
    └── research/            # Initial research files
```

## Workflow Summary

The generator operates as 12 sequential scripts:

1. **Initialize Config** - Gather requirements, create configuration
2. **Research Industry** - Search companies/products (Exa + Jina)
3. **Generate Product Schema** - Create product catalog foundation
4. **Analyze Schemas** - Identify relevant directory schemas
5. **Create Schemas** - Generate industry-specific schemas
6. **Generate Directories** - Create CSV data for all schemas
7. **Generate Product Pages** - Detailed markdown product pages
8. **Generate Category Pages** - Category landing pages
9. **Generate Site Pages** - Home, about, contact pages
10. **Validate Site** - Comprehensive validation checks
11. **Convert to Astro** - Transform to Astro components
12. **Generate Demo Features** - Document demoable features

See [site-gen-design.md](site-gen-design.md) for complete details.

## Key Features

- **Configuration-Driven**: Central YAML config controls all generation
- **Validation Checkpoints**: Human review at critical stages
- **Product-Centric**: Product catalog as master reference
- **Directory Integration**: Coherent CSV data for all schemas
- **Link Validation**: Ensures no broken internal links
- **RAG-Ready**: Markdown format for Pinecone indexing
- **Chatbot Integration**: Ready for Salient chat API

## Integration Points

Generated sites integrate with:
- Salient chat API (API token authentication)
- Account-specific agent configurations  
- RAG-powered chatbot with industry knowledge
- Directory search functionality

## Next Steps

1. Complete Foundation Features (F01-F06):
   - ✓ F01-T1: ConfigLoader class
   - → F01-T2: StateManager class (next)
   - F02: LLM Client with retry logic
   - F03: Research tools (Exa + Jina)
   - F04: IO utilities
   - F05: Validation modules
   - F06: Generation functions
2. Develop scripts 01-12 following [implementation plan](site-gen-plan.md)
3. Test complete workflow on AgTech vertical
4. Review validation reports and demo features
5. Refine based on results
6. Extend to additional industry verticals
