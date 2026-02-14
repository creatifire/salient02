"""Configuration validation functions."""

from typing import Dict, Any, List
from ..errors.exceptions import ConfigValidationError


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate site-gen-config.yaml structure.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigValidationError: If configuration is invalid
        
    Validates:
        - Required top-level sections exist
        - Company information is complete
        - LLM configuration is valid
        - Generation parameters are reasonable
    """
    errors: List[str] = []
    
    # Check required top-level sections
    required_sections = ['company', 'llm', 'generation']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate company section
    if 'company' in config:
        company = config['company']
        required_company_fields = ['name', 'industry', 'description']
        for field in required_company_fields:
            if field not in company or not company[field]:
                errors.append(f"Missing or empty company.{field}")
    
    # Validate LLM section
    if 'llm' in config:
        llm = config['llm']
        
        if 'api_key' not in llm or not llm['api_key']:
            errors.append("Missing or empty llm.api_key")
        
        if 'models' in llm:
            models = llm['models']
            if 'tool_calling' not in models or not models['tool_calling']:
                errors.append("Missing or empty llm.models.tool_calling")
            if 'no_tools' not in models or not models['no_tools']:
                errors.append("Missing or empty llm.models.no_tools")
        else:
            errors.append("Missing llm.models section")
    
    # Validate generation section
    if 'generation' in config:
        gen = config['generation']
        
        # Validate product_count
        if 'product_count' in gen:
            product_count = gen['product_count']
            if not isinstance(product_count, int) or product_count < 1:
                errors.append("generation.product_count must be a positive integer")
            if product_count > 1000:
                errors.append("generation.product_count exceeds maximum of 1000")
        
        # Validate category_count
        if 'category_count' in gen:
            category_count = gen['category_count']
            if not isinstance(category_count, int) or category_count < 1:
                errors.append("generation.category_count must be a positive integer")
            if category_count > 50:
                errors.append("generation.category_count exceeds maximum of 50")
        
        # Validate product_relationships
        if 'product_relationships' in gen:
            relationships = gen['product_relationships']
            if not isinstance(relationships, dict):
                errors.append("generation.product_relationships must be a dictionary")
            else:
                if 'min' in relationships:
                    min_rel = relationships['min']
                    if not isinstance(min_rel, int) or min_rel < 0:
                        errors.append("generation.product_relationships.min must be non-negative integer")
                
                if 'max' in relationships:
                    max_rel = relationships['max']
                    if not isinstance(max_rel, int) or max_rel < 0:
                        errors.append("generation.product_relationships.max must be non-negative integer")
                
                if 'min' in relationships and 'max' in relationships:
                    if relationships['max'] < relationships['min']:
                        errors.append("generation.product_relationships.max must be >= min")
    
    # Raise exception if any errors found
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ConfigValidationError(error_msg)


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str],
    context: str = ""
) -> List[str]:
    """
    Validate that required fields are present and non-empty.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context string for error messages (e.g., "company")
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    prefix = f"{context}." if context else ""
    
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing or empty {prefix}{field}")
    
    return errors
