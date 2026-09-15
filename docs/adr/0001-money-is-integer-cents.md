# ADR-0001: Money is integer cents

- **Status**: accepted
- **Date**: 2025-11-04

## Context

The original rating code used `float` for prices. Two incidents followed:

1. A fuel surcharge of `subtotal * 0.155` produced `3.1000000000000005` on some
   inputs, which reached an invoice line as `3.1000000000000005`.
2. Totals computed as the sum of floated lines disagreed with totals computed
   from the floated subtotal, by a cent, on roughly one quote in four hundred.
   Finance found it during reconciliation, not us.

## Decision

`freightline.money.Money` holds an `int` of minor units and a currency. It is the
only monetary type in the codebase.

Intermediate arithmetic uses `Decimal`, always constructed from a string. A
calculation rounds exactly once, at the point it becomes a `Money`, via
`Money.from_decimal` (`ROUND_HALF_UP`).

Rate cards store amounts as **strings** so they parse to exact `Decimal` values.
`ServiceRate.base` is `"8.50"`, never `8.50`.

## Consequences

- `Money(100.5)` raises. That is deliberate — it catches a float leaking in at
  the boundary rather than four layers deeper.
- Currency mixing raises rather than coercing.
- Division is not implemented. `CarrierSummary.average` does integer division on
  cents and accepts the truncation, because an average is a reporting figure and
  never appears on an invoice.
- Every test that asserts on a price asserts on `Money` or `Decimal`, never on a
  float literal.

## Rejected alternatives

- **`decimal.Decimal` everywhere.** Correct, but nothing stops a `Decimal` from
  carrying more precision than a currency has, and nothing forces the rounding to
  happen exactly once.
- **A third-party money library.** More capability than we need, and the
  conversion rules would still have to be written down somewhere.
