from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ecommerce_logistics_engine",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    worker_prefetch_multiplier=1,  # Fair task distribution for IO-bound work
)
