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