#!/usr/bin/env bash
#
# arch-check.sh — stack-agnostic heuristic structural check (read-only).
#   AP-06 persistence calls inside route files
#   AP-22 layer leakage: model->model / model->HTTP imports, controller function using >= 2 models,
#         missing/empty/unwired controller layer, route importing a model or service
#   AP-23 source files loose at the project root
#
# Usage: arch-check.sh [PROJECT_DIR]
#
# Optional configuration — export, or define in PROJECT_DIR/.arch-check.conf:
#   ROUTE_DIRS, ROUTE_FILE_GLOBS   extra regex of route directory / file names
#   EXTRA_PATTERN, EXCLUDE_PATTERN extra persistence-call regex / matches to ignore
#   MODEL_DIRS, CONTROLLER_DIRS    extra regex of model / controller directory names
#   LAYOUT_ROOT_ALLOW              root file basenames allowed to stay at the root
#   LAYOUT_EXCLUDE                 AP-22/AP-23 lines to ignore
#
# Line-based heuristic, not a parser: aliases, class methods, generated routes and multiline
# calls can be missed. Every `note:` line is a gap to verify by reading the code.
#
# Exit: 0 PASS | 1 FAIL (lists rule file:line) | 2 nothing to scan (never a pass)

set -uo pipefail

TMP_MODELS="$(mktemp)"; TMP_CTRL="$(mktemp)"
trap 'rm -f "$TMP_MODELS" "$TMP_CTRL"' EXIT

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR="$(cd "$PROJECT_DIR" 2>/dev/null && pwd)" || {
  printf 'arch-check: no such directory: %s\n' "${1:-}" >&2
  exit 2
}
PROJECT_NAME="$(basename "$PROJECT_DIR")"

