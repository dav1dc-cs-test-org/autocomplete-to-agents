#!/usr/bin/env python3
"""Rebuild the local database with a realistic spread of demo shipments.

    python scripts/seed_data.py [--db var/freightline.db] [--count 60]

Deterministic: the same seed produces the same data, so screenshots and demo
numbers stay stable between runs.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from freightline.carriers import get_carrier  # noqa: E402
from freightline.models import (  # noqa: E402
    Address,
    Parcel,
    QuoteRequest,
    ServiceLevel,
    ShipmentStatus,
    TrackingEvent,
)
from freightline.service import FreightlineService  # noqa: E402
from freightline.storage.db import apply_migrations, connect  # noqa: E402

RANDOM_SEED = 20260914

LANES = [
    ("94105", "10001", "US", "US"),
    ("94105", "60601", "US", "US"),
    ("10001", "30301", "US", "US"),
    ("60601", "98101", "US", "US"),
    ("02108", "94105", "US", "US"),
    ("10001", "99501", "US", "US"),
    ("94105", "M5V3L9", "US", "CA"),
]

CARRIER_SERVICES = [
    ("atlas", ServiceLevel.GROUND),
    ("atlas", ServiceLevel.EXPRESS),
    ("atlas", ServiceLevel.OVERNIGHT),
    ("borealis", ServiceLevel.EXPRESS),
    ("borealis", ServiceLevel.OVERNIGHT),
    ("pigeon", ServiceLevel.ECONOMY),
    ("pigeon", ServiceLevel.GROUND),
]

JOURNEYS = {
    "atlas": [("MANIFESTED", 0), ("PICKED_UP", 4), ("DEPARTED_HUB", 10), ("ON_VEHICLE", 30)],
    "borealis": [("BOOKED", 0), ("UPLIFT", 3), ("IN_FLIGHT", 6), ("LAST_MILE", 22)],
    "pigeon": [("10", 0), ("20", 8), ("22", 20), ("30", 40)],
}

TERMINAL = {
    "atlas": {"delivered": "DELIVERED", "exception": "DELAYED", "returned": "RTS"},
    "borealis": {"delivered": "DELIVERED", "exception": "CUSTOMS_HOLD", "returned": "RETURN_TO_SHIPPER"},
    "pigeon": {"delivered": "40", "exception": "50", "returned": "60"},
}


def address(postal_code: str, country: str, *, residential: bool = False) -> Address:
    return Address(
        line1="-",
        city="-",
        region="-",
        postal_code=postal_code,
        country=country,
        residential=residential,
    )


def build(rng: random.Random, index: int) -> tuple[QuoteRequest, str]:
    origin_pc, dest_pc, origin_country, dest_country = rng.choice(LANES)
    carrier_code, service = rng.choice(CARRIER_SERVICES)
    if dest_country != "US" and not get_carrier(carrier_code).profile.supports_international:
        carrier_code, service = "atlas", ServiceLevel.GROUND

    request = QuoteRequest(
        origin=address(origin_pc, origin_country),
        destination=address(dest_pc, dest_country, residential=rng.random() < 0.35),
        parcel=Parcel(
            weight_kg=Decimal(str(round(rng.uniform(0.4, 34.0), 2))),
            length_cm=Decimal(str(rng.choice([20, 30, 45, 60, 130]))),
            width_cm=Decimal(str(rng.choice([15, 20, 35, 50]))),
            height_cm=Decimal(str(rng.choice([10, 15, 25, 40]))),
        ),
        carrier_code=carrier_code,
        service=service,
        saturday_delivery=rng.random() < 0.12,
    )
    return request, f"PO-{4000 + index}"


def outcome(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.70:
        return "delivered"
    if roll < 0.85:
        return "in_flight"
    if roll < 0.95:
        return "exception"
    return "returned"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="var/freightline.db")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args(argv)

    database = Path(args.db)
    if database.exists():
        database.unlink()

    conn = connect(database)
    apply_migrations(conn)
    service = FreightlineService(conn)
    rng = random.Random(args.seed)

    start = datetime.now(UTC) - timedelta(days=30)
    created = 0

    for index in range(args.count):
        request, reference = build(rng, index)
        shipment = service.create_shipment(request, reference=reference)
        booked_at = start + timedelta(hours=rng.randint(0, 24 * 29))

        carrier = get_carrier(shipment.carrier_code)
        scans = list(JOURNEYS[shipment.carrier_code])
        result = outcome(rng)
        if result != "in_flight":
            scans.append((TERMINAL[shipment.carrier_code][result], 52))
        else:
            scans = scans[:3]

        for code, hours in scans:
            service.repo.append_event(
                TrackingEvent(
                    shipment_id=shipment.id,
                    carrier_code=carrier.profile.code,
                    carrier_status_code=code,
                    status=carrier.map_status(code),
                    description=f"{carrier.profile.name} scan {code}",
                    occurred_at=booked_at + timedelta(hours=hours),
                    location=rng.choice(["Oakland CA", "Memphis TN", "Newark NJ", "Reno NV"]),
                )
            )
        service.repo.update_status(shipment.id, carrier.map_status(scans[-1][0]))
        created += 1

    statuses = conn.execute(
        "SELECT status, COUNT(*) AS n FROM shipments GROUP BY status ORDER BY n DESC"
    ).fetchall()
    conn.close()

    print(f"seeded {created} shipments into {database}")
    for row in statuses:
        print(f"  {row['status']:<18} {row['n']}")
    assert ShipmentStatus.DELIVERED.value in {row["status"] for row in statuses}
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
