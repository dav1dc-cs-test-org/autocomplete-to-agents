"""Surcharges.

Each surcharge is a small object that decides whether it applies to a quote and
returns the amount to add. ``SURCHARGES`` is ordered: percentage surcharges run
after the flat ones so that fuel is calculated on the accumulated subtotal, the
way carriers actually bill it.

Adding a surcharge touches five places. The ``new-surcharge`` agent skill in
``.github/skills/`` walks through all of them.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from ..models import QuoteLine, QuoteRequest
from ..money import Money
from .zones import is_remote

FUEL_RATE = Decimal("0.155")
OVERSIZE_LONGEST_SIDE_CM = Decimal("120")
OVERSIZE_GIRTH_CM = Decimal("300")
HEAVY_WEIGHT_KG = Decimal("30")


@runtime_checkable
class Surcharge(Protocol):
    @property
    def code(self) -> str: ...

    @property
    def label(self) -> str: ...

    def applies_to(self, request: QuoteRequest) -> bool: ...

    def amount(self, request: QuoteRequest, subtotal: Money) -> Money: ...


@dataclass(frozen=True)
class FlatSurcharge:
    code: str
    label: str
    value: str

    def applies_to(self, request: QuoteRequest) -> bool:  # pragma: no cover - overridden
        raise NotImplementedError

    def amount(self, request: QuoteRequest, subtotal: Money) -> Money:
        return Money.parse(self.value, request.currency)


@dataclass(frozen=True)
class ResidentialSurcharge(FlatSurcharge):
    code: str = "residential"
    label: str = "Residential delivery"
    value: str = "4.95"

    def applies_to(self, request: QuoteRequest) -> bool:
        return request.destination.residential


@dataclass(frozen=True)
class RemoteAreaSurcharge(FlatSurcharge):
    code: str = "remote_area"
    label: str = "Remote area delivery"
    value: str = "12.50"

    def applies_to(self, request: QuoteRequest) -> bool:
        return is_remote(request.destination)


@dataclass(frozen=True)
class SaturdayDeliverySurcharge(FlatSurcharge):
    code: str = "saturday_delivery"
    label: str = "Saturday delivery"
    value: str = "16.00"

    def applies_to(self, request: QuoteRequest) -> bool:
        return request.saturday_delivery


@dataclass(frozen=True)
class OversizeSurcharge(FlatSurcharge):
    code: str = "oversize"
    label: str = "Oversize parcel"
    value: str = "28.00"

    def applies_to(self, request: QuoteRequest) -> bool:
        parcel = request.parcel
        return (
            parcel.longest_side_cm > OVERSIZE_LONGEST_SIDE_CM
            or parcel.girth_cm > OVERSIZE_GIRTH_CM
        )


@dataclass(frozen=True)
class HeavyweightSurcharge(FlatSurcharge):
    code: str = "heavyweight"
    label: str = "Heavyweight handling"
    value: str = "19.50"

    def applies_to(self, request: QuoteRequest) -> bool:
        return request.parcel.weight_kg > HEAVY_WEIGHT_KG


@dataclass(frozen=True)
class FuelSurcharge:
    """Percentage of the accumulated subtotal. Always runs last."""

    code: str = "fuel"
    label: str = "Fuel surcharge"
    rate: Decimal = FUEL_RATE

    def applies_to(self, request: QuoteRequest) -> bool:
        return True

    def amount(self, request: QuoteRequest, subtotal: Money) -> Money:
        return subtotal.times(self.rate)


SURCHARGES: tuple[Surcharge, ...] = (
    ResidentialSurcharge(),
    RemoteAreaSurcharge(),
    SaturdayDeliverySurcharge(),
    OversizeSurcharge(),
    HeavyweightSurcharge(),
    FuelSurcharge(),
)


def applicable_surcharges(request: QuoteRequest) -> tuple[Surcharge, ...]:
    return tuple(surcharge for surcharge in SURCHARGES if surcharge.applies_to(request))


def build_lines(request: QuoteRequest, base: Money) -> tuple[QuoteLine, ...]:
    """Compute surcharge lines, accumulating the subtotal as it goes."""
    lines: list[QuoteLine] = []
    subtotal = base
    for surcharge in SURCHARGES:
        if not surcharge.applies_to(request):
            continue
        amount = surcharge.amount(request, subtotal)
        if amount.is_zero():
            continue
        lines.append(QuoteLine(code=surcharge.code, label=surcharge.label, amount=amount))
        subtotal = subtotal.plus(amount)
    return tuple(lines)
