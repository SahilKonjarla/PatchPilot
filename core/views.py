import hmac, hashlib, json, os, sys, logging

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache

from services.queue.tasks import review_pull_request
from observability import metrics

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    """Index route: lists available endpoints."""
    return JsonResponse({"ok": True, "routes": ["/healthz/", "/metrics/", "/webhook/"]})

def healthz(request):
    """Health check endpoint for liveness probes."""
    return JsonResponse({"status": "ok"})

def metrics_view(request):
    """Prometheus metrics endpoint."""
    return HttpResponse(generate_latest(metrics.registry), content_type=CONTENT_TYPE_LATEST)

@csrf_exempt
def webhook(request):
    """
        GitHub webhook endpoint.
        - Verifies HMAC signature.
        - Filters non-PR events.
        - Deduplicates by delivery ID.
        - Enqueues Celery task for review.
    """

    if request.method != "POST":
        return HttpResponse(status=405)

    if not _verify_signature(request):
        print("[Webhook] Signature invalid", file=sys.stderr, flush=True)
        return HttpResponse("Invalid signature", status=401)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        logger.error("[Webhook] Failed to parse JSON body.")
        return HttpResponse("Invalid JSON", status=400)

    action = payload.get("action")
    if not _is_pr_event(payload):
        logger.debug("[Webhook] Ignored event: %s", action)
        return JsonResponse({"ignored": True}, status=202)

    logger.info("[Webhook] Passed PR filter. Action=%s", action)

    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if delivery_id:
        cache_key = f"pp:delivery:{delivery_id}"
        if cache.get(cache_key):
            logger.info("[Webhook] Duplicate delivery ignored: %s", delivery_id)
            return JsonResponse({"duplicate": True}, status=202)
        cache.set(cache_key, True, timeout=600)
    try:

        pr = payload["pull_request"]
        repo_full = payload["repository"]["full_name"]
        pr_number = pr["number"]
        head_sha = pr["head"]["sha"]
        installation_id = payload.get("installation", {}).get("id")

        # Enqueue task (heavy work happens off-request)
        logger.info("[Webhook] Enqueuing PR #%s in %s", pr_number, repo_full)
        result = review_pull_request.delay(repo_full, pr_number, head_sha, installation_id)
        logger.info("[Webhook] Task enqueued: %s", result.id)
        return JsonResponse({"enqueued": True}, status=202)
    except Exception as e:
        logger.error("[Webhook] Failed to enqueue task: %s", e, exc_info=True)
        return HttpResponse("Internal server error", status=500)

def _verify_signature(request) -> bool:
    """Verify GitHub webhook signature using X-Hub-Signature-256 header."""
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not sig:
        return False
    digest = hmac.new(WEBHOOK_SECRET, msg=request.body, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", sig)

def _is_pr_event(payload: dict) -> bool:
    """
        Return True if the event is a PR action we care about.
        Actions: opened, synchronize, reopened, review_requested, ready_for_review.
    """

    return (
            payload.get("action") in {
        "opened",
        "synchronize",
        "reopened",
        "review_requested",
        "ready_for_review",
    }
            and "pull_request" in payload
    )
