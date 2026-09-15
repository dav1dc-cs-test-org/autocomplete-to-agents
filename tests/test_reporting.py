from __future__ import annotations

import csv
import io
from decimal import Decimal

from freightline.models import ServiceLevel, Shipment, ShipmentStatus
from freightline.reporting import summarize_by_carrier, summarize_by_status, to_csv
from freightline.reporting.exporters import escape_cell


def shipment(
    index: int,
    *,
    carrier_code: str = "atlas",
    total_cents: int = 1000,
    status: ShipmentStatus = ShipmentStatus.DELIVERED,
    reference: str | None = None,
) -> Shipment:
    return Shipment(
        id=f"id-{index}",
        carrier_code=carrier_code,
        service=ServiceLevel.GROUND,
        tracking_number=f"ATL{index:012d}",
        origin_postal_code="94105",
        destination_postal_code="10001",
        status=status,
        total_cents=total_cents,
        reference=reference,
    )


def test_summary_groups_by_carrier():
    summaries = summarize_by_carrier(
        [shipment(1), shipment(2), shipment(3, carrier_code="pigeon", total_cents=500)]
    )
    assert [s.carrier_code for s in summaries] == ["atlas", "pigeon"]
    assert summaries[0].shipment_count == 2


def test_summary_orders_by_spend_descending():
    summaries = summarize_by_carrier(
        [shipment(1, total_cents=100), shipment(2, carrier_code="pigeon", total_cents=900)]
    )
    assert summaries[0].carrier_code == "pigeon"


def test_average_is_integer_cents():
    summaries = summarize_by_carrier([shipment(1, total_cents=101), shipment(2, total_cents=100)])
    assert summaries[0].average.cents == 100


def test_average_of_nothing_is_zero():
    summaries = summarize_by_carrier([shipment(1, total_cents=0)])
    assert summaries[0].average.cents == 0


def test_exception_rate():
    summaries = summarize_by_carrier(
        [shipment(1), shipment(2, status=ShipmentStatus.EXCEPTION)]
    )
    assert summaries[0].exception_rate == Decimal("0.5000")


def test_status_summary_includes_empty_statuses():
    counts = summarize_by_status([shipment(1)])
    assert counts["delivered"] == 1
    assert counts["returned"] == 0


def test_csv_has_a_header_and_a_row_per_shipment():
    rows = list(csv.reader(io.StringIO(to_csv([shipment(1), shipment(2)]))))
    assert rows[0][0] == "id"
    assert len(rows) == 3


def test_csv_neutralises_formula_injection():
    body = to_csv([shipment(1, reference="=cmd|'/c calc'!A1")])
    rows = list(csv.reader(io.StringIO(body)))
    reference_index = rows[0].index("reference")
    assert rows[1][reference_index].startswith("'=")


def test_escape_cell_leaves_ordinary_text_alone():
    assert escape_cell("PO-4471") == "PO-4471"


def test_escape_cell_handles_none():
    assert escape_cell(None) == ""
