# Issues staged for the coding agent

Three tickets sized for delegation. Demo step 03 (`03-app-delegate`, run in the
Copilot app) rewrites them into their final form so they can be created and
assigned without a terminal.

| File | Ticket | Why it is delegable |
| --- | --- | --- |
| [01-cli-json-output.md](01-cli-json-output.md) | `--format json` on `freightline quote` | One file, a precisely specified output shape, an existing test module to extend |
| [02-insurance-surcharge.md](02-insurance-surcharge.md) | Declared-value insurance surcharge | Ripples across seven files — but a skill enumerates all seven |
| [03-carrier-detail-endpoint.md](03-carrier-detail-endpoint.md) | `GET /v1/carriers/{code}` | Mirrors an endpoint that already exists; the error path is already built |

## Creating them

```bash
GH_PAGER=cat gh issue create \
  --title "CLI: add --format json to freightline quote" \
  --body-file demo/issues/01-cli-json-output.md \
  --label "good first issue"
```

Then assign to Copilot from the issue page, or:

```bash
GH_PAGER=cat gh issue develop <number> --name "copilot/cli-json-output"
```

## What makes these delegable

Each one names the files in scope, states acceptance criteria as assertions
rather than adjectives, points at the contract test or skill that enumerates the
ripple, and says what is explicitly **out** of scope. The out-of-scope line is
the one people forget, and it is the one that stops a two-file ticket coming back
as a twenty-file refactor.
