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

app_startups_total.inc()
