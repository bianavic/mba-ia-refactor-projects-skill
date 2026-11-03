#!/usr/bin/env bash
# api-test.sh — HTTP contract of the Task Manager API (task-manager-api)
#
# Boot (a disposable database is mandatory — the isolation gate refuses tasks.db):
#   T=$(mktemp -d); export DATABASE_URL="sqlite:///$T/tasks.db" SEED_ADMIN_PASSWORD=<pw> SEED_USER_PASSWORD=<pw>
#   python seed.py && python app.py > "$APP_LOG_FILE" 2>&1 &      # port 5000 (APP_PORT)
#   BASE_URL=http://localhost:5000 ./api-test.sh
# Variables read: BASE_URL, DATABASE_URL (the same as the app), SEED_ADMIN_PASSWORD, SEED_USER_PASSWORD,
# APP_LOG_FILE (optional, for T7). Re-runnable: unique values use $RUN; ids are discovered at runtime.
#
# Inventory (method path — access — sections):
#   GET    /                          — public                                          — T1
#   GET    /health                    — public                                          — T0 T1
#   POST   /login                     — public                                          — T0 T1 T2 T6 T7
#   POST   /users                     — public (role/active: admin only)                — T1 T2 T3 T4 T7
#   GET    /users                     — admin                                           — T1 T3 T4 T7
#   GET    /users/<int:user_id>       — owner-or-admin (owner: the user id itself)      — T1 T2 T3 T7
#   PUT    /users/<int:user_id>       — owner-or-admin (owner: the user id itself)      — T1 T2 T3 T7
#   DELETE /users/<int:user_id>       — owner-or-admin (owner: the user id itself)      — T3 T8
#   GET    /users/<int:user_id>/tasks — owner-or-admin (owner: the user id itself)      — T1 T3 T5
#   GET    /tasks                     — authenticated                                   — T1 T3 T4
#   GET    /tasks/<int:task_id>       — authenticated                                   — T1 T2 T3
#   POST   /tasks                     — authenticated                                   — T1 T2 T3 T4 T6
#   PUT    /tasks/<int:task_id>       — owner-or-admin (owner: tasks.user_id; unassigned → admin only) — T1 T2 T3
#   DELETE /tasks/<int:task_id>       — owner-or-admin (owner: tasks.user_id)           — T1 T3 T4
#   GET    /tasks/search              — authenticated                                   — T1 T2 T5
#   GET    /tasks/stats               — authenticated                                   — T1 T3
#   GET    /reports/summary           — admin                                           — T1 T3
#   GET    /reports/user/<int:user_id>— owner-or-admin (owner: the user id itself)      — T1 T3 T5 T7
#   GET    /categories                — authenticated                                   — T1 T3 T4
#   POST   /categories                — admin                                           — T1 T2 T3
#   PUT    /categories/<int:cat_id>   — admin                                           — T1 T2 T3
#   DELETE /categories/<int:cat_id>   — admin                                           — T1 T2 T3
set -uo pipefail

BASE="${BASE_URL:-http://localhost:5000}"
DB_URL="${DATABASE_URL:-sqlite:///tasks.db}"
DB="${DB_URL#sqlite:///}"
RUN="$$$(date +%s)"
PASS=0; FAIL=0; SKIP=0
EXERCISED="$(mktemp)"
INVENTORY=22

echo "=================================================="
echo "api-test.sh — task-manager-api"
echo "Base URL: $BASE"
echo "Start:    $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

# ---------- helpers ----------
redact() {
  sed -E 's/[A-Za-z0-9._%+*-]+@[A-Za-z0-9.-]+/<REDACTED>/g; s/("token": *")[^"]*"/\1<REDACTED>"/g'
}

