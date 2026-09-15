from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from freightline.models import Parcel
from freightline.money import Money
from freightline.rating.surcharges import SURCHARGES, FuelSurcharge, build_lines


def codes(request) -> list[str]:
    return [line.code for line in build_lines(request, Money.parse("20.00"))]


def test_no_optional_surcharges_on_a_plain_commercial_parcel(quote_request):
    assert codes(quote_request) == ["fuel"]


def test_residential_delivery_adds_a_line(quote_request, nyc_home):
    assert "residential" in codes(replace(quote_request, destination=nyc_home))


def test_remote_area_adds_a_line(quote_request, anchorage):
    assert "remote_area" in codes(replace(quote_request, destination=anchorage))


def test_saturday_delivery_adds_a_line(quote_request):
    assert "saturday_delivery" in codes(replace(quote_request, saturday_delivery=True))


def test_oversize_parcel_adds_a_line(quote_request):
    oversize = replace(
        quote_request,
        parcel=Parcel(
            weight_kg=Decimal("5"),
            length_cm=Decimal("150"),
            width_cm=Decimal("40"),
            height_cm=Decimal("40"),
        ),
    )
    assert "oversize" in codes(oversize)


def test_heavy_parcel_adds_a_line(quote_request):
    heavy = replace(
        quote_request,
        parcel=Parcel(
            weight_kg=Decimal("35"),
            length_cm=Decimal("40"),
            width_cm=Decimal("30"),
            height_cm=Decimal("30"),
        ),
    )
    assert "heavyweight" in codes(heavy)


def test_fuel_is_always_last(quote_request, nyc_home):
    assert codes(replace(quote_request, destination=nyc_home))[-1] == "fuel"


def test_fuel_compounds_on_the_flat_surcharges(quote_request, nyc_home):
    lines = build_lines(replace(quote_request, destination=nyc_home), Money.parse("20.00"))
    residential = next(line for line in lines if line.code == "residential")
    fuel = next(line for line in lines if line.code == "fuel")
    expected_subtotal = Money.parse("20.00").plus(residential.amount)
    assert fuel.amount == expected_subtotal.times(Decimal("0.155"))


def test_surcharge_codes_are_unique():
    all_codes = [surcharge.code for surcharge in SURCHARGES]
    assert len(all_codes) == len(set(all_codes))


def test_fuel_surcharge_is_registered_exactly_once():
    assert sum(isinstance(s, FuelSurcharge) for s in SURCHARGES) == 1
