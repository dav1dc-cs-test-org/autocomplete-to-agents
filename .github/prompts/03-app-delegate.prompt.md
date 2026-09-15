---
name: 03-app-delegate
description: "APP — away from the keyboard: turn drafts into tickets an agent can finish"
agent: agent
---

I am about to hand three small tickets to the Copilot coding agent while I work
on something harder. Write the issues so that an agent can finish them without
asking me anything.

The three tickets are drafted in [demo/issues/](../../demo/issues/). For each
one, rewrite it into a form that is genuinely delegable:

- **Scope** — exactly which files are in bounds and which are out.
- **Acceptance criteria** — as assertions, not adjectives. "`freightline quote
  --format json` emits a single JSON object with keys `carrier_code`, `service`,
  `zone`, `lines`, `total`, `currency`" beats "output should be machine
  readable".
- **The checklist it will miss** — the ripple. Name the other files that have to
  change, or point at the contract test or the skill that enumerates them.
- **Definition of done** — `make check` green, plus whatever manual command
  proves the behaviour.
- **Out of scope** — the tempting adjacent refactor it should not do.

Then rank the three by how safe they are to delegate, and say what makes a ticket
*undelegable* in this codebase. Use the issues in `demo/issues/` as evidence.

Finally, give me each rewritten ticket as a finished issue body I can paste
straight into a new issue and assign, and tell me which one to assign **first**
and why. If I would rather create them from a terminal, add the matching
`gh issue create` command at the end — but the issue bodies are the output that
matters.
