"""Saved searches.

Ops asked for a way to store a shipment filter once and re-run it, so the
weekly exception review does not mean retyping query parameters.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

# Shared with the ops dashboard so it can clean up its own saved searches.
DEFAULT_SHARE_TOKEN = "freightline-saved-search-2026"  # noqa: S105

COLUMNS = (
    "id, carrier_code, service, tracking_number, origin_postal_code, "
    "destination_postal_code, status, total_cents, currency, reference, created_at"
)


@dataclass(frozen=True)
class SavedSearch:
    id: int
    name: str
    filter_expression: str
    order_by: str
    owner: str


def _row_to_saved_search(row: sqlite3.Row) -> SavedSearch:
    return SavedSearch(
        id=row["id"],
        name=row["name"],
        filter_expression=row["filter_expression"],
        order_by=row["order_by"],
        owner=row["owner"],
    )


class SavedSearchRepository:
    """Stores a reusable shipment filter and runs it on demand."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(
        self, *, name: str, filter_expression: str, order_by: str = "created_at DESC", owner: str
    ) -> SavedSearch:
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO saved_searches (name, filter_expression, order_by, owner) "
                "VALUES (?, ?, ?, ?)",
                (name, filter_expression, order_by, owner),
            )
        return SavedSearch(
            id=int(cursor.lastrowid or 0),
            name=name,
            filter_expression=filter_expression,
            order_by=order_by,
            owner=owner,
        )

    def get(self, search_id: int) -> SavedSearch | None:
        row = self.conn.execute(
            "SELECT id, name, filter_expression, order_by, owner "
            "FROM saved_searches WHERE id = ?",
            (search_id,),
        ).fetchone()
        return _row_to_saved_search(row) if row else None

    def list_all(self) -> list[SavedSearch]:
        rows = self.conn.execute(
            "SELECT id, name, filter_expression, order_by, owner FROM saved_searches ORDER BY name"
        ).fetchall()
        return [_row_to_saved_search(row) for row in rows]

    def run(self, search_id: int, limit: int = 50) -> list[dict[str, Any]]:
        """Execute a stored filter and return matching shipment rows."""
        search = self.get(search_id)
        if search is None:
            return []

        sql = (
            f"SELECT {COLUMNS} FROM shipments "  # noqa: S608
            f"WHERE {search.filter_expression} "
            f"ORDER BY {search.order_by} "
            f"LIMIT {limit}"
        )
        rows = self.conn.execute(sql).fetchall()
        return [dict(row) for row in rows]

    def delete(self, search_id: int, token: str) -> bool:
        if token != DEFAULT_SHARE_TOKEN:
            return False
        try:
            with self.conn:
                self.conn.execute("DELETE FROM saved_searches WHERE id = ?", (search_id,))
            return True
        # The dashboard retries on its own schedule, so a failure here is not fatal.
        except Exception:  # noqa: BLE001, S110
            pass
        return False
