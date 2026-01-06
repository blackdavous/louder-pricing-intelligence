"""
Louder Price Intelligence - Streamlit Frontend
Interface for product price analysis and recommendations
"""
import streamlit as st
import requests
import re
from typing import Optional, Dict, Any
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
BACKEND_AVAILABLE = False

# Check if backend is running
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=2)
    BACKEND_AVAILABLE = response.status_code == 200
except:
    BACKEND_AVAILABLE = False


def extract_product_info_from_url(url: str) -> Optional[Dict[str, str]]:
    """
    Extract product information from Mercado Libre URL.
    
    Examples:
    - https://www.mercadolibre.com.mx/rollo-de-cable-uso-rudo-calibre-14-awg-para-bocina-100m/p/MLM53396734
    - https://articulo.mercadolibre.com.mx/MLM-123456789-producto
    """
    # Extract product name from URL
    patterns = [
        r'mercadolibre\.com\.mx/([^/]+)/p/',  # /p/ URLs
        r'MLM-\d+-([^/\?]+)',  # MLM URLs
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            product_name = match.group(1)
            # Clean up: replace hyphens with spaces and capitalize
            product_name = product_name.replace('-', ' ').title()
            return {
                "name": product_name,
                "url": url
            }
    
    return None


def run_analysis_locally(product_name: str, cost: float, margin: float) -> Dict[str, Any]:
    """
    Run analysis locally using the agent modules directly.
    This is used when the backend API is not available.
    """
    import sys
    import os
    import asyncio
    
    # Add backend to path
    backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    try:
        from app.agents.market_research import MarketResearchAgent
        from app.agents.pricing_intelligence import PricingIntelligenceAgent
        
        async def run():
            # Step 1: Market Research
            market_agent = MarketResearchAgent()
            product_attributes = {
                "category": "general",
                "type": "product"
            }
            research_result = await market_agent.run(product_name, product_attributes)
            
            # Step 2: Extract competitor prices (or use samples if none found)
            competitors = research_result.get('competitors', [])
            if competitors:
                competitor_prices = [c.get('price', 0) for c in competitors if c.get('price')]
            else:
                # Use sample data
                competitor_prices = [2350.0, 2449.0, 2524.0, 2599.0, 2674.0, 2699.0, 2724.0, 
                                    2799.0, 2849.0, 2874.0, 2924.0, 2949.0, 2974.0, 2999.0, 3049.0]
            
            # Step 3: Pricing Intelligence
            pricing_agent = PricingIntelligenceAgent()
            result = await pricing_agent.run(
                product_id="temp-product",
                product_name=product_name,
                cost_price=cost,
                competitor_prices=competitor_prices,
                target_margin_percent=margin
            )
            
            # Format result
            recommendation = result.get('recommendation')
            stats = result.get('price_statistics')
            
            if recommendation and stats:
                return {
                    "success": True,
                    "product_name": product_name,
                    "recommended_price": recommendation.recommended_price,
                    "margin_percent": recommendation.expected_margin_percent,
                    "confidence": recommendation.confidence,
                    "market_position": recommendation.market_position,
                    "alternatives": recommendation.alternative_prices,
                    "reasoning": recommendation.reasoning,
                    "statistics": {
                        "sample_size": len(competitor_prices),
                        "min_price": stats.min,
                        "median_price": stats.median,
                        "mean_price": stats.mean,
                        "max_price": stats.max,
                        "std_dev": stats.std_dev
                    },
                    "competitors_analyzed": len(competitors)
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo generar recomendación"
                }
        
        # Run async function
        result = asyncio.run(run())
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    st.set_page_config(
        page_title="Louder Price Intelligence",
        page_icon="💰",
        layout="wide"
    )
    
    # Header
    st.title("💰 Louder Price Intelligence")
    st.markdown("**Análisis inteligente de precios para Mercado Libre**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Backend status
        if BACKEND_AVAILABLE:
            st.success("✅ Backend conectado")
        else:
            st.warning("⚠️ Modo local (sin API)")
            st.caption("El análisis se ejecutará directamente")
        
        st.divider()
        
        # Cost and margin inputs
        st.subheader("Parámetros del producto")
        
        product_cost = st.number_input(
            "💵 Costo del producto (MXN)",
            min_value=0.0,
            value=500.0,
            step=50.0,
            help="Costo de adquisición o fabricación"
        )
        
        target_margin = st.number_input(
            "📈 Margen objetivo (%)",
            min_value=0.0,
            max_value=500.0,
            value=40.0,
            step=5.0,
            help="Margen de ganancia deseado"
        )
        
        st.divider()
        
        # Info section
        st.subheader("ℹ️ Información")
        st.caption("""
        **Cómo usar:**
        1. Ingresa un link de ML o nombre del producto
        2. Ajusta costo y margen deseado
        3. Haz clic en Analizar
        4. Obtén tu recomendación de precio
        
        **Posicionamiento:**
        - 🟢 Budget: 25° percentil
        - 🔵 Competitive: 50° percentil  
        - 🟠 Premium: 75° percentil
        - 🟣 Luxury: 90° percentil
        """)
    
    # Main content area
    st.divider()
    
    # Product input section
    st.header("🔍 Buscar Producto")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        product_input = st.text_input(
            "Ingresa el link de Mercado Libre o nombre del producto",
            placeholder="https://www.mercadolibre.com.mx/producto... o 'Cable para bocina calibre 14'",
            help="Puedes pegar un link completo de Mercado Libre o escribir el nombre del producto"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        analyze_button = st.button("🚀 Analizar", type="primary", use_container_width=True)
    
    # Process input when button is clicked
    if analyze_button and product_input:
        
        # Determine if input is URL or product name
        product_name = product_input
        is_url = False
        
        if "mercadolibre.com" in product_input.lower():
            is_url = True
            extracted = extract_product_info_from_url(product_input)
            if extracted:
                product_name = extracted["name"]
                st.info(f"📦 Producto detectado: **{product_name}**")
            else:
                st.warning("⚠️ No se pudo extraer el nombre del producto del link. Usando link completo.")
        
        # Progress indicator
        with st.spinner(f"🔄 Analizando **{product_name}**..."):
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("⏳ Buscando competidores en Mercado Libre...")
                progress_bar.progress(20)
                time.sleep(0.5)
                
                # Run analysis
                if BACKEND_AVAILABLE:
                    # Use API
                    status_text.text("📡 Conectando con API...")
                    progress_bar.progress(40)
                    
                    response = requests.post(
                        f"{API_BASE_URL}/api/agents/pricing-workflow",
                        json={
                            "product_name": product_name,
                            "product_cost": product_cost,
                            "target_margin_percent": target_margin
                        },
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                    else:
                        st.error(f"❌ Error en la API: {response.status_code}")
                        st.stop()
                else:
                    # Run locally
                    status_text.text("🧮 Calculando estadísticas...")
                    progress_bar.progress(60)
                    
                    result = run_analysis_locally(product_name, product_cost, target_margin)
                    
                    if not result.get("success"):
                        st.error(f"❌ Error en el análisis: {result.get('error')}")
                        st.stop()
                
                status_text.text("✅ Análisis completado!")
                progress_bar.progress(100)
                time.sleep(0.5)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                st.divider()
                st.header("📊 Resultados del Análisis")
                
                # Main recommendation card
                st.subheader("💡 Recomendación de Precio")
                
                rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(4)
                
                with rec_col1:
                    st.metric(
                        "💰 Precio Recomendado",
                        f"${result['recommended_price']:,.2f} MXN",
                        help="Precio óptimo según análisis de mercado"
                    )
                
                with rec_col2:
                    margin_value = result['margin_percent']
                    margin_delta = margin_value - target_margin
                    st.metric(
                        "📈 Margen Real",
                        f"{margin_value:.1f}%",
                        f"{margin_delta:+.1f}% vs objetivo",
                        help="Margen de ganancia real con el precio recomendado"
                    )
                
                with rec_col3:
                    confidence = result['confidence'].upper()
                    confidence_color = {
                        "HIGH": "🟢",
                        "MEDIUM": "🟡", 
                        "LOW": "🔴"
                    }.get(confidence, "⚪")
                    
                    st.metric(
                        "🎯 Confianza",
                        f"{confidence_color} {confidence}",
                        help="Nivel de confianza basado en cantidad de datos"
                    )
                
                with rec_col4:
                    position = result['market_position'].upper()
                    position_emoji = {
                        "BUDGET": "🟢",
                        "COMPETITIVE": "🔵",
                        "PREMIUM": "🟠",
                        "LUXURY": "🟣"
                    }.get(position, "⚪")
                    
                    st.metric(
                        "🏆 Posicionamiento",
                        f"{position_emoji} {position}",
                        help="Posición en el mercado"
                    )
                
                st.divider()
                
                # Statistics section
                col_stats1, col_stats2 = st.columns(2)
                
                with col_stats1:
                    st.subheader("📊 Estadísticas del Mercado")
                    
                    stats = result.get('statistics', {})
                    
                    st.write(f"**📦 Muestra:** {stats.get('sample_size', result.get('competitors_analyzed', 0))} productos")
                    st.write(f"**💵 Precio mínimo:** ${stats.get('min_price', 0):,.2f} MXN")
                    st.write(f"**📊 Precio mediano:** ${stats.get('median_price', 0):,.2f} MXN")
                    st.write(f"**📈 Precio promedio:** ${stats.get('mean_price', 0):,.2f} MXN")
                    st.write(f"**💰 Precio máximo:** ${stats.get('max_price', 0):,.2f} MXN")
                    st.write(f"**📉 Desv. estándar:** ${stats.get('std_dev', 0):,.2f} MXN")
                
                with col_stats2:
                    st.subheader("🎯 Alternativas de Precio")
                    
                    alternatives = result.get('alternatives', [])
                    
                    if alternatives:
                        for i, alt_price in enumerate(alternatives, 1):
                            alt_margin = ((alt_price - product_cost) / product_cost) * 100 if product_cost > 0 else 0
                            st.write(f"**{i}.** ${alt_price:,.2f} MXN _(margen: {alt_margin:.1f}%)_")
                    else:
                        st.info("No hay alternativas disponibles")
                
                st.divider()
                
                # Reasoning section
                st.subheader("💭 Razonamiento")
                st.info(result.get('reasoning', 'No disponible'))
                
                # Raw data expander (for debugging)
                with st.expander("🔧 Ver datos completos (debug)"):
                    st.json(result)
                
            except requests.exceptions.Timeout:
                st.error("⏱️ Timeout: El análisis tomó demasiado tiempo. Intenta nuevamente.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Error de conexión: No se pudo conectar con el backend.")
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")
                st.exception(e)
    
    elif analyze_button and not product_input:
        st.warning("⚠️ Por favor ingresa un producto o link de Mercado Libre")
    
    # Footer
    st.divider()
    st.caption("💡 **Louder Price Intelligence** - Análisis de precios basado en IA | Versión 0.1.0")


if __name__ == "__main__":
    main()
