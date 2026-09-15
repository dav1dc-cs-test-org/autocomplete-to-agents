# Demo runbook — Copilot 101: From Autocomplete to Agents

**50 minutes, ten prompts, four surfaces.** Every prompt is saved in
[.github/prompts/](../.github/prompts/) and named `NN-<surface>-<topic>`, so the
filename tells you where to run it.

```bash
python scripts/demo_prompt.py --list      # name, surface, and the argument it makes
python scripts/demo_prompt.py 05          # print one, ready to paste anywhere
copilot -p "$(python scripts/demo_prompt.py 05)"
```

The surface is part of the content. A prompt that produces the same experience
everywhere teaches nothing about surfaces — so each step below is placed where
the *location* is doing work, and says what that work is.

---

## Before you present

```bash
make setup
make seed
make check                                # 172 tests, ruff clean, mypy clean
scripts/demo_review_branch.sh --push      # builds demo/saved-searches and opens the PR
```

Then run `/00-ide-preflight` in chat and confirm it says `READY`.

Open in this order, so you never alt-tab into a login screen:

1. **The Copilot app**, on this repository — steps 01, 03, 10
2. **VS Code** on this repo, Chat panel open — steps 02, 04, 06, 08, 09
3. **A terminal** in the repo root with `copilot` already authenticated — 05, 07
4. The `demo/saved-searches` pull request on github.com — step 04

**Enable Copilot code review** on the repository before you start
(Settings → Copilot → Code review), or the step 04 beat has nothing to show.

### The one thing to do out of order

Kick off **step 03** (assign the issues to the coding agent) at the *start* of
step 02. The agent needs a few minutes. By the time you finish Agent Mode, there
is a pull request waiting — which is exactly the point you are making.

---

## The run

| # | Prompt | Surface | Min | Why *this* surface |
| --- | --- | --- | --- | --- |
| 01 | `01-app-orient` | App | 4 | No clone, no venv — the IDE structurally cannot do this |
| 02 | `02-ide-add-carrier` | IDE | 8 | Per-edit approval; watch it fail a test and self-correct |
| 03 | `03-app-delegate` | App | 3 | Delegation means you are *not* at the keyboard |
| 04 | `04-ide-review-pr` | Web → IDE | 5 | Web: it reviews unasked. IDE: two files open side by side |
| 05 | `05-cli-triage` | CLI | 6 | Failure, diff, fix, test, stage — one scrollback, no context switch |
| 06 | `06-ide-instructions` | IDE | 5 | The rule and the diff it produced, visible at once |
| 07 | `07-cli-skill-surcharge` | CLI | 6 | Same `SKILL.md`, no editor. This is the portability proof |
| 08 | `08-ide-security-audit` | IDE | 5 | Agent picker, tool restriction, and the handoff button |
| 09 | `09-ide-sdk-automation` | IDE + terminal | 5 | Read the integration; run it where it will live |
| 10 | `10-app-monday-plan` | App | 3 | Close the session with the editor already shut |

---

### 01 — The landscape (4 min) · **App**

> **Surface argument:** you have not cloned this repository. You may not even have
> decided whether to take the ticket. This is genuine first contact, and it is the
> one thing an IDE structurally cannot do.

Open the Copilot app on this repo and run `01-app-orient`.

Say out loud: this is a codebase none of us wrote, and the first question is not
"write me code", it is "what am I looking at". Let it draw the Mermaid diagram.

The beat to land: it finds `carriers/pigeon.py` on question 5 without being told
it is legacy. Nobody labelled it. It read the code.

Then — and only then — switch to VS Code and ask the same question. Point out
what changed: now it can open files, run the tests, and check its own answer.
Same question, more tools.

> *"Understanding doesn't need a working copy. Changing does."*

> If someone asks why not just use completions: completions answer "what comes
> next on this line". This answers "what is this system". Different tool.

---

### 02 — Agent Mode (8 min) · **IDE**

> **Surface argument:** you approve every edit, one at a time, in a diff view.
> This is the answer to the "so it just changes my code?" objection that someone
> in the room is already forming.

**First, go start step 03.** Then come back.

Run `/02-ide-add-carrier`.

Watch for, and narrate:

1. It reads `test_carrier_contract.py` and treats it as the specification.
2. It creates the adapter, then **runs the tests and fails** — probably on the
   rate card or the architecture doc.
3. It fixes its own failure and re-runs.

Land it: *you gave it a goal and a rate sheet. It worked out that the change
touches the adapter, the registry, the rate card, the tests and a Markdown table
in a doc — because the repository made all of that checkable.*

Then show the diff. `git diff --stat`. Count the files out loud, and point out
that you approved every edit.

---

