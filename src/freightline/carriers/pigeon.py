# Pigeon Post integration.
#
# Written in 2016 against the PigeonPost v1 SOAP gateway and never revisited.
# It predates BaseCarrier, the CarrierProfile dataclass, and type hints. It works,
# it is covered by tests, and nobody wants to touch it.
#
# Known issues (see docs/adr/0003-legacy-pigeon.md):
#   * Does not inherit from BaseCarrier, so it duplicates normalisation logic.
#   * Status codes are numeric strings from the old gateway, mapped by hand.
#   * Tracking numbers have two historical formats that both still circulate.
#   * Raises ValueError instead of freightline.errors.ValidationError.
#
# MIGRATION TARGET: this module is the subject of the `legacy-migrator` custom agent.

from __future__ import annotations

import random
import re

from ..models import ServiceLevel, ShipmentStatus
from .base import CarrierProfile

CARRIER_CODE = "pigeon"
CARRIER_NAME = "Pigeon Post"

# Format A (pre-2019): PP + 9 digits.  Format B (current): PGN + 10 digits.
OLD_FORMAT = "PP"
NEW_FORMAT = "PGN"

STATUS_CODES = {
    "10": "created",
    "11": "created",
    "20": "in_transit",
    "21": "in_transit",
    "22": "in_transit",
    "30": "out_for_delivery",
    "40": "delivered",
    "41": "delivered",
    "50": "exception",
    "51": "exception",
    "52": "exception",
    "60": "returned",
    "61": "returned",
}


class PigeonCarrier:
    profile = CarrierProfile(
        code=CARRIER_CODE,
        name=CARRIER_NAME,
        services=(ServiceLevel.ECONOMY, ServiceLevel.GROUND),
        tracking_pattern=r"(PP\d{9}|PGN\d{10})",
        tracking_template="PGN##########",
        supports_saturday_delivery=False,
        supports_international=False,
    )

    STATUS_MAP = {code: ShipmentStatus(value) for code, value in STATUS_CODES.items()}

    def generate_tracking_number(self):
        # New shipments always get the current format; PP numbers are read-only history.
        n = ""
        for _ in range(10):
            n = n + random.choice("0123456789")  # noqa: S311 - not a security token
        return NEW_FORMAT + n

    def normalize_tracking_number(self, raw):
        if raw is None:
            raise ValueError("tracking number is required")
        t = str(raw).replace(" ", "").replace("-", "").upper()
        if t.startswith(OLD_FORMAT) and not t.startswith(NEW_FORMAT):
            if len(t) == 11 and t[2:].isdigit():
                return t
            raise ValueError("bad legacy pigeon tracking number: " + str(raw))
        if t.startswith(NEW_FORMAT):
            if len(t) == 13 and t[3:].isdigit():
                return t
            raise ValueError("bad pigeon tracking number: " + str(raw))
        raise ValueError("unrecognised pigeon tracking number: " + str(raw))

    def map_status(self, carrier_status_code):
        c = str(carrier_status_code).strip()
        # The gateway zero-pads inconsistently depending on which datacentre answers.
        if len(c) == 1:
            c = "0" + c
        if c in STATUS_CODES:
            return ShipmentStatus(STATUS_CODES[c])
        raise ValueError("unknown pigeon status code: " + str(carrier_status_code))

    def supports(self, service):
        return service in self.profile.services

    def legacy_label_payload(self, shipment):
        """Builds the flat pipe-delimited record the v1 gateway still expects."""
        parts = [
            "LBL",
            shipment.tracking_number,
            shipment.origin_postal_code,
            shipment.destination_postal_code,
            str(shipment.total_cents),
            shipment.currency,
        ]
        return "|".join(parts)


def looks_like_pigeon(tracking_number):
    """Cheap sniff used by the inbound webhook router."""
    if not tracking_number:
        return False
    return bool(re.match(r"^(PP\d{9}|PGN\d{10})$", str(tracking_number).upper()))
