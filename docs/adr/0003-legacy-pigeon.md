# ADR-0003: Pigeon Post stays on its own pattern, for now

- **Status**: accepted, revisit 2027-Q1
- **Date**: 2026-06-02

## Context

`carriers/pigeon.py` was written in 2016 against the PigeonPost v1 SOAP gateway.
It predates `BaseCarrier`, `CarrierProfile`, the `FreightlineError` hierarchy, and
type annotations. It is the only module with a mypy override in
`pyproject.toml`.

It is also correct, covered by tests, and handles two live tracking formats and a
gateway that pads its status codes inconsistently depending on which datacentre
answers.

When we introduced `BaseCarrier` during the Borealis onboarding, migrating Pigeon
at the same time was scoped at three days and would have put the Borealis launch
at risk.

## Decision

Leave it. Constrain it:

- It satisfies the `CarrierAdapter` protocol structurally, so the registry and
  the contract tests treat it like everything else.
- The mypy override is scoped to that single module, not to the package.
- Its quirks are documented in the module docstring rather than in tribal memory.

## Known divergence

| | Pigeon | Everything else |
| --- | --- | --- |
| Base class | none | `BaseCarrier` |
| Errors | `ValueError` | `ValidationError` |
| Status codes | numeric strings, whitespace padded | uppercase words |
| Tracking formats | two live (`PP` + 9, `PGN` + 10) | one |
| Type annotations | none | full |

The `ValueError` divergence is the one that bites: `ValidationError` is **not** a
`ValueError` subclass, so any caller that catches `ValueError` around a Pigeon
call breaks silently the day we migrate. `tests/test_carriers.py` currently
catches `ValueError` for exactly this reason.

## Migration plan

The `legacy-migrator` custom agent in `.github/agents/` encodes the sequence:
characterise the current behaviour first, migrate in reviewable steps, change the
exception type and every caller in the same step, and only then remove the mypy
override.

Trigger: PigeonPost have announced the v1 gateway retires in 2027-Q2. The v2
integration is a rewrite, and this module should be on current patterns before
that work starts, not during it.
