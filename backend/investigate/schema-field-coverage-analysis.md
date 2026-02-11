# Schema Field Coverage Analysis for directory_tools.py

## Current Code Coverage (lines 286-327)

### ✅ Fully Handled Schemas

#### 1. **medical_professional** ✅
- **Detection**: `'department' in entry.entry_data or 'specialty' in entry.entry_data`
- **Fields displayed**:
  - ✅ department
  - ✅ specialty
  - ✅ education
- **Missing important fields**:
  - ❌ board_certifications
  - ❌ gender
  - ❌ residencies/fellowships

#### 2. **pharmaceutical** ✅ (Partial)
- **Detection**: `'drug_class' in entry.entry_data`
- **Fields displayed**:
  - ✅ drug_class
  - ✅ dosage_forms
  - ✅ indications (truncated to 100 chars)
- **Missing important fields**:
  - ❌ generic_name
  - ❌ brand_names
  - ❌ strengths
  - ❌ contraindications
  - ❌ side_effects

#### 3. **product** ✅ (Partial)
- **Detection**: `'category' in entry.entry_data`
- **Fields displayed**:
  - ✅ category
  - ✅ price
  - ✅ in_stock
- **Missing important fields**:
  - ❌ manufacturer
  - ❌ model_number
  - ❌ features (array)
  - ❌ warranty

---

## ❌ Completely Missing Schemas (7 schemas with NO handlers)

### 4. **contact_information** ❌
**Required field**: service_type
**Key display fields**:
- ❌ service_type
- ❌ hours_of_operation
- ❌ description
- ✅ phone, email, fax, location (handled via contact_info section)

**Detection needed**: `'service_type' in entry.entry_data`

---

### 5. **department** ❌
**Required field**: department_function
**Key display fields**:
- ❌ department_function
- ❌ manager_name
- ❌ staff_count
- ❌ budget
- ❌ key_responsibilities (array)

**Detection needed**: `'department_function' in entry.entry_data`

---

### 6. **service** ❌
**Required field**: service_type
**Key display fields**:
- ❌ service_type
- ❌ service_category
- ❌ duration
- ❌ cost
- ❌ insurance_accepted (array)
- ❌ preparation_required
- ❌ preparation_instructions
- ❌ recovery_time

**Detection needed**: `'service_category' in entry.entry_data` (to distinguish from contact_information)

---

### 7. **location** ❌
**Required field**: location_type
**Key display fields**:
- ❌ location_type
- ❌ building_name
- ❌ floor
- ❌ room_number
- ❌ directions
- ❌ parking_info
- ❌ accessibility_features (array)
- ❌ hours

**Detection needed**: `'location_type' in entry.entry_data`

---

### 8. **faq** ❌
**Required field**: answer
**Key display fields**:
- ❌ question (or use name field)
- ❌ answer
- ❌ category
- ❌ related_links (array)
- ❌ last_updated

**Detection needed**: `'answer' in entry.entry_data`

---

### 9. **cross_sell** ❌
**Required fields**: primary_item, suggested_item, relationship
**Key display fields**:
- ❌ primary_item
- ❌ suggested_item
- ❌ relationship
- ❌ reason
- ❌ bundle_discount
- ❌ frequently_bought_together

**Detection needed**: `'primary_item' in entry.entry_data and 'suggested_item' in entry.entry_data`

---

### 10. **up_sell** ❌
**Required fields**: base_item, premium_item, additional_features
**Key display fields**:
- ❌ base_item
- ❌ premium_item
- ❌ additional_features (array)
- ❌ price_difference
- ❌ value_proposition
- ❌ benefits (array)

**Detection needed**: `'base_item' in entry.entry_data and 'premium_item' in entry.entry_data`

---

### 11. **competitive_sell** ❌
**Required fields**: competitor_product, our_product, differentiators
**Key display fields**:
- ❌ competitor_product
- ❌ our_product
- ❌ differentiators (array)
- ❌ price_comparison
- ❌ value_proposition
- ❌ certifications (array)

**Detection needed**: `'competitor_product' in entry.entry_data and 'our_product' in entry.entry_data`

---

## Summary

**Total Schemas**: 11
**Fully Handled**: 0 (all partial)
**Partially Handled**: 3 (medical_professional, pharmaceutical, product)
**Not Handled At All**: 7 (contact_information, department, service, location, faq, cross_sell, up_sell, competitive_sell)
**Missing Fields in Partial**: ~20+ important fields

**CRITICAL**: 7 out of 11 schemas have ZERO field handlers in directory_tools.py!

---

## Recommendation

**Option 1**: Add detection and formatting for all 7 missing schemas (complex, text format)
**Option 2**: Refactor to JSON format as planned - easier to include ALL fields systematically
**Option 3**: Use entry_type from database instead of field detection (cleaner)

**BEST APPROACH**: Combine Option 2 + 3:
- Use `entry.directory_list.entry_type` for detection (no field guessing)
- Return JSON with ALL relevant fields from each schema
- Simpler, more maintainable, easier for LLM to parse

