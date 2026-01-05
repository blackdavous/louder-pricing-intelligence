# Plan de Sistema de Monitoreo de Precios Competitivos - Louder Audio

## Resumen Ejecutivo

Sistema autónomo de agentes que monitorea continuamente los precios de la competencia en Mercado Libre para productos de audio profesional de la marca Louder. Utiliza la API de Mercado Libre para obtener datos de mercado, OpenAI para análisis inteligente y embeddings para matching de productos similares.

---

## 1. Análisis de la Situación Actual

### Productos Louder (Ejemplos del catálogo):
- Bocinas profesionales (10", 12", 15", 18")
- Subwoofers y woofers de alta potencia
- Bocinas para line array
- Bocinas ambientales
- Cables de audio
- Máquinas de humo/efectos

### Rango de Precios Actuales:
- Entrada: $549 - $899 MXN (bocinas 10"-12")
- Media: $899 - $1,699 MXN (bocinas 12"-15")
- Alta: $1,699 - $4,347+ MXN (bocinas 18", máquinas de humo)

### Desafíos Identificados:
- Alta competencia en categorías similares
- Necesidad de posicionamiento competitivo por percentil
- Productos únicos pero con sustitutos similares
- Precios dinámicos en el mercado

---

## 2. Arquitectura del Sistema

### Stack Tecnológico Propuesto

#### Backend Framework
- **FastAPI** (Python)
  - API REST para gestión del sistema
  - Webhooks para actualizaciones
  - Admin dashboard

#### Bases de Datos
- **PostgreSQL con pgvector**
  - Almacenamiento de productos propios
  - Histórico de precios de competencia
  - Búsqueda vectorial para matching de productos
  
- **Redis**
  - Cache de consultas a APIs
  - Cola de tareas (Bull/BullMQ alternativa Python: Celery)
  - Rate limiting

#### Procesamiento Asíncrono
- **Celery** con Redis como broker
  - Tareas programadas (scraping periódico)
  - Procesamiento de análisis de precios
  - Generación de embeddings

#### APIs Externas
- **Mercado Libre API**
  - Search API: Búsqueda de productos competencia
  - Items API: Detalles de productos
  - Categories API: Filtrado por categorías
  
- **OpenAI API**
  - GPT-4o-mini: Generación de queries de búsqueda optimizadas
  - GPT-4o: Análisis de similitud y categorización
  - text-embedding-3-small: Embeddings para matching semántico

#### MCP Servers
- **MCP Server Custom para Mercado Libre**
  - Tools para búsqueda de productos
  - Tools para análisis de precios
  - Tools para extracción de características

- **MCP Server para Análisis Estadístico**
  - Distribuciones de precios
  - Cálculo de percentiles
  - Recomendaciones de pricing

---

## 3. Flujo de Trabajo del Sistema

### Fase 1: Configuración Inicial de Productos

**Agente: Product Catalog Manager**

**Responsabilidades:**
1. Importar catálogo de productos Louder desde CSV/JSON
2. Para cada producto, generar:
   - Descripción normalizada
   - Keywords de búsqueda
   - Categoría de ML sugerida
   - Atributos clave (tamaño, potencia, impedancia, etc.)
3. Generar embeddings de cada producto
4. Almacenar en BD con metadata

**Tools necesarias:**
- `import_catalog`: Importa productos desde archivo
- `generate_search_keywords`: Usa LLM para generar keywords óptimas
- `generate_product_embedding`: Crea vector semántico
- `store_product`: Guarda en PostgreSQL

---

### Fase 2: Búsqueda Inteligente de Competencia

**Agente: Market Research Agent**

**Responsabilidades:**
1. Para cada producto Louder:
   - Generar query de búsqueda óptima usando LLM
   - Aplicar filtros relevantes (categoría, rango de precio estimado)
   - Ejecutar búsqueda en ML API
   - Obtener top 20-50 resultados
2. Filtrar resultados por relevancia:
   - Excluir productos idénticos (mismo seller)
   - Verificar similitud semántica con embeddings
   - Score de relevancia > threshold

**Tools necesarias:**
- `generate_ml_search_query`: LLM genera query optimizada
- `search_mercadolibre`: Ejecuta búsqueda en ML API
- `filter_by_similarity`: Compara embeddings (cosine similarity)
- `exclude_own_products`: Filtra productos propios

**Ejemplo de búsqueda generada:**
```
Producto: "Bocina 12 Pulgadas Profesional 8 Ohms"

Query generada por LLM:
- Término: "bocina 12 pulgadas profesional"
- Filtros:
  - category_id: MLM1389 (Audio Profesional)
  - price_range: 600-1500 MXN
  - condition: new
  - shipping: free_shipping
  - Excluir: seller_id=LOUDER_ID
```

---

### Fase 3: Extracción de Datos de Competencia

**Agente: Product Data Extractor**

**Responsabilidades:**
1. Para cada producto competidor relevante:
   - Obtener detalles completos vía Items API
   - Extraer: precio actual, stock, seller info, specs
   - Calcular métricas: precio/unidad, rating, ventas
2. Enriquecer datos:
   - Generar embedding del producto competidor
   - Calcular similarity score con producto Louder
   - Clasificar nivel de competencia (directa/indirecta)

**Tools necesarias:**
- `get_item_details`: Obtiene info completa de ML
- `extract_specifications`: Parse de atributos técnicos
- `calculate_similarity_score`: Compara con producto base
- `store_competitor_data`: Guarda en BD con timestamp

---

### Fase 4: Análisis Estadístico y Pricing

**Agente: Pricing Intelligence Agent**

**Responsabilidades:**
1. Agrupar productos competidores por producto Louder
2. Análisis estadístico de precios:
   - Distribución de precios (media, mediana, desv. estándar)
   - Cálculo de percentiles (P10, P25, P50, P75, P90)
   - Detección de outliers
   - Tendencias temporales (si hay histórico)
3. Posicionamiento actual:
   - En qué percentil está el precio actual Louder
   - Gap vs competencia directa
4. Recomendación de precio:
   - Según percentil objetivo configurado
   - Considerando: costo, margen mínimo, estrategia
   - Alertas si precio fuera de rango competitivo

**Tools necesarias:**
- `calculate_price_distribution`: Stats de precios
- `get_current_position`: Percentil actual del producto
- `calculate_target_price`: Precio según percentil objetivo
- `generate_pricing_report`: Reporte con recomendaciones

**Ejemplo de output:**
```json
{
  "product_id": "LOUDER-BC12-PRO",
  "product_name": "Bocina 12 Pulgadas Profesional",
  "current_price": 899,
  "competitors_analyzed": 23,
  "price_statistics": {
    "min": 650,
    "max": 1450,
    "mean": 987,
    "median": 950,
    "std_dev": 185
  },
  "percentiles": {
    "p10": 720,
    "p25": 850,
    "p50": 950,
    "p75": 1100,
    "p90": 1280
  },
  "current_position": {
    "percentile": 42,
    "interpretation": "Por debajo de la mediana"
  },
  "recommendation": {
    "target_percentile": 50,
    "target_price": 950,
    "price_adjustment": "+51 MXN (+5.7%)",
    "confidence": "high",
    "reasoning": "El producto está bien posicionado. Ajuste moderado mantendría competitividad mientras mejora margen."
  }
}
```

---

### Fase 5: Orquestación y Automatización

**Agente: Orchestrator Agent**

**Responsabilidades:**
- Coordinar ejecución de todos los agentes
- Gestionar flujo de datos entre agentes
- Manejar errores y reintentos
- Programar ejecuciones periódicas

**Configuración de Ejecución:**
- **Daily Full Scan**: Todos los productos, 1 vez al día
- **Priority Products Scan**: Top 10 productos, cada 6 horas
- **Flash Updates**: Productos en promoción, cada 1 hora
- **On-Demand**: Triggered por usuario o evento

**Tools necesarias:**
- `schedule_scan`: Programa escaneo
- `trigger_pipeline`: Ejecuta flujo completo
- `monitor_health`: Verifica estado del sistema
- `send_alerts`: Notificaciones (email, Slack, etc.)

---

## 4. MCP Servers Personalizados

### MCP Server: Mercado Libre Intelligence

**Tools ofrecidas:**

1. **ml_search_products**
   - Input: query, filters, limit
   - Output: Lista de productos con metadata
   - Cache: 1 hora

2. **ml_get_product_details**
   - Input: product_id
   - Output: Detalles completos + precio histórico
   - Cache: 30 minutos

3. **ml_get_category_info**
   - Input: category_id
   - Output: Attributes, filters disponibles
   - Cache: 24 horas

4. **ml_batch_get_prices**
   - Input: array de product_ids
   - Output: Precios actuales en batch
   - Optimizado para rate limits

### MCP Server: Pricing Analytics

**Tools ofrecidas:**

1. **calculate_price_stats**
   - Input: array de precios
   - Output: Estadísticas descriptivas

2. **get_percentile_price**
   - Input: precios array, target percentile
   - Output: Precio correspondiente

3. **detect_price_anomalies**
   - Input: precios + contexto
   - Output: Outliers detectados

4. **generate_pricing_recommendation**
   - Input: stats + business rules
   - Output: Precio sugerido con reasoning

---

## 5. Base de Datos Schema

### Tabla: products

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    ml_id VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    current_price DECIMAL(10,2),
    cost DECIMAL(10,2),
    min_margin_percent DECIMAL(5,2),
    target_percentile INTEGER DEFAULT 50,
    attributes JSONB, -- {size, power, impedance, etc.}
    search_keywords TEXT[],
    embedding vector(1536), -- OpenAI embedding
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops);
```

### Tabla: competitor_products

```sql
CREATE TABLE competitor_products (
    id SERIAL PRIMARY KEY,
    ml_id VARCHAR(50) UNIQUE NOT NULL,
    seller_id VARCHAR(50),
    seller_name VARCHAR(255),
    title VARCHAR(500),
    category_id VARCHAR(50),
    attributes JSONB,
    embedding vector(1536),
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

### Tabla: price_snapshots

```sql
CREATE TABLE price_snapshots (
    id SERIAL PRIMARY KEY,
    louder_product_id INTEGER REFERENCES products(id),
    competitor_product_id INTEGER REFERENCES competitor_products(id),
    price DECIMAL(10,2) NOT NULL,
    stock_available INTEGER,
    shipping_free BOOLEAN,
    seller_reputation JSONB,
    similarity_score DECIMAL(5,4), -- 0-1 similarity con producto Louder
    competition_level VARCHAR(20), -- direct, indirect, substitute
    snapshot_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON price_snapshots(louder_product_id, snapshot_at DESC);
CREATE INDEX ON price_snapshots(competitor_product_id, snapshot_at DESC);
```

### Tabla: pricing_recommendations

```sql
CREATE TABLE pricing_recommendations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    recommended_price DECIMAL(10,2),
    current_price DECIMAL(10,2),
    current_percentile DECIMAL(5,2),
    target_percentile INTEGER,
    competitors_analyzed INTEGER,
    price_stats JSONB, -- {min, max, mean, median, std, percentiles}
    reasoning TEXT,
    confidence VARCHAR(20), -- high, medium, low
    applied BOOLEAN DEFAULT FALSE,
    generated_at TIMESTAMP DEFAULT NOW()
);
```

### Tabla: scan_logs

```sql
CREATE TABLE scan_logs (
    id SERIAL PRIMARY KEY,
    scan_type VARCHAR(50), -- full, priority, flash, on-demand
    products_scanned INTEGER,
    competitors_found INTEGER,
    errors JSONB,
    duration_seconds INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) -- success, partial, failed
);
```

---

## 6. API Endpoints (FastAPI)

### Admin & Control

```
POST   /api/products/import          # Import catálogo inicial
GET    /api/products                 # List productos Louder
GET    /api/products/{id}            # Detalle producto
PUT    /api/products/{id}            # Update producto
POST   /api/products/{id}/scan       # Trigger scan on-demand

POST   /api/scans/trigger            # Ejecutar escaneo manual
GET    /api/scans                    # Histórico de scans
GET    /api/scans/{id}               # Detalle de scan

GET    /api/pricing/recommendations  # Lista recomendaciones
POST   /api/pricing/apply/{id}       # Aplicar recomendación
```

### Analytics & Reports

```
GET    /api/analytics/product/{id}         # Dashboard de producto
GET    /api/analytics/market-overview      # Vista general del mercado
GET    /api/analytics/price-trends/{id}    # Histórico de precios
GET    /api/analytics/competitors/{id}     # Competencia de un producto
```

### Webhooks & Notifications

```
POST   /api/webhooks/ml-price-change  # ML notifica cambio precio
POST   /api/notifications/config      # Configurar alertas
```

---

## 7. Configuración de Agentes (LangGraph/CrewAI/AutoGen)

Recomiendo usar **LangGraph** para máxima flexibilidad:

### Graph Structure

```
START
  ↓
[Product Catalog Manager] (one-time setup)
  ↓
[Orchestrator] (scheduled)
  ↓
  ├─→ [Market Research Agent] (parallel for each product)
  │     ↓
  │   [Product Data Extractor]
  │     ↓
  │   [Store Data]
  ↓
[Pricing Intelligence Agent] (aggregates all)
  ↓
[Generate Reports]
  ↓
[Send Notifications] (if needed)
  ↓
END
```

### Agent Definitions

```python
# Ejemplo con LangGraph

from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

# State schema
class MarketState(TypedDict):
    products: list[Product]
    current_product: Product
    search_results: list[dict]
    competitor_data: list[CompetitorProduct]
    pricing_analysis: dict
    recommendations: list[PricingRecommendation]

# Agents
market_research_agent = ChatOpenAI(model="gpt-4o-mini").bind_tools([
    search_mercadolibre,
    generate_ml_search_query,
    filter_by_similarity
])

data_extractor_agent = ChatOpenAI(model="gpt-4o-mini").bind_tools([
    get_item_details,
    extract_specifications,
    calculate_similarity_score
])

pricing_agent = ChatOpenAI(model="gpt-4o").bind_tools([
    calculate_price_distribution,
    get_current_position,
    calculate_target_price
])
```

---

## 8. Consideraciones de Rate Limiting

### API de Mercado Libre
- **Límite**: ~5000 requests/hora (varía por endpoint)
- **Estrategia**: 
  - Cache agresivo (Redis)
  - Batch requests cuando posible
  - Exponential backoff en errores 429
  - Distribuir scans en el tiempo

### OpenAI API
- **Límite**: Depende del tier (verificar billing)
- **Estrategia**:
  - Usar GPT-4o-mini para tareas simples
  - Batch embeddings (hasta 100 por request)
  - Cache de embeddings de productos estables

---

## 9. Monitoreo y Alertas

### Métricas Clave
- Tasa de éxito de scans (>95%)
- Tiempo promedio de scan por producto (<30s)
- Cobertura de competencia (>15 productos/item)
- Tasa de aplicación de recomendaciones
- ROI: margen ganado vs costo del sistema

### Alertas Automáticas
1. **Precio fuera de rango**: Producto cae fuera del percentil 25-75
2. **Competencia nueva**: Producto muy similar detectado
3. **Cambio brusco**: Competidor baja precio >20%
4. **Oportunidad**: Gap grande entre precio actual y P75
5. **Error crítico**: Scan fallando >3 veces consecutivas

### Dashboard (Streamlit/Grafana)
- Mapa de calor de competitividad
- Gráficos de tendencia de precios
- Table de recomendaciones pendientes
- Logs de scans y errores

---

## 10. Plan de Implementación por Fases

### Fase 1: Foundation (Semana 1-2)
- [ ] Setup de base de datos PostgreSQL + pgvector
- [ ] Setup Redis y Celery
- [ ] Implementar modelos SQLAlchemy
- [ ] API básica FastAPI con CRUD productos
- [ ] Script de importación de catálogo

### Fase 2: MCP Servers (Semana 2-3)
- [ ] MCP Server para Mercado Libre API
  - Tool: search_products
  - Tool: get_product_details
  - Tool: batch_get_prices
- [ ] MCP Server para Analytics
  - Tool: calculate_price_stats
  - Tool: get_percentile_price
- [ ] Tests de integración con rate limiting

### Fase 3: Agentes Core (Semana 3-4)
- [ ] Market Research Agent
  - Generación de queries con LLM
  - Búsqueda en ML API
  - Filtrado por similitud
- [ ] Product Data Extractor
  - Extracción de detalles
  - Generación de embeddings
  - Storage en BD
- [ ] Tests con productos reales

### Fase 4: Pricing Intelligence (Semana 4-5)
- [ ] Pricing Intelligence Agent
  - Cálculo de distribuciones
  - Percentiles y posicionamiento
  - Generación de recomendaciones
- [ ] Dashboard de analytics (Streamlit)
- [ ] Validación de recomendaciones

### Fase 5: Automatización (Semana 5-6)
- [ ] Orchestrator Agent (LangGraph)
- [ ] Celery tasks para scans programados
- [ ] Sistema de notificaciones (email/Slack)
- [ ] Webhooks de ML (si disponible)
- [ ] Tests end-to-end

### Fase 6: Producción (Semana 6-7)
- [ ] Deploy en servidor (Railway/Render/DigitalOcean)
- [ ] Setup de monitoring (Sentry + Prometheus)
- [ ] Backup de BD automatizado
- [ ] Documentación completa
- [ ] Capacitación

### Fase 7: Optimización (Semana 8+)
- [ ] Fine-tuning de similarity thresholds
- [ ] Optimización de costos de API
- [ ] A/B testing de estrategias de pricing
- [ ] Expansión a más productos
- [ ] Integración con sistema de gestión de precios

---

## 11. Costos Estimados Mensuales

### Infrastructure
- **PostgreSQL**: $15/mes (DigitalOcean Managed DB - 1GB)
- **Redis**: $10/mes (Railway/Render)
- **Server**: $20/mes (2GB RAM, 1 vCPU)
- **Total Infra**: ~$45/mes

### APIs
- **OpenAI**:
  - GPT-4o-mini: ~5000 requests/día × 30 días = 150k requests
  - Input: 150k × 500 tokens × $0.150/1M = $11.25
  - Output: 150k × 200 tokens × $0.600/1M = $18
  - Embeddings: 100 productos × 30 updates × $0.020/1M tokens = $0.06
  - **Subtotal**: ~$30/mes
  
- **Mercado Libre API**: Gratis (dentro de límites)
  
- **Total APIs**: ~$30/mes

### TOTAL ESTIMADO: ~$75-100/mes

### ROI Esperado
Si el sistema ayuda a:
- Optimizar precios de 50 productos
- Incremento de margen promedio: 3%
- Ventas mensuales: $50,000 MXN
- **Ganancia adicional**: $1,500 MXN/mes
- **ROI**: ~1,400% 🚀

---

## 12. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Rate limit de ML API | Alto | Cache agresivo, distribuir requests |
| Cambios en ML API | Alto | Abstracción en MCP server, versionado |
| Costos de OpenAI altos | Medio | Usar modelos pequeños, cache embeddings |
| Falsos positivos en matching | Medio | Threshold ajustable, revisión manual periódica |
| Competencia cambia precios post-scan | Bajo | Aumentar frecuencia en productos clave |

---

## 13. Mejoras Futuras

1. **ML Predictions**: Predecir cambios de precio de competencia
2. **Demand Forecasting**: Ajustar precios según demanda estimada
3. **Dynamic Pricing**: Auto-aplicar cambios (con límites)
4. **Multi-Marketplace**: Expandir a Amazon, Walmart, etc.
5. **Sentiment Analysis**: Analizar reviews de competencia
6. **Image Recognition**: Comparar fotos de productos similares
7. **Integration con ERP**: Sincronizar con sistema de inventario

---

## Próximos Pasos Inmediatos

1. ✅ **Revisar y aprobar este plan**
2. 🔜 **Obtener credenciales de Mercado Libre API**
3. 🔜 **Obtener API key de OpenAI**
4. 🔜 **Preparar catálogo de productos en CSV/JSON**
5. 🔜 **Setup de entorno de desarrollo**
6. 🔜 **Comenzar Fase 1: Foundation**

---

## Contacto y Soporte

Para dudas sobre la implementación o ajustes al plan:
- Revisar documentación de [Mercado Libre API](https://developers.mercadolibre.com.mx/)
- Revisar [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- Consultar [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Versión**: 1.0  
**Fecha**: Diciembre 2025  
**Autor**: AI Assistant + Louder Team
