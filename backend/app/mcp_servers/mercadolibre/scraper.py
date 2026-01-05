"""
Web scraper for Mercado Libre.
Migrated from agente_precios_ml_gagr.ipynb

This module extracts product data from ML HTML without using API.
Strategy: Extract __PRELOADED_STATE__ or JSON-LD from HTML.
"""
import re
import json
import time
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import IdentifiedProduct, Offer, ScrapingResult
from app.core.logging import get_logger
from dataclasses import dataclass

logger = get_logger(__name__)


@dataclass
class ProductDetails:
    """Detailed information extracted from a specific product page."""
    product_id: str
    title: str
    price: float
    currency: str
    condition: str
    brand: Optional[str]
    model: Optional[str]
    category: Optional[str]
    attributes: Dict[str, Any]  # Technical specifications
    description: Optional[str]
    images: List[str]
    seller_name: Optional[str]
    permalink: str
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "product_id": self.product_id,
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "condition": self.condition,
            "brand": self.brand,
            "model": self.model,
            "category": self.category,
            "attributes": self.attributes,
            "description": self.description,
            "images": self.images,
            "seller_name": self.seller_name,
            "permalink": self.permalink,
        }


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}


# Accessory keywords to filter out
ACCESSORY_NEGATIVES = [
    "funda", "case", "carcasa", "protector", "mica", "glass", "templado", "cable",
    "adaptador", "cargador", "base", "soporte", "refacción", "repuesto", "control",
    "almohadillas", "earpads", "estuche", "solo caja"
]


def normalize_text(s: str) -> str:
    """Normalize text: lowercase and single spaces."""
    return re.sub(r"\s+", " ", s.lower().strip())


def normalize_model(s: str) -> str:
    """Normalize model: alphanumeric only."""
    return re.sub(r"[^a-z0-9]", "", normalize_text(s))


def extract_product(description: str) -> IdentifiedProduct:
    """
    Extract product brand and model from description.
    
    Args:
        description: Product description or name
        
    Returns:
        IdentifiedProduct with brand, model, and signature
    """
    d = normalize_text(description)
    
    # Detect brand (can be extended)
    brand = "sony" if " sony " in f" {d} " else None
    
    # Extract model pattern (e.g., "WH-1000XM5", "MDR-ZX110")
    mm = re.search(r"\b([a-z]{1,4}\s*[-]?\s*\d{2,6}\s*[a-z]{0,6}\d*)\b", d)
    model = mm.group(1) if mm else None
    model_norm = normalize_model(model) if model else None
    
    # Create signature
    signature = " ".join([x for x in [brand, model] if x]).strip() or description.strip()
    
    return IdentifiedProduct(brand, model, model_norm, signature)


def match_title(title: str, product: IdentifiedProduct) -> bool:
    """
    Check if a title matches the target product.
    
    Args:
        title: Product title from listing
        product: Target product to match
        
    Returns:
        True if title matches product
    """
    t = normalize_text(title)
    
    # Filter out accessories
    if any(x in t for x in ACCESSORY_NEGATIVES):
        return False
    
    # Match by model (strongest match)
    if product.model_norm:
        return product.model_norm in normalize_model(title)
    
    # Match by brand (weaker match)
    if product.brand:
        return product.brand in t
    
    # Default: accept (for generic searches)
    return True


def listing_url(query: str) -> str:
    """
    Generate Mercado Libre listing URL from query.
    
    Args:
        query: Search query
        
    Returns:
        ML listing URL
    """
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_text(query)).strip("-")
    return f"https://listado.mercadolibre.com.mx/{slug}"


def extract_js_object_by_brackets(text: str, start_idx: int) -> Optional[str]:
    """
    Extract JavaScript object by balanced bracket matching.
    More robust than regex for nested objects.
    
    Args:
        text: Full text containing JS object
        start_idx: Index of opening brace '{'
        
    Returns:
        Extracted JS object string or None
    """
    i = start_idx
    if i < 0 or i >= len(text) or text[i] != "{":
        return None
    
    depth = 0
    in_str = False
    esc = False
    quote = ""
    
    for j in range(i, len(text)):
        ch = text[j]
        
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        else:
            if ch in ("'", '"'):
                in_str = True
                quote = ch
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[i:j+1]
    
    return None


def extract_preloaded_state(html: str) -> Optional[dict]:
    """
    Extract __PRELOADED_STATE__ from HTML.
    
    This is a JavaScript object embedded in the page with product data.
    
    Args:
        html: Page HTML
        
    Returns:
        Parsed dict or None
    """
    m = re.search(r"__PRELOADED_STATE__\s*=\s*", html)
    if not m:
        return None
    
    k = m.end()
    brace = html.find("{", k)
    if brace == -1:
        return None
    
    obj_str = extract_js_object_by_brackets(html, brace)
    if not obj_str:
        return None
    
    # Try direct JSON parse
    try:
        return json.loads(obj_str)
    except Exception:
        pass
    
    # Clean common JS issues
    cleaned = obj_str
    cleaned = re.sub(r"\bundefined\b", "null", cleaned)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    
    try:
        return json.loads(cleaned)
    except Exception:
        logger.warning("Failed to parse __PRELOADED_STATE__")
        return None


