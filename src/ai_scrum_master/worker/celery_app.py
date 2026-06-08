import os
from celery import Celery

# Configure Redis connection strings (using default localhost for local dev without docker, and redis service name for docker)
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
redis_result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "ai_scrum_worker",
    broker=redis_url,
    backend=redis_result_backend,
    include=["ai_scrum_master.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "2"))
)
