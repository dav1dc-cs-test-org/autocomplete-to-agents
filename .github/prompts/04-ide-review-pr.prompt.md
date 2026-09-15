---
name: 04-ide-review-pr
description: "IDE — multi-file context: the correct pattern is two directories away"
agent: agent
---

Branch `demo/saved-searches` adds a saved-search feature. CI is green: ruff
passes, mypy passes, every test passes, and the PR ships its own tests.

Review it as if you were the last person to look at it before it goes to
production.

```bash
git diff main...demo/saved-searches
```

For every problem you find:

- name it and give it a severity;
- show the **exact input** that exploits or triggers it;
- give me the replacement code;
- name the test that should have caught it, as a sentence, and say why the tests
  in the PR do not.

Then open `src/freightline/storage/repository.py` and
`src/freightline/api/routes_admin.py` alongside the new code. For each finding,
tell me which of two kinds it is:

- **wrong in the abstract** — you would flag it in any codebase;
- **inconsistent with this one** — the correct pattern already exists two
  directories away, and the new file simply disagrees with it.

The second kind is the interesting one. Quote both versions side by side.

Then answer the question that matters for this demo: **which of these findings
could a linter or a type checker have found, and which needed someone to
actually read the code?** Be honest — if ruff would have caught it, say so, and
check whether anything in the diff stopped ruff from catching it.

Do not fix anything yet. I want the review first.
