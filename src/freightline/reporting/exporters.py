"""CSV export.

Finance opens these in Excel, so every field is checked for the leading
characters that spreadsheets treat as the start of a formula. A shipment
reference is customer-supplied, which makes this an injection sink, not a
cosmetic concern.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from ..models import Shipment

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

COLUMNS = (
    "id",
    "carrier_code",
    "service",
    "tracking_number",
    "origin_postal_code",
    "destination_postal_code",
    "status",
    "total",
    "currency",
    "reference",
    "created_at",
)


def escape_cell(value: object) -> str:
    """Neutralise spreadsheet formula injection without mangling normal text."""
    text = "" if value is None else str(value)
    if text.startswith(FORMULA_PREFIXES):
        return f"'{text}"
    return text


def _row_for(shipment: Shipment) -> list[str]:
    return [
        escape_cell(shipment.id),
        escape_cell(shipment.carrier_code),
        escape_cell(shipment.service.value),
        escape_cell(shipment.tracking_number),
        escape_cell(shipment.origin_postal_code),
        escape_cell(shipment.destination_postal_code),
        escape_cell(shipment.status.value),
        escape_cell(shipment.total.amount),
        escape_cell(shipment.currency),
        escape_cell(shipment.reference),
        escape_cell(shipment.created_at.isoformat()),
    ]


def to_csv(shipments: Iterable[Shipment]) -> str:
    """Render shipments as CSV text with a header row."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for shipment in shipments:
        writer.writerow(_row_for(shipment))
    return buffer.getvalue()