### 03 — Coding agent (3 min, started earlier) · **App**

> **Surface argument:** the whole claim is that this happens while you are doing
> something else. Assigning it from a browser tab next to your IDE quietly
> undermines that. Do it from the app, then put the device down.

At the start of step 02, open `03-app-delegate` in the app. It rewrites the three
drafts in [demo/issues/](../demo/issues/) into tickets an agent can actually
finish — scope, acceptance criteria as assertions, the ripple, and the
out-of-scope line people forget. Create the issues, assign them to Copilot, and
go back to VS Code.

When you return here, open the pull request **in the app**. Show the session log
— the agent's plan, the commands it ran, the tests it ran. Not a black box.

The honest framing: *this is for the tickets you keep not getting to. It is not
for the thing you have been thinking about in the shower for a week.*

> If the PR is not ready, skip to 04 and come back at 09. Nothing downstream
> depends on it.

---

### 04 — Code review (5 min) · **Web, then IDE**

> **Surface argument:** two different things are being shown. On the web the
> review happens **without you asking**. In the IDE you can open the offending
> file next to the file it should have copied — and three of the findings are
> only findings *because* of that comparison.

**Web first.** Open the `demo/saved-searches` pull request.

1. Show CI. Green. Ruff, mypy, 179 tests, all passing. The PR ships its own tests.
2. Show the Copilot review comments on the diff. Nobody requested them. It should
   flag the interpolated `filter_expression` and the missing auth dependency.

**Then the IDE.** Run `/04-ide-review-pr`. It opens `storage/repository.py` and
`api/routes_admin.py` alongside the new code and sorts every finding into *wrong
in the abstract* versus *inconsistent with the file two directories away*.

Land the question the prompt asks: *which of these could a linter have caught?*
Answer: almost none of them, because the linter was suppressed with `# noqa` in
the same commit that introduced the problem.

Crib sheet for what is actually wrong: [demo/pr/README.md](../demo/pr/README.md).
Do not read it out — let the tooling find it.

---

### 05 — Copilot CLI (6 min) · **CLI**

> **Surface argument:** the failing output is already in your scrollback. So is
> the diff, the fix, the re-run, and `git add`. Zero context switches. Run this
> one in the IDE and you have argued yourself out of a surface.

```bash
python scripts/demo_break.py surcharge-order
copilot
```

Then paste `05-cli-triage` (or `copilot -p "$(python scripts/demo_prompt.py 05)"`).

It runs pytest, reads the failures, works out that fuel stopped compounding,
finds the hunk with `git diff`, fixes it, adds a regression test, and stages the
commit.

The point: *no context switch.* The tests, the diff, the fix, and the commit all
happened where you already were.

Reset afterwards: `python scripts/demo_break.py --revert`.

---

### 06 — Custom instructions (5 min) · **IDE**

> **Surface argument:** the payoff is seeing the rule and the code it produced at
> the same time. That needs an editor with two files open and a diff view.

Open [.github/copilot-instructions.md](../.github/copilot-instructions.md) and one
scoped file, e.g.
[pricing.instructions.md](../.github/instructions/pricing.instructions.md). Point
at `applyTo:` — these apply by path, so the money rules only load when money is
in play.

Run `/06-ide-instructions`. It lists the rules it is about to follow
*before* writing code, then shows you where each one is visible in the diff.

The beat: it raises a `FreightlineError` subclass with a `code`, it names the
test as a sentence, and it does not write a float. Nobody asked for any of that
in the prompt.

> The one-liner: *every rule in here is a code review comment somebody got tired
> of leaving.*

**Now set up step 07.** This is the most important transition in the deck:

> *"Everything I just showed you lives in VS Code and on GitHub.com. Custom
> instructions don't travel any further than that. Watch what happens when I
> leave the editor entirely."*

---

### 07 — Skills (6 min) · **CLI**

> **Surface argument:** this is the portability proof, and it only lands if you
> leave the IDE. GitHub's own comparison is explicit: custom instructions are VS
> Code and GitHub.com; **Agent Skills work in VS Code, Copilot CLI, and the
> coding agent.** Same `SKILL.md`, three runtimes, open standard.

Open [.github/skills/add-surcharge/SKILL.md](../.github/skills/add-surcharge/SKILL.md)
so the room can read it. Say what a skill is: instructions apply automatically by
path; a skill loads when the *task* matches, and it can carry scripts and
examples with it.

Then close the editor and go to the terminal.

```bash
copilot -p "$(python scripts/demo_prompt.py 07)"
```

Narrate it working the checklist in order and reporting which step it is on. It
prints unified diffs, because there is no diff view out here.

