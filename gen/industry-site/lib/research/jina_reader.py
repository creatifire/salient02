"""
Jina Reader client for web scraping and content extraction.

This module provides integration with the Jina Reader API for extracting
clean markdown content from web pages.
"""

from typing import Optional
import requests
from ..logging.logger import get_logger
from ..errors.exceptions import ResearchError
from ..llm.retry import exponential_backoff

logger = get_logger(__name__)


class JinaReader:
    """
    Client for Jina Reader API integration.
    
    Provides methods for scraping web pages and extracting clean markdown content.
    Jina Reader has a free tier that works without API key.
    """
    
    JINA_API_BASE = "https://r.jina.ai/"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize Jina Reader client.
        
        Args:
            api_key: Optional Jina API key (free tier works without key)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.timeout = timeout
        logger.info(f"Jina Reader client initialized (API key: {'provided' if api_key else 'free tier'})")
    
    def _build_headers(self) -> dict:
        """
        Build request headers with optional authentication.
        
        Returns:
            Dictionary of headers
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Industry-Site-Generator/1.0)',
            'Accept': 'text/plain, text/markdown, */*'
        }
        
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        
        return headers
    
    @exponential_backoff(max_retries=3, base_delay=2.0)
    def _make_request(self, url: str) -> str:
        """
        Make request to Jina API with retry logic.
        
        Args:
            url: Target URL to scrape
            
        Returns:
            Response text (markdown content)
            
        Raises:
            Exception: If request fails
        """
        jina_url = f"{self.JINA_API_BASE}{url}"
        response = requests.get(
            jina_url,
            headers=self._build_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.text
    
    def scrape_url(self, url: str) -> str:
        """
        Scrape a URL and extract clean markdown content.
        
        Args:
            url: Target URL to scrape
            
        Returns:
            Clean markdown content from the page
            
        Raises:
            ResearchError: If scraping fails or URL is invalid
            
        Example:
            >>> reader = JinaReader(api_key)
            >>> content = reader.scrape_url('https://example.com/products')
            >>> print(content[:200])
        """
        if not url:
            raise ResearchError("URL is required")
        
        if not url.startswith(('http://', 'https://')):
            raise ResearchError(f"Invalid URL format: {url}")
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Make request with retry logic
            content = self._make_request(url)
            
            # Clean and validate content
            cleaned_content = self._clean_content(content)
            
            logger.info(f"Successfully scraped {len(cleaned_content)} characters from {url}")
            return cleaned_content
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout while scraping {url}"
            logger.error(error_msg)
            raise ResearchError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to scrape {url}: {str(e)}"
            logger.error(error_msg)
            raise ResearchError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error scraping {url}: {str(e)}"
            logger.error(error_msg)
            raise ResearchError(error_msg) from e
    
    def scrape_multiple(self, urls: list[str]) -> dict[str, str]:
        """
        Scrape multiple URLs and return results.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Dictionary mapping URLs to their content
            
        Example:
            >>> reader = JinaReader()
            >>> results = reader.scrape_multiple([
            ...     'https://example.com/page1',
            ...     'https://example.com/page2'
            ... ])
        """
        results = {}
        
        for url in urls:
            try:
                content = self.scrape_url(url)
                results[url] = content
            except ResearchError as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                results[url] = None
        
        return results
    
    @staticmethod
    def _clean_content(content: str) -> str:
        """
        Clean and normalize markdown content.
        
        Args:
            content: Raw content from Jina API
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Jina Reader already returns clean markdown, but we can do light cleanup
        # Remove excessive whitespace
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip trailing whitespace but keep leading (for markdown indentation)
            line = line.rstrip()
            cleaned_lines.append(line)
        
        # Remove excessive blank lines (more than 2 in a row)
        result = []
        blank_count = 0
        
        for line in cleaned_lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        
        return '\n'.join(result)
    
    def extract_text_snippet(self, url: str, max_length: int = 500) -> str:
        """
        Scrape URL and return a text snippet.
        
        Args:
            url: Target URL
            max_length: Maximum length of snippet
            
        Returns:
            Text snippet from page
        """
        content = self.scrape_url(url)
        
        # Remove markdown formatting for snippet
        text = content.replace('#', '').replace('*', '').replace('_', '')
        text = ' '.join(text.split())  # Normalize whitespace
        
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text


def scrape_url(url: str, api_key: Optional[str] = None) -> str:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: Target URL to scrape
        api_key: Optional Jina API key
        
    Returns:
        Clean markdown content
        
    Example:
        >>> content = scrape_url('https://example.com')
    """
    reader = JinaReader(api_key)
    return reader.scrape_url(url)


def scrape_multiple_urls(urls: list[str], api_key: Optional[str] = None) -> dict[str, str]:
    """
    Convenience function to scrape multiple URLs.
    
    Args:
        urls: List of URLs to scrape
        api_key: Optional Jina API key
        
    Returns:
        Dictionary mapping URLs to content
    """
    reader = JinaReader(api_key)
    return reader.scrape_multiple(urls)
