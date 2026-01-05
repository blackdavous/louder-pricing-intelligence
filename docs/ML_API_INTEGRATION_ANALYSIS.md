# Análisis de Integración - ML API + Web Scraping

## 🔍 Resultados de las Pruebas

### Estado del Token ✅
- **Token renovado exitosamente**
- User: ROAL2642779 (ID: 491630401)
- Válido por: 6 horas
- Auto-renovación disponible con refresh_token

### Tests de Conectividad

| Test | Estado | Notas |
|------|--------|-------|
| Token Validity | ✅ PASS | `/users/me` funciona |
| Search Endpoint | ❌ FAIL (403) | Acceso prohibido - cuenta puede estar limitada |
| Categories | ✅ PASS | `/categories` funciona sin problemas |

---

## 💡 Conclusión Clave

**La API tiene restricciones 403 en búsquedas**, probablemente porque:
1. Cuenta nueva sin historial de ventas
2. Rate limiting preventivo de Mercado Libre
3. Scopes insuficientes para búsquedas públicas

**PERO** el notebook de Gustavo funciona perfecto porque:
- ✅ Hace web scraping del HTML público
- ✅ No requiere autenticación
- ✅ Extrae datos directamente del frontend
- ✅ Más robusto para este caso de uso

---

## 🎯 Estrategia Híbrida Recomendada

### Arquitectura de 3 Capas

```
┌─────────────────────────────────────────────────┐
│         MarketResearchAgent                     │
│      (Orquestador de búsqueda)                 │
└──────────────────┬──────────────────────────────┘
                   ↓
         ┌─────────┴─────────┐
         │   Data Strategy   │
         │   Selector        │
         └─────────┬─────────┘
                   ↓
    ┌──────────────┼──────────────┐
    ↓              ↓              ↓
┌───────┐    ┌──────────┐   ┌──────────┐
│ Layer 1│    │ Layer 2  │   │ Layer 3  │
│Web Scrp│    │ ML API   │   │ Cache    │
│ PRIMARY│    │ FALLBACK │   │ OPTIONAL │
└────────┘    └──────────┘   └──────────┘
```

### Layer 1: Web Scraper (PRIMARY)
**Basado en el notebook de Gustavo**

✅ **Ventajas:**
- Funciona sin restricciones
- Extrae datos ricos del HTML
- No consume rate limits
- Análisis estadístico integrado (IQR)

📝 **Implementación:**
```python
# backend/app/mcp_servers/mercadolibre/scraper.py
class MLWebScraper:
    def search_products_html(query: str) -> List[Offer]:
        """Extrae productos del HTML (notebook logic)"""
        # 1. Extract __PRELOADED_STATE__
        # 2. Fallback to JSON-LD
        # 3. Filter by product matching
        # 4. Apply IQR outlier detection
```

### Layer 2: ML API (FALLBACK)
**Para endpoints que SÍ funcionan**

✅ **Endpoints disponibles:**
- `/users/me` - Info de usuario
- `/categories` - Categorías
- `/items/{id}` - Detalles de producto (si tenemos ID)

❌ **Endpoints bloqueados:**
- `/sites/MLM/search` - 403 Forbidden

📝 **Uso limitado:**
```python
# Solo para obtener categorías y detalles específicos
async def get_category_id(category_name: str) -> str:
    """Usar API para mapear categorías"""
    
async def get_item_details(item_id: str) -> dict:
    """Si tenemos un ID, obtener detalles completos"""
```

### Layer 3: Cache (OPTIONAL)
**Redis para evitar re-scrapear**

```python
# Cache por 6 horas
cache_key = f"ml:search:{query_hash}"
if cached := redis.get(cache_key):
    return cached
```

---

## 🚀 Plan de Implementación

### Fase 1: Migrar Lógica del Notebook ✅ PRIORITARIO

**Archivos a crear/actualizar:**

1. **`backend/app/mcp_servers/mercadolibre/scraper.py`**
   - Clase `MLWebScraper` con toda la lógica del notebook
   - Métodos: `extract_preloaded_state`, `extract_jsonld`, `build_offers`

