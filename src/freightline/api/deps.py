"""Request-scoped dependencies."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, status

from ..config import Settings, get_settings
from ..service import FreightlineService
from ..storage.db import apply_migrations, connect


def get_connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    conn = connect(settings.database_path)
    apply_migrations(conn)
    try:
        yield conn
    finally:
        conn.close()


def get_service(
    conn: sqlite3.Connection = Depends(get_connection),
) -> FreightlineService:
    return FreightlineService(conn)


def settings() -> Settings:
    return get_settings()


def require_admin(
    authorization: str = Header(default=""),
    config: Settings = Depends(settings),
) -> None:
    """Bearer-token gate for the admin surface.

    Fails closed: if no admin token is configured, the surface is unavailable
    rather than open.
    """
    import hmac

    if not config.admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin surface is not configured",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token, config.admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
