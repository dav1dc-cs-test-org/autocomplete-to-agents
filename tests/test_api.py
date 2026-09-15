"""HTTP contract tests.

Skipped when the ``api`` extra is not installed so the domain suite still runs
in a minimal environment.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi", reason="install with: pip install -e '.[api]'")

from fastapi.testclient import TestClient  # noqa: E402

from freightline.api.app import create_app  # noqa: E402
from freightline.api.deps import get_connection, settings  # noqa: E402
from freightline.config import Settings  # noqa: E402
from freightline.storage.db import in_memory  # noqa: E402
from freightline.tracking.webhooks import compute_signature  # noqa: E402

WEBHOOK_SECRET = "test-webhook-secret"
ADMIN_TOKEN = "test-admin-token"

QUOTE_BODY = {
    "carrier_code": "atlas",
    "service": "ground",
    "origin": {"line1": "1 Market St", "city": "SF", "region": "CA", "postal_code": "94105"},
    "destination": {"line1": "20 W 34th", "city": "NY", "region": "NY", "postal_code": "10001"},
    "parcel": {"weight_kg": "2.5", "length_cm": "30", "width_cm": "20", "height_cm": "15"},
}


@pytest.fixture()
def client():
    conn = in_memory()
    app = create_app()
    app.dependency_overrides[get_connection] = lambda: conn
    app.dependency_overrides[settings] = lambda: Settings(
        webhook_secret=WEBHOOK_SECRET, admin_token=ADMIN_TOKEN
    )
    with TestClient(app) as test_client:
        yield test_client
    conn.close()


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_openapi_document_is_generated(client):
    schema = client.get("/openapi.json").json()
    assert "/v1/quotes" in schema["paths"]
    assert "/v1/shipments" in schema["paths"]


def test_list_carriers(client):
    codes = [carrier["code"] for carrier in client.get("/v1/carriers").json()]
    assert codes == ["atlas", "borealis", "pigeon"]


def test_create_quote(client):
    body = client.post("/v1/quotes", json=QUOTE_BODY).json()
    assert body["carrier_code"] == "atlas"
    assert body["zone"] == 7
    assert any(line["code"] == "fuel" for line in body["lines"])


def test_quote_rejects_unknown_fields(client):
    payload = {**QUOTE_BODY, "discount_code": "FREE"}
    assert client.post("/v1/quotes", json=payload).status_code == 422


def test_quote_rejects_a_zero_weight_parcel(client):
    payload = {**QUOTE_BODY, "parcel": {**QUOTE_BODY["parcel"], "weight_kg": "0"}}
    assert client.post("/v1/quotes", json=payload).status_code == 422


def test_quote_for_an_unsupported_service_returns_a_domain_error(client):
    payload = {**QUOTE_BODY, "carrier_code": "borealis"}
    response = client.post("/v1/quotes", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == "unsupported_service"


def test_quote_for_an_unknown_carrier_returns_404(client):
    payload = {**QUOTE_BODY, "carrier_code": "teleport"}
    response = client.post("/v1/quotes", json=payload)
    assert response.status_code == 404
    assert response.json()["code"] == "unknown_carrier"


def test_create_and_fetch_a_shipment(client):
    created = client.post("/v1/shipments", json={**QUOTE_BODY, "reference": "PO-1"})
    assert created.status_code == 201
    shipment_id = created.json()["id"]

    fetched = client.get(f"/v1/shipments/{shipment_id}")
    assert fetched.status_code == 200
    assert fetched.json()["reference"] == "PO-1"


def test_fetching_a_missing_shipment_returns_404(client):
    response = client.get("/v1/shipments/ghost")
    assert response.status_code == 404
    assert response.json()["code"] == "shipment_not_found"


def test_search_is_paginated(client):
    for index in range(3):
        client.post("/v1/shipments", json={**QUOTE_BODY, "reference": f"PO-{index}"})
    page = client.get("/v1/shipments", params={"limit": 2}).json()
    assert len(page["items"]) == 2
    assert page["total"] == 3


def test_search_caps_the_page_size(client):
    assert client.get("/v1/shipments", params={"limit": 10_000}).status_code == 422


def test_search_rejects_an_arbitrary_sort_column(client):
    response = client.get("/v1/shipments", params={"sort_by": "(SELECT 1)"})
    assert response.status_code == 422


def test_webhook_requires_a_valid_signature(client):
    created = client.post("/v1/shipments", json=QUOTE_BODY).json()
    payload = f'{{"shipment_id":"{created["id"]}","status":"DELIVERED","ts":"2026-03-01T18:00:00Z"}}'
    response = client.post(
        "/v1/webhooks/atlas",
        content=payload,
        headers={"x-freightline-signature": "sha256=nope", "content-type": "application/json"},
    )
    assert response.status_code == 401


def test_webhook_updates_status_when_signed(client):
    created = client.post("/v1/shipments", json=QUOTE_BODY).json()
    payload = f'{{"shipment_id":"{created["id"]}","status":"DELIVERED","ts":"2026-03-01T18:00:00Z"}}'
    body = payload.encode("utf-8")
    response = client.post(
        "/v1/webhooks/atlas",
        content=body,
        headers={
            "x-freightline-signature": compute_signature(WEBHOOK_SECRET, body),
            "content-type": "application/json",
        },
    )
    assert response.status_code == 202
    assert client.get(f"/v1/shipments/{created['id']}").json()["status"] == "delivered"


def test_admin_reports_require_a_bearer_token(client):
    assert client.get("/v1/admin/reports/carriers").status_code == 401


def test_admin_reports_accept_the_configured_token(client):
    client.post("/v1/shipments", json=QUOTE_BODY)
    response = client.get(
        "/v1/admin/reports/carriers", headers={"authorization": f"Bearer {ADMIN_TOKEN}"}
    )
    assert response.status_code == 200
    assert response.json()[0]["carrier_code"] == "atlas"


def test_csv_export_is_attachment(client):
    client.post("/v1/shipments", json=QUOTE_BODY)
    response = client.get(
        "/v1/admin/reports/export.csv", headers={"authorization": f"Bearer {ADMIN_TOKEN}"}
    )
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
