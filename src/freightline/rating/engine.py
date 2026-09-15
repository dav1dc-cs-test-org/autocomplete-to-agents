"""The rating engine.

    quote request -> zone -> billable weight -> base charge -> surcharges -> total

Each step is a separate, individually testable function. ``RatingEngine`` wires
them together and is the only thing the API and CLI import.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ..models import Quote, QuoteLine, QuoteRequest
from ..money import Money
from .surcharges import build_lines
from .tables import ServiceRate, rate_for
from .zones import resolve_zone

WEIGHT_PRECISION = Decimal("0.01")


def dimensional_weight_kg(volume_cm3: Decimal, dim_divisor: int) -> Decimal:
    """Volumetric weight: the carrier charges for space as well as mass."""
    return (volume_cm3 / Decimal(dim_divisor)).quantize(WEIGHT_PRECISION, rounding=ROUND_HALF_UP)


def billable_weight_kg(request: QuoteRequest, rate: ServiceRate) -> Decimal:
    """The greater of actual and dimensional weight."""
    actual = request.parcel.weight_kg.quantize(WEIGHT_PRECISION, rounding=ROUND_HALF_UP)
    dimensional = dimensional_weight_kg(request.parcel.volume_cm3, rate.dim_divisor)
    return max(actual, dimensional)


def base_charge(rate: ServiceRate, zone: int, weight_kg: Decimal) -> Decimal:
    """Zone-adjusted base charge, floored at the published minimum."""
    linehaul = rate.base_decimal() + rate.per_kg_decimal() * weight_kg
    adjusted = linehaul * rate.multiplier_for(zone)
    return max(adjusted, rate.minimum_decimal())


class RatingEngine:
    """Prices a quote request against the published rate cards."""

    def __init__(self, default_currency: str = "USD") -> None:
        self.default_currency = default_currency

    def quote(self, request: QuoteRequest) -> Quote:
        currency = request.currency or self.default_currency
        rate = rate_for(request.carrier_code, request.service)
        zone = resolve_zone(request.origin, request.destination)
        weight = billable_weight_kg(request, rate)

        base = Money.from_decimal(base_charge(rate, zone, weight), currency)
        base_line = QuoteLine(
            code="base", label=f"{request.service.value.title()} linehaul", amount=base, kind="base"
        )
        surcharge_lines = build_lines(request, base)
        lines = (base_line, *surcharge_lines)

        total = Money.zero(currency)
        for line in lines:
            total = total.plus(line.amount)

        return Quote(
            carrier_code=request.carrier_code,
            service=request.service,
            zone=zone,
            billable_weight_kg=weight,
            lines=lines,
            total=total,
            currency=currency,
        )


_DEFAULT_ENGINE = RatingEngine()


def quote(request: QuoteRequest) -> Quote:
    """Price ``request`` with the process-wide default engine."""
    return _DEFAULT_ENGINE.quote(request)
