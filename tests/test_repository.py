from __future__ import annotations

from datetime import UTC, datetime

import pytest

from freightline.errors import ShipmentNotFoundError, ValidationError
from freightline.models import ServiceLevel, Shipment, ShipmentStatus, TrackingEvent
from freightline.storage.repository import SearchFilters


def make_shipment(
    shipment_id: str,
    *,
    carrier_code: str = "atlas",
    status: ShipmentStatus = ShipmentStatus.CREATED,
    total_cents: int = 2310,
    reference: str | None = None,
    destination: str = "10001",
) -> Shipment:
    return Shipment(
        id=shipment_id,
        carrier_code=carrier_code,
        service=ServiceLevel.GROUND,
        tracking_number=f"ATL{shipment_id.zfill(12)[:12]}",
        origin_postal_code="94105",
        destination_postal_code=destination,
        status=status,
        total_cents=total_cents,
        reference=reference,
    )


def test_create_and_get_round_trips(repo):
    created = repo.create(make_shipment("000000000001"))
    assert repo.get(created.id).tracking_number == created.tracking_number


def test_get_missing_shipment_raises(repo):
    with pytest.raises(ShipmentNotFoundError):
        repo.get("nope")


def test_find_by_tracking_number(repo):
    created = repo.create(make_shipment("000000000002"))
    assert repo.find_by_tracking_number(created.tracking_number).id == created.id


def test_find_by_tracking_number_returns_none_when_absent(repo):
    assert repo.find_by_tracking_number("ATL999999999999") is None


def test_update_status(repo):
    created = repo.create(make_shipment("000000000003"))
    repo.update_status(created.id, ShipmentStatus.DELIVERED)
    assert repo.get(created.id).status is ShipmentStatus.DELIVERED


def test_update_status_on_missing_shipment_raises(repo):
    with pytest.raises(ShipmentNotFoundError):
        repo.update_status("nope", ShipmentStatus.DELIVERED)


def test_search_filters_by_carrier(repo):
    repo.create(make_shipment("000000000004", carrier_code="atlas"))
    repo.create(make_shipment("000000000005", carrier_code="pigeon"))
    results = repo.search(SearchFilters(carrier_code="pigeon"))
    assert [s.carrier_code for s in results] == ["pigeon"]


def test_search_filters_by_status(repo):
    repo.create(make_shipment("000000000006", status=ShipmentStatus.DELIVERED))
    repo.create(make_shipment("000000000007", status=ShipmentStatus.EXCEPTION))
    results = repo.search(SearchFilters(status=ShipmentStatus.EXCEPTION))
    assert len(results) == 1


def test_search_filters_by_destination_prefix(repo):
    repo.create(make_shipment("000000000008", destination="10001"))
    repo.create(make_shipment("000000000009", destination="94105"))
    results = repo.search(SearchFilters(destination_postal_code="100"))
    assert len(results) == 1


def test_search_sorts_by_an_allow_listed_column(repo):
    repo.create(make_shipment("000000000010", total_cents=100))
    repo.create(make_shipment("000000000011", total_cents=900))
    results = repo.search(sort_by="total_cents", direction="asc")
    assert [s.total_cents for s in results] == [100, 900]


def test_search_rejects_an_unknown_sort_column(repo):
    with pytest.raises(ValidationError):
        repo.search(sort_by="total_cents; DROP TABLE shipments")


def test_search_rejects_an_unknown_sort_direction(repo):
    with pytest.raises(ValidationError):
        repo.search(direction="sideways")


def test_search_rejects_a_nonsense_limit(repo):
    with pytest.raises(ValidationError):
        repo.search(limit=0)


def test_search_caps_the_page_size(repo):
    for index in range(5):
        repo.create(make_shipment(f"00000000002{index}"))
    assert len(repo.search(limit=100000)) == 5


def test_reference_is_never_interpolated_into_sql(repo):
    """A hostile reference value must be matched literally, not executed."""
    hostile = "' OR '1'='1"
    repo.create(make_shipment("000000000030", reference=hostile))
    repo.create(make_shipment("000000000031", reference="PO-1"))
    results = repo.search(SearchFilters(reference=hostile))
    assert len(results) == 1
    assert repo.count() == 2


def test_count_respects_filters(repo):
    repo.create(make_shipment("000000000040", carrier_code="atlas"))
    repo.create(make_shipment("000000000041", carrier_code="pigeon"))
    assert repo.count(SearchFilters(carrier_code="atlas")) == 1


def test_events_are_returned_oldest_first(repo):
    created = repo.create(make_shipment("000000000050"))
    for hour, status in ((9, ShipmentStatus.IN_TRANSIT), (8, ShipmentStatus.CREATED)):
        repo.append_event(
            TrackingEvent(
                shipment_id=created.id,
                carrier_code="atlas",
                carrier_status_code="PICKED_UP",
                status=status,
                description="scan",
                occurred_at=datetime(2026, 3, 1, hour, tzinfo=UTC),
            )
        )
    events = repo.events_for(created.id)
    assert [event.status for event in events] == [
        ShipmentStatus.CREATED,
        ShipmentStatus.IN_TRANSIT,
    ]


def test_events_require_a_real_shipment(repo):
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        repo.append_event(
            TrackingEvent(
                shipment_id="ghost",
                carrier_code="atlas",
                carrier_status_code="PICKED_UP",
                status=ShipmentStatus.IN_TRANSIT,
                description="scan",
                occurred_at=datetime(2026, 3, 1, tzinfo=UTC),
            )
        )