json() {  # json key [key|index...] — reads JSON from stdin
  python3 -c '
import sys, json
try:
    v = json.load(sys.stdin)
    for k in sys.argv[1:]:
        v = v[int(k)] if isinstance(v, list) else v[k]
except Exception:
    print("<missing>"); sys.exit(0)
print(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
' "$@"
}

pyq() {  # pyq "<python expression over d>" — evaluates over the JSON body on stdin; the expression is always a literal written in this script, never input
  python3 -c '
import sys, json
d = json.load(sys.stdin)
j = lambda *v: "|".join(str(x) for x in v)
print(eval(sys.argv[1]))
' "$1" 2>/dev/null || echo "<error>"
}

mark() { echo "$1" >> "$EXERCISED"; }

req() {  # req <curl args...> → STATUS, BODY
  local out
  out="$(curl -sS -m 15 -w $'\n%{http_code}' "$@" 2>/dev/null)"
  STATUS="${out##*$'\n'}"
  BODY="${out%$'\n'*}"
}

ok()   { PASS=$((PASS+1)); echo "  PASS $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; echo "       expected: $2"; echo "       actual:   $(printf '%s' "$3" | head -c 300 | redact)"; }
skip() { SKIP=$((SKIP+1)); echo "  SKIP $1 — $2"; }

check() {  # check <endpoint> <status> <desc> <curl args...>
  local ep="$1" exp="$2" desc="$3"; shift 3
  mark "$ep"
  req "$@"
  if [ "$STATUS" = "$exp" ]; then
    ok "[$exp] $ep — $desc :: $(printf '%s' "$BODY" | tr -d '\n' | head -c 100 | redact)"
  else
    bad "$ep — $desc" "HTTP $exp" "HTTP $STATUS $BODY"
  fi
}

check_equal() {  # check_equal <expected> <actual> <desc>
  if [ "$1" = "$2" ]; then ok "$3"; else bad "$3" "$1" "$2"; fi
}

deny() {  # deny <regex> <desc> — on the BODY of the last request; never prints the value
  if printf '%s' "$BODY" | grep -Eq "$1"; then
    bad "$2" "absent: /$1/" "(present — value not printed)"
  else
    ok "$2"
  fi
}

check_db() {  # check_db <expected> <desc> <sql>
  if ! command -v sqlite3 >/dev/null 2>&1; then skip "$2" "sqlite3 unavailable"; return; fi
  local got; got="$(sqlite3 "$DB" "$3" 2>&1)"
  check_equal "$1" "$got" "DB: $2"
}

H_JSON=(-H "Content-Type: application/json")
auth() { echo "Authorization: Bearer $1"; }

# =================================================================
echo; echo "== T0. Preflight"
req "$BASE/health"
if [ "$STATUS" != "200" ]; then
  echo "Application not answering at $BASE (HTTP '$STATUS'). Boot with: DATABASE_URL=sqlite:///<tmp>/tasks.db python app.py"
  exit 2
fi
mark "GET /health"; ok "[200] GET /health — application up"

# Isolation gate: only a database file in a temporary directory
case "$DB" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*|"${TMPDIR:-/nonexistent}"*) DBCLASS="temp-file" ;;
  *) echo "DB target: not isolated — DATABASE_URL is not a file in a temporary directory"; exit 2 ;;
esac
[ -f "$DB" ] || { echo "DB target: not isolated — DATABASE_URL file does not exist (does the app use another database?)"; exit 2; }
if [ -z "${SEED_ADMIN_PASSWORD:-}" ] || [ -z "${SEED_USER_PASSWORD:-}" ]; then
  echo "SEED_ADMIN_PASSWORD and SEED_USER_PASSWORD are required (the same used by seed.py)"; exit 2
fi

login_token() {  # login_token <email> <password> → TOKEN, LOGIN_ID
  req -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"$1\",\"password\":\"$2\"}"
  TOKEN="$(printf '%s' "$BODY" | json token)"
  LOGIN_ID="$(printf '%s' "$BODY" | json user id)"
}
login_token "joao@email.com" "$SEED_ADMIN_PASSWORD"; TA="$TOKEN"; ADMIN_ID="$LOGIN_ID"
mark "POST /login"; check_equal "200" "$STATUS" "POST /login — seeded admin logs in"
login_token "maria@email.com" "$SEED_USER_PASSWORD"; TM="$TOKEN"; MARIA_ID="$LOGIN_ID"
login_token "pedro@email.com" "$SEED_USER_PASSWORD"; TP="$TOKEN"; PEDRO_ID="$LOGIN_ID"
AH=(-H "$(auth "$TA")"); MH=(-H "$(auth "$TM")"); PH=(-H "$(auth "$TP")")

# the app must be using this file: API category count == DB category count (read-only)
req "${AH[@]}" "$BASE/categories"
api_count="$(printf '%s' "$BODY" | pyq 'len(d)')"
db_count="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM categories' 2>/dev/null)"
if [ "$api_count" != "$db_count" ]; then
  echo "DB target: not isolated — the app does not use the given DATABASE_URL (api=$api_count db=$db_count)"; exit 2
fi
echo "DB target: $DBCLASS"

# =================================================================
echo; echo "== T1. Happy path"
check "GET /" 200 "index" "$BASE/"
check_equal "Task Manager API" "$(printf '%s' "$BODY" | json message)" "GET / message"
check "GET /health" 200 "health" "$BASE/health"
check_equal "ok" "$(printf '%s' "$BODY" | json status)" "GET /health status"

check "POST /login" 200 "login returns own data and a token" -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"maria@email.com\",\"password\":\"$SEED_USER_PASSWORD\"}"
check_equal "maria@email.com" "$(printf '%s' "$BODY" | json user email)" "login shows the subject's own full email"
check_equal "True" "$(printf '%s' "$BODY" | pyq 'len(d["token"]) > 20 and not d["token"].startswith("fake-jwt-token")')" "token is signed, not fake-jwt-token-<id>"

