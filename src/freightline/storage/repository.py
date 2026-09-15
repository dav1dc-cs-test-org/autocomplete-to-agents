"""Data access for shipments, tracking events, and the quote audit trail.

Every value that reaches SQL goes through a bound parameter. The only things
interpolated into a statement are identifiers drawn from the allow-lists below,
which is why ``search`` validates ``sort_by`` and ``direction`` against them
instead of passing them through.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from ..config import MAX_PAGE_SIZE
from ..errors import ShipmentNotFoundError, ValidationError
from ..models import Quote, ServiceLevel, Shipment, ShipmentStatus, TrackingEvent
from ..util.dates import parse_iso8601, to_iso8601

SORTABLE_COLUMNS = frozenset({"created_at", "total_cents", "carrier_code", "status"})
SORT_DIRECTIONS = frozenset({"asc", "desc"})

_SHIPMENT_COLUMNS = (
    "id, carrier_code, service, tracking_number, origin_postal_code, "
    "destination_postal_code, status, total_cents, currency, reference, created_at"
)


@dataclass(frozen=True)
class SearchFilters:
    carrier_code: str | None = None
    status: ShipmentStatus | None = None
    reference: str | None = None
    destination_postal_code: str | None = None


def _row_to_shipment(row: sqlite3.Row) -> Shipment:
    return Shipment(
        id=row["id"],
        carrier_code=row["carrier_code"],
        service=ServiceLevel(row["service"]),
        tracking_number=row["tracking_number"],
        origin_postal_code=row["origin_postal_code"],
        destination_postal_code=row["destination_postal_code"],
        status=ShipmentStatus(row["status"]),
        total_cents=row["total_cents"],
        currency=row["currency"],
        reference=row["reference"],
        created_at=parse_iso8601(row["created_at"].replace(" ", "T")),
    )


class ShipmentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # -- shipments ---------------------------------------------------------

    def create(self, shipment: Shipment) -> Shipment:
        with self.conn:
            self.conn.execute(
                "INSERT INTO shipments ("
                "  id, carrier_code, service, tracking_number, origin_postal_code,"
                "  destination_postal_code, status, total_cents, currency, reference, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    shipment.id,
                    shipment.carrier_code,
                    shipment.service.value,
                    shipment.tracking_number,
                    shipment.origin_postal_code,
                    shipment.destination_postal_code,
                    shipment.status.value,
                    shipment.total_cents,
                    shipment.currency,
                    shipment.reference,
                    to_iso8601(shipment.created_at),
                ),
            )
        return shipment

    def get(self, shipment_id: str) -> Shipment:
        row = self.conn.execute(
            f"SELECT {_SHIPMENT_COLUMNS} FROM shipments WHERE id = ?",  # noqa: S608
            (shipment_id,),
        ).fetchone()
        if row is None:
            raise ShipmentNotFoundError(
                f"no shipment with id {shipment_id!r}", details={"shipment_id": shipment_id}
            )
        return _row_to_shipment(row)

    def find_by_tracking_number(self, tracking_number: str) -> Shipment | None:
        row = self.conn.execute(
            f"SELECT {_SHIPMENT_COLUMNS} FROM shipments WHERE tracking_number = ?",  # noqa: S608
            (tracking_number,),
        ).fetchone()
        return _row_to_shipment(row) if row else None

    def update_status(self, shipment_id: str, status: ShipmentStatus) -> None:
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE shipments SET status = ? WHERE id = ?", (status.value, shipment_id)
            )
        if cursor.rowcount == 0:
            raise ShipmentNotFoundError(
                f"no shipment with id {shipment_id!r}", details={"shipment_id": shipment_id}
            )

    def search(
        self,
        filters: SearchFilters | None = None,
        *,
        sort_by: str = "created_at",
        direction: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Shipment]:
        """Filtered, sorted, paginated shipment search.

        ``sort_by`` and ``direction`` become part of the SQL text, so both are
        checked against a fixed allow-list. ``limit`` is capped server-side so a
        caller cannot ask for the whole table.
        """
        active = filters or SearchFilters()

        if sort_by not in SORTABLE_COLUMNS:
            raise ValidationError(
                f"cannot sort by {sort_by!r}", details={"sortable": sorted(SORTABLE_COLUMNS)}
            )
        normalized_direction = direction.lower()
        if normalized_direction not in SORT_DIRECTIONS:
            raise ValidationError(
                f"invalid sort direction {direction!r}", details={"allowed": sorted(SORT_DIRECTIONS)}
            )
        if limit < 1:
            raise ValidationError("limit must be at least 1", details={"limit": limit})
        if offset < 0:
            raise ValidationError("offset cannot be negative", details={"offset": offset})

        clauses: list[str] = []
        params: list[object] = []
        if active.carrier_code:
            clauses.append("carrier_code = ?")
            params.append(active.carrier_code)
        if active.status:
            clauses.append("status = ?")
            params.append(active.status.value)
        if active.reference:
            clauses.append("reference = ?")
            params.append(active.reference)
        if active.destination_postal_code:
            clauses.append("destination_postal_code LIKE ?")
            params.append(f"{active.destination_postal_code}%")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        order = f"ORDER BY {sort_by} {normalized_direction.upper()}"
        params.extend([min(limit, MAX_PAGE_SIZE), offset])

        sql = f"SELECT {_SHIPMENT_COLUMNS} FROM shipments {where} {order} LIMIT ? OFFSET ?"  # noqa: S608
        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_shipment(row) for row in rows]

    def count(self, filters: SearchFilters | None = None) -> int:
        active = filters or SearchFilters()
        clauses: list[str] = []
        params: list[object] = []
        if active.carrier_code:
            clauses.append("carrier_code = ?")
            params.append(active.carrier_code)
        if active.status:
            clauses.append("status = ?")
            params.append(active.status.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT COUNT(*) AS total FROM shipments {where}"  # noqa: S608
        return int(self.conn.execute(sql, params).fetchone()["total"])

    # -- tracking events ---------------------------------------------------

    def append_event(self, event: TrackingEvent) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO tracking_events ("
                "  shipment_id, carrier_code, carrier_status_code, status,"
                "  description, location, occurred_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event.shipment_id,
                    event.carrier_code,
                    event.carrier_status_code,
                    event.status.value,
                    event.description,
                    event.location,
                    to_iso8601(event.occurred_at),
                ),
            )

    def events_for(self, shipment_id: str, *, limit: int = 100) -> list[TrackingEvent]:
        rows = self.conn.execute(
            "SELECT shipment_id, carrier_code, carrier_status_code, status, description,"
            "       location, occurred_at"
            "  FROM tracking_events WHERE shipment_id = ?"
            " ORDER BY occurred_at ASC LIMIT ?",
            (shipment_id, min(limit, MAX_PAGE_SIZE)),
        ).fetchall()
        return [
            TrackingEvent(
                shipment_id=row["shipment_id"],
                carrier_code=row["carrier_code"],
                carrier_status_code=row["carrier_status_code"],
                status=ShipmentStatus(row["status"]),
                description=row["description"],
                occurred_at=parse_iso8601(row["occurred_at"]),
                location=row["location"],
            )
            for row in rows
        ]

    # -- quote audit -------------------------------------------------------

    def record_quote(self, quote: Quote, *, shipment_id: str | None = None) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO quote_audit ("
                "  shipment_id, carrier_code, service, zone, billable_kg,"
                "  breakdown, total_cents, currency"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    shipment_id,
                    quote.carrier_code,
                    quote.service.value,
                    quote.zone,
                    str(quote.billable_weight_kg),
                    json.dumps(quote.breakdown()),
                    quote.total.cents,
                    quote.currency,
                ),
            )
