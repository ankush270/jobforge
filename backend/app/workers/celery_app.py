"""Celery app configuration and background tasks."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "jobforge",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min hard limit
    task_soft_time_limit=300,  # 5 min soft limit
    worker_prefetch_multiplier=1,
    beat_schedule={
        "scrape-jobs-every-6h": {
            "task": "app.workers.tasks.scrape_all_sources",
            "schedule": 6 * 3600,
        },
        "check-follow-ups-hourly": {
            "task": "app.workers.tasks.check_pending_follow_ups",
            "schedule": 3600,
        },
        "detect-ghosted-daily": {
            "task": "app.workers.tasks.detect_ghosted_applications",
            "schedule": 86400,
        },
    },
)
