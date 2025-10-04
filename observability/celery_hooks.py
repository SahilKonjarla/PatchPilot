from celery.signals import task_prerun, task_postrun, task_failure
from observability.metrics import tasks_total, task_duration_seconds
import time

_task_start_time = {}

@task_prerun.connect
def before_task(sender=None, task_id=None, task=None, **kwargs):
    _task_start_time[task_id] = time.time()
    tasks_total.labels(name=sender.name, status="started").inc()

@task_postrun.connect
def after_task(sender=None, task_id=None, task=None, **kwargs):
    start = _task_start_time.pop(task_id, None)
    if start:
        task_duration_seconds.labels(name=sender.name, status="succeeded").observe(time.time() - start)
    tasks_total.labels(name=sender.name, status="success").inc()

@task_failure.connect
def on_failure(sender=None, task_id=None, exception=None, **kwargs):
    tasks_total.labels(name=sender.name, status="failed").inc()
