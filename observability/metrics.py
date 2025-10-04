from prometheus_client import Counter, Histogram, CollectorRegistry


registry = CollectorRegistry()

app_startups_total = Counter(
    "patchpilot_app_startups_total", "Total app startups", registry=registry
)
http_requests_total = Counter(
    "patchpilot_http_requests_total", "HTTP requests by method+endpoint",
    ["method", "endpoint"], registry=registry
)
request_latency_seconds = Histogram(
    "patchpilot_request_latency_seconds", "Latency by endpoint",
    ["endpoint"], registry=registry
)

# --- Celery task metrics ---
tasks_total = Counter(
    "patchpilot_tasks_total",
    "Total number of Celery tasks executed (by name + status)",
    ["name", "status"],
    registry=registry,
)

task_duration_seconds = Histogram(
    "patchpilot_task_duration_seconds",
    "Duration of Celery tasks in seconds",
    ["name"],
    registry=registry,
)

app_startups_total.inc()
