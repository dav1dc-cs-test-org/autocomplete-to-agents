from __future__ import annotations

from decimal import Decimal

import pytest

from freightline.errors import ValidationError
from freightline.money import Money, sum_money


def test_parse_keeps_exact_cents():
    assert Money.parse("12.34").cents == 1234


def test_parse_rounds_half_up():
    assert Money.parse("0.005").cents == 1
    assert Money.parse("0.004").cents == 0


def test_amount_round_trips():
    assert Money.parse("99.99").amount == Decimal("99.99")


def test_addition_and_subtraction():
    assert Money.parse("10.00").plus(Money.parse("2.50")).amount == Decimal("12.50")
    assert Money.parse("10.00").minus(Money.parse("2.50")).amount == Decimal("7.50")


def test_multiplication_rounds_once():
    # 20.00 * 0.155 = 3.10 exactly; no float drift is permitted anywhere in between.
    assert Money.parse("20.00").times(Decimal("0.155")).amount == Decimal("3.10")


def test_mixing_currencies_is_rejected():
    with pytest.raises(ValidationError):
        Money.parse("1.00", "USD").plus(Money.parse("1.00", "EUR"))


def test_unsupported_currency_is_rejected():
    with pytest.raises(ValidationError):
        Money(100, "XYZ")


def test_float_cents_are_rejected():
    with pytest.raises(ValidationError):
        Money(100.5, "USD")  # type: ignore[arg-type]


def test_sum_of_empty_list_is_zero():
    assert sum_money([]).is_zero()


def test_sum_money_totals():
    values = [Money.parse("1.11"), Money.parse("2.22"), Money.parse("3.33")]
    assert sum_money(values).amount == Decimal("6.66")


def test_money_is_ordered():
    assert Money.parse("1.00") < Money.parse("2.00")
