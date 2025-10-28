# Backend Scripts

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

