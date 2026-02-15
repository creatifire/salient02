# Generate Product Names

Generate {count} realistic product names for {company_name} in the {industry} industry.

## Context
Base product names on these real products from market research:
{real_products}

## Product Categories
Organize products into these {category_count} categories:
{categories}

## Requirements
- Product names should sound professional and realistic
- Names should be similar to real products but not identical
- Distribute products evenly across all categories
- Include a brief description for each product (1-2 sentences)
- Names should fit the industry and company brand

## Output Format
Return as JSON array:
```json
[
  {{
    "name": "Product Name",
    "category": "Category Name",
    "description": "Brief product description"
  }}
]
```
