# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Unit tests for ProfileSchemaLoader.

Tests profile schema loading, validation, prompt generation, and field value validation.
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from app.services.profile_schema_loader import ProfileSchemaLoader


class TestLoadSchema:
    """Tests for ProfileSchemaLoader.load_schema()"""
    
    def test_load_schema_instance_level(self, tmp_path):
        """Load from agent instance folder (highest priority)."""
        # Create test directory structure
        config_dir = tmp_path / "config" / "agent_configs" / "wyckoff" / "wyckoff_info_chat1"
        config_dir.mkdir(parents=True)
        
        # Create test profile.yaml
        schema_content = {
            'profile_version': '1.0',
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    'description': 'Email address',
                    'validation': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    'examples': ['user@example.com'],
                    'semantic_hints': 'Capture when user provides contact info'
                }
            }
        }
        
        with open(config_dir / "profile.yaml", 'w') as f:
            yaml.dump(schema_content, f)
        
        # Mock the Path to point to our tmp_path
        with patch('app.services.profile_schema_loader.Path') as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            
            schema = ProfileSchemaLoader.load_schema('wyckoff', 'wyckoff_info_chat1')
            
            assert schema is not None
            assert schema['profile_version'] == '1.0'
            assert 'email' in schema['fields']
    
    def test_load_schema_system_fallback(self, tmp_path):
        """Fall back to system default when instance file missing."""
        # Create system default directory
        system_dir = tmp_path / "config" / "prompt_modules" / "system"
        system_dir.mkdir(parents=True)
        
        # Create system default profile.yaml
        schema_content = {
            'profile_version': '1.0-system',
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    'description': 'Email address',
                    'validation': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    'examples': ['user@example.com'],
                    'semantic_hints': 'Capture email'
                }
            }
        }
        
        with open(system_dir / "profile.yaml", 'w') as f:
            yaml.dump(schema_content, f)
        
        # Mock the Path to point to our tmp_path
        with patch('app.services.profile_schema_loader.Path') as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            
            schema = ProfileSchemaLoader.load_schema('nonexistent', 'nonexistent_agent')
            
            assert schema is not None
            assert schema['profile_version'] == '1.0-system'
    
    def test_load_schema_missing_both(self, tmp_path):
        """Returns None when both instance and system files missing."""
        # Mock the Path to point to our tmp_path (no files created)
        with patch('app.services.profile_schema_loader.Path') as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            
            schema = ProfileSchemaLoader.load_schema('missing', 'missing_agent')
            
            assert schema is None


class TestValidateSchema:
    """Tests for ProfileSchemaLoader.validate_schema()"""
    
    def test_validate_schema_valid(self):
        """Valid schema passes validation."""
        schema = {
            'profile_version': '1.0',
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    'description': 'Email address',
                    'validation': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    'examples': ['user@example.com'],
                    'semantic_hints': 'Capture when user provides contact'
                },
                'phone': {
                    'type': 'phone',
                    'required': False,
                    'description': 'Phone number',
                    'validation': r'^\+?[1-9]\d{1,14}$',
                    'examples': ['+1234567890'],
                    'semantic_hints': 'Capture phone if mentioned'
                }
            }
        }
        
        is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_schema_missing_fields(self):
        """Detect missing required metadata."""
        schema = {
            'profile_version': '1.0',
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    # Missing: description, validation, examples, semantic_hints
                }
            }
        }
        
        is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
        
        assert not is_valid
        assert len(errors) > 0
        assert any('missing required metadata' in err for err in errors)
    
    def test_validate_schema_invalid_field_type(self):
        """Reject invalid field types."""
        schema = {
            'profile_version': '1.0',
            'fields': {
                'custom_field': {
                    'type': 'invalid_type',  # Not in VALID_FIELD_TYPES
                    'required': True,
                    'description': 'Some field',
                    'examples': ['example'],
                    'semantic_hints': 'Capture this'
                }
            }
        }
        
        is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
        
        assert not is_valid
        assert any('invalid type' in err.lower() for err in errors)
    
    def test_validate_schema_invalid_regex(self):
        """Detect malformed regex patterns."""
        schema = {
            'profile_version': '1.0',
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    'description': 'Email',
                    'validation': '[invalid regex(',  # Malformed regex
                    'examples': ['test@test.com'],
                    'semantic_hints': 'Capture email'
                }
            }
        }
        
        is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
        
        assert not is_valid
        assert any('invalid regex' in err.lower() for err in errors)
    
    def test_validate_schema_missing_validation_for_email(self):
        """Email type requires validation regex."""
        schema = {
            'profile_version': '1.0',
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    'description': 'Email',
                    # Missing: validation (required for email type)
                    'examples': ['test@test.com'],
                    'semantic_hints': 'Capture email'
                }
            }
        }
        
        is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
        
        assert not is_valid
        assert any('requires \'validation\' regex pattern' in err for err in errors)
    
    def test_validate_schema_missing_enum_values(self):
        """Enum type requires enum_values list."""
        schema = {
            'profile_version': '1.0',
            'fields': {
                'relationship': {
                    'type': 'enum',
                    'required': True,
                    'description': 'Relationship to patient',
                    # Missing: enum_values (required for enum type)
                    'examples': ['self'],
                    'semantic_hints': 'Ask relationship'
                }
            }
        }
        
        is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
        
        assert not is_valid
        assert any('requires \'enum_values\' list' in err for err in errors)
    
    def test_validate_schema_missing_profile_version(self):
        """Missing profile_version key."""
        schema = {
            # Missing: profile_version
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    'description': 'Email',
                    'validation': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    'examples': ['test@test.com'],
                    'semantic_hints': 'Capture email'
                }
            }
        }
        
        is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
        
        assert not is_valid
        assert any('profile_version' in err for err in errors)


