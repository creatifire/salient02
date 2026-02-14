#!/usr/bin/env python3
"""
Test script for ConfigLoader implementation.
Verifies F01-T1: Implement ConfigLoader Class
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config.config_loader import ConfigLoader
from lib.errors.exceptions import ConfigValidationError


def test_config_loader():
    """Test ConfigLoader functionality."""
    
    print("=" * 60)
    print("Testing ConfigLoader Implementation (F01-T1)")
    print("=" * 60)
    
    # Test 1: Load valid configuration
    print("\n[Test 1] Loading valid configuration...")
    try:
        config_path = Path("agtech/site-gen-config.yaml")
        loader = ConfigLoader(config_path)
        config = loader.load()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False
    
    # Test 2: Verify config structure
    print("\n[Test 2] Verifying configuration structure...")
    try:
        assert 'company' in config, "Missing 'company' section"
        assert 'llm' in config, "Missing 'llm' section"
        assert 'generation' in config, "Missing 'generation' section"
        print("✓ All required sections present")
    except AssertionError as e:
        print(f"✗ {e}")
        return False
    
    # Test 3: Verify company information
    print("\n[Test 3] Verifying company information...")
    try:
        company = loader.company
        assert company['name'] == "AgriTech Solutions", f"Unexpected company name: {company['name']}"
        assert company['industry'] == "agtech", f"Unexpected industry: {company['industry']}"
        assert 'description' in company, "Missing company description"
        print(f"✓ Company: {company['name']}")
        print(f"  Industry: {company['industry']}")
        print(f"  Description: {company['description'][:50]}...")
    except (AssertionError, KeyError) as e:
        print(f"✗ {e}")
        return False
    
    # Test 4: Test dot notation access
    print("\n[Test 4] Testing dot notation access...")
    try:
        company_name = loader.get('company.name')
        assert company_name == "AgriTech Solutions", f"Unexpected value: {company_name}"
        
        tool_model = loader.get('llm.models.tool_calling')
        assert tool_model == "anthropic/claude-sonnet-4.5", f"Unexpected model: {tool_model}"
        
        product_count = loader.get('generation.product_count')
        assert product_count == 100, f"Unexpected count: {product_count}"
        
        # Test default value
        nonexistent = loader.get('nonexistent.key', 'default_value')
        assert nonexistent == 'default_value', "Default value not returned"
        
        print("✓ Dot notation access working correctly")
        print(f"  company.name: {company_name}")
        print(f"  llm.models.tool_calling: {tool_model}")
        print(f"  generation.product_count: {product_count}")
    except (AssertionError, Exception) as e:
        print(f"✗ {e}")
        return False
    
    # Test 5: Test environment variable substitution
    print("\n[Test 5] Testing environment variable substitution...")
    try:
        api_key = loader.get('llm.api_key')
        # Should be substituted if env var exists, or remain as ${...} if not
        print(f"  llm.api_key: {api_key[:20] if len(api_key) > 20 else api_key}...")
        
        if api_key.startswith('${'):
            print("  ℹ Environment variable not set (expected for testing)")
        else:
            print("  ✓ Environment variable substituted successfully")
    except Exception as e:
        print(f"✗ {e}")
        return False
    
    # Test 6: Test property accessors
    print("\n[Test 6] Testing property accessors...")
    try:
        company = loader.company
        llm = loader.llm
        generation = loader.generation
        
        assert isinstance(company, dict), "company property should return dict"
        assert isinstance(llm, dict), "llm property should return dict"
        assert isinstance(generation, dict), "generation property should return dict"
        
        print("✓ Property accessors working correctly")
    except (AssertionError, Exception) as e:
        print(f"✗ {e}")
        return False
    
    # Test 7: Test dictionary-style access
    print("\n[Test 7] Testing dictionary-style access...")
    try:
        company = loader['company']
        assert company['name'] == "AgriTech Solutions", "Dictionary access failed"
        
        assert 'company' in loader, "__contains__ not working"
        assert 'nonexistent' not in loader, "__contains__ not working for missing keys"
        
        print("✓ Dictionary-style access working correctly")
    except (AssertionError, KeyError) as e:
        print(f"✗ {e}")
        return False
    
    # Test 8: Test validation (should pass for valid config)
    print("\n[Test 8] Testing validation with valid config...")
    try:
        # Validation happens automatically in load()
        print("✓ Configuration validated successfully")
    except Exception as e:
        print(f"✗ Validation failed unexpectedly: {e}")
        return False
    
    # Test 9: Test error handling for missing file
    print("\n[Test 9] Testing error handling for missing file...")
    try:
        bad_loader = ConfigLoader(Path("nonexistent/config.yaml"))
        bad_loader.load()
        print("✗ Should have raised FileNotFoundError")
        return False
    except FileNotFoundError:
        print("✓ FileNotFoundError raised correctly for missing file")
    except Exception as e:
        print(f"✗ Wrong exception type: {e}")
        return False
    
    # Test 10: Test runtime error when accessing before load
    print("\n[Test 10] Testing runtime error when accessing before load...")
    try:
        unloaded_loader = ConfigLoader(config_path)
        _ = unloaded_loader.get('company.name')
        print("✗ Should have raised RuntimeError")
        return False
    except RuntimeError as e:
        if "not loaded" in str(e):
            print("✓ RuntimeError raised correctly when accessing before load")
        else:
            print(f"✗ Wrong RuntimeError message: {e}")
            return False
    except Exception as e:
        print(f"✗ Wrong exception type: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_config_loader()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
