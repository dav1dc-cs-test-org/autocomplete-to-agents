---
name: add-surcharge
description: Add a new surcharge to the Freightline rating engine. Use when asked to add, change, or remove a surcharge, accessorial, fee, or accessorial charge on a quote — for example residential, remote area, dangerous goods, signature required, or a fuel-style percentage charge.
argument-hint: [surcharge name] [flat amount or percentage] [when it applies]
---

# Add a surcharge

A surcharge is never one file. This is the whole checklist, in order. Do not
stop early, and do not report success until `make check` passes.

## 0. Decide flat or percentage

| | Flat | Percentage |
| --- | --- | --- |
| Base class | subclass `FlatSurcharge` | standalone frozen dataclass |
| Amount | fixed `value` string | `subtotal.times(rate)` |
| Position in `SURCHARGES` | **before** `FuelSurcharge()` | after every flat one |

Ordering matters: `build_lines` hands each surcharge the running subtotal, so a
flat surcharge placed after `FuelSurcharge()` silently escapes fuel. If the
request is ambiguous, assume flat and say so.

## 1. Define it — `src/freightline/rating/surcharges.py`

```python
@dataclass(frozen=True)
class SignatureRequiredSurcharge(FlatSurcharge):
    code: str = "signature_required"
    label: str = "Signature required"
    value: str = "6.50"

    def applies_to(self, request: QuoteRequest) -> bool:
        return request.signature_required
```

- `code` is `snake_case` and permanent — it appears in `Quote.breakdown()`, in
  the `quote_audit` table, and in the API response. Treat it as a contract.
- `label` is what a customer reads on an invoice. Sentence case.
- `value` is a **string**, so it becomes an exact `Decimal`. Never a float.
- Thresholds go in a module-level constant next to `HEAVY_WEIGHT_KG`, not inline.

## 2. Register it — same file

Insert into the `SURCHARGES` tuple at the position decided in step 0.

## 3. Carry any new input through

If `applies_to` needs a field that `QuoteRequest` does not have yet:

1. Add it to `QuoteRequest` in `models.py` **with a default**, so existing
   callers keep working.
2. Add it to `QuoteIn` in `api/schemas.py` with the same default. An optional
   request field with a default is an additive API change; a required one is
   breaking — see `.github/instructions/api-contracts.instructions.md`.
3. Map it in `api/mapping.py::to_quote_request`.
4. Add the CLI flag in `cli.py::_add_quote_arguments` and wire it in
   `_build_request`.

## 4. Test it — `tests/test_surcharges.py`

At minimum:

- it appears in `codes(...)` when it should apply;
- it is absent from the baseline `quote_request`;
- fuel compounds on it (compute the expected subtotal explicitly);
- the surcharge-code uniqueness test still passes.

Name tests as sentences. Use `dataclasses.replace` on the `quote_request`
fixture rather than building a new request.

## 5. Document it

- Add a row to the surcharge table in `docs/ARCHITECTURE.md` if one exists for
  this area, and mention it in the rating pipeline section if the ordering rule
  is affected.
- Add a bullet under `## Unreleased` in `CHANGELOG.md`.

## 6. Verify

```bash
make check
```

Then show the before/after on a real quote so the effect is visible:

```bash
.venv/bin/freightline quote --carrier atlas --service ground \
  --from 94105 --to 10001 --weight 2.5
```

## Report back

State, in this order: the `code` you chose, where you placed it in `SURCHARGES`
and why, every file you touched, and the `make check` result. If you changed
`QuoteRequest` or `QuoteIn`, say explicitly whether the change is additive or
breaking.
