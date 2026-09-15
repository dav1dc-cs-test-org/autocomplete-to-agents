from __future__ import annotations

import pytest

from freightline.errors import ShipmentNotFoundError, UnsupportedServiceError
from freightline.models import ServiceLevel, ShipmentStatus
from freightline.storage.repository import SearchFilters


def test_quote_prices_a_supported_service(service, quote_request):
    assert service.quote(quote_request).total.cents > 0


def test_quote_rejects_a_service_the_carrier_does_not_run(service, quote_request):
    from dataclasses import replace

    with pytest.raises(UnsupportedServiceError) as excinfo:
        service.quote(replace(quote_request, carrier_code="borealis"))
    assert "express" in excinfo.value.details["supported"]


def test_create_shipment_persists_and_prices(service, quote_request):
    shipment = service.create_shipment(quote_request, reference="PO-4471")
    stored = service.get(shipment.id)
    assert stored.reference == "PO-4471"
    assert stored.total_cents == shipment.total_cents
    assert stored.status is ShipmentStatus.CREATED


def test_created_tracking_number_matches_the_carrier_format(service, quote_request):
    from freightline.carriers import get_carrier

    shipment = service.create_shipment(quote_request)
    carrier = get_carrier(shipment.carrier_code)
    assert carrier.normalize_tracking_number(shipment.tracking_number) == shipment.tracking_number


def test_create_shipment_writes_a_quote_audit_row(service, quote_request, conn):
    service.create_shipment(quote_request)
    total = conn.execute("SELECT COUNT(*) AS n FROM quote_audit").fetchone()["n"]
    assert total == 1


def test_ingest_tracking_advances_status(service, quote_request):
    shipment = service.create_shipment(quote_request)
    service.ingest_tracking(
        "atlas",
        {
            "shipment_id": shipment.id,
            "status": "ON_VEHICLE",
            "ts": "2026-03-01T14:00:00Z",
        },
    )
    assert service.get(shipment.id).status is ShipmentStatus.OUT_FOR_DELIVERY


def test_ingest_tracking_handles_a_batch(service, quote_request):
    shipment = service.create_shipment(quote_request)
    service.ingest_tracking(
        "atlas",
        {
            "events": [
                {"shipment_id": shipment.id, "status": "PICKED_UP", "ts": "2026-03-01T08:00:00Z"},
                {"shipment_id": shipment.id, "status": "DELIVERED", "ts": "2026-03-01T18:00:00Z"},
            ]
        },
    )
    assert service.get(shipment.id).status is ShipmentStatus.DELIVERED
    assert len(service.repo.events_for(shipment.id)) == 2


def test_ingest_tracking_for_an_unknown_shipment_raises(service):
    with pytest.raises(ShipmentNotFoundError):
        service.ingest_tracking(
            "atlas", {"shipment_id": "ghost", "status": "DELIVERED", "ts": "2026-03-01T18:00:00Z"}
        )


def test_search_returns_created_shipments(service, quote_request):
    service.create_shipment(quote_request, reference="PO-1")
    service.create_shipment(quote_request, reference="PO-2")
    assert len(service.search(SearchFilters(carrier_code="atlas"))) == 2


def test_shipment_service_level_round_trips(service, quote_request):
    shipment = service.create_shipment(quote_request)
    assert service.get(shipment.id).service is ServiceLevel.GROUND
