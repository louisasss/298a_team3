import time
import pytest

from src.failure import settings

@pytest.fixture(autouse=True)
def reset_failure_settings():
    yield
    settings.error_rate = 0.0
    settings.latency_ms = 0
    settings.target = ""


def test_version_endpoint_reports_the_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "dev"}


def test_version_header_is_on_responses(client):
    response = client.get("/healthz")
    assert response.headers["x-app-version"] == "dev"


def test_full_error_rate_fails_business_requests(client):
    settings.error_rate = 1.0
    assert client.get("/shipments").status_code == 500
    assert client.get("/shipments").status_code == 500


def test_full_error_rate_leaves_operational_endpoints_alone(client):
    settings.error_rate = 1.0
    assert client.get("/healthz").status_code == 200
    assert client.get("/version").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_target_limits_failures_to_one_operation(client):
    settings.error_rate = 1.0
    settings.target = "POST /shipments"
    response = client.post(
        "/shipments", json={"origin": "San Jose", "destination": "Austin"}
    )
    assert response.status_code == 500
    assert client.get("/shipments").status_code == 200


def test_failed_post_creates_nothing(client):
    settings.error_rate = 1.0
    settings.target = "POST /shipments"
    before = len(client.get("/shipments").json())
    response = client.post(
        "/shipments", json={"origin": "San Jose", "destination": "Austin"}
    )
    assert response.status_code == 500
    after = len(client.get("/shipments").json())
    assert after == before


def test_latency_delays_requests(client):
    settings.latency_ms = 200
    start = time.perf_counter()
    response = client.get("/shipments")
    elapsed = time.perf_counter() - start
    assert response.status_code == 200
    assert elapsed >= 0.2


def test_injected_failures_are_counted_in_metrics(client):
    settings.error_rate = 1.0
    client.get("/shipments")
    body = client.get("/metrics").text
    assert 'route="/shipments",status="500"' in body