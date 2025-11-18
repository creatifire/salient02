# Agent Configuration Guide

## Overview

This guide explains how to configure AI agents for your Salient account. Agents can search through different types of directories (doctors, products, services, etc.) to answer user questions accurately.

## What is a Directory?

A **directory** is a searchable collection of structured information. Think of it like a specialized phonebook or catalog. Each directory type (schema) defines what fields are available and how to search them.

Your agent can access multiple directories and automatically choose the right one based on user questions.

## Configuration File Location

Agent configurations are stored in YAML files at:
```
backend/config/agent_configs/{account_name}/{agent_instance_name}/config.yaml
```

## Basic Configuration Structure

```yaml
instance_name: "my_info_agent"
account_name: "my_account"
description: "Answers questions about our services"

tools:
  directory:
    enabled: true
    accessible_lists:
      - doctors
      - contact_information
      - services

prompting:
  modules:
    selected:
      - system_prompt
      - tool_selection_hints
```

## Supported Directory Schemas

Salient supports 11 directory schemas. Each schema has specific fields optimized for different types of information.

---

### 1. Medical Professional

**Use for**: Doctors, nurses, specialists, healthcare providers

**Required Fields**:
- `name` - Provider's full name
- `specialty` - Medical specialty (e.g., "Cardiology", "Pediatrics")

**Optional Fields**:
- `department` - Department name
- `education` - Medical school/training
- `board_certifications` - Board certifications with years
- `gender` - Gender identity
- `residencies` - Residency programs
- `fellowships` - Fellowship programs
- `languages` - Array of languages spoken
- `accepting_new_patients` - Boolean

**Contact Fields** (applies to all schemas):
- `phone` - Phone number
- `email` - Email address
- `fax` - Fax number
- `location` - Physical location/office
- `product_url` - Website URL

**Example**:
```yaml
- name: "Dr. Jane Smith"
  specialty: "Cardiology"
  department: "Medicine"
  education: "Harvard Medical School"
  board_certifications: "Cardiovascular Disease, 2015"
  gender: "female"
  languages: ["English", "Spanish"]
  accepting_new_patients: true
  contact_info:
    phone: "555-123-4567"
    email: "jsmith@hospital.com"
    location: "Building A, Floor 3"
```

---

### 2. Contact Information

**Use for**: Department phone numbers, general contact points, service desks

**Required Fields**:
- `name` - Department or service name

**Optional Fields**:
- `service_type` - Type of service (e.g., "Emergency", "Billing", "Scheduling")
- `hours_of_operation` - Business hours
- `description` - What this contact point handles
- `department_name` - Formal department name

**Example**:
```yaml
- name: "Emergency Department"
  service_type: "Emergency"
  hours_of_operation: "24/7"
  description: "Emergency medical services"
  contact_info:
    phone: "555-911-0000"
    location: "Main Hospital, Ground Floor"
```

---

### 3. Pharmaceutical

**Use for**: Medications, drugs, prescriptions

**Required Fields**:
- `name` - Drug name (generic or brand)
- `drug_class` - Medication class (e.g., "Beta Blocker", "Antibiotic")

**Optional Fields**:
- `generic_name` - Generic drug name
- `brand_names` - Array of brand names
- `dosage_forms` - Array of forms (e.g., ["tablet", "liquid"])
- `strengths` - Array of available strengths
- `indications` - What it treats
- `contraindications` - When NOT to use
- `side_effects` - Common side effects
- `interactions` - Drug interactions
- `pregnancy_category` - Safety during pregnancy

**Example**:
```yaml
- name: "Lisinopril"
  generic_name: "Lisinopril"
  brand_names: ["Prinivil", "Zestril"]
  drug_class: "ACE Inhibitor"
  dosage_forms: ["tablet"]
  strengths: ["5mg", "10mg", "20mg"]
  indications: "High blood pressure, heart failure"
  side_effects: "Dizziness, dry cough, headache"
```

---

### 4. Product

**Use for**: Physical products, equipment, retail items

**Required Fields**:
- `name` - Product name
- `category` - Product category

**Optional Fields**:
- `subcategory` - More specific category
- `price` - Numeric price
- `in_stock` - Boolean availability
- `manufacturer` - Manufacturer name
- `model_number` - Model/SKU
- `features` - Array of features
- `warranty` - Warranty information
- `specifications` - Technical specs

