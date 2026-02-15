"""Research module for industry and company research."""

from .exa_client import ExaClient, search_companies, search_products
from .jina_reader import JinaReader, scrape_url, scrape_multiple_urls
from .analyzer import (
    ResearchAnalyzer,
    analyze_products,
    categorize_products,
    extract_product_names
)

__all__ = [
    'ExaClient',
    'search_companies',
    'search_products',
    'JinaReader',
    'scrape_url',
    'scrape_multiple_urls',
    'ResearchAnalyzer',
    'analyze_products',
    'categorize_products',
    'extract_product_names'
]
