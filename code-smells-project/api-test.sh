#!/usr/bin/env bash
# api-test.sh — contrato HTTP da API da Loja (code-smells-project)
#
# Boot (banco descartável obrigatório — o gate de isolamento recusa loja.db):
#   export DB_PATH="$(mktemp -d)/loja-test.db" ADMIN_PASSWORD=<senha> SEED_CUSTOMER_PASSWORD=<senha>
#   python app.py > "$APP_LOG_FILE" 2>&1 &        # porta 5000 (APP_PORT)
#   BASE_URL=http://localhost:5000 ./api-test.sh
# Variáveis lidas: BASE_URL, DB_PATH (o mesmo do app), ADMIN_PASSWORD, SEED_CUSTOMER_PASSWORD,
# APP_LOG_FILE (opcional, para T7). Pode rodar várias vezes até o reset do T8, que apaga tudo:
# depois dele, reinicie o app com um DB_PATH novo.
#
# Inventário (método rota — acesso — seção que exercita):
#   GET    /                                — public          — T1
#   GET    /produtos                        — public          — T1 T4
#   GET    /produtos/busca                  — public          — T1 T2 T5
#   GET    /produtos/<int:id>               — public          — T1 T2
#   POST   /produtos                        — admin           — T1 T2 T3 T4
#   PUT    /produtos/<int:id>               — admin           — T1 T2 T3
#   DELETE /produtos/<int:id>               — admin           — T1 T2 T3 T4
#   GET    /usuarios                        — admin           — T1 T3 T7
#   GET    /usuarios/<int:id>               — owner-or-admin (dono: o próprio id)          — T1 T2 T3 T7
#   POST   /usuarios                        — public          — T1 T2
#   POST   /login                           — public          — T1 T2 T7
#   POST   /pedidos                         — owner-or-admin (dono: usuario_id do corpo)   — T1 T2 T3 T6
#   GET    /pedidos                         — admin           — T1 T3
#   GET    /pedidos/usuario/<int:usuario_id>— owner-or-admin (dono: usuario_id da rota)    — T1 T3 T5
#   PUT    /pedidos/<int:pedido_id>/status  — admin           — T1 T2 T3
#   GET    /relatorios/vendas               — admin           — T1 T3
#   GET    /health                          — public          — T0 T1 T7
#   POST   /admin/reset-db                  — admin           — T3 T8
#   POST   /admin/query                     — admin + ADMIN_QUERY_ENABLED (desligado → 403) — T1 T3
#   DELETE /usuarios/<int:id>               — owner-or-admin (dono: o próprio id)          — T3 T8
#   GET    /usuarios/<int:id>/export        — owner-or-admin (dono: o próprio id)          — T1 T3 T7
set -uo pipefail

BASE="${BASE_URL:-http://localhost:5000}"
DB="${DB_PATH:-loja.db}"
RUN="$$-$(date +%s)"
PASS=0; FAIL=0; SKIP=0
EXERCISED="$(mktemp)"
INVENTORY=21

echo "=================================================="
echo "api-test.sh — code-smells-project"
echo "Base URL: $BASE"
echo "Início:   $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

# ---------- helpers ----------
redact() {
  sed -E 's/[A-Za-z0-9._%+*-]+@[A-Za-z0-9.-]+/<REDACTED>/g; s/("token": *")[^"]*"/\1<REDACTED>"/g'
}

