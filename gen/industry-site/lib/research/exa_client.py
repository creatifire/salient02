"""
Exa search client for industry and company research.

This module provides integration with the Exa API for searching companies,
products, and industry-related information.
"""

from typing import List, Dict, Any, Optional
from exa_py import Exa
from ..logging.logger import get_logger
from ..errors.exceptions import ResearchError
from ..llm.retry import exponential_backoff

logger = get_logger(__name__)


class ExaClient:
    """
    Client for Exa search API integration.
    
    Provides methods for searching companies and products in specific industries.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Exa client.
        
        Args:
            api_key: Exa API key
            
        Raises:
            ResearchError: If API key is invalid or client initialization fails
        """
        if not api_key:
            raise ResearchError("Exa API key is required")
        
        try:
            self.client = Exa(api_key)
            logger.info("Exa client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Exa client: {str(e)}")
            raise ResearchError(f"Failed to initialize Exa client: {str(e)}") from e
    
    @exponential_backoff(max_retries=3, base_delay=2.0)
    def _make_search_request(
        self,
        query: str,
        num_results: int
    ) -> Any:
        """
        Make a search request with retry logic.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Search results from Exa API
        """
        return self.client.search(
            query,
            num_results=num_results
        )
    
    def search_companies(
        self,
        industry: str,
        num_results: int = 20,
        focus_areas: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for companies in a specific industry.
        
        Args:
            industry: Industry name (e.g., 'agtech', 'fintech')
            num_results: Number of results to return (default: 20)
            focus_areas: Optional specific focus areas within the industry
            
        Returns:
            List of company dictionaries with keys:
                - name: Company name
                - url: Company website URL
                - title: Page title
                - description: Brief description
                
        Raises:
            ResearchError: If search fails or returns invalid data
            
        Example:
            >>> client = ExaClient(api_key)
            >>> companies = client.search_companies('agtech', num_results=10)
            >>> print(companies[0]['name'])
        """
        try:
            # Build search query
            if focus_areas:
                query = f"top {industry} companies {focus_areas} products services"
            else:
                query = f"top {industry} companies products services"
            
            logger.info(f"Searching for {industry} companies: {query}")
            
            # Make search request with retry
            results = self._make_search_request(
                query=query,
                num_results=num_results
            )
            
            # Extract and structure results
            companies = []
            for result in results.results:
                company = {
                    'name': self._extract_company_name(result.title),
                    'url': result.url,
                    'title': result.title,
                    'description': getattr(result, 'text', '')[:200] if hasattr(result, 'text') else ''
                }
                companies.append(company)
            
            logger.info(f"Found {len(companies)} companies for {industry}")
            return companies
            
        except Exception as e:
            error_msg = f"Failed to search companies for {industry}: {str(e)}"
            logger.error(error_msg)
            raise ResearchError(error_msg) from e
    
    def search_products(
        self,
        industry: str,
        company_name: Optional[str] = None,
        num_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for products in a specific industry.
        
        Args:
            industry: Industry name
            company_name: Optional specific company to search
            num_results: Number of results to return
            
        Returns:
            List of product information dictionaries
            
        Raises:
            ResearchError: If search fails
        """
        try:
            # Build search query
            if company_name:
                query = f"{company_name} {industry} products catalog features"
            else:
                query = f"{industry} products catalog services offerings"
            
            logger.info(f"Searching for {industry} products: {query}")
            
            # Make search request with retry
            results = self._make_search_request(
                query=query,
                num_results=num_results
            )
            
            # Extract and structure results
            products = []
            for result in results.results:
                product_info = {
                    'source': result.url,
                    'title': result.title,
                    'content': getattr(result, 'text', '')[:500] if hasattr(result, 'text') else ''
                }
                products.append(product_info)
            
            logger.info(f"Found {len(products)} product results for {industry}")
            return products
            
        except Exception as e:
            error_msg = f"Failed to search products for {industry}: {str(e)}"
            logger.error(error_msg)
            raise ResearchError(error_msg) from e
    
    @staticmethod
    def _extract_company_name(title: str) -> str:
        """
        Extract company name from page title.
        
        Args:
            title: Page title
            
        Returns:
            Extracted company name
        """
        # Remove common suffixes and clean up
        name = title.split('|')[0].split('-')[0].strip()
        
        # Remove common words
        for word in ['Home', 'Official', 'Website', 'Site']:
            name = name.replace(word, '').strip()
        
        return name if name else title


def search_companies(industry: str, api_key: str, num_results: int = 20) -> List[Dict[str, Any]]:
    """
    Convenience function to search for companies.
    
    Args:
        industry: Industry name
        api_key: Exa API key
        num_results: Number of results to return
        
    Returns:
        List of company dictionaries
        
    Example:
        >>> companies = search_companies('agtech', api_key)
    """
    client = ExaClient(api_key)
    return client.search_companies(industry, num_results)


def search_products(
    industry: str,
    api_key: str,
    company_name: Optional[str] = None,
    num_results: int = 20
) -> List[Dict[str, Any]]:
    """
    Convenience function to search for products.
    
    Args:
        industry: Industry name
        api_key: Exa API key
        company_name: Optional specific company
        num_results: Number of results to return
        
    Returns:
        List of product dictionaries
    """
    client = ExaClient(api_key)
    return client.search_products(industry, company_name, num_results)
