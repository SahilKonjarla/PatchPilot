import time
from observability.metrics import http_requests_total, request_latency_seconds

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        resp = self.get_response(request)
        elapsed = time.time() - start
        http_requests_total.labels(request.method, request.path).inc()
        request_latency_seconds.labels(request.path).observe(elapsed)
        return resp