"""The carrier contract.

Every registered carrier must satisfy all of these. They are parameterised over
the registry, so registering a new carrier immediately produces a checklist of
everything else that has to change: rate card, zone coverage, tracking format,
status vocabulary, and the architecture doc.

If you are adding a carrier and one of these fails, the failure message is the
instruction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from freightline.carriers import all_carrier_codes, get_carrier
from freightline.carriers.base import CarrierAdapter
from freightline.models import ShipmentStatus
from freightline.rating.tables import RATE_CARDS, services_for
from freightline.rating.zones import ZONE_MAX, ZONE_MIN

ARCHITECTURE_DOC = Path(__file__).resolve().parents[1] / "docs" / "ARCHITECTURE.md"

CARRIER_CODES = all_carrier_codes()


@pytest.fixture(params=CARRIER_CODES, ids=CARRIER_CODES)
def carrier(request):
    return get_carrier(request.param)


def test_at_least_three_carriers_are_registered():
    assert len(CARRIER_CODES) >= 3


def test_registry_key_matches_profile_code(carrier):
    assert get_carrier(carrier.profile.code) is carrier


def test_adapter_satisfies_the_protocol(carrier):
    assert isinstance(carrier, CarrierAdapter)


def test_carrier_has_a_published_rate_card(carrier):
    code = carrier.profile.code
    assert code in RATE_CARDS, (
        f"{code!r} is registered but has no entry in freightline.rating.tables.RATE_CARDS"
    )


def test_rate_card_covers_exactly_the_advertised_services(carrier):
    code = carrier.profile.code
    assert set(services_for(code)) == set(carrier.profile.services), (
        f"{code!r} advertises {[s.value for s in carrier.profile.services]} "
        f"but publishes rates for {[s.value for s in services_for(code)]}"
    )


def test_every_service_prices_every_zone(carrier):
    for service in carrier.profile.services:
        rate = RATE_CARDS[carrier.profile.code][service]
        missing = [
            zone for zone in range(ZONE_MIN, ZONE_MAX + 1) if zone not in rate.zone_multipliers
        ]
        assert not missing, f"{carrier.profile.code}/{service.value} is missing zones {missing}"


def test_generated_tracking_numbers_validate(carrier):
    generated = carrier.generate_tracking_number()
    assert carrier.normalize_tracking_number(generated) == generated


def test_tracking_normalisation_is_idempotent(carrier):
    generated = carrier.generate_tracking_number()
    once = carrier.normalize_tracking_number(generated)
    assert carrier.normalize_tracking_number(once) == once


def test_status_map_covers_the_canonical_vocabulary(carrier):
    mapped = set(carrier.STATUS_MAP.values())
    missing = [status.value for status in ShipmentStatus if status not in mapped]
    assert not missing, (
        f"{carrier.profile.code!r} never maps any carrier code to {missing}; "
        "every canonical status must be reachable"
    )


def test_status_map_only_emits_canonical_statuses(carrier):
    for code, status in carrier.STATUS_MAP.items():
        assert isinstance(status, ShipmentStatus), f"{carrier.profile.code}:{code} is not canonical"


def test_carrier_is_documented_in_the_architecture_doc(carrier):
    doc = ARCHITECTURE_DOC.read_text(encoding="utf-8")
    assert f"`{carrier.profile.code}`" in doc, (
        f"add {carrier.profile.code!r} to the carrier panel table in docs/ARCHITECTURE.md"
    )
    assert carrier.profile.name in doc


def test_unknown_carrier_lookup_lists_the_known_ones():
    from freightline.errors import UnknownCarrierError

    with pytest.raises(UnknownCarrierError) as excinfo:
        get_carrier("teleport")
    assert excinfo.value.details["known"] == CARRIER_CODES
