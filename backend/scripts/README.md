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

---

## generate_windriver_data.py

Generates diverse test data for hospital directory entries. Creates realistic CSV files with healthcare professionals including physicians, nurse practitioners, therapists, and allied health staff.

### Quick Start

```bash
cd /path/to/salient02

# Generate 500 entries for Windriver Hospital (default)
python backend/scripts/generate_windriver_data.py \
    --count 500 \
    --output backend/data/windriver/windriver_doctors_profiles.csv

# Generate 200 entries for a new hospital
python backend/scripts/generate_windriver_data.py \
    --count 200 \
    --output backend/data/newhospital/staff_profiles.csv

# Generate 1000 entries with custom starting ID
python backend/scripts/generate_windriver_data.py \
    --count 1000 \
    --output backend/data/largehospital/staff.csv \
    --start-id 9400000
```

### Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `--count` | No | Total number of entries to generate (default: 500) | `500`, `200`, `1000` |
| `--output` | Yes | Output CSV file path | `backend/data/windriver/staff.csv` |
| `--start-id` | No | Starting ID number for entries (default: 9300000) | `9300000`, `9400000` |

### What It Generates

The script creates healthcare professional entries with a fixed distribution:

- **60% Physicians (MD/DO)** - Medical and surgical specialists
  - Medical specialties: Cardiology, Neurology, Gastroenterology, Endocrinology, Nephrology, Pulmonology, Infectious Disease, Hematology/Oncology, Psychiatry, etc.
  - Surgical specialties: General Surgery, Orthopedic Surgery, Neurosurgery, Plastic Surgery, Vascular Surgery, Cardiothoracic Surgery, Urology, Ophthalmology, etc.
  - Emergency & Critical Care, Pediatrics, OB/GYN, Radiology, Pathology, Anesthesiology, Podiatry, Dental Medicine

- **10% Advanced Practice Providers**
  - Nurse Practitioners (NP) - Family, Adult Health, Pediatric, Psychiatric-Mental Health, Acute Care
  - Physician Assistants (PA) - Emergency Medicine, Surgery, Cardiology, Internal Medicine, Pediatrics
  - Certified Nurse Midwives (CNM)

- **15% Therapists**
  - Physical Therapists (PT) - Orthopedic, Neurologic, Cardiopulmonary, Geriatric, Pediatric, Sports
  - Occupational Therapists (OT) - Hand Therapy, Pediatric, Geriatric, Neurologic
  - Speech-Language Pathologists (SLP) - Pediatric, Adult, Swallowing Disorders, Voice Disorders
  - Respiratory Therapists (RT) - Critical Care, Pediatric, Neonatal, Pulmonary Rehabilitation

- **15% Other Allied Health**
  - Clinical Nurse Specialists (CNS)
  - Surgical Technologists (CST)
  - Registered Dietitians (RD)
  - Pharmacists (PharmD)
  - Medical Trainers/Educators (MEd)
  - Radiologic Technologists (RT(R))
  - Medical Technologists (MT(ASCP))
  - Perioperative Nurses (RN)

### Features

**Diversity**:
- Realistic names across diverse ethnicities and backgrounds
- Gender diversity (male/female)
- 13 supported languages: English (required), Spanish, French, Hindi, Urdu, Mandarin, Cantonese, Arabic, Swahili, Japanese, Korean, Cambodian, Telugu
- 50% of entries speak 1-3 additional languages beyond English

**Realistic Data**:
- Real US and international medical schools
- Realistic residency and fellowship programs at major hospitals
- Appropriate board certifications with years
- Realistic education and training timelines
- Hospital-appropriate specialty terminology

**CSV Format**:
- Matches structure of `wyckoff_doctors_profiles.csv`
- Compatible with `seed_directory.py` for direct import
- All fields properly quoted and formatted

### Output Format

The generated CSV includes these columns:

