"""Application service layer.

The one place that composes rating, carriers, and storage. Both the HTTP API and
the CLI call into here, which is why neither of them contains business rules.
"""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from .carriers import get_carrier
from .errors import UnsupportedServiceError
from .models import Quote, QuoteRequest, Shipment, ShipmentStatus
from .rating import RatingEngine
from .storage.repository import SearchFilters, ShipmentRepository
from .tracking.normalizer import normalize_payload


class FreightlineService:
    def __init__(self, conn: sqlite3.Connection, engine: RatingEngine | None = None) -> None:
        self.repo = ShipmentRepository(conn)
        self.engine = engine or RatingEngine()

    def quote(self, request: QuoteRequest) -> Quote:
        """Price a request, rejecting service levels the carrier does not run."""
        carrier = get_carrier(request.carrier_code)
        if not carrier.supports(request.service):
            raise UnsupportedServiceError(
                f"{carrier.profile.name} does not offer {request.service.value}",
                details={
                    "carrier_code": carrier.profile.code,
                    "supported": [service.value for service in carrier.profile.services],
                },
            )
        return self.engine.quote(request)

    def create_shipment(self, request: QuoteRequest, *, reference: str | None = None) -> Shipment:
        """Quote, mint a tracking number, persist, and record the audit row."""
        carrier = get_carrier(request.carrier_code)
        priced = self.quote(request)

        shipment = Shipment(
            id=uuid.uuid4().hex,
            carrier_code=carrier.profile.code,
            service=request.service,
            tracking_number=carrier.generate_tracking_number(),
            origin_postal_code=request.origin.normalized_postal_code,
            destination_postal_code=request.destination.normalized_postal_code,
            status=ShipmentStatus.CREATED,
            total_cents=priced.total.cents,
            currency=priced.currency,
            reference=reference,
        )
        self.repo.create(shipment)
        self.repo.record_quote(priced, shipment_id=shipment.id)
        return shipment

    def ingest_tracking(self, carrier_code: str, payload: dict[str, Any]) -> list[str]:
        """Store normalized events and advance shipment status.

        The shipment is resolved first so an event for an unknown shipment fails
        as a domain error rather than a foreign-key violation.
        """
        events = normalize_payload(carrier_code, payload)
        touched: list[str] = []
        for event in events:
            self.repo.get(event.shipment_id)
            self.repo.append_event(event)
            self.repo.update_status(event.shipment_id, event.status)
            touched.append(event.shipment_id)
        return touched

    def search(self, filters: SearchFilters | None = None, **kwargs: Any) -> list[Shipment]:
        return self.repo.search(filters, **kwargs)

    def get(self, shipment_id: str) -> Shipment:
        return self.repo.get(shipment_id)
