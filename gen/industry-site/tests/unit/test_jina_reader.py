"""
Unit tests for the Jina Reader client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from lib.research.jina_reader import JinaReader, scrape_url, scrape_multiple_urls
from lib.errors.exceptions import ResearchError


@pytest.mark.unit
def test_jina_reader_initialization():
    """Test JinaReader initializes correctly."""
    # Without API key
    reader = JinaReader()
    assert reader.api_key is None
    assert reader.timeout == 30
    
    # With API key
    reader = JinaReader(api_key='test-key', timeout=60)
    assert reader.api_key == 'test-key'
    assert reader.timeout == 60


@pytest.mark.unit
def test_build_headers_without_api_key():
    """Test headers are built correctly without API key."""
    reader = JinaReader()
    headers = reader._build_headers()
    
    assert 'User-Agent' in headers
    assert 'Accept' in headers
    assert 'Authorization' not in headers


@pytest.mark.unit
def test_build_headers_with_api_key():
    """Test headers include authorization when API key provided."""
    reader = JinaReader(api_key='test-key-123')
    headers = reader._build_headers()
    
    assert 'Authorization' in headers
    assert headers['Authorization'] == 'Bearer test-key-123'


@pytest.mark.unit
def test_scrape_url_mocked():
    """Test scraping URL with mocked response."""
    mock_content = """# Product Catalog

## Featured Products

- **Smart Sensor** - IoT device for monitoring
- **Control System** - Automated control platform
- **Analytics Dashboard** - Real-time data visualization

Contact us for more information."""
    
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        reader = JinaReader()
        content = reader.scrape_url('https://example.com/products')
        
        assert len(content) > 0
        assert 'Product Catalog' in content
        assert 'Smart Sensor' in content
        assert 'IoT device' in content
        
        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'https://r.jina.ai/https://example.com/products' in call_args[0][0]


@pytest.mark.unit
def test_clean_markdown_output():
    """Test that output is clean markdown without HTML tags."""
    mock_content = """# Clean Markdown

This is **bold** and this is *italic*.

- List item 1
- List item 2

No HTML tags here."""
    
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        reader = JinaReader()
        content = reader.scrape_url('https://example.com')
        
        # Should not contain HTML tags
        assert '<html>' not in content.lower()
        assert '<div>' not in content.lower()
        assert '<p>' not in content.lower()
        assert '<script>' not in content.lower()
        
        # Should contain markdown
        assert '#' in content or '**' in content or '*' in content


@pytest.mark.unit
def test_invalid_url_handling():
    """Test handling of invalid URLs."""
    reader = JinaReader()
    
    # Test empty URL
    with pytest.raises(ResearchError) as exc_info:
        reader.scrape_url('')
    assert 'required' in str(exc_info.value).lower()
    
    # Test invalid URL format (no protocol)
    with pytest.raises(ResearchError) as exc_info:
        reader.scrape_url('example.com')
    assert 'Invalid URL format' in str(exc_info.value)
    
    # Test invalid URL format
    with pytest.raises(ResearchError) as exc_info:
        reader.scrape_url('not-a-url')
    assert 'Invalid URL format' in str(exc_info.value)


@pytest.mark.unit
def test_empty_content_handling():
    """Test handling of empty page content."""
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = ''
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        reader = JinaReader()
        content = reader.scrape_url('https://example.com/empty')
        
        # Should handle empty content gracefully
        assert content == ''


@pytest.mark.unit
def test_request_timeout_handling():
    """Test handling of request timeouts."""
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout('Request timed out')
        
        reader = JinaReader(timeout=5)
        
        with pytest.raises(ResearchError) as exc_info:
            reader.scrape_url('https://slow-site.com')
        
        # Error message contains info about the timeout
        assert 'scraping' in str(exc_info.value).lower()
        assert 'slow-site.com' in str(exc_info.value)


@pytest.mark.unit
def test_request_error_handling():
    """Test handling of HTTP request errors."""
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException('Connection error')
        
        reader = JinaReader()
        
        with pytest.raises(ResearchError) as exc_info:
            reader.scrape_url('https://bad-site.com')
        
        # Error message contains info about the failure
        assert 'scraping' in str(exc_info.value).lower()
        assert 'bad-site.com' in str(exc_info.value)


@pytest.mark.unit
def test_scrape_multiple_urls():
    """Test scraping multiple URLs."""
    mock_content_1 = "# Page 1\n\nContent from page 1."
    mock_content_2 = "# Page 2\n\nContent from page 2."
    
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response_1 = Mock()
        mock_response_1.text = mock_content_1
        mock_response_1.raise_for_status = Mock()
        
        mock_response_2 = Mock()
        mock_response_2.text = mock_content_2
        mock_response_2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response_1, mock_response_2]
        
        reader = JinaReader()
        results = reader.scrape_multiple([
            'https://example.com/page1',
            'https://example.com/page2'
        ])
        
        assert len(results) == 2
        assert 'https://example.com/page1' in results
        assert 'https://example.com/page2' in results
        assert 'Page 1' in results['https://example.com/page1']
        assert 'Page 2' in results['https://example.com/page2']


@pytest.mark.unit
def test_scrape_multiple_with_failures():
    """Test scraping multiple URLs handles individual failures."""
    mock_content = "# Success Page"
    
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_success = Mock()
        mock_success.text = mock_content
        mock_success.raise_for_status = Mock()
        
        # First succeeds, second fails
        mock_get.side_effect = [
            mock_success,
            requests.exceptions.RequestException('Failed')
        ]
        
        reader = JinaReader()
        results = reader.scrape_multiple([
            'https://example.com/success',
            'https://example.com/fail'
        ])
        
        # Should have both entries
        assert len(results) == 2
        assert results['https://example.com/success'] is not None
        assert results['https://example.com/fail'] is None


@pytest.mark.unit
def test_clean_content_removes_excessive_whitespace():
    """Test content cleaning removes excessive blank lines."""
    content_with_blanks = """# Title


