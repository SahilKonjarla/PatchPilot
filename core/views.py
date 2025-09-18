from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.http import JsonResponse, HttpResponse
from observability import metrics

# Create your views here.
def index(request):
    return JsonResponse({"ok": True, "routes": ["/healthz/", "/metrics/", "/webhook/"]})

def healthz(request):
    return JsonResponse({"status": "ok"})

def metrics_view(request):
    return HttpResponse(generate_latest(metrics.registry), content_type=CONTENT_TYPE_LATEST)

def webhook(request):
    # Stub: real HMAC verify + enqueue comes in M2
    return JsonResponse({"accepted": True}, status=202)
