"""The carrier adapter contract.

Every integration implements :class:`CarrierAdapter`. The contract is
deliberately narrow: rating lives in ``freightline.rating`` and is table-driven,
so an adapter only has to describe identity, tracking-number shape, and how the
carrier's own status vocabulary maps onto ours.

``tests/test_carrier_contract.py`` enforces this for every registered carrier.
Anything you add here becomes a requirement for all of them.
"""

from __future__ import annotations

import re
import secrets
import string
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ..errors import ValidationError
from ..models import ServiceLevel, ShipmentStatus

DIGIT_SLOT = "#"
LETTER_SLOT = "@"


@dataclass(frozen=True)
class CarrierProfile:
    """Static facts about a carrier, surfaced by ``GET /v1/carriers``.

    ``tracking_template`` is the generator counterpart of ``tracking_pattern``:
    ``#`` becomes a digit and ``@`` becomes an uppercase letter. Anything a
    carrier generates must validate against its own pattern, which is what
    ``tests/test_carrier_contract.py`` checks.
    """

    code: str
    name: str
    services: tuple[ServiceLevel, ...]
    tracking_pattern: str
    tracking_template: str
    supports_saturday_delivery: bool = False
    supports_international: bool = False


@runtime_checkable
class CarrierAdapter(Protocol):
    """What every carrier integration must provide."""

    profile: CarrierProfile

    def normalize_tracking_number(self, raw: str) -> str:
        """Strip carrier-specific formatting and validate the shape."""
        ...

    def generate_tracking_number(self) -> str:
        """Mint a new tracking number in this carrier's format."""
        ...

    def map_status(self, carrier_status_code: str) -> ShipmentStatus:
        """Translate a carrier status code into our canonical vocabulary."""
        ...

    def supports(self, service: ServiceLevel) -> bool: ...


def fill_template(template: str) -> str:
    """Expand ``#``/``@`` slots in a tracking template."""
    out: list[str] = []
    for char in template:
        if char == DIGIT_SLOT:
            out.append(secrets.choice(string.digits))
        elif char == LETTER_SLOT:
            out.append(secrets.choice(string.ascii_uppercase))
        else:
            out.append(char)
    return "".join(out)


class BaseCarrier:
    """Shared behaviour. Subclasses set ``profile`` and ``STATUS_MAP``."""

    profile: CarrierProfile
    STATUS_MAP: dict[str, ShipmentStatus] = {}

    def generate_tracking_number(self) -> str:
        return fill_template(self.profile.tracking_template)

    def normalize_tracking_number(self, raw: str) -> str:
        candidate = re.sub(r"[\s\-]", "", raw).upper()
        if not re.fullmatch(self.profile.tracking_pattern, candidate):
            raise ValidationError(
                f"{raw!r} is not a valid {self.profile.name} tracking number",
                details={"carrier_code": self.profile.code, "value": raw},
            )
        return candidate

    def map_status(self, carrier_status_code: str) -> ShipmentStatus:
        key = carrier_status_code.strip().upper()
        if key not in self.STATUS_MAP:
            raise ValidationError(
                f"unknown {self.profile.name} status code {carrier_status_code!r}",
                details={"carrier_code": self.profile.code, "known": sorted(self.STATUS_MAP)},
            )
        return self.STATUS_MAP[key]

    def supports(self, service: ServiceLevel) -> bool:
        return service in self.profile.services
