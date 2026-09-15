---
title: "CLI: add `--format json` to `freightline quote`"
labels: ["good first issue", "cli"]
---

## Problem

`freightline quote` prints a human-readable table. Our warehouse integration
shells out to it and parses stdout with `awk`, which breaks every time we change
a column width. It has broken twice this quarter.

## What to do

Add `--format {table,json}` to the `quote` subcommand, defaulting to `table` so
nothing changes for humans.

With `--format json`, print a single JSON object to stdout and nothing else:

```json
{
  "carrier_code": "atlas",
  "service": "ground",
  "zone": 7,
  "billable_weight_kg": "2.50",
  "currency": "USD",
  "lines": [
    {"code": "base", "label": "Ground linehaul", "amount": "20.00", "kind": "base"},
    {"code": "fuel", "label": "Fuel surcharge", "amount": "3.10", "kind": "surcharge"}
  ],
  "total": "23.10"
}
```

## Acceptance criteria

- `freightline quote --format json ...` emits exactly one JSON object and exits 0.
- Every monetary value and the billable weight are JSON **strings**, not numbers.
  These are `Decimal` values and must not go through a float.
- `--format table` output is byte-for-byte unchanged from today.
- An invalid `--format` value is rejected by argparse with exit code 2.
- A domain error still prints to **stderr** in the existing `error [code]: ...`
  form and exits 3 — the JSON flag must not swallow errors onto stdout.

## Scope

- `src/freightline/cli.py`
- `tests/test_cli.py`

Out of scope: adding `--format` to `ship`, `track`, or `report`. If it turns out
to be trivially shared, say so in the PR and we will open a follow-up.

## Done

`make check` green, plus:

```bash
.venv/bin/freightline quote --carrier atlas --service ground \
  --from 94105 --to 10001 --weight 2.5 --format json | python -m json.tool
```
