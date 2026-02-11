# Industry Site Generator

## Objective

LLM-powered script that generates industry-specific demo sites for the Salient platform by conducting online research and constructing complete Astro-based websites tailored to specific enterprise segments.

## Structure

```
industry-site/
├── README.md              # This file
├── generate_site.py       # Site generation script(s)
├── agtech/               # Generated AgTech demo site
└── [future industries]/   # Additional industry verticals
```

## Current Status

Initial setup. Design and implementation details to be developed iteratively.

## Scope

- Automated research: LLM conducts online research for industry-specific content
- Site generation: Creates complete Astro static sites
- Industry focus: Starting with AgTech, expandable to other enterprise segments
- Version control: Scripts and generated sites tracked in git

## Integration

Generated sites can integrate with:
- Salient chat API (using API token authentication)
- Account-specific agent configurations
- RAG-powered chatbot with industry-specific knowledge
