---
name: 10-app-monday-plan
description: "APP — laptop already shut: what to do in your own repo on Monday"
agent: agent
---

I am taking one thing from this session back to my own repository on Monday.

Look at what this repository actually has — `.github/copilot-instructions.md`,
the four scoped files in `.github/instructions/`, the three skills in
`.github/skills/`, the three custom agents in `.github/agents/`, the numbered
prompts, the CI workflow — and work out which of them earn their keep first.

Give me:

1. **One hour.** The single highest-leverage thing, with the actual file content
   to paste. Be specific about what makes a rule worth writing down: it has to be
   something a reviewer says more than once, and something that is checkable.
2. **One week.** The next three, in order, and what has to be true before each
   one is worth doing.
3. **What not to do.** Which of these would be premature or actively harmful in a
   repository that does not already have the thing they depend on. Be blunt —
   a custom agent over a codebase with no tests is theatre.
4. **How I would know it is working.** A concrete signal for each, not a vibe.
   "Nobody has commented 'use Decimal' on a PR in a month" is a signal.

Then draft the `.github/copilot-instructions.md` I should start with — but write
it as a template with the five questions I have to answer about my own codebase
to fill it in, because you do not know my conventions yet.
