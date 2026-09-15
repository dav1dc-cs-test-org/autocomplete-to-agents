#!/usr/bin/env bash
# Build the deliberately-defective branch used by the code-review demo steps.
#
#   scripts/demo_review_branch.sh                  # create the branch locally
#   scripts/demo_review_branch.sh --push           # ...push it and open a PR
#   scripts/demo_review_branch.sh --push --base X  # against a non-default base
#
# The branch is never merged. scripts/demo_reset.sh removes it.
set -euo pipefail

BRANCH="demo/saved-searches"
PUSH=0
BASE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --base) BASE="${2:?--base needs a branch name}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "working tree is dirty. Commit or stash before building the demo branch." >&2
  git status --short >&2
  exit 1
fi

if git show-ref --quiet --verify "refs/heads/$BRANCH"; then
  echo "$BRANCH already exists. Run scripts/demo_reset.sh --yes first." >&2
  exit 1
fi

# The base is the repository's default branch, never the branch you happen to be
# standing on: a local scratch branch produces a PR nobody can open.
if [[ -z "$BASE" ]] && command -v gh >/dev/null 2>&1; then
  BASE="$(GH_PAGER=cat gh repo view --json defaultBranchRef \
            --jq .defaultBranchRef.name 2>/dev/null || true)"
fi
if [[ -z "$BASE" ]]; then
  BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  BASE="${BASE#origin/}"
fi
BASE="${BASE:-main}"

if ! git show-ref --quiet --verify "refs/heads/$BASE"; then
  echo "base branch '$BASE' does not exist locally. Run: git fetch origin $BASE" >&2
  exit 1
fi

START="$(git rev-parse --abbrev-ref HEAD)"
trap 'git switch --quiet "$START" 2>/dev/null || true' EXIT

echo "base branch:    $BASE"
echo "starting point: $START"

# Branch from the base, not from HEAD, so the PR diff is exactly the seeded change.
git switch --quiet -c "$BRANCH" "$BASE"

cp demo/pr/changes/saved_searches.py        src/freightline/storage/saved_searches.py
cp demo/pr/changes/routes_saved_searches.py src/freightline/api/routes_saved_searches.py
cp demo/pr/changes/0004_saved_searches.sql  src/freightline/storage/migrations/0004_saved_searches.sql
cp demo/pr/changes/test_saved_searches.py   tests/test_saved_searches.py

python3 - <<'PY'
from pathlib import Path

app = Path("src/freightline/api/app.py")
text = app.read_text(encoding="utf-8")

text = text.replace(
    "from . import routes_admin, routes_quotes, routes_shipments",
    "from . import routes_admin, routes_quotes, routes_saved_searches, routes_shipments",
    1,
)
text = text.replace(
    "    app.include_router(routes_shipments.router)",
    "    app.include_router(routes_shipments.router)\n"
    "    app.include_router(routes_saved_searches.router)",
    1,
)
app.write_text(text, encoding="utf-8")
print("wired routes_saved_searches into app.py")
PY

if [[ -x .venv/bin/python ]]; then
  echo
  echo "--- proving CI would be green ---"
  .venv/bin/ruff check src tests scripts
  .venv/bin/mypy
  .venv/bin/python -m pytest -q
fi

git add -A
git commit -q -m "Add saved searches for the ops dashboard

Ops re-type the same shipment filters every week for the exception review.
This stores a filter once and re-runs it.

- POST   /v1/saved-searches
- GET    /v1/saved-searches
- GET    /v1/saved-searches/{id}/run
- DELETE /v1/saved-searches/{id}

Includes migration 0004 and tests."

echo
echo "created $BRANCH from $BASE"

if [[ "$PUSH" == "1" ]]; then
  git push -u origin "$BRANCH"

  if ! git ls-remote --exit-code --heads origin "$BASE" >/dev/null 2>&1; then
    echo "cannot open a PR: base '$BASE' does not exist on origin." >&2
    echo "push it first, or re-run with --base <an existing remote branch>." >&2
  elif command -v gh >/dev/null 2>&1; then
    GH_PAGER=cat gh pr create \
      --base "$BASE" \
      --head "$BRANCH" \
      --title "Add saved searches for the ops dashboard" \
      --body-file demo/pr/PR_BODY.md \
      || echo "gh pr create failed; open it manually against $BASE." >&2
  else
    echo "gh not found; open the PR manually against $BASE."
  fi
fi

echo
echo "returning to $START. Review with: git diff $BASE...$BRANCH"
