"""
Research analyzer for extracting and structuring product information.

This module provides functions to analyze scraped web content and extract
structured product information using LLM assistance.
"""

from typing import List, Dict, Any, Optional
import json
from ..logging.logger import get_logger
from ..errors.exceptions import ResearchError
from ..llm.client import LLMClient
from ..llm.prompts import load_prompt, load_system_prompt

logger = get_logger(__name__)


class ResearchAnalyzer:
    """
    Analyzer for extracting structured data from research content.
    
    Uses LLM to intelligently extract and structure product information
    from scraped web content.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize research analyzer.
        
        Args:
            llm_client: LLM client for analysis
        """
        self.llm = llm_client
        logger.info("Research analyzer initialized")
    
    def analyze_products(
        self,
        content: str,
        company_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze content and extract product information.
        
        Args:
            content: Scraped content to analyze
            company_name: Optional company name for context
            
        Returns:
            List of product dictionaries with keys:
                - name: Product name
                - description: Product description
                - category: Product category (if identifiable)
                - features: List of key features
                
        Raises:
            ResearchError: If analysis fails
            
        Example:
            >>> analyzer = ResearchAnalyzer(llm_client)
            >>> products = analyzer.analyze_products(content, "AgriTech Corp")
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for analysis")
            return []
        
        try:
            logger.info(f"Analyzing content for products (length: {len(content)} chars)")
            
            # Load prompt for product extraction
            prompt = load_prompt('research', 'extract_products', {
                'content': content[:5000]  # Limit to first 5000 chars
            })
            
            # Get system prompt
            system_prompt = load_system_prompt('researcher')
            
            # Make LLM call
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            
            response = self.llm.chat(messages, temperature=0.3)
            
            # Parse response
            products = self._parse_product_response(response['content'])
            
            logger.info(f"Extracted {len(products)} products from content")
            return products
            
        except Exception as e:
            error_msg = f"Failed to analyze products: {str(e)}"
            logger.error(error_msg)
            raise ResearchError(error_msg) from e
    
    def categorize_products(
        self,
        products: List[str],
        num_categories: int = 10
    ) -> Dict[str, List[str]]:
        """
        Categorize products into logical groups.
        
        Args:
            products: List of product names
            num_categories: Number of categories to create
            
        Returns:
            Dictionary mapping category names to product lists
            
        Raises:
            ResearchError: If categorization fails
            
        Example:
            >>> categories = analyzer.categorize_products(
            ...     ['Tractor', 'Software', 'Seeds'],
            ...     num_categories=3
            ... )
        """
        if not products:
            logger.warning("No products provided for categorization")
            return {}
        
        try:
            logger.info(f"Categorizing {len(products)} products into {num_categories} categories")
            
            # Format products as string
            products_str = '\n'.join(f"- {p}" for p in products)
            
            # Load prompt
            prompt = load_prompt('research', 'categorize_products', {
                'products': products_str,
                'num_categories': str(num_categories)
            })
            
            # Get system prompt
            system_prompt = load_system_prompt('researcher')
            
            # Make LLM call
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            
            response = self.llm.chat(messages, temperature=0.2)
            
            # Parse response
            categories = self._parse_category_response(response['content'])
            
            logger.info(f"Created {len(categories)} categories")
            return categories
            
        except Exception as e:
            error_msg = f"Failed to categorize products: {str(e)}"
            logger.error(error_msg)
            raise ResearchError(error_msg) from e
    
    def extract_product_names(self, content: str) -> List[str]:
        """
        Simple extraction of product names from content.
        
        This is a lightweight extraction without full LLM analysis.
        Useful for quick scans or when full analysis isn't needed.
        
        Args:
            content: Content to extract from
            
        Returns:
            List of product names
        """
        if not content:
            return []
        
        # Look for common product patterns
        # This is a basic implementation - the LLM-based analyze_products is more robust
        names = []
        
        # Split into lines and look for product-like entries
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and very long lines
            if not line or len(line) > 200:
                continue
            
            # Look for list items or product names
            if any(indicator in line.lower() for indicator in [
                'product', 'model', 'series', '®', '™'
            ]):
                # Clean up the line
                name = line.strip('- *•').strip()
                if name and len(name) > 2:
                    names.append(name)
        
        logger.info(f"Extracted {len(names)} potential product names")
        return names[:100]  # Limit to 100 products
    
    def _parse_product_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured product list.
        
        Args:
            response: LLM response text
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        try:
            # Try to parse as JSON first
            if '{' in response and '[' in response:
                # Find JSON content
                start = response.find('[')
                end = response.rfind(']') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    products = json.loads(json_str)
                    return products
        except json.JSONDecodeError:
            logger.warning("Failed to parse response as JSON, using text parsing")
        
        # Fallback: Parse as text
        lines = response.split('\n')
        current_product = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_product:
                    products.append(current_product)
                    current_product = {}
                continue
            
            # Look for product indicators
            if line.startswith(('Product Name:', 'Name:', '**')):
                if current_product:
                    products.append(current_product)
                current_product = {'name': line.split(':', 1)[-1].strip('* ').strip()}
            elif 'description:' in line.lower():
                current_product['description'] = line.split(':', 1)[-1].strip()
            elif 'category:' in line.lower():
                current_product['category'] = line.split(':', 1)[-1].strip()
        
        # Add last product
        if current_product:
            products.append(current_product)
        
        return products
    
    def _parse_category_response(self, response: str) -> Dict[str, List[str]]:
        """
        Parse LLM response into category dictionary.
        
        Args:
            response: LLM response text
            
        Returns:
            Dictionary mapping categories to products
        """
        categories = {}
        
        try:
            # Try to parse as JSON
            if '{' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                    
                    # Handle nested structure
                    if 'categories' in data:
                        for cat in data['categories']:
                            if 'name' in cat and 'products' in cat:
                                categories[cat['name']] = cat['products']
                    else:
                        categories = data
                    
                    return categories
        except json.JSONDecodeError:
            logger.warning("Failed to parse categories as JSON, using text parsing")
        
        # Fallback: Parse as text
        current_category = None
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for category headers
            if line.endswith(':') or line.startswith('#'):
                current_category = line.strip('#: ')
                if current_category not in categories:
                    categories[current_category] = []
            elif current_category and (line.startswith('-') or line.startswith('•')):
                product = line.strip('- •').strip()
                categories[current_category].append(product)
        
        return categories


def analyze_products(
    content: str,
    llm_client: LLMClient,
    company_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to analyze products.
    
    Args:
        content: Content to analyze
        llm_client: LLM client
        company_name: Optional company name
        
    Returns:
        List of product dictionaries
    """
    analyzer = ResearchAnalyzer(llm_client)
    return analyzer.analyze_products(content, company_name)


def categorize_products(
    products: List[str],
    llm_client: LLMClient,
    num_categories: int = 10
) -> Dict[str, List[str]]:
    """
    Convenience function to categorize products.
    
    Args:
        products: List of product names
        llm_client: LLM client
        num_categories: Number of categories
        
    Returns:
        Dictionary of categories
    """
    analyzer = ResearchAnalyzer(llm_client)
    return analyzer.categorize_products(products, num_categories)


def extract_product_names(content: str) -> List[str]:
    """
    Convenience function to extract product names.
    
    Args:
        content: Content to extract from
        
    Returns:
        List of product names
    """
    analyzer = ResearchAnalyzer(None)  # No LLM needed for simple extraction
    return analyzer.extract_product_names(content)
