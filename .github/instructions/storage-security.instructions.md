---
applyTo: "src/freightline/storage/**,src/freightline/tracking/**"
description: SQL and untrusted-input rules
---

# Storage and untrusted input

## SQL

`ShipmentRepository` is the only module that writes SQL.

- Every **value** is a bound parameter (`?`). No exceptions, no "it's only an
  internal ID", no f-strings holding user data.
- The only things interpolated into a statement are **identifiers** taken from
  `SORTABLE_COLUMNS` and `SORT_DIRECTIONS`. Validate against the allow-list and
  raise `ValidationError` on a miss; never sanitise-and-continue.
- `limit` is capped server-side at `MAX_PAGE_SIZE` even when the HTTP layer has
  already bounded it. Two layers, on purpose.
- Schema changes are new forward-only files in `storage/migrations/`, numbered in
  sequence. Never edit a migration that has shipped.

## Inbound webhooks

- Verify the HMAC over the raw body, with `hmac.compare_digest`. A `==`
  comparison on a signature is a timing oracle and will be rejected.
- Fail closed: no configured secret means reject, never "skip verification".
- Reject deliveries outside the replay tolerance window.
- Secrets come from `Settings`. A credential literal in source is a blocker, and
  that includes "temporary" defaults like `secret or "changeme"`.

## Exports

Anything customer-supplied that lands in a CSV goes through
`reporting.exporters.escape_cell`. Finance opens these in Excel; a `reference`
beginning `=` is a formula, not a string.

## Error swallowing

`except Exception: pass` is never acceptable. Catch the narrowest type you can
name and either handle it or wrap and re-raise as a `FreightlineError`. If a
failure genuinely is ignorable, log it and say why in a comment.
