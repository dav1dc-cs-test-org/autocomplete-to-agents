"""Normalize carrier tracking payloads into :class:`TrackingEvent`.

Carriers disagree about field names, casing, and timestamp formats. This module
absorbs all of that so nothing downstream has to know which carrier an event
came from.
"""

from __future__ import annotations

from typing import Any

from ..carriers import get_carrier
from ..errors import ValidationError
from ..models import TrackingEvent
from ..util.dates import parse_iso8601

# Per-carrier field aliases: canonical name -> the keys that carrier might use.
_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "shipment_id": ("shipment_id", "shipmentId", "reference", "ref", "consignment"),
    "status_code": ("status_code", "statusCode", "status", "event_code", "eventCode", "code"),
    "description": ("description", "message", "event_description", "detail", "text"),
    "occurred_at": ("occurred_at", "occurredAt", "timestamp", "event_time", "eventTime", "ts"),
    "location": ("location", "city", "site", "facility", "scan_location"),
}


def _pick(payload: dict[str, Any], field: str) -> Any:
    for alias in _FIELD_ALIASES[field]:
        if alias in payload and payload[alias] not in (None, ""):
            return payload[alias]
    return None


def _require(payload: dict[str, Any], field: str) -> Any:
    value = _pick(payload, field)
    if value is None:
        raise ValidationError(
            f"tracking payload is missing {field}",
            details={"field": field, "accepted_keys": list(_FIELD_ALIASES[field])},
        )
    return value


def normalize_event(carrier_code: str, payload: dict[str, Any]) -> TrackingEvent:
    """Turn one raw carrier event into a canonical :class:`TrackingEvent`."""
    carrier = get_carrier(carrier_code)
    raw_status = str(_require(payload, "status_code"))
    status = carrier.map_status(raw_status)
    description = _pick(payload, "description") or status.value.replace("_", " ").title()

    return TrackingEvent(
        shipment_id=str(_require(payload, "shipment_id")),
        carrier_code=carrier.profile.code,
        carrier_status_code=raw_status,
        status=status,
        description=str(description),
        occurred_at=parse_iso8601(str(_require(payload, "occurred_at"))),
        location=(str(_pick(payload, "location")) if _pick(payload, "location") else None),
    )


def normalize_payload(carrier_code: str, payload: dict[str, Any]) -> list[TrackingEvent]:
    """Handle both single-event and batched carrier webhook shapes."""
    raw_events = payload.get("events")
    if raw_events is None:
        return [normalize_event(carrier_code, payload)]
    if not isinstance(raw_events, list):
        raise ValidationError("'events' must be a list", details={"got": type(raw_events).__name__})
    return [normalize_event(carrier_code, event) for event in raw_events]
