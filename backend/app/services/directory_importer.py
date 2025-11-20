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
    
    @staticmethod
    def contact_information_mapper(row: Dict) -> Dict:
        """Map contact information CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - department_name (required)
        - phone_number (required)
        - service_type (required, for tags)
        - hours_of_operation
        - building_location, fax_number, email (contact_info)
        - description, alternate_phone, extension (optional)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        service_type = row.get('service_type', '').strip()
        tags = [service_type] if service_type else []
        
        contact_info = {}
        if row.get('phone_number', '').strip():
            contact_info['phone'] = row['phone_number'].strip()
        if row.get('fax_number', '').strip():
            contact_info['fax'] = row['fax_number'].strip()
        if row.get('email', '').strip():
            contact_info['email'] = row['email'].strip()
        if row.get('building_location', '').strip():
            contact_info['location'] = row['building_location'].strip()
        
        entry_data = {}
        if service_type:
            entry_data['service_type'] = service_type
        
        optional_fields = ['hours_of_operation', 'description', 'alternate_phone', 'extension']
        for field in optional_fields:
            value = row.get(field, '').strip()
            if value:
                entry_data[field] = value
        
        return {
            'name': row.get('department_name', '').strip(),
            'tags': tags,
            'contact_info': contact_info,
            'entry_data': entry_data
        }
    
    @staticmethod
    def department_mapper(row: Dict) -> Dict:
        """Map department CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - name (required)
        - department_function (required)
        - manager_name, staff_count, budget
        - key_responsibilities (pipe-separated)
        - phone, email, location (contact_info)
        - tags (comma-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        contact_info = {}
        if row.get('phone', '').strip():
            contact_info['phone'] = row['phone'].strip()
        if row.get('email', '').strip():
            contact_info['email'] = row['email'].strip()
        if row.get('location', '').strip():
            contact_info['location'] = row['location'].strip()
        
        entry_data = {}
        if row.get('department_function', '').strip():
            entry_data['department_function'] = row['department_function'].strip()
        if row.get('manager_name', '').strip():
            entry_data['manager_name'] = row['manager_name'].strip()
        if row.get('staff_count', '').strip():
            try:
                entry_data['staff_count'] = int(row['staff_count'])
            except ValueError:
                pass
        if row.get('budget', '').strip():
            entry_data['budget'] = row['budget'].strip()
        if row.get('key_responsibilities', '').strip():
            responsibilities = [r.strip() for r in row['key_responsibilities'].split('|') if r.strip()]
            if responsibilities:
                entry_data['key_responsibilities'] = responsibilities
        
        return {
            'name': row.get('name', '').strip(),
            'tags': tags,
            'contact_info': contact_info,
            'entry_data': entry_data
        }
    
    @staticmethod
    def service_mapper(row: Dict) -> Dict:
        """Map service CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - name (required)
        - service_type (required)
        - service_category, duration, cost
        - insurance_accepted (pipe-separated)
        - preparation_required (TRUE/FALSE)
        - preparation_instructions, recovery_time, prerequisites
        - phone, email, location (contact_info)
        - tags (comma-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        contact_info = {}
        if row.get('phone', '').strip():
            contact_info['phone'] = row['phone'].strip()
        if row.get('email', '').strip():
            contact_info['email'] = row['email'].strip()
        if row.get('location', '').strip():
            contact_info['location'] = row['location'].strip()
        
        entry_data = {}
        if row.get('service_type', '').strip():
            entry_data['service_type'] = row['service_type'].strip()
        if row.get('service_category', '').strip():
            entry_data['service_category'] = row['service_category'].strip()
        if row.get('duration', '').strip():
            entry_data['duration'] = row['duration'].strip()
        if row.get('cost', '').strip():
            entry_data['cost'] = row['cost'].strip()
        if row.get('insurance_accepted', '').strip():
            insurance = [i.strip() for i in row['insurance_accepted'].split('|') if i.strip()]
            if insurance:
                entry_data['insurance_accepted'] = insurance
        if row.get('preparation_required', '').strip():
            prep_value = row['preparation_required'].strip().upper()
            entry_data['preparation_required'] = prep_value == 'TRUE'
        if row.get('preparation_instructions', '').strip():
            entry_data['preparation_instructions'] = row['preparation_instructions'].strip()
        if row.get('recovery_time', '').strip():
            entry_data['recovery_time'] = row['recovery_time'].strip()
        if row.get('prerequisites', '').strip():
            entry_data['prerequisites'] = row['prerequisites'].strip()
        
        return {
            'name': row.get('name', '').strip(),
            'tags': tags,
            'contact_info': contact_info,
            'entry_data': entry_data
        }
    
    @staticmethod
    def location_mapper(row: Dict) -> Dict:
        """Map location CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - name (required)
        - location_type (required)
        - building_name, floor, room_number
        - directions, parking_info
        - accessibility_features (pipe-separated)
        - hours
        - phone, email (contact_info)
        - tags (comma-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        contact_info = {}
        if row.get('phone', '').strip():
            contact_info['phone'] = row['phone'].strip()
        if row.get('email', '').strip():
            contact_info['email'] = row['email'].strip()
        
        entry_data = {}
        if row.get('location_type', '').strip():
            entry_data['location_type'] = row['location_type'].strip()
        if row.get('building_name', '').strip():
            entry_data['building_name'] = row['building_name'].strip()
        if row.get('floor', '').strip():
            entry_data['floor'] = row['floor'].strip()
        if row.get('room_number', '').strip():
            entry_data['room_number'] = row['room_number'].strip()
        if row.get('directions', '').strip():
            entry_data['directions'] = row['directions'].strip()
        if row.get('parking_info', '').strip():
            entry_data['parking_info'] = row['parking_info'].strip()
        if row.get('accessibility_features', '').strip():
            features = [f.strip() for f in row['accessibility_features'].split('|') if f.strip()]
            if features:
                entry_data['accessibility_features'] = features
        if row.get('hours', '').strip():
            entry_data['hours'] = row['hours'].strip()
        
        return {
            'name': row.get('name', '').strip(),
            'tags': tags,
            'contact_info': contact_info,
            'entry_data': entry_data
        }
    
    @staticmethod
    def faq_mapper(row: Dict) -> Dict:
        """Map FAQ CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - question (required, used as name)
        - answer (required)
        - category
        - related_links (pipe-separated)
        - last_updated
        - tags (comma-separated)
        - keywords (pipe-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        entry_data = {}
        if row.get('question', '').strip():
            entry_data['question'] = row['question'].strip()
        if row.get('answer', '').strip():
            entry_data['answer'] = row['answer'].strip()
        if row.get('category', '').strip():
            entry_data['category'] = row['category'].strip()
        if row.get('related_links', '').strip():
            links = [l.strip() for l in row['related_links'].split('|') if l.strip()]
            if links:
                entry_data['related_links'] = links
        if row.get('last_updated', '').strip():
            entry_data['last_updated'] = row['last_updated'].strip()
        if row.get('keywords', '').strip():
            keywords = [k.strip() for k in row['keywords'].split('|') if k.strip()]
            if keywords:
                entry_data['keywords'] = keywords
        
        return {
            'name': row.get('question', '').strip(),
            'tags': tags,
            'contact_info': {},
            'entry_data': entry_data
        }
    
    @staticmethod
    def cross_sell_mapper(row: Dict) -> Dict:
        """Map cross-sell CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - primary_item (required)
        - suggested_item (required)
        - relationship (required)
        - reason, bundle_discount, bundle_price
        - frequently_bought_together (TRUE/FALSE)
        - tags (comma-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        entry_data = {}
        if row.get('primary_item', '').strip():
            entry_data['primary_item'] = row['primary_item'].strip()
        if row.get('suggested_item', '').strip():
            entry_data['suggested_item'] = row['suggested_item'].strip()
        if row.get('relationship', '').strip():
            entry_data['relationship'] = row['relationship'].strip()
        if row.get('reason', '').strip():
            entry_data['reason'] = row['reason'].strip()
        if row.get('bundle_discount', '').strip():
            entry_data['bundle_discount'] = row['bundle_discount'].strip()
        if row.get('bundle_price', '').strip():
            try:
                entry_data['bundle_price'] = float(row['bundle_price'])
            except ValueError:
                entry_data['bundle_price'] = row['bundle_price'].strip()
        if row.get('frequently_bought_together', '').strip():
            fbt_value = row['frequently_bought_together'].strip().upper()
            entry_data['frequently_bought_together'] = fbt_value == 'TRUE'
        
        # Name is combination of primary and suggested items
        primary = row.get('primary_item', '').strip()
        suggested = row.get('suggested_item', '').strip()
        name = f"{primary} + {suggested}" if primary and suggested else primary or suggested
        
        return {
            'name': name,
            'tags': tags,
            'contact_info': {},
            'entry_data': entry_data
        }
    
    @staticmethod
    def up_sell_mapper(row: Dict) -> Dict:
        """Map up-sell CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - base_item (required)
        - premium_item (required)
        - additional_features (pipe-separated, required)
        - price_difference, value_proposition
        - benefits (pipe-separated)
        - tags (comma-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        entry_data = {}
        if row.get('base_item', '').strip():
            entry_data['base_item'] = row['base_item'].strip()
        if row.get('premium_item', '').strip():
            entry_data['premium_item'] = row['premium_item'].strip()
        if row.get('additional_features', '').strip():
            features = [f.strip() for f in row['additional_features'].split('|') if f.strip()]
            if features:
                entry_data['additional_features'] = features
        if row.get('price_difference', '').strip():
            entry_data['price_difference'] = row['price_difference'].strip()
        if row.get('value_proposition', '').strip():
            entry_data['value_proposition'] = row['value_proposition'].strip()
        if row.get('benefits', '').strip():
            benefits = [b.strip() for b in row['benefits'].split('|') if b.strip()]
            if benefits:
                entry_data['benefits'] = benefits
        
        # Name is base → premium
        base = row.get('base_item', '').strip()
        premium = row.get('premium_item', '').strip()
        name = f"{base} → {premium}" if base and premium else base or premium
        
        return {
            'name': name,
            'tags': tags,
            'contact_info': {},
            'entry_data': entry_data
        }
    
    @staticmethod
    def competitive_sell_mapper(row: Dict) -> Dict:
        """Map competitive-sell CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - competitor_product (required)
        - our_product (required)
        - differentiators (pipe-separated, required)
        - price_comparison, value_proposition
        - feature_comparison
        - certifications (pipe-separated)
        - tags (comma-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        entry_data = {}
        if row.get('competitor_product', '').strip():
            entry_data['competitor_product'] = row['competitor_product'].strip()
        if row.get('our_product', '').strip():
            entry_data['our_product'] = row['our_product'].strip()
        if row.get('differentiators', '').strip():
            diffs = [d.strip() for d in row['differentiators'].split('|') if d.strip()]
            if diffs:
                entry_data['differentiators'] = diffs
        if row.get('price_comparison', '').strip():
            entry_data['price_comparison'] = row['price_comparison'].strip()
        if row.get('value_proposition', '').strip():
            entry_data['value_proposition'] = row['value_proposition'].strip()
        if row.get('feature_comparison', '').strip():
            entry_data['feature_comparison'] = row['feature_comparison'].strip()
        if row.get('certifications', '').strip():
            certs = [c.strip() for c in row['certifications'].split('|') if c.strip()]
            if certs:
                entry_data['certifications'] = certs
        
        # Name is "Ours vs Competitor"
        ours = row.get('our_product', '').strip()
        competitor = row.get('competitor_product', '').strip()
        name = f"{ours} vs {competitor}" if ours and competitor else ours or competitor
        
        return {
            'name': name,
            'tags': tags,
            'contact_info': {},
            'entry_data': entry_data
        }
    
    @staticmethod
    def classes_mapper(row: Dict) -> Dict:
        """Map classes/seminars CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - name (required)
        - event_type (required: 'class' or 'seminar')
        - program_name, start_date, end_date, days_of_week (pipe-separated)
        - time_of_day, duration, timezone, session_count (numeric)
        - cost_type, price, early_bird_price, registration_fee (numeric)
        - payment_required (TRUE/FALSE), instructor_name, delivery_format
        - venue, capacity (numeric), registration_required (TRUE/FALSE)
        - registration_deadline, enrollment_status, description
        - target_audience, prerequisites (pipe-separated)
        - learning_objectives (pipe-separated), materials_provided (pipe-separated)
        - materials_required (pipe-separated)
        - certificate_offered (TRUE/FALSE), continuing_education_credits
        - phone, email, location (contact_info), product_url (contact_info)
        - tags (comma-separated)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        tags = []
        if row.get('tags', '').strip():
            tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        
        contact_info = {}
        if row.get('phone', '').strip():
            contact_info['phone'] = row['phone'].strip()
        if row.get('email', '').strip():
            contact_info['email'] = row['email'].strip()
        if row.get('location', '').strip():
            contact_info['location'] = row['location'].strip()
        if row.get('product_url', '').strip():
            contact_info['product_url'] = row['product_url'].strip()
        
        entry_data = {}
        
        # Event identification
        if row.get('event_type', '').strip():
            entry_data['event_type'] = row['event_type'].strip()
        if row.get('program_name', '').strip():
            entry_data['program_name'] = row['program_name'].strip()
        
        # Scheduling
        if row.get('start_date', '').strip():
            entry_data['start_date'] = row['start_date'].strip()
        if row.get('end_date', '').strip():
            entry_data['end_date'] = row['end_date'].strip()
        if row.get('days_of_week', '').strip():
            days = [d.strip() for d in row['days_of_week'].split('|') if d.strip()]
            if days:
                entry_data['days_of_week'] = days
        if row.get('time_of_day', '').strip():
            entry_data['time_of_day'] = row['time_of_day'].strip()
        if row.get('duration', '').strip():
            entry_data['duration'] = row['duration'].strip()
        if row.get('timezone', '').strip():
            entry_data['timezone'] = row['timezone'].strip()
        if row.get('session_count', '').strip():
            try:
                entry_data['session_count'] = int(row['session_count'])
            except ValueError:
                pass
        
        # Cost
        if row.get('cost_type', '').strip():
            entry_data['cost_type'] = row['cost_type'].strip()
        if row.get('price', '').strip():
            try:
                entry_data['price'] = float(row['price'])
            except ValueError:
                pass
        if row.get('early_bird_price', '').strip():
            try:
                entry_data['early_bird_price'] = float(row['early_bird_price'])
            except ValueError:
                pass
        if row.get('registration_fee', '').strip():
            try:
                entry_data['registration_fee'] = float(row['registration_fee'])
            except ValueError:
                pass
        if row.get('payment_required', '').strip():
            payment_value = row['payment_required'].strip().upper()
            entry_data['payment_required'] = payment_value == 'TRUE'
        
        # Logistics
        if row.get('instructor_name', '').strip():
            entry_data['instructor_name'] = row['instructor_name'].strip()
        if row.get('delivery_format', '').strip():
            entry_data['delivery_format'] = row['delivery_format'].strip()
        if row.get('venue', '').strip():
            entry_data['venue'] = row['venue'].strip()
        if row.get('capacity', '').strip():
            try:
                entry_data['capacity'] = int(row['capacity'])
            except ValueError:
                pass
        if row.get('registration_required', '').strip():
            reg_value = row['registration_required'].strip().upper()
            entry_data['registration_required'] = reg_value == 'TRUE'
        if row.get('registration_deadline', '').strip():
            entry_data['registration_deadline'] = row['registration_deadline'].strip()
        if row.get('enrollment_status', '').strip():
            entry_data['enrollment_status'] = row['enrollment_status'].strip()
        
        # Content
        if row.get('description', '').strip():
            entry_data['description'] = row['description'].strip()
        if row.get('target_audience', '').strip():
            entry_data['target_audience'] = row['target_audience'].strip()
        if row.get('prerequisites', '').strip():
            prereqs = [p.strip() for p in row['prerequisites'].split('|') if p.strip()]
            if prereqs:
                entry_data['prerequisites'] = prereqs
        if row.get('learning_objectives', '').strip():
            objectives = [o.strip() for o in row['learning_objectives'].split('|') if o.strip()]
            if objectives:
                entry_data['learning_objectives'] = objectives
        if row.get('materials_provided', '').strip():
            materials_prov = [m.strip() for m in row['materials_provided'].split('|') if m.strip()]
            if materials_prov:
                entry_data['materials_provided'] = materials_prov
        if row.get('materials_required', '').strip():
            materials_req = [m.strip() for m in row['materials_required'].split('|') if m.strip()]
            if materials_req:
                entry_data['materials_required'] = materials_req
        if row.get('certificate_offered', '').strip():
            cert_value = row['certificate_offered'].strip().upper()
            entry_data['certificate_offered'] = cert_value == 'TRUE'
        if row.get('continuing_education_credits', '').strip():
            entry_data['continuing_education_credits'] = row['continuing_education_credits'].strip()
        
        return {
            'name': row.get('name', '').strip(),
            'tags': tags,
            'contact_info': contact_info,
            'entry_data': entry_data
        }
    
    @staticmethod
    def experts_mapper(row: Dict) -> Dict:
        """Map experts CSV to DirectoryEntry fields.
        
        Expected CSV columns:
        - name (required)
        - provider_type (required: tutor, consultant, coach, contractor, freelancer)
        - expertise, years_of_experience (numeric)
        - hourly_rate, fixed_price, retainer, per_session_cost (numeric)
        - availability (JSON string), location_type
        - certifications (pipe-separated), education
        - professional_associations (pipe-separated)
        - subjects (pipe-separated), levels (pipe-separated)
        - bio, portfolio (pipe-separated)
        - languages (comma-separated, also goes to tags)
        - phone, email, website, location (contact_info)
        
        Returns:
            Dict with name, tags, contact_info, entry_data
        """
        # Parse tags from languages (comma-separated)
        tags = []
        if row.get('languages', '').strip():
            tags = [lang.strip() for lang in row['languages'].split(',') if lang.strip()]
        
        # Parse contact info
        contact_info = {}
        if row.get('phone', '').strip():
            contact_info['phone'] = row['phone'].strip()
        if row.get('email', '').strip():
            contact_info['email'] = row['email'].strip()
        if row.get('website', '').strip():
            contact_info['website'] = row['website'].strip()
        if row.get('location', '').strip():
            contact_info['location'] = row['location'].strip()
        
        # Parse entry-specific fields
        entry_data = {}
        
        # Required field
        if row.get('provider_type', '').strip():
            entry_data['provider_type'] = row['provider_type'].strip()
        
        # Basic info
        if row.get('expertise', '').strip():
            entry_data['expertise'] = row['expertise'].strip()
        if row.get('years_of_experience', '').strip():
            try:
                entry_data['years_of_experience'] = int(row['years_of_experience'])
            except ValueError:
                pass
        
        # Pricing fields (numeric)
        if row.get('hourly_rate', '').strip():
            try:
                entry_data['hourly_rate'] = float(row['hourly_rate'])
            except ValueError:
                pass
        if row.get('fixed_price', '').strip():
            try:
                entry_data['fixed_price'] = float(row['fixed_price'])
            except ValueError:
                pass
        if row.get('retainer', '').strip():
            try:
                entry_data['retainer'] = float(row['retainer'])
            except ValueError:
                pass
        if row.get('per_session_cost', '').strip():
            try:
                entry_data['per_session_cost'] = float(row['per_session_cost'])
            except ValueError:
                pass
        
        # Availability (JSON string)
        if row.get('availability', '').strip():
            try:
                import json
                entry_data['availability'] = json.loads(row['availability'])
            except (ValueError, json.JSONDecodeError):
                # If not valid JSON, store as string
                entry_data['availability'] = row['availability'].strip()
        
        # Location type
        if row.get('location_type', '').strip():
            entry_data['location_type'] = row['location_type'].strip()
        
        # Certifications (pipe-separated array)
        if row.get('certifications', '').strip():
            certs = [c.strip() for c in row['certifications'].split('|') if c.strip()]
            if certs:
                entry_data['certifications'] = certs
        
        # Education
        if row.get('education', '').strip():
            entry_data['education'] = row['education'].strip()
        
        # Professional associations (pipe-separated array)
        if row.get('professional_associations', '').strip():
            assocs = [a.strip() for a in row['professional_associations'].split('|') if a.strip()]
            if assocs:
                entry_data['professional_associations'] = assocs
        
        # Tutor-specific: subjects (pipe-separated array)
        if row.get('subjects', '').strip():
            subjects = [s.strip() for s in row['subjects'].split('|') if s.strip()]
            if subjects:
                entry_data['subjects'] = subjects
        
        # Tutor-specific: levels (pipe-separated array)
        if row.get('levels', '').strip():
            levels = [l.strip() for l in row['levels'].split('|') if l.strip()]
            if levels:
                entry_data['levels'] = levels
        
        # Bio
        if row.get('bio', '').strip():
            entry_data['bio'] = row['bio'].strip()
        
        # Portfolio (pipe-separated array of URLs)
        if row.get('portfolio', '').strip():
            portfolio = [p.strip() for p in row['portfolio'].split('|') if p.strip()]
            if portfolio:
                entry_data['portfolio'] = portfolio
        
        # Languages (also stored in entry_data for filtering)
        if tags:
            entry_data['languages'] = tags
        
        return {
            'name': row.get('name', '').strip(),
            'tags': tags,
            'contact_info': contact_info,
            'entry_data': entry_data
        }

