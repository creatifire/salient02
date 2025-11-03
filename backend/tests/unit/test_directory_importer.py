# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Unit tests for DirectoryImporter.

Tests schema validation, CSV parsing, and multiple field mappers.
"""

import pytest
import tempfile
import csv
from pathlib import Path
from uuid import uuid4
from app.services.directory_importer import DirectoryImporter


class TestDirectoryImporter:
    """Test suite for DirectoryImporter class."""
    
    def test_load_schema_success(self):
        """Test successful schema loading."""
        schema = DirectoryImporter.load_schema("medical_professional.yaml")
        
        assert schema is not None
        assert schema['entry_type'] == 'medical_professional'
        assert 'required_fields' in schema
        assert 'fields' in schema
        assert 'department' in schema['required_fields']
        assert 'specialty' in schema['required_fields']
    
    def test_load_schema_not_found(self):
        """Test schema loading with non-existent file."""
        with pytest.raises(FileNotFoundError):
            DirectoryImporter.load_schema("nonexistent_schema.yaml")
    
    def test_validate_entry_success(self):
        """Test validation with valid entry."""
        schema = {
            'required_fields': ['department', 'specialty']
        }
        entry_data = {
            'name': 'Dr. John Doe',
            'entry_data': {
                'department': 'Cardiology',
                'specialty': 'Interventional Cardiology'
            }
        }
        
        assert DirectoryImporter.validate_entry(entry_data, schema, 1) is True
    
    def test_validate_entry_missing_name(self):
        """Test validation fails when name is missing."""
        schema = {'required_fields': []}
        entry_data = {
            'name': '',  # Empty name
            'entry_data': {}
        }
        
        assert DirectoryImporter.validate_entry(entry_data, schema, 1) is False
    
    def test_validate_entry_missing_required_field(self):
        """Test validation fails when required field is missing."""
        schema = {
            'required_fields': ['department', 'specialty']
        }
        entry_data = {
            'name': 'Dr. John Doe',
            'entry_data': {
                'department': 'Cardiology'
                # Missing 'specialty'
            }
        }
        
        assert DirectoryImporter.validate_entry(entry_data, schema, 1) is False
    
    def test_validate_entry_empty_required_field(self):
        """Test validation fails when required field is empty string."""
        schema = {
            'required_fields': ['department', 'specialty']
        }
        entry_data = {
            'name': 'Dr. John Doe',
            'entry_data': {
                'department': 'Cardiology',
                'specialty': '   '  # Empty/whitespace
            }
        }
        
        assert DirectoryImporter.validate_entry(entry_data, schema, 1) is False
    
    def test_medical_professional_mapper_complete(self):
        """Test medical professional mapper with complete data."""
        row = {
            'doctor_name': 'Dr. Jane Smith',
            'department': 'Cardiology',
            'speciality': 'Interventional Cardiology',
            'language': 'English, Spanish, French',
            'phone': '(718) 555-1234',
            'location': 'Brooklyn, NY',
            'facility': 'Main Hospital',
            'board_certifications': 'American Board of Internal Medicine',
            'education': 'Harvard Medical School, MD',
            'gender': 'Female'
        }
        
        result = DirectoryImporter.medical_professional_mapper(row)
        
        assert result['name'] == 'Dr. Jane Smith'
        assert result['tags'] == ['English', 'Spanish', 'French']
        assert result['contact_info']['phone'] == '(718) 555-1234'
        assert result['contact_info']['location'] == 'Brooklyn, NY'
        assert result['entry_data']['department'] == 'Cardiology'
        assert result['entry_data']['specialty'] == 'Interventional Cardiology'
        assert result['entry_data']['gender'] == 'Female'
    
    def test_medical_professional_mapper_minimal(self):
        """Test medical professional mapper with minimal data."""
        row = {
            'doctor_name': 'Dr. Bob Jones',
            'department': 'Emergency Medicine',
            'specialty': 'EM'  # Using 'specialty' instead of 'speciality'
        }
        
        result = DirectoryImporter.medical_professional_mapper(row)
        
        assert result['name'] == 'Dr. Bob Jones'
        assert result['tags'] == []  # No languages
        assert result['contact_info'] == {}  # No contact info
        assert result['entry_data']['department'] == 'Emergency Medicine'
        assert result['entry_data']['specialty'] == 'EM'
        assert 'gender' not in result['entry_data']  # Optional field not present
    
    def test_medical_professional_mapper_empty_tags(self):
        """Test medical professional mapper with empty/missing language."""
        row = {
            'doctor_name': 'Dr. Alice Brown',
            'department': 'Surgery',
            'speciality': 'General Surgery',
            'language': '   '  # Whitespace only
        }
        
        result = DirectoryImporter.medical_professional_mapper(row)
        
        assert result['tags'] == []  # Should be empty, not ['']
    
    def test_pharmaceutical_mapper(self):
        """Test pharmaceutical mapper."""
        row = {
            'drug_name': 'Aspirin',
            'drug_class': 'Antiplatelet',
            'category': 'Pain Relief',
            'active_ingredients': 'Acetylsalicylic Acid, Magnesium',
            'dosage_forms': 'tablet, capsule, liquid',
            'indications': 'Pain, fever, inflammation',
            'website': 'https://example.com',
            'manufacturer': 'Acme Pharma'
        }
        
        result = DirectoryImporter.pharmaceutical_mapper(row)
        
        assert result['name'] == 'Aspirin'
        assert 'Antiplatelet' in result['tags']
        assert 'Pain Relief' in result['tags']
        assert result['entry_data']['active_ingredients'] == ['Acetylsalicylic Acid', 'Magnesium']
        assert result['entry_data']['dosage_forms'] == ['tablet', 'capsule', 'liquid']
        assert result['contact_info']['manufacturer_website'] == 'https://example.com'
    
    def test_product_mapper(self):
        """Test product mapper."""
        row = {
            'product_name': 'Widget Pro',
            'category': 'Electronics',
            'brand': 'Acme',
            'sku': 'WP-2024',
            'price': '99.99',
            'sale_price': '79.99',
            'in_stock': 'true',
            'url': 'https://shop.example.com/widget-pro',
            'warranty': '2 years'
        }
        
        result = DirectoryImporter.product_mapper(row)
        
        assert result['name'] == 'Widget Pro'
        assert 'Electronics' in result['tags']
        assert 'Acme' in result['tags']
        assert result['entry_data']['sku'] == 'WP-2024'
        assert result['entry_data']['price'] == 99.99
        assert result['entry_data']['sale_price'] == 79.99
        assert result['entry_data']['in_stock'] is True
        assert result['contact_info']['product_url'] == 'https://shop.example.com/widget-pro'
    
    def test_parse_csv_with_validation(self):
        """Test CSV parsing with schema validation."""
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['doctor_name', 'department', 'speciality', 'language'])
            writer.writeheader()
            writer.writerow({
                'doctor_name': 'Dr. Valid Doctor',
                'department': 'Cardiology',
                'speciality': 'Interventional',
                'language': 'English'
            })
            writer.writerow({
                'doctor_name': 'Dr. Missing Specialty',
                'department': 'Surgery',
                'speciality': '',  # Missing required field
                'language': 'Spanish'
            })
            writer.writerow({
                'doctor_name': '',  # Missing name
                'department': 'ER',
                'speciality': 'Emergency',
                'language': 'French'
            })
            writer.writerow({
                'doctor_name': 'Dr. Another Valid',
                'department': 'Neurology',
                'speciality': 'Neurosurgery',
                'language': ''
            })
            csv_path = f.name
        
        try:
            # Parse with validation
            list_id = uuid4()
            entries = DirectoryImporter.parse_csv(
                csv_path,
                list_id,
                DirectoryImporter.medical_professional_mapper,
                schema_file="medical_professional.yaml"
            )
            
            # Should have 2 valid entries (rows 1 and 4)
            assert len(entries) == 2
            assert entries[0].name == 'Dr. Valid Doctor'
            assert entries[1].name == 'Dr. Another Valid'
            assert all(e.directory_list_id == list_id for e in entries)
        finally:
            Path(csv_path).unlink()
    
    def test_parse_csv_without_validation(self):
        """Test CSV parsing without schema validation."""
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['doctor_name', 'department', 'speciality'])
            writer.writeheader()
            writer.writerow({
                'doctor_name': 'Dr. Test',
                'department': '',  # Would fail validation
                'speciality': 'Test Specialty'
            })
            csv_path = f.name
        
        try:
            # Parse without validation
            list_id = uuid4()
            entries = DirectoryImporter.parse_csv(
                csv_path,
                list_id,
                DirectoryImporter.medical_professional_mapper,
                schema_file=None  # No validation
            )
            
            # Should pass without validation
            assert len(entries) == 1
            assert entries[0].name == 'Dr. Test'
        finally:
            Path(csv_path).unlink()
    
    def test_parse_csv_file_not_found(self):
        """Test CSV parsing with non-existent file."""
        with pytest.raises(FileNotFoundError):
            DirectoryImporter.parse_csv(
                "/nonexistent/file.csv",
                uuid4(),
                DirectoryImporter.medical_professional_mapper
            )