Land it: *the difference between the ten-year veteran and the new starter is
knowing that this change touches the CLI too. That knowledge was in someone's
head. Now it is in the repo.*

Then land it a second time, which is the part people remember:

> *"And that file is not a VS Code file. It is the same file the coding agent
> read on that pull request."*

---

### 08 — Custom agents (5 min) · **IDE**

> **Surface argument:** three things here are editor affordances — the agent
> picker, the visible tool list, and the handoff button that moves the findings
> to a second agent in one click.

Open the agent picker. Show the three in
[.github/agents/](../.github/agents/): `security-auditor`, `api-contract-guardian`,
`legacy-migrator`.

Open `security-auditor.agent.md`. Point at two lines:

- `tools:` — no `edit`. It physically cannot change your code.
- the body — it knows *this* codebase's sinks, not generic OWASP advice.

Run `/08-ide-security-audit`. Then show the **handoff** button at the bottom of
the response, and click through to the fixing agent.

The framing: *not a smarter model — a narrower one. Same model, one job, the
right tools.*

---

### 09 — Copilot SDK (5 min) · **IDE + terminal**

> **Surface argument:** this one is deliberately surface-*less*. You have just
> shown four places Copilot lives. The SDK is how you build a fifth one that is
> yours — so run it where it would actually live, in a terminal, and read it
> where you would actually maintain it.

```bash
python tools/copilot_sdk/rate_card_auditor.py --carrier atlas
```

While it runs, open [the source](../tools/copilot_sdk/rate_card_auditor.py) and
show three things:

- `@define_tool` on `get_rate_card` — the model asks for our data instead of
  being handed a paraphrase of it;
- `deny_shell` — the host process decides what the agent is allowed to do;
- the exit code — it composes with CI.

Then run `/09-ide-sdk-automation` to extend it live if you have time.

The point: *the agent is now a library. Anywhere you have a script, you can have
this.*

---

### 10 — Monday (3 min) · **App**

> **Surface argument:** the output is a plan for a *different* repository, so
> produce it somewhere that is not this repository's workspace. Closing the
> laptop before the last slide is the demo.

Close VS Code. Close the terminal. Run `10-app-monday-plan` in the app and let it
produce the plan on screen.

Close on the three concrete actions:

1. Add `.github/copilot-instructions.md` to one repository. One hour.
2. Turn on Copilot code review for your next pull request. One click.
3. Find one issue you have been ignoring for a month and assign it.

Then: *this repository is the worked example. Clone it, read the ten prompts,
steal the instruction files.*

---

## Three things not to do on stage

1. **Do not run 02 in the CLI.** It works — and you lose the per-edit diff
   approval, which is your answer to the control objection.
2. **Do not run 05 in the IDE.** It works — and it makes the CLI look redundant.
   You will have argued yourself out of a surface.
3. **Do not run 04 entirely on the web.** The web shows *automatic*; the IDE
   shows *interrogable*. The contrast is the content.

## Reset between runs

```bash
scripts/demo_reset.sh          # dry run — shows what it would discard
scripts/demo_reset.sh --yes    # do it
```

Discards uncommitted changes under `src/`, `tests/`, `docs/`, deletes the demo
artifacts and local `demo/*` branches, re-seeds, and re-runs the tests.

Remote branches are left alone on purpose — `--yes` prints the `git push origin
--delete` command for any it finds, but will not run it for you. Close the demo
pull request when you are done with it; it must never be merged.

Because the reset only deletes the branch **locally**, rebuilding after a reset
that you pushed needs `--force`:

```bash
scripts/demo_review_branch.sh --push --force   # refreshes the branch and its PR
```

Without `--force` the script stops and tells you, rather than building a branch
whose push would be rejected.

`demo_review_branch.sh` always bases the PR on the repository's **default**
branch, whatever branch you happen to be standing on. Override with
`--base <branch>` if you need something else.

## If something goes wrong

| Symptom | Do this |
| --- | --- |
| Forgot which surface a prompt wants | `python scripts/demo_prompt.py --list` prints the surface and the reason. It is also in the filename. |
| A prompt is not in the slash menu | Chat view → right-click → Diagnostics. Check `.github/prompts/` was picked up. |
| The agent's carrier work stalls | Tell it: `run pytest tests/test_carrier_contract.py and fix what fails`. |
| No coding-agent PR yet | Skip to 04; come back at 09. `demo/saved-searches` is pre-built either way. |
| CLI not authenticated | `copilot` then `/login`. Do this before you start. |
| SDK runtime missing | `python -m copilot download-runtime`. Do this before you start. |
| The app cannot see the repo | Fall back to Copilot chat on github.com — same argument, same prompt. |
| Running long | Cut 09 to the source walkthrough only. Never cut 07 or 10. |
