from __future__ import annotations

import pytest

from freightline.errors import ValidationError
from freightline.models import ShipmentStatus
from freightline.tracking.normalizer import normalize_event, normalize_payload


def test_normalizes_an_atlas_event():
    event = normalize_event(
        "atlas",
        {
            "shipmentId": "abc123",
            "statusCode": "ON_VEHICLE",
            "message": "Out for delivery",
            "timestamp": "2026-03-01T14:05:00Z",
            "city": "Brooklyn, NY",
        },
    )
    assert event.status is ShipmentStatus.OUT_FOR_DELIVERY
    assert event.location == "Brooklyn, NY"
    assert event.occurred_at.tzinfo is not None


def test_normalizes_a_borealis_event_with_different_field_names():
    event = normalize_event(
        "borealis",
        {
            "reference": "abc123",
            "event_code": "IN_FLIGHT",
            "detail": "Departed ANC",
            "eventTime": "2026-03-01T02:00:00+00:00",
        },
    )
    assert event.status is ShipmentStatus.IN_TRANSIT
    assert event.carrier_code == "borealis"


def test_normalizes_a_legacy_pigeon_numeric_code():
    event = normalize_event(
        "pigeon",
        {"ref": "abc123", "code": "40", "ts": "2026-03-01T18:00:00Z"},
    )
    assert event.status is ShipmentStatus.DELIVERED


def test_description_falls_back_to_the_canonical_status():
    event = normalize_event(
        "atlas",
        {"shipment_id": "abc", "status": "DELIVERED", "occurred_at": "2026-03-01T18:00:00Z"},
    )
    assert event.description == "Delivered"


def test_missing_required_field_names_the_accepted_keys():
    with pytest.raises(ValidationError) as excinfo:
        normalize_event("atlas", {"status": "DELIVERED", "ts": "2026-03-01T18:00:00Z"})
    assert "shipment_id" in excinfo.value.details["accepted_keys"]


def test_bad_timestamp_is_rejected():
    with pytest.raises(ValidationError):
        normalize_event("atlas", {"shipment_id": "a", "status": "DELIVERED", "ts": "last tuesday"})


def test_unknown_status_code_is_rejected():
    with pytest.raises(ValidationError):
        normalize_event(
            "atlas", {"shipment_id": "a", "status": "TELEPORTED", "ts": "2026-03-01T18:00:00Z"}
        )


def test_batched_payloads_are_expanded():
    events = normalize_payload(
        "atlas",
        {
            "events": [
                {"shipment_id": "a", "status": "PICKED_UP", "ts": "2026-03-01T08:00:00Z"},
                {"shipment_id": "a", "status": "DELIVERED", "ts": "2026-03-01T18:00:00Z"},
            ]
        },
    )
    assert [event.status for event in events] == [
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.DELIVERED,
    ]


def test_single_event_payloads_still_work():
    events = normalize_payload(
        "atlas", {"shipment_id": "a", "status": "DELIVERED", "ts": "2026-03-01T18:00:00Z"}
    )
    assert len(events) == 1


def test_events_must_be_a_list():
    with pytest.raises(ValidationError):
        normalize_payload("atlas", {"events": {"shipment_id": "a"}})
