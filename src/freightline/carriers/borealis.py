"""Borealis Air: time-definite air freight, no ground product."""

from __future__ import annotations

from ..models import ServiceLevel, ShipmentStatus
from .base import BaseCarrier, CarrierProfile


class BorealisCarrier(BaseCarrier):
    profile = CarrierProfile(
        code="borealis",
        name="Borealis Air",
        services=(ServiceLevel.EXPRESS, ServiceLevel.OVERNIGHT),
        tracking_pattern=r"BX[A-Z]\d{9}",
        tracking_template="BX@#########",
        supports_saturday_delivery=True,
        supports_international=True,
    )

    STATUS_MAP = {
        "BOOKED": ShipmentStatus.CREATED,
        "TENDERED": ShipmentStatus.CREATED,
        "UPLIFT": ShipmentStatus.IN_TRANSIT,
        "IN_FLIGHT": ShipmentStatus.IN_TRANSIT,
        "CUSTOMS_HOLD": ShipmentStatus.EXCEPTION,
        "CUSTOMS_CLEARED": ShipmentStatus.IN_TRANSIT,
        "LAST_MILE": ShipmentStatus.OUT_FOR_DELIVERY,
        "DELIVERED": ShipmentStatus.DELIVERED,
        "MISROUTED": ShipmentStatus.EXCEPTION,
        "RETURN_TO_SHIPPER": ShipmentStatus.RETURNED,
    }