json() {  # json chave [chave|índice...]  — lê JSON da stdin
  python3 -c '
import sys, json
try:
    v = json.load(sys.stdin)
    for k in sys.argv[1:]:
        v = v[int(k)] if isinstance(v, list) else v[k]
except Exception:
    print("<ausente>"); sys.exit(0)
print(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
' "$@"
}

mark() { echo "$1" >> "$EXERCISED"; }

req() {  # req <curl args...> → STATUS, BODY
  local out
  out="$(curl -sS -m 15 -w $'\n%{http_code}' "$@" 2>/dev/null)"
  STATUS="${out##*$'\n'}"
  BODY="${out%$'\n'*}"
}

ok()   { PASS=$((PASS+1)); echo "  PASS $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; echo "       esperado: $2"; echo "       obtido:   $(printf '%s' "$3" | head -c 300 | redact)"; }
skip() { SKIP=$((SKIP+1)); echo "  SKIP $1 — $2"; }

check() {  # check <endpoint> <status> <desc> <curl args...>
  local ep="$1" exp="$2" desc="$3"; shift 3
  mark "$ep"
  req "$@"
  if [ "$STATUS" = "$exp" ]; then
    ok "[$exp] $ep — $desc :: $(printf '%s' "$BODY" | tr -d '\n' | head -c 110 | redact)"
  else
    bad "$ep — $desc" "HTTP $exp" "HTTP $STATUS $BODY"
  fi
}

check_equal() {  # check_equal <esperado> <obtido> <desc>
  if [ "$1" = "$2" ]; then ok "$3"; else bad "$3" "$1" "$2"; fi
}

deny() {  # deny <regex> <desc>  — sobre o BODY da última requisição
  if printf '%s' "$BODY" | grep -Eq "$1"; then
    bad "$2" "ausente: /$1/" "(presente — valor não impresso)"
  else
    ok "$2"
  fi
}

check_db() {  # check_db <esperado> <desc> <sql>
  if ! command -v sqlite3 >/dev/null 2>&1; then skip "$2" "sqlite3 indisponível"; return; fi
  local got; got="$(sqlite3 "$DB" "$3" 2>&1)"
  check_equal "$1" "$got" "DB: $2"
}

H_JSON=(-H "Content-Type: application/json")
auth() { echo "Authorization: Bearer $1"; }

# =================================================================
echo; echo "== T0. Preflight"
req "$BASE/health"
if [ "$STATUS" != "200" ]; then
  echo "Aplicação não responde em $BASE (HTTP '$STATUS'). Suba com: DB_PATH=<tmp> python app.py"
  exit 2
fi
mark "GET /health"; ok "[200] GET /health — aplicação no ar"

# Gate de isolamento: só um arquivo de banco em diretório temporário
case "$DB" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*|"${TMPDIR:-/nonexistent}"*) DBCLASS="temp-file" ;;
  ":memory:") DBCLASS="in-memory" ;;
  *) echo "DB target: not isolated — DB_PATH não está em um diretório temporário"; exit 2 ;;
esac
if [ ! -f "$DB" ]; then echo "DB target: not isolated — arquivo DB_PATH inexistente (o app usa outro banco?)"; exit 2; fi
api_count="$(printf '%s' "$BODY" | json counts produtos)"
db_count="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM produtos' 2>/dev/null)"
if [ "$api_count" != "$db_count" ]; then
  echo "DB target: not isolated — o app não usa o DB_PATH informado (api=$api_count db=$db_count)"; exit 2
fi
echo "DB target: $DBCLASS"

if [ -z "${ADMIN_PASSWORD:-}" ] || [ -z "${SEED_CUSTOMER_PASSWORD:-}" ]; then
  echo "ADMIN_PASSWORD e SEED_CUSTOMER_PASSWORD são necessários (os mesmos do boot)"; exit 2
fi

login_token() {  # login_token <email> <senha> → TOKEN, UID_
  req -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"$1\",\"senha\":\"$2\"}"
  TOKEN="$(printf '%s' "$BODY" | json token)"; UID_="$(printf '%s' "$BODY" | json dados id)"
}
login_token admin@loja.com "$ADMIN_PASSWORD";           TA="$TOKEN"; ADMIN_ID="$UID_"
login_token joao@email.com "$SEED_CUSTOMER_PASSWORD";   TJ="$TOKEN"; J="$UID_"
login_token maria@email.com "$SEED_CUSTOMER_PASSWORD";  TM="$TOKEN"; M="$UID_"
for v in "$TA" "$TJ" "$TM"; do
  if [ "$v" = "<ausente>" ] || [ -z "$v" ]; then echo "Login do seed falhou — confira as senhas do boot"; exit 2; fi
done
echo "  tokens obtidos para admin, joao, maria (ids $ADMIN_ID, $J, $M)"

# =================================================================
echo; echo "== T1. Caminho feliz"
check "GET /" 200 "boas-vindas" "$BASE/"
check_equal "Bem-vindo à API da Loja" "$(printf '%s' "$BODY" | json mensagem)" "GET / mensagem"

