#!/usr/bin/env bash
# Suite de testes manuais do task-manager-api (todos os 22 endpoints).
# Pré-requisito: python seed.py && python app.py  (servidor em :5000)
# Rode o arquivo inteiro com `bash manual-tests.sh`, ou copie/cole seções uma de cada vez.
#
# Leituras (GET) são públicas. Escritas exigem 'Authorization: Bearer <token>',
# obtido no POST /login abaixo — por isso o login acontece antes de tudo.

BASE=http://localhost:5000

get_token() {  # get_token <email> <senha>
  curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"$1\",\"password\":\"$2\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))"
}

# joao@email.com é admin no seed; maria@email.com é 'user' comum.
ADMIN_TOKEN=$(get_token joao@email.com 1234)
USER_TOKEN=$(get_token maria@email.com abcd)
AUTH_ADMIN=(-H "Authorization: Bearer $ADMIN_TOKEN")
AUTH_USER=(-H "Authorization: Bearer $USER_TOKEN")

echo "=================================================="
echo "AUTH (novo: escritas exigem token)"
echo "=================================================="

echo "--- token de admin obtido: ${ADMIN_TOKEN:0:24}... ---"
echo "--- token de user comum obtido: ${USER_TOKEN:0:24}... ---"

echo "--- POST /tasks SEM token (esperado 401) ---"
curl -s -w "\nHTTP %{http_code}\n" -X POST "$BASE/tasks" -H "Content-Type: application/json" \
  -d '{"title":"Task anonima"}'

echo "--- DELETE /users/1 SEM token (esperado 401) ---"
curl -s -w "\nHTTP %{http_code}\n" -X DELETE "$BASE/users/1"

echo "--- POST /tasks com token INVÁLIDO (esperado 401) ---"
curl -s -w "\nHTTP %{http_code}\n" -X POST "$BASE/tasks" \
  -H "Authorization: Bearer nao-e-um-token-valido" -H "Content-Type: application/json" \
  -d '{"title":"Task forjada"}'

echo "--- PUT /users/1 com token de OUTRO usuário (esperado 403) ---"
curl -s -w "\nHTTP %{http_code}\n" -X PUT "$BASE/users/1" "${AUTH_USER[@]}" \
  -H "Content-Type: application/json" -d '{"name":"Invadido"}'

echo "--- POST /users tentando virar admin sem ser admin (esperado 403) ---"
curl -s -w "\nHTTP %{http_code}\n" -X POST "$BASE/users" -H "Content-Type: application/json" \
  -d '{"name":"Mallory","email":"mallory@email.com","password":"1234","role":"admin"}'

echo "--- POST /categories com role 'user' comum (esperado 403) ---"
curl -s -w "\nHTTP %{http_code}\n" -X POST "$BASE/categories" "${AUTH_USER[@]}" \
  -H "Content-Type: application/json" -d '{"name":"Proibida"}'

echo "=================================================="
echo "APP"
echo "=================================================="

echo "--- GET / ---"
curl -s "$BASE/" | python3 -m json.tool

echo "--- GET /health ---"
curl -s "$BASE/health" | python3 -m json.tool

echo "--- GET /rota-inexistente (esperado 404 em JSON, via middlewares/error_handler.py) ---"
curl -s -w "\nHTTP %{http_code}\n" "$BASE/rota-inexistente"

echo "--- DELETE /health (método não suportado pela rota, esperado 405 em JSON) ---"
curl -s -w "\nHTTP %{http_code}\n" -X DELETE "$BASE/health"

echo "=================================================="
echo "USERS"
echo "=================================================="

echo "--- GET /users (senha não deve aparecer em nenhum item) ---"
curl -s "$BASE/users" | python3 -m json.tool

echo "--- GET /users/1 ---"
curl -s "$BASE/users/1" | python3 -m json.tool

echo "--- GET /users/1/tasks ---"
curl -s "$BASE/users/1/tasks" | python3 -m json.tool

echo "--- GET /users/9999 (esperado 404) ---"
curl -s "$BASE/users/9999" | python3 -m json.tool

echo "--- POST /users (cria usuário novo, guarde o id retornado) ---"
curl -s -X POST "$BASE/users" -H "Content-Type: application/json" \
  -d '{"name":"Ana Costa","email":"ana@email.com","password":"1234","role":"user"}' | python3 -m json.tool

