"""Mapping between HTTP payloads and domain objects."""

from __future__ import annotations

from ..models import Address, Parcel, Quote, QuoteRequest, Shipment, TrackingEvent
from ..util.dates import to_iso8601
from .schemas import (
    AddressIn,
    CarrierOut,
    ParcelIn,
    QuoteIn,
    QuoteLineOut,
    QuoteOut,
    ShipmentOut,
    TrackingEventOut,
)


def to_address(payload: AddressIn) -> Address:
    return Address(
        line1=payload.line1,
        city=payload.city,
        region=payload.region,
        postal_code=payload.postal_code,
        country=payload.country.upper(),
        residential=payload.residential,
    )


def to_parcel(payload: ParcelIn) -> Parcel:
    return Parcel(
        weight_kg=payload.weight_kg,
        length_cm=payload.length_cm,
        width_cm=payload.width_cm,
        height_cm=payload.height_cm,
    )


def to_quote_request(payload: QuoteIn) -> QuoteRequest:
    return QuoteRequest(
        origin=to_address(payload.origin),
        destination=to_address(payload.destination),
        parcel=to_parcel(payload.parcel),
        carrier_code=payload.carrier_code.strip().lower(),
        service=payload.service,
        currency=payload.currency.upper(),
        saturday_delivery=payload.saturday_delivery,
    )


def from_quote(quote: Quote) -> QuoteOut:
    return QuoteOut(
        carrier_code=quote.carrier_code,
        service=quote.service,
        zone=quote.zone,
        billable_weight_kg=quote.billable_weight_kg,
        lines=[
            QuoteLineOut(code=line.code, label=line.label, amount=line.amount.amount, kind=line.kind)
            for line in quote.lines
        ],
        total=quote.total.amount,
        currency=quote.currency,
    )


def from_shipment(shipment: Shipment) -> ShipmentOut:
    return ShipmentOut(
        id=shipment.id,
        carrier_code=shipment.carrier_code,
        service=shipment.service,
        tracking_number=shipment.tracking_number,
        origin_postal_code=shipment.origin_postal_code,
        destination_postal_code=shipment.destination_postal_code,
        status=shipment.status,
        total=shipment.total.amount,
        currency=shipment.currency,
        reference=shipment.reference,
        created_at=to_iso8601(shipment.created_at),
    )


def from_event(event: TrackingEvent) -> TrackingEventOut:
    return TrackingEventOut(
        shipment_id=event.shipment_id,
        carrier_code=event.carrier_code,
        carrier_status_code=event.carrier_status_code,
        status=event.status,
        description=event.description,
        location=event.location,
        occurred_at=to_iso8601(event.occurred_at),
    )


def from_carrier_profile(profile: object) -> CarrierOut:
    return CarrierOut(
        code=profile.code,  # type: ignore[attr-defined]
        name=profile.name,  # type: ignore[attr-defined]
        services=list(profile.services),  # type: ignore[attr-defined]
        supports_saturday_delivery=profile.supports_saturday_delivery,  # type: ignore[attr-defined]
        supports_international=profile.supports_international,  # type: ignore[attr-defined]
    )