check "GET /produtos" 200 "lista completa sem paginação" "$BASE/produtos"
check_equal "True" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin)["dados"]; print(any(p["nome"]=="Notebook Gamer" for p in d) and len(d)>=10)')" "GET /produtos contém o seed"
P1="$(printf '%s' "$BODY" | python3 -c 'import sys,json; print([p for p in json.load(sys.stdin)["dados"] if p["nome"]=="Mouse Wireless"][0]["id"])')"

check "GET /produtos/busca" 200 "busca por termo" "$BASE/produtos/busca?q=Mouse"
check_equal "Mouse Wireless" "$(printf '%s' "$BODY" | json dados 0 nome)" "busca q=Mouse devolve Mouse Wireless"
check "GET /produtos/busca" 200 "filtro categoria+preço" "$BASE/produtos/busca?categoria=moveis&preco_min=1000&preco_max=2000"
check_equal "Cadeira Gamer" "$(printf '%s' "$BODY" | json dados 0 nome)" "filtro devolve Cadeira Gamer"

check "GET /produtos/<int:id>" 200 "detalhe" "$BASE/produtos/$P1"
check_equal "89.9" "$(printf '%s' "$BODY" | json dados preco)" "preço do Mouse Wireless"

check "POST /produtos" 201 "admin cria" -X POST "$BASE/produtos" "${H_JSON[@]}" -H "$(auth "$TA")" \
  -d "{\"nome\":\"Produto Teste $RUN\",\"descricao\":\"d\",\"preco\":10.5,\"estoque\":7,\"categoria\":\"livros\"}"
NP="$(printf '%s' "$BODY" | json dados id)"
req "$BASE/produtos/$NP"
check_equal "Produto Teste $RUN|10.5|7|livros" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin)["dados"]; print("|".join(str(d[k]) for k in ("nome","preco","estoque","categoria")))')" "produto criado persistido"

check "PUT /produtos/<int:id>" 200 "admin atualiza" -X PUT "$BASE/produtos/$NP" "${H_JSON[@]}" -H "$(auth "$TA")" \
  -d "{\"nome\":\"Produto Teste $RUN\",\"preco\":12,\"estoque\":9,\"categoria\":\"livros\"}"
req "$BASE/produtos/$NP"
check_equal "12.0|9" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin)["dados"]; print(str(float(d["preco"]))+"|"+str(d["estoque"]))')" "atualização persistida"

check "POST /usuarios" 201 "cadastro público" -X POST "$BASE/usuarios" "${H_JSON[@]}" \
  -d "{\"nome\":\"Teste $RUN\",\"email\":\"t$RUN@ex.com\",\"senha\":\"pw-$RUN\",\"tipo\":\"admin\"}"
NU="$(printf '%s' "$BODY" | json dados id)"
check "POST /login" 200 "login do novo usuário" -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"t$RUN@ex.com\",\"senha\":\"pw-$RUN\"}"
TN="$(printf '%s' "$BODY" | json token)"
check_equal "cliente" "$(printf '%s' "$BODY" | json dados tipo)" "cadastro ignora tipo do corpo (AP-17)"

check "GET /usuarios" 200 "admin lista" -H "$(auth "$TA")" "$BASE/usuarios"
check_equal "admin@loja.com|j***@email.com" "$(printf '%s' "$BODY" | python3 -c '
import sys,json; d={u["id"]:u["email"] for u in json.load(sys.stdin)["dados"]}
print(d['"$ADMIN_ID"']+"|"+d['"$J"'])')" "email completo só do próprio admin; outros mascarados"

check "GET /usuarios/<int:id>" 200 "dono vê o próprio" -H "$(auth "$TJ")" "$BASE/usuarios/$J"
check_equal "joao@email.com" "$(printf '%s' "$BODY" | json dados email)" "dono recebe email completo"

req "$BASE/produtos/$P1"; EST0="$(printf '%s' "$BODY" | json dados estoque)"
check "POST /pedidos" 201 "dono cria pedido" -X POST "$BASE/pedidos" "${H_JSON[@]}" -H "$(auth "$TJ")" \
  -d "{\"usuario_id\":$J,\"itens\":[{\"produto_id\":$P1,\"quantidade\":2}]}"
PED="$(printf '%s' "$BODY" | json dados pedido_id)"
check_equal "179.8" "$(printf '%s' "$BODY" | json dados total)" "total = 2 × 89.9"
req "$BASE/produtos/$P1"
check_equal "$((EST0-2))" "$(printf '%s' "$BODY" | json dados estoque)" "estoque baixado em 2"