DB_TASKS="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM tasks')"
check "GET /tasks" 200 "list all tasks" "${MH[@]}" "$BASE/tasks"
check_equal "$DB_TASKS" "$(printf '%s' "$BODY" | pyq 'len(d)')" "GET /tasks returns every task (no default page)"
check_equal "True" "$(printf '%s' "$BODY" | pyq 'all("user_name" in t and "category_name" in t and "overdue" in t for t in d)')" "GET /tasks rows carry user_name, category_name, overdue"
OVERDUE_ID="$(sqlite3 "$DB" "SELECT id FROM tasks WHERE title='Implementar autenticação JWT'")"
check "GET /tasks/<int:task_id>" 200 "seeded overdue task" "${MH[@]}" "$BASE/tasks/$OVERDUE_ID"
check_equal "True|Implementar autenticação JWT" "$(printf '%s' "$BODY" | pyq 'j(d["overdue"], d["title"])')" "overdue computed by Task.is_overdue"
check "GET /tasks/search" 200 "search by text" "${MH[@]}" "$BASE/tasks/search?q=pagina"
check_equal "Adicionar paginação na API" "$(printf '%s' "$BODY" | json 0 title)" "search finds the matching task"
check "GET /tasks/stats" 200 "stats" "${MH[@]}" "$BASE/tasks/stats"
check_equal "$DB_TASKS" "$(printf '%s' "$BODY" | json total)" "stats total equals DB"
check_equal "$(sqlite3 "$DB" "SELECT COUNT(*) FROM tasks WHERE status='done'")" "$(printf '%s' "$BODY" | json done)" "stats done equals DB"

check "POST /tasks" 201 "maria creates a task assigned to herself" -X POST "${MH[@]}" "${H_JSON[@]}" \
  -d "{\"title\":\"Task $RUN\",\"priority\":2,\"user_id\":$MARIA_ID,\"category_id\":1,\"due_date\":\"2030-01-15\",\"tags\":[\"a\",\"b\"]}" "$BASE/tasks"
MT="$(printf '%s' "$BODY" | json id)"
check_equal "Task $RUN|2|['a', 'b']|2030-01-15 00:00:00" "$(printf '%s' "$BODY" | pyq 'j(d["title"], d["priority"], d["tags"], d["due_date"])')" "created task values"
check "PUT /tasks/<int:task_id>" 200 "owner updates status" -X PUT "${MH[@]}" "${H_JSON[@]}" -d '{"status":"in_progress","due_date":null}' "$BASE/tasks/$MT"
check_equal "in_progress|None" "$(printf '%s' "$BODY" | pyq 'j(d["status"], d["due_date"])')" "update applied"

check "GET /users" 200 "admin lists users" "${AH[@]}" "$BASE/users"
check_equal "$(sqlite3 "$DB" 'SELECT COUNT(*) FROM users')" "$(printf '%s' "$BODY" | pyq 'len(d)')" "GET /users returns every user"
check_equal "$(sqlite3 "$DB" "SELECT COUNT(*) FROM tasks WHERE user_id=$MARIA_ID")" "$(printf '%s' "$BODY" | pyq "[u['task_count'] for u in d if u['id']==$MARIA_ID][0]")" "task_count for maria equals DB"
check "GET /users/<int:user_id>" 200 "maria reads herself" "${MH[@]}" "$BASE/users/$MARIA_ID"
check_equal "maria@email.com|$(sqlite3 "$DB" "SELECT COUNT(*) FROM tasks WHERE user_id=$MARIA_ID")" "$(printf '%s' "$BODY" | pyq 'j(d["email"], len(d["tasks"]))')" "own record with full email and her tasks"

check "POST /users" 201 "anonymous signup" -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"Novo $RUN\",\"email\":\"new$RUN@ex.com\",\"password\":\"pw-$RUN\"}"
NU="$(printf '%s' "$BODY" | json id)"
check_equal "user|new$RUN@ex.com" "$(printf '%s' "$BODY" | pyq 'j(d["role"], d["email"])')" "signup gets role user and sees own email"
login_token "new$RUN@ex.com" "pw-$RUN"; TN="$TOKEN"; NH=(-H "$(auth "$TN")")
check "PUT /users/<int:user_id>" 200 "user renames himself" -X PUT "${NH[@]}" "${H_JSON[@]}" -d "{\"name\":\"Renomeado $RUN\"}" "$BASE/users/$NU"
check_equal "Renomeado $RUN" "$(printf '%s' "$BODY" | json name)" "rename applied"
check "GET /users/<int:user_id>/tasks" 200 "maria's tasks" "${MH[@]}" "$BASE/users/$MARIA_ID/tasks"
check_equal "True" "$(printf '%s' "$BODY" | pyq "any(t['id']==$MT and 'overdue' in t and 'user_id' not in t for t in d)")" "user tasks shape (with overdue, without user_id)"

check "GET /reports/summary" 200 "admin summary" "${AH[@]}" "$BASE/reports/summary"
DB_TASKS="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM tasks')"
check_equal "$DB_TASKS|$(sqlite3 "$DB" 'SELECT COUNT(*) FROM users')" "$(printf '%s' "$BODY" | pyq 'j(d["overview"]["total_tasks"], d["overview"]["total_users"])')" "summary overview equals DB"
check_equal "$(sqlite3 "$DB" "SELECT COUNT(*) FROM tasks WHERE priority=1")" "$(printf '%s' "$BODY" | pyq 'd["tasks_by_priority"]["critical"]')" "summary priority 1 → critical"
check "GET /reports/user/<int:user_id>" 200 "maria's own report" "${MH[@]}" "$BASE/reports/user/$MARIA_ID"
check_equal "$(sqlite3 "$DB" "SELECT COUNT(*) FROM tasks WHERE user_id=$MARIA_ID")|maria@email.com" "$(printf '%s' "$BODY" | pyq 'j(d["statistics"]["total_tasks"], d["user"]["email"])')" "user report values"

