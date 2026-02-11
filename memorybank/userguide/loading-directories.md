# Loading Directory Data

## Overview

This guide explains how to load your data into Salient's directory system so your AI agents can search it and answer user questions.

**What you'll learn**:
- How to prepare your data in CSV format
- How to load data into a directory
- How to verify your data loaded correctly
- Common issues and how to fix them

**Who this guide is for**: Anyone managing directory data for AI agents, including non-technical and semi-technical users.

---

## What is "Loading a Directory"?

Loading a directory means importing your data (like doctors, products, services, etc.) from a CSV file into Salient's database where your AI agent can search it.

**Think of it like**:
- Uploading contacts to your phone
- Importing products into an online store
- Loading addresses into a GPS system

Once loaded, your AI agent can answer questions like:
- "What's the phone number for the cardiology department?"
- "Do you have any cardiologists who speak Spanish?"
- "What products do you have in the medical equipment category?"

---

## Before You Start

### Prerequisites

1. **Account Created**: Your Salient account must exist in the system
2. **CSV File Ready**: Your data prepared in CSV format
3. **Schema Chosen**: Know which directory type matches your data (see [Available Directory Types](#available-directory-types))
4. **Terminal Access**: Basic familiarity with running commands

### Required Information

Before running the import, have this information ready:

| Information | Description | Example |
|------------|-------------|---------|
| **Account Name** | Your Salient account identifier | `hospital`, `store`, `clinic` |
| **Directory Name** | What you want to call this directory | `doctors`, `products`, `services` |
| **Schema Type** | What kind of data you're loading | `medical_professional`, `product`, `contact_information` |
| **CSV File Path** | Where your CSV file is located | `backend/data/hospital/doctors.csv` |

---

## Available Directory Types

Salient supports 11 types of directories. Choose the one that matches your data:

### Healthcare & Medical
1. **`medical_professional`** - Doctors, nurses, specialists
2. **`pharmaceutical`** - Medications, drugs
3. **`service`** - Medical procedures, treatments
4. **`department`** - Hospital departments

### General Business
5. **`contact_information`** - Phone numbers, contact points
6. **`product`** - Physical products, equipment
7. **`location`** - Buildings, rooms, facilities
8. **`faq`** - Frequently asked questions

### Sales & Marketing
9. **`cross_sell`** - Complementary product recommendations
10. **`up_sell`** - Premium upgrade recommendations
11. **`competitive_sell`** - Competitor comparisons

**See schema details**: [Agent Configuration Guide](agent-configuration-guide.md)

---

## Step-by-Step: Loading Your Data

### Step 1: Prepare Your CSV File

Your CSV file should have:
- **First row**: Column headers (field names)
- **Remaining rows**: Your data

**CSV Format Tips**:
- Save as `.csv` (not Excel `.xlsx`)
- Use UTF-8 encoding for special characters
- Put text in double quotes if it contains commas
- Keep column names consistent

**Example CSV** (`doctors.csv`):
```csv
doctor_name,specialty,department,phone,location,language
"Dr. Jane Smith, MD",Cardiology,Medicine,555-123-4567,Building A Floor 3,"English, Spanish"
"Dr. Robert Chen, MD",Neurology,Medicine,555-234-5678,Building B Floor 2,"English, Mandarin"
```

**Need help with CSV format?** See sample files in `backend/scripts/sample_directory_csvs/`

### Step 2: Place Your CSV File

Put your CSV file in an organized location:

```
backend/data/{your_account}/{filename}.csv
```

**Example**:
```
backend/data/hospital/doctors.csv
backend/data/hospital/contact_info.csv
backend/data/store/products.csv
```

### Step 3: Run the Import Command

Open your terminal and navigate to your Salient directory:

```bash
cd /path/to/salient02
```

Run the import command with your specific details:

```bash
python backend/scripts/seed_directory.py \
    --account {your_account} \
    --list {directory_name} \
    --entry-type {schema_type} \
    --csv {path_to_csv} \
    --mapper {schema_type} \
    --description "{friendly description}"
```

**Replace the `{placeholders}`** with your actual values.

### Step 4: Verify Success

Look for these success messages:

```
✓ Account 'hospital' found
✓ Schema file loaded: medical_professional.yaml
✓ CSV file loaded: 124 rows
✓ Directory list created/updated
✓ 124 entries imported successfully
```

---

## Real Examples

### Example 1: Loading Doctors

**Scenario**: Import 124 doctors for Wyckoff Hospital

```bash
python backend/scripts/seed_directory.py \
    --account wyckoff \
    --list doctors \
    --entry-type medical_professional \
    --csv backend/data/wyckoff/doctors_profile.csv \
    --mapper medical_professional \
    --description "Wyckoff Heights Medical Center - Medical Professionals"
```

**What happens**:
- Creates a directory called "doctors" for Wyckoff account
- Imports 124 doctor records
- AI agent can now search: "Find me a cardiologist who speaks Spanish"

### Example 2: Loading Contact Information

**Scenario**: Import department phone numbers

```bash
python backend/scripts/seed_directory.py \
    --account hospital \
    --list contact_info \
    --entry-type contact_information \
    --csv backend/data/hospital/departments.csv \
    --mapper contact_information \
    --description "Hospital Department Contact Information"
```

**What happens**:
- Creates "contact_info" directory
- Imports department names, phone numbers, hours
- AI agent can answer: "What's the emergency room phone number?"

### Example 3: Loading Products

**Scenario**: Import medical equipment catalog

```bash
python backend/scripts/seed_directory.py \
    --account medsupply \
    --list equipment \
    --entry-type product \
    --csv backend/data/medsupply/products.csv \
    --mapper product \
    --description "Medical Equipment Catalog"
```

**What happens**:
- Creates "equipment" directory
- Imports product names, prices, specs
- AI agent can answer: "What hospital beds do you have in stock?"

### Example 4: Loading Services

**Scenario**: Import medical services and procedures

```bash
python backend/scripts/seed_directory.py \
    --account clinic \
    --list services \
    --entry-type service \
    --csv backend/data/clinic/services.csv \
    --mapper service \
    --description "Medical Services and Procedures"
```

**What happens**:
- Creates "services" directory
- Imports service names, costs, insurance info
- AI agent can answer: "Do you offer cardiac stress tests? What's the cost?"

---

## Command Arguments Explained

### Required Arguments

| Argument | What It Is | Example |
|----------|-----------|---------|
| `--account` | Your Salient account name (lowercase, no spaces) | `hospital`, `store`, `clinic` |
| `--list` | Name for this directory (you choose) | `doctors`, `products`, `services` |
| `--entry-type` | Schema type matching your data | `medical_professional`, `product`, `service` |
| `--csv` | Path to your CSV file | `backend/data/hospital/doctors.csv` |
| `--mapper` | Which mapper to use (usually same as entry-type) | `medical_professional`, `product`, `service` |

### Optional Arguments

| Argument | What It Is | Example |
|----------|-----------|---------|
| `--description` | Friendly description of this directory | `"Hospital staff directory"` |
| `--schema-file` | Custom schema file (advanced) | `medical_professional_v2.yaml` |

---

## Understanding Mappers

A **mapper** tells Salient how to read your CSV columns and organize the data.

**Available Mappers** (11 total):
1. `medical_professional` - For doctors, nurses, medical staff
2. `contact_information` - For phone numbers, contact points
3. `pharmaceutical` - For medications, drugs
4. `product` - For products, equipment
5. `department` - For organizational departments
6. `service` - For services, procedures
7. `location` - For buildings, rooms, facilities
8. `faq` - For FAQs
9. `cross_sell` - For product bundles
10. `up_sell` - For premium upgrades
11. `competitive_sell` - For competitor comparisons

**Rule of thumb**: Your `--entry-type` and `--mapper` should usually be the same.

---

## CSV Field Requirements

Different directory types expect different CSV columns. Here are the most common:

### Medical Professional

**Required columns**:
- `doctor_name` - Full name with credentials (e.g., "Dr. Jane Smith, MD")
- `specialty` - Medical specialty (e.g., "Cardiology")

**Optional but recommended**:
- `department` - Department name
- `phone` - Contact phone
- `location` - Office location
- `language` - Languages spoken (comma-separated)
- `education` - Medical school
- `board_certifications` - Board certifications

### Contact Information

**Required columns**:
- `name` - Department or service name

**Optional but recommended**:
- `phone` - Phone number
- `email` - Email address
- `service_type` - Type of service
- `hours_of_operation` - Business hours
- `location` - Physical location

### Product

**Required columns**:
- `name` - Product name
- `category` - Product category

**Optional but recommended**:
- `price` - Price (numeric)
- `in_stock` - Availability (TRUE/FALSE)
- `manufacturer` - Manufacturer name
- `model_number` - Model/SKU
- `features` - Features (pipe-separated: `"Feature1|Feature2"`)

### Service

**Required columns**:
- `name` - Service name
- `service_type` - Type of service

**Optional but recommended**:
- `duration` - How long (e.g., "45 minutes")
- `cost` - Price or price range
- `insurance_accepted` - Accepted insurance (pipe-separated)
- `preparation_required` - TRUE/FALSE
- `preparation_instructions` - What to do before

**See all fields**: [Agent Configuration Guide](agent-configuration-guide.md)

---

## Multi-Value Fields in CSV

Some fields can have multiple values (like languages or features).

**Format**: Use pipe `|` to separate multiple values

**Examples**:
```csv
# Languages (multiple values)
"English|Spanish|Mandarin"

# Features (multiple values)
"Electric adjustment|Memory foam|Side rails"

# Insurance accepted (multiple values)
"Medicare|BlueCross|Aetna|Cigna"
```

**Tags**: Use comma `,` to separate tags
```csv
# Tags
"Beginner, Online, Certification Available"
```

---

## Important Behaviors

### Delete-and-Replace

**⚠️ Important**: Running the import command multiple times with the same `--account` and `--list` will:
1. **Delete** all existing data in that directory
2. **Replace** it with data from your CSV file

**What this means**:
- ✅ Safe to re-run to update data
- ✅ Ensures data is always fresh
- ⚠️ Previous data is completely removed
- ⚠️ Always keep backup of your CSV files

**Example**:
```bash
# First run: Imports 100 doctors
python backend/scripts/seed_directory.py --account hospital --list doctors ...

# Second run: Deletes 100 doctors, imports new CSV
python backend/scripts/seed_directory.py --account hospital --list doctors ...
```

### Using Different Directory Names

You can create multiple directories of the same type:

```bash
# Cardiology doctors
python backend/scripts/seed_directory.py \
    --account hospital \
    --list cardiology_doctors \
    --entry-type medical_professional \
    --csv backend/data/hospital/cardiology.csv \
    --mapper medical_professional

# Pediatric doctors
python backend/scripts/seed_directory.py \
    --account hospital \
    --list pediatric_doctors \
    --entry-type medical_professional \
    --csv backend/data/hospital/pediatrics.csv \
    --mapper medical_professional
```

Both are `medical_professional` type, but stored as separate directories.

---

## Troubleshooting

### Error: "Account not found"

**Problem**: The account name doesn't exist in the system

**Solution**:
1. Check your account name spelling
2. Verify account exists: Contact your administrator
3. Account names are case-sensitive and usually lowercase

### Error: "CSV file not found"

**Problem**: The file path is incorrect

**Solution**:
1. Check the file path is correct
2. Use `ls backend/data/` to see available files
3. Use relative path from project root: `backend/data/account/file.csv`

### Error: "No mapper found"

**Problem**: The mapper name doesn't match available mappers

**Solution**:
1. Check mapper spelling
2. Use one of the 11 available mappers (see [Understanding Mappers](#understanding-mappers))
3. Mapper names must match exactly (use underscores, not spaces)

### Error: "Required field missing"

**Problem**: Your CSV is missing a required column

**Solution**:
1. Check CSV field requirements for your schema type
2. Add the missing column to your CSV
3. See [CSV Field Requirements](#csv-field-requirements)

### No Data Appears in Agent

**Problem**: Import succeeded but agent can't find data

**Solution**:
1. Verify agent config includes this directory in `accessible_lists`
2. Check agent config file: `backend/config/agent_configs/{account}/{agent}/config.yaml`
3. Directory name in config must match `--list` name used in import
4. Restart your application after configuration changes

### CSV Formatting Issues

**Problem**: Data imports but looks wrong (broken names, missing fields)

**Solution**:
1. Ensure CSV is UTF-8 encoded
2. Quote text fields that contain commas: `"Last, First"`
3. Use pipe `|` for multi-value fields: `"Value1|Value2"`
4. Check sample CSVs in `backend/scripts/sample_directory_csvs/`

### Too Many or Too Few Records

**Problem**: Row count doesn't match expectations

**Solution**:
1. Check CSV for blank rows (they're skipped)
2. Verify CSV header row exists
3. Look for malformed rows (missing quotes, extra commas)
4. Test with a small CSV (3-5 rows) first

---

## Best Practices

### 1. Test With Small Files First

Before loading 1,000 rows, test with 3-5 rows:

```bash
# Create test.csv with 3 sample rows
python backend/scripts/seed_directory.py \
    --account test_account \
    --list test_directory \
    --entry-type medical_professional \
    --csv backend/data/test/test.csv \
    --mapper medical_professional
```

Verify it works, then load your full file.

### 2. Keep CSV Backups

Always keep backup copies of your CSV files:
```
backend/data/hospital/
├── doctors.csv           # Current version
├── doctors_backup.csv    # Backup before changes
└── doctors_2025-01-18.csv  # Dated backup
```

### 3. Use Descriptive Directory Names

**Good**: `doctors`, `pediatric_doctors`, `emergency_contacts`

**Bad**: `data1`, `list`, `temp`

### 4. Document Your Directories

Keep a record of what each directory contains:

```yaml
# directory_inventory.txt
doctors:
  type: medical_professional
  source: doctors_profile.csv
  last_updated: 2025-01-18
  row_count: 124

contact_info:
  type: contact_information
  source: departments.csv
  last_updated: 2025-01-18
  row_count: 15
```

### 5. Validate After Import

After importing, test your agent:
- Ask a simple question: "How many doctors do we have?"
- Test specific searches: "Find Dr. Smith"
- Verify contact info: "What's the emergency room number?"

---

## Quick Reference

### Basic Import Command Template

```bash
python backend/scripts/seed_directory.py \
    --account YOUR_ACCOUNT \
    --list YOUR_DIRECTORY_NAME \
    --entry-type SCHEMA_TYPE \
    --csv PATH_TO_CSV \
    --mapper SCHEMA_TYPE \
    --description "Your description here"
```

### Common Schema Types

- `medical_professional` - Doctors, nurses, medical staff
- `contact_information` - Phone numbers, contacts
- `product` - Products, equipment
- `service` - Services, procedures
- `pharmaceutical` - Medications, drugs
- `department` - Departments
- `location` - Buildings, rooms
- `faq` - FAQs

### File Locations

- **Your CSV files**: `backend/data/{account}/{filename}.csv`
- **Sample CSVs**: `backend/scripts/sample_directory_csvs/`
- **Schema definitions**: `backend/config/directory_schemas/`
- **Agent configs**: `backend/config/agent_configs/{account}/{agent}/config.yaml`

---

## Getting Help

### Documentation

- **Schema field reference**: [Agent Configuration Guide](agent-configuration-guide.md)
- **Creating new schemas**: [Adding and Modifying Directory Schemas](adding-modifying-directory-schemas.md)
- **Technical details**: `backend/scripts/README.md`

### Sample Files

Look at existing sample CSVs for formatting examples:
```bash
ls backend/scripts/sample_directory_csvs/
```

Each file shows the correct format for that schema type.

### Support

If you encounter issues:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review sample CSV files for correct format
3. Test with a small CSV file (3-5 rows) first
4. Contact your Salient administrator

---

## Next Steps

After loading your directory data:

1. **Configure Your Agent**: Update agent config to access this directory
   - File: `backend/config/agent_configs/{account}/{agent}/config.yaml`
   - Add directory to `accessible_lists`

2. **Test Your Agent**: Ask questions to verify data is searchable
   - Simple queries: "How many [items] do we have?"
   - Specific searches: "Find [specific item]"
   - Complex queries: "Find [items] that match [criteria]"

3. **Monitor and Update**: Keep your data current
   - Re-run import when data changes
   - Keep CSV backups
   - Document when you update

---

## Version History

- **v1.0** (2025-01-18): Initial guide for loading directory data


