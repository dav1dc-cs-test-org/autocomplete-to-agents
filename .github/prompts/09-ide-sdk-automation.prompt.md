---
name: 09-ide-sdk-automation
description: "IDE — read and extend: the agent as a library inside your own tooling"
agent: agent
---

Look at [tools/copilot_sdk/rate_card_auditor.py](../../tools/copilot_sdk/rate_card_auditor.py).

It runs the same agent that powers Copilot CLI, but inside our own script, with
a custom tool that hands the model our real rate cards instead of letting it
guess.

First, explain it to me as an integration, not as code:

1. What is the boundary? Where do *we* decide things, and where does the agent?
2. `get_rate_card` is registered as a tool. Why is that better than pasting the
   rate card into the prompt?
3. The permission handler denies shell commands. Walk me through what would
   happen if the model tried to run one anyway.
4. This is billed per prompt and runs in CI. What would you change before letting
   it run on every pull request?

Then extend it: add a second custom tool `list_carriers` that returns the
registered carrier codes and their advertised services, so the auditor can find a
carrier that has **no** rate card at all rather than only checking the ones that
do. Keep the existing output format.

Run it and show me the report.
