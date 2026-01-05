"""
Search Strategy Agent - Determines optimal search terms for similar products.

This agent analyzes the characteristics of a pivot product (e.g., your Louder branded item)
and generates search terms to find similar products in the market, regardless of brand.

Use case: You import and rebrand products, so you need to find competitors with similar
specifications, not the same brand.
"""
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from app.core.logging import get_logger
from app.mcp_servers.mercadolibre.scraper import ProductDetails

logger = get_logger(__name__)


class SearchStrategyAgent:
    """
    Agent that determines optimal search strategy for finding similar products.
    
    Input: Complete product details (specifications, attributes)
    Output: Optimized search terms that focus on product category and key specifications
    """
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        """
        Initialize the search strategy agent.
        
        Args:
            model: OpenAI model to use
            temperature: Temperature for generation (0.2 = more focused)
        """
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        logger.info(
            "SearchStrategyAgent initialized",
            model=model,
            temperature=temperature
        )
    
    def generate_search_terms(self, product: ProductDetails) -> Dict[str, Any]:
        """
        Generate optimal search terms based on product characteristics.
        
        Args:
            product: Complete product details
            
        Returns:
            Dict with:
                - primary_search: Main search term (most likely to find similar products)
                - alternative_searches: List of alternative search terms
                - key_specs: Key specifications to focus on
                - reasoning: Why these terms were chosen
        """
        logger.info(
            "Generating search strategy",
            product_id=product.product_id,
            title=product.title
        )
        
        # Build product description for LLM
        product_info = self._build_product_description(product)
        
        # Create prompt
        prompt = f"""Eres un experto en análisis de productos electrónicos y estrategias de búsqueda para e-commerce.

Tu tarea es analizar un producto que el usuario importa y rebrandea, y generar los MEJORES términos de búsqueda para encontrar productos SIMILARES en Mercado Libre.

IMPORTANTE:
- NO busques por marca, ya que el usuario usa su propia marca (Louder)
- Enfócate en las CARACTERÍSTICAS TÉCNICAS y CATEGORÍA del producto
- Los competidores tendrán marcas diferentes pero características similares
- Genera términos que encuentren productos con las MISMAS ESPECIFICACIONES

PRODUCTO A ANALIZAR:
{product_info}

Por favor, genera:
1. **primary_search**: El término de búsqueda PRINCIPAL (el más probable de encontrar productos similares)
   - Debe incluir tipo de producto + especificación clave
   - Ejemplo: "bocina techo 5 pulgadas" o "audífonos bluetooth cancelación ruido"
   
2. **alternative_searches**: 3-5 búsquedas alternativas para ampliar resultados
   - Variaciones con diferentes términos técnicos
   - Diferentes formas de describir el producto
   
3. **key_specs**: Lista de especificaciones técnicas CLAVE que deben tener los productos comparables
   - Ejemplo: ["5 pulgadas", "10W", "línea 70-100V", "instalación empotrada"]
   
4. **exclude_terms**: Términos que deben EXCLUIRSE (para evitar productos diferentes)
   - Ejemplo: ["bluetooth", "portátil"] si el producto es de instalación fija
   
5. **reasoning**: Breve explicación de por qué elegiste estos términos

Responde SOLO en formato JSON válido:
{{
  "primary_search": "término principal",
  "alternative_searches": ["alternativa 1", "alternativa 2", ...],
  "key_specs": ["spec 1", "spec 2", ...],
  "exclude_terms": ["término 1", "término 2", ...],
  "reasoning": "explicación breve"
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            result = self._parse_llm_response(response.content)
            
            logger.info(
                "Search strategy generated",
                primary_search=result.get("primary_search"),
                alternatives_count=len(result.get("alternative_searches", []))
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating search strategy: {e}")
            # Fallback to basic strategy
            return self._fallback_strategy(product)
    
    def _build_product_description(self, product: ProductDetails) -> str:
        """Build a comprehensive product description for the LLM."""
        lines = [
            f"Título: {product.title}",
            f"Precio: ${product.price:,.2f} {product.currency}",
            f"Condición: {product.condition}",
        ]
        
        if product.brand:
            lines.append(f"Marca: {product.brand}")
        
        if product.category:
            lines.append(f"Categoría: {product.category}")
        
        if product.attributes:
            lines.append("\nEspecificaciones técnicas:")
            for key, value in product.attributes.items():
                lines.append(f"  - {key}: {value}")
        
        if product.description:
            desc_short = product.description[:500] if len(product.description) > 500 else product.description
            lines.append(f"\nDescripción: {desc_short}")
        
        return "\n".join(lines)
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        import json
        import re
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        # Try direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise
    
    def _fallback_strategy(self, product: ProductDetails) -> Dict[str, Any]:
        """Fallback strategy when LLM fails."""
        logger.warning("Using fallback search strategy")
        
        # Extract key terms from title (remove brand)
        title_clean = product.title.lower()
        if product.brand:
            title_clean = title_clean.replace(product.brand.lower(), "").strip()
        
        # Simple word extraction
        words = [w for w in title_clean.split() if len(w) > 3][:5]
        primary = " ".join(words)
        
        return {
            "primary_search": primary,
            "alternative_searches": [product.title],
            "key_specs": list(product.attributes.keys())[:5] if product.attributes else [],
            "exclude_terms": [],
            "reasoning": "Fallback strategy - usando términos básicos del título"
        }
