---
title: "Rating: add a declared-value insurance surcharge"
labels: ["rating"]
---

## Problem

`QuoteRequest.declared_value` exists and is never read. Customers who declare a
value are not charged for the cover, and finance found the gap during the
quarterly reconciliation.

## What to do

Add an insurance surcharge:

- code `insurance`, label `Declared value insurance`;
- **1.2%** of the declared value;
- minimum charge `3.50` whenever it applies;
- applies only when `declared_value` is set and greater than zero;
- it is a flat charge for ordering purposes: it goes **before** `FuelSurcharge()`
  in `SURCHARGES`, so fuel compounds on it.

The percentage is of the *declared value*, not of the running subtotal — unlike
fuel. That distinction is the whole point of this ticket; make it obvious in the
code.

## Scope

Follow the `add-surcharge` skill in `.github/skills/add-surcharge/SKILL.md`. It
lists every file that has to change, including `api/schemas.py`,
`api/mapping.py`, `cli.py`, and the changelog.

Out of scope: per-carrier insurance rates. One rate for the whole panel for now.

## Acceptance criteria

- A quote with no declared value has no `insurance` line.
- A quote with a declared value of `1000.00` has an `insurance` line of `12.00`.
- A quote with a declared value of `100.00` has an `insurance` line of `3.50`
  (the minimum), not `1.20`.
- The `insurance` line appears before `fuel`, and `fuel` is computed on a
  subtotal that includes it.
- No float appears anywhere in the calculation.

## Done

`make check` green, and the `add-surcharge` checklist reported item by item in
the PR description.
