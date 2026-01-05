# 🎯 Louder Pricing Intelligence

Sistema inteligente de análisis de precios para productos de audio en Mercado Libre. Utiliza **web scraping** + **agentes LLM** para encontrar competidores y generar recomendaciones de precio competitivas.

## ⚡ Características Principales

- **Análisis de Producto Pivote**: Extrae especificaciones completas de TU producto
- **Búsqueda Inteligente**: LLM genera términos de búsqueda basados en características técnicas  
- **Scraping Sin API**: Extrae datos de HTML de Mercado Libre (sin limitaciones de API)
- **Filtrado Inteligente**: LLM clasifica productos comparables vs accesorios/bundles
- **Estadísticas Avanzadas**: Método IQR para detección de outliers, análisis por condición
- **Recomendación Estratégica**: LLM genera pricing con reasoning y alternativas

## 🏗️ Arquitectura

### Flujo Completo (5 Pasos + Extracción)

```
Paso 0: Extraer especificaciones de TU producto (Python)
   ↓
Paso 1: LLM genera búsquedas óptimas por specs (gpt-4o-mini)
   ↓
Paso 2: Scraping HTML de productos similares (Python)
   ↓
Paso 3: LLM filtra productos comparables (gpt-4o-mini)
   ↓
Paso 4: Análisis estadístico con IQR (Python)
   ↓
Paso 5: LLM genera recomendación de precio (gpt-4o)
```

### Componentes

| Paso | Componente | Tecnología | Duración | Costo LLM |
|------|-----------|-----------|----------|-----------|
| 0 | ProductDetails Extractor | Python + Regex | ~1.5s | ❌ $0 |
| 1 | SearchStrategyAgent | gpt-4o-mini (temp 0.2) | ~3-5s | ✅ $ |
| 2 | MLWebScraper | Python + requests | ~1-2s | ❌ $0 |
| 3 | ProductMatchingAgent | gpt-4o-mini (temp 0.1) | ~20-25s | ✅ $ |
| 4 | Stats Module | Python (IQR, percentiles) | <0.1s | ❌ $0 |
| 5 | PricingIntelligenceAgent | gpt-4o (temp 0.3) | ~0.5-1s | ✅ $$ |

**Total**: ~28-35 segundos | **Ahorro**: 48% menos llamadas LLM vs arquitectura anterior

## 📋 Caso de Uso

**Problema**: Importas productos de China y los rebrandeas con tu marca (ej. Louder). Necesitas saber precios competitivos, pero no puedes buscar por marca porque usas tu propia marca.

**Solución**:
```python
# URL de tu producto
url = "https://www.mercadolibre.com.mx/bocina-louder-ypo-900red/p/MLM50988032"

# El sistema:
# 1. Extrae: "5 pulgadas, 10W, línea 70-100V, empotrada"
# 2. Busca: "bocina techo 5 pulgadas 10W" (sin marca)
# 3. Encuentra competidores con características similares
# 4. Recomienda: $699 MXN (mediana del mercado)
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.11+
- UV package manager
- OpenAI API key

### Setup en 3 Pasos

```bash
# 1. Clonar e instalar
git clone <repo>
cd audiolouder
uv pip install -r requirements.txt --system

# 2. Configurar
cp .env.example .env
# Editar .env: OPENAI_API_KEY=sk-...

# 3. Probar
python scripts/demo_pivot_product.py
```

## 🎮 Uso Básico

### Modo 1: Análisis desde URL (RECOMENDADO)

```python
from app.agents.pricing_pipeline import PricingPipeline
import asyncio

pipeline = PricingPipeline()

# Tu producto
url = "https://www.mercadolibre.com.mx/tu-producto/p/MLM..."

result = await pipeline.analyze_product(
    product_input=url,
    max_offers=30
)

print(f"Precio: ${result['final_recommendation']['recommended_price']}")
```

### Modo 2: Análisis desde Descripción (LEGACY)

```python
result = await pipeline.analyze_product(
    product_input="Sony WH-1000XM5 audífonos",
    max_offers=25
)
```

## 📊 Ejemplo de Resultado

```json
{
  "pivot_product": {
    "title": "Bocina Techo Louder YPO-900RED",
    "attributes": {"Potencia": "10W", "Tamaño": "5\""}
  },
  "search_strategy": {
    "primary_search": "bocina techo 5 pulgadas 10W",
    "reasoning": "Enfoque en specs sin marca"
  },
  "statistics": {
    "median": 699.00,
    "q1": 599.00,
    "q3": 899.00
  },
  "final_recommendation": {
    "recommended_price": 699.00,
    "strategy": "COMPETITIVE",
    "alternatives": {
      "aggressive": 649.00,
      "premium": 799.00
    }
  }
}
```

## 📁 Estructura

```
audiolouder/
├── backend/app/
│   ├── agents/                    # Agentes LLM
│   │   ├── search_strategy.py    # Genera búsquedas por specs
│   │   ├── product_matching.py   # Filtra comparables
│   │   ├── pricing_intelligence.py # Recomendación
│   │   └── pricing_pipeline.py   # Orchestrador
│   └── mcp_servers/mercadolibre/
│       ├── scraper.py             # Web scraping
│       ├── stats.py               # Análisis estadístico
│       └── models.py              # Data classes
├── scripts/
│   ├── demo_pivot_product.py      # Demo con URL
│   └── demo_new_pipeline.py       # Demo legacy
├── docs/                          # Documentación técnica
└── tests/                         # Tests
```

## 🔧 Configuración

Archivo `.env`:

```bash
# OpenAI (REQUERIDO)
OPENAI_API_KEY=sk-...
OPENAI_MODEL_MINI=gpt-4o-mini
OPENAI_MODEL_FULL=gpt-4o

# Mercado Libre (OPCIONAL - solo para API oficial)
ML_API_ENABLED=false
ML_ACCESS_TOKEN=...

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🧪 Testing

```bash
# Demo completo
python scripts/demo_pivot_product.py

# Tests de integración
pytest tests/
```

## 📚 Documentación

- [NEW_AGENT_ARCHITECTURE.md](docs/NEW_AGENT_ARCHITECTURE.md) - Arquitectura con diagramas Mermaid
- [MCP_SERVERS_IMPLEMENTATION.md](docs/MCP_SERVERS_IMPLEMENTATION.md) - Detalles de scraping
- [ML_API_INTEGRATION_ANALYSIS.md](docs/ML_API_INTEGRATION_ANALYSIS.md) - Análisis API vs Scraping

## 🛠️ Stack Tecnológico

- **Python 3.11+**: Lenguaje principal
- **LangChain + LangGraph**: Framework para agentes
- **OpenAI GPT-4o/mini**: Modelos de lenguaje
- **UV**: Gestor de paquetes moderno
- **Structlog**: Logging estructurado
- **FastAPI**: REST API (opcional)

## 🤝 Equipo

Proyecto académico - Maestría en IA y Ciencia de Datos, Universidad Panamericana 2026

- Edgar Alberto Morales Gutiérrez
- Gustavo Alberto Gómez Rojas
- Carlos David Gómez Rodríguez

---

**Ver más**: [Documentación completa](docs/) | [Scripts de ejemplo](scripts/)
