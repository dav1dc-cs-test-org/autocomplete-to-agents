"""Quote and carrier endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..carriers import all_carriers
from ..service import FreightlineService
from .deps import get_service
from .mapping import from_carrier_profile, from_quote, to_quote_request
from .schemas import CarrierOut, QuoteIn, QuoteOut

router = APIRouter(tags=["rating"])


@router.post("/v1/quotes", response_model=QuoteOut, summary="Price a shipment")
def create_quote(
    payload: QuoteIn,
    service: FreightlineService = Depends(get_service),
) -> QuoteOut:
    return from_quote(service.quote(to_quote_request(payload)))


@router.get("/v1/carriers", response_model=list[CarrierOut], summary="List carriers")
def list_carriers() -> list[CarrierOut]:
    return [from_carrier_profile(carrier.profile) for carrier in all_carriers()]
