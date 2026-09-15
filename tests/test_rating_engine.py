from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from freightline.errors import RateUnavailableError, UnsupportedServiceError
from freightline.models import Parcel, ServiceLevel
from freightline.money import Money, sum_money
from freightline.rating.engine import RatingEngine, billable_weight_kg, dimensional_weight_kg
from freightline.rating.tables import rate_for


@pytest.fixture()
def engine() -> RatingEngine:
    return RatingEngine()


def test_dimensional_weight_uses_the_carrier_divisor():
    # 30 x 20 x 15 = 9000 cm3; Atlas ground divides by 5000.
    assert dimensional_weight_kg(Decimal("9000"), 5000) == Decimal("1.80")


def test_billable_weight_is_the_greater_of_actual_and_dimensional(quote_request):
    rate = rate_for("atlas", ServiceLevel.GROUND)
    assert billable_weight_kg(quote_request, rate) == Decimal("2.50")


def test_bulky_light_parcel_bills_on_dimensional_weight(quote_request):
    bulky = replace(
        quote_request,
        parcel=Parcel(
            weight_kg=Decimal("1.0"),
            length_cm=Decimal("60"),
            width_cm=Decimal("50"),
            height_cm=Decimal("40"),
        ),
    )
    rate = rate_for("atlas", ServiceLevel.GROUND)
    # 120000 / 5000 = 24 kg dimensional, far above the 1 kg actual weight.
    assert billable_weight_kg(bulky, rate) == Decimal("24.00")


def test_quote_total_equals_the_sum_of_its_lines(engine, quote_request):
    quote = engine.quote(quote_request)
    assert quote.total == sum_money([line.amount for line in quote.lines], quote.currency)


def test_quote_always_starts_with_a_base_line(engine, quote_request):
    quote = engine.quote(quote_request)
    assert quote.lines[0].kind == "base"
    assert quote.lines[0].code == "base"


def test_fuel_is_the_last_line_and_a_percentage_of_everything_before_it(engine, quote_request):
    quote = engine.quote(quote_request)
    fuel = quote.lines[-1]
    assert fuel.code == "fuel"

    subtotal = sum_money([line.amount for line in quote.lines[:-1]], quote.currency)
    assert fuel.amount == subtotal.times(Decimal("0.155"))


def test_longer_lane_costs_more(engine, quote_request, sf, nyc):
    near = engine.quote(replace(quote_request, destination=sf))
    far = engine.quote(replace(quote_request, destination=nyc))
    assert far.total > near.total
    assert far.zone > near.zone


def test_minimum_charge_floors_a_tiny_parcel(engine, quote_request, sf):
    tiny = replace(
        quote_request,
        destination=sf,
        parcel=Parcel(
            weight_kg=Decimal("0.1"),
            length_cm=Decimal("10"),
            width_cm=Decimal("10"),
            height_cm=Decimal("5"),
        ),
    )
    quote = engine.quote(tiny)
    base = quote.line("base")
    assert base is not None
    assert base.amount == Money.parse("11.00")


def test_faster_service_costs_more(engine, quote_request):
    ground = engine.quote(quote_request)
    express = engine.quote(replace(quote_request, service=ServiceLevel.EXPRESS))
    assert express.total > ground.total


def test_unsupported_service_names_the_alternatives(engine, quote_request):
    with pytest.raises(UnsupportedServiceError) as excinfo:
        engine.quote(replace(quote_request, carrier_code="borealis"))
    assert "ground" in str(excinfo.value) or excinfo.value.details["supported"]


def test_unknown_carrier_has_no_rate_card(engine, quote_request):
    with pytest.raises(RateUnavailableError):
        engine.quote(replace(quote_request, carrier_code="teleport"))


def test_quote_breakdown_is_keyed_by_line_code(engine, quote_request):
    quote = engine.quote(quote_request)
    breakdown = quote.breakdown()
    assert set(breakdown) == {line.code for line in quote.lines}
