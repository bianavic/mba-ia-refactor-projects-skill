#!/usr/bin/env bash
#
# arch-check.sh — stack-agnostic structural check for AP-16
# ("Persistence/ORM Calls Inline in Routes").
#
# Shipped with the refactor-arch skill. Phase 3, step 6 runs this against the
# audited project when that project does not already ship an equivalent check.
#
# Why this exists as a separate script: endpoint tests prove BEHAVIOR over HTTP,
# this proves STRUCTURE by reading the code. Black-box testing cannot tell a
# route that queries the database directly from one that delegates to a
# Controller/Service — both return the same HTTP response.
#
# Usage:
#   arch-check.sh [PROJECT_DIR]
#
# Configuration (optional). Either export the variables or drop a shell file
# named `.arch-check.conf` at the root of PROJECT_DIR defining them:
#   ROUTE_DIRS        extra regex of directory names holding route/view files
#   ROUTE_FILE_GLOBS  extra regex of route/view FILE names (basename match)
#   EXTRA_PATTERN     extra regex of persistence calls for this stack
#   EXCLUDE_PATTERN   regex of matches to ignore (documented exceptions)
#
# Exit codes: 0 = PASS (no inline persistence call), 1 = FAIL (lists file:line),
#             2 = could not determine what to scan (treated as a failure to
#                 verify, never as a pass).

set -uo pipefail

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR="$(cd "$PROJECT_DIR" 2>/dev/null && pwd)" || {
  printf 'arch-check: no such directory: %s\n' "${1:-}" >&2
  exit 2
}
PROJECT_NAME="$(basename "$PROJECT_DIR")"

# shellcheck disable=SC1091
[ -f "$PROJECT_DIR/.arch-check.conf" ] && . "$PROJECT_DIR/.arch-check.conf"

ROUTE_DIRS="${ROUTE_DIRS:-}"
ROUTE_FILE_GLOBS="${ROUTE_FILE_GLOBS:-}"
EXTRA_PATTERN="${EXTRA_PATTERN:-}"
EXCLUDE_PATTERN="${EXCLUDE_PATTERN:-}"

# ---------------------------------------------------------------------------
# 1. Source discovery — which extensions this project actually uses.
# ---------------------------------------------------------------------------

find_sources() {
  find "$PROJECT_DIR" \
    \( -name node_modules -o -name .git -o -name .claude -o -name venv \
       -o -name .venv -o -name env -o -name __pycache__ -o -name dist \
       -o -name build -o -name target -o -name vendor -o -name .idea \
       -o -name migrations -o -name testdata \) -prune -o \
    -type f \( -name '*.py' -o -name '*.js' -o -name '*.mjs' -o -name '*.ts' \
    -o -name '*.go' -o -name '*.java' -o -name '*.kt' -o -name '*.rb' \
    -o -name '*.php' -o -name '*.cs' \) -print 2>/dev/null
}

ALL_SOURCES="$(find_sources | sort)"

if [ -z "$ALL_SOURCES" ]; then
  printf 'arch-check: no source files found under %s\n' "$PROJECT_DIR" >&2
  exit 2
fi

detect_langs() {
  printf '%s\n' "$ALL_SOURCES" | sed 's/.*\.//' | sort -u
}
LANGS="$(detect_langs)"
has_lang() { printf '%s\n' "$LANGS" | grep -qx "$1"; }

# ---------------------------------------------------------------------------
# 2. Route/view file selection.
#
# A file is a route/view file when it lives in a routing directory OR its name
# marks it as one. Controllers/services are deliberately NOT scanned: they are
# the layer persistence calls are supposed to be moved INTO.
# ---------------------------------------------------------------------------

DIR_RE='/(routes?|views?|urls|handlers?|endpoints?|resources?|web|http|delivery|api)/'
[ -n "$ROUTE_DIRS" ] && DIR_RE="$DIR_RE|/($ROUTE_DIRS)/"

