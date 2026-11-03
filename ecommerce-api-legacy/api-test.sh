#!/usr/bin/env bash
# api-test.sh — testes de contrato da ecommerce-api-legacy (LMS com checkout).
#
# Boot:  ADMIN_TOKEN=<token> SEED_USER_PASSWORD=<senha> DB_FILE=<tmpdir>/db.sqlite npm start
#        (DB_FILE vazio ou ":memory:" = banco em memória; o seed roda no boot sobre banco vazio)
# Rodar: ADMIN_TOKEN=<token> SEED_USER_PASSWORD=<senha> DB_FILE=<mesmo arquivo> APP_LOG=<log do app> ./api-test.sh
# Porta: 3000 (PORT em src/config/index.js); BASE_URL sobrescreve.
#
# Inventário de endpoints (acesso | resolvedor de dono) → seções:
#   POST   /api/checkout                 público p/ e-mail novo; dono (pwd) p/ e-mail existente | e-mail → users.id → T1 T2 T3 T4 T6 T7 T8
#   GET    /api/admin/financial-report   admin (X-Admin-Token)                                  → T1 T2 T3 T4 T5 T7
#   DELETE /api/users/:id                admin (X-Admin-Token)                                  → T2 T3 T8
#   GET    /api/users/:id/export         admin (X-Admin-Token)                                  → T1 T2 T3 T7 T8
#
# Reexecutável: e-mails únicos por execução; ids descobertos nas respostas.
set -uo pipefail

BASE="${BASE_URL:-http://localhost:3000}"
ADMIN="${ADMIN_TOKEN:-}"
SEED_PWD="${SEED_USER_PASSWORD:-}"
DB="${DB_FILE:-:memory:}"
APP_LOG="${APP_LOG:-}"
RUN="$(date +%s)$$"

TOTAL=0; FAIL=0; SKIP=0
EXERCISED=""
INVENTORY=4

echo "=============================================="
echo "api-test — ecommerce-api-legacy"
echo "Base URL: $BASE"
echo "Início:   $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# ---------- helpers ----------
redact() {
    sed -E -e 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/<REDACTED>/g' \
           -e 's/[0-9]{12,19}/<REDACTED>/g' -e 's/scrypt\$[0-9a-f$]+/<REDACTED>/g'
}

json() { python3 -c '
import json,sys
d=json.load(sys.stdin)
for k in sys.argv[1:]:
    d=d[int(k)] if isinstance(d,list) else d[k]
print(json.dumps(d) if isinstance(d,(dict,list)) else d)' "$@" 2>/dev/null; }

mark() { case "|$EXERCISED|" in *"|$1|"*) ;; *) EXERCISED="$EXERCISED|$1";; esac; }

pass() { TOTAL=$((TOTAL+1)); echo "  ok   $1"; }
fail() { TOTAL=$((TOTAL+1)); FAIL=$((FAIL+1)); echo "  FAIL $1"; }

BODY=""; STATUS=""
# check <status> <desc> <curl args...> — guarda BODY e STATUS
check() {
    local want="$1" desc="$2"; shift 2
    local out
    out=$(curl -sS -w $'\n%{http_code}' "$@" 2>/dev/null)
    STATUS="${out##*$'\n'}"; BODY="${out%$'\n'*}"
    if [ "$STATUS" = "$want" ]; then
        pass "$desc → $STATUS $(printf '%s' "$BODY" | redact | head -c 80)"
    else
        fail "$desc — esperado $want, recebido $STATUS: $(printf '%s' "$BODY" | redact | head -c 120)"
    fi
}

check_equal() {
    if [ "$1" = "$2" ]; then pass "$3 (= $(printf '%s' "$1" | redact))"
    else fail "$3 — esperado '$(printf '%s' "$1" | redact)', recebido '$(printf '%s' "$2" | redact)'"; fi
}

# deny <padrão> <desc> <curl args...> — o padrão NÃO pode aparecer no corpo
deny() {
    local pat="$1" desc="$2"; shift 2
    local body; body=$(curl -sS "$@" 2>/dev/null)
    if printf '%s' "$body" | grep -qE -- "$pat"; then fail "$desc — valor proibido presente"
    else pass "$desc"; fi
}

DB_CLI=""
check_db() {
    local want="$1" desc="$2" sql="$3"
    if [ -z "$DB_CLI" ]; then skip "$desc" "banco não acessível pelo shell ($DB_REASON)"; return; fi
    check_equal "$want" "$(sqlite3 "$DB" "$sql" 2>&1)" "DB: $desc"
}

