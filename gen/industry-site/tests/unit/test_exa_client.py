"""
Unit tests for the Exa search client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lib.research.exa_client import ExaClient, search_companies, search_products
from lib.errors.exceptions import ResearchError


@pytest.mark.unit
def test_exa_client_initialization():
    """Test ExaClient initializes with valid API key."""
    with patch('lib.research.exa_client.Exa') as mock_exa:
        client = ExaClient(api_key='test-key')
        mock_exa.assert_called_once_with('test-key')
        assert client.client is not None


@pytest.mark.unit
def test_exa_client_requires_api_key():
    """Test ExaClient raises error without API key."""
    with pytest.raises(ResearchError) as exc_info:
        ExaClient(api_key='')
    assert 'API key is required' in str(exc_info.value)


@pytest.mark.unit
def test_exa_client_initialization_failure():
    """Test ExaClient handles initialization failures."""
    with patch('lib.research.exa_client.Exa', side_effect=Exception('API Error')):
        with pytest.raises(ResearchError) as exc_info:
            ExaClient(api_key='test-key')
        assert 'Failed to initialize' in str(exc_info.value)


@pytest.mark.unit
def test_search_companies_mocked(mocker):
    """Test search_companies with mocked API response."""
    # Create mock result objects
    mock_result1 = Mock()
    mock_result1.title = "AgriTech Solutions | Leading Farm Technology"
    mock_result1.url = "https://agritech.example.com"
    mock_result1.text = "AgriTech Solutions provides precision farming tools."
    
    mock_result2 = Mock()
    mock_result2.title = "FarmTech Corp - Innovative Agricultural Solutions"
    mock_result2.url = "https://farmtech.example.com"
    mock_result2.text = "FarmTech Corp specializes in smart irrigation systems."
    
    # Create mock search response
    mock_response = Mock()
    mock_response.results = [mock_result1, mock_result2]
    
    # Patch the Exa client
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        # Test the search
        client = ExaClient(api_key='test-key')
        results = client.search_companies('agtech', num_results=10)
        
        # Verify results
        assert len(results) == 2
        assert results[0]['name'] == 'AgriTech Solutions'
        assert results[0]['url'] == 'https://agritech.example.com'
        assert 'precision farming' in results[0]['description']
        
        assert results[1]['name'] == 'FarmTech Corp'
        assert results[1]['url'] == 'https://farmtech.example.com'
        
        # Verify API was called correctly
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        assert 'agtech' in call_args[0][0].lower()
        assert call_args[1]['num_results'] == 10


@pytest.mark.unit
def test_search_companies_with_focus_areas(mocker):
    """Test search_companies includes focus areas in query."""
    mock_response = Mock()
    mock_response.results = []
    
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        client = ExaClient(api_key='test-key')
        client.search_companies('agtech', focus_areas='precision agriculture')
        
        # Verify query includes focus areas
        call_args = mock_client.search.call_args[0][0]
        assert 'precision agriculture' in call_args


@pytest.mark.unit
def test_search_companies_error_handling():
    """Test search_companies handles API errors gracefully."""
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.side_effect = Exception('API rate limit exceeded')
        mock_exa.return_value = mock_client
        
        client = ExaClient(api_key='test-key')
        
        with pytest.raises(ResearchError) as exc_info:
            client.search_companies('agtech')
        
        assert 'Failed to search companies' in str(exc_info.value)


@pytest.mark.unit
def test_result_structure():
    """Test that results have all required fields."""
    mock_result = Mock()
    mock_result.title = "Test Company"
    mock_result.url = "https://test.com"
    mock_result.text = "Test description"
    
    mock_response = Mock()
    mock_response.results = [mock_result]
    
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        client = ExaClient(api_key='test-key')
        results = client.search_companies('test')
        
        # Verify structure
        assert len(results) == 1
        result = results[0]
        assert 'name' in result
        assert 'url' in result
        assert 'title' in result
        assert 'description' in result
        
        assert isinstance(result['name'], str)
        assert isinstance(result['url'], str)
        assert isinstance(result['title'], str)
        assert isinstance(result['description'], str)


@pytest.mark.unit
def test_search_products_mocked():
    """Test search_products with mocked API response."""
    mock_result = Mock()
    mock_result.title = "Agricultural Equipment Catalog"
    mock_result.url = "https://example.com/products"
    mock_result.text = "Tractors, harvesters, and irrigation systems available."
    
    mock_response = Mock()
    mock_response.results = [mock_result]
    
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        client = ExaClient(api_key='test-key')
        results = client.search_products('agtech', num_results=5)
        
        assert len(results) == 1
        assert results[0]['source'] == 'https://example.com/products'
        assert 'Tractors' in results[0]['content']


@pytest.mark.unit
def test_search_products_with_company_name():
    """Test search_products includes company name in query."""
    mock_response = Mock()
    mock_response.results = []
    
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        client = ExaClient(api_key='test-key')
        client.search_products('agtech', company_name='AgriTech')
        
        call_args = mock_client.search.call_args[0][0]
        assert 'AgriTech' in call_args
        assert 'agtech' in call_args.lower()


@pytest.mark.unit
def test_convenience_search_companies():
    """Test convenience function search_companies."""
    mock_response = Mock()
    mock_response.results = []
    
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        results = search_companies('fintech', 'test-key', num_results=15)
        
        assert isinstance(results, list)
        mock_client.search.assert_called_once()


@pytest.mark.unit
def test_convenience_search_products():
    """Test convenience function search_products."""
    mock_response = Mock()
    mock_response.results = []
    
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        results = search_products('fintech', 'test-key')
        
        assert isinstance(results, list)
        mock_client.search.assert_called_once()


@pytest.mark.unit
def test_extract_company_name():
    """Test company name extraction from titles."""
    test_cases = [
        ("AgriTech Solutions | Home", "AgriTech Solutions"),
        ("FarmTech Corp - Official Website", "FarmTech Corp"),
        ("AgTech Inc | Leading Provider", "AgTech Inc"),
        ("Simple Name", "Simple Name"),
    ]
    
    for title, expected in test_cases:
        result = ExaClient._extract_company_name(title)
        assert result == expected, f"Failed for title: {title}"


@pytest.mark.unit
def test_result_without_text_attribute():
    """Test handling of results without text attribute."""
    mock_result = Mock(spec=['title', 'url'])  # No 'text' attribute
    mock_result.title = "Test Company"
    mock_result.url = "https://test.com"
    
    mock_response = Mock()
    mock_response.results = [mock_result]
    
    with patch('lib.research.exa_client.Exa') as mock_exa:
        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_exa.return_value = mock_client
        
        client = ExaClient(api_key='test-key')
        results = client.search_companies('test')
        
        # Should handle missing text gracefully
        assert len(results) == 1
        assert results[0]['description'] == ''


@pytest.mark.llm
def test_search_companies_real_api():
    """
    Integration test with real Exa API.
    Run with: pytest tests/unit/test_exa_client.py -v -m llm
    Requires EXA_API_KEY environment variable.
    """
    import os
    api_key = os.getenv('EXA_API_KEY')
    
    if not api_key:
        pytest.skip("EXA_API_KEY not found")
    
    client = ExaClient(api_key)
    results = client.search_companies('agtech', num_results=5)
    
    assert len(results) > 0
    assert len(results) <= 5
    
    for result in results:
        assert 'name' in result
        assert 'url' in result
        assert result['url'].startswith('http')
