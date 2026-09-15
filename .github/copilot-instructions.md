# Freightline

Freightline rates, books, and tracks parcel shipments across a carrier panel.
One FastAPI process, one SQLite database, one CLI. Read
[docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) before changing anything that
crosses a package boundary.

## Setup

```bash
make setup     # venv + editable install with dev and api extras
make check     # ruff + mypy + pytest, exactly what CI runs
make seed      # rebuild var/freightline.db with demo data
```

Always run `make check` before claiming work is done. If you cannot run it, say
so explicitly rather than assuming it passes.

## Architectural rules

These are not preferences. Breaking one is a bug.

- **The domain never imports the API.** `freightline.api` may import anything;
  nothing outside it may import `freightline.api`. The CLI must stay installable
  without FastAPI.
- **`service.py` is the only composition point.** Route handlers and CLI
  commands contain transport concerns and nothing else. Business rules that
  appear in both belong in the service layer.
- **Money is `freightline.money.Money`**, which is integer cents. Never `float`.
  Use `Decimal` for intermediate arithmetic and convert once, at the end, with
  `Money.from_decimal`. A `float` anywhere near a price is a review blocker.
- **Rating is table-driven.** Prices live in `rating/tables.py`. Carrier adapters
  describe identity and vocabulary, not cost.
- **`ShipmentRepository` is the only module that writes SQL.** Every value is a
  bound parameter. The only things ever interpolated into a statement are
  identifiers drawn from `SORTABLE_COLUMNS` / `SORT_DIRECTIONS`.

## Error handling

- Raise a subclass of `freightline.errors.FreightlineError`. Never raise bare
  `Exception`, `ValueError`, or `RuntimeError` from library code.
- Every error subclass carries a stable `code` and an `http_status`. Callers
  branch on `code`, never on message text.
- Put actionable context in `details`: the invalid value *and* the valid
  options. `details={"carrier_code": code, "known": all_carrier_codes()}`, not
  `details={"error": "bad"}`.
- Never write `except Exception: pass`. Catch the narrowest type you can name,
  and either handle it or re-raise it wrapped.

## Python style

- Python 3.11+. `from __future__ import annotations` at the top of every module.
- Full type annotations on every public function. `make check` runs mypy in
  strict-ish mode and it must stay clean.
- Line length 100. Ruff is the formatter and linter of record.
- Prefer frozen dataclasses for domain types. Pydantic models exist only in
  `freightline/api/schemas.py`.
- Datetimes are timezone-aware UTC everywhere. Parse with
  `util.dates.parse_iso8601`, render with `util.dates.to_iso8601`.

## Comments and docstrings

- Write a comment only for what the code cannot say itself: a constraint, a
  workaround, a reason. Do not narrate the next line.
- Module docstrings explain *why the module exists* and any rule that holds
  across it. Function docstrings are one line unless there is a real subtlety.
- Never add a comment that describes the change you just made, or addresses a
  reviewer. The diff is not the audience; the next reader is.

## Tests

- pytest, in `tests/`, one module per source module.
- Test names are sentences about behaviour: `test_fuel_compounds_on_the_flat_surcharges`,
  not `test_fuel_2`.
- Assert on behaviour and invariants. Prefer `total == sum(lines)` over a
  hardcoded number, and when you do hardcode a number, say in a comment where it
  came from.
- Every bug fix gets a regression test that fails before the fix.
- Contract rules that apply to all carriers go in `tests/test_carrier_contract.py`,
  parameterised over the registry — never copy-pasted per carrier.

## Changes that ripple

Adding a carrier or a surcharge touches several files. Do not stop at the first
one. `tests/test_carrier_contract.py` is the checklist for carriers; the
`add-surcharge` skill in `.github/skills/` is the checklist for surcharges.

Record anything notable in [CHANGELOG.md](../CHANGELOG.md) under `## Unreleased`.