def extract_jsonld_nodes(html: str) -> List[Dict[str, Any]]:
    """
    Extract JSON-LD nodes from HTML (fallback method).
    
    Args:
        html: Page HTML
        
    Returns:
        List of JSON-LD nodes with product data
    """
    nodes = []
    
    for m in re.finditer(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE
    ):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except Exception:
            continue
        
        # Traverse object tree to find product nodes
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, dict):
                if ("name" in x or "title" in x) and ("offers" in x or "price" in x):
                    nodes.append(x)
                for v in x.values():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(x, list):
                for v in x:
                    if isinstance(v, (dict, list)):
                        stack.append(v)
    
    return nodes


def offers_from_state(state: dict, product: IdentifiedProduct, limit: int = 150) -> List[Offer]:
    """
    Extract offers from __PRELOADED_STATE__.
    
    Args:
        state: Parsed __PRELOADED_STATE__ dict
        product: Target product for filtering
        limit: Max offers to extract
        
    Returns:
        List of Offer objects
    """
    out: List[Offer] = []
    stack = [state]
    
    while stack and len(out) < limit:
        x = stack.pop()
        
        if isinstance(x, dict):
            title = x.get("title") or x.get("name")
            price = x.get("price")
            if isinstance(price, dict):
                price = price.get("amount") or price.get("value")
            url = x.get("permalink") or x.get("url") or ""
            item_id = x.get("id") or x.get("item_id") or ""
            
            if title and price is not None:
                try:
                    p = float(price)
                    if match_title(str(title), product):
                        out.append(Offer(
                            title=str(title),
                            price=p,
                            condition=str(x.get("condition") or "unknown"),
                            url=str(url),
                            item_id=str(item_id),
                            source="preloaded_state",
                        ))
                except Exception:
                    pass
            
            for v in x.values():
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(x, list):
            for v in x:
                if isinstance(v, (dict, list)):
                    stack.append(v)
    
    return out


def offers_from_jsonld(nodes: List[Dict[str, Any]], product: IdentifiedProduct, limit: int = 150) -> List[Offer]:
    """
    Extract offers from JSON-LD nodes (fallback).
    
    Args:
        nodes: JSON-LD nodes
        product: Target product
        limit: Max offers
        
    Returns:
        List of Offer objects
    """
    out: List[Offer] = []
    
    for node in nodes:
        title = node.get("name") or node.get("title")
        url = node.get("url") or ""
        offers = node.get("offers")
        cand_prices = []
        
        if isinstance(offers, dict):
            cand_prices.append(offers.get("price"))
            url = offers.get("url") or url
        elif isinstance(offers, list):
            for o in offers:
                if isinstance(o, dict):
                    cand_prices.append(o.get("price"))
                    if not url:
                        url = o.get("url") or url
        
        for pr in cand_prices:
            if title and pr is not None:
                try:
                    p = float(pr)
                    if match_title(str(title), product):
                        out.append(Offer(
                            title=str(title),
                            price=p,
                            condition="unknown",
                            url=str(url),
                            item_id="",
                            source="jsonld",
                        ))
                        if len(out) >= limit:
                            return out
                except Exception:
                    continue
    
    return out


