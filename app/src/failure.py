import os
import time
import random

from fastapi import HTTPException, Request

def _parse_rate(raw):
    try:
        rate = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, rate))


def _parse_latency_ms(raw):
    try:
        latency = int(raw)
    except (TypeError, ValueError):
        return 0
    return max(0, latency)


class FailureSettings:
    def __init__(self):
        self.error_rate = _parse_rate(os.environ.get("FAILURE_ERROR_RATE"))
        self.latency_ms = _parse_latency_ms(os.environ.get("FAILURE_LATENCY_MS"))
        self.target = os.environ.get("FAILURE_TARGET", "").strip()


settings = FailureSettings()

print(
    "failure injection: "
    f"error_rate={settings.error_rate} "
    f"latency_ms={settings.latency_ms} "
    f"target={settings.target or 'all'}"
)


def maybe_inject_failure(request: Request) -> None:
    if settings.error_rate == 0 and settings.latency_ms == 0:
        return
    route = request.scope.get("route")
    route_path = route.path if route is not None else "unmatched"
    operation = f"{request.method} {route_path}"
    if settings.target and settings.target != operation:
        return 
    if settings.latency_ms > 0:
        time.sleep(settings.latency_ms / 1000)
    if settings.error_rate > 0 and random.random() < settings.error_rate:
        raise HTTPException(status_code=500, detail="injected failure")
