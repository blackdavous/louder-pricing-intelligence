from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
import time

from .core.config import settings
from .core.logging import get_logger
from .core.monitoring import (
    api_requests_total,
    api_request_duration_seconds,
    system_info,
)
from .database import init_db
from .api import api_router

# Initialize structured logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events para startup y shutdown.
    """
    # Startup
    logger.info(
        "Application starting",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )
    
    if settings.INIT_DB_ON_STARTUP:
        logger.info("Initializing database")
        init_db()
        logger.info("Database initialized successfully")
    
    # Update system info metric
    system_info.info({
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    })
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de monitoreo de precios competitivos para Louder Audio",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Prometheus metrics middleware
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """
    Track request metrics with Prometheus.
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    api_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    api_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    # Log request
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_seconds=round(duration, 4)
    )
    
    return response


# Mount Prometheus metrics endpoint
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    logger.info("Prometheus metrics endpoint enabled at /metrics")


# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """
    Root endpoint - health check.
    """
    return {
        "message": "Louder Price Intelligence API",
        "version": settings.VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint para monitoring.
    """
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Verificar conexión real
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