class TestGeneratePromptModule:
    """Tests for ProfileSchemaLoader.generate_prompt_module()"""
    
    def test_generate_prompt_module(self):
        """Generate valid markdown content from schema."""
        schema = {
            'profile_version': '1.0',
            'fields': {
                'email': {
                    'type': 'email',
                    'required': True,
                    'description': 'Email address for contact',
                    'validation': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    'examples': ['user@example.com', 'test@test.com'],
                    'semantic_hints': 'Capture when user mentions email or wants follow-up'
                },
                'phone': {
                    'type': 'phone',
                    'required': False,
                    'description': 'Phone number',
                    'validation': r'^\+?[1-9]\d{1,14}$',
                    'examples': ['+1234567890'],
                    'semantic_hints': 'Capture if user prefers phone contact'
                }
            },
            'capture_hints': {
                'timing': 'Ask for contact info near end of conversation',
                'approach': 'Frame as "staying in touch" or "sending summary"'
            }
        }
        
        markdown = ProfileSchemaLoader.generate_prompt_module(schema)
        
        # Verify structure
        assert '# Profile Capture Guidelines' in markdown
        assert 'Profile Schema Version: 1.0' in markdown
        assert '## Required Profile Fields' in markdown
        assert '## Optional Profile Fields' in markdown
        assert '## Capture Guidelines' in markdown
        assert '## Additional Capture Hints' in markdown
        
        # Verify field content
        assert 'email' in markdown.lower()
        assert 'phone' in markdown.lower()
        assert 'Email address for contact' in markdown
        assert 'Capture when user mentions email' in markdown
        
        # Verify examples
        assert 'user@example.com' in markdown
        
        # Verify capture hints
        assert 'staying in touch' in markdown
    
    def test_generate_prompt_module_empty_fields(self):
        """Handle schema with no fields."""
        schema = {
            'profile_version': '1.0',
            'fields': {}
        }
        
        markdown = ProfileSchemaLoader.generate_prompt_module(schema)
        
        assert '# Profile Capture Guidelines' in markdown
        assert '*No fields defined in schema*' in markdown