skip() { SKIP=$((SKIP+1)); echo "  skip $1 — $2"; }

post_checkout() { curl -sS -X POST "$BASE/api/checkout" -H 'Content-Type: application/json' -d "$1"; }
A=(-H "X-Admin-Token: $ADMIN")

# ---------- T0. Preflight ----------
echo; echo "T0. Preflight"
code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/admin/financial-report")
if [ "$code" = "000" ]; then
    echo "  aplicação inacessível em $BASE — suba com: ADMIN_TOKEN=... DB_FILE=... npm start"; exit 2
fi
echo "  aplicação respondeu (HTTP $code)"

# Isolation gate: mesma variável que a aplicação lê (DB_FILE)
case "$DB" in
    ":memory:") DB_CLASS="in-memory" ;;
    "${TMPDIR:-/nonexistent}"*|/tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) DB_CLASS="temp-file" ;;
    *) echo "DB target: not isolated — DB_FILE não é :memory: nem arquivo temporário"; exit 2 ;;
esac
echo "DB target: $DB_CLASS"
if [ "$DB_CLASS" = "temp-file" ]; then
    if ! command -v sqlite3 >/dev/null; then DB_REASON="sqlite3 CLI ausente"
    elif [ ! -f "$DB" ]; then echo "DB target: not isolated — arquivo inexistente, a aplicação não o usa"; exit 2
    else DB_CLI=1; fi
else DB_REASON="banco em memória do processo"; fi

if [ -z "$ADMIN" ]; then echo "  ADMIN_TOKEN não informado — rotas admin não podem ser testadas"; exit 2; fi
code=$(curl -s -o /dev/null -w '%{http_code}' "${A[@]}" "$BASE/api/admin/financial-report")
if [ "$code" != "200" ]; then echo "  ADMIN_TOKEN recusado pela aplicação (HTTP $code) — use o mesmo valor do boot"; exit 2; fi
echo "  token admin aceito"

EMAIL="aluno.$RUN@teste.com"; NAME="Aluno $RUN"; PWD_OK="senha-$RUN"
OTHER_EMAIL="outro.$RUN@teste.com"; OTHER_PWD="outra-$RUN"

# ---------- T1. Happy path ----------
echo; echo "T1. Happy path"
USERS_BEFORE=$(sqlite3 "$DB" 'SELECT COUNT(*) FROM users' 2>/dev/null || echo "?")
PAY_BEFORE=$(sqlite3 "$DB" 'SELECT COUNT(*) FROM payments' 2>/dev/null || echo "?")
check 200 "checkout de aluno novo" -X POST "$BASE/api/checkout" -H 'Content-Type: application/json' \
    -d "{\"usr\":\"$NAME\",\"eml\":\"$EMAIL\",\"pwd\":\"$PWD_OK\",\"c_id\":2,\"card\":\"4111222233334444\"}"
mark "POST /api/checkout"
check_equal "Sucesso" "$(printf '%s' "$BODY" | json msg)" "checkout.msg"
ENR_ID=$(printf '%s' "$BODY" | json enrollment_id)
case "$ENR_ID" in ''|*[!0-9]*) fail "checkout.enrollment_id numérico";; *) pass "checkout.enrollment_id numérico";; esac