case "$PROJECT_DIR" in */.claude/skills/*)
  printf 'arch-check: %s is inside a skill directory; pass the audited project directory as argument\n' "$PROJECT_DIR" >&2
  exit 2;;
esac

# shellcheck disable=SC1091
[ -f "$PROJECT_DIR/.arch-check.conf" ] && . "$PROJECT_DIR/.arch-check.conf"

ROUTE_DIRS="${ROUTE_DIRS:-}"
ROUTE_FILE_GLOBS="${ROUTE_FILE_GLOBS:-}"
EXTRA_PATTERN="${EXTRA_PATTERN:-}"
EXCLUDE_PATTERN="${EXCLUDE_PATTERN:-}"
MODEL_DIRS="${MODEL_DIRS:-}"
CONTROLLER_DIRS="${CONTROLLER_DIRS:-}"
LAYOUT_ROOT_ALLOW="${LAYOUT_ROOT_ALLOW:-}"
LAYOUT_EXCLUDE="${LAYOUT_EXCLUDE:-}"

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
# A file is a route/view file when ANY of these holds:
#   - it lives in a routing directory (routes/, views/, handlers/, ...);
#   - its name marks it as one (*route*, *router*, *urls*, ...);
#   - its content DECLARES a route (@app.route, @bp.get, router.post('/...')).
# The content rule is what catches a monolith whose routes live in app.py or
# app.js — without it such a project has "no route file" and the check is
# inconclusive exactly on the code that most needs it.
# Controllers/services are deliberately NOT scanned by name: they are the layer
# persistence calls are supposed to be moved INTO.
# ---------------------------------------------------------------------------

DIR_RE='/(routes?|views?|urls|handlers?|endpoints?|resources?|web|http|delivery|api)/'
[ -n "$ROUTE_DIRS" ] && DIR_RE="$DIR_RE|/($ROUTE_DIRS)/"

FILE_RE='/[^/]*(route|router|routes|urls|handler|endpoint|resource)[^/]*\.[a-z]+$'
[ -n "$ROUTE_FILE_GLOBS" ] && FILE_RE="$FILE_RE|/[^/]*($ROUTE_FILE_GLOBS)[^/]*\.[a-z]+$"

# Route declarations, per framework family.
#   Flask/FastAPI: @app.route(...), @bp.get(...), @router.post(...), add_url_rule(...)
#   Django:        urlpatterns = [...]
#   Express/Koa/Fastify-style: app.get('/x', ...), router.post("/x", ...)
DECL_RE='@[A-Za-z_][A-Za-z0-9_]*\.(route|get|post|put|delete|patch)[[:space:]]*\('
DECL_RE="$DECL_RE"'|\.add_url_rule[[:space:]]*\(|^urlpatterns[[:space:]]*='
DECL_RE="$DECL_RE"'|\b(app|router|server|[a-z][A-Za-z0-9_]*Router)\.(get|post|put|delete|patch|all|route)[[:space:]]*\([[:space:]]*['"'"'"`]/'

declares_routes() {
  printf '%s\n' "$ALL_SOURCES" | while IFS= read -r f; do
    [ -n "$f" ] && grep -Eq "$DECL_RE" "$f" 2>/dev/null && printf '%s\n' "$f"
  done
}

# Middlewares/interceptors are a cross-cutting layer, not the routing layer —
# `error_handler.py` matching "handler" above is a false positive, so drop them.
NOT_ROUTE_RE='/(middlewares?|interceptors?|filters?)/|/[^/]*error[_.-]?handler[^/]*\.'

ROUTE_FILES="$( { printf '%s\n' "$ALL_SOURCES" | grep -Ei "$DIR_RE|$FILE_RE"; declares_routes; } \
  | grep -Eiv "$NOT_ROUTE_RE" \
  | sort -u)"

# ---------------------------------------------------------------------------
# 3. Persistence patterns, by detected language.
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
  # (FindOneUser, SaveOne, DeleteArticleModel) are the idiomatic AP-06 shape.
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
printf 'AP-06: routes must not touch persistence directly\n'
printf 'Mode: heuristic line-based scan; PASS means no matching signal was found\n'
printf 'Detected sources: %s\n' "$(printf '%s' "$LANGS" | tr '\n' ' ')"
printf '==========================================================\n\n'

if [ -z "$ROUTE_FILES" ]; then
  printf 'INCONCLUSIVE: no route/view file identified under %s.\n' "$PROJECT_NAME"
  printf 'This is not a pass — AP-06 was not verified. Point the check at the\n'
  printf 'routing layer with ROUTE_DIRS / ROUTE_FILE_GLOBS (see the header of\n'
  printf 'scripts/arch-check.sh).\n'
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

ROUTE_RC=0
printf '\n----------------------------------------------------------\n'
if [ "$total_hits" -eq 0 ]; then
  printf 'AP-06 PASS: no route in %s touches persistence directly (%d route file(s) checked)\n' \
    "$PROJECT_NAME" "$scanned"
else
  printf 'AP-06 FAIL: %d inline persistence call(s) across %d route file(s).\n' \
    "$total_hits" "$bad_files"
  printf 'Move each call into a Controller/Service; the route may only call that function.\n'
  ROUTE_RC=1
fi

# ---------------------------------------------------------------------------
# 5. Layer structure (AP-22, AP-23).
#
# Model file   = a file in a model directory or named like one AND holding a
#                persistence call (PATTERN) or declaring an ORM entity
#                (MODEL_DECL_RE, e.g. SQLAlchemy `db.Model`). Helpers in the same
#                directory that do neither are not models.
# Controller   = a file in a controller directory or named like one.
# Heuristics are line-based, not a parser: they list candidates to confirm by
# opening the file. Limits are printed, never hidden.
# ---------------------------------------------------------------------------

LAYOUT_RC=0
layout_hits=0
layout_report=""
add_hit() { # <rule> <file:line> <text>
  local line="$1 $2 — $3"
  [ -n "$LAYOUT_EXCLUDE" ] && printf '%s' "$line" | grep -Eq "$LAYOUT_EXCLUDE" && return
  layout_report="$layout_report  FAIL $line"$'\n'
  layout_hits=$((layout_hits + 1))
}

MODEL_DIR_RE='/(models?|entities|repositories|repos|daos?)/'
[ -n "$MODEL_DIRS" ] && MODEL_DIR_RE="$MODEL_DIR_RE|/($MODEL_DIRS)/"
MODEL_FILE_RE='/[^/]*([Mm]odel|[Rr]epository|[Rr]epo|[Dd]ao|[Ee]ntity)[^/]*\.[a-z]+$'
CTRL_DIR_RE='/controllers?/'
[ -n "$CONTROLLER_DIRS" ] && CTRL_DIR_RE="$CTRL_DIR_RE|/($CONTROLLER_DIRS)/"
CTRL_FILE_RE='/[^/]*[Cc]ontroller[^/]*\.[a-z]+$'
MODEL_DECL_RE='\bdb\.Model\b|\(([A-Za-z_]+\.)?(Base|DeclarativeBase|Model)\)[[:space:]]*:|declarative_base[[:space:]]*\(|mongoose\.(Schema|model)[[:space:]]*\(|sequelize\.define[[:space:]]*\(|extends[[:space:]]+(Model|ActiveRecord::Base|ApplicationRecord)\b|@Entity\b'
TEST_RE='(^|/)(tests?|__tests__|spec)/|/(test_[^/]*|[^/]*_test|[^/]*\.test|[^/]*\.spec)\.[a-z]+$'

MODEL_FILES=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  if grep -nE "$PATTERN|$MODEL_DECL_RE" "$f" 2>/dev/null | grep -vE "$COMMENT_ONLY" | grep -q .; then
    MODEL_FILES="$MODEL_FILES$f"$'\n'
  fi
done <<EOF
$(printf '%s\n' "$ALL_SOURCES" | grep -E "$MODEL_DIR_RE|$MODEL_FILE_RE" | grep -Eiv "$TEST_RE" | grep -Fvx -f <(printf '%s\n' "$ROUTE_FILES"))
EOF
MODEL_FILES="$(printf '%s' "$MODEL_FILES" | sed '/^$/d')"
CTRL_FILES="$(printf '%s\n' "$ALL_SOURCES" | grep -E "$CTRL_DIR_RE|$CTRL_FILE_RE" | grep -Eiv "$TEST_RE")"

mod_name() { local b; b="$(basename "$1")"; printf '%s' "${b%.*}"; }
IMPORT_RE='(^|[^A-Za-z0-9_])(import|from|require|use|using|include)([^A-Za-z0-9_]|$)'
HTTP_IMPORT_RE='(from|import)[[:space:]]+(flask|fastapi|starlette|django\.http|django\.shortcuts|aiohttp\.web)|require\([[:space:]]*['"'"'"`](express|koa|fastify|hapi|@hapi/hapi)['"'"'"`]|from[[:space:]]+['"'"'"`](express|koa|fastify|@nestjs/common)['"'"'"`]|import[[:space:]]+.*['"'"'"`](express|koa|fastify)['"'"'"`]|net/http|gin-gonic|javax\.servlet|org\.springframework\.web'

n_models=0; n_ctrl=0
if [ -n "$MODEL_FILES" ]; then
  n_models="$(printf '%s\n' "$MODEL_FILES" | wc -l | tr -d ' ')"
  while IFS= read -r mf; do
    rel="${mf#"$PROJECT_DIR"/}"; me="$(mod_name "$mf")"
    # (a) model imports another model
    while IFS= read -r of; do
      [ "$of" = "$mf" ] && continue
      on="$(mod_name "$of")"
      grep -nwE "$on" "$mf" 2>/dev/null | grep -vE "$COMMENT_ONLY" | grep -E "$IMPORT_RE" | while IFS= read -r hit; do
        printf '%s\n' "AP-22 ${rel}:${hit%%:*} — model '$me' imports model '$on' (cross-model logic belongs in a Service)"
      done
    done <<EOM
$MODEL_FILES
EOM
    # (b) model imports HTTP/routing code
    grep -nE "$HTTP_IMPORT_RE" "$mf" 2>/dev/null | grep -vE "$COMMENT_ONLY" | while IFS= read -r hit; do
      printf '%s\n' "AP-22 ${rel}:${hit%%:*} — model '$me' imports HTTP/routing code"
    done
  done <<EOF > "$TMP_MODELS"
$MODEL_FILES
EOF
  while IFS= read -r l; do
    [ -n "$l" ] || continue
    rule="${l%% *}"; rest="${l#* }"; add_hit "$rule" "${rest%% — *}" "${rest#* — }"
  done < "$TMP_MODELS"
fi

# Controller implementation = a controller file that is not a package marker and defines at
# least one function. An empty directory, `__init__`/`index` or a file with no function is
# not a controller layer.
FUNC_RE='(^|[[:space:]])(def|function|func|fn)[[:space:]]+[A-Za-z_]|=>|^[[:space:]]*(module\.)?exports(\.[A-Za-z_]+)?[[:space:]]*='
CTRL_IMPL=""
while IFS= read -r cf; do
  [ -n "$cf" ] || continue
  case "$(basename "$cf")" in __init__.*|index.*) continue;; esac
  grep -vE "$COMMENT_ONLY" "$cf" 2>/dev/null | grep -Eq "$FUNC_RE" && CTRL_IMPL="$CTRL_IMPL$cf"$'\n'
done <<EOF
$CTRL_FILES
EOF
CTRL_IMPL="$(printf '%s' "$CTRL_IMPL" | sed '/^$/d')"
[ -n "$CTRL_IMPL" ] && n_ctrl="$(printf '%s\n' "$CTRL_IMPL" | wc -l | tr -d ' ')"

# (c) one controller function that uses >= 2 models (top-level functions only)
CTRL_LANGS_OK=0
if [ -n "$CTRL_FILES" ] && [ -n "$MODEL_FILES" ]; then
  names=""
  while IFS= read -r mf; do names="$names $(mod_name "$mf")"; done <<EOF
$MODEL_FILES
EOF
  while IFS= read -r cf; do
    [ -n "$cf" ] || continue
    case "$cf" in *.py|*.js|*.mjs|*.ts|*.rb|*.php) CTRL_LANGS_OK=1;; *) continue;; esac
    rel="${cf#"$PROJECT_DIR"/}"
    awk -v names="$names" -v rel="$rel" '
      function flush(   k, list, c) {
        if (fn != "") { c = 0; list = ""
          for (k in seen) { c++; list = list (list == "" ? "" : ", ") k }
          if (c >= 2) printf "AP-22 %s:%d — function %s uses %d models (%s): orchestration belongs in a Service\n", rel, fnline, fn, c, list }
        delete seen; fn = "" }
      BEGIN { n = split(names, arr, " ") }
      /^[ \t]?[ \t]?((async|export|public|private|static)[ \t]+)*(def|function|func|fn)[ \t]+[A-Za-z_]/ ||
      /^[ \t]?[ \t]?(export[ \t]+)?(const|let|var)[ \t]+[A-Za-z_0-9]+[ \t]*=[ \t]*(async[ \t]*)?(\(|function|[A-Za-z_]+[ \t]*=>)/ {
        flush(); fn = $0; fnline = FNR
        sub(/^[ \t]*((async|export|public|private|static|const|let|var)[ \t]+)*(def|function|func|fn)?[ \t]*/, "", fn)
        sub(/[^A-Za-z_0-9].*$/, "", fn); next }
      fn != "" { low = tolower($0)
        for (i = 1; i <= n; i++) { m = tolower(arr[i])
          if (m != "" && low ~ ("(^|[^a-z0-9_])" m "[.][a-z_0-9]+[(]")) seen[arr[i]] = 1 } }
      END { flush() }' "$cf" | while IFS= read -r l; do
        rule="${l%% *}"; rest="${l#* }"; printf '%s\n' "$rule ${rest%% — *} — ${rest#* — }"
      done
  done <<EOF > "$TMP_CTRL"
