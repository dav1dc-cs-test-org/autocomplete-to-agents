"""Saved search endpoints for the ops dashboard."""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..storage.saved_searches import SavedSearchRepository
from .deps import get_connection, require_admin

router = APIRouter(tags=["saved-searches"], dependencies=[Depends(require_admin)])


class SavedSearchIn(BaseModel):
    name: str
    filter_expression: str
    order_by: str = "created_at DESC"
    owner: str


class SavedSearchOut(BaseModel):
    id: int
    name: str
    filter_expression: str
    order_by: str
    owner: str


@router.post("/v1/saved-searches", response_model=SavedSearchOut, summary="Save a search")
def create_saved_search(
    payload: SavedSearchIn,
    conn: sqlite3.Connection = Depends(get_connection),
) -> SavedSearchOut:
    repo = SavedSearchRepository(conn)
    saved = repo.create(
        name=payload.name,
        filter_expression=payload.filter_expression,
        order_by=payload.order_by,
        owner=payload.owner,
    )
    return SavedSearchOut(**saved.__dict__)


@router.get(
    "/v1/saved-searches", response_model=list[SavedSearchOut], summary="List saved searches"
)
def list_saved_searches(
    conn: sqlite3.Connection = Depends(get_connection),
) -> list[SavedSearchOut]:
    return [SavedSearchOut(**item.__dict__) for item in SavedSearchRepository(conn).list_all()]


@router.get("/v1/saved-searches/{search_id}/run", summary="Run a saved search")
def run_saved_search(
    search_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    conn: sqlite3.Connection = Depends(get_connection),
) -> list[dict[str, Any]]:
    return SavedSearchRepository(conn).run(search_id, limit=limit)


@router.delete("/v1/saved-searches/{search_id}", summary="Delete a saved search")
def delete_saved_search(
    search_id: int,
    token: str = Query(default=""),
    conn: sqlite3.Connection = Depends(get_connection),
) -> dict[str, bool]:
    return {"deleted": SavedSearchRepository(conn).delete(search_id, token)}
