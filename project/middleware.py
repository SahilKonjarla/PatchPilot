import time, logging
from observability.metrics import http_requests_total, request_latency_seconds

logger = logging.getLogger(__name__)

class MetricsMiddleware:
    """
    Django middleware that tracks HTTP request metrics for Prometheus.

    Captures:
    - Total number of requests, labeled by method and path
    - Latency (seconds) per path
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        try:
            response = self.get_response(request)
            return response
        finally:
            elapsed = time.time() - start

            # Normalize path to avoid exploding labels (optional)
            path = request.path or "unknown"

            try:
                http_requests_total.labels(request.method, path).inc()
                request_latency_seconds.labels(path).observe(elapsed)
            except Exception as e:
                # Defensive logging: metrics failures should never break requests
                logger.warning(f"[MetricsMiddleware] Failed to record metrics for {path}: {e}")

            logger.debug(
                f"[MetricsMiddleware] {request.method} {path} took {elapsed:.4f}s"
            )
