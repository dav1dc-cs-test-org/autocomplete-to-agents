Ops re-type the same shipment filters every week for the exception review, so
this stores a filter once and lets them re-run it.

## What this adds

- `POST /v1/saved-searches` — store a named filter
- `GET /v1/saved-searches` — list them
- `GET /v1/saved-searches/{id}/run` — run one and return matching shipments
- `DELETE /v1/saved-searches/{id}` — remove one
- Migration `0004_saved_searches.sql`
- Tests covering create, get, list, run, and delete

## Notes

`filter_expression` is stored as written so ops can express conditions the
existing `GET /v1/shipments` filters do not cover — date ranges, `OR`, `IS NULL`.
The dashboard is the only client today.

## Checks

- [x] `make check` green
- [x] Migration applies cleanly on a seeded database
- [ ] Reviewed by someone who knows the storage layer