check "GET /pedidos" 200 "admin lista todos" -H "$(auth "$TA")" "$BASE/pedidos"
check_equal "Mouse Wireless" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; print([p for p in json.load(sys.stdin)["dados"] if p["id"]=='"$PED"'][0]["itens"][0]["produto_nome"])')" "pedido listado com produto_nome"

check "GET /pedidos/usuario/<int:usuario_id>" 200 "dono lista os seus" -H "$(auth "$TJ")" "$BASE/pedidos/usuario/$J"
check_equal "True" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin)["dados"]; print(any(p["id"]=='"$PED"' for p in d) and all(p["usuario_id"]=='"$J"' for p in d))')" "só pedidos do dono"

check "PUT /pedidos/<int:pedido_id>/status" 200 "admin aprova" -X PUT "$BASE/pedidos/$PED/status" "${H_JSON[@]}" -H "$(auth "$TA")" -d '{"status":"aprovado"}'
req -H "$(auth "$TJ")" "$BASE/pedidos/usuario/$J"
check_equal "aprovado" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; print([p for p in json.load(sys.stdin)["dados"] if p["id"]=='"$PED"'][0]["status"])')" "status persistido"

check "GET /relatorios/vendas" 200 "admin relatório" -H "$(auth "$TA")" "$BASE/relatorios/vendas"
check_equal "$(sqlite3 "$DB" 'SELECT COUNT(*) FROM pedidos')" "$(printf '%s' "$BODY" | json dados total_pedidos)" "total_pedidos = COUNT(*) no banco"
check_equal "$(sqlite3 "$DB" "SELECT COUNT(*) FROM pedidos WHERE status='aprovado'")" "$(printf '%s' "$BODY" | json dados pedidos_aprovados)" "pedidos_aprovados = banco"

check "GET /health" 200 "health" "$BASE/health"
check_equal "ok|connected|1.0.0" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["status"]+"|"+d["database"]+"|"+d["versao"])')" "health valores"

check "GET /usuarios/<int:id>/export" 200 "dono exporta" -H "$(auth "$TJ")" "$BASE/usuarios/$J/export"
check_equal "$J|True" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin)["dados"]; print(str(d["usuario"]["id"])+"|"+str(any(p["id"]=='"$PED"' for p in d["pedidos"])))')" "export traz perfil e pedidos"

check "POST /admin/query" 403 "admin, mas ADMIN_QUERY_ENABLED desligado" -X POST "$BASE/admin/query" "${H_JSON[@]}" -H "$(auth "$TA")" -d '{"sql":"SELECT 1"}'

