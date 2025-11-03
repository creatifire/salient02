# Backend Scripts

## init_accounts_agents.sql

Initializes foundational multi-tenant data: accounts and agent instances.

### Quick Start

```bash
# Using psql
psql $DATABASE_URL -f backend/scripts/init_accounts_agents.sql

# Or check connection first
psql $DATABASE_URL -c "SELECT count(*) FROM accounts;"
```

### What It Does

Seeds 5 accounts and 6 agent instances into the database:

**Accounts**: `default_account`, `acme`, `agrofresh`, `wyckoff`, `prepexcellence`

**Agent Instances**:
- `default_account/simple_chat1`
- `default_account/simple_chat2`
- `acme/acme_chat1`
- `agrofresh/agro_info_chat1`
- `wyckoff/wyckoff_info_chat1`
- `prepexcellence/prepexcel_info_chat1`

### Behavior

**Idempotent**: Safe to run multiple times. Uses `ON CONFLICT DO NOTHING` to skip existing records.

**UUIDs**: Uses fixed UUIDs matching existing production data for consistency with config files and references.

### Prerequisites

1. Database connection available via `$DATABASE_URL`
2. Config files must exist for each agent: `backend/config/agent_configs/{account}/{instance}/config.yaml`

### Run Order

1. **First**: Run `init_accounts_agents.sql` (creates accounts and agents)
2. **Second**: Run `seed_directory.py` (loads directory data for agents that need it)

---

## seed_directory.py

Loads CSV data into directory tables (doctors, products, drugs, etc.) for agent tool usage.

### Quick Start

```bash
cd /path/to/salient02

python backend/scripts/seed_directory.py \
    --account wyckoff \
    --list doctors \
    --entry-type medical_professional \
    --csv backend/data/wyckoff/doctors_profile.csv \
    --mapper medical_professional \
    --description "Wyckoff Heights Medical Center - Medical Professionals"
```

### Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `--account` | Yes | Account slug | `wyckoff`, `acme`, `prepexcellence` |
| `--list` | Yes | Directory list name | `doctors`, `products`, `drugs` |
| `--entry-type` | Yes | Entry type matching schema | `medical_professional`, `pharmaceutical`, `product` |
| `--csv` | Yes | Path to CSV file | `backend/data/wyckoff/doctors.csv` |
| `--mapper` | Yes | Field mapper name | `medical_professional`, `pharmaceutical`, `product` |
| `--description` | No | List description | `"Medical staff directory"` |
| `--schema-file` | No | Schema YAML file | Defaults to `{entry-type}.yaml` |

### Available Mappers

- **`medical_professional`** - Doctors, nurses, medical staff
- **`pharmaceutical`** - Drugs, medications  
- **`product`** - Products, inventory items

### How It Works

**Mapper Function**: Reads CSV column headers and transforms each row into a structured format:
- `name` - Main entry name (from `doctor_name`, `drug_name`, or `product_name`)
- `tags` - Searchable tags (from `language`, `drug_class`, `category`, `brand`)
- `contact_info` - JSONB column storing contact details (phone, email, location, urls)
- `entry_data` - JSONB column storing all other fields (specialty, department, price, etc.)

**Database Tables**:
1. **`directory_lists`** - One record per list (e.g., "Wyckoff doctors list")
   - Links to: account_id
   - Stores: list_name, entry_type, schema_file
2. **`directory_entries`** - Many records per list (e.g., 124 doctors)
   - Links to: directory_list_id (FK)
   - Stores: name, tags, contact_info (JSONB), entry_data (JSONB)

**Example**: CSV row with headers `doctor_name`, `specialty`, `phone` → Mapper extracts values → Creates entry with `name="Dr. Smith"`, `entry_data={"specialty": "Cardiology"}`, `contact_info={"phone": "555-1234"}`

### CSV Field Requirements

#### 1. medical_professional

**Required columns:**
- `doctor_name` - Full name with credentials (e.g., "Geoffrey C. Achonu, MD")
- `department` - Department name (e.g., "Emergency Medicine")
- `specialty` or `speciality` - Medical specialty (e.g., "Plastic Surgery")

**Optional columns:**
- `language` - Comma-separated languages (becomes searchable tags)
- `phone` - Contact phone
- `location` - Office location
- `facility` - Hospital/clinic name
- `board_certifications` - Board certifications
- `education` - Medical school
- `residencies` - Residency programs
- `fellowships` - Fellowship programs
- `internship` - Internship details
- `gender` - Gender (e.g., "male", "female")
- `profile_pic` - Profile image URL

#### 2. pharmaceutical

**Required columns:**
- `drug_name` - Drug name (e.g., "Lisinopril")

**Optional columns:**
- `drug_class` - Drug classification (becomes searchable tag)
- `category` - Category (becomes searchable tag)
- `active_ingredients` - Comma-separated active ingredients
- `dosage_forms` - Comma-separated forms (e.g., "tablet, capsule")
- `common_dosages` - Common dosage information
- `indications` - Medical indications
- `contraindications` - Contraindications
- `side_effects` - Side effects
- `interactions` - Drug interactions
- `pregnancy_category` - Pregnancy category
- `manufacturer` - Manufacturer name
- `website` - Manufacturer website URL
- `contact` - Manufacturer contact info

#### 3. product

**Required columns:**
- `product_name` - Product name

**Optional columns:**
- `category` - Product category (becomes searchable tag)
- `brand` - Brand name (becomes searchable tag)
- `sku` - Stock keeping unit
- `price` - Regular price (numeric)
- `sale_price` - Sale price (numeric)
- `in_stock` - Stock status (true/false/yes/no/1/0)
- `url` - Product page URL
- `support_email` - Support email
- `warranty` - Warranty information
- `dimensions` - Product dimensions
- `weight` - Product weight
- `specifications` - Technical specifications

### Behavior

**Delete-and-replace strategy**: Running the script multiple times with the same `--account` and `--list` will delete existing data and reload from CSV. This makes it safe to re-run for updates.

### Prerequisites

1. Account must exist in database (check with `admin_queries.sql`)
2. CSV file must exist at specified path
3. Backend virtual environment must be activated

### Example: Load Wyckoff Doctors

```bash
python backend/scripts/seed_directory.py \
    --account wyckoff \
    --list doctors \
    --entry-type medical_professional \
    --csv backend/data/wyckoff/doctors_profile.csv \
    --mapper medical_professional
```

Result: 124 doctors loaded into `directory_entries` table, accessible via `search_directory` agent tool.