- `id` - Sequential ID number (starting from `--start-id`)
- `doctor_name` - Full name with credentials (e.g., "Maria Diaz, MD", "John Smith, NP")
- `department` - Primary department (e.g., "Emergency Medicine", "Surgery")
- `speciality` - Medical specialty or subspecialty
- `facility` - Hospital/facility name (empty by default)
- `phone` - Contact phone (empty by default)
- `location` - Office location (empty by default)
- `board_certifications` - Board certifications with years
- `education` - Medical school or training program
- `residencies` - Residency programs with institution and years
- `fellowships` - Fellowship programs (if applicable)
- `gender` - Gender (male/female)
- `language` - Comma-separated languages spoken
- `insurance` - Insurance information (empty by default)
- `internship` - Internship details (if applicable)
- `badge` - Badge information (empty by default)
- `profile_pic` - Profile picture URL (empty by default)
- `is_active` - Active status (always "1")
- `created_on` - Creation timestamp (default format)

### Behavior

**Automatic Directory Creation**: If the output directory doesn't exist, it will be created automatically.

**Idempotent**: Safe to run multiple times - generates new data each run (uses random seed for variety).

**Distribution**: Maintains fixed percentages (60/10/15/15) with rounding handled automatically.

### Prerequisites

1. Python 3.7+ with standard library (no external dependencies)
2. Output directory must be writable (or will be created if missing)

### Example: Generate Windriver Hospital Data

```bash
python backend/scripts/generate_windriver_data.py \
    --count 500 \
    --output backend/data/windriver/windriver_doctors_profiles.csv
```

Result: 500 entries (300 physicians, 50 advanced practice, 75 therapists, 75 other) saved to CSV file.

### Example: Generate Test Data for New Hospital

```bash
# Create data for a smaller hospital
python backend/scripts/generate_windriver_data.py \
    --count 150 \
    --output backend/data/smallhospital/staff_profiles.csv \
    --start-id 9500000
```

Result: 150 entries (90 physicians, 15 advanced practice, 22 therapists, 23 other) with IDs starting at 9500000.

### Integration with seed_directory.py

After generating the CSV, load it into the database:

```bash
# Step 1: Generate CSV
python backend/scripts/generate_windriver_data.py \
    --count 500 \
    --output backend/data/windriver/windriver_doctors_profiles.csv

# Step 2: Load into database
python backend/scripts/seed_directory.py \
    --account windriver \
    --list doctors \
    --entry-type medical_professional \
    --csv backend/data/windriver/windriver_doctors_profiles.csv \
    --mapper medical_professional \
    --description "Windriver Hospital - Medical Professionals"
```

---

## summarize_session.py

Generates conversation summaries using OpenRouter with config-driven model settings. Supports printing to stdout, saving to file, and sending via email (Mailgun).

### Quick Start

```bash
cd /path/to/salient02

# Print summary to stdout
python backend/scripts/summarize_session.py \
    abc123 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml

# Save to file
python backend/scripts/summarize_session.py \
    abc123 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml \
    --output summary.txt

# Send via email (HTML format)
python backend/scripts/summarize_session.py \
    abc123 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml \
    --email user@example.com \
    --format html

# French summary
python backend/scripts/summarize_session.py \
    abc123 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml \
    --language french

# Spanish HTML email
python backend/scripts/summarize_session.py \
    abc123 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml \
    --language spanish \
    --format html \
    --email user@example.com

# All options (German summary to file and email)
python backend/scripts/summarize_session.py \
    abc123 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml \
    --language german \
    --output zusammenfassung.html \
    --email user@example.com \
    --format html
```

### Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `session_id` | Yes | Session ID (UUID) or session_key | `abc123`, `550e8400-e29b-41d4-a716-446655440000` |
| `config_path` | Yes | Path to agent config.yaml with model_settings | `backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml` |
| `--output`, `-o` | No | Save summary to file | `summary.txt`, `output/email_summary.html` |
| `--email`, `-e` | No | Send summary via email (Mailgun) | `user@example.com` |
| `--format`, `-f` | No | Output format: `text` or `html` (default: text) | `html`, `text` |
| `--language`, `-l` | No | Target language for summary (default: english) | `french`, `spanish`, `german`, `mandarin` |
| `--api-key`, `-a` | No | OpenRouter API key (defaults to env var) | `sk-or-v1-...` |

