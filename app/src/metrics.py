import os

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

VERSION = os.environ.get("APP_VERSION", "dev")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests served, by method, route, status, and version.",
    labelnames = ["method","route","status","version"],
)


BUILD_INFO = Gauge(
    "parcelpost_build_info",
    "Build information for the running app. The value is always 1.",
    labelnames=["version"],
)

BUILD_INFO.labels(version=VERSION).set(1)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        response = await call_next(request)
        route = request.scope.get("route")
        route_path = route.path if route is not None else "unmatched"
        REQUEST_COUNT.labels(
            method=request.method,
            route=route_path,
            status=str(response.status_code),
            version=VERSION,
        ).inc()
        return response


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
