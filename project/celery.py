import os
import logging
from celery import Celery
import observability.celery_hooks

# Ensure Django settings are loaded before Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# Set up logging for Celery context
logger = logging.getLogger(__name__)

# Initialize Celery application
app = Celery("patchpilot")

# Broker and backend configuration (default: Redis local)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app.conf.broker_url = redis_url
app.conf.result_backend = redis_url

# Optional: common Celery reliability settings
app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    task_retry_backoff=True,
    task_max_retries=5,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_annotations={"*": {"max_retries": 3}},
)

# Auto-discover tasks across Django apps
app.autodiscover_tasks()

logger.info("[Celery] PatchPilot worker initialized with broker: %s", redis_url)
