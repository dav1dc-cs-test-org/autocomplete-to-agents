"""Request and response models for the HTTP boundary.

These are the API contract. Field names, enums, and required-ness here are what
clients depend on, so changing them is a breaking change — see
``.github/instructions/api-contracts.instructions.md``.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..models import ServiceLevel, ShipmentStatus


class AddressIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line1: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=16)
    country: str = Field(default="US", min_length=2, max_length=2)
    residential: bool = False


class ParcelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weight_kg: Decimal = Field(gt=0, le=Decimal("1000"))
    length_cm: Decimal = Field(gt=0, le=Decimal("400"))
    width_cm: Decimal = Field(gt=0, le=Decimal("400"))
    height_cm: Decimal = Field(gt=0, le=Decimal("400"))


class QuoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carrier_code: str = Field(min_length=1, max_length=32)
    service: ServiceLevel
    origin: AddressIn
    destination: AddressIn
    parcel: ParcelIn
    currency: str = Field(default="USD", min_length=3, max_length=3)
    saturday_delivery: bool = False


class QuoteLineOut(BaseModel):
    code: str
    label: str
    amount: Decimal
    kind: str


class QuoteOut(BaseModel):
    carrier_code: str
    service: ServiceLevel
    zone: int
    billable_weight_kg: Decimal
    lines: list[QuoteLineOut]
    total: Decimal
    currency: str


class ShipmentIn(QuoteIn):
    reference: str | None = Field(default=None, max_length=120)


class ShipmentOut(BaseModel):
    id: str
    carrier_code: str
    service: ServiceLevel
    tracking_number: str
    origin_postal_code: str
    destination_postal_code: str
    status: ShipmentStatus
    total: Decimal
    currency: str
    reference: str | None
    created_at: str


class ShipmentPage(BaseModel):
    items: list[ShipmentOut]
    total: int
    limit: int
    offset: int


class CarrierOut(BaseModel):
    code: str
    name: str
    services: list[ServiceLevel]
    supports_saturday_delivery: bool
    supports_international: bool


class TrackingEventOut(BaseModel):
    shipment_id: str
    carrier_code: str
    carrier_status_code: str
    status: ShipmentStatus
    description: str
    location: str | None
    occurred_at: str


class ErrorOut(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)
