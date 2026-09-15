"""Roll-ups over a list of shipments.

Pure functions over in-memory data — no SQL. That keeps the aggregation logic
testable without a database and lets the same code run over API results, a CSV
import, or a nightly batch.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from ..models import Shipment, ShipmentStatus
from ..money import Money


@dataclass(frozen=True)
class CarrierSummary:
    carrier_code: str
    shipment_count: int
    total: Money
    delivered: int
    exceptions: int

    @property
    def average(self) -> Money:
        if self.shipment_count == 0:
            return Money.zero(self.total.currency)
        return Money(self.total.cents // self.shipment_count, self.total.currency)

    @property
    def exception_rate(self) -> Decimal:
        if self.shipment_count == 0:
            return Decimal("0.00")
        rate = Decimal(self.exceptions) / Decimal(self.shipment_count)
        return rate.quantize(Decimal("0.0001"))


def summarize_by_carrier(shipments: list[Shipment]) -> list[CarrierSummary]:
    """One summary per carrier, ordered by spend descending."""
    buckets: dict[str, list[Shipment]] = {}
    for shipment in shipments:
        buckets.setdefault(shipment.carrier_code, []).append(shipment)

    summaries: list[CarrierSummary] = []
    for carrier_code, group in buckets.items():
        currency = group[0].currency
        total = Money.zero(currency)
        for shipment in group:
            total = total.plus(shipment.total)
        summaries.append(
            CarrierSummary(
                carrier_code=carrier_code,
                shipment_count=len(group),
                total=total,
                delivered=sum(1 for s in group if s.status is ShipmentStatus.DELIVERED),
                exceptions=sum(1 for s in group if s.status is ShipmentStatus.EXCEPTION),
            )
        )
    return sorted(summaries, key=lambda s: (-s.total.cents, s.carrier_code))


def summarize_by_status(shipments: list[Shipment]) -> dict[str, int]:
    """Every canonical status appears, including the ones with zero shipments."""
    counts = Counter(shipment.status.value for shipment in shipments)
    return {status.value: counts.get(status.value, 0) for status in ShipmentStatus}
