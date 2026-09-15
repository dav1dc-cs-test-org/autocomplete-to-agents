## What and why

<!-- The behaviour change, in the language of the person who asked for it. -->

## The ripple

<!--
Changes here are rarely one file. Tick what applies, delete the rest.

- [ ] Carrier — `tests/test_carrier_contract.py` passes for the new code
- [ ] Surcharge — followed `.github/skills/add-surcharge/SKILL.md`
- [ ] API schema — classified below as additive or breaking
- [ ] Migration — new forward-only file, no shipped migration edited
- [ ] CHANGELOG.md updated under `## Unreleased`
-->

## API contract

- [ ] No change to `api/schemas.py` or any route signature
- [ ] Additive
- [ ] **Breaking** — migration note and deprecation window below

## Checks

- [ ] `make check` green
- [ ] Manual command that proves the behaviour, pasted with its output
- [ ] Regression test that fails without this change (bug fixes only)

## Anything a reviewer should look at twice

<!-- Where you were unsure. This is the most useful section in the template. -->