check 200 "relatório financeiro (admin)" "${A[@]}" "$BASE/api/admin/financial-report"
mark "GET /api/admin/financial-report"
REPORT="$BODY"
check_equal "Clean Architecture" "$(printf '%s' "$REPORT" | json 0 course)" "relatório[0].course"
check_equal "Docker" "$(printf '%s' "$REPORT" | json 1 course)" "relatório[1].course"
MINE=$(printf '%s' "$REPORT" | python3 -c '
import json,sys
r=json.load(sys.stdin)
print([s["paid"] for c in r if c["course"]=="Docker" for s in c["students"] if s["student"]==sys.argv[1]])' "$NAME")
check_equal "[497]" "$MINE" "relatório lista o aluno novo em Docker com paid 497"
REV_OK=$(printf '%s' "$REPORT" | python3 -c '
import json,sys
r=json.load(sys.stdin)
print(all(abs(c["revenue"]-sum(s["paid"] for s in c["students"]))<1e-6 for c in r))')
check_equal "True" "$REV_OK" "revenue de cada curso = soma dos pagamentos PAID"

USER_ID=$(sqlite3 "$DB" "SELECT id FROM users WHERE email='$EMAIL'" 2>/dev/null)
if [ -z "$USER_ID" ]; then
    # Sem acesso ao banco: o export não lista por e-mail, então o id vem do último usuário criado
    USER_ID=""
    skip "descobrir id do aluno novo pelo banco" "$DB_REASON"
fi
if [ -n "$USER_ID" ]; then
    check 200 "exportação de dados do aluno (admin)" "${A[@]}" "$BASE/api/users/$USER_ID/export"
    mark "GET /api/users/:id/export"
    check_equal "$EMAIL" "$(printf '%s' "$BODY" | json user email)" "export.user.email é do titular"
    check_equal "$ENR_ID" "$(printf '%s' "$BODY" | json enrollments 0 id)" "export.enrollments[0].id"
    check_equal "PAID" "$(printf '%s' "$BODY" | json payments 0 status)" "export.payments[0].status"
    check_equal "497" "$(printf '%s' "$BODY" | json payments 0 amount)" "export.payments[0].amount"
fi

# ---------- T2. Sad paths ----------
echo; echo "T2. Sad paths"
J=(-X POST "$BASE/api/checkout" -H 'Content-Type: application/json')
check 400 "checkout sem eml" "${J[@]}" -d '{"usr":"A","pwd":"x","c_id":1,"card":"4111222233334444"}'
check_equal "Bad Request" "$BODY" "corpo do 400 mantém o texto original"
check 400 "checkout sem pwd (sem senha padrão)" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"sem.pwd.$RUN@t.com\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 400 "checkout com card numérico (antes derrubava o processo)" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"num.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":4111222233334444}"
code=$(curl -s -o /dev/null -w '%{http_code}' "${A[@]}" "$BASE/api/admin/financial-report")
check_equal "200" "$code" "processo continua de pé após card numérico"
check 400 "checkout com c_id string" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"cid.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":\"1\",\"card\":\"4111222233334444\"}"
check 400 "checkout com eml sem @" "${J[@]}" -d '{"usr":"A","eml":"invalido","pwd":"x","c_id":1,"card":"4111222233334444"}'
check 400 "checkout com JSON malformado" "${J[@]}" -d '{"usr":'
check 404 "checkout de curso inexistente" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"nf.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":999,\"card\":\"4111222233334444\"}"
check_equal "Curso não encontrado" "$BODY" "mensagem do 404 de curso"
check 400 "checkout com pagamento recusado" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"den.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"5111222233334444\"}"
check_equal "Pagamento recusado" "$BODY" "mensagem do pagamento recusado"
check 400 "relatório com limit=0" "${A[@]}" "$BASE/api/admin/financial-report?limit=0"
check 400 "relatório com limit=abc" "${A[@]}" "$BASE/api/admin/financial-report?limit=abc"
check 400 "relatório com limit=101" "${A[@]}" "$BASE/api/admin/financial-report?limit=101"
check 400 "relatório com offset sem limit" "${A[@]}" "$BASE/api/admin/financial-report?offset=1"
check 400 "delete com id não numérico" -X DELETE "${A[@]}" "$BASE/api/users/abc"
mark "DELETE /api/users/:id"
check 404 "delete de usuário inexistente" -X DELETE "${A[@]}" "$BASE/api/users/99999999"
check_equal "Usuário não encontrado" "$BODY" "mensagem do 404 de usuário"
check 404 "export de usuário inexistente" "${A[@]}" "$BASE/api/users/99999999/export"
mark "GET /api/users/:id/export"
check 400 "export com id não numérico" "${A[@]}" "$BASE/api/users/abc/export"

# ---------- T3. Permissões ----------
echo; echo "T3. Permissões (anônimo / outro usuário / dono / admin)"
W=(-H "X-Admin-Token: errado-$RUN")
check 401 "relatório anônimo" "$BASE/api/admin/financial-report"
check 401 "relatório com token errado" "${W[@]}" "$BASE/api/admin/financial-report"
check 200 "relatório admin" "${A[@]}" "$BASE/api/admin/financial-report"
TARGET="${USER_ID:-1}"
check 401 "delete anônimo" -X DELETE "$BASE/api/users/$TARGET"
check 401 "delete com token errado" -X DELETE "${W[@]}" "$BASE/api/users/$TARGET"
check 200 "usuário segue existindo após deletes negados" "${A[@]}" "$BASE/api/users/$TARGET/export"
check 401 "export anônimo" "$BASE/api/users/$TARGET/export"
check 401 "export com token errado" "${W[@]}" "$BASE/api/users/$TARGET/export"
# Checkout em conta existente — dono resolvido por e-mail → users.id (id ≠ id da matrícula)
check 200 "outro usuário cria a própria conta" "${J[@]}" -d "{\"usr\":\"Outro\",\"eml\":\"$OTHER_EMAIL\",\"pwd\":\"$OTHER_PWD\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 401 "outro usuário (sua senha) compra na conta do aluno" "${J[@]}" -d "{\"usr\":\"Outro\",\"eml\":\"$EMAIL\",\"pwd\":\"$OTHER_PWD\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 401 "anônimo (senha errada) compra na conta do aluno" "${J[@]}" -d "{\"usr\":\"X\",\"eml\":\"$EMAIL\",\"pwd\":\"errada\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 401 "admin (token, sem senha certa) compra na conta do aluno" "${J[@]}" "${A[@]}" -d "{\"usr\":\"X\",\"eml\":\"$EMAIL\",\"pwd\":\"errada\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 200 "dono (senha certa) compra na própria conta" "${J[@]}" -d "{\"usr\":\"$NAME\",\"eml\":\"$EMAIL\",\"pwd\":\"$PWD_OK\",\"c_id\":1,\"card\":\"4111222233334444\"}"
if [ -n "$SEED_PWD" ]; then
    check 200 "usuário semente com SEED_USER_PASSWORD" "${J[@]}" -d "{\"usr\":\"Leonan\",\"eml\":\"leonan@fullcycle.com.br\",\"pwd\":\"$SEED_PWD\",\"c_id\":2,\"card\":\"4111222233334444\"}"
    check 401 "usuário semente com a antiga senha '123'" "${J[@]}" -d '{"usr":"Leonan","eml":"leonan@fullcycle.com.br","pwd":"123","c_id":2,"card":"4111222233334444"}'
else
    skip "usuário semente" "SEED_USER_PASSWORD não informado"
fi

# ---------- T4. Bordas ----------
echo; echo "T4. Bordas"
check 200 "relatório limit=1" "${A[@]}" "$BASE/api/admin/financial-report?limit=1"
check_equal "1" "$(printf '%s' "$BODY" | json | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))')" "limit=1 devolve 1 curso"
check 200 "relatório limit=1&offset=1" "${A[@]}" "$BASE/api/admin/financial-report?limit=1&offset=1"
check_equal "Docker" "$(printf '%s' "$BODY" | json 0 course)" "offset=1 devolve o 2º curso"
check 200 "relatório limit=100 (máximo)" "${A[@]}" "$BASE/api/admin/financial-report?limit=100"
check 400 "relatório offset negativo" "${A[@]}" "$BASE/api/admin/financial-report?limit=1&offset=-1"
check 400 "card com 11 dígitos" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"c11.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"41112222333\"}"
check 200 "card com 12 dígitos" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"c12.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"411122223333\"}"
check 200 "card com 19 dígitos" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"c19.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"4111222233334444555\"}"
check 400 "card com 20 dígitos" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"c20.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"41112222333344445555\"}"
check 400 "usr string vazia" "${J[@]}" -d "{\"usr\":\"\",\"eml\":\"e1.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 400 "usr só espaços" "${J[@]}" -d "{\"usr\":\"   \",\"eml\":\"e2.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 400 "c_id zero" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"z.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":0,\"card\":\"4111222233334444\"}"
check 400 "c_id negativo" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"n.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":-1,\"card\":\"4111222233334444\"}"
check 400 "c_id fracionário" "${J[@]}" -d "{\"usr\":\"A\",\"eml\":\"f.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1.5,\"card\":\"4111222233334444\"}"
check 200 "nome com unicode" "${J[@]}" -d "{\"usr\":\"João Ñandú 学生\",\"eml\":\"uni.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"4111222233334444\"}"
check 400 "delete com id 0" -X DELETE "${A[@]}" "$BASE/api/users/0"

# ---------- T5. Estados vazios ----------
echo; echo "T5. Estados vazios"
check 200 "relatório com offset além do fim" "${A[@]}" "$BASE/api/admin/financial-report?limit=10&offset=1000"
check_equal "[]" "$BODY" "página vazia devolve []"

# ---------- T6. Persistência e integridade ----------
echo; echo "T6. Persistência e integridade"
if [ -n "$DB_CLI" ]; then
    check_db "1" "um usuário com o e-mail do aluno" "SELECT COUNT(*) FROM users WHERE email='$EMAIL'"
    check_db "1" "senha gravada como hash scrypt" "SELECT pass LIKE 'scrypt\$%' FROM users WHERE email='$EMAIL'"
    check_db "0" "nenhuma senha em texto puro (curta) na tabela users" "SELECT COUNT(*) FROM users WHERE length(pass) < 60"
    check_db "2" "aluno tem 2 matrículas (T1 + dono em T3)" "SELECT COUNT(*) FROM enrollments WHERE user_id=$USER_ID"
    check_db "2" "aluno tem 2 pagamentos PAID" "SELECT COUNT(*) FROM payments p JOIN enrollments e ON e.id=p.enrollment_id WHERE e.user_id=$USER_ID AND p.status='PAID'"
    check_db "1" "auditoria da matrícula de T1" "SELECT COUNT(*) FROM audit_logs WHERE action='Checkout curso 2 por $USER_ID'"
    check_db "0" "pagamento recusado não criou usuário (atomicidade)" "SELECT COUNT(*) FROM users WHERE email='den.$RUN@t.com'"
    check_db "0" "curso inexistente não criou usuário" "SELECT COUNT(*) FROM users WHERE email='nf.$RUN@t.com'"
    check_db "0" "nenhum pagamento sem matrícula" "SELECT COUNT(*) FROM payments WHERE enrollment_id NOT IN (SELECT id FROM enrollments)"
    check_db "0" "nenhuma matrícula sem pagamento" "SELECT COUNT(*) FROM enrollments WHERE id NOT IN (SELECT enrollment_id FROM payments)"
    # Corrida: dois checkouts simultâneos do mesmo e-mail novo com senhas diferentes
    RACE_EMAIL="corrida.$RUN@teste.com"
    for pw in senha-a senha-b; do
        post_checkout "{\"usr\":\"Corrida\",\"eml\":\"$RACE_EMAIL\",\"pwd\":\"$pw\",\"c_id\":1,\"card\":\"4111222233334444\"}" >/dev/null &
    done
    wait
    check_db "1" "checkouts simultâneos do mesmo e-mail criam uma só conta" "SELECT COUNT(*) FROM users WHERE email='$RACE_EMAIL'"
    check_db "1" "índice UNIQUE em users.email" "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_users_email'"
    DUP=$(sqlite3 "$DB" "INSERT INTO users (name, email, pass) VALUES ('x', '$RACE_EMAIL', 'x')" 2>&1)
    case "$DUP" in *UNIQUE*) pass "banco rejeita e-mail duplicado (UNIQUE)";; *) fail "banco aceitou e-mail duplicado";; esac
    # Senha errada em rajada não pode segurar a fila de transações (scrypt fora da transação).
    # Compara uma operação que usa a fila (DELETE) com uma que não usa (export) durante a mesma rajada:
    # a carga de CPU do scrypt atinge as duas; só a fila de transações atrasaria apenas o DELETE.
    for k in $(seq 1 20); do
        post_checkout "{\"usr\":\"X\",\"eml\":\"$EMAIL\",\"pwd\":\"errada-$k\",\"c_id\":1,\"card\":\"4111222233334444\"}" >/dev/null &
    done
    sleep 0.05
    TF=$(mktemp)
    curl -s -o /dev/null -w '%{time_total}' -X DELETE "${A[@]}" "$BASE/api/users/99999998" >"$TF.del" &
    curl -s -o /dev/null -w '%{time_total}' "${A[@]}" "$BASE/api/users/$USER_ID/export" >"$TF.exp" &
    wait
    T_DEL=$(cat "$TF.del"); T_EXP=$(cat "$TF.exp"); rm -f "$TF" "$TF.del" "$TF.exp"
    FAST=$(python3 -c "print(1 if float('$T_DEL') <= float('$T_EXP') + 0.25 else 0)")
    check_equal "1" "$FAST" "delete não espera a fila durante rajada de senhas erradas (delete ${T_DEL}s vs export ${T_EXP}s)"
else
    skip "verificações no banco" "$DB_REASON"
fi

# ---------- T7. Privacidade ----------
echo; echo "T7. Privacidade"
if [ -n "$USER_ID" ]; then
    deny '"pass"|scrypt\$' "export não traz hash de senha" "${A[@]}" "$BASE/api/users/$USER_ID/export"
fi
deny '@' "relatório não traz e-mails" "${A[@]}" "$BASE/api/admin/financial-report"
deny '"pass"|scrypt\$' "checkout não devolve hash" "${J[@]}" -d "{\"usr\":\"P\",\"eml\":\"priv.$RUN@t.com\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"4111222233334444\"}"
if [ -n "$APP_LOG" ] && [ -f "$APP_LOG" ]; then
    if grep -q '4111222233334444' "$APP_LOG"; then fail "log da aplicação contém número de cartão completo"; else pass "log da aplicação sem número de cartão completo"; fi
    if grep -q '\*\*\*\*4444' "$APP_LOG"; then pass "log registra o cartão mascarado"; else fail "log não registra o cartão mascarado"; fi
    if grep -q "$EMAIL" "$APP_LOG"; then fail "log da aplicação contém e-mail do aluno"; else pass "log da aplicação sem e-mail do aluno"; fi
    if grep -q "$PWD_OK" "$APP_LOG"; then fail "log da aplicação contém senha"; else pass "log da aplicação sem senha"; fi
else
    skip "log da aplicação" "APP_LOG não informado"
fi

# ---------- T8. Operações destrutivas ----------
echo; echo "T8. Exclusão do titular"
DEL_EMAIL="apagar.$RUN@teste.com"; DEL_NAME="Apagar $RUN"
post_checkout "{\"usr\":\"$DEL_NAME\",\"eml\":\"$DEL_EMAIL\",\"pwd\":\"x\",\"c_id\":1,\"card\":\"4111222233334444\"}" >/dev/null
DEL_ID=$(sqlite3 "$DB" "SELECT id FROM users WHERE email='$DEL_EMAIL'" 2>/dev/null)
if [ -z "$DEL_ID" ]; then DEL_ID="$USER_ID"; fi
if [ -z "$DEL_ID" ]; then
    skip "exclusão do titular" "id do usuário descartável indisponível ($DB_REASON)"
else
    PAY_COUNT=$(sqlite3 "$DB" 'SELECT COUNT(*) FROM payments' 2>/dev/null)
    check 200 "delete admin do usuário descartável" -X DELETE "${A[@]}" "$BASE/api/users/$DEL_ID"
    check_equal "Usuário deletado" "$BODY" "mensagem de sucesso do delete"
    check 404 "segundo delete do mesmo id" -X DELETE "${A[@]}" "$BASE/api/users/$DEL_ID"
    check 404 "export após delete" "${A[@]}" "$BASE/api/users/$DEL_ID/export"
    check 200 "relatório após delete" "${A[@]}" "$BASE/api/admin/financial-report"
    deny "$DEL_NAME" "relatório não mostra mais o nome apagado" "${A[@]}" "$BASE/api/admin/financial-report"
    check_db "0" "linha do usuário removida" "SELECT COUNT(*) FROM users WHERE id=$DEL_ID"
    check_db "0" "nenhuma matrícula aponta para o id" "SELECT COUNT(*) FROM enrollments WHERE user_id=$DEL_ID"
    check_db "0" "nenhuma auditoria com 'por <id>'" "SELECT COUNT(*) FROM audit_logs WHERE action LIKE '% por $DEL_ID'"
    check_db "1" "auditoria anonimizada mantida" "SELECT COUNT(*) >= 1 FROM audit_logs WHERE action LIKE '% por [removed]'"
    check_db "$PAY_COUNT" "pagamentos mantidos para contabilidade" "SELECT COUNT(*) FROM payments"
fi

# ---------- rodapé ----------
N_EXERCISED=$(printf '%s' "$EXERCISED" | tr '|' '\n' | grep -c .)
echo
echo "=============================================="
echo "TOTAL: $TOTAL checks | failures: $FAIL | skipped: $SKIP"
echo "Coverage: $INVENTORY endpoints inventoried / $N_EXERCISED exercised"
echo "=============================================="
if [ "$FAIL" -gt 0 ]; then exit 1; fi
if [ "$N_EXERCISED" -ne "$INVENTORY" ]; then echo "cobertura incompleta"; exit 1; fi
exit 0
