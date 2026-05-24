import uuid
import logging
import time


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.monotonic()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        elapsed_ms = round((time.monotonic() - started_at) * 1000)
        logging.getLogger("core.request").info(
            "http request",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "request_id": request_id,
            },
        )
        return response
