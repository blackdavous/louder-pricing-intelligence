"""
Web Scraper MCP Server for Mercado Libre
Uses browser automation to extract product data
"""
from .server import (
    WebScraperClient,
    search_products_web_tool,
    get_product_details_web_tool
)

__all__ = [
    'WebScraperClient',
    'search_products_web_tool',
    'get_product_details_web_tool'
]
