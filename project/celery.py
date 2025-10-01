import os
import logging
from celery import Celery

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
    task_track_started=True,   # Track when a task starts (not just queued)
    task_acks_late=True,       # Don’t ack until task completes → prevents lost tasks
    worker_prefetch_multiplier=1,  # Ensures fair scheduling across workers
    task_default_retry_delay=10,   # Default retry delay (s)
    task_annotations={"*": {"max_retries": 3}},  # Retry policy for all tasks
)

# Auto-discover tasks across Django apps
app.autodiscover_tasks()

logger.info("[Celery] PatchPilot worker initialized with broker: %s", redis_url)
