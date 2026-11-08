def scrape(client) -> str:
    return client.get("/metrics").text


def counter_value(body:str, route:str, status: str) -> float:
    for line in body.splitlines():
        if (
            line.startswith("http_requests_total{")
            and f'route="{route}"' in line
            and f'status="{status}"' in line
        ):
            return float(line.rsplit(" ",1)[1])
    return 0.0


def test_build_info_reports_the_version(client):
    body = scrape(client)
    assert 'parcelpost_build_info{version="dev"} 1.0' in body


def test_counter_counts_requests_with_route_and_status(client):
    before = counter_value(scrape(client), "/healthz", "200")
    client.get("/healthz")
    client.get("/healthz")
    after = counter_value(scrape(client), "/healthz", "200")
    assert after - before == 2


def test_counter_uses_the_route_template_not_the_raw_path(client):
    created = client.post(
        "/shipments", json={"origin": "San Jose", "destination": "Austin"}
    )
    shipment_id = created.json()["id"]
    before = counter_value(scrape(client), "/shipments/{shipment_id}", "200")
    client.get(f"/shipments/{shipment_id}")
    body = scrape(client)
    assert counter_value(body, "/shipments/{shipment_id}", "200") - before == 1
    assert f'route="/shipments/{shipment_id}"' not in body


def test_unknown_id_is_counted_under_the_template_with_404(client):
    before = counter_value(scrape(client), "/shipments/{shipment_id}", "404")
    client.get("/shipments/999999")
    after = counter_value(scrape(client), "/shipments/{shipment_id}", "404")
    assert after - before == 1


def test_unmatched_path_is_counted_as_unmatched(client):
    before = counter_value(scrape(client), "unmatched", "404")
    client.get("/no-such-path")
    after = counter_value(scrape(client), "unmatched", "404")
    assert after - before == 1


def test_metrics_endpoint_does_not_count_itself(client):
    body = scrape(client)
    assert 'route="/metrics"' not in body


def histogram_count(body: str, route: str) -> float:
    for line in body.splitlines():
        if (
            line.startswith("http_request_duration_seconds_count{")
            and f'route="{route}"' in line
        ):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


def bucket_value(body: str, route: str, le: str) -> float:
    for line in body.splitlines():
        if (
            line.startswith("http_request_duration_seconds_bucket{")
            and f'route="{route}"' in line
            and f'le="{le}"' in line
        ):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


def test_histogram_counts_requests_by_route(client):
    before = histogram_count(scrape(client), "/healthz")
    client.get("/healthz")
    after = histogram_count(scrape(client), "/healthz")
    assert after - before == 1


def test_histogram_inf_bucket_equals_count(client):
    client.get("/healthz")
    body = scrape(client)
    assert bucket_value(body, "/healthz", "+Inf") == histogram_count(body, "/healthz")


def test_histogram_uses_the_contract_buckets(client):
    client.get("/healthz")
    body = scrape(client)
    assert 'le="0.01"' in body
    assert 'le="0.005"' not in body
