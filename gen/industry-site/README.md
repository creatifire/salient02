# Industry Site Generator

## Overview

LLM-powered workflow that generates industry-specific demo sites for the Salient platform through automated research and content generation. Creates complete Astro-based websites with product catalogs, directory data, and chatbot integration.

## Documentation

- **[Site Generation Design](site-gen-design.md)** - Complete workflow design with 12 sequential scripts, data flow, validation checkpoints, and configuration templates
- **[Code Organization](site-gen-code-org.md)** - Detailed code architecture, module structure, class interfaces, and implementation examples

## Quick Start

1. Review the [design document](site-gen-design.md) to understand the workflow
2. Check the [code organization](site-gen-code-org.md) for implementation details
3. Run scripts sequentially (01-12) for each industry vertical

## Current Status

**Design Complete**: Workflow and code architecture documented  
**Implementation**: Ready to begin script development  
**First Industry**: AgTech vertical with initial research completed

## Project Structure

```
industry-site/
├── README.md                 # This file
├── site-gen-design.md       # Workflow design
├── site-gen-code-org.md     # Code architecture
├── lib/                     # Shared modules (to be created)
├── 01-12_*.py              # Generation scripts (to be created)
└── agtech/                 # AgTech vertical
    └── research/           # Initial research files
        ├── agtech-case-study.md
        ├── agtech-chatbot-pain-points.md
        ├── agtech-marketing-strategy.md
        └── agtech-strategic-brief.md
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

1. Implement `lib/` modules per [code organization](site-gen-code-org.md)
2. Develop scripts 01-12 following design patterns
3. Test complete workflow on AgTech vertical
4. Review validation reports and demo features
5. Refine based on results
6. Extend to additional industry verticals
