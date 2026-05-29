import threading
import time
from collections import defaultdict

from django.http import HttpResponse


REQUESTS = defaultdict(int)
LATENCY_SECONDS = defaultdict(lambda: {"count": 0.0, "sum": 0.0})
LOCK = threading.Lock()
SERVICE_NAME = "auth-service"


class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/metrics":
            return self.get_response(request)

        started_at = time.monotonic()
        response = self.get_response(request)
        elapsed_seconds = time.monotonic() - started_at

        route = getattr(getattr(request, "resolver_match", None), "route", None) or request.path
        key = (request.method, route, str(response.status_code))
        with LOCK:
            REQUESTS[key] += 1
            summary = LATENCY_SECONDS[(request.method, route)]
            summary["count"] += 1
            summary["sum"] += elapsed_seconds

        return response


def metrics_view(_request):
    lines = [
        "# HELP app_http_requests_total Total HTTP requests handled by the service.",
        "# TYPE app_http_requests_total counter",
    ]
    with LOCK:
        for (method, route, status), value in sorted(REQUESTS.items()):
            lines.append(
                'app_http_requests_total{service="%s",method="%s",route="%s",status="%s"} %d'
                % (SERVICE_NAME, method, route, status, value)
            )

        lines.extend(
            [
                "# HELP app_http_request_duration_seconds HTTP request latency summary.",
                "# TYPE app_http_request_duration_seconds summary",
            ]
        )
        for (method, route), summary in sorted(LATENCY_SECONDS.items()):
            count = int(summary["count"])
            total = summary["sum"]
            labels = 'service="%s",method="%s",route="%s"' % (
                SERVICE_NAME,
                method,
                route,
            )
            lines.append(f"app_http_request_duration_seconds_count{{{labels}}} {count}")
            lines.append(f"app_http_request_duration_seconds_sum{{{labels}}} {total:.6f}")

    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; version=0.0.4")
