# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Generic CSV importer for directory entries with schema validation.

Provides flexible CSV parsing with configurable field mapping and YAML schema validation.
Supports multiple directory types (medical professionals, pharmaceuticals, products, etc.).
"""

from __future__ import annotations

import csv
import yaml
import logfire
from typing import List, Dict, Callable, Optional
from uuid import UUID
from pathlib import Path
from ..models.directory import DirectoryEntry


class DirectoryImporter:
    """Generic CSV importer with configurable field mapping and schema validation."""
    
    @staticmethod
    def load_schema(schema_file: str) -> Dict:
        """Load YAML schema definition from backend/config/directory_schemas/.
        
        Args:
            schema_file: Schema filename (e.g., "medical_professional.yaml")
            
        Returns:
            Dict containing schema definition
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
            yaml.YAMLError: If schema file is malformed
        """
        schema_path = Path(__file__).parent.parent.parent / "config" / "directory_schemas" / schema_file
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        logfire.info(
            'service.directory.importer.schema_loaded',
            schema_file=schema_file,
            entry_type=schema.get('entry_type')
        )
        return schema
    
    @staticmethod
    def validate_entry(entry_data: Dict, schema: Dict, row_num: int) -> bool:
        """Validate entry_data against schema required fields.
        
        Args:
            entry_data: Mapped entry data with name, tags, contact_info, entry_data
            schema: YAML schema definition
            row_num: CSV row number (for logging)
            
        Returns:
            True if valid, False if validation fails
        """
        # Check name (always required)
        if not entry_data.get('name', '').strip():
            logfire.warn(
                'service.directory.importer.validation.missing_name',
                row_num=row_num
            )
            return False
        
        # Check required fields in entry_data JSONB
        required_fields = schema.get('required_fields', [])
        for field in required_fields:
            field_value = entry_data.get('entry_data', {}).get(field)
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                logfire.warn(
                    'service.directory.importer.validation.missing_field',
                    row_num=row_num,
                    field=field
                )
                return False
        
        return True
    
    @staticmethod
    def parse_csv(
        csv_path: str, 
        directory_list_id: UUID, 
        field_mapper: Callable[[Dict], Dict],
        schema_file: Optional[str] = None
    ) -> List[DirectoryEntry]:
        """Parse CSV with optional schema validation.
        
        Args:
            csv_path: Path to CSV file
            directory_list_id: UUID of parent DirectoryList
            field_mapper: Function to map CSV row to DirectoryEntry fields
            schema_file: Optional YAML schema file for validation
            
        Returns:
            List of DirectoryEntry instances (not yet persisted)
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
        """
        entries = []
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Load schema if provided
        schema = None
        if schema_file:
            try:
                schema = DirectoryImporter.load_schema(schema_file)
                logfire.info(
                    'service.directory.importer.schema_validation_enabled',
                    schema_file=schema_file
                )
            except Exception as e:
                logfire.exception(
                    'service.directory.importer.schema_load_failed',
                    schema_file=schema_file
                )
                raise
        
        # Parse CSV
        total_rows = 0
        skipped_rows = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                try:
                    entry_data = field_mapper(row)
                    
                    # Validate against schema
                    if schema and not DirectoryImporter.validate_entry(entry_data, schema, total_rows):
                        skipped_rows += 1
                        continue
                    
                    entry = DirectoryEntry(directory_list_id=directory_list_id, **entry_data)
                    entries.append(entry)
                except Exception as e:
                    logfire.warn(
                        'service.directory.importer.parse_error',
                        row_num=total_rows,
                        error=str(e)
                    )
                    skipped_rows += 1
                    continue
        
        logfire.info(
            'service.directory.importer.parse_complete',
            csv_file=csv_file.name,
            entries_parsed=len(entries),
            total_rows=total_rows,
            skipped_rows=skipped_rows,
            success_rate=len(entries)/total_rows*100 if total_rows > 0 else 0
        )
        
        return entries
    
    @staticmethod
    def medical_professional_mapper(row: Dict) -> Dict:
        """Map Wyckoff doctor CSV columns to DirectoryEntry fields.
        
        Expected CSV columns:
        - doctor_name (required)
        - department (required)
        - speciality/specialty (required)
        - language (comma-separated, for tags)
        - phone, location, facility (contact_info)
        - board_certifications, education, residencies, etc. (optional)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        # Parse tags (languages for medical professionals)
        tags_raw = row.get('language', '').strip()
        tags = [tag.strip() for tag in tags_raw.split(',') if tag.strip()] if tags_raw else []
        
        # Build contact_info JSONB (skip empty fields)
        contact_info = {}
        if row.get('phone', '').strip():
            contact_info['phone'] = row['phone'].strip()
        if row.get('location', '').strip():
            contact_info['location'] = row['location'].strip()
        if row.get('facility', '').strip():
            contact_info['facility'] = row['facility'].strip()
        
        # Build entry_data JSONB (skip empty, normalize spelling)
        entry_data = {}
        if row.get('department', '').strip():
            entry_data['department'] = row['department'].strip()
        
        # Normalize "speciality" → "specialty"
        specialty = row.get('speciality', row.get('specialty', '')).strip()
        if specialty:
            entry_data['specialty'] = specialty
        
        # Optional fields
        optional_fields = ['board_certifications', 'education', 'residencies', 'fellowships', 'internship', 'gender', 'profile_pic']
        for field in optional_fields:
            value = row.get(field, '').strip()
            if value:
                entry_data[field] = value
        
        return {
            'name': row.get('doctor_name', '').strip(),
            'tags': tags,
            'contact_info': contact_info,
            'entry_data': entry_data
        }
    
    @staticmethod
    def pharmaceutical_mapper(row: Dict) -> Dict:
        """Map pharmaceutical CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - drug_name (required)
        - drug_class, category (for tags)
        - active_ingredients (comma-separated)
        - dosage_forms, common_dosages, indications, etc.
        - website, contact (manufacturer info)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        drug_class = row.get('drug_class', '').strip()
        tags = [drug_class] if drug_class else []
        
        category = row.get('category', '').strip()
        if category and category not in tags:
            tags.append(category)
        
        entry_data = {}
        if drug_class:
            entry_data['drug_class'] = drug_class
        
        if row.get('active_ingredients', '').strip():
            ingredients = [ing.strip() for ing in row['active_ingredients'].split(',') if ing.strip()]
            entry_data['active_ingredients'] = ingredients
        
        optional_fields = ['dosage_forms', 'common_dosages', 'indications', 'contraindications', 'side_effects', 'interactions', 'pregnancy_category', 'manufacturer']
        for field in optional_fields:
            value = row.get(field, '').strip()
            if value:
                if field == 'dosage_forms':
                    entry_data[field] = [f.strip() for f in value.split(',') if f.strip()]
                else:
                    entry_data[field] = value
        
        return {
            'name': row.get('drug_name', '').strip(),
            'tags': tags,
            'contact_info': {
                'manufacturer_website': row.get('website', '').strip(),
                'manufacturer_contact': row.get('contact', '').strip()
            } if row.get('website') or row.get('contact') else {},
            'entry_data': entry_data
        }
    
    @staticmethod
    def product_mapper(row: Dict) -> Dict:
        """Map product catalog CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - product_name (required)
        - category, brand (for tags)
        - sku, price, sale_price, in_stock
        - url, support_email (contact_info)
        - warranty, dimensions, weight, specifications
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        category = row.get('category', '').strip()
        tags = [category] if category else []
        
        brand = row.get('brand', '').strip()
        if brand and brand not in tags:
            tags.append(brand)
        
        entry_data = {}
        if category:
            entry_data['category'] = category
        if row.get('sku', '').strip():
            entry_data['sku'] = row['sku'].strip()
        if brand:
            entry_data['brand'] = brand
        
        # Price fields
        if row.get('price', '').strip():
            try:
                entry_data['price'] = float(row['price'])
            except ValueError:
                pass
        
        if row.get('sale_price', '').strip():
            try:
                entry_data['sale_price'] = float(row['sale_price'])
            except ValueError:
                pass
        
        # Boolean fields
        if row.get('in_stock', '').strip():
            entry_data['in_stock'] = row['in_stock'].lower() in ['true', '1', 'yes']
        
        optional_fields = ['warranty', 'dimensions', 'weight', 'specifications']
        for field in optional_fields:
            value = row.get(field, '').strip()
            if value:
                entry_data[field] = value
        
        return {
            'name': row.get('product_name', '').strip(),
            'tags': tags,
            'contact_info': {
                'product_url': row.get('url', '').strip(),
                'support_email': row.get('support_email', '').strip()
            } if row.get('url') or row.get('support_email') else {},
            'entry_data': entry_data
        }