**Example**:
```yaml
- name: "UltraComfort Hospital Bed"
  category: "Medical Equipment"
  subcategory: "Patient Beds"
  price: 4999.99
  in_stock: true
  manufacturer: "MedEquip Inc"
  model_number: "UC-2000"
  features:
    - "Electric height adjustment"
    - "Memory foam mattress"
    - "Built-in side rails"
  warranty: "5 years parts and labor"
```

---

### 5. Department

**Use for**: Organizational departments, business units

**Required Fields**:
- `name` - Department name
- `department_function` - What the department does

**Optional Fields**:
- `manager_name` - Department manager
- `staff_count` - Number of staff
- `budget` - Annual budget
- `key_responsibilities` - Array of responsibilities
- `reporting_structure` - Who they report to

**Example**:
```yaml
- name: "Cardiology Department"
  department_function: "Cardiovascular care and treatment"
  manager_name: "Dr. Robert Chen"
  staff_count: 45
  key_responsibilities:
    - "Patient cardiac care"
    - "Cardiac catheterization"
    - "Heart surgery support"
  contact_info:
    phone: "555-234-5678"
    location: "Building B, Floor 2"
```

---

### 6. Service

**Use for**: Medical procedures, treatments, services offered

**Required Fields**:
- `name` - Service name
- `service_type` - Type (e.g., "Diagnostic", "Treatment", "Preventive")

**Optional Fields**:
- `service_category` - Broader category
- `duration` - How long it takes
- `cost` - Price or price range
- `insurance_accepted` - Array of accepted insurance
- `preparation_required` - Boolean
- `preparation_instructions` - What to do before
- `recovery_time` - Expected recovery period
- `prerequisites` - Requirements before service

**Example**:
```yaml
- name: "Cardiac Stress Test"
  service_type: "Diagnostic"
  service_category: "Cardiology"
  duration: "45-60 minutes"
  cost: "$350-$500"
  insurance_accepted: ["Medicare", "BlueCross", "Aetna"]
  preparation_required: true
  preparation_instructions: "Wear comfortable clothing, avoid caffeine 24 hours before"
  recovery_time: "Immediate, resume normal activities"
```

---

### 7. Location

**Use for**: Physical locations, rooms, buildings, facilities

**Required Fields**:
- `name` - Location name
- `location_type` - Type (e.g., "Office", "Lab", "Clinic", "Building")

**Optional Fields**:
- `building_name` - Building name
- `floor` - Floor number or name
- `room_number` - Room identifier
- `directions` - How to find it
- `parking_info` - Parking instructions
- `accessibility_features` - Array of accessibility options
- `hours` - Operating hours

**Example**:
```yaml
- name: "Cardiology Lab 3"
  location_type: "Lab"
  building_name: "Medical Center West"
  floor: "2nd Floor"
  room_number: "W-203"
  directions: "Take west elevators to floor 2, turn left"
  parking_info: "Visitor parking in Lot C"
  accessibility_features:
    - "Wheelchair accessible"
    - "Elevator access"
  hours: "Mon-Fri 7AM-7PM"
```

---

### 8. FAQ

**Use for**: Frequently asked questions and answers

**Required Fields**:
- `name` - Question text (or use `question` field)
- `answer` - Answer text

**Optional Fields**:
- `question` - Question (if not using `name`)
- `category` - FAQ category
- `related_links` - Array of related URLs
- `last_updated` - Date of last update
- `keywords` - Array of search keywords

**Example**:
```yaml
- name: "How do I schedule an appointment?"
  answer: "Call our scheduling line at 555-123-4567 or use our online portal at www.hospital.com/schedule"
  category: "Appointments"
  keywords: ["appointment", "schedule", "booking"]
  last_updated: "2025-01-15"
```

---

### 9. Cross-Sell

**Use for**: Product recommendations, complementary items

**Required Fields**:
- `primary_item` - Main product/service
- `suggested_item` - Recommended companion
- `relationship` - How they relate (e.g., "Frequently bought together")

**Optional Fields**:
- `reason` - Why to buy together
- `bundle_discount` - Discount for bundle
- `bundle_price` - Bundle price
- `frequently_bought_together` - Boolean

**Example**:
```yaml
- primary_item: "Blood Pressure Monitor"
  suggested_item: "Blood Pressure Cuff Replacement"
  relationship: "Compatible accessories"
  reason: "Spare cuffs extend monitor life"
  bundle_discount: "15%"
  bundle_price: 89.99
  frequently_bought_together: true
```

---

### 10. Up-Sell

**Use for**: Premium alternatives, upgrades

