# Louder Price Intelligence System

## 🚀 Inicio Rápido

### Requisitos Previos
- Docker y Docker Compose instalados
- Python 3.11+ (para desarrollo local sin Docker)
- PostgreSQL 14+ con extensión pgvector (si no usas Docker)

### 1. Configuración Inicial

```powershell
# Clonar el repositorio (o navegar a la carpeta del proyecto)
cd audiolouder

# Copiar archivo de variables de entorno
cp .env.example .env

# Editar .env con tus credenciales
notepad .env
```

### 2. Ejecutar con Docker (Recomendado)

```powershell
# Construir y levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Servicios disponibles:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:8501
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### 3. Ejecutar en Desarrollo Local

```powershell
# Instalar dependencias del backend
cd backend
pip install -r requirements.txt

# Ejecutar migraciones
alembic upgrade head

# Iniciar el servidor
uvicorn app.main:app --reload --port 8000

# En otra terminal, ejecutar frontend
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Estructura del Proyecto

```
audiolouder/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/       # Endpoints de la API
│   │   │   │   ├── products.py
│   │   │   │   ├── scans.py
│   │   │   │   ├── pricing.py
│   │   │   │   └── analytics.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   └── config.py        # Configuración
│   │   ├── models/               # Modelos SQLAlchemy
│   │   │   ├── product.py
│   │   │   ├── competitor_product.py
│   │   │   ├── price_snapshot.py
│   │   │   ├── pricing_recommendation.py
│   │   │   └── scan_log.py
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── agents/               # Sistema de agentes (LangGraph)
│   │   ├── tasks/                # Tareas Celery
│   │   ├── database.py
│   │   └── main.py
│   ├── alembic/                  # Migraciones de DB
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                    # Streamlit dashboard
│   ├── requirements.txt
│   └── Dockerfile
├── mcp_servers/
│   ├── mercadolibre/             # MCP Server para ML API
│   └── analytics/                # MCP Server para Analytics
├── scripts/
│   └── import_catalog.py         # Script para importar productos
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# Database
DATABASE_URL=postgresql://louder_user:louder_password@localhost:5432/louder_pricing

# Redis
REDIS_URL=redis://localhost:6379/0

# APIs
MERCADOLIBRE_APP_ID=your_ml_app_id
MERCADOLIBRE_CLIENT_SECRET=your_ml_client_secret
OPENAI_API_KEY=your_openai_api_key

# App
DEBUG=true
PROJECT_NAME=Louder Price Intelligence
VERSION=1.0.0
```

---

## 📊 Uso del Sistema

### 1. Importar Catálogo de Productos

```powershell
# Preparar archivo CSV
# Formato: sku,nombre,categoria,precio_actual,costo,descripcion

# Ejecutar script de importación
python scripts/import_catalog.py --file catalogo.csv
```

### 2. Trigger un Scan Manual

```powershell
# Vía API
curl -X POST http://localhost:8000/api/scans/trigger \
  -H "Content-Type: application/json" \
  -d '{"scan_type": "full"}'

# O desde el frontend en http://localhost:8501
```

### 3. Ver Recomendaciones

- Accede al dashboard en http://localhost:8501
- Navega a la sección "💰 Pricing"
- Revisa y aplica recomendaciones

---

## 🧪 Testing

```powershell
# Ejecutar tests
cd backend
pytest

# Con coverage
pytest --cov=app tests/
```

---

## 🚢 Deployment

### Opción 1: Docker Compose en Servidor

```powershell
# En el servidor de producción
docker-compose -f docker-compose.prod.yml up -d
```

### Opción 2: Servicios Individuales

- **Backend**: Deploy en Railway, Render, DigitalOcean
- **PostgreSQL**: Managed database (DigitalOcean, AWS RDS)
- **Redis**: Redis Cloud, AWS ElastiCache
- **Frontend**: Streamlit Cloud, Railway

---

## 📚 API Endpoints

### Productos
- `GET /api/products/` - Lista productos
- `POST /api/products/` - Crear producto
- `GET /api/products/{id}` - Detalle de producto
- `PUT /api/products/{id}` - Actualizar producto
- `POST /api/products/{id}/scan` - Scan on-demand

### Scans
- `GET /api/scans/` - Lista de scans
- `POST /api/scans/trigger` - Ejecutar scan

### Pricing
- `GET /api/pricing/recommendations` - Lista recomendaciones
- `POST /api/pricing/recommendations/{id}/apply` - Aplicar recomendación

### Analytics
- `GET /api/analytics/overview` - Vista general
- `GET /api/analytics/product/{id}` - Analytics de producto
- `GET /api/analytics/price-trends/{id}` - Tendencias de precio

**Documentación completa:** http://localhost:8000/docs

---

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📝 Próximos Pasos

- [ ] Obtener credenciales de Mercado Libre API
- [ ] Obtener API Key de OpenAI
- [ ] Preparar catálogo de productos
- [ ] Implementar MCP Servers
- [ ] Implementar sistema de agentes
- [ ] Configurar Celery para tareas programadas
- [ ] Testing completo
- [ ] Deploy a producción

---

## 📄 Licencia

Este proyecto es propiedad de Louder Audio.

---

## 💬 Soporte

Para dudas o problemas, contactar al equipo de desarrollo.
