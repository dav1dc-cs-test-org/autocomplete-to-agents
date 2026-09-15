# Demo PR: `demo/saved-searches`

> **These files are intentionally defective.** They exist so the Copilot Code
> Review and `security-auditor` demo steps have something real to find. They are
> not part of `main` and must never be merged.

`scripts/demo_review_branch.sh` copies them into place on a throwaway branch,
commits, and optionally opens a pull request.

## Why it looks green

The whole point of this demo beat is that **CI passes**:

- `ruff` passes — the security rules that would have fired are suppressed with
  `# noqa`, the way a hurried developer suppresses them.
- `mypy` passes — everything is annotated.
- `pytest` passes — the branch ships its own tests, and they only cover the happy
  path, which is the normal failure mode of self-reviewed tests.

A reviewer has to actually read it.

## What is wrong (presenter crib sheet — do not read this out)

| # | Defect | File |
| --- | --- | --- |
| 1 | `filter_expression` is interpolated straight into a `WHERE` clause; it arrives from an unauthenticated HTTP body | `saved_searches.py` |
| 2 | `order_by` is interpolated with no allow-list, unlike `ShipmentRepository.search` two files away | `saved_searches.py` |
| 3 | `limit` is interpolated and never capped, so one request can read the whole table | `saved_searches.py` |
| 4 | `except Exception: pass` swallows the failure of the delete, including the authorisation failure | `saved_searches.py` |
| 5 | A share token literal in source, compared with `==` rather than `compare_digest` | `saved_searches.py` |
| 6 | The router has no `require_admin` dependency, so all of the above is anonymous | `routes_saved_searches.py` |
| 7 | `limit` has no `le=` bound in the route signature, unlike every other paginated route | `routes_saved_searches.py` |
| 8 | Three `# noqa` comments suppressing four rules, added in the same commit as the code they silence | `saved_searches.py` |
| 9 | Tests assert only the happy path; no test supplies a hostile `filter_expression` | `test_saved_searches.py` |

Findings 2, 3, 6 and 7 are the interesting ones for the demo, because the correct
pattern already exists in this repository — `ShipmentRepository.search` does the
allow-list, the cap, and the bound, and `routes_admin.py` does the auth. The
review question is not "is this insecure in the abstract" but "why does this file
disagree with the file next to it".
