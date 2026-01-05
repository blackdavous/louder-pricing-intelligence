"""
Structured logging configuration for MLOps best practices.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import EventDict, WrappedLogger

from .config import settings


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log entries."""
    event_dict["app"] = settings.PROJECT_NAME
    event_dict["environment"] = settings.ENVIRONMENT
    event_dict["version"] = settings.VERSION
    return event_dict


def setup_logging() -> None:
    """
    Configure structured logging with MLOps best practices.
    
    Outputs JSON logs in production, pretty-printed logs in development.
    Includes request IDs, user context, and performance metrics.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_app_context,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.ENVIRONMENT == "production":
        # JSON logging for production (easy to parse by log aggregators)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty printing for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Initialize logging on module import
setup_logging()