# =================================================================
echo; echo "== T2. Caminhos tristes"
AH=(-H "$(auth "$TA")")
check "POST /produtos" 400 "sem nome" -X POST "$BASE/produtos" "${H_JSON[@]}" "${AH[@]}" -d '{"preco":1,"estoque":1}'
check_equal "Nome é obrigatório" "$(printf '%s' "$BODY" | json erro)" "mensagem sem nome"
check "POST /produtos" 400 "preço não numérico (era 500)" -X POST "$BASE/produtos" "${H_JSON[@]}" "${AH[@]}" -d '{"nome":"Xyz","preco":"abc","estoque":1}'
check "POST /produtos" 400 "categoria inválida" -X POST "$BASE/produtos" "${H_JSON[@]}" "${AH[@]}" -d '{"nome":"Xyz","preco":1,"estoque":1,"categoria":"armas"}'
check "POST /produtos" 400 "JSON malformado" -X POST "$BASE/produtos" "${H_JSON[@]}" "${AH[@]}" -d '{"nome":'
check_equal "Dados inválidos" "$(printf '%s' "$BODY" | json erro)" "mensagem JSON malformado"
check "PUT /produtos/<int:id>" 400 "nome curto no update (regra unificada)" -X PUT "$BASE/produtos/$NP" "${H_JSON[@]}" "${AH[@]}" -d '{"nome":"A","preco":1,"estoque":1}'
check_equal "Nome muito curto" "$(printf '%s' "$BODY" | json erro)" "mensagem nome curto"
check "PUT /produtos/<int:id>" 400 "categoria inválida no update" -X PUT "$BASE/produtos/$NP" "${H_JSON[@]}" "${AH[@]}" -d '{"nome":"Abc","preco":1,"estoque":1,"categoria":"x"}'
check "PUT /produtos/<int:id>" 404 "id inexistente" -X PUT "$BASE/produtos/999999" "${H_JSON[@]}" "${AH[@]}" -d '{"nome":"Abc","preco":1,"estoque":1}'
check "GET /produtos/<int:id>" 404 "id inexistente" "$BASE/produtos/999999"
check_equal "Produto não encontrado|False" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["erro"]+"|"+str(d["sucesso"]))')" "corpo 404 preservado"
check "DELETE /produtos/<int:id>" 404 "id inexistente" -X DELETE "${AH[@]}" "$BASE/produtos/999999"
check "GET /produtos/busca" 400 "preco_min não numérico (era 500)" "$BASE/produtos/busca?preco_min=abc"
check "POST /usuarios" 400 "sem senha" -X POST "$BASE/usuarios" "${H_JSON[@]}" -d '{"nome":"a","email":"b@c.d"}'
check "POST /usuarios" 400 "sem corpo" -X POST "$BASE/usuarios"
check "POST /login" 401 "senha errada" -X POST "$BASE/login" "${H_JSON[@]}" -d '{"email":"joao@email.com","senha":"errada"}'
check_equal "Email ou senha inválidos|False" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["erro"]+"|"+str(d["sucesso"]))')" "corpo 401 preservado"
check "POST /login" 401 "injeção SQL no email não autentica" -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"' OR 1=1 --\",\"senha\":\"x\"}"
check "POST /login" 400 "sem corpo (era 500)" -X POST "$BASE/login"
JH=(-H "$(auth "$TJ")")
check "POST /pedidos" 400 "sem corpo" -X POST "$BASE/pedidos" "${JH[@]}"
check "POST /pedidos" 400 "sem usuario_id" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"itens\":[{\"produto_id\":$P1,\"quantidade\":1}]}"
check "POST /pedidos" 400 "itens vazio" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"usuario_id\":$J,\"itens\":[]}"
check "POST /pedidos" 400 "quantidade não inteira (era 500)" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"usuario_id\":$J,\"itens\":[{\"produto_id\":$P1,\"quantidade\":\"x\"}]}"
check "POST /pedidos" 400 "item sem produto_id (era 500)" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"usuario_id\":$J,\"itens\":[{\"quantidade\":1}]}"
check "POST /pedidos" 400 "produto inexistente" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"usuario_id\":$J,\"itens\":[{\"produto_id\":999999,\"quantidade\":1}]}"
check "POST /pedidos" 404 "usuario_id inexistente (admin)" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${AH[@]}" -d "{\"usuario_id\":999999,\"itens\":[{\"produto_id\":$P1,\"quantidade\":1}]}"
check "POST /pedidos" 400 "estoque insuficiente" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"usuario_id\":$J,\"itens\":[{\"produto_id\":$P1,\"quantidade\":100000}]}"
check "PUT /pedidos/<int:pedido_id>/status" 400 "status inválido" -X PUT "$BASE/pedidos/$PED/status" "${H_JSON[@]}" "${AH[@]}" -d '{"status":"voando"}'
check "PUT /pedidos/<int:pedido_id>/status" 400 "sem corpo (era 500)" -X PUT "$BASE/pedidos/$PED/status" "${AH[@]}"
check "GET /usuarios/<int:id>" 404 "admin, id inexistente" "${AH[@]}" "$BASE/usuarios/999999"
for p in "page=0" "per_page=1000" "per_page=abc"; do
  check "GET /produtos" 400 "paginação inválida $p" "$BASE/produtos?$p"
done
check "GET /produtos" 400 "500 nunca vaza exceção — erro tem só a chave erro" "$BASE/produtos?page=-1"
check_equal "erro" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; print(",".join(json.load(sys.stdin).keys()))')" "corpo de erro"

# =================================================================
echo; echo "== T3. Permissões (anônimo / dono / outro usuário / admin)"
MH=(-H "$(auth "$TM")")
BADT=(-H "Authorization: Bearer token-forjado")
# dono-ou-admin: recursos de joao ($J); pedido $PED (id ≠ id do dono)
for spec in "GET /usuarios/<int:id>|$BASE/usuarios/$J" "GET /pedidos/usuario/<int:usuario_id>|$BASE/pedidos/usuario/$J" "GET /usuarios/<int:id>/export|$BASE/usuarios/$J/export"; do
  ep="${spec%%|*}"; url="${spec#*|}"
  check "$ep" 401 "anônimo" "$url"
  check "$ep" 401 "token forjado" "${BADT[@]}" "$url"
  check "$ep" 200 "dono" "${JH[@]}" "$url"
  check "$ep" 403 "outro usuário" "${MH[@]}" "$url"
  check "$ep" 200 "admin" "${AH[@]}" "$url"
done
BODYP="{\"usuario_id\":$J,\"itens\":[{\"produto_id\":$P1,\"quantidade\":1}]}"
check "POST /pedidos" 401 "anônimo" -X POST "$BASE/pedidos" "${H_JSON[@]}" -d "$BODYP"
check "POST /pedidos" 403 "outro usuário em nome do dono" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${MH[@]}" -d "$BODYP"
check "POST /pedidos" 201 "dono" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "$BODYP"
check "POST /pedidos" 201 "admin em nome do dono" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${AH[@]}" -d "$BODYP"
check "DELETE /usuarios/<int:id>" 401 "anônimo" -X DELETE "$BASE/usuarios/$J"
check "DELETE /usuarios/<int:id>" 403 "outro usuário" -X DELETE "${MH[@]}" "$BASE/usuarios/$J"
# somente admin: anônimo 401, cliente 403 (o admin 2xx está no T1/T8)
for spec in "POST /produtos|POST|$BASE/produtos" "PUT /produtos/<int:id>|PUT|$BASE/produtos/$NP" "DELETE /produtos/<int:id>|DELETE|$BASE/produtos/$NP" \
            "GET /usuarios|GET|$BASE/usuarios" "GET /pedidos|GET|$BASE/pedidos" "PUT /pedidos/<int:pedido_id>/status|PUT|$BASE/pedidos/$PED/status" \
            "GET /relatorios/vendas|GET|$BASE/relatorios/vendas" "POST /admin/reset-db|POST|$BASE/admin/reset-db" "POST /admin/query|POST|$BASE/admin/query"; do
  ep="${spec%%|*}"; rest="${spec#*|}"; meth="${rest%%|*}"; url="${rest#*|}"
  check "$ep" 401 "anônimo" -X "$meth" "${H_JSON[@]}" -d '{}' "$url"
  check "$ep" 403 "cliente" -X "$meth" "${H_JSON[@]}" "${JH[@]}" -d '{}' "$url"
done

# =================================================================
echo; echo "== T4. Bordas"
mkp() { check "POST /produtos" "$1" "$2" -X POST "$BASE/produtos" "${H_JSON[@]}" "${AH[@]}" -d "$3"; }
N200="$(python3 -c 'print("n"*200)')"; N201="$(python3 -c 'print("n"*201)')"
mkp 400 "nome com 1 char (min-1)" '{"nome":"a","preco":1,"estoque":1}'
mkp 201 "nome com 2 chars (min)" '{"nome":"ab","preco":1,"estoque":1}'
mkp 201 "nome com 200 chars (max)" "{\"nome\":\"$N200\",\"preco\":1,\"estoque\":1}"
mkp 400 "nome com 201 chars (max+1)" "{\"nome\":\"$N201\",\"preco\":1,\"estoque\":1}"
mkp 201 "preço zero" '{"nome":"Grátis","preco":0,"estoque":0}'
mkp 400 "estoque negativo" '{"nome":"Neg","preco":1,"estoque":-1}'
mkp 400 "estoque fracionado" '{"nome":"Frac","preco":1,"estoque":1.5}'
mkp 201 "unicode no nome" '{"nome":"Café ☕ 日本","preco":1,"estoque":1}'
check_equal "Café ☕ 日本" "$(curl -sS "$BASE/produtos/$(printf '%s' "$BODY" | json dados id)" | json dados nome)" "unicode persistido"
check "POST /pedidos" 400 "quantidade zero" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"usuario_id\":$J,\"itens\":[{\"produto_id\":$P1,\"quantidade\":0}]}"
check "POST /pedidos" 400 "quantidade negativa (aumentava estoque)" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" -d "{\"usuario_id\":$J,\"itens\":[{\"produto_id\":$P1,\"quantidade\":-5}]}"
check "GET /produtos" 200 "page=1&per_page=2" "$BASE/produtos?page=1&per_page=2"
check_equal "2" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["dados"]))')" "per_page=2 devolve 2"
check "GET /produtos" 200 "página além do fim" "$BASE/produtos?page=100000&per_page=100"
check_equal "[]" "$(printf '%s' "$BODY" | json dados)" "página vazia é []"
mkp 201 "produto descartável" '{"nome":"Descartável","preco":1,"estoque":1}'
DP="$(printf '%s' "$BODY" | json dados id)"
check "DELETE /produtos/<int:id>" 200 "admin deleta" -X DELETE "${AH[@]}" "$BASE/produtos/$DP"
check "DELETE /produtos/<int:id>" 404 "deletar duas vezes" -X DELETE "${AH[@]}" "$BASE/produtos/$DP"
check "GET /produtos/<int:id>" 404 "deletado some" "$BASE/produtos/$DP"

