import hmac, hashlib, json, os
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from services.queue.tasks import review_pull_request
from observability import metrics
import sys

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()

# Create your views here.
def index(request):
    return JsonResponse({"ok": True, "routes": ["/healthz/", "/metrics/", "/webhook/"]})

def healthz(request):
    return JsonResponse({"status": "ok"})

def metrics_view(request):
    return HttpResponse(generate_latest(metrics.registry), content_type=CONTENT_TYPE_LATEST)

@csrf_exempt
def webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    if not _verify_signature(request):
        print("[Webhook] Signature invalid", file=sys.stderr, flush=True)
        return HttpResponse("Invalid signature", status=401)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        print("[Webhook] Invalid JSON", file=sys.stderr, flush=True)
        return HttpResponse("Invalid JSON", status=400)

    # Ignore non-PR events early
    if not _is_pr_event(payload):
        print(f"[Webhook] Ignored event: {payload.get('action')}", file=sys.stderr, flush=True)
        return JsonResponse({"ignored": True}, status=202)

    print("[Webhook] Passed PR event filter", file=sys.stderr, flush=True)

    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if delivery_id:
        cache_key = f"pp:delivery:{delivery_id}"
        if cache.get(cache_key):
            print("[Webhook] Duplicate delivery ignored", file=sys.stderr, flush=True)
            return JsonResponse({"duplicate": True}, status=202)
        cache.set(cache_key, True, timeout=600)

    pr = payload["pull_request"]
    repo_full = payload["repository"]["full_name"]  # e.g., "user/repo"
    pr_number = pr["number"]
    head_sha = pr["head"]["sha"]
    installation_id = payload.get("installation", {}).get("id")

    # Enqueue task (heavy work happens off-request)
    print(f"[Webhook] Enqueuing PR #{pr_number} in {repo_full}", file=sys.stderr, flush=True)
    result = review_pull_request.delay(repo_full, pr_number, head_sha, installation_id)
    print(f"[Webhook] Task enqueued: {result.id}", file=sys.stderr, flush=True)
    return JsonResponse({"enqueued": True}, status=202)

def _verify_signature(request) -> bool:
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not sig:
        return False
    digest = hmac.new(WEBHOOK_SECRET, msg=request.body, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", sig)

def _is_pr_event(payload: dict) -> bool:
    return (
        payload.get("action") in {"opened", "synchronize", "reopened", "review_requested", "ready_for_review"}
        and "pull_request" in payload
    )

