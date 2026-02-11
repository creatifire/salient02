# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Profile schema loader for dynamic profile field configuration.

Provides schema loading, validation, and prompt module generation for profile capture.
Follows DirectoryImporter pattern with profile-specific logic:
- File-level cascade: instance → system fallback
- Field type validation with regex support
- Prompt module generation for system prompt integration
"""

from __future__ import annotations

import re
import yaml
import logfire
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class ProfileSchemaLoader:
    """Load and validate profile schemas from YAML files."""
    
    # Valid field types
    VALID_FIELD_TYPES = {
        'email', 'phone', 'url', 'string', 'text', 
        'enum', 'date', 'number', 'boolean', 'address'
    }
    
    # Required metadata for all fields
    REQUIRED_METADATA = {'type', 'required', 'description', 'examples', 'semantic_hints'}
    
    # Conditionally required metadata
    REQUIRES_VALIDATION = {'email', 'phone', 'url', 'date'}  # Must have validation regex
    REQUIRES_ENUM_VALUES = {'enum'}  # Must have enum_values list
    
    @staticmethod
    def load_schema(
        account_slug: str,
        instance_slug: str,
        schema_file: str = "profile.yaml"
    ) -> Optional[Dict]:
        """
        Load profile schema with file-level cascade.
        
        Cascade order:
        1. backend/config/agent_configs/{account}/{instance}/{schema_file}
        2. backend/config/prompt_modules/system/{schema_file}
        
        Args:
            account_slug: Account slug (e.g., "wyckoff")
            instance_slug: Agent instance slug (e.g., "wyckoff_info_chat1")
            schema_file: Schema filename (default: "profile.yaml")
            
        Returns:
            Dict containing schema definition, or None if neither file exists
        """
        # Try instance-level first (highest priority)
        instance_path = (
            Path(__file__).parent.parent.parent / "config" / "agent_configs" / 
            account_slug / instance_slug / schema_file
        )
        
        if instance_path.exists():
            try:
                with open(instance_path, 'r', encoding='utf-8') as f:
                    schema = yaml.safe_load(f)
                
                logfire.info(
                    'service.profile_schema_loader.schema_loaded',
                    source='instance',
                    account=account_slug,
                    instance=instance_slug,
                    file_path=str(instance_path),
                    profile_version=schema.get('profile_version', 'unknown')
                )
                return schema
                
            except yaml.YAMLError as e:
                logfire.error(
                    'service.profile_schema_loader.yaml_error',
                    source='instance',
                    account=account_slug,
                    instance=instance_slug,
                    file_path=str(instance_path),
                    error=str(e),
                    error_line=getattr(e, 'problem_mark', None)
                )
                return None
            except Exception as e:
                logfire.error(
                    'service.profile_schema_loader.load_error',
                    source='instance',
                    account=account_slug,
                    instance=instance_slug,
                    file_path=str(instance_path),
                    error=str(e)
                )
                return None
        
        # Fall back to system default
        system_path = (
            Path(__file__).parent.parent.parent / "config" / 
            "prompt_modules" / "system" / schema_file
        )
        
        if system_path.exists():
            try:
                with open(system_path, 'r', encoding='utf-8') as f:
                    schema = yaml.safe_load(f)
                
                logfire.info(
                    'service.profile_schema_loader.schema_loaded',
                    source='system_fallback',
                    account=account_slug,
                    instance=instance_slug,
                    file_path=str(system_path),
                    profile_version=schema.get('profile_version', 'unknown')
                )
                return schema
                
            except yaml.YAMLError as e:
                logfire.error(
                    'service.profile_schema_loader.yaml_error',
                    source='system_fallback',
                    file_path=str(system_path),
                    error=str(e),
                    error_line=getattr(e, 'problem_mark', None)
                )
                return None
            except Exception as e:
                logfire.error(
                    'service.profile_schema_loader.load_error',
                    source='system_fallback',
                    file_path=str(system_path),
                    error=str(e)
                )
                return None
        
        # Neither file exists
        logfire.warn(
            'service.profile_schema_loader.schema_not_found',
            account=account_slug,
            instance=instance_slug,
            schema_file=schema_file,
            searched_paths=[str(instance_path), str(system_path)]
        )
        return None
    
    @staticmethod
    def validate_schema(schema: Dict) -> Tuple[bool, List[str]]:
        """
        Validate profile schema structure and field definitions.
        
        Checks:
        - Required top-level keys: profile_version, fields
        - Required field metadata: type, required, description, validation, examples, semantic_hints
        - Field type validity (email, phone, string, text, enum, date, address, url, number, boolean)
        - Regex pattern validity for validation rules
        - Enum values presence when type=enum
        
        Args:
            schema: Schema dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check top-level required keys
        if not isinstance(schema, dict):
            errors.append("Schema must be a dictionary")
            return False, errors
        
        if 'profile_version' not in schema:
            errors.append("Missing required top-level key: 'profile_version'")
        
        if 'fields' not in schema:
            errors.append("Missing required top-level key: 'fields'")
            return False, errors
        
        fields = schema.get('fields', {})
        if not isinstance(fields, dict):
            errors.append("'fields' must be a dictionary")
            return False, errors
        
        if not fields:
            errors.append("'fields' dictionary is empty (must have at least one field)")
        
        # Validate each field
        for field_name, field_def in fields.items():
            field_errors = ProfileSchemaLoader._validate_field(field_name, field_def)
            errors.extend(field_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def _validate_field(field_name: str, field_def: Dict) -> List[str]:
        """
        Validate a single field definition.
        
        Args:
            field_name: Name of the field
            field_def: Field definition dictionary
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not isinstance(field_def, dict):
            errors.append(f"Field '{field_name}': definition must be a dictionary")
            return errors
        
        # Check required metadata
        missing_metadata = ProfileSchemaLoader.REQUIRED_METADATA - set(field_def.keys())
        if missing_metadata:
            errors.append(
                f"Field '{field_name}': missing required metadata: {', '.join(sorted(missing_metadata))}"
            )
        
        # Check field type
        field_type = field_def.get('type')
        if field_type not in ProfileSchemaLoader.VALID_FIELD_TYPES:
            errors.append(
                f"Field '{field_name}': invalid type '{field_type}'. "
                f"Valid types: {', '.join(sorted(ProfileSchemaLoader.VALID_FIELD_TYPES))}"
            )
        
        # Check validation regex for types that require it
        if field_type in ProfileSchemaLoader.REQUIRES_VALIDATION:
            validation = field_def.get('validation')
            if not validation:
                errors.append(
                    f"Field '{field_name}': type '{field_type}' requires 'validation' regex pattern"
                )
            else:
                # Verify regex is valid
                try:
                    re.compile(validation)
                except re.error as e:
                    errors.append(
                        f"Field '{field_name}': invalid regex pattern in 'validation': {str(e)}"
                    )
        
        # Check enum_values for enum type
        if field_type in ProfileSchemaLoader.REQUIRES_ENUM_VALUES:
            enum_values = field_def.get('enum_values')
            if not enum_values:
                errors.append(
                    f"Field '{field_name}': type 'enum' requires 'enum_values' list"
                )
            elif not isinstance(enum_values, list) or not enum_values:
                errors.append(
                    f"Field '{field_name}': 'enum_values' must be a non-empty list"
                )
        
        # Check required field is boolean
        if 'required' in field_def and not isinstance(field_def['required'], bool):
            errors.append(
                f"Field '{field_name}': 'required' must be a boolean (true/false)"
            )
        
        # Check examples is a list
        if 'examples' in field_def:
            if not isinstance(field_def['examples'], list):
                errors.append(
                    f"Field '{field_name}': 'examples' must be a list"
                )
            elif not field_def['examples']:
                errors.append(
                    f"Field '{field_name}': 'examples' list is empty (must have at least one example)"
                )
        
        return errors
    
    @staticmethod
    def generate_prompt_module(schema: Dict) -> str:
        """
        Generate profile_capture_hints.md content from schema.
        
        Creates a markdown module containing:
        - Required/optional fields list
        - Semantic hints per field
        - Capture guidelines
        - Example scenarios
        - Validation rules summary
        
        Args:
            schema: Validated profile schema
            
        Returns:
            Markdown content as string
        """
        lines = []
        
        # Header
        lines.append("# Profile Capture Guidelines")
        lines.append("")
        lines.append(f"Profile Schema Version: {schema.get('profile_version', 'unknown')}")
        lines.append("")
        
        fields = schema.get('fields', {})
        if not fields:
            lines.append("*No fields defined in schema*")
            return "\n".join(lines)
        
        # Separate required and optional fields
        required_fields = []
        optional_fields = []
        
        for field_name, field_def in fields.items():
            if field_def.get('required', False):
                required_fields.append((field_name, field_def))
            else:
                optional_fields.append((field_name, field_def))
        
        # Required Fields Section
        if required_fields:
            lines.append("## Required Profile Fields")
            lines.append("")
            lines.append("The following fields are **required** and must be captured during the conversation:")
            lines.append("")
            
            for field_name, field_def in required_fields:
                lines.append(f"### {field_name.replace('_', ' ').title()}")
                lines.append(f"**Type**: {field_def.get('type', 'unknown')}")
                lines.append(f"**Description**: {field_def.get('description', 'No description')}")
                lines.append("")
                
                # Semantic hints
                semantic_hints = field_def.get('semantic_hints', '')
                if semantic_hints:
                    lines.append(f"**When to capture**: {semantic_hints}")
                    lines.append("")
                
                # Examples
                examples = field_def.get('examples', [])
                if examples:
                    lines.append("**Examples**:")
                    for example in examples:
                        lines.append(f"- {example}")
                    lines.append("")
                
                # Validation rules
                validation = field_def.get('validation')
                if validation:
                    lines.append(f"**Validation**: Must match pattern: `{validation}`")
                    lines.append("")
                
                # Enum values
                enum_values = field_def.get('enum_values')
                if enum_values:
                    lines.append(f"**Allowed values**: {', '.join(enum_values)}")
                    lines.append("")
                
                lines.append("")
        
        # Optional Fields Section
        if optional_fields:
            lines.append("## Optional Profile Fields")
            lines.append("")
            lines.append("The following fields are **optional** and may be captured if relevant:")
            lines.append("")
            
            for field_name, field_def in optional_fields:
                lines.append(f"### {field_name.replace('_', ' ').title()}")
                lines.append(f"**Type**: {field_def.get('type', 'unknown')}")
                lines.append(f"**Description**: {field_def.get('description', 'No description')}")
                lines.append("")
                
                # Semantic hints
                semantic_hints = field_def.get('semantic_hints', '')
                if semantic_hints:
                    lines.append(f"**When to capture**: {semantic_hints}")
                    lines.append("")
                
                # Examples (brief for optional fields)
                examples = field_def.get('examples', [])
                if examples:
                    lines.append(f"**Examples**: {', '.join(str(e) for e in examples[:3])}")
                    lines.append("")
                
                lines.append("")
        
        # Capture Guidelines Section
        lines.append("## Capture Guidelines")
        lines.append("")
        lines.append("- **Natural conversation**: Ask for profile information conversationally, not like a form")
        lines.append("- **Context-appropriate timing**: Capture information when it naturally fits the conversation flow")
        lines.append("- **Validate immediately**: Use the profile capture tool to validate and store each field")
        lines.append("- **Handle errors gracefully**: If validation fails, explain the issue and ask for correction")
        lines.append("- **Don't repeat requests**: Check if information is already captured before asking again")
        lines.append("")
        
        # Capture hints from schema
        capture_hints = schema.get('capture_hints', {})
        if capture_hints:
            lines.append("## Additional Capture Hints")
            lines.append("")
            for hint_key, hint_value in capture_hints.items():
                lines.append(f"**{hint_key.replace('_', ' ').title()}**: {hint_value}")
                lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def validate_field_value(
        field_name: str,
        field_value: str,
        field_schema: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a captured field value against schema.
        
        Applies:
        - Regex validation (if specified)
        - Length constraints (min_length, max_length)
        - Value constraints (min_value, max_value)
        - Enum validation (if type=enum)
        
        Args:
            field_name: Name of the field being validated
            field_value: Value to validate
            field_schema: Field schema definition
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        field_type = field_schema.get('type')
        
        # Regex validation (for email, phone, url, date)
        validation_pattern = field_schema.get('validation')
        if validation_pattern:
            try:
                if not re.match(validation_pattern, field_value):
                    return False, f"Invalid format for {field_name}. Expected pattern: {validation_pattern}"
            except re.error:
                logfire.error(
                    'service.profile_schema_loader.validation_regex_error',
                    field_name=field_name,
                    pattern=validation_pattern
                )
                return False, f"Internal validation error for {field_name}"
        
        # Enum validation
        if field_type == 'enum':
            enum_values = field_schema.get('enum_values', [])
            if field_value not in enum_values:
                return False, f"Invalid value for {field_name}. Must be one of: {', '.join(enum_values)}"
        
        # Length constraints (for string/text types)
        if field_type in {'string', 'text', 'email', 'phone', 'url'}:
            min_length = field_schema.get('min_length')
            max_length = field_schema.get('max_length')
            
            if min_length is not None and len(field_value) < min_length:
                return False, f"{field_name} must be at least {min_length} characters"
            
            if max_length is not None and len(field_value) > max_length:
                return False, f"{field_name} must be at most {max_length} characters"
        
        # Numeric validation (for number type)
        if field_type == 'number':
            try:
                numeric_value = float(field_value)
                
                min_value = field_schema.get('min_value')
                max_value = field_schema.get('max_value')
                
                if min_value is not None and numeric_value < min_value:
                    return False, f"{field_name} must be at least {min_value}"
                
                if max_value is not None and numeric_value > max_value:
                    return False, f"{field_name} must be at most {max_value}"
                    
            except ValueError:
                return False, f"{field_name} must be a valid number"
        
        # Boolean validation
        if field_type == 'boolean':
            if field_value.lower() not in {'true', 'false', 'yes', 'no', '1', '0'}:
                return False, f"{field_name} must be a boolean value (true/false, yes/no, 1/0)"
        
        # All validations passed
        return True, None