### How It Works

**Configuration Loading**:
- Reads `model_settings` from specified config.yaml file
- Extracts: `model`, `temperature`, `max_tokens`
- Uses OpenRouter API (like rest of backend)

**Session Retrieval**:
- Loads session from PostgreSQL database
- Retrieves all messages in conversation thread (ordered by created_at)
- Supports lookup by session ID (UUID) or session_key

**Summary Generation**:
- Formats conversation with timestamps and roles
- Sends to OpenRouter with professional summarization prompt
- **Language support**: Generate summaries in any language (English, French, Spanish, German, Mandarin, etc.)
- Returns concise summary (200-400 words) highlighting:
  - Main topics discussed
  - Key information provided
  - Questions and answers
  - Action items or follow-ups

**Output Options**:
1. **Print to stdout** (default) - Display in terminal
2. **Save to file** (`--output`) - Write to text/HTML file
3. **Send via email** (`--email`) - Mailgun integration with professional formatting

### Output Formats

**Text Format** (`--format text`):
```
Conversation Summary
Date: 2025-01-28 10:30:00
Account: windriver

The conversation focused on finding a cardiologist...

Key topics:
- Doctor search by specialty
- Insurance acceptance
- Office locations

---
This summary was automatically generated.
```

**HTML Format** (`--format html`):
- Professional email styling
- Section headings (<h2>)
- Bullet points for key topics
- Highlighted important information
- Responsive design for email clients

### Prerequisites

1. **Database Connection**: `DATABASE_URL` in .env file
2. **OpenRouter API Key**: `OPENROUTER_API_KEY` in .env file
3. **Mailgun (optional)**: `MAILGUN_API_KEY` and `MAILGUN_DOMAIN` for email
4. **Python Dependencies**: `sqlalchemy`, `asyncpg`, `pyyaml`, `python-dotenv`, `openai`, `requests` (for email)
5. **Virtual Environment**: Backend `.venv` activated

### Example: Generate Email Summary

```bash
# Load session and generate HTML email
python backend/scripts/summarize_session.py \
    550e8400-e29b-41d4-a716-446655440000 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml \
    --email patient@example.com \
    --format html
```

Result: Professional HTML email sent via Mailgun with conversation summary.

### Example: Batch Processing

```bash
# Generate summaries for multiple sessions
for session_id in abc123 def456 ghi789; do
    python backend/scripts/summarize_session.py \
        $session_id \
        backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml \
        --output "summaries/session_${session_id}.txt"
done
```

### Configuration Examples

**Using Wind River config** (Gemini Flash 3):
```bash
python backend/scripts/summarize_session.py \
    abc123 \
    backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml
```
Uses: `google/gemini-3-flash-preview`, temperature: 0.3, max_tokens: 8000

**Using custom config** (GPT-4o):
```yaml
# custom_config.yaml
model_settings:
  model: "openai/gpt-4o"
  temperature: 0.5
  max_tokens: 4000
```

```bash
python backend/scripts/summarize_session.py \
    abc123 \
    custom_config.yaml
```

### Error Handling

**Session Not Found**:
```
✗ Error: Session not found: abc123
```
Check session ID is correct (UUID or session_key)

**Config File Not Found**:
```
✗ Error: Config file not found: config.yaml
```
Verify path to config.yaml file

**Missing API Key**:
```
✗ Error: OpenRouter API key required (set OPENROUTER_API_KEY env var)
```
Add `OPENROUTER_API_KEY` to .env file

**No Messages in Session**:
```
⚠ Warning: No messages found in this session
```
Session exists but has no conversation history

### Cost Tracking

The script uses OpenRouter's cost tracking:
```
✓ Summary generated
  Tokens - Prompt: 1247, Completion: 234, Total: 1481
```

Cost is tracked in OpenRouter's usage dashboard.

