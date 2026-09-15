"""Behaviour that is specific to one carrier, including the legacy Pigeon quirks."""

from __future__ import annotations

import pytest

from freightline.carriers import get_carrier
from freightline.carriers.pigeon import looks_like_pigeon
from freightline.errors import ValidationError
from freightline.models import ServiceLevel, ShipmentStatus


def test_atlas_accepts_formatted_tracking_numbers():
    atlas = get_carrier("atlas")
    assert atlas.normalize_tracking_number("atl-1234 5678 9012") == "ATL123456789012"


def test_atlas_rejects_a_wrong_length_tracking_number():
    with pytest.raises(ValidationError):
        get_carrier("atlas").normalize_tracking_number("ATL123")


def test_borealis_does_not_offer_ground():
    assert get_carrier("borealis").supports(ServiceLevel.GROUND) is False


def test_borealis_customs_hold_is_an_exception():
    assert get_carrier("borealis").map_status("CUSTOMS_HOLD") is ShipmentStatus.EXCEPTION


def test_carrier_lookup_is_case_insensitive():
    assert get_carrier("ATLAS").profile.code == "atlas"


def test_pigeon_still_accepts_the_pre_2019_format():
    assert get_carrier("pigeon").normalize_tracking_number("PP-123 456 789") == "PP123456789"


def test_pigeon_accepts_the_current_format():
    assert get_carrier("pigeon").normalize_tracking_number("pgn1234567890") == "PGN1234567890"


def test_pigeon_generates_only_the_current_format():
    assert get_carrier("pigeon").generate_tracking_number().startswith("PGN")


def test_pigeon_tolerates_whitespace_around_status_codes():
    """The v1 gateway pads its fixed-width fields with spaces."""
    assert get_carrier("pigeon").map_status("  40  ") is ShipmentStatus.DELIVERED


def test_pigeon_maps_numeric_status_codes():
    pigeon = get_carrier("pigeon")
    assert pigeon.map_status("40") is ShipmentStatus.DELIVERED
    assert pigeon.map_status("50") is ShipmentStatus.EXCEPTION


def test_pigeon_rejects_unknown_status_codes():
    with pytest.raises(ValueError):
        get_carrier("pigeon").map_status("99")


@pytest.mark.parametrize(
    "value,expected",
    [("PP123456789", True), ("PGN1234567890", True), ("ATL123456789012", False), ("", False)],
)
def test_pigeon_sniffer(value, expected):
    assert looks_like_pigeon(value) is expected