# =================================================================
echo; echo "== T5. Estados vazios"
check "GET /produtos/busca" 200 "busca sem resultado" "$BASE/produtos/busca?q=zzz-inexistente-$RUN"
check_equal "0|[]" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(str(d["total"])+"|"+json.dumps(d["dados"]))')" "total 0 e lista vazia"
check "GET /pedidos/usuario/<int:usuario_id>" 200 "usuário novo sem pedidos" -H "$(auth "$TN")" "$BASE/pedidos/usuario/$NU"
check_equal "[]" "$(printf '%s' "$BODY" | json dados)" "lista vazia"

# =================================================================
echo; echo "== T6. Persistência e integridade"
check_db "0" "nenhuma senha em texto puro (seed)" "SELECT COUNT(*) FROM usuarios WHERE senha IN ('$ADMIN_PASSWORD','$SEED_CUSTOMER_PASSWORD','pw-$RUN')"
check_db "0" "toda senha tem formato de hash longo" "SELECT COUNT(*) FROM usuarios WHERE length(senha) < 60"
check_db "1" "pedido $PED tem 1 item gravado" "SELECT COUNT(*) FROM itens_pedido WHERE pedido_id = $PED"
check_db "0" "nenhum item órfão" "SELECT COUNT(*) FROM itens_pedido WHERE pedido_id NOT IN (SELECT id FROM pedidos)"
# atomicidade: 2º item falha → nada gravado, estoque do 1º intacto
req "$BASE/produtos/$P1"; EST1="$(printf '%s' "$BODY" | json dados estoque)"
NPED0="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM pedidos')"
check "POST /pedidos" 400 "2º item sem estoque" -X POST "$BASE/pedidos" "${H_JSON[@]}" "${JH[@]}" \
  -d "{\"usuario_id\":$J,\"itens\":[{\"produto_id\":$P1,\"quantidade\":1},{\"produto_id\":$P1,\"quantidade\":100000}]}"
