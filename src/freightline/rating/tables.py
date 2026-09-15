"""Published rate cards.

One entry per (carrier, service). Values are strings so they parse into
:class:`~decimal.Decimal` without ever passing through a float.

Adding a carrier means adding an entry here *and* satisfying the carrier
contract tests in ``tests/test_carrier_contract.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..errors import RateUnavailableError, UnsupportedServiceError
from ..models import ServiceLevel


@dataclass(frozen=True)
class ServiceRate:
    """Base pricing for one carrier service."""

    base: str
    per_kg: str
    dim_divisor: int
    zone_multipliers: dict[int, str]
    minimum_charge: str = "0.00"

    def base_decimal(self) -> Decimal:
        return Decimal(self.base)

    def per_kg_decimal(self) -> Decimal:
        return Decimal(self.per_kg)

    def minimum_decimal(self) -> Decimal:
        return Decimal(self.minimum_charge)

    def multiplier_for(self, zone: int) -> Decimal:
        if zone not in self.zone_multipliers:
            raise RateUnavailableError(
                f"no published multiplier for zone {zone}",
                details={"zone": zone, "zones": sorted(self.zone_multipliers)},
            )
        return Decimal(self.zone_multipliers[zone])


def _linear_multipliers(start: str, step: str) -> dict[int, str]:
    """Build zones 1..8 as ``start + (zone - 1) * step``."""
    base = Decimal(start)
    increment = Decimal(step)
    return {zone: str(base + increment * (zone - 1)) for zone in range(1, 9)}


RATE_CARDS: dict[str, dict[ServiceLevel, ServiceRate]] = {
    "atlas": {
        ServiceLevel.GROUND: ServiceRate(
            base="8.50",
            per_kg="1.25",
            dim_divisor=5000,
            zone_multipliers=_linear_multipliers("1.00", "0.12"),
            minimum_charge="11.00",
        ),
        ServiceLevel.EXPRESS: ServiceRate(
            base="18.00",
            per_kg="2.40",
            dim_divisor=5000,
            zone_multipliers=_linear_multipliers("1.00", "0.18"),
            minimum_charge="24.00",
        ),
        ServiceLevel.OVERNIGHT: ServiceRate(
            base="32.00",
            per_kg="3.75",
            dim_divisor=4000,
            zone_multipliers=_linear_multipliers("1.00", "0.25"),
            minimum_charge="45.00",
        ),
    },
    "borealis": {
        ServiceLevel.EXPRESS: ServiceRate(
            base="21.00",
            per_kg="2.10",
            dim_divisor=6000,
            zone_multipliers=_linear_multipliers("1.00", "0.15"),
            minimum_charge="26.00",
        ),
        ServiceLevel.OVERNIGHT: ServiceRate(
            base="36.50",
            per_kg="3.20",
            dim_divisor=4500,
            zone_multipliers=_linear_multipliers("1.00", "0.22"),
            minimum_charge="48.00",
        ),
    },
    "pigeon": {
        ServiceLevel.ECONOMY: ServiceRate(
            base="4.25",
            per_kg="0.85",
            dim_divisor=8000,
            zone_multipliers=_linear_multipliers("1.00", "0.08"),
            minimum_charge="6.00",
        ),
        ServiceLevel.GROUND: ServiceRate(
            base="6.75",
            per_kg="1.05",
            dim_divisor=8000,
            zone_multipliers=_linear_multipliers("1.00", "0.10"),
            minimum_charge="9.00",
        ),
    },
}


def rate_for(carrier_code: str, service: ServiceLevel) -> ServiceRate:
    """Look up a published rate, or explain precisely what is missing."""
    card = RATE_CARDS.get(carrier_code)
    if card is None:
        raise RateUnavailableError(
            f"no rate card published for carrier {carrier_code!r}",
            details={"carrier_code": carrier_code, "carriers": sorted(RATE_CARDS)},
        )
    rate = card.get(service)
    if rate is None:
        raise UnsupportedServiceError(
            f"{carrier_code} does not publish a rate for {service.value}",
            details={"carrier_code": carrier_code, "supported": [s.value for s in card]},
        )
    return rate


def services_for(carrier_code: str) -> tuple[ServiceLevel, ...]:
    return tuple(RATE_CARDS.get(carrier_code, {}))