FILE_RE='/[^/]*(route|router|routes|urls|handler|endpoint|resource|controller_test)[^/]*\.[a-z]+$'
[ -n "$ROUTE_FILE_GLOBS" ] && FILE_RE="$FILE_RE|/[^/]*($ROUTE_FILE_GLOBS)[^/]*\.[a-z]+$"

# Middlewares/interceptors are a cross-cutting layer, not the routing layer —
# `error_handler.py` matching "handler" above is a false positive, so drop them.
NOT_ROUTE_RE='/(middlewares?|interceptors?|filters?)/|/[^/]*error[_.-]?handler[^/]*\.'

ROUTE_FILES="$(printf '%s\n' "$ALL_SOURCES" \
  | grep -Ei "$DIR_RE|$FILE_RE" \
  | grep -Eiv "$NOT_ROUTE_RE" \
  | sort -u)"

# ---------------------------------------------------------------------------
# 3. Persistence patterns, by detected language.
#
# Kept in sync with the AP-16 signals in
# references/anti-patterns-catalog.md and with references/verification-recipes.md.
# ---------------------------------------------------------------------------

# Universal: raw SQL literals embedded in a route file.
PATTERN='(SELECT[[:space:]]+.*[[:space:]]FROM[[:space:]]|INSERT[[:space:]]+INTO[[:space:]]|DELETE[[:space:]]+FROM[[:space:]]|UPDATE[[:space:]]+[A-Za-z_"`]+[[:space:]]+SET[[:space:]])'
# Universal: a raw driver/cursor/pool handle being queried.
PATTERN="$PATTERN"'|\b(cursor|conn|connection|db|database|pool|client|knex|tx)\.(execute|executemany|query|queryRow|run|all|get|prepare|exec|fetchone|fetchall)[[:space:]]*\('

