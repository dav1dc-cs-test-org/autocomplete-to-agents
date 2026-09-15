"""Shipment and tracking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response, status

from ..config import Settings
from ..models import ShipmentStatus
from ..service import FreightlineService
from ..storage.repository import SORTABLE_COLUMNS, SearchFilters
from ..tracking.webhooks import verify_signature
from .deps import get_service, settings
from .mapping import from_event, from_shipment, to_quote_request
from .schemas import ShipmentIn, ShipmentOut, ShipmentPage, TrackingEventOut

router = APIRouter(tags=["shipments"])

DEFAULT_LIMIT = 50


@router.post(
    "/v1/shipments",
    response_model=ShipmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a shipment",
)
def create_shipment(
    payload: ShipmentIn,
    service: FreightlineService = Depends(get_service),
) -> ShipmentOut:
    shipment = service.create_shipment(to_quote_request(payload), reference=payload.reference)
    return from_shipment(shipment)


@router.get("/v1/shipments", response_model=ShipmentPage, summary="Search shipments")
def search_shipments(
    carrier_code: str | None = None,
    shipment_status: ShipmentStatus | None = Query(default=None, alias="status"),
    reference: str | None = None,
    sort_by: str = Query(default="created_at"),
    direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: FreightlineService = Depends(get_service),
) -> ShipmentPage:
    filters = SearchFilters(
        carrier_code=carrier_code, status=shipment_status, reference=reference
    )
    items = service.repo.search(
        filters, sort_by=sort_by, direction=direction, limit=limit, offset=offset
    )
    return ShipmentPage(
        items=[from_shipment(item) for item in items],
        total=service.repo.count(filters),
        limit=limit,
        offset=offset,
    )


@router.get("/v1/shipments/sortable", summary="Columns accepted by sort_by")
def sortable_columns() -> dict[str, list[str]]:
    return {"sortable": sorted(SORTABLE_COLUMNS)}


@router.get("/v1/shipments/{shipment_id}", response_model=ShipmentOut, summary="Fetch a shipment")
def get_shipment(
    shipment_id: str,
    service: FreightlineService = Depends(get_service),
) -> ShipmentOut:
    return from_shipment(service.get(shipment_id))


@router.get(
    "/v1/shipments/{shipment_id}/events",
    response_model=list[TrackingEventOut],
    summary="Tracking history",
)
def get_events(
    shipment_id: str,
    service: FreightlineService = Depends(get_service),
) -> list[TrackingEventOut]:
    service.get(shipment_id)
    return [from_event(event) for event in service.repo.events_for(shipment_id)]


@router.post(
    "/v1/webhooks/{carrier_code}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Carrier tracking webhook",
)
async def receive_webhook(
    carrier_code: str,
    request: Request,
    response: Response,
    service: FreightlineService = Depends(get_service),
    config: Settings = Depends(settings),
) -> dict[str, object]:
    """Verify the HMAC over the raw body *before* parsing it."""
    raw_body = await request.body()
    verify_signature(
        config.webhook_secret, raw_body, request.headers.get("x-freightline-signature", "")
    )

    import json

    payload = json.loads(raw_body.decode("utf-8"))
    touched = service.ingest_tracking(carrier_code, payload)
    return {"accepted": len(touched), "shipment_ids": touched}
