---
title: "API: add `GET /v1/carriers/{carrier_code}`"
labels: ["api"]
---

## Problem

`GET /v1/carriers` returns the whole panel. The booking UI needs one carrier and
currently fetches all of them and filters client-side, which means a new carrier
silently appears in a dropdown before its rate card is live.

## What to do

Add `GET /v1/carriers/{carrier_code}` returning a single `CarrierOut`, plus the
information the UI actually needs that the list endpoint does not carry:

- `services` — already on `CarrierOut`;
- `tracking_pattern` — so the UI can validate a tracking number client-side;
- `has_published_rates` — boolean, true when `rating.tables.services_for(code)`
  is non-empty and matches `profile.services`.

Unknown carrier codes must return **404** with the existing
`unknown_carrier` error body. `get_carrier` already raises
`UnknownCarrierError` with the right `http_status`, and `app.py` already has the
handler — do not add a `try/except` in the route.

## Scope

- `src/freightline/api/routes_quotes.py`
- `src/freightline/api/schemas.py`
- `src/freightline/api/mapping.py`
- `tests/test_api.py`

Out of scope: changing the shape of `GET /v1/carriers`. Adding the two new fields
to the list response would be additive, but it is a separate decision.

## Acceptance criteria

- `GET /v1/carriers/atlas` returns 200 with `code == "atlas"` and
  `has_published_rates == true`.
- `GET /v1/carriers/ATLAS` returns the same thing — lookup is case-insensitive
  today and must stay that way.
- `GET /v1/carriers/teleport` returns 404 with `{"code": "unknown_carrier", ...}`
  and `details.known` listing the real codes.
- The route appears in `/openapi.json` with a `summary` and a `response_model`.
- Read `.github/instructions/api-contracts.instructions.md` and state in the PR
  whether this change is additive or breaking.

## Done

`make check` green.