check "GET /categories" 200 "list categories" "${MH[@]}" "$BASE/categories"
check_equal "$(sqlite3 "$DB" 'SELECT COUNT(*) FROM tasks WHERE category_id=1')" "$(printf '%s' "$BODY" | pyq '[c["task_count"] for c in d if c["id"]==1][0]')" "category 1 task_count equals DB"
check "POST /categories" 201 "admin creates category" -X POST "${AH[@]}" "${H_JSON[@]}" -d "{\"name\":\"Cat $RUN\",\"color\":\"#123abc\"}" "$BASE/categories"
CT="$(printf '%s' "$BODY" | json id)"
check_equal "Cat $RUN|#123abc|" "$(printf '%s' "$BODY" | pyq 'j(d["name"], d["color"], d["description"])')" "category values (description defaults to '')"
check "PUT /categories/<int:cat_id>" 200 "admin updates category" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"description":"Nova"}' "$BASE/categories/$CT"
check_equal "Nova" "$(printf '%s' "$BODY" | json description)" "category update applied"

# =================================================================
echo; echo "== T2. Sad paths"
check "POST /tasks" 400 "missing title" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"priority":2}' "$BASE/tasks"
check_equal "Título é obrigatório" "$(printf '%s' "$BODY" | json error)" "error message kept"
check "POST /tasks" 400 "priority as text (was 500)" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","priority":"high"}' "$BASE/tasks"
check "POST /tasks" 400 "numeric title (was 500)" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":12345}' "$BASE/tasks"
check "POST /tasks" 400 "invalid status" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","status":"x"}' "$BASE/tasks"
check_equal "Status inválido" "$(printf '%s' "$BODY" | json error)" "status message kept"
check "POST /tasks" 404 "unknown user_id" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","user_id":999999}' "$BASE/tasks"
check "POST /tasks" 404 "unknown category_id" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","category_id":999999}' "$BASE/tasks"
check "POST /tasks" 400 "bad date" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","due_date":"15/01/2030"}' "$BASE/tasks"
check "POST /tasks" 400 "malformed JSON" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":' "$BASE/tasks"
check_equal "Dados inválidos" "$(printf '%s' "$BODY" | json error)" "malformed JSON answers JSON error"
check "PUT /tasks/<int:task_id>" 400 "title null (was 500)" -X PUT "${MH[@]}" "${H_JSON[@]}" -d '{"title":null}' "$BASE/tasks/$MT"
check "PUT /tasks/<int:task_id>" 400 "priority as text (was 500)" -X PUT "${MH[@]}" "${H_JSON[@]}" -d '{"priority":"x"}' "$BASE/tasks/$MT"
check "PUT /tasks/<int:task_id>" 404 "unknown task (admin)" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"status":"done"}' "$BASE/tasks/999999"
check "GET /tasks/<int:task_id>" 404 "unknown task" "${MH[@]}" "$BASE/tasks/999999"
check_equal "Task não encontrada" "$(printf '%s' "$BODY" | json error)" "not-found message kept"
check "GET /tasks/search" 400 "priority not numeric (was 500)" "${MH[@]}" "$BASE/tasks/search?priority=abc"
check "GET /tasks/search" 400 "user_id not numeric (was 500)" "${MH[@]}" "$BASE/tasks/search?user_id=abc"
check "POST /users" 409 "duplicate email" -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"Dup\",\"email\":\"new$RUN@ex.com\",\"password\":\"pw-$RUN\"}"
check "POST /users" 400 "invalid email" -X POST "${H_JSON[@]}" "$BASE/users" -d '{"name":"X","email":"nope","password":"abcdef"}'
check "POST /users" 400 "short password" -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"X\",\"email\":\"s$RUN@ex.com\",\"password\":\"abc\"}"
check "POST /users" 400 "invalid role" -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"X\",\"email\":\"r$RUN@ex.com\",\"password\":\"abcdef\",\"role\":\"root\"}"
check "POST /users" 400 "email not a string (was 500)" -X POST "${H_JSON[@]}" "$BASE/users" -d '{"name":"X","email":123,"password":"abcdef"}'
check "PUT /users/<int:user_id>" 400 "password null (was 500)" -X PUT "${NH[@]}" "${H_JSON[@]}" -d '{"password":null}' "$BASE/users/$NU"
check "PUT /users/<int:user_id>" 400 "empty name" -X PUT "${NH[@]}" "${H_JSON[@]}" -d '{"name":""}' "$BASE/users/$NU"
check "PUT /users/<int:user_id>" 400 "active not boolean (admin)" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"active":"yes"}' "$BASE/users/$NU"
check "PUT /users/<int:user_id>" 409 "email taken" -X PUT "${NH[@]}" "${H_JSON[@]}" -d '{"email":"maria@email.com"}' "$BASE/users/$NU"
check "GET /users/<int:user_id>" 404 "unknown user (admin)" "${AH[@]}" "$BASE/users/999999"
check "POST /login" 401 "wrong password" -X POST "$BASE/login" "${H_JSON[@]}" -d '{"email":"maria@email.com","password":"wrong"}'
check_equal "Credenciais inválidas" "$(printf '%s' "$BODY" | json error)" "login error message kept"
check "POST /login" 400 "missing password" -X POST "$BASE/login" "${H_JSON[@]}" -d '{"email":"maria@email.com"}'
check "POST /categories" 400 "invalid color" -X POST "${AH[@]}" "${H_JSON[@]}" -d '{"name":"C","color":"#12345678901"}' "$BASE/categories"
check "POST /categories" 400 "missing name" -X POST "${AH[@]}" "${H_JSON[@]}" -d '{"color":"#123456"}' "$BASE/categories"
check "PUT /categories/<int:cat_id>" 400 "no body (was 500)" -X PUT "${AH[@]}" "$BASE/categories/$CT"
check "PUT /categories/<int:cat_id>" 404 "unknown category" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"name":"x"}' "$BASE/categories/999999"
check "DELETE /categories/<int:cat_id>" 404 "unknown category" -X DELETE "${AH[@]}" "$BASE/categories/999999"