if has_lang py; then
  PATTERN="$PATTERN"'|\bdb\.session\.'
  PATTERN="$PATTERN"'|\bsession\.(add|commit|delete|merge|flush|refresh|scalars|scalar|execute)[[:space:]]*\('
  PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*\.query\b'
  PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*\.objects\.'
  PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*\.(get_by_id|get_all|find_by_[a-z_]+)[[:space:]]*\('
fi

if has_lang js || has_lang mjs || has_lang ts; then
  PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*\.(find|findOne|findAll|findById|findByPk|findFirst|findMany|create|update|updateOne|upsert|destroy|insert|insertMany|save|delete|deleteOne|deleteMany|remove|aggregate|count)[[:space:]]*\('
  PATTERN="$PATTERN"'|\bprisma\.[a-z]'
fi

if has_lang go; then
  PATTERN="$PATTERN"'|\b(db|DB|tx|gormDB|orm)\.(Query|QueryRow|QueryContext|Exec|ExecContext|Find|First|Take|Last|Where|Create|Save|Updates?|Delete|Preload|Joins|Model|Raw|Scan|Table)[[:space:]]*\('
  PATTERN="$PATTERN"'|\b(gorm|sqlx|sql)\.(Open|Connect|DB\b)'
  PATTERN="$PATTERN"'|\bGetDB[[:space:]]*\('
  # Go exposes persistence as package-level functions, not methods on a model,
  # so receiver-based patterns miss it entirely. Verb-first free functions
  # (FindOneUser, SaveOne, DeleteArticleModel) are the idiomatic AP-16 shape.
  PATTERN="$PATTERN"'|\b(Find|Save|Insert|Delete|Remove|Update|Upsert|Fetch|Query|Load)[A-Z][A-Za-z0-9_]*[[:space:]]*\('
  PATTERN="$PATTERN"'|\bGet[A-Za-z0-9_]*Model[[:space:]]*\('
fi

if has_lang java || has_lang kt; then
  PATTERN="$PATTERN"'|\b(entityManager|em|jdbcTemplate|sessionFactory)\.'
  PATTERN="$PATTERN"'|\.(createQuery|createNativeQuery|persist|merge|flush)[[:space:]]*\('
  PATTERN="$PATTERN"'|\b[a-zA-Z]*Repository\.(save|saveAll|findAll|findById|findBy[A-Za-z]+|delete|deleteById|count)[[:space:]]*\('
fi

if has_lang rb; then
  PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*\.(find|find_by|where|create|create!|update|update!|destroy|destroy_all|all|first|last|pluck)\b'
  PATTERN="$PATTERN"'|ActiveRecord::'
fi

if has_lang php; then
  PATTERN="$PATTERN"'|\bDB::(table|select|insert|update|delete|statement|raw)[[:space:]]*\('
  PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*::(find|findOrFail|where|create|all|destroy|firstWhere)[[:space:]]*\('
  PATTERN="$PATTERN"'|->(prepare|execute|query|fetchAll|fetch)[[:space:]]*\('
fi

if has_lang cs; then
  PATTERN="$PATTERN"'|\b(context|_context|dbContext|_db)\.(Set|SaveChanges|SaveChangesAsync|Add|Remove|Update|Find|FindAsync)[[:space:]]*\('
fi

[ -n "$EXTRA_PATTERN" ] && PATTERN="$PATTERN|$EXTRA_PATTERN"

# Comment-only lines are not code — they never count as a violation.
COMMENT_ONLY='^[0-9]+:[[:space:]]*(#|//|\*|/\*|--|"""|'"'''"')'

# ---------------------------------------------------------------------------
# 4. Report.
# ---------------------------------------------------------------------------

printf '==========================================================\n'
printf 'arch-check — %s\n' "$PROJECT_NAME"
printf 'AP-16: routes must not touch persistence directly\n'
printf 'Detected sources: %s\n' "$(printf '%s' "$LANGS" | tr '\n' ' ')"
printf '==========================================================\n\n'

if [ -z "$ROUTE_FILES" ]; then
  printf 'INCONCLUSIVE: no route/view file identified under %s.\n' "$PROJECT_NAME"
  printf 'This is not a pass — AP-16 was not verified. Point the check at the\n'
  printf 'routing layer with ROUTE_DIRS / ROUTE_FILE_GLOBS (see the header, or\n'
  printf 'references/verification-recipes.md).\n'
  printf '==========================================================\n'
  exit 2
fi

total_hits=0
bad_files=0
scanned=0

while IFS= read -r file; do
  [ -n "$file" ] || continue
  rel="${file#"$PROJECT_DIR"/}"
  scanned=$((scanned + 1))

  hits="$(grep -nE "$PATTERN" "$file" 2>/dev/null | grep -vE "$COMMENT_ONLY")"
  [ -n "$EXCLUDE_PATTERN" ] && hits="$(printf '%s' "$hits" | grep -vE "$EXCLUDE_PATTERN")"

  if [ -z "$hits" ]; then
    printf '  OK   %s\n' "$rel"
  else
    count="$(printf '%s\n' "$hits" | wc -l | tr -d ' ')"
    printf '  FAIL %s — %s inline call(s)\n' "$rel" "$count"
    printf '%s\n' "$hits" | sed 's/^/         /'
    total_hits=$((total_hits + count))
    bad_files=$((bad_files + 1))
  fi
done <<EOF
$ROUTE_FILES
EOF

printf '\n==========================================================\n'
if [ "$total_hits" -eq 0 ]; then
  printf 'PASS: no route in %s touches persistence directly.\n' "$PROJECT_NAME"
  printf '(%d route file(s) checked)\n' "$scanned"
  printf '==========================================================\n'
  exit 0
fi

printf 'FAIL: %d inline persistence call(s) across %d route file(s).\n' \
  "$total_hits" "$bad_files"
printf 'Move each call into a Controller/Service; the route may only call that function.\n'
printf '==========================================================\n'
exit 1
