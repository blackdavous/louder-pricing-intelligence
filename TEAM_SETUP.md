# 🚀 Guía para Compañeros de Equipo

Esta guía es para **Edgar, Gustavo y Carlos** (o cualquier miembro del equipo) que quiera probar el proyecto.

---

## ⚠️ IMPORTANTE: Seguridad de Credenciales

- **NUNCA subas tu archivo `.env` a Git**
- Cada persona debe tener su propia API key de OpenAI
- El archivo `.env` está protegido automáticamente por `.gitignore`
- Solo compartimos el template `.env.example` en Git

---

## 📋 Requisitos Previos

✅ Python 3.11+ instalado  
✅ Git instalado  
✅ Cuenta de OpenAI (crear en https://platform.openai.com)  
✅ Editor de texto (VS Code, Notepad++, etc.)  

---

## 🔧 Instalación Rápida (5 minutos)

### Paso 1: Clonar el Proyecto

```bash
# Clona el repositorio
git clone https://github.com/byed2015/louder-pricing-intelligence.git
cd louder-pricing-intelligence
```

### Paso 2: Crear tu archivo `.env` personal

```bash
# Windows PowerShell
Copy-Item .env.example .env

# O simplemente copia el archivo manualmente en el explorador
```

### Paso 3: Obtener tu OpenAI API Key

1. Ve a https://platform.openai.com/api-keys
2. Inicia sesión o crea cuenta (si no tienes)
3. Click en **"Create new secret key"**
4. Nombre sugerido: `Louder-Testing`
5. **Copia la key** (se muestra solo una vez - guárdala bien)

La key se ve así: `sk-proj-aBc123XyZ...` (64+ caracteres)

### Paso 4: Configurar tu `.env`

Abre el archivo `.env` que acabas de crear y actualiza:

```bash
# ⚠️ REQUERIDO - Pega aquí tu API key de OpenAI
OPENAI_API_KEY=sk-proj-tu-key-real-aqui

# Estos dejarlos como están por ahora
ML_API_ENABLED=False
ML_ACCESS_TOKEN=
ML_CLIENT_ID=
ML_CLIENT_SECRET=
```

**⚠️ Guardar el archivo!**

### Paso 5: Instalar Dependencias

```bash
# Opción 1: Instalar UV (package manager rápido)
pip install uv
uv pip install -r requirements.txt --system

# Opción 2: Usar pip tradicional
pip install -r requirements.txt
```

**Tiempo estimado**: 1-2 minutos

---

## ✅ Verificar que Funciona

Ejecuta el demo principal:

```bash
python scripts/demo_pivot_product.py
```

**Si ves esto, ¡todo funciona!**:
```
======================================================================
  PRICING PIPELINE - Pivot Product Mode
======================================================================

🎯 Pivot Product: Louder YPO-900RED
   URL: https://www.mercadolibre.com.mx/...

⏳ Running pipeline (5 steps + pivot extraction)...
   0. Extract pivot product specifications
   ✅ Extracted: {'brand': 'Louder', 'model': 'YPO-900RED', ...}
   
   1. Generate search strategy (LLM)
   ✅ Generated 3 targeted searches
   
   2. Scrape Mercado Libre (parallel)
   ✅ Found 47 products
   
   3. Filter and match products (LLM)
   ✅ Filtered to 8 comparable products
   
   4. Calculate statistics
   ✅ Stats ready
   
   5. Generate pricing recommendation (LLM)
   ✅ Recommendation generated

💰 RECOMMENDED PRICE: $1,899 MXN
   Min: $1,499 | Max: $2,199 | Avg: $1,850

✅ Demo completed!
```

---

## 🧪 Probar con Diferentes Productos

### Modo 1: URL de Mercado Libre (Recomendado)

Edita `scripts/demo_pivot_product.py` línea 10:

```python
pivot_product_url = "https://www.mercadolibre.com.mx/p/MLM12345678"  # Tu URL
```

### Modo 2: Descripción Simple (Legacy)

```bash
python scripts/demo_new_pipeline.py
```

---

## 🔍 Problemas Comunes

### ❌ Error: "The api_key client option must be set"

**Causa**: No configuraste tu OpenAI API key

**Solución**:
1. Verifica que existe `.env` (no `.env.example`)
2. Abre `.env` y verifica que `OPENAI_API_KEY` tiene tu key
3. La key debe empezar con `sk-...`
4. No debe tener espacios ni comillas

### ❌ Error: "Module not found: openai"

**Causa**: Dependencias no instaladas

**Solución**:
```bash
pip install -r requirements.txt
```

### ❌ Error: "HTTPError 403 Forbidden"

**Causa**: Mercado Libre bloqueó la petición (rate limiting)

**Solución**:
- Espera 30 segundos y vuelve a intentar
- Reduce el número de búsquedas en el demo

### ❌ Error: "Insufficient quota" (OpenAI)

**Causa**: Se acabó tu crédito de OpenAI

**Solución**:
1. Ve a https://platform.openai.com/account/billing
2. Agrega método de pago
3. OpenAI da $5 USD gratis para nuevas cuentas

---

## 💰 ¿Cuánto Cuesta Usarlo?

El sistema hace 3 llamadas a OpenAI por análisis:
- **SearchStrategyAgent**: gpt-4o-mini = ~$0.0001 USD
- **ProductMatchingAgent**: gpt-4o-mini = ~$0.0002 USD
- **PricingIntelligenceAgent**: gpt-4o = ~$0.0010 USD

**Total por análisis**: ~$0.0013 USD (0.013 centavos)

**Para 100 análisis de prueba**: ~$0.13 USD

**Crédito gratis de OpenAI**: $5 USD = ~3,800 análisis

---

## 📂 Estructura del Proyecto

```
louder-pricing-intelligence/
│
├── .env.example          # ← Template (este SÍ está en Git)
├── .env                  # ← TU archivo personal (NO está en Git)
├── .gitignore            # ← Protege .env automáticamente
│
├── scripts/
│   ├── demo_pivot_product.py    # ← Demo principal
│   └── demo_new_pipeline.py     # ← Demo alternativo
│
├── backend/app/
│   ├── agents/                  # Lógica de los agentes LLM
│   │   ├── search_strategy.py
│   │   ├── product_matching.py
│   │   └── pricing_intelligence.py
│   └── mcp_servers/mercadolibre/
│       ├── scraper.py           # Web scraping ML
│       └── stats.py             # Estadísticas
│
└── docs/                        # Documentación técnica
```

---

## 🤝 Colaborar en el Proyecto

### Si encuentras un bug:

1. Anota el error completo
2. Comparte el comando que ejecutaste
3. Avisa al equipo

### Si quieres mejorar el código:

```bash
# Crea una branch nueva
git checkout -b feature/mi-mejora

# Haz tus cambios
# ...

# Commit y push
git add .
git commit -m "feat: descripción de tu mejora"
git push origin feature/mi-mejora
```

---

## ✉️ Contacto

Si tienes problemas después de seguir esta guía:
- Revisa la sección de "Problemas Comunes"
- Contacta al equipo principal del proyecto

---

## ✅ Checklist Final

Antes de reportar problemas, verifica:

- [ ] Python 3.11+ instalado (`python --version`)
- [ ] Proyecto clonado correctamente
- [ ] Archivo `.env` existe (no `.env.example`)
- [ ] `OPENAI_API_KEY` configurada en `.env`
- [ ] La API key es válida (no expirada)
- [ ] Dependencias instaladas (`pip list | grep openai`)
- [ ] Internet funcionando

---

**¡Ya estás listo para probar el sistema!** 🎉

Para más detalles técnicos, consulta:
- [NEW_AGENT_ARCHITECTURE.md](docs/NEW_AGENT_ARCHITECTURE.md)
- [README.md](README.md)
