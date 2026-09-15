"""Zone resolution.

A "zone" is the distance band between origin and destination, 1 (same metro)
through 8 (longest haul). Domestic zones come from the postal-code band table;
international lanes get a floor so cross-border never prices as a local move.
"""

from __future__ import annotations

from ..errors import ValidationError
from ..models import Address

ZONE_MIN = 1
ZONE_MAX = 8
INTERNATIONAL_ZONE_FLOOR = 5

# First digit of a US ZIP maps to a coarse geographic band.
_US_BANDS: dict[str, int] = {
    "0": 1,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 4,
    "6": 5,
    "7": 5,
    "8": 6,
    "9": 7,
}

# Non-US countries get a single band each. Good enough for rating; the carriers
# re-rate internationally at pickup anyway.
_COUNTRY_BANDS: dict[str, int] = {
    "CA": 8,
    "MX": 9,
    "GB": 12,
    "IE": 12,
    "FR": 13,
    "DE": 13,
    "NL": 13,
    "ES": 14,
    "IT": 14,
    "JP": 20,
    "AU": 22,
}

# Sparsely served destinations that carriers bill as remote.
REMOTE_POSTAL_PREFIXES: frozenset[str] = frozenset(
    {"995", "996", "997", "998", "999", "967", "968", "889"}
)


def region_band(address: Address) -> int:
    """Map an address to its coarse band. Raises if the country is unknown."""
    if address.country == "US":
        first = address.normalized_postal_code[:1]
        if first not in _US_BANDS:
            raise ValidationError(
                f"unrecognised US postal code {address.postal_code!r}",
                details={"postal_code": address.postal_code},
            )
        return _US_BANDS[first]
    band = _COUNTRY_BANDS.get(address.country)
    if band is None:
        raise ValidationError(
            f"no zone band configured for country {address.country!r}",
            details={"country": address.country, "supported": sorted(_COUNTRY_BANDS)},
        )
    return band


def resolve_zone(origin: Address, destination: Address) -> int:
    """Distance band between two addresses, clamped to 1..8."""
    distance = abs(region_band(origin) - region_band(destination))
    zone = distance + 1
    if origin.country != destination.country:
        zone = max(zone, INTERNATIONAL_ZONE_FLOOR)
    return max(ZONE_MIN, min(zone, ZONE_MAX))


def is_remote(address: Address) -> bool:
    """True when the destination sits in a carrier-declared remote area."""
    if address.country != "US":
        return False
    return address.normalized_postal_code[:3] in REMOTE_POSTAL_PREFIXES