# =================================================================
echo; echo "== T3. Permission boundaries"
for ep in "GET /tasks|/tasks" "GET /tasks/<int:task_id>|/tasks/$MT" "GET /tasks/search|/tasks/search" "GET /tasks/stats|/tasks/stats" \
          "GET /users|/users" "GET /users/<int:user_id>|/users/$MARIA_ID" "GET /users/<int:user_id>/tasks|/users/$MARIA_ID/tasks" \
          "GET /reports/summary|/reports/summary" "GET /reports/user/<int:user_id>|/reports/user/$MARIA_ID" "GET /categories|/categories"; do
  check "${ep%%|*}" 401 "anonymous" "$BASE${ep#*|}"
done
check "POST /tasks" 401 "anonymous" -X POST "${H_JSON[@]}" -d '{"title":"abcd"}' "$BASE/tasks"
check "PUT /tasks/<int:task_id>" 401 "anonymous" -X PUT "${H_JSON[@]}" -d '{"status":"done"}' "$BASE/tasks/$MT"
check "DELETE /tasks/<int:task_id>" 401 "anonymous" -X DELETE "$BASE/tasks/$MT"
check "PUT /users/<int:user_id>" 401 "anonymous" -X PUT "${H_JSON[@]}" -d '{"name":"x"}' "$BASE/users/$MARIA_ID"
check "DELETE /users/<int:user_id>" 401 "anonymous" -X DELETE "$BASE/users/$MARIA_ID"
check "POST /categories" 401 "anonymous" -X POST "${H_JSON[@]}" -d '{"name":"x"}' "$BASE/categories"
check "PUT /categories/<int:cat_id>" 401 "anonymous" -X PUT "${H_JSON[@]}" -d '{"name":"x"}' "$BASE/categories/$CT"
check "DELETE /categories/<int:cat_id>" 401 "anonymous" -X DELETE "$BASE/categories/$CT"
check "GET /tasks" 401 "forged old-style token" -H "Authorization: Bearer fake-jwt-token-$ADMIN_ID" "$BASE/tasks"
check "GET /tasks" 401 "tampered token" -H "Authorization: Bearer ${TA}x" "$BASE/tasks"
# admin-only routes: regular user and manager → 403
check "GET /users" 403 "regular user" "${MH[@]}" "$BASE/users"
check "GET /users" 403 "manager is not admin" "${PH[@]}" "$BASE/users"
check "GET /reports/summary" 403 "regular user" "${MH[@]}" "$BASE/reports/summary"
check "POST /categories" 403 "regular user" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"name":"x"}' "$BASE/categories"
check "PUT /categories/<int:cat_id>" 403 "regular user" -X PUT "${MH[@]}" "${H_JSON[@]}" -d '{"name":"x"}' "$BASE/categories/$CT"
check "DELETE /categories/<int:cat_id>" 403 "regular user" -X DELETE "${MH[@]}" "$BASE/categories/$CT"
# owner-or-admin on users: owner, another user, admin
check "GET /users/<int:user_id>" 403 "another user" "${PH[@]}" "$BASE/users/$MARIA_ID"
check "GET /users/<int:user_id>" 200 "admin" "${AH[@]}" "$BASE/users/$MARIA_ID"
check "PUT /users/<int:user_id>" 403 "another user" -X PUT "${PH[@]}" "${H_JSON[@]}" -d '{"name":"hack"}' "$BASE/users/$MARIA_ID"
check "PUT /users/<int:user_id>" 200 "admin" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"name":"Maria Santos"}' "$BASE/users/$MARIA_ID"
check "DELETE /users/<int:user_id>" 403 "another user" -X DELETE "${PH[@]}" "$BASE/users/$MARIA_ID"
check "GET /users/<int:user_id>/tasks" 403 "another user" "${PH[@]}" "$BASE/users/$MARIA_ID/tasks"
check "GET /users/<int:user_id>/tasks" 200 "admin" "${AH[@]}" "$BASE/users/$MARIA_ID/tasks"
check "GET /reports/user/<int:user_id>" 403 "another user" "${PH[@]}" "$BASE/reports/user/$MARIA_ID"
check "GET /reports/user/<int:user_id>" 200 "admin" "${AH[@]}" "$BASE/reports/user/$MARIA_ID"
# owner-or-admin on tasks: the owner is tasks.user_id; the task id differs from the owner id
check_equal "True" "$( [ "$MT" != "$MARIA_ID" ] && echo True || echo False )" "task id differs from its owner's id"
check "PUT /tasks/<int:task_id>" 403 "another user" -X PUT "${PH[@]}" "${H_JSON[@]}" -d '{"status":"done"}' "$BASE/tasks/$MT"
check "DELETE /tasks/<int:task_id>" 403 "another user" -X DELETE "${PH[@]}" "$BASE/tasks/$MT"
check "PUT /tasks/<int:task_id>" 200 "admin" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"priority":3}' "$BASE/tasks/$MT"
check "PUT /tasks/<int:task_id>" 200 "owner" -X PUT "${MH[@]}" "${H_JSON[@]}" -d '{"priority":4}' "$BASE/tasks/$MT"
check "POST /tasks" 201 "admin creates an unassigned task" -X POST "${AH[@]}" "${H_JSON[@]}" -d "{\"title\":\"Sem dono $RUN\"}" "$BASE/tasks"
UT="$(printf '%s' "$BODY" | json id)"
check "PUT /tasks/<int:task_id>" 403 "unassigned task: regular user" -X PUT "${MH[@]}" "${H_JSON[@]}" -d '{"status":"done"}' "$BASE/tasks/$UT"
check "PUT /tasks/<int:task_id>" 200 "unassigned task: admin" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"status":"done"}' "$BASE/tasks/$UT"
check "GET /tasks/stats" 200 "manager (authenticated)" "${PH[@]}" "$BASE/tasks/stats"
# privileged fields (AP-17 re-check)
check "POST /users" 403 "anonymous signup asking for admin" -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"Esc\",\"email\":\"esc$RUN@ex.com\",\"password\":\"abcdef\",\"role\":\"admin\"}"
check_db "0" "escalation attempt created no row" "SELECT COUNT(*) FROM users WHERE email='esc$RUN@ex.com'"
check "PUT /users/<int:user_id>" 403 "user promotes himself" -X PUT "${NH[@]}" "${H_JSON[@]}" -d '{"role":"admin"}' "$BASE/users/$NU"
check "PUT /users/<int:user_id>" 403 "user changes his active flag" -X PUT "${NH[@]}" "${H_JSON[@]}" -d '{"active":true}' "$BASE/users/$NU"
check_db "user" "role unchanged after the attempt" "SELECT role FROM users WHERE id=$NU"
check "POST /users" 201 "admin creates a manager" -X POST "${AH[@]}" "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"Ger $RUN\",\"email\":\"mgr$RUN@ex.com\",\"password\":\"abcdef\",\"role\":\"manager\"}"
check_equal "manager" "$(printf '%s' "$BODY" | json role)" "admin may assign a role"
# inactive account: admin deactivates, login and token are refused
check "PUT /users/<int:user_id>" 200 "admin deactivates a user" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"active":false}' "$BASE/users/$NU"
check "GET /tasks" 403 "inactive user's token" "${NH[@]}" "$BASE/tasks"
check "POST /login" 403 "inactive user login" -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"new$RUN@ex.com\",\"password\":\"pw-$RUN\"}"
check "PUT /users/<int:user_id>" 200 "admin reactivates" -X PUT "${AH[@]}" "${H_JSON[@]}" -d '{"active":true}' "$BASE/users/$NU"
# CORS: flask-cors 6 does not grant private-network access
req -X OPTIONS -D - -o /dev/null -H "Origin: https://evil.example" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Private-Network: true" "$BASE/tasks"
deny "Access-Control-Allow-Private-Network: *true" "CORS preflight does not grant private-network access (CVE-2024-6221)"

