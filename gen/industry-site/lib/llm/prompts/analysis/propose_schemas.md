# Propose New Schemas

Propose new directory schemas that would be valuable for the {industry} industry.

## Industry Context
- Industry: {industry}
- Company: {company_name}
- Existing Products: {products}
- Current Schemas: {existing_schemas}

## Requirements
- Suggest 3-5 new schema ideas
- Each schema should be industry-appropriate
- Should complement existing schemas
- Must be able to link to products
- Should add real value to the site

## Output Format
Return as JSON:
```json
{{
  "proposed_schemas": [
    {{
      "name": "schema_name",
      "purpose": "What this schema represents",
      "example_entries": ["Example 1", "Example 2"],
      "links_to_products": true/false,
      "value_proposition": "Why this adds value"
    }}
  ]
}}
```
