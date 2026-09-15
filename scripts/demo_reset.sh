#!/usr/bin/env bash
# Put the repository back into its demo-ready state.
#
#   scripts/demo_reset.sh          # show what would change (default)
#   scripts/demo_reset.sh --yes    # actually do it
#
# This DISCARDS uncommitted work in src/, tests/, and docs/, and deletes the
# demo branches. It is deliberately a dry run unless you pass --yes.
set -euo pipefail

APPLY=0
[[ "${1:-}" == "--yes" ]] && APPLY=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARTIFACTS=(
  "src/freightline/carriers/cascade.py"
  "src/freightline/storage/saved_searches.py"
  "src/freightline/api/routes_saved_searches.py"
  "src/freightline/storage/migrations/0004_saved_searches.sql"
  "tests/test_saved_searches.py"
  "tests/test_cascade.py"
)

echo "=== uncommitted changes that would be discarded ==="
git status --short -- src tests docs CHANGELOG.md || true

echo
echo "=== generated files that would be deleted ==="
for path in "${ARTIFACTS[@]}"; do
  [[ -e "$path" ]] && echo "  $path"
done
[[ -d var ]] && echo "  var/ (demo database)"

echo
echo "=== branches that would be deleted ==="
git branch --list 'demo/*' | sed 's/^/  /' || true

if [[ "$APPLY" != "1" ]]; then
  echo
  echo "dry run. Re-run with --yes to apply."
  exit 0
fi

echo
CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT" == demo/* ]]; then
  git switch main 2>/dev/null || git switch master
fi

git checkout -- src tests docs CHANGELOG.md 2>/dev/null || true
for path in "${ARTIFACTS[@]}"; do
  rm -f "$path"
done
rm -rf var

while read -r branch; do
  [[ -n "$branch" ]] && git branch -D "$branch"
done < <(git branch --list 'demo/*' | tr -d ' *')

# Remote demo branches are left alone on purpose. Delete them yourself if you
# pushed one: git push origin --delete demo/saved-searches
if git ls-remote --heads origin 'demo/*' 2>/dev/null | grep -q .; then
  echo
  echo "note: demo branches still exist on origin. To remove them:"
  git ls-remote --heads origin 'demo/*' | awk '{sub("refs/heads/","",$2); print "  git push origin --delete " $2}'
fi

if [[ -x .venv/bin/python ]]; then
  .venv/bin/python scripts/seed_data.py
  .venv/bin/python -m pytest -q
fi

echo
echo "reset complete. Run /00-ide-preflight in chat to confirm."
