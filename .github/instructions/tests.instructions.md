---
applyTo: "tests/**"
description: How this repository tests
---

# Tests

## Naming

A test name is a sentence about behaviour, readable in the failure output:

```python
def test_fuel_compounds_on_the_flat_surcharges(): ...
def test_search_rejects_an_unknown_sort_column(): ...
```

Not `test_fuel_2`, `test_search_error`, or `test_happy_path`.

## Shape

- One test module per source module. New source module, new test module.
- Use the fixtures in `conftest.py` (`conn`, `repo`, `service`, `sf`, `nyc`,
  `nyc_home`, `anchorage`, `small_parcel`, `quote_request`) rather than building
  addresses and parcels inline.
- Vary a fixture with `dataclasses.replace`, not by constructing a whole new
  request.
- Assert on invariants where you can: `quote.total == sum_money(line.amount for
  line in quote.lines)` survives a rate-card change; `assert quote.total.cents ==
  2310` does not.
- When a literal number is the point of the test, add a one-line comment saying
  where it came from.

## Rules that apply to every carrier

They go in `tests/test_carrier_contract.py`, parameterised over
`all_carrier_codes()`. Never copy a per-carrier test five times. The failure
message must tell the reader what to change — these tests are the onboarding
checklist for adding a carrier.

## Coverage expectations

- Every error path a caller can trigger has a test, and the test asserts on the
  error `code` or on `details`, never on the message string.
- Every bug fix ships with a regression test that fails without the fix.
- Security-relevant behaviour is tested as behaviour: a hostile `reference` value
  is matched literally, an unknown `sort_by` is rejected, an unsigned webhook is
  refused.

## What not to do

- No `time.sleep`. Inject a clock or a `sleep` callable.
- No network calls. Carrier adapters are pure; if one ever is not, fake it.
- No asserting on log output as a substitute for asserting on behaviour.
