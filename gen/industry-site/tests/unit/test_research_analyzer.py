"""
Unit tests for the research analyzer.
"""

import pytest
from unittest.mock import Mock, patch
import json
from lib.research.analyzer import (
    ResearchAnalyzer,
    analyze_products,
    categorize_products,
    extract_product_names
)
from lib.errors.exceptions import ResearchError


@pytest.mark.unit
def test_research_analyzer_initialization():
    """Test ResearchAnalyzer initializes correctly."""
    mock_llm = Mock()
    analyzer = ResearchAnalyzer(mock_llm)
    assert analyzer.llm == mock_llm


@pytest.mark.unit
def test_analyze_products_with_mocked_llm():
    """Test product analysis with mocked LLM."""
    # Create mock LLM response
    llm_response = json.dumps([
        {
            "name": "Smart Tractor X1",
            "description": "AI-powered autonomous farming vehicle",
            "category": "Equipment",
            "features": ["GPS guided", "Autonomous operation", "Real-time monitoring"]
        },
        {
            "name": "FarmSense Pro",
            "description": "IoT sensor system for crop monitoring",
            "category": "Software",
            "features": ["Soil monitoring", "Weather integration", "Mobile alerts"]
        }
    ])
    
    mock_llm = Mock()
    mock_llm.chat.return_value = {
        'content': llm_response,
        'model': 'test-model',
        'finish_reason': 'stop',
        'usage': {'total_tokens': 100}
    }
    
    analyzer = ResearchAnalyzer(mock_llm)
    
    sample_content = """
    Our product line includes:
    - Smart Tractor X1: Advanced autonomous farming
    - FarmSense Pro: Comprehensive monitoring solution
    """
    
    products = analyzer.analyze_products(sample_content)
    
    # Verify results
    assert len(products) == 2
    assert products[0]['name'] == 'Smart Tractor X1'
    assert products[1]['name'] == 'FarmSense Pro'
    assert 'description' in products[0]
    assert 'category' in products[0]
    
    # Verify LLM was called
    mock_llm.chat.assert_called_once()


@pytest.mark.unit
def test_extract_product_names():
    """Test basic product name extraction without LLM."""
    content = """
    Our Products:
    - Smart Tractor Model X1
    - Harvester Series Y2
    - Drone Model Z3
    - Irrigation System A4
    
    Each product® is designed for efficiency.
    """
    
    names = extract_product_names(content)
    
    assert isinstance(names, list)
    assert len(names) > 0
    # Should find product-related entries
    assert any('product' in name.lower() or 'model' in name.lower() for name in names)


@pytest.mark.unit
def test_categorize_products():
    """Test product categorization with mocked LLM."""
    category_response = json.dumps({
        "categories": [
            {
                "name": "Heavy Equipment",
                "description": "Large farming machinery",
                "products": ["Tractor X1", "Harvester Y2"]
            },
            {
                "name": "Technology",
                "description": "Software and sensors",
                "products": ["Drone Z3", "Sensor A4"]
            }
        ]
    })
    
    mock_llm = Mock()
    mock_llm.chat.return_value = {
        'content': category_response,
        'model': 'test-model',
        'finish_reason': 'stop',
        'usage': {'total_tokens': 80}
    }
    
    analyzer = ResearchAnalyzer(mock_llm)
    
    products = ["Tractor X1", "Harvester Y2", "Drone Z3", "Sensor A4"]
    categories = analyzer.categorize_products(products, num_categories=2)
    
    # Verify structure
    assert isinstance(categories, dict)
    assert len(categories) >= 2
    assert "Heavy Equipment" in categories
    assert "Technology" in categories
    assert isinstance(categories["Heavy Equipment"], list)
    
    # Verify LLM was called with correct params
    mock_llm.chat.assert_called_once()
    call_args = mock_llm.chat.call_args[0][0]
    assert any('Tractor X1' in msg['content'] for msg in call_args)


@pytest.mark.unit
def test_empty_content_handling():
    """Test that empty content is handled gracefully."""
    mock_llm = Mock()
    analyzer = ResearchAnalyzer(mock_llm)
    
    # Test empty string
    products = analyzer.analyze_products('')
    assert products == []
    
    # Test whitespace only
    products = analyzer.analyze_products('   \n  \t  ')
    assert products == []
    
    # LLM should not be called for empty content
    mock_llm.chat.assert_not_called()


@pytest.mark.unit
def test_empty_products_categorization():
    """Test categorization with empty product list."""
    mock_llm = Mock()
    analyzer = ResearchAnalyzer(mock_llm)
    
    categories = analyzer.categorize_products([])
    assert categories == {}
    
    # LLM should not be called
    mock_llm.chat.assert_not_called()


@pytest.mark.unit
def test_structured_json_output():
    """Test that output format is correct JSON structure."""
    json_response = json.dumps([
        {"name": "Product A", "description": "Description A", "category": "Cat A"},
        {"name": "Product B", "description": "Description B", "category": "Cat B"}
    ])
    
    mock_llm = Mock()
    mock_llm.chat.return_value = {'content': json_response, 'usage': {'total_tokens': 50}}
    
    analyzer = ResearchAnalyzer(mock_llm)
    products = analyzer.analyze_products("Sample content")
    
    # Verify structure
    assert isinstance(products, list)
    assert all(isinstance(p, dict) for p in products)
    assert all('name' in p for p in products)


@pytest.mark.unit
def test_parse_product_response_json():
    """Test parsing JSON response from LLM."""
    analyzer = ResearchAnalyzer(Mock())
    
    json_response = """
    Here are the products:
    [
        {"name": "Product 1", "description": "Desc 1"},
        {"name": "Product 2", "description": "Desc 2"}
    ]
    """
    
    products = analyzer._parse_product_response(json_response)
    
    assert len(products) == 2
    assert products[0]['name'] == 'Product 1'
    assert products[1]['name'] == 'Product 2'


