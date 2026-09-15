---
name: onboard-carrier
description: Add a new carrier integration to Freightline end to end. Use when asked to add, onboard, integrate, or register a carrier, shipping provider, or delivery partner, or when the carrier contract tests in tests/test_carrier_contract.py are failing.
argument-hint: [carrier name] [services] [tracking number format]
---

# Onboard a carrier

`tests/test_carrier_contract.py` is the specification. It is parameterised over
the registry, so the moment you register an adapter it produces a checklist of
everything still missing. Run it early and let the failures drive the work.

```bash
.venv/bin/python -m pytest tests/test_carrier_contract.py -q
```

## 1. Adapter — `src/freightline/carriers/<code>.py`

Subclass `BaseCarrier`. Set `profile` and `STATUS_MAP`; inherit everything else.

```python
class CascadeCarrier(BaseCarrier):
    profile = CarrierProfile(
        code="cascade",
        name="Cascade Logistics",
        services=(ServiceLevel.GROUND, ServiceLevel.EXPRESS),
        tracking_pattern=r"CSC\d{10}",
        tracking_template="CSC##########",
        supports_saturday_delivery=False,
        supports_international=False,
    )
    STATUS_MAP = {...}
```

`tracking_pattern` and `tracking_template` are two views of one format and must
agree: `#` expands to a digit, `@` to an uppercase letter, everything else is
literal. The contract test generates a number and feeds it back through
`normalize_tracking_number`.

## 2. Register — `carriers/registry.py`

One entry in `_REGISTRY`, keyed by `profile.code`.

## 3. Rate card — `rating/tables.py`

An entry under `RATE_CARDS[code]` covering **every** service in
`profile.services` and **every** zone 1–8. Use `_linear_multipliers(start, step)`
unless the carrier publishes a genuinely irregular matrix. All amounts are
string literals so they parse as exact `Decimal`s.

A service advertised in `profile.services` but missing from the rate card fails
`test_rate_card_covers_exactly_the_advertised_services`, and so does the reverse.

## 4. Status vocabulary

`STATUS_MAP` must reach **all six** canonical `ShipmentStatus` values:
`created`, `in_transit`, `out_for_delivery`, `delivered`, `exception`,
`returned`. Most carriers have several codes per canonical status — map them
all; the normalizer has no fallback by design.

## 5. Document — `docs/ARCHITECTURE.md`

Add a row to the carrier panel table. The contract test asserts that
`` `code` `` and the display name both appear in that file.

## 6. Carrier-specific tests — `tests/test_carriers.py`

The contract tests cover the rules that apply to everyone. Add tests here only
for what is genuinely unique to this carrier: an unusual tracking format, a
status code that maps somewhere non-obvious, a service it refuses.

## 7. Verify

```bash
make check
.venv/bin/freightline carriers
.venv/bin/freightline quote --carrier <code> --service <service> \
  --from 94105 --to 10001 --weight 2.5
```

## Report back

List every file you touched, the six contract areas and how each is satisfied,
and the `make check` result. If the carrier needed anything the contract does not
currently express, say so — that is a gap in the contract, not a reason to skip.