$CTRL_FILES
EOF
  while IFS= read -r l; do
    [ -n "$l" ] || continue
    rule="${l%% *}"; rest="${l#* }"; add_hit "$rule" "${rest%% — *}" "${rest#* — }"
  done < "$TMP_CTRL"
fi

# (d)-(g) MVC completeness: the layers must exist and be connected, not only be clean.
# Route files = files that DECLARE a route (an aggregator that only registers routers is not one).
ROUTE_DECL=""
while IFS= read -r rf; do
  [ -n "$rf" ] && grep -Eq "$DECL_RE" "$rf" 2>/dev/null && ROUTE_DECL="$ROUTE_DECL$rf"$'\n'
done <<EOF
$ROUTE_FILES
EOF
ROUTE_DECL="$(printf '%s' "$ROUTE_DECL" | sed '/^$/d')"

if [ -n "$ROUTE_DECL" ]; then
  # (d) a controller layer with no implementation (missing, empty directory, markers only)
  [ -z "$CTRL_IMPL" ] && add_hit "AP-22" "controllers:0" "routes exist but no controller file defines a function (missing or empty controller layer)"
  # (d) no model file holding persistence calls
  [ -z "$MODEL_FILES" ] && add_hit "AP-22" "models:0" "routes exist but no model file holds persistence calls or declares an ORM entity (set MODEL_DIRS/EXTRA_PATTERN if the stack differs)"

  CTRL_NAMES="controller"
  while IFS= read -r cf; do
    [ -n "$cf" ] && CTRL_NAMES="$CTRL_NAMES|$(mod_name "$cf")"
  done <<EOF