2. **`backend/app/mcp_servers/mercadolibre/models.py`**
   - Dataclasses: `IdentifiedProduct`, `Offer`, `PriceStatistics`
   - Funciones de normalización y matching

3. **`backend/app/mcp_servers/mercadolibre/stats.py`**
   - Análisis estadístico (IQR, percentiles, outliers)
   - Funciones del notebook: `percentile`, `iqr_bounds`, `summarize_offers`

4. **Actualizar `backend/app/mcp_servers/mercadolibre/server.py`**
   - Integrar `MLWebScraper` como método principal
   - Mantener `MercadoLibreClient` para endpoints que funcionan

### Fase 2: Integrar con Agentes

**Actualizar `backend/app/agents/market_research.py`:**

```python
async def execute_searches(self, state: MarketResearchState):
    """
    Usa web scraper en lugar de API search.
    """
    from app.mcp_servers.mercadolibre.scraper import MLWebScraper
    
    scraper = MLWebScraper()
    
    for query in state["search_queries"]:
        # Use scraper instead of API
        result = await scraper.search_products_html(
            query=" ".join(query.keywords)
        )
        all_results.extend(result["offers"])
    
    state["raw_results"] = all_results
    return state
```

### Fase 3: Token Management

**Para endpoints que SÍ funcionan (categorías, detalles):**

```python
# backend/app/mcp_servers/mercadolibre/token_manager.py
class MLTokenManager:
    def __init__(self):
        self.token_path = "ml_token.json"
        self.refresh_threshold = 3600  # Renovar 1h antes
    
    async def get_valid_token(self) -> str:
        """Auto-renovar si está por expirar"""
        token = self.load_token()
        if self.is_near_expiry(token):
            token = await self.refresh_token()
        return token["access_token"]
```

---

## 📋 Checklist de Migración

### Inmediato (Hoy)
- [x] Probar token ML
- [x] Identificar limitaciones (403 en search)
- [ ] Extraer código del notebook a módulos Python
- [ ] Crear `scraper.py` con lógica del notebook
- [ ] Tests unitarios del scraper

### Corto Plazo (Esta Semana)
- [ ] Integrar scraper con `MarketResearchAgent`
- [ ] Agregar logging detallado
- [ ] Implementar token auto-renewal
- [ ] Cache con Redis (opcional)
- [ ] Tests end-to-end

### Mediano Plazo (Próximas 2 Semanas)
- [ ] Monitoring de rate limits (scraping)
- [ ] Retry logic con exponential backoff
- [ ] User-agent rotation (evitar detección)
- [ ] Proxy support (si es necesario)
- [ ] Dashboard de métricas

---

## ⚠️ Consideraciones Importantes

### Web Scraping - Buenas Prácticas

```python
# 1. Respetar robots.txt
# 2. Rate limiting (1-2 requests por segundo)
time.sleep(random.uniform(1.0, 2.0))

# 3. User-Agent realista (ya implementado en notebook)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept-Language": "es-MX,es;q=0.9"
}

# 4. Manejo de errores
try:
    response = session.get(url, timeout=25)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        # Backoff exponencial
```

### Prevención de Ban

1. **Rate Limiting:**
   - Max 30-60 requests/minuto
   - Pausas aleatorias entre requests

2. **Session Persistence:**
   - Reusar sesión HTTP (ya en notebook)
   - Cookies persistence

3. **Monitoring:**
   - Log todos los status codes
   - Alert si detectamos bloqueos

---

## 🎉 Conclusión

**Mejor estrategia para tu proyecto:**

```
✅ USAR Web Scraping (notebook) como PRINCIPAL
✅ API solo para categorías y detalles de items
✅ Token management automático
✅ Cache para optimizar
❌ NO usar /search de API (está bloqueado)
```

**Próximo paso:**
Migrar el código del notebook a `backend/app/mcp_servers/mercadolibre/scraper.py`

¿Procedemos con la migración del notebook a módulos Python del backend?
