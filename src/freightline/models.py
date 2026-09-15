"""Core domain types.

These are plain dataclasses on purpose. Pydantic models live in
``freightline.api.schemas`` and exist only at the HTTP boundary, so the domain
stays importable without the ``api`` extra installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from .errors import ValidationError
from .money import Money


class ShipmentStatus(StrEnum):
    """Canonical status vocabulary. Carrier-specific codes normalize into this."""

    CREATED = "created"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    RETURNED = "returned"


class ServiceLevel(StrEnum):
    ECONOMY = "economy"
    GROUND = "ground"
    EXPRESS = "express"
    OVERNIGHT = "overnight"


@dataclass(frozen=True)
class Address:
    line1: str
    city: str
    region: str
    postal_code: str
    country: str = "US"
    residential: bool = False

    def __post_init__(self) -> None:
        if not self.postal_code.strip():
            raise ValidationError("postal_code is required")
        if len(self.country) != 2:
            raise ValidationError(
                "country must be a 2-letter ISO code", details={"country": self.country}
            )

    @property
    def normalized_postal_code(self) -> str:
        return self.postal_code.strip().upper().replace(" ", "")


@dataclass(frozen=True)
class Parcel:
    """A single physical piece. Dimensions are centimetres, weight kilograms."""

    weight_kg: Decimal
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal

    def __post_init__(self) -> None:
        for name in ("weight_kg", "length_cm", "width_cm", "height_cm"):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise ValidationError(f"{name} must be a Decimal, got {type(value).__name__}")
            if value <= 0:
                raise ValidationError(f"{name} must be greater than zero")

    @property
    def volume_cm3(self) -> Decimal:
        return self.length_cm * self.width_cm * self.height_cm

    @property
    def longest_side_cm(self) -> Decimal:
        return max(self.length_cm, self.width_cm, self.height_cm)

    @property
    def girth_cm(self) -> Decimal:
        """Length plus twice the two shorter sides, the standard oversize measure."""
        sides = sorted([self.length_cm, self.width_cm, self.height_cm])
        return sides[2] + 2 * (sides[0] + sides[1])


@dataclass(frozen=True)
class QuoteRequest:
    origin: Address
    destination: Address
    parcel: Parcel
    carrier_code: str
    service: ServiceLevel
    currency: str = "USD"
    saturday_delivery: bool = False
    declared_value: Money | None = None


@dataclass(frozen=True)
class QuoteLine:
    """One charge on a quote. ``kind`` is either ``base`` or ``surcharge``."""

    code: str
    label: str
    amount: Money
    kind: str = "surcharge"


@dataclass(frozen=True)
class Quote:
    carrier_code: str
    service: ServiceLevel
    zone: int
    billable_weight_kg: Decimal
    lines: tuple[QuoteLine, ...]
    total: Money
    currency: str = "USD"

    def line(self, code: str) -> QuoteLine | None:
        return next((line for line in self.lines if line.code == code), None)

    def breakdown(self) -> dict[str, str]:
        return {line.code: str(line.amount.amount) for line in self.lines}


@dataclass
class Shipment:
    id: str
    carrier_code: str
    service: ServiceLevel
    tracking_number: str
    origin_postal_code: str
    destination_postal_code: str
    status: ShipmentStatus = ShipmentStatus.CREATED
    total_cents: int = 0
    currency: str = "USD"
    reference: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def total(self) -> Money:
        return Money(self.total_cents, self.currency)


@dataclass(frozen=True)
class TrackingEvent:
    shipment_id: str
    carrier_code: str
    carrier_status_code: str
    status: ShipmentStatus
    description: str
    occurred_at: datetime
    location: str | None = None
