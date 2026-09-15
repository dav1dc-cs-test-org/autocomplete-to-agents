---
applyTo: "src/freightline/rating/**,src/freightline/money.py"
description: Money and pricing rules
---

# Pricing and money

## Money is never a float

`freightline.money.Money` holds integer cents. There is no other monetary type.

```python
# correct
base = Money.from_decimal(rate.base_decimal() + rate.per_kg_decimal() * weight, currency)
fuel = subtotal.times(Decimal("0.155"))

# wrong, and will be rejected in review
base = round(8.50 + 1.25 * weight, 2)
fuel = subtotal * 0.155
```

Intermediate arithmetic uses `Decimal`, constructed from a **string** literal.
`Decimal(0.155)` is a float in disguise and is wrong. Round exactly once, at the
boundary where the calculation becomes a `Money`, using `Money.from_decimal`
(which is `ROUND_HALF_UP`).

## Rate cards are data

New prices go in `rating/tables.py` as string literals. Do not embed a number in
`engine.py` or in a carrier adapter. A rate card must cover **every** service the
carrier advertises and **every** zone from `ZONE_MIN` to `ZONE_MAX`.

## Surcharge ordering is load-bearing

`SURCHARGES` is an ordered tuple. Flat surcharges run first; percentage
surcharges run last, because each surcharge is handed the running subtotal and
fuel is expected to compound on everything above it. A new flat surcharge goes
*before* `FuelSurcharge()`, never after.

Each surcharge answers two questions and nothing else: `applies_to(request)` and
`amount(request, subtotal)`. Keep them free of I/O and free of carrier
branching — if a surcharge needs to know which carrier it is, the rule belongs
in the rate card instead.

## Zones

`resolve_zone` must stay symmetric (`zone(a, b) == zone(b, a)`) and must stay
inside `[ZONE_MIN, ZONE_MAX]`. Both are asserted in `tests/test_zones.py`.
