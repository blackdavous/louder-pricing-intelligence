"""
MCP Server for Web Scraping Mercado Libre.

⚠️ DEPRECATED - Kept for reference only ⚠️

Este módulo fue implementado como fallback temporal cuando la API de 
Mercado Libre estaba bloqueada. Ahora se debe usar la nueva API oficial.

Status: DEPRECATED - Do not use in production
Original Purpose: Uses Selenium to extract product data by navigating
                 the website like a real user, avoiding API blocks.
"""
import asyncio
import time
import random
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebScraperClient:
    """
    Web scraper for Mercado Libre using Selenium.
    
    Simulates human browsing to extract product information
    without using the API.
    """
    
    BASE_URL = "https://www.mercadolibre.com.mx"
    
    def __init__(self, headless: bool = True):
        """
        Initialize web scraper.
        
        Args:
            headless: Run browser in headless mode (no GUI)
        """
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome driver with options."""
        if self.driver:
            return
        
        logger.info("Initializing Chrome driver", headless=self.headless)
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Chrome driver", error=str(e))
            raise
    
    def _human_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Simulate human delay between actions."""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _random_scroll(self):
        """Perform random scroll to simulate human behavior."""
        scroll_amount = random.randint(200, 500)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self._human_delay(0.3, 0.8)
    
    async def search_products(
        self,
        query: str,
        limit: int = 50,
        condition: str = "all",  # all, new, used
        sort: str = "relevance",  # relevance, price_asc, price_desc
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Search for products on Mercado Libre by navigating the website.
        
        Args:
            query: Search query
            limit: Maximum number of results
            condition: Product condition filter
            sort: Sort order
            min_price: Minimum price filter
            max_price: Maximum price filter
        
        Returns:
            Dict with search results
        """
        logger.info(
            "Starting web scraping search",
            query=query,
            limit=limit,
            condition=condition
        )
        
        try:
            self._init_driver()
            
            # Build search URL
            search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}"
            
            # Add filters to URL
            if condition != "all":
                search_url += f"&condition={condition}"
            
            if sort != "relevance":
                sort_map = {
                    "price_asc": "price_asc",
                    "price_desc": "price_desc"
                }
                search_url += f"&sort={sort_map.get(sort, 'relevance')}"
            
            if min_price or max_price:
                price_filter = f"&price={min_price or '*'}-{max_price or '*'}"
                search_url += price_filter
            
            logger.info("Navigating to search URL", url=search_url)
            self.driver.get(search_url)
            
            # Wait for results to load
            self._human_delay(2, 4)
            
            # Random scroll to load dynamic content
            for _ in range(random.randint(1, 3)):
                self._random_scroll()
            
            # Extract products
            products = []
            
            # Try multiple selectors (ML changes their HTML frequently)
            selectors = [
                ("css", "li.ui-search-layout__item"),
                ("css", "div.ui-search-result__wrapper"),
                ("css", "div.ui-search-result__content-wrapper"),
                ("class", "ui-search-result"),
                ("css", "div.poly-component__item")
            ]
            
            product_elements = []
            for selector_type, selector_value in selectors:
                try:
                    if selector_type == "class":
                        elements = self.driver.find_elements(By.CLASS_NAME, selector_value)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector_value)
                    
                    if elements:
                        logger.info(f"Found {len(elements)} elements with {selector_type}:{selector_value}")
                        product_elements = elements
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector_value} failed: {e}")
                    continue
            
            if not product_elements:
                # Save page HTML for debugging
                with open("ml_debug.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logger.warning("No product elements found. HTML saved to ml_debug.html")
            
            try:
                logger.info(f"Processing {len(product_elements)} product elements")
                
                for idx, element in enumerate(product_elements[:limit]):
                    try:
                        # Extract product data
                        product_data = self._extract_product_from_element(element)
                        if product_data:
                            products.append(product_data)
                        
                        # Human-like delay between extractions
                        if idx % 10 == 0:
                            self._human_delay(0.2, 0.5)
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract product {idx}", error=str(e))
                        continue
                
            except TimeoutException:
                logger.warning("Timeout waiting for products")
            
            logger.info(
                "Search completed",
                query=query,
                products_found=len(products)
            )
            
            return {
                "success": True,
                "query": query,
                "total_results": len(products),
                "results": products,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Web scraping search failed", error=str(e), query=query)
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }
    
    def _extract_product_from_element(self, element) -> Optional[Dict[str, Any]]:
        """
        Extract product information from a search result element.
        
        Args:
            element: Selenium WebElement
        
        Returns:
            Dict with product data or None if extraction fails
        """
        try:
            product = {}
            
            # Extract title
            try:
                title_elem = element.find_element(By.CLASS_NAME, "ui-search-item__title")
                product["title"] = title_elem.text.strip()
            except NoSuchElementException:
                product["title"] = "N/A"
            
            # Extract price
            try:
                price_elem = element.find_element(By.CLASS_NAME, "andes-money-amount__fraction")
                price_text = price_elem.text.replace(",", "").replace(".", "")
                product["price"] = float(price_text)
            except (NoSuchElementException, ValueError):
                # Try alternative price selector
                try:
                    price_elem = element.find_element(By.CSS_SELECTOR, ".price-tag-fraction")
                    price_text = price_elem.text.replace(",", "").replace(".", "")
                    product["price"] = float(price_text)
                except:
                    product["price"] = None
            
            # Extract currency
            try:
                currency_elem = element.find_element(By.CLASS_NAME, "andes-money-amount__currency-symbol")
                product["currency"] = currency_elem.text.strip()
            except NoSuchElementException:
                product["currency"] = "MXN"
            
            # Extract link
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, "a.ui-search-link")
                product["permalink"] = link_elem.get_attribute("href")
                
                # Extract ID from link
                id_match = re.search(r'MLM-?(\d+)', product["permalink"])
                if id_match:
                    product["id"] = f"MLM{id_match.group(1)}"
                else:
                    product["id"] = None
            except NoSuchElementException:
                product["permalink"] = None
                product["id"] = None
            
            # Extract condition
            try:
                condition_elem = element.find_element(By.CLASS_NAME, "ui-search-item__group__element")
                condition_text = condition_elem.text.lower()
                if "nuevo" in condition_text:
                    product["condition"] = "new"
                elif "usado" in condition_text:
                    product["condition"] = "used"
                else:
                    product["condition"] = "unknown"
            except NoSuchElementException:
                product["condition"] = "unknown"
            
            # Extract shipping info
            try:
                shipping_elem = element.find_element(By.CLASS_NAME, "ui-search-item__shipping")
                shipping_text = shipping_elem.text.lower()
                product["free_shipping"] = "gratis" in shipping_text or "free" in shipping_text
            except NoSuchElementException:
                product["free_shipping"] = False
            
            # Extract thumbnail
            try:
                img_elem = element.find_element(By.CSS_SELECTOR, "img.ui-search-result-image__element")
                product["thumbnail"] = img_elem.get_attribute("src")
            except NoSuchElementException:
                product["thumbnail"] = None
            
            # Only return if we have at least title and price
            if product.get("title") and product.get("price"):
                return product
            
            return None
            
        except Exception as e:
            logger.warning("Failed to extract product data", error=str(e))
            return None
    
    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Get detailed product information by visiting the product page.
        
        Args:
            product_url: Full URL to product page
        
        Returns:
            Dict with detailed product information
        """
        logger.info("Fetching product details", url=product_url)
        
        try:
            self._init_driver()
            
            self.driver.get(product_url)
            self._human_delay(2, 4)
            
            # Scroll to load all content
            for _ in range(2):
                self._random_scroll()
            
            product_details = {}
            
            # Extract title
            try:
                title_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ui-pdp-title"))
                )
                product_details["title"] = title_elem.text.strip()
            except TimeoutException:
                product_details["title"] = "N/A"
            
            # Extract price
            try:
                price_elem = self.driver.find_element(By.CLASS_NAME, "andes-money-amount__fraction")
                price_text = price_elem.text.replace(",", "").replace(".", "")
                product_details["price"] = float(price_text)
            except (NoSuchElementException, ValueError):
                product_details["price"] = None
            
            # Extract condition
            try:
                condition_elem = self.driver.find_element(By.CLASS_NAME, "ui-pdp-subtitle")
                condition_text = condition_elem.text.lower()
                if "nuevo" in condition_text:
                    product_details["condition"] = "new"
                elif "usado" in condition_text:
                    product_details["condition"] = "used"
                else:
                    product_details["condition"] = "unknown"
            except NoSuchElementException:
                product_details["condition"] = "unknown"
            
            # Extract attributes/specifications
            attributes = []
            try:
                attr_elements = self.driver.find_elements(By.CLASS_NAME, "ui-pdp-highlighted-specs-list__item")
                for attr_elem in attr_elements:
                    try:
                        attr_text = attr_elem.text.strip()
                        if attr_text:
                            attributes.append(attr_text)
                    except:
                        continue
            except NoSuchElementException:
                pass
            
            product_details["attributes"] = attributes
            product_details["permalink"] = product_url
            
            logger.info("Product details extracted successfully", title=product_details.get("title"))
            
            return {
                "success": True,
                "product": product_details
            }
            
        except Exception as e:
            logger.error("Failed to get product details", error=str(e), url=product_url)
            return {
                "success": False,
                "error": str(e)
            }
    
    def close(self):
        """Close the browser."""
        if self.driver:
            logger.info("Closing Chrome driver")
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# MCP Tool functions

async def search_products_web_tool(
    query: str,
    limit: int = 50,
    condition: str = "all",
    sort: str = "relevance",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    MCP Tool: Search products using web scraping.
    
    Args:
        query: Search query
        limit: Maximum results
        condition: Product condition filter
        sort: Sort order
        min_price: Minimum price
        max_price: Maximum price
    
    Returns:
        Search results
    """
    client = WebScraperClient(headless=True)
    try:
        result = await client.search_products(
            query=query,
            limit=limit,
            condition=condition,
            sort=sort,
            min_price=min_price,
            max_price=max_price
        )
        return result
    finally:
        client.close()


async def get_product_details_web_tool(product_url: str) -> Dict[str, Any]:
    """
    MCP Tool: Get product details using web scraping.
    
    Args:
        product_url: URL to product page
    
    Returns:
        Product details
    """
    client = WebScraperClient(headless=True)
    try:
        result = await client.get_product_details(product_url)
        return result
    finally:
        client.close()
