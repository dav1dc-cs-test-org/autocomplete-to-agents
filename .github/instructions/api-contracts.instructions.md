---
applyTo: "src/freightline/api/**"
description: HTTP API contract rules
---

# API contract

The schemas in `api/schemas.py` are a published contract. Clients depend on
field names, types, enum members, and required-ness.

## Breaking vs additive

| Change | Verdict |
| --- | --- |
| Add an optional response field | additive |
| Add an optional request field with a default | additive |
| Add a new enum member to a **response** enum | breaking for strict clients — call it out |
| Rename or remove a field | breaking |
| Make an optional request field required | breaking |
| Narrow a type or tighten a validator | breaking |
| Change an HTTP status code or error `code` | breaking |

If a change is breaking, say so in the PR description and propose a versioned
path (`/v2/...`) or a deprecation window. Do not quietly change the shape.

## Rules

- Request models set `model_config = ConfigDict(extra="forbid")`. Unknown fields
  are a 422, not a silent no-op.
- Every route declares `response_model` and a `summary`. Those become the
  OpenAPI document, which is the contract other teams read.
- Pagination parameters are bounded in the signature (`ge=`, `le=`), not checked
  in the body. The repository caps again server-side; both layers stay.
- Route handlers do not contain business rules. They map payload → domain call →
  payload, through `api/mapping.py`.
- Domain errors propagate. `FreightlineError` already carries `http_status` and
  `code`, and `app.py` has the single handler that translates them. Do not
  wrap domain calls in `try/except HTTPException`.
- Anything under `/v1/admin` depends on `require_admin`, which fails closed when
  no token is configured.

## Webhooks

Verify the HMAC over the **raw request body** before parsing it. Never parse
first and verify a re-serialised payload — that is a different byte string.
