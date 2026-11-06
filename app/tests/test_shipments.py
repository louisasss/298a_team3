def test_create_shipment_return_201_with_tracking_code(client):
    response = client.post(
        "/shipments", json={"origin": "San Jose", "destination": "Milpitas"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["origin"] == "San Jose"
    assert body["destination"] == "Milpitas"
    assert body["status"] == "created"
    assert body["tracking_code"].startswith("PP-")
    assert body["id"] is not None


def test_create_shipment_mising_field_returns_400(client):
    response = client.post("/shipments", json={"origin": "San Jose"})
    assert response.status_code == 400


def test_create_shipment_empty_field_returns_400(client):
    response = client.post(
        "/shipments", json={"origin": "", "destination": "Milpitas"}
    )
    assert response.status_code == 400


def create_one(client, origin="San Jose", destination="Milpitas"):
    response = client.post(
        "/shipments", json={"origin": origin, "destination": destination}
    )
    assert response.status_code == 201
    return response.json()


def test_list_shipments_returns_created_shipments(client):
    create_one(client)
    create_one(client, origin="Fremont", destination="San Jose")
    response = client.get("/shipments")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["origin"] == "San Jose"
    assert body[1]["origin"] == "Fremont"


def test_list_shipments_filter_by_status(client):
    create_one(client)
    response = client.get("/shipments", params={"status": "created"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = client.get("/shipments", params={"status": "delivered"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_shipments_unknown_status_returns_400(client):
    response = client.get("/shipments", params={"status": "bogus"})
    assert response.status_code == 400


def test_get_shipment_by_id(client):
    created = create_one(client)
    response = client.get(f"/shipments/{created['id']}")
    assert response.status_code == 200
    assert response.json()["tracking_code"] == created["tracking_code"]


def test_get_shipment_unknown_id_returns_404(client):
    response = client.get("/shipments/9999")
    assert response.status_code == 404