# =================================================================
echo; echo "== T4. Edge cases"
T199="$(python3 -c 'print("a"*200)')"; T201="$(python3 -c 'print("a"*201)')"
check "POST /tasks" 400 "title length 2 (min-1)" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"ab"}' "$BASE/tasks"
check "POST /tasks" 201 "title length 3 (min)" -X POST "${MH[@]}" "${H_JSON[@]}" -d "{\"title\":\"abc\",\"user_id\":$MARIA_ID}" "$BASE/tasks"
E1="$(printf '%s' "$BODY" | json id)"
check "POST /tasks" 201 "title length 200 (max)" -X POST "${MH[@]}" "${H_JSON[@]}" -d "{\"title\":\"$T199\",\"user_id\":$MARIA_ID}" "$BASE/tasks"
E2="$(printf '%s' "$BODY" | json id)"
check "POST /tasks" 400 "title length 201 (max+1)" -X POST "${MH[@]}" "${H_JSON[@]}" -d "{\"title\":\"$T201\"}" "$BASE/tasks"
check "POST /tasks" 400 "priority 0" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","priority":0}' "$BASE/tasks"
check "POST /tasks" 400 "priority 6" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","priority":6}' "$BASE/tasks"
check "POST /tasks" 400 "priority boolean" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","priority":true}' "$BASE/tasks"
check "POST /tasks" 400 "tags with a number" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"abcd","tags":["a",1]}' "$BASE/tasks"
check "POST /tasks" 201 "unicode title" -X POST "${MH[@]}" "${H_JSON[@]}" -d "{\"title\":\"Ação çãõ ✓\",\"user_id\":$MARIA_ID}" "$BASE/tasks"
E3="$(printf '%s' "$BODY" | json id)"
check_equal "Ação çãõ ✓" "$(printf '%s' "$BODY" | json title)" "unicode stored as sent"
check "GET /tasks" 400 "page=0" "${MH[@]}" "$BASE/tasks?page=0"
check "GET /tasks" 400 "per_page=abc" "${MH[@]}" "$BASE/tasks?per_page=abc"
check "GET /tasks" 400 "per_page=101" "${MH[@]}" "$BASE/tasks?per_page=101"
check "GET /tasks" 200 "page 1 of 2" "${MH[@]}" "$BASE/tasks?page=1&per_page=2"
check_equal "2" "$(printf '%s' "$BODY" | pyq 'len(d)')" "per_page limits the list"
check "GET /users" 200 "page of users" "${AH[@]}" "$BASE/users?page=1&per_page=1"
check_equal "1" "$(printf '%s' "$BODY" | pyq 'len(d)')" "users per_page=1"
check "GET /categories" 200 "page beyond the end" "${MH[@]}" "$BASE/categories?page=999&per_page=10"
check_equal "[]" "$(printf '%s' "$BODY" | json)" "page beyond the end is empty"
check "POST /users" 409 "duplicate POST (same email again)" -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"Novo\",\"email\":\"new$RUN@ex.com\",\"password\":\"pw-$RUN\"}"
check "DELETE /tasks/<int:task_id>" 200 "owner deletes" -X DELETE "${MH[@]}" "$BASE/tasks/$E1"
check "DELETE /tasks/<int:task_id>" 404 "delete twice" -X DELETE "${MH[@]}" "$BASE/tasks/$E1"
check "DELETE /tasks/<int:task_id>" 200 "owner deletes (max title)" -X DELETE "${MH[@]}" "$BASE/tasks/$E2"
check "DELETE /tasks/<int:task_id>" 200 "owner deletes (unicode)" -X DELETE "${MH[@]}" "$BASE/tasks/$E3"

