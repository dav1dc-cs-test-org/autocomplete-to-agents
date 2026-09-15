"""Money arithmetic.

Everything monetary in Freightline is minor units (cents) held in an ``int``.
Floats are never used for money: rounding is explicit and happens once, at the
boundary where a :class:`~decimal.Decimal` computation becomes a ``Money``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .errors import ValidationError

CENTS = Decimal("0.01")
SUPPORTED_CURRENCIES = frozenset({"USD", "CAD", "EUR", "GBP"})


@dataclass(frozen=True, order=True)
class Money:
    """An exact monetary amount in minor units."""

    cents: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.currency not in SUPPORTED_CURRENCIES:
            raise ValidationError(
                f"unsupported currency {self.currency!r}",
                details={"supported": sorted(SUPPORTED_CURRENCIES)},
            )
        if not isinstance(self.cents, int):
            raise ValidationError("Money.cents must be an int (minor units)")

    @classmethod
    def zero(cls, currency: str = "USD") -> Money:
        return cls(0, currency)

    @classmethod
    def parse(cls, value: str | Decimal | int, currency: str = "USD") -> Money:
        """Build a Money from a major-unit value such as ``"12.50"``."""
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
        return cls.from_decimal(amount, currency)

    @classmethod
    def from_decimal(cls, amount: Decimal, currency: str = "USD") -> Money:
        quantized = amount.quantize(CENTS, rounding=ROUND_HALF_UP)
        return cls(int(quantized * 100), currency)

    @property
    def amount(self) -> Decimal:
        """The value in major units, exact to two places."""
        return (Decimal(self.cents) / 100).quantize(CENTS)

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValidationError(
                "cannot combine amounts in different currencies",
                details={"left": self.currency, "right": other.currency},
            )

    def plus(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.cents + other.cents, self.currency)

    def minus(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.cents - other.cents, self.currency)

    def times(self, factor: Decimal | int | str) -> Money:
        multiplier = factor if isinstance(factor, Decimal) else Decimal(str(factor))
        return Money.from_decimal(self.amount * multiplier, self.currency)

    def is_zero(self) -> bool:
        return self.cents == 0

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


def sum_money(items: list[Money], currency: str = "USD") -> Money:
    """Total a list of Money values, tolerating an empty list."""
    total = Money.zero(currency)
    for item in items:
        total = total.plus(item)
    return total