echo "--- POST /users (email duplicado, esperado 409) ---"
curl -s -X POST "$BASE/users" -H "Content-Type: application/json" \
  -d '{"name":"Ana Duplicada","email":"ana@email.com","password":"1234"}' | python3 -m json.tool

echo "--- POST /users (senha curta, esperado 400) ---"
curl -s -X POST "$BASE/users" -H "Content-Type: application/json" \
  -d '{"name":"Curta","email":"curta@email.com","password":"12"}' | python3 -m json.tool

echo "--- PUT /users/<id> (admin altera o usuário criado acima) ---"
curl -s -X PUT "$BASE/users/4" "${AUTH_ADMIN[@]}" -H "Content-Type: application/json" \
  -d '{"name":"Ana Costa Silva"}' | python3 -m json.tool

echo "--- POST /login (credenciais válidas do seed; token deve ser assinado, não 'fake-jwt-token-<id>') ---"
curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -m json.tool

echo "--- POST /login (senha errada, esperado 401) ---"
curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"errada"}' | python3 -m json.tool

echo "--- DELETE /users/<id> (admin remove o usuário criado acima, não um do seed) ---"
curl -s -X DELETE "$BASE/users/4" "${AUTH_ADMIN[@]}" | python3 -m json.tool

echo "=================================================="
echo "TASKS"
echo "=================================================="

echo "--- GET /tasks?page=1&per_page=5 (paginação) ---"
curl -s "$BASE/tasks?page=1&per_page=5" | python3 -m json.tool

echo "--- GET /tasks/1 ---"
curl -s "$BASE/tasks/1" | python3 -m json.tool

echo "--- GET /tasks/9999 (esperado 404) ---"
curl -s "$BASE/tasks/9999" | python3 -m json.tool

echo "--- GET /tasks/search?q=bug&status=pending ---"
curl -s "$BASE/tasks/search?q=bug&status=pending" | python3 -m json.tool

echo "--- GET /tasks/stats ---"
curl -s "$BASE/tasks/stats" | python3 -m json.tool

echo "--- POST /tasks (cria task nova, guarde o id retornado) ---"
curl -s -X POST "$BASE/tasks" "${AUTH_ADMIN[@]}" -H "Content-Type: application/json" \
  -d '{"title":"Nova task de teste","description":"criada via curl","status":"pending","priority":2,"user_id":1,"category_id":1,"due_date":"2026-12-01","tags":["teste","curl"]}' | python3 -m json.tool

echo "--- POST /tasks (título curto, esperado 400) ---"
curl -s -X POST "$BASE/tasks" "${AUTH_ADMIN[@]}" -H "Content-Type: application/json" \
  -d '{"title":"ab"}' | python3 -m json.tool

echo "--- PUT /tasks/<id> (ajuste <id> para o retornado no POST acima) ---"
curl -s -X PUT "$BASE/tasks/11" "${AUTH_ADMIN[@]}" -H "Content-Type: application/json" \
  -d '{"status":"in_progress","priority":1}' | python3 -m json.tool

echo "--- DELETE /tasks/<id> (remove a task criada acima) ---"
curl -s -X DELETE "$BASE/tasks/11" "${AUTH_ADMIN[@]}" | python3 -m json.tool

echo "=================================================="
echo "REPORTS / CATEGORIES"
echo "=================================================="

echo "--- GET /reports/summary ---"
curl -s "$BASE/reports/summary" | python3 -m json.tool

echo "--- GET /reports/user/1 ---"
curl -s "$BASE/reports/user/1" | python3 -m json.tool

echo "--- GET /categories ---"
curl -s "$BASE/categories" | python3 -m json.tool

echo "--- POST /categories (cria categoria nova, guarde o id retornado) ---"
curl -s -X POST "$BASE/categories" "${AUTH_ADMIN[@]}" -H "Content-Type: application/json" \
  -d '{"name":"QA","description":"Testes","color":"#9b59b6"}' | python3 -m json.tool

echo "--- PUT /categories/<id> (ajuste <id> para o retornado no POST acima) ---"
curl -s -X PUT "$BASE/categories/5" "${AUTH_ADMIN[@]}" -H "Content-Type: application/json" \
  -d '{"description":"Testes manuais e automatizados"}' | python3 -m json.tool

echo "--- DELETE /categories/<id> (remove a categoria criada acima) ---"
curl -s -X DELETE "$BASE/categories/5" "${AUTH_ADMIN[@]}" | python3 -m json.tool