class MLWebScraper:
    """
    Mercado Libre web scraper.
    Extracts product data from HTML without API.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
    
    def search_products(
        self,
        description: str,
        max_offers: int = 25,
        timeout: int = 25
    ) -> ScrapingResult:
        """
        Search for products and extract offers from HTML.
        
        Args:
            description: Product description (e.g., "Sony WH-1000XM5 audifonos")
            max_offers: Maximum offers to return
            timeout: Request timeout in seconds
            
        Returns:
            ScrapingResult with offers and metadata
        """
        logger.info(
            "Starting ML web scraping",
            description=description,
            max_offers=max_offers
        )
        
        # Extract product info
        product = extract_product(description)
        url = listing_url(product.signature)
        
        logger.info(
            "Product identified",
            brand=product.brand,
            model=product.model,
            signature=product.signature,
            url=url
        )
        
        # Fetch HTML
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            logger.error("Failed to fetch HTML", error=str(e), url=url)
            return ScrapingResult(
                identified_product=product,
                strategy="error",
                listing_url=url,
                offers=[],
                timestamp=datetime.now().isoformat()
            )
        
        offers: List[Offer] = []
        strategy = "none"
        
        # Try __PRELOADED_STATE__ first
        state = extract_preloaded_state(html)
        if isinstance(state, dict):
            offers = offers_from_state(state, product, limit=max_offers * 6)
            strategy = "preloaded_state"
            logger.info(f"Extracted {len(offers)} offers from __PRELOADED_STATE__")
        
        # Fallback to JSON-LD
        if not offers:
            nodes = extract_jsonld_nodes(html)
            offers = offers_from_jsonld(nodes, product, limit=max_offers * 6)
            strategy = "jsonld" if offers else "no_offers"
            logger.info(f"Extracted {len(offers)} offers from JSON-LD")
        
        # Limit offers
        offers = offers[:max_offers]
        
        logger.info(
            "Scraping completed",
            strategy=strategy,
            offers_count=len(offers)
        )
        
        return ScrapingResult(
            identified_product=product,
            strategy=strategy,
            listing_url=url,
            offers=offers,
            timestamp=datetime.now().isoformat()
        )
    
    def extract_product_details(self, product_url: str) -> Optional[ProductDetails]:
        """
        Extract detailed information from a specific product page.
        
        This is used to analyze your pivot product (e.g., Louder branded item)
        to understand its characteristics before searching for similar products.
        
        Args:
            product_url: Full URL to the product page (e.g., https://www.mercadolibre.com.mx/.../p/MLM50988032)
            
        Returns:
            ProductDetails with complete product information or None
        """
        logger.info(
            "Extracting product details from URL",
            url=product_url
        )
        
        try:
            response = requests.get(product_url, headers=DEFAULT_HEADERS, timeout=15)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            logger.error(f"Failed to fetch product page: {e}")
            return None
        
        # Try to extract from __PRELOADED_STATE__
        state = extract_preloaded_state(html)
        if state:
            details = self._extract_details_from_state(state, product_url)
            if details:
                return details
        
        # Fallback to JSON-LD
        nodes = extract_jsonld_nodes(html)
        if nodes:
            details = self._extract_details_from_jsonld(nodes, product_url)
            if details:
                return details
        
        logger.warning("Could not extract product details from page")
        return None
    
    def _extract_details_from_state(self, state: dict, url: str) -> Optional[ProductDetails]:
        """Extract product details from __PRELOADED_STATE__."""
        try:
            # Navigate the state structure to find product info
            components = state.get("components", {})
            
            # Try different paths where product data might be
            product_data = None
            for key, value in components.items():
                if isinstance(value, dict) and "product" in value:
                    product_data = value.get("product")
                    break
                elif isinstance(value, dict) and "item" in value:
                    product_data = value.get("item")
                    break
            
            if not product_data:
                return None
            
            # Extract attributes
            attributes = {}
            if "attributes" in product_data:
                for attr in product_data.get("attributes", []):
                    if isinstance(attr, dict):
                        name = attr.get("name") or attr.get("id")
                        value = attr.get("value_name") or attr.get("value")
                        if name and value:
                            attributes[name] = value
            
            # Extract images
            images = []
            if "pictures" in product_data:
                for pic in product_data.get("pictures", []):
                    if isinstance(pic, dict) and "url" in pic:
                        images.append(pic["url"])
            
            return ProductDetails(
                product_id=product_data.get("id", ""),
                title=product_data.get("title", ""),
                price=float(product_data.get("price", 0)),
                currency=product_data.get("currency_id", "MXN"),
                condition=product_data.get("condition", "unknown"),
                brand=attributes.get("Marca") or attributes.get("BRAND"),
                model=attributes.get("Modelo") or attributes.get("MODEL"),
                category=product_data.get("category_id"),
                attributes=attributes,
                description=product_data.get("description"),
                images=images,
                seller_name=product_data.get("seller", {}).get("nickname") if isinstance(product_data.get("seller"), dict) else None,
                permalink=url
            )
        except Exception as e:
            logger.error(f"Error extracting from state: {e}")
            return None
    
    def _extract_details_from_jsonld(self, nodes: List[dict], url: str) -> Optional[ProductDetails]:
        """Extract product details from JSON-LD."""
        try:
            # Find Product node
            product_node = None
            for node in nodes:
                if node.get("@type") == "Product":
                    product_node = node
                    break
            
            if not product_node:
                return None
            
            # Extract offers
            offers_data = product_node.get("offers", {})
            if isinstance(offers_data, list) and offers_data:
                offers_data = offers_data[0]
            
            price = 0.0
            currency = "MXN"
            if isinstance(offers_data, dict):
                price = float(offers_data.get("price", 0))
                currency = offers_data.get("priceCurrency", "MXN")
            
            # Extract brand
            brand_data = product_node.get("brand")
            brand = None
            if isinstance(brand_data, dict):
                brand = brand_data.get("name")
            elif isinstance(brand_data, str):
                brand = brand_data
            
            # Extract images
            images = []
            image_data = product_node.get("image", [])
            if isinstance(image_data, str):
                images = [image_data]
            elif isinstance(image_data, list):
                images = [img if isinstance(img, str) else img.get("url") for img in image_data if img]
            
            # Extract product ID from URL or sku
            product_id = product_node.get("sku", "")
            if not product_id:
                match = re.search(r"ML[A-Z]\d+", url)
                product_id = match.group(0) if match else ""
            
            return ProductDetails(
                product_id=product_id,
                title=product_node.get("name", ""),
                price=price,
                currency=currency,
                condition=product_node.get("itemCondition", "unknown"),
                brand=brand,
                model=product_node.get("model"),
                category=product_node.get("category"),
                attributes={},  # JSON-LD typically doesn't have detailed attributes
                description=product_node.get("description"),
                images=images,
                seller_name=None,
                permalink=url
            )
        except Exception as e:
            logger.error(f"Error extracting from JSON-LD: {e}")
            return None
