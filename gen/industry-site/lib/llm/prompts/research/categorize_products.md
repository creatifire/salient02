# Categorize Products Prompt

Organize the following products into logical categories.

## Products to Categorize
{products}

## Requirements
- Create {num_categories} high-level categories
- Categories should be intuitive and industry-appropriate
- Distribute products evenly across categories
- Each category should have a clear, descriptive name
- Ensure no product appears in multiple categories

## Output Format
Return as JSON with structure:
```json
{{
  "categories": [
    {{
      "name": "Category Name",
      "description": "Brief category description",
      "products": ["Product 1", "Product 2", ...]
    }}
  ]
}}
```
