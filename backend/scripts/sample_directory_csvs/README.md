# Sample Directory CSV Files

This folder contains sample CSV files for each directory schema type supported by Salient.

## Purpose

These samples help you:
- Understand the expected CSV format for each schema
- See which fields are required vs optional
- Use as templates for creating your own data files
- Test the directory import functionality

## Available Schemas

| Schema | Sample File | Mapper Available |
|--------|-------------|------------------|
| Medical Professional | `medical_professional_sample.csv` | ✅ Yes |
| Contact Information | `contact_information_sample.csv` | ✅ Yes |
| Pharmaceutical | `pharmaceutical_sample.csv` | ✅ Yes |
| Product | `product_sample.csv` | ✅ Yes |
| Department | `department_sample.csv` | ❌ No (add mapper if needed) |
| Service | `service_sample.csv` | ❌ No (add mapper if needed) |
| Location | `location_sample.csv` | ❌ No (add mapper if needed) |
| FAQ | `faq_sample.csv` | ❌ No (add mapper if needed) |
| Cross-Sell | `cross_sell_sample.csv` | ❌ No (add mapper if needed) |
| Up-Sell | `up_sell_sample.csv` | ❌ No (add mapper if needed) |
| Competitive-Sell | `competitive_sell_sample.csv` | ❌ No (add mapper if needed) |

## Using These Samples

### For Schemas WITH Mappers (✅)

You can use these samples directly with the `seed_directory.py` script:

```bash
# Example: Import medical professionals
python backend/scripts/seed_directory.py \
    --account your_account \
    --list doctors \
    --entry-type medical_professional \
    --csv backend/scripts/sample_directory_csvs/medical_professional_sample.csv \
    --mapper medical_professional \
    --description "Sample medical professionals"

# Example: Import contact information
python backend/scripts/seed_directory.py \
    --account your_account \
    --list contacts \
    --entry-type contact_information \
    --csv backend/scripts/sample_directory_csvs/contact_information_sample.csv \
    --mapper contact_information \
    --description "Sample contact information"

# Example: Import pharmaceuticals
python backend/scripts/seed_directory.py \
    --account your_account \
    --list drugs \
    --entry-type pharmaceutical \
    --csv backend/scripts/sample_directory_csvs/pharmaceutical_sample.csv \
    --mapper pharmaceutical \
    --description "Sample pharmaceutical database"

# Example: Import products
python backend/scripts/seed_directory.py \
    --account your_account \
    --list products \
    --entry-type product \
    --csv backend/scripts/sample_directory_csvs/product_sample.csv \
    --mapper product \
    --description "Sample product catalog"
```

### For Schemas WITHOUT Mappers (❌)

These samples show the expected field structure, but you'll need to either:

**Option 1**: Create a custom mapper in `backend/app/services/directory_importer.py`

See `memorybank/userguide/adding-modifying-directory-schemas.md` for detailed instructions.

**Option 2**: Import data directly via API or database

The samples show which fields your data should have.

## CSV Format Guidelines

### General Rules

1. **First row is header**: Column names matching schema fields
2. **Double quotes for text**: Use `"text here"` for fields with commas or special characters
3. **Multi-value fields**: Use pipe `|` as separator (e.g., `Item 1|Item 2|Item 3`)
4. **Empty fields**: Leave blank (don't use `NULL` or `N/A`)
5. **Boolean fields**: Use `TRUE` or `FALSE` (case-insensitive)
6. **Numeric fields**: No quotes, no commas (e.g., `4999.99` not `"4,999.99"`)

### Schema-Specific Notes

#### Medical Professional
- `board_certifications`, `residencies`, `fellowships`: Multi-line text OK
- `language`: Comma-separated (e.g., `"English, Spanish"`)

#### Contact Information
- `department_name`: Primary identifier (required)
- `phone_number`: Include extension in `extension` field if needed
- `hours_of_operation`: Free-form text

#### Pharmaceutical
- `active_ingredients`: Comma-separated list
- `dosage_forms`: Comma-separated list (e.g., `"Tablet, Oral Solution"`)

#### Product
- `in_stock`: Boolean (TRUE/FALSE)
- `price`: Numeric without currency symbol

#### Department
- `key_responsibilities`: Pipe-separated list (e.g., `"Task 1|Task 2|Task 3"`)
- `staff_count`: Numeric

#### Service
- `insurance_accepted`: Pipe-separated list
- `preparation_required`: Boolean

#### Location
- `accessibility_features`: Pipe-separated list

#### FAQ
- `keywords`: Pipe-separated list for search
- `related_links`: Pipe-separated list of URLs

#### Cross-Sell / Up-Sell
- `additional_features`: Pipe-separated list
- `frequently_bought_together`: Boolean (cross-sell only)

#### Competitive-Sell
- `differentiators`: Pipe-separated list
- `certifications`: Pipe-separated list

## Customizing for Your Data

1. **Copy the relevant sample**: `cp {schema}_sample.csv my_data.csv`
2. **Replace sample data**: Keep the header row, replace data rows
3. **Add more rows**: Follow the same format
4. **Validate fields**: Check against schema in `backend/config/directory_schemas/{schema}.yaml`
5. **Import**: Use `seed_directory.py` script (if mapper exists)

## Field Mapping Reference

For schemas with mappers, see the mapper function in `backend/app/services/directory_importer.py` to understand how CSV columns map to database fields.

Example mapper functions:
- `medical_professional_mapper()` - Line ~170
- `contact_information_mapper()` - Line ~332
- `pharmaceutical_mapper()` - Line ~222
- `product_mapper()` - Line ~270

## Need Help?

- **Schema details**: See `memorybank/userguide/agent-configuration-guide.md`
- **Adding new schemas**: See `memorybank/userguide/adding-modifying-directory-schemas.md`
- **Database schema**: See `backend/config/directory_schemas/*.yaml`
- **Import errors**: Check logs for validation failures (missing required fields, incorrect types)

## Version

These samples align with schema version 1.0 as of 2025-01-18.