req "$BASE/produtos/$P1"
check_equal "$EST1" "$(printf '%s' "$BODY" | json dados estoque)" "estoque intacto após falha"
check_db "$NPED0" "nenhum pedido parcial" "SELECT COUNT(*) FROM pedidos"

# =================================================================
echo; echo "== T7. Privacidade"
for spec in "GET /usuarios|$TA|$BASE/usuarios" "GET /usuarios/<int:id>|$TJ|$BASE/usuarios/$J" "GET /usuarios/<int:id>/export|$TJ|$BASE/usuarios/$J/export"; do
  ep="${spec%%|*}"; rest="${spec#*|}"; tk="${rest%%|*}"; url="${rest#*|}"
  check "$ep" 200 "resposta de usuário" -H "$(auth "$tk")" "$url"
  deny '"senha"' "$ep sem campo senha"
  deny 'scrypt:|pbkdf2:' "$ep sem hash"
done
check "POST /login" 200 "login" -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"t$RUN@ex.com\",\"senha\":\"pw-$RUN\"}"
deny '"senha"' "login sem campo senha"
check "GET /health" 200 "health" "$BASE/health"
deny 'secret_key|db_path|"debug"|ambiente' "health sem segredos/config interna"
check "GET /usuarios/<int:id>" 200 "admin vê outro usuário" "${AH[@]}" "$BASE/usuarios/$J"
deny 'joao@email\.com' "email de terceiro mascarado para admin"
if [ -n "${APP_LOG_FILE:-}" ] && [ -f "$APP_LOG_FILE" ]; then
  req -X POST "$BASE/login" "${H_JSON[@]}" -d "{\"email\":\"t$RUN@ex.com\",\"senha\":\"errada\"}"
  if grep -q "t$RUN@ex.com" "$APP_LOG_FILE"; then bad "log sem email em claro" "ausente" "(presente — valor não impresso)"; else ok "log sem email em claro após cadastro/login/falha"; fi
  if grep -q "pw-$RUN" "$APP_LOG_FILE"; then bad "log sem senha" "ausente" "(presente)"; else ok "log sem senha"; fi
