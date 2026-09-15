---
name: 00-ide-preflight
description: "IDE — needs the terminal and make check: verify the repo is demo-ready"
agent: agent
---

Check that this repository is ready to be demoed, and fix anything that is not.

1. Confirm the virtualenv exists and the package is installed in editable mode
   with the `dev` and `api` extras. If not, run `make setup`.
2. Run `make check` and report the result: ruff, mypy, and the pytest count.
3. Confirm the demo seams are in their starting state:
   - `src/freightline/carriers/` contains exactly `atlas`, `borealis`, and
     `pigeon` — no `cascade`.
   - `src/freightline/storage/saved_searches.py` does **not** exist.
   - `git status` is clean.
4. Rebuild the demo database with `make seed` and show the status breakdown.
5. List what is registered for Copilot in this repo: the instruction files, the
   agent skills, the custom agents, and the numbered prompts. Say where each one
   lives.

Report a single verdict line at the end: `READY` or `NOT READY`, followed by the
exact commands to fix anything that is not ready.