# =================================================================
echo; echo "== T5. Empty states"
check "GET /tasks/search" 200 "filter matching nothing" "${MH[@]}" "$BASE/tasks/search?q=zz-nothing-$RUN"
check_equal "[]" "$(printf '%s' "$BODY" | json)" "empty search is []"
check "GET /users/<int:user_id>/tasks" 200 "user with no tasks" "${NH[@]}" "$BASE/users/$NU/tasks"
check_equal "[]" "$(printf '%s' "$BODY" | json)" "no tasks is []"
check "GET /reports/user/<int:user_id>" 200 "report over no data" "${NH[@]}" "$BASE/reports/user/$NU"
check_equal "0|0|0" "$(printf '%s' "$BODY" | pyq 'j(d["statistics"]["total_tasks"], d["statistics"]["overdue"], d["statistics"]["completion_rate"])')" "zeros, not null"

# =================================================================
echo; echo "== T6. Persistence and integrity"
check "GET /tasks/<int:task_id>" 200 "re-read the updated task" "${MH[@]}" "$BASE/tasks/$MT"
check_equal "in_progress|4" "$(printf '%s' "$BODY" | pyq 'j(d["status"], d["priority"])')" "updates persisted"
check_db "in_progress|4|a,b" "task row in the database" "SELECT status, priority, tags FROM tasks WHERE id=$MT"
BEFORE="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM tasks')"
check "POST /tasks" 404 "failing create (unknown user)" -X POST "${MH[@]}" "${H_JSON[@]}" -d '{"title":"atomic","user_id":999999}' "$BASE/tasks"
check_db "$BEFORE" "failed create left no partial row" "SELECT COUNT(*) FROM tasks"
check_db "1" "invalid color never stored" "SELECT COUNT(*) = 0 FROM categories WHERE length(color) <> 7"
check_db "0" "no password stored as unsalted MD5 or plaintext" "SELECT COUNT(*) FROM users WHERE password NOT LIKE 'scrypt:%' AND password NOT LIKE 'pbkdf2:%'"
if command -v sqlite3 >/dev/null 2>&1; then
  if sqlite3 "$DB" "INSERT INTO users (name, email, password, role, active) VALUES ('Dup', 'maria@email.com', 'x', 'user', 1)" 2>/dev/null; then
    bad "DB: unique email enforced by the database" "constraint error" "row inserted"
  else
    ok "DB: unique email enforced by the database"
  fi
  # legacy MD5 hash is accepted once and upgraded on login
  LEGACY_MD5="$(printf '%s' "legacy-$RUN" | python3 -c 'import sys,hashlib;print(hashlib.md5(sys.stdin.read().encode()).hexdigest())')"
  sqlite3 "$DB" "UPDATE users SET password='$LEGACY_MD5' WHERE id=$NU"
  check "POST /login" 200 "login with a legacy MD5 hash" -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"new$RUN@ex.com\",\"password\":\"legacy-$RUN\"}"
  check_db "1" "legacy hash replaced by a salted hash" "SELECT password LIKE 'scrypt:%' OR password LIKE 'pbkdf2:%' FROM users WHERE id=$NU"
  TN="$(printf '%s' "$BODY" | json token)"; NH=(-H "$(auth "$TN")")
