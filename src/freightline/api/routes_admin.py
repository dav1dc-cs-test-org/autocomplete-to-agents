"""Reporting endpoints. Behind the admin bearer token."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from ..reporting import summarize_by_carrier, summarize_by_status, to_csv
from ..service import FreightlineService
from ..storage.repository import SearchFilters
from .deps import get_service, require_admin

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])

REPORT_LIMIT = 200


@router.get("/reports/carriers", summary="Spend and exception rate per carrier")
def carrier_report(
    service: FreightlineService = Depends(get_service),
) -> list[dict[str, object]]:
    shipments = service.repo.search(SearchFilters(), limit=REPORT_LIMIT)
    return [
        {
            "carrier_code": summary.carrier_code,
            "shipment_count": summary.shipment_count,
            "total": str(summary.total.amount),
            "average": str(summary.average.amount),
            "delivered": summary.delivered,
            "exceptions": summary.exceptions,
            "exception_rate": str(summary.exception_rate),
            "currency": summary.total.currency,
        }
        for summary in summarize_by_carrier(shipments)
    ]


@router.get("/reports/statuses", summary="Shipment counts per canonical status")
def status_report(service: FreightlineService = Depends(get_service)) -> dict[str, int]:
    return summarize_by_status(service.repo.search(SearchFilters(), limit=REPORT_LIMIT))


@router.get("/reports/export.csv", summary="CSV export for finance")
def export_csv(service: FreightlineService = Depends(get_service)) -> Response:
    body = to_csv(service.repo.search(SearchFilters(), limit=REPORT_LIMIT))
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="shipments.csv"'},
    )
