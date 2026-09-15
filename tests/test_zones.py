from __future__ import annotations

import pytest

from freightline.errors import ValidationError
from freightline.models import Address
from freightline.rating.zones import ZONE_MAX, ZONE_MIN, is_remote, resolve_zone


def us(postal_code: str, *, residential: bool = False) -> Address:
    return Address(
        line1="-",
        city="-",
        region="-",
        postal_code=postal_code,
        residential=residential,
    )


def test_same_band_is_zone_one():
    assert resolve_zone(us("94105"), us("94110")) == 1


def test_coast_to_coast_is_a_high_zone():
    assert resolve_zone(us("94105"), us("10001")) == 7


def test_zone_is_symmetric():
    assert resolve_zone(us("94105"), us("10001")) == resolve_zone(us("10001"), us("94105"))


@pytest.mark.parametrize("origin,destination", [("94105", "10001"), ("60601", "30301")])
def test_zone_stays_within_published_range(origin, destination):
    zone = resolve_zone(us(origin), us(destination))
    assert ZONE_MIN <= zone <= ZONE_MAX


def test_international_lane_has_a_zone_floor():
    canada = Address(line1="-", city="-", region="-", postal_code="M5V3L9", country="CA")
    assert resolve_zone(us("10001"), canada) >= 5


def test_unknown_country_is_rejected():
    antarctica = Address(line1="-", city="-", region="-", postal_code="0000", country="AQ")
    with pytest.raises(ValidationError):
        resolve_zone(us("10001"), antarctica)


def test_postal_codes_are_normalized_before_lookup():
    assert resolve_zone(us(" 94105 "), us("94110")) == 1


def test_remote_areas_are_flagged():
    assert is_remote(us("99501")) is True
    assert is_remote(us("10001")) is False