else
  skip "DB integrity checks" "sqlite3 unavailable"
fi
check_db "0" "no orphan task (user_id pointing at nothing)" "SELECT COUNT(*) FROM tasks WHERE user_id IS NOT NULL AND user_id NOT IN (SELECT id FROM users)"

# =================================================================
echo; echo "== T7. Privacy"
check "POST /login" 200 "login" -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"maria@email.com\",\"password\":\"$SEED_USER_PASSWORD\"}"
deny '"password"' "login does not return the password hash"
check "GET /users" 200 "admin list" "${AH[@]}" "$BASE/users"
deny '"password"' "GET /users has no password field"
deny 'maria@email\.com' "GET /users masks another user's email for the admin"
check_equal "joao@email.com" "$(printf '%s' "$BODY" | pyq "[u['email'] for u in d if u['id']==$ADMIN_ID][0]")" "admin sees his own full email"
check "GET /users/<int:user_id>" 200 "admin reads maria" "${AH[@]}" "$BASE/users/$MARIA_ID"
deny '"password"' "GET /users/<id> has no password field"
check_equal "m***@email.com" "$(printf '%s' "$BODY" | json email)" "maria's email masked for the admin"
check "PUT /users/<int:user_id>" 200 "update response" -X PUT "${NH[@]}" "${H_JSON[@]}" -d "{\"name\":\"Priv $RUN\"}" "$BASE/users/$NU"
deny '"password"' "PUT /users/<id> has no password field"
check "POST /users" 201 "signup response" -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"Priv $RUN\",\"email\":\"priv$RUN@ex.com\",\"password\":\"abcdef\"}"
deny '"password"' "POST /users has no password field"
check "GET /reports/user/<int:user_id>" 200 "admin reads maria's report" "${AH[@]}" "$BASE/reports/user/$MARIA_ID"
deny 'maria@email\.com' "user report masks the email for a non-subject"
if [ -n "${APP_LOG_FILE:-}" ] && [ -f "$APP_LOG_FILE" ]; then
  if grep -q "priv$RUN@ex.com\|new$RUN@ex.com\|Priv $RUN\|Novo $RUN" "$APP_LOG_FILE"; then
    bad "application log has no email or name of the users created" "absent" "(present — value not printed)"
  else
    ok "application log has no email or name of the users created"
  fi
else
  skip "application log has no personal data" "APP_LOG_FILE not provided"
fi

# =================================================================
echo; echo "== T8. Destructive operations"
check "DELETE /categories/<int:cat_id>" 200 "admin deletes category" -X DELETE "${AH[@]}" "$BASE/categories/$CT"
check "DELETE /categories/<int:cat_id>" 404 "delete twice" -X DELETE "${AH[@]}" "$BASE/categories/$CT"
check "DELETE /tasks/<int:task_id>" 200 "admin deletes the unassigned task" -X DELETE "${AH[@]}" "$BASE/tasks/$UT"
# disposable subject with tasks: deletion removes the user and their tasks
req -X POST "${H_JSON[@]}" "$BASE/users" -d "{\"name\":\"Apagar $RUN\",\"email\":\"del$RUN@ex.com\",\"password\":\"pw2-$RUN\"}"
DU="$(printf '%s' "$BODY" | json id)"
login_token "del$RUN@ex.com" "pw2-$RUN"; TD="$TOKEN"
req -X POST -H "$(auth "$TD")" "${H_JSON[@]}" -d "{\"title\":\"Do apagado\",\"user_id\":$DU}" "$BASE/tasks"
check_db "1" "disposable user owns a task" "SELECT COUNT(*) FROM tasks WHERE user_id=$DU"
check "DELETE /users/<int:user_id>" 200 "subject deletes own account" -X DELETE -H "$(auth "$TD")" "$BASE/users/$DU"
check "GET /users/<int:user_id>" 404 "deleted user (admin)" "${AH[@]}" "$BASE/users/$DU"
check "DELETE /users/<int:user_id>" 404 "delete twice (admin)" -X DELETE "${AH[@]}" "$BASE/users/$DU"
check_db "0" "nothing points at the deleted user" "SELECT (SELECT COUNT(*) FROM users WHERE id=$DU)+(SELECT COUNT(*) FROM tasks WHERE user_id=$DU)"
check "GET /tasks" 401 "deleted user's token" -H "$(auth "$TD")" "$BASE/tasks"
check "DELETE /users/<int:user_id>" 200 "admin deletes another user" -X DELETE "${AH[@]}" "$BASE/users/$NU"
check "DELETE /tasks/<int:task_id>" 200 "owner deletes own task" -X DELETE "${MH[@]}" "$BASE/tasks/$MT"

# =================================================================
EXN="$(sort -u "$EXERCISED" | wc -l | tr -d ' ')"
TOTAL=$((PASS+FAIL))
echo
echo "=================================================="
echo "TOTAL: $TOTAL checks | failures: $FAIL | skipped: $SKIP"
echo "Coverage: $INVENTORY endpoints inventoried / $EXN exercised"
echo "=================================================="
rm -f "$EXERCISED"
if [ "$EXN" != "$INVENTORY" ]; then echo "Incomplete coverage"; exit 1; fi
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