**Required Fields**:
- `base_item` - Standard product/service
- `premium_item` - Premium alternative
- `additional_features` - Array of extra features

**Optional Fields**:
- `price_difference` - Additional cost
- `value_proposition` - Why upgrade is worth it
- `benefits` - Array of benefits

**Example**:
```yaml
- base_item: "Standard Annual Checkup"
  premium_item: "Comprehensive Executive Checkup"
  additional_features:
    - "Full cardiac screening"
    - "Advanced bloodwork panel"
    - "Nutritionist consultation"
  price_difference: "$350"
  value_proposition: "Catch health issues earlier with comprehensive screening"
  benefits:
    - "Peace of mind"
    - "Early detection"
    - "Personalized health plan"
```

---

### 11. Competitive-Sell

**Use for**: Comparing your products/services to competitors

**Required Fields**:
- `competitor_product` - Competitor's offering
- `our_product` - Your offering
- `differentiators` - Array of advantages

**Optional Fields**:
- `price_comparison` - Price difference
- `value_proposition` - Your unique value
- `feature_comparison` - Feature-by-feature comparison
- `certifications` - Array of certifications you have

**Example**:
```yaml
- competitor_product: "Generic MRI Scan"
  our_product: "Advanced 3T MRI Scan"
  differentiators:
    - "Higher resolution imaging"
    - "50% faster scan time"
    - "Board-certified radiologist review within 24 hours"
  price_comparison: "Only $100 more"
  value_proposition: "Better images, faster results, expert analysis"
  certifications:
    - "ACR Accredited"
    - "Radiological Society Gold Standard"
```

---

## Configuring Directory Access

### Single Directory

```yaml
tools:
  directory:
    enabled: true
    accessible_lists:
      - doctors
```

### Multiple Directories

The agent will automatically choose the right directory based on the user's question:

```yaml
tools:
  directory:
    enabled: true
    accessible_lists:
      - doctors
      - contact_information
      - services
      - locations
```

## Common Patterns

### Healthcare Organization

```yaml
tools:
  directory:
    enabled: true
    accessible_lists:
      - doctors                # Medical professionals
      - contact_information    # Department phone numbers
      - services              # Procedures and treatments
      - locations             # Facilities and rooms
      - faq                   # Common questions
```

### E-commerce Business

```yaml
tools:
  directory:
    enabled: true
    accessible_lists:
      - products              # Product catalog
      - cross_sell           # Complementary items
      - up_sell              # Premium alternatives
      - competitive_sell     # Competitor comparisons
      - faq                  # Product questions
```

### Pharmaceutical Company

```yaml
tools:
  directory:
    enabled: true
    accessible_lists:
      - pharmaceutical       # Drug information
      - products            # Medical devices
      - contact_information # Support contacts
      - faq                # Medication questions
```

## Best Practices

### 1. Use Tags for Searchability

Add tags to entries for easier searching:

```yaml
tags: ["English", "Spanish", "Evening Hours"]
```

### 2. Complete Contact Information

Always include relevant contact fields:

```yaml
contact_info:
  phone: "555-123-4567"
  email: "dept@company.com"
  location: "Building A, Room 201"
```

### 3. Use Arrays for Multiple Values

```yaml
languages: ["English", "Spanish", "Mandarin"]
features: ["Feature 1", "Feature 2", "Feature 3"]
```

### 4. Be Specific with Descriptions

Good:
```yaml
description: "24/7 emergency cardiac care with board-certified cardiologists"
```

Bad:
```yaml
description: "Emergency services"
```

### 5. Keep Information Current

- Update phone numbers when they change
- Mark products as out of stock
- Update hours of operation seasonally
- Refresh FAQ answers regularly

## Troubleshooting

### Agent Can't Find Information

**Check**:
1. Is the directory listed in `accessible_lists`?
2. Are required fields filled in?
3. Are search terms similar to field values?
4. Are tags relevant to search queries?

### Wrong Directory Selected

**Fix**: Improve directory descriptions in schema files to better distinguish their purposes.

### Missing Fields in Responses

**Check**: Ensure optional fields you want displayed are actually filled in the data.

## Getting Help

For schema-specific questions or custom schema requirements, contact your Salient administrator or refer to:
- `backend/config/directory_schemas/*.yaml` - Full schema definitions
- `memorybank/architecture/directory-search-tool.md` - Technical details

## Version History

- **v1.0** (2025-01-18): Initial guide with 11 schemas

