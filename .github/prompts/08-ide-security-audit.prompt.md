---
name: 08-ide-security-audit
description: "IDE — agent picker, read-only tools, handoffs: one job, done narrowly"
agent: security-auditor
---

Audit branch `demo/saved-searches` against `main`.

```bash
git diff main...demo/saved-searches
```

Then widen: the saved-search code is new, but check whether the same class of
defect exists anywhere else in `src/freightline/`. If the branch introduces an
unparameterised query, go and confirm whether `ShipmentRepository` has one too.

Give me the finding table first, then the detail, then the **Clean** list.

I specifically want to know:

- which findings are exploitable by an unauthenticated caller;
- which ones the repository's own instruction files already prohibit in writing,
  and therefore should never have reached review;
- and for the highest-severity finding, the regression test that would have made
  this branch fail CI.

Do not edit anything. Show me the patches in chat.
