"""
MCP Server for Mercado Libre API Integration.

Provides tools for:
- Searching products
- Getting product details
- Batch price retrieval
"""
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MercadoLibreClient:
    """
    Client for Mercado Libre API.
    
    Updated to work with new API endpoint.
    Ready to integrate custom API when credentials are provided.
    
    Provides methods for searching products, getting details,
    and batch operations.
    """
    
    # TODO: Update these URLs with your new API endpoint when ready
    BASE_URL = "https://api.mercadolibre.com"  # Change to your new API
    AUTH_URL = "https://api.mercadolibre.com/oauth/token"  # If authentication is needed
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or settings.ML_CLIENT_ID
        self.client_secret = client_secret or settings.ML_CLIENT_SECRET
        self.country = settings.ML_COUNTRY
        self.access_token: Optional[str] = None
        
        # Log initialization status
        logger.info(
            "Initializing MercadoLibreClient",
            api_enabled=settings.ML_API_ENABLED,
            has_credentials=bool(self.client_id and self.client_secret)
        )
    
    async def get_access_token(self) -> Optional[str]:
        """
        Get OAuth access token using client credentials flow.
        This is needed when API blocks public access.
        
        TODO: Adjust this method according to your new API authentication:
              - If using API Key, modify to set headers instead
              - If using Bearer token, adjust the flow accordingly
              - If no auth needed, return None and skip this step
        
        Returns:
            Access token string or None if failed
        """
        if self.access_token:
            return self.access_token
            
        logger.info("Requesting OAuth access token")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.AUTH_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    logger.info("OAuth token obtained successfully")
                    return self.access_token
                else:
                    logger.error(
                        "Failed to get OAuth token",
                        status=response.status_code,
                        error=response.text
                    )
                    return None
                    
        except httpx.HTTPError as e:
            logger.error("OAuth request failed", error=str(e))
            return None
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
        condition: str = "all",  # all, new, used
        sort: str = "relevance"  # relevance, price_asc, price_desc
    ) -> Dict[str, Any]:
        """
        Search for products on Mercado Libre.
        
        Args:
            query: Search query string
            category: Category filter (e.g., "MLM1051" for Audio)
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Number of results (max 50)
            offset: Pagination offset
            condition: Product condition filter
            sort: Sort order
        
        Returns:
            Dict with search results and metadata
        """
        logger.info(
            "Searching products on Mercado Libre",
            query=query,
            category=category,
            limit=limit
        )
        
        # Build search URL
        url = f"{self.BASE_URL}/sites/{self.country}/search"
        
        # Build params
        params = {
            "q": query,
            "limit": min(limit, 50),
            "offset": offset,
        }
        
        if category:
            params["category"] = category
        
        if min_price is not None:
            params["price"] = f"{min_price}-{max_price or ''}"
        
        if condition != "all":
            params["condition"] = condition
        
        if sort != "relevance":
            params["sort"] = sort
        
        try:
            # Get access token if not already obtained
            token = await self.get_access_token()
            
            headers = {
                "User-Agent": "Louder Price Intelligence/1.0",
                "Accept": "application/json"
            }
            
            # Add authorization if token available
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                
                logger.info(
                    "Search completed",
                    query=query,
                    results_found=data.get("paging", {}).get("total", 0),
                    results_returned=len(data.get("results", []))
                )
                
                return {
                    "success": True,
                    "query": query,
                    "total_results": data.get("paging", {}).get("total", 0),
                    "returned": len(data.get("results", [])),
                    "offset": offset,
                    "limit": limit,
                    "results": data.get("results", []),
                    "filters": data.get("available_filters", []),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except httpx.HTTPError as e:
            logger.error("ML API search failed", error=str(e), query=query)
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.
        
        Args:
            product_id: Mercado Libre product ID (e.g., "MLM123456")
        
        Returns:
            Dict with product details
        """
        logger.info("Fetching product details", product_id=product_id)
        
        url = f"{self.BASE_URL}/items/{product_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract relevant fields
                product = {
                    "success": True,
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "price": data.get("price"),
                    "currency_id": data.get("currency_id"),
                    "available_quantity": data.get("available_quantity"),
                    "sold_quantity": data.get("sold_quantity"),
                    "condition": data.get("condition"),
                    "permalink": data.get("permalink"),
                    "thumbnail": data.get("thumbnail"),
                    "pictures": [p.get("secure_url") for p in data.get("pictures", [])],
                    "attributes": data.get("attributes", []),
                    "category_id": data.get("category_id"),
                    "seller_id": data.get("seller_id"),
                    "shipping": {
                        "free_shipping": data.get("shipping", {}).get("free_shipping", False),
                        "mode": data.get("shipping", {}).get("mode"),
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info("Product details fetched", product_id=product_id, price=product["price"])
                
                return product
                
        except httpx.HTTPError as e:
            logger.error("Failed to fetch product details", error=str(e), product_id=product_id)
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def batch_get_prices(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Get current prices for multiple products in batch.
        
        Args:
            product_ids: List of ML product IDs
        
        Returns:
            Dict with product prices and metadata
        """
        logger.info("Batch fetching prices", count=len(product_ids))
        
        # ML API supports multi-get with comma-separated IDs (max 20)
        batch_size = 20
        all_results = []
        
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]
            ids_param = ",".join(batch)
            
            url = f"{self.BASE_URL}/items"
            params = {"ids": ids_param}
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params, timeout=30.0)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Process batch results
                    for item in data:
                        if item.get("code") == 200:
                            body = item.get("body", {})
                            all_results.append({
                                "id": body.get("id"),
                                "title": body.get("title"),
                                "price": body.get("price"),
                                "currency_id": body.get("currency_id"),
                                "available_quantity": body.get("available_quantity"),
                                "condition": body.get("condition"),
                                "seller_id": body.get("seller_id"),
                            })
                        else:
                            logger.warning(
                                "Failed to fetch item in batch",
                                item_id=item.get("body", {}).get("id"),
                                error_code=item.get("code")
                            )
                    
            except httpx.HTTPError as e:
                logger.error("Batch request failed", error=str(e), batch_size=len(batch))
        
        logger.info("Batch fetch completed", requested=len(product_ids), retrieved=len(all_results))
        
        return {
            "success": True,
            "requested": len(product_ids),
            "retrieved": len(all_results),
            "products": all_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_category_info(self, category_id: str) -> Dict[str, Any]:
        """
        Get category information including attributes.
        
        Args:
            category_id: ML category ID (e.g., "MLM1051")
        
        Returns:
            Dict with category info
        """
        logger.info("Fetching category info", category_id=category_id)
        
        url = f"{self.BASE_URL}/categories/{category_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "success": True,
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "path_from_root": data.get("path_from_root", []),
                    "attributes": data.get("attributes", []),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except httpx.HTTPError as e:
            logger.error("Failed to fetch category", error=str(e), category_id=category_id)
            return {
                "success": False,
                "error": str(e),
                "category_id": category_id,
                "timestamp": datetime.utcnow().isoformat()
            }


# Singleton instance
ml_client = MercadoLibreClient()


# MCP Tool Functions
async def search_products_tool(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    MCP Tool: Search products on Mercado Libre.
    
    This tool searches for products matching the query and filters.
    """
    return await ml_client.search_products(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        limit=limit
    )


async def get_product_details_tool(product_id: str) -> Dict[str, Any]:
    """
    MCP Tool: Get detailed product information.
    
    Fetches complete details for a specific product ID.
    """
    return await ml_client.get_product_details(product_id)


async def batch_get_prices_tool(product_ids: List[str]) -> Dict[str, Any]:
    """
    MCP Tool: Get prices for multiple products.
    
    Efficiently fetches current prices for a list of product IDs.
    """
    return await ml_client.batch_get_prices(product_ids)
