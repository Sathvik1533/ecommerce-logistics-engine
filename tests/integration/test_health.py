import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_liveness_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["environment"] == "testing"


@pytest.mark.integration
def test_readiness_endpoint_responds(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # In an isolated unit/integration environment without live MySQL,
    # the database check reports degraded status
    assert data["status"] in ["ready", "degraded"]
    assert "checks" in data


@pytest.mark.integration
def test_openapi_schema_generated(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    schema = response.json()
    assert schema["info"]["title"] == "E-Commerce Logistics Engine"
    assert "/api/v1/orders/" in schema["paths"]
    assert "/api/v1/inventory/reserve" in schema["paths"]


@pytest.mark.integration
def test_scaffolded_endpoints_return_501(client: TestClient):
    order_payload = {
        "customer_id": "cust_999",
        "currency": "USD",
        "items": [{"sku": "SKU-TEST", "quantity": 1, "unit_price": "25.00"}],
    }
    response = client.post("/api/v1/orders/", json=order_payload)
    # Honest expectation: 501 Not Implemented because the engineer implements the core logic
    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
