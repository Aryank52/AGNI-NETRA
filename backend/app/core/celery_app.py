import ssl

from celery import Celery
from backend.app.core.config import settings


REDIS_SSL_OPTIONS = {
    "ssl_cert_reqs": ssl.CERT_REQUIRED,
}


celery_app = Celery(
    "agni_netra_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.app.tasks.maintenance_tasks"
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,

    # Upstash Redis TLS
    broker_use_ssl=REDIS_SSL_OPTIONS,
    redis_backend_use_ssl=REDIS_SSL_OPTIONS,
)