@pytest.mark.unit
def test_parse_product_response_text():
    """Test parsing text response when JSON fails."""
    analyzer = ResearchAnalyzer(Mock())
    
    text_response = """
    Product Name: Tractor X1
    Description: Heavy duty farming tractor
    Category: Equipment
    
    Product Name: Software Suite
    Description: Farm management software
    Category: Software
    """
    
    products = analyzer._parse_product_response(text_response)
    
    assert len(products) >= 2
    # Should find at least some products
    assert any('Tractor' in p.get('name', '') for p in products)


@pytest.mark.unit
def test_parse_category_response_json():
    """Test parsing category JSON response."""
    analyzer = ResearchAnalyzer(Mock())
    
    json_response = """
    {
        "categories": [
            {"name": "Equipment", "products": ["Tractor", "Harvester"]},
            {"name": "Software", "products": ["App A", "App B"]}
        ]
    }
    """
    
    categories = analyzer._parse_category_response(json_response)
    
    assert "Equipment" in categories
    assert "Software" in categories
    assert len(categories["Equipment"]) == 2
    assert "Tractor" in categories["Equipment"]


@pytest.mark.unit
def test_parse_category_response_text():
    """Test parsing category text response."""
    analyzer = ResearchAnalyzer(Mock())
    
    text_response = """
    Equipment:
    - Tractor
    - Harvester
    
    Software:
    - App A
    - App B
    """
    
    categories = analyzer._parse_category_response(text_response)
    
    assert isinstance(categories, dict)
    assert len(categories) >= 2


@pytest.mark.unit
def test_llm_error_handling():
    """Test handling of LLM errors."""
    mock_llm = Mock()
    mock_llm.chat.side_effect = Exception("LLM API Error")
    
    analyzer = ResearchAnalyzer(mock_llm)
    
    with pytest.raises(ResearchError) as exc_info:
        analyzer.analyze_products("Some content")
    
    assert "Failed to analyze products" in str(exc_info.value)


@pytest.mark.unit
def test_categorization_llm_error():
    """Test handling of LLM errors during categorization."""
    mock_llm = Mock()
    mock_llm.chat.side_effect = Exception("LLM API Error")
    
    analyzer = ResearchAnalyzer(mock_llm)
    
    with pytest.raises(ResearchError) as exc_info:
        analyzer.categorize_products(["Product A", "Product B"])
    
    assert "Failed to categorize products" in str(exc_info.value)


@pytest.mark.unit
def test_convenience_analyze_products():
    """Test convenience function for analyzing products."""
    mock_llm = Mock()
    mock_llm.chat.return_value = {
        'content': '[{"name": "Test", "description": "Desc"}]',
        'usage': {'total_tokens': 30}
    }
    
    products = analyze_products("Content", mock_llm)
    
    assert isinstance(products, list)
    mock_llm.chat.assert_called_once()


@pytest.mark.unit
def test_convenience_categorize_products():
    """Test convenience function for categorizing products."""
    mock_llm = Mock()
    mock_llm.chat.return_value = {
        'content': '{"Cat A": ["Prod 1"], "Cat B": ["Prod 2"]}',
        'usage': {'total_tokens': 40}
    }
    
    categories = categorize_products(["Prod 1", "Prod 2"], mock_llm)
    
    assert isinstance(categories, dict)
    mock_llm.chat.assert_called_once()


@pytest.mark.unit
def test_content_truncation():
    """Test that very long content is truncated appropriately."""
    mock_llm = Mock()
    mock_llm.chat.return_value = {'content': '[]', 'usage': {'total_tokens': 10}}
    
    analyzer = ResearchAnalyzer(mock_llm)
    
    # Create very long content
    long_content = "Product: " + "A" * 10000
    analyzer.analyze_products(long_content)
    
    # Verify LLM was called
    mock_llm.chat.assert_called_once()
    call_args = mock_llm.chat.call_args[0][0]
    
    # Content should be truncated in the prompt
    user_message = next(msg['content'] for msg in call_args if msg['role'] == 'user')
    # The truncated content should be much shorter
    assert len(user_message) < len(long_content)


@pytest.mark.unit
def test_extract_product_names_with_empty_content():
    """Test product name extraction with empty content."""
    names = extract_product_names('')
    assert names == []
    
    names = extract_product_names(None)
    assert names == []


@pytest.mark.unit
def test_extract_product_names_limits_results():
    """Test that product name extraction limits results."""
    # Create content with many products
    content = '\n'.join([f'Product® Model-{i}' for i in range(200)])
    
    names = extract_product_names(content)
    
    # Should be limited to 100
    assert len(names) <= 100


@pytest.mark.llm
def test_analyze_products_real_llm():
    """
    Integration test with real LLM.
    Run with: pytest tests/unit/test_research_analyzer.py -v -m llm
    """
    import os
    from lib.llm.client import LLMClient
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not found")
    
    llm = LLMClient(api_key=api_key, default_model='anthropic/claude-haiku-4.5')
    analyzer = ResearchAnalyzer(llm)
    
    sample_content = """
    Our agricultural products include:
    - Smart Tractor X1: GPS-guided autonomous tractor
    - HarvestMaster Pro: Advanced combine harvester
    - FarmSense: IoT sensor network for crop monitoring
    """
    
    products = analyzer.analyze_products(sample_content, "AgriTech Corp")
    
    assert len(products) > 0
    assert isinstance(products, list)
    # Should extract at least some product names
    assert any('tractor' in p.get('name', '').lower() for p in products)