$CTRL_IMPL
EOF
  LOWER_NAMES=""
  while IFS= read -r lf; do
    [ -n "$lf" ] && LOWER_NAMES="$LOWER_NAMES $(mod_name "$lf")"
  done <<EOF
$MODEL_FILES
$(printf '%s\n' "$ALL_SOURCES" | grep -E '/services?/|[Ss]ervice[^/]*\.[a-z]+$' | grep -Eiv "$TEST_RE")
EOF

  ROUTE_IMPORTS=""
  while IFS= read -r rf; do
    [ -n "$rf" ] || continue
    rel="${rf#"$PROJECT_DIR"/}"
    imports="$(grep -nE "$IMPORT_RE" "$rf" 2>/dev/null | grep -vE "$COMMENT_ONLY")"
    ROUTE_IMPORTS="$ROUTE_IMPORTS$imports"$'\n'
    # (e) every route file delegates to a controller
    if [ -n "$CTRL_IMPL" ] && ! printf '%s\n' "$imports" | grep -Eiq "$CTRL_NAMES"; then
      add_hit "AP-22" "${rel}:1" "route file imports no controller (a route only calls a controller)"
    fi
    # (f) a route never reaches a model or service directly
    for n in $LOWER_NAMES; do
      hit="$(printf '%s\n' "$imports" | grep -Fvi 'controller' | grep -wE "$n" | head -n1)"
      [ -n "$hit" ] && add_hit "AP-22" "${rel}:${hit%%:*}" "route imports '$n' directly (Routes → Controllers → Services → Models)"
    done
  done <<EOF