else
  skip "log sem email em claro" "APP_LOG_FILE não informado"
fi

# =================================================================
echo; echo "== T8. Operações destrutivas"
# titular descartável com pedido; exclusão desvincula pedidos e apaga o usuário
req -X POST "$BASE/usuarios" "${H_JSON[@]}" -d "{\"nome\":\"Apagar $RUN\",\"email\":\"del$RUN@ex.com\",\"senha\":\"pw2-$RUN\"}"
DU="$(printf '%s' "$BODY" | json dados id)"
login_token "del$RUN@ex.com" "pw2-$RUN"; TD="$TOKEN"
req -X POST "$BASE/pedidos" "${H_JSON[@]}" -H "$(auth "$TD")" -d "{\"usuario_id\":$DU,\"itens\":[{\"produto_id\":$P1,\"quantidade\":1}]}"
DPED="$(printf '%s' "$BODY" | json dados pedido_id)"
check "DELETE /usuarios/<int:id>" 200 "titular apaga a própria conta" -X DELETE -H "$(auth "$TD")" "$BASE/usuarios/$DU"
check "GET /usuarios/<int:id>" 404 "usuário apagado" "${AH[@]}" "$BASE/usuarios/$DU"
check "DELETE /usuarios/<int:id>" 404 "apagar duas vezes (admin)" -X DELETE "${AH[@]}" "$BASE/usuarios/$DU"
check_db "0" "nenhum registro aponta para o usuário apagado" "SELECT (SELECT COUNT(*) FROM usuarios WHERE id=$DU)+(SELECT COUNT(*) FROM pedidos WHERE usuario_id=$DU)"
check_db "1" "pedido mantido e desvinculado (usuario_id NULL)" "SELECT COUNT(*) FROM pedidos WHERE id=$DPED AND usuario_id IS NULL"
check_db "0" "email do apagado não está no banco" "SELECT COUNT(*) FROM usuarios WHERE email='del$RUN@ex.com'"
# reset total — por último
check "POST /admin/reset-db" 200 "admin reseta o banco" -X POST "${AH[@]}" "$BASE/admin/reset-db"
check_db "0|0|0|0" "todas as tabelas vazias" "SELECT (SELECT COUNT(*) FROM produtos)||'|'||(SELECT COUNT(*) FROM usuarios)||'|'||(SELECT COUNT(*) FROM pedidos)||'|'||(SELECT COUNT(*) FROM itens_pedido)"
check "GET /relatorios/vendas" 200 "relatório sobre banco vazio" "${AH[@]}" "$BASE/relatorios/vendas"
check_equal "0|0|0" "$(printf '%s' "$BODY" | python3 -c 'import sys,json; d=json.load(sys.stdin)["dados"]; print("|".join(str(d[k]) for k in ("total_pedidos","faturamento_bruto","ticket_medio")))')" "relatório zerado, não null"
check "GET /produtos" 200 "lista vazia" "$BASE/produtos"
check_equal "[]" "$(printf '%s' "$BODY" | json dados)" "produtos vazio"

# =================================================================
EXN="$(sort -u "$EXERCISED" | wc -l | tr -d ' ')"
TOTAL=$((PASS+FAIL))
echo
echo "=================================================="
echo "TOTAL: $TOTAL checks | failures: $FAIL | skipped: $SKIP"
echo "Coverage: $INVENTORY endpoints inventoried / $EXN exercised"
echo "=================================================="
rm -f "$EXERCISED"
if [ "$EXN" != "$INVENTORY" ]; then echo "Cobertura incompleta"; exit 1; fi
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
