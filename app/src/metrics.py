import os
import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

VERSION = os.environ.get("APP_VERSION", "dev")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests served, by method, route, status, and version.",
    labelnames = ["method","route","status","version"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds, by method, route, and version.",
    labelnames=["method", "route", "version"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
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
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        route = request.scope.get("route")
        route_path = route.path if route is not None else "unmatched"
        REQUEST_COUNT.labels(
            method=request.method,
            route=route_path,
            status=str(response.status_code),
            version=VERSION,
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            route=route_path,
            version=VERSION,
        ).observe(duration)
        return response


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