$ROUTE_DECL
EOF

  # (g) a controller no route file imports is dead code
  while IFS= read -r cf; do
    [ -n "$cf" ] || continue
    cn="$(mod_name "$cf")"
    printf '%s\n' "$ROUTE_IMPORTS" | grep -wqE "$cn" || \
      add_hit "AP-22" "${cf#"$PROJECT_DIR"/}:1" "controller '$cn' is imported by no route file (unwired)"
  done <<EOF
$CTRL_IMPL
EOF
fi

# AP-23: source files at the project root other than the entry point or a standalone script (seed).
# Skipped for languages whose idiom puts package code at the root (Go, Java, Kotlin, C#).
ENTRY_RE='^(app|main|server|index|manage|wsgi|asgi|run|start|serve|cli|seed|__main__|__init__|setup|conftest|gulpfile|Rakefile|artisan)\.[a-z]+$'
CONF_RE='^.*\.(config|conf|setup)\.[a-z]+$'
ROOT_TEST_RE='^(test_.*|.*_test|.*\.test|.*\.spec)\.[a-z]+$'
n_root=0
ROOT_SRC="$(printf '%s\n' "$ALL_SOURCES" | awk -v root="$PROJECT_DIR/" 'index($0, root) == 1 { r = substr($0, length(root) + 1); if (r !~ /\//) print $0 }' \
  | grep -E '\.(py|js|mjs|ts|rb|php)$')"
while IFS= read -r rf; do
  [ -n "$rf" ] || continue
  b="$(basename "$rf")"
  case "$b" in .*) continue;; esac
  n_root=$((n_root + 1))
  printf '%s' "$b" | grep -Eq "$ENTRY_RE|$CONF_RE|$ROOT_TEST_RE" && continue
  [ -n "$LAYOUT_ROOT_ALLOW" ] && printf '%s' "$b" | grep -Eq "$LAYOUT_ROOT_ALLOW" && continue
  add_hit "AP-23" "$b:1" "source file at the project root that is not an entry point (group it by role in a directory)"
done <<EOF
$ROOT_SRC
EOF

printf '\n----------------------------------------------------------\n'
printf 'AP-22/AP-23: layers must not leak; supporting modules grouped by role\n'
[ -n "$layout_report" ] && printf '%s' "$layout_report"
if [ "$layout_hits" -eq 0 ]; then
  printf 'LAYOUT PASS: %s model file(s), %s controller file(s), %s root source file(s) checked\n' \
    "$n_models" "$n_ctrl" "$n_root"
else
  printf 'LAYOUT FAIL: %d finding(s). Create/wire controllers or extract a Service (RP-21) / group supporting modules (RP-22), re-run.\n' "$layout_hits"
  LAYOUT_RC=1
fi
[ "$n_models" -eq 0 ] && printf 'note: no model file identified — model checks (AP-22 a/b/c) not verified\n'
[ "$n_models" -gt 0 ] && [ "$n_ctrl" -gt 0 ] && [ "$CTRL_LANGS_OK" -eq 0 ] && \
  printf 'note: controller check (AP-22 c) supports py/js/mjs/ts/rb/php only — not verified for this stack\n'

printf '\n==========================================================\n'
if [ "$ROUTE_RC" -eq 0 ] && [ "$LAYOUT_RC" -eq 0 ]; then
  printf 'PASS\n'
  printf '(%d route file(s) checked)\n' "$scanned"
  printf 'note: aliases, class methods, generated routes and multiline calls may not be detected; confirm manually\n'
  printf '==========================================================\n'
  exit 0
fi
printf 'FAIL\n'
printf '==========================================================\n'
exit 1
