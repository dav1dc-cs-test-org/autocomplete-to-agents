"""SQLite connection handling and forward-only migrations.

Migrations are plain ``.sql`` files in ``storage/migrations``, applied in
filename order and recorded in ``schema_migrations``. There is no down-migration:
rollbacks happen by deploying a new forward migration.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(database_path: str | Path) -> sqlite3.Connection:
    """Open a connection with the settings the rest of the app assumes.

    ``check_same_thread=False`` is required because the API serves sync route
    handlers from a worker threadpool; writes are still serialised by SQLite's
    own locking.
    """
    path = Path(database_path)
    if path.parent and str(path.parent) not in ("", "."):
        path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _applied_versions(conn: sqlite3.Connection) -> set[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "  version TEXT PRIMARY KEY,"
        "  applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}


def pending_migrations(conn: sqlite3.Connection) -> list[Path]:
    applied = _applied_versions(conn)
    return [path for path in sorted(MIGRATIONS_DIR.glob("*.sql")) if path.stem not in applied]


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply every pending migration. Returns the versions that ran."""
    applied: list[str] = []
    for path in pending_migrations(conn):
        with conn:
            conn.executescript(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (path.stem,))
        applied.append(path.stem)
    return applied


def in_memory() -> sqlite3.Connection:
    """A migrated, throwaway database. Used by the test suite."""
    conn = connect(":memory:")
    apply_migrations(conn)
    return conn
