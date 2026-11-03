#!/usr/bin/env bash
#
# completion-box.sh — prints the Phase 3 completion box, the challenge's fixed template.
# The box text is fixed here, not composed by hand; the tree is generated from the directory.
#
# Usage: completion-box.sh <project-dir>
# Exit:  0 box printed | 1 a precondition failed (reasons on stderr, nothing on stdout) | 2 usage
#
# Preconditions, all checked here: arch-check.sh exits 0 (structural rules AP-06/AP-22/AP-23 only —
# "Zero anti-patterns remaining" also relies on the Phase 2 re-audit, which this script does not run),
# and the validation log
# <repo root>/evidence/logs/<project dir>-validation.txt is valid (Domain line, AP-12 lines with none
# BLOCKED — "BLOCKED (left open)", the user's Phase 2 answer to a failed lookup, is accepted —, a boot section showing the app listening, a passing DB target line, api-test.sh footer
# with TOTAL, a coverage line with equal numbers, exit code 0). The log and api-test.sh are produced by
# the Phase 3 validation step; neither exists until that step runs.

set -uo pipefail

PROJECT="${1:-}"
[ -d "$PROJECT" ] || { echo "usage: completion-box.sh <project-dir>" >&2; exit 2; }
PROJECT="$(cd "$PROJECT" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$PROJECT" rev-parse --show-toplevel 2>/dev/null)" || REPO="$(dirname "$PROJECT")"
LOG="$REPO/evidence/logs/$(basename "$PROJECT")-validation.txt"

problems=()
add() { problems+=("$1"); }

bash "$HERE/arch-check.sh" "$PROJECT" >/dev/null 2>&1 || add "arch-check.sh did not exit 0"

if [ ! -s "$LOG" ]; then
  add "validation log missing or empty: $LOG"
else
  grep -q '^Domain: ' "$LOG" || add "log: no Domain: line"
  grep -q '^AP-12: ' "$LOG" || add "log: no AP-12: line"
  # Only a bare BLOCKED fails; "BLOCKED (left open)" is a Phase 2 decision, counted as left open.
  ! grep -q '^AP-12: .*| BLOCKED |' "$LOG" \
    || add "log: an AP-12 component is BLOCKED without a Phase 2 decision (retry, or leave it open)"
  sed -n '/^## Boot/,/^## api-test.sh/p' "$LOG" | grep -qiE 'running on|listening|started|ready' \
    || add "log: boot section does not show the application listening"
  grep -q '^DB target: ' "$LOG" && ! grep -q '^DB target: not isolated' "$LOG" \
    || add "log: no passing DB target: line"
  grep -q '^TOTAL' "$LOG" || add "log: no TOTAL footer"
  cov="$(grep -E '[0-9]+ endpoints inventoried / [0-9]+ exercised' "$LOG" | tail -n 1)"
  if [ -z "$cov" ]; then add "log: no coverage line"
  else
    inv="$(printf '%s' "$cov" | sed -E 's/.*[^0-9]([0-9]+) endpoints inventoried.*/\1/')"
    exe="$(printf '%s' "$cov" | sed -E 's/.*\/ ([0-9]+) exercised.*/\1/')"
    [ "$inv" = "$exe" ] || add "log: coverage differs ($inv inventoried / $exe exercised)"
  fi
  [ "$(grep -E '^api-test\.sh exit code: ' "$LOG" | tail -n 1)" = "api-test.sh exit code: 0" ] \
    || add "log: api-test.sh exit code is not 0"
fi

if [ "${#problems[@]}" -gt 0 ]; then
  echo "completion-box: not printing the box — Phase 3 is not complete:" >&2
  for p in "${problems[@]}"; do echo "  - $p" >&2; done
  exit 1
fi

# directory tree: no hidden tooling, caches, dependencies, build output, databases or env files
SKIP_DIRS=".git .claude .idea .vscode node_modules __pycache__ venv .venv dist build target vendor"
SKIP_FILES=".DS_Store .env"

skipped() { # skipped <name> <is-dir>
  local n="$1" s
  for s in $SKIP_DIRS; do [ "$2" = 1 ] && [ "$n" = "$s" ] && return 0; done
  for s in $SKIP_FILES; do [ "$n" = "$s" ] && return 0; done
  case "$n" in *.pyc|*.db|*.sqlite|*.sqlite3|*.log) return 0 ;; esac
  return 1
}

print_tree() { # print_tree <dir> <prefix>
  local dir="$1" prefix="$2" entries=() name
  while IFS= read -r name; do
    [ -d "$dir/$name" ] && d=1 || d=0
    skipped "$name" "$d" || entries+=("$name")
  done < <(ls -A "$dir" | LC_ALL=C sort)
  local total="${#entries[@]}" i=0 branch next
  for name in ${entries[@]+"${entries[@]}"}; do
    i=$((i + 1))
    if [ "$i" -eq "$total" ]; then branch="└── "; next="    "; else branch="├── "; next="│   "; fi
    if [ -d "$dir/$name" ]; then
      printf '%s%s%s/\n' "$prefix" "$branch" "$name"
      print_tree "$dir/$name" "$prefix$next"
    else
      printf '%s%s%s\n' "$prefix" "$branch" "$name"
    fi
  done
}

cat <<'BOX'
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
BOX
printf '%s/\n' "$(basename "$PROJECT")"
print_tree "$PROJECT" ""
cat <<'BOX'

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
BOX
