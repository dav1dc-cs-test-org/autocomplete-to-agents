"""Carrier registry.

The single place that knows which integrations exist. The API, the CLI, the
rating engine, and the tracking normalizer all resolve carriers through here, so
registering a new carrier is one line — and then the contract tests tell you
about the other five places that need to change.
"""

from __future__ import annotations

from ..errors import UnknownCarrierError
from .atlas import AtlasCarrier
from .base import CarrierAdapter
from .borealis import BorealisCarrier
from .pigeon import PigeonCarrier

_REGISTRY: dict[str, CarrierAdapter] = {
    AtlasCarrier.profile.code: AtlasCarrier(),
    BorealisCarrier.profile.code: BorealisCarrier(),
    PigeonCarrier.profile.code: PigeonCarrier(),
}


def get_carrier(code: str) -> CarrierAdapter:
    """Resolve a carrier code, or raise with the list of valid codes."""
    key = code.strip().lower()
    adapter = _REGISTRY.get(key)
    if adapter is None:
        raise UnknownCarrierError(
            f"unknown carrier {code!r}",
            details={"carrier_code": code, "known": all_carrier_codes()},
        )
    return adapter


def all_carriers() -> tuple[CarrierAdapter, ...]:
    return tuple(_REGISTRY[code] for code in all_carrier_codes())


def all_carrier_codes() -> list[str]:
    return sorted(_REGISTRY)


def is_registered(code: str) -> bool:
    return code.strip().lower() in _REGISTRY
