# From Autocomplete to Agents

A working Python codebase and ten saved prompts for a 50-minute GitHub Copilot
demo. Every prompt runs on any surface — VS Code, github.com, the Copilot app, or
the CLI.

**Start here: [docs/DEMO-RUNBOOK.md](docs/DEMO-RUNBOOK.md).**

```bash
make setup                             # venv + editable install
make check                             # ruff + mypy + 172 tests
make seed                              # var/freightline.db with 60 shipments
python scripts/demo_prompt.py --list   # the ten prompts
```

## Why a real codebase

Demos that start with an empty folder prove that Copilot can write a to-do app.
Nobody's job is writing to-do apps.

**Freightline** is a parcel rating, booking, and tracking service: ~2,500 lines
across a rating engine, three carrier integrations, a SQLite repository, a
FastAPI surface, and a CLI. It has a carrier that predates its own base class, an
approximation documented in an ADR, and a contract test suite that turns "add a
carrier" into an executable checklist.

In other words, it has the things your codebase has. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## The ten prompts

Saved in [.github/prompts/](.github/prompts/), named `NN-<surface>-<topic>` so the
filename tells you where to run it. In VS Code, type `/` in chat. On any other
surface:

```bash
python scripts/demo_prompt.py --list             # name, surface, and why
python scripts/demo_prompt.py 05                 # print it
copilot -p "$(python scripts/demo_prompt.py 05)" # or run it
```

| # | Prompt | Surface | Why that surface |
| --- | --- | --- | --- |
| 00 | `00-ide-preflight` | IDE | Needs the terminal and `make check` |
| 01 | `01-app-orient` | App | No clone, no venv — the IDE cannot do this |
| 02 | `02-ide-add-carrier` | IDE | Per-edit approval while it self-corrects |
| 03 | `03-app-delegate` | App | Delegation means you are not at the keyboard |
| 04 | `04-ide-review-pr` | Web → IDE | Web reviews unasked; IDE opens both files at once |
| 05 | `05-cli-triage` | CLI | Failure, diff, fix, test, stage — one scrollback |
| 06 | `06-ide-instructions` | IDE | The rule and the diff it produced, side by side |
| 07 | `07-cli-skill-surcharge` | CLI | Same `SKILL.md`, no editor — the portability proof |
| 08 | `08-ide-security-audit` | IDE | Agent picker, tool restriction, handoff button |
| 09 | `09-ide-sdk-automation` | IDE + terminal | Read the integration; run it where it will live |
| 10 | `10-app-monday-plan` | App | Close the session with the editor already shut |

The surface is part of the content. [docs/DEMO-RUNBOOK.md](docs/DEMO-RUNBOOK.md)
carries the full argument for each one.

## What is configured for Copilot

| Thing | Where | Loads |
| --- | --- | --- |
| Repo instructions | [.github/copilot-instructions.md](.github/copilot-instructions.md) | Always |
| Scoped instructions | [.github/instructions/](.github/instructions/) | By `applyTo:` path |
| Skills | [.github/skills/](.github/skills/) | When the task matches |
| Custom agents | [.github/agents/](.github/agents/) | When you pick one |
| Prompts | [.github/prompts/](.github/prompts/) | When you invoke one |

Skills and agents are portable: the same files work in VS Code, Copilot CLI, and
the coding agent.

## Demo machinery

| Script | Does |
| --- | --- |
| `scripts/demo_prompt.py` | Print a prompt, or `--list` for the surface cheat-sheet |
| `scripts/demo_review_branch.sh` | Build `demo/saved-searches` — a green-CI PR with real defects |
| `scripts/demo_break.py` | Introduce one known bug so the CLI has something to triage |
| `scripts/demo_reset.sh` | Put everything back (dry run by default) |
| `scripts/seed_data.py` | Deterministic demo data |

[demo/issues/](demo/issues/) holds three tickets sized for the coding agent.
[demo/pr/](demo/pr/) holds the deliberately defective branch content — it is
never merged, and its README is the presenter crib sheet.

## Try Freightline itself

```bash
.venv/bin/freightline carriers
.venv/bin/freightline quote --carrier atlas --service ground \
  --from 94105 --to 10001 --weight 2.5 --residential
make serve        # http://localhost:8000/docs
```

`freightline quote` alone accepts `--format {table,json}`; the default `table`
format is the human-readable breakdown above. JSON format writes one object with
the exact top-level keys `carrier_code`, `service`, `zone`,
`billable_weight_kg`, `currency`, `lines`, and `total`. Monetary amounts and
billable weight are strings with two decimal places. Each `lines` entry contains
exactly `code`, `label`, `amount`, and `kind`.

## Licence

MIT. Take the instruction files, take the skills, take the prompts.
