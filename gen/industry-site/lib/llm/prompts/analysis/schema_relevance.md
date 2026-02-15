# Evaluate Schema Relevance

Evaluate which existing schemas are relevant for the {industry} industry.

## Available Schemas
{schemas_list}

## Industry Context
- Industry: {industry}
- Company: {company_name}
- Products: {product_categories}

## Evaluation Criteria
- Does the schema make sense for this industry?
- Can it meaningfully connect to the products?
- Would it add value to the site?
- Is it commonly used in this industry?

## Output Format
Return as JSON:
```json
{{
  "relevant_schemas": [
    {{
      "schema_name": "schema.yaml",
      "relevance_score": 0.0-1.0,
      "reasoning": "Why this schema is relevant",
      "recommended": true/false
    }}
  ]
}}
```
