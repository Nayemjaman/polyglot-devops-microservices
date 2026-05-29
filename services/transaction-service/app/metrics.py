import threading
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


REQUESTS: dict[tuple[str, str, str], int] = defaultdict(int)
LATENCY_SECONDS: dict[tuple[str, str], dict[str, float]] = defaultdict(
    lambda: {"count": 0.0, "sum": 0.0}
)
LOCK = threading.Lock()


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path or request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        started_at = time.monotonic()
        response = await call_next(request)
        elapsed_seconds = time.monotonic() - started_at
        route = _route_label(request)
        method = request.method
        status = str(response.status_code)

        with LOCK:
            REQUESTS[(method, route, status)] += 1
            summary = LATENCY_SECONDS[(method, route)]
            summary["count"] += 1
            summary["sum"] += elapsed_seconds

        return response


def render_metrics(service_name: str) -> str:
    lines = [
        "# HELP app_http_requests_total Total HTTP requests handled by the service.",
        "# TYPE app_http_requests_total counter",
    ]

    with LOCK:
        for (method, route, status), value in sorted(REQUESTS.items()):
            lines.append(
                'app_http_requests_total{service="%s",method="%s",route="%s",status="%s"} %d'
                % (service_name, method, route, status, value)
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
                service_name,
                method,
                route,
            )
            lines.append(f"app_http_request_duration_seconds_count{{{labels}}} {count}")
            lines.append(f"app_http_request_duration_seconds_sum{{{labels}}} {total:.6f}")

    return "\n".join(lines) + "\n"
