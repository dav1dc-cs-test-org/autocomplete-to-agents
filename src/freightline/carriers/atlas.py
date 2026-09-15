"""Atlas Freight: our highest-volume domestic carrier."""

from __future__ import annotations

from ..models import ServiceLevel, ShipmentStatus
from .base import BaseCarrier, CarrierProfile


class AtlasCarrier(BaseCarrier):
    profile = CarrierProfile(
        code="atlas",
        name="Atlas Freight",
        services=(ServiceLevel.GROUND, ServiceLevel.EXPRESS, ServiceLevel.OVERNIGHT),
        tracking_pattern=r"ATL\d{12}",
        tracking_template="ATL############",
        supports_saturday_delivery=True,
        supports_international=True,
    )

    STATUS_MAP = {
        "MANIFESTED": ShipmentStatus.CREATED,
        "PICKED_UP": ShipmentStatus.IN_TRANSIT,
        "DEPARTED_HUB": ShipmentStatus.IN_TRANSIT,
        "ARRIVED_HUB": ShipmentStatus.IN_TRANSIT,
        "ON_VEHICLE": ShipmentStatus.OUT_FOR_DELIVERY,
        "DELIVERED": ShipmentStatus.DELIVERED,
        "POD_SIGNED": ShipmentStatus.DELIVERED,
        "DELAYED": ShipmentStatus.EXCEPTION,
        "DAMAGED": ShipmentStatus.EXCEPTION,
        "REFUSED": ShipmentStatus.RETURNED,
        "RTS": ShipmentStatus.RETURNED,
    }