Line 1



Line 2




Line 3"""
    
    reader = JinaReader()
    cleaned = reader._clean_content(content_with_blanks)
    
    # Should reduce multiple blank lines
    assert '\n\n\n\n' not in cleaned
    # Should keep some structure
    assert '\n\n' in cleaned


@pytest.mark.unit
def test_extract_text_snippet():
    """Test extracting text snippet from scraped content."""
    mock_content = """# Products

**Featured Item**: Smart Sensor for agriculture monitoring.

This is a long description that goes on and on with lots of details about the product."""
    
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        reader = JinaReader()
        snippet = reader.extract_text_snippet('https://example.com', max_length=50)
        
        assert len(snippet) <= 53  # 50 + '...'
        assert '...' in snippet
        # Should remove markdown formatting
        assert '#' not in snippet
        assert '**' not in snippet


@pytest.mark.unit
def test_convenience_scrape_url():
    """Test convenience function for single URL."""
    mock_content = "# Test Page"
    
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = scrape_url('https://example.com')
        
        assert 'Test Page' in content


@pytest.mark.unit
def test_convenience_scrape_multiple():
    """Test convenience function for multiple URLs."""
    mock_content = "# Test"
    
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = scrape_multiple_urls(['https://example.com'])
        
        assert isinstance(results, dict)
        assert len(results) == 1


@pytest.mark.unit
def test_jina_url_construction():
    """Test that Jina API URL is constructed correctly."""
    with patch('lib.research.jina_reader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        reader = JinaReader()
        reader.scrape_url('https://example.com/page')
        
        # Verify the Jina URL was constructed correctly
        call_args = mock_get.call_args[0][0]
        assert call_args == 'https://r.jina.ai/https://example.com/page'


@pytest.mark.llm
def test_scrape_url_real_api():
    """
    Integration test with real Jina Reader API (free tier).
    Run with: pytest tests/unit/test_jina_reader.py -v -m llm
    """
    import os
    api_key = os.getenv('JINA_API_KEY')  # Optional - free tier works without
    
    reader = JinaReader(api_key=api_key, timeout=30)
    
    # Test with a well-known, stable URL
    try:
        content = reader.scrape_url('https://example.com')
        
        assert len(content) > 0
        assert isinstance(content, str)
        # Should be markdown, not HTML
        assert '<html>' not in content.lower()
        
    except ResearchError as e:
        # If it fails, it should be a proper error, not a crash
        assert 'Failed to scrape' in str(e) or 'Timeout' in str(e)
