#!/usr/bin/env bash
# Build the deliberately-defective branch used by the code-review demo steps.
#
#   scripts/demo_review_branch.sh            # create the branch locally
#   scripts/demo_review_branch.sh --push     # ...and push it and open a PR
#
# The branch is never merged. scripts/demo_reset.sh removes it.
set -euo pipefail

BRANCH="demo/saved-searches"
PUSH=0
[[ "${1:-}" == "--push" ]] && PUSH=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "working tree is dirty. Commit or stash before building the demo branch." >&2
  git status --short >&2
  exit 1
fi

BASE="$(git rev-parse --abbrev-ref HEAD)"
echo "base branch: $BASE"

git switch -c "$BRANCH" 2>/dev/null || git switch "$BRANCH"

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
echo "created $BRANCH"

if [[ "$PUSH" == "1" ]]; then
  git push -u origin "$BRANCH"
  if command -v gh >/dev/null 2>&1; then
    GH_PAGER=cat gh pr create \
      --base "$BASE" \
      --head "$BRANCH" \
      --title "Add saved searches for the ops dashboard" \
      --body-file demo/pr/PR_BODY.md
  else
    echo "gh not found; open the PR manually."
  fi
fi

git switch "$BASE"
echo "back on $BASE. Review with: git diff $BASE...$BRANCH"
