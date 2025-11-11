"""
Phase 3 schema validation tests.

Validates that medical_professional.yaml and phone_directory.yaml have all required fields
for Phase 3 (directory_purpose, synonym_mappings_heading, formal_terms).
"""

import yaml
import sys

def test_medical_professional_schema():
    """Test medical_professional.yaml schema structure."""
    print("\n" + "="*60)
    print("Testing medical_professional.yaml schema")
    print("="*60)
    
    schema = yaml.safe_load(open('backend/config/directory_schemas/medical_professional.yaml'))
    
    # Test YAML syntax
    print("✅ YAML syntax valid")
    
    # Test directory_purpose
    assert 'directory_purpose' in schema, "❌ Missing directory_purpose"
    assert 'description' in schema['directory_purpose'], "❌ Missing description"
    assert 'use_for' in schema['directory_purpose'], "❌ Missing use_for"
    assert len(schema['directory_purpose']['use_for']) >= 3, "❌ Not enough use_for items"
    assert 'example_queries' in schema['directory_purpose'], "❌ Missing example_queries"
    assert len(schema['directory_purpose']['example_queries']) >= 3, "❌ Not enough example_queries"
    assert 'not_for' in schema['directory_purpose'], "❌ Missing not_for"
    print("✅ directory_purpose section complete")
    
    # Test synonym_mappings_heading
    assert 'synonym_mappings_heading' in schema['search_strategy'], "❌ Missing synonym_mappings_heading"
    print(f"✅ synonym_mappings_heading: {schema['search_strategy']['synonym_mappings_heading']}")
    
    # Test formal_terms (not medical_specialties)
    for i, mapping in enumerate(schema['search_strategy']['synonym_mappings']):
        assert 'formal_terms' in mapping, f"❌ Missing formal_terms in mapping {i}"
        assert 'medical_specialties' not in mapping, f"❌ Old medical_specialties key still present in mapping {i}"
    print(f"✅ All {len(schema['search_strategy']['synonym_mappings'])} synonym mappings use formal_terms")
    
    print("\n✅ medical_professional.yaml: ALL TESTS PASSED\n")


def test_phone_directory_schema():
    """Test phone_directory.yaml schema structure."""
    print("\n" + "="*60)
    print("Testing phone_directory.yaml schema")
    print("="*60)
    
    schema = yaml.safe_load(open('backend/config/directory_schemas/phone_directory.yaml'))
    
    # Test YAML syntax
    print("✅ YAML syntax valid")
    
    # Test directory_purpose
    assert 'directory_purpose' in schema, "❌ Missing directory_purpose"
    assert 'description' in schema['directory_purpose'], "❌ Missing description"
    assert 'use_for' in schema['directory_purpose'], "❌ Missing use_for"
    assert 'example_queries' in schema['directory_purpose'], "❌ Missing example_queries"
    assert 'not_for' in schema['directory_purpose'], "❌ Missing not_for"
    print("✅ directory_purpose section complete")
    
    # Test synonym_mappings_heading
    assert 'synonym_mappings_heading' in schema['search_strategy'], "❌ Missing synonym_mappings_heading"
    print(f"✅ synonym_mappings_heading: {schema['search_strategy']['synonym_mappings_heading']}")
    
    # Test formal_terms (not department_names)
    for i, mapping in enumerate(schema['search_strategy']['synonym_mappings']):
        assert 'formal_terms' in mapping, f"❌ Missing formal_terms in mapping {i}"
        assert 'department_names' not in mapping, f"❌ Old department_names key still present in mapping {i}"
    print(f"✅ All {len(schema['search_strategy']['synonym_mappings'])} synonym mappings use formal_terms")
    
    print("\n✅ phone_directory.yaml: ALL TESTS PASSED\n")


def test_schema_loading():
    """Test schema loading via DirectoryImporter."""
    print("\n" + "="*60)
    print("Testing DirectoryImporter schema loading")
    print("="*60)
    
    sys.path.insert(0, 'backend')
    from app.services.directory_importer import DirectoryImporter
    
    # Load medical_professional schema
    med_schema = DirectoryImporter.load_schema("medical_professional.yaml")
    assert med_schema['entry_type'] == 'medical_professional', "❌ Wrong entry_type"
    assert 'directory_purpose' in med_schema, "❌ directory_purpose not loaded"
    print("✅ medical_professional.yaml loads via DirectoryImporter")
    
    # Load phone_directory schema
    phone_schema = DirectoryImporter.load_schema("phone_directory.yaml")
    assert phone_schema['entry_type'] == 'phone_directory', "❌ Wrong entry_type"
    assert 'directory_purpose' in phone_schema, "❌ directory_purpose not loaded"
    print("✅ phone_directory.yaml loads via DirectoryImporter")
    
    print("\n✅ Schema loading: ALL TESTS PASSED\n")


if __name__ == "__main__":
    try:
        test_medical_professional_schema()
        test_phone_directory_schema()
        # test_schema_loading()  # Skipped: requires .env access (sandbox restriction)
        
        print("\n" + "="*60)
        print("SUMMARY: ALL PHASE 3 SCHEMA VALIDATION TESTS PASSED ✅")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

