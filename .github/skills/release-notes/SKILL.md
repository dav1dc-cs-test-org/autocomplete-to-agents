---
name: release-notes
description: Produce release notes for Freightline from the commit history. Use when asked for release notes, a changelog entry, a summary of what shipped, or what changed since a tag or between two refs.
argument-hint: [since ref, e.g. v4.7.1 or HEAD~20]
---

# Release notes

## Gather

```bash
git log --no-pager --oneline --no-merges <since>..HEAD
git --no-pager diff --stat <since>..HEAD
```

If no `<since>` is given, use the most recent tag (`git describe --tags
--abbrev=0`), and fall back to `HEAD~20` when there are no tags.

## Classify

Group every commit under exactly one heading, in this order. Drop headings with
no entries.

- **Breaking** — anything in the API-contract breaking column, a renamed error
  `code`, a changed surcharge `code`, or a removed CLI flag.
- **Added**
- **Changed**
- **Fixed**
- **Security**
- **Internal** — refactors, tests, tooling. One rolled-up line, not a list.

## Write

Each entry is one line, in the imperative, describing the **user-visible
effect** — not the implementation.

```
- Quote responses now include a `dangerous_goods` line for UN-classified parcels.
```

not

```
- Added DangerousGoodsSurcharge class to surcharges.py
```

Rules:

- Name the affected surface in backticks: `POST /v1/quotes`, `freightline ship`,
  `carrier_code`.
- A breaking entry states the migration in the same line: what to change, and by
  when.
- No commit hashes in the body. No "various fixes".
- If a commit's effect is not determinable from its message, open the diff rather
  than guessing, and if it is still unclear, list it under Internal.

## Output

Write to `CHANGELOG.md` under a new version heading above `## Unreleased`, in
Keep a Changelog style, and print the same block in the chat so it can be pasted
into a GitHub release.
