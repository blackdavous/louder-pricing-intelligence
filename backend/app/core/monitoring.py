"""
Prometheus monitoring and metrics collection.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
from time import time
from typing import Callable, Any

# API Metrics
api_requests_total = Counter(
    "louder_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"]
)

api_request_duration_seconds = Histogram(
    "louder_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"]
)

# ML Metrics
ml_searches_total = Counter(
    "louder_ml_searches_total",
    "Total Mercado Libre searches performed",
    ["status"]
)

ml_products_found = Histogram(
    "louder_ml_products_found",
    "Number of competitor products found per search",
    buckets=[0, 5, 10, 20, 50, 100, 200]
)

# Pricing Metrics
pricing_recommendations_total = Counter(
    "louder_pricing_recommendations_total",
    "Total pricing recommendations generated",
    ["confidence"]
)

pricing_recommendations_applied = Counter(
    "louder_pricing_recommendations_applied",
    "Total pricing recommendations applied"
)

price_change_amount = Histogram(
    "louder_price_change_amount",
    "Amount of price change in MXN",
    buckets=[-1000, -500, -100, -50, 0, 50, 100, 500, 1000]
)

# Database Metrics
db_query_duration_seconds = Histogram(
    "louder_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"]
)

db_connections_active = Gauge(
    "louder_db_connections_active",
    "Number of active database connections"
)

# Agent Metrics
agent_execution_duration_seconds = Histogram(
    "louder_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name", "status"]
)

agent_errors_total = Counter(
    "louder_agent_errors_total",
    "Total agent execution errors",
    ["agent_name", "error_type"]
)

# System Info
system_info = Info(
    "louder_system",
    "System information"
)


def track_time(metric: Histogram, labels: dict = None):
    """Decorator to track execution time of functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def track_agent_execution(agent_name: str):
    """Decorator to track agent execution metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                agent_errors_total.labels(
                    agent_name=agent_name,
                    error_type=type(e).__name__
                ).inc()
                raise
            finally:
                duration = time() - start_time
                agent_execution_duration_seconds.labels(
                    agent_name=agent_name,
                    status=status
                ).observe(duration)
        
        return wrapper
    return decorator


# Initialize system info
system_info.info({
    "app": "louder-pricing-intelligence",
    "version": "0.1.0"
})
