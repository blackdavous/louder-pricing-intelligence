"""
Celery configuration
"""
from celery import Celery
from celery.schedules import crontab

from core.config import settings


# Create Celery app
celery_app = Celery(
    "louder",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.scan_tasks",
        "tasks.pricing_tasks",
        "tasks.notification_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Full scan daily at 2 AM
    "full-scan-daily": {
        "task": "tasks.scan_tasks.run_full_scan",
        "schedule": crontab(hour=2, minute=0),
    },
    # Priority products scan every 6 hours
    "priority-scan-6h": {
        "task": "tasks.scan_tasks.run_priority_scan",
        "schedule": crontab(hour="*/6", minute=0),
    },
    # Flash updates for products in promotion every hour
    "flash-scan-hourly": {
        "task": "tasks.scan_tasks.run_flash_scan",
        "schedule": crontab(hour="*", minute=0),
    },
    # Daily pricing analysis at 4:30 AM
    "daily-pricing-analysis": {
        "task": "tasks.pricing_tasks.run_daily_analysis",
        "schedule": crontab(hour=4, minute=30),
    },
    # Cache cleanup daily at 1 AM
    "cleanup-cache": {
        "task": "tasks.maintenance_tasks.cleanup_cache",
        "schedule": crontab(hour=1, minute=0),
    },
}
