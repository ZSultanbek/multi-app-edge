from django.http import JsonResponse
from django.urls import path

from .tasks import ping


def healthz(request):
    """Liveness endpoint. Deliberately does not touch the database: a health
    check that fails when postgres blips will restart-loop a healthy app."""
    return JsonResponse({"status": "ok"})


def readyz(request):
    """Readiness endpoint. This one DOES check the database, because an app
    that cannot reach its database is not ready to serve traffic."""
    from django.db import connection

    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return JsonResponse({"status": "ready"})
    except Exception as exc:  # noqa: BLE001 - surface the reason, do not hide it
        return JsonResponse({"status": "unready", "error": str(exc)}, status=503)


def index(request):
    return JsonResponse(
        {
            "app": "alpha",
            "mounted_at": request.META.get("HTTP_X_SCRIPT_NAME", "/"),
            "scheme_seen_by_django": request.scheme,
            "hint": "generated URLs below should carry the /alpha prefix",
            "self": request.build_absolute_uri("/"),
        }
    )


def enqueue(request):
    task = ping.delay()
    return JsonResponse({"queued": task.id})


urlpatterns = [
    path("", index),
    path("healthz", healthz),
    path("readyz", readyz),
    path("enqueue", enqueue),
]