class TestValidateFieldValue:
    """Tests for ProfileSchemaLoader.validate_field_value()"""
    
    def test_validate_field_value_email(self):
        """Test email validation."""
        field_schema = {
            'type': 'email',
            'validation': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        }
        
        # Valid email
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'email', 'user@example.com', field_schema
        )
        assert is_valid
        assert error is None
        
        # Invalid email
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'email', 'invalid-email', field_schema
        )
        assert not is_valid
        assert error is not None
        assert 'invalid format' in error.lower()
    
    def test_validate_field_value_phone(self):
        """Test phone validation."""
        field_schema = {
            'type': 'phone',
            'validation': r'^\+?[1-9]\d{1,14}$'
        }
        
        # Valid phone
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'phone', '+1234567890', field_schema
        )
        assert is_valid
        assert error is None
        
        # Invalid phone
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'phone', 'abc-def-ghij', field_schema
        )
        assert not is_valid
        assert error is not None
    
    def test_validate_field_value_enum(self):
        """Test enum validation."""
        field_schema = {
            'type': 'enum',
            'enum_values': ['self', 'parent', 'spouse', 'child', 'other']
        }
        
        # Valid enum value
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'relationship', 'parent', field_schema
        )
        assert is_valid
        assert error is None
        
        # Invalid enum value
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'relationship', 'invalid', field_schema
        )
        assert not is_valid
        assert 'must be one of' in error.lower()
    
    def test_validate_field_value_string_length(self):
        """Test string length constraints."""
        field_schema = {
            'type': 'string',
            'min_length': 3,
            'max_length': 50
        }
        
        # Valid length
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'name', 'John Doe', field_schema
        )
        assert is_valid
        assert error is None
        
        # Too short
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'name', 'AB', field_schema
        )
        assert not is_valid
        assert 'at least 3 characters' in error
        
        # Too long
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'name', 'A' * 51, field_schema
        )
        assert not is_valid
        assert 'at most 50 characters' in error
    
    def test_validate_field_value_number_range(self):
        """Test numeric value constraints."""
        field_schema = {
            'type': 'number',
            'min_value': 0,
            'max_value': 100
        }
        
        # Valid number
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'age', '25', field_schema
        )
        assert is_valid
        assert error is None
        
        # Too small
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'age', '-5', field_schema
        )
        assert not is_valid
        assert 'at least 0' in error
        
        # Too large
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'age', '150', field_schema
        )
        assert not is_valid
        assert 'at most 100' in error
        
        # Not a number
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'age', 'not-a-number', field_schema
        )
        assert not is_valid
        assert 'valid number' in error.lower()
    
    def test_validate_field_value_boolean(self):
        """Test boolean validation."""
        field_schema = {
            'type': 'boolean'
        }
        
        # Valid boolean values
        for value in ['true', 'false', 'yes', 'no', '1', '0', 'True', 'FALSE']:
            is_valid, error = ProfileSchemaLoader.validate_field_value(
                'consent', value, field_schema
            )
            assert is_valid, f"Expected '{value}' to be valid boolean"
            assert error is None
        
        # Invalid boolean
        is_valid, error = ProfileSchemaLoader.validate_field_value(
            'consent', 'maybe', field_schema
        )
        assert not is_valid
        assert 'boolean value' in error.lower()


class TestMalformedYAMLLogging:
    """Tests for Logfire error logging with malformed YAML."""
    
    @patch('app.services.profile_schema_loader.logfire')
    def test_malformed_yaml_logging(self, mock_logfire, tmp_path):
        """Verify Logfire error logging for malformed YAML."""
        # Create test directory
        config_dir = tmp_path / "config" / "agent_configs" / "test" / "test_agent"
        config_dir.mkdir(parents=True)
        
        # Create malformed YAML
        with open(config_dir / "profile.yaml", 'w') as f:
            f.write("invalid: yaml: content:\n  - bad indentation\n wrong")
        
        # Mock the Path to point to our tmp_path
        with patch('app.services.profile_schema_loader.Path') as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            
            schema = ProfileSchemaLoader.load_schema('test', 'test_agent')
            
            # Should return None
            assert schema is None
            
            # Verify Logfire error was called
            assert mock_logfire.error.called
            call_args = mock_logfire.error.call_args
            assert 'service.profile_schema_loader.yaml_error' in call_args[0]
            assert 'source' in call_args[1]
            assert 'error' in call_args[1]


class TestFieldTypes:
    """Test all field type validations work correctly."""
    
    def test_all_valid_field_types_accepted(self):
        """All defined field types should be accepted."""
        valid_types = ProfileSchemaLoader.VALID_FIELD_TYPES
        
        for field_type in valid_types:
            schema = {
                'profile_version': '1.0',
                'fields': {
                    'test_field': {
                        'type': field_type,
                        'required': True,
                        'description': f'Test {field_type} field',
                        'examples': ['example'],
                        'semantic_hints': 'Test hint'
                    }
                }
            }
            
            # Add conditional requirements
            if field_type in ProfileSchemaLoader.REQUIRES_VALIDATION:
                schema['fields']['test_field']['validation'] = r'^.*$'
            
            if field_type in ProfileSchemaLoader.REQUIRES_ENUM_VALUES:
                schema['fields']['test_field']['enum_values'] = ['value1', 'value2']
            
            is_valid, errors = ProfileSchemaLoader.validate_schema(schema)
            assert is_valid, f"Field type '{field_type}' should be valid. Errors: {errors}"

