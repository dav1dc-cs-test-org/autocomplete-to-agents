---
name: 05-cli-triage
description: "CLI — one scrollback: failing tests, git diff, fix, re-run, stage"
agent: agent
---

The build is red. I did not write the change and I do not know what it was.

Work it out from the terminal, the way you would at 4pm on a Friday:

1. Run the test suite. Do not fix anything yet — read the failures first.
2. Tell me what the failures have in common. Which module is implicated, and
   what does the *pattern* of failures say about the change that caused it?
3. Use `git diff` to find the actual change. Show me just the relevant hunk.
4. Explain the bug in one sentence — the behaviour, not the diff.
5. Fix it. Smallest possible change.
6. Add the regression test that would have caught it, named as a sentence.
7. Run `make check` and show me it is green.
8. Stage the fix and write the commit message. Do not commit until I say so.

If more than one thing is broken, deal with them one at a time and say which you
are on.
