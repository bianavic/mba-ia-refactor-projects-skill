#!/usr/bin/env bash
# Manual test suite for task-manager-api (all 22 endpoints).
# Prereq: python seed.py && python app.py  (server on :5000)
# Run whole file with `bash manual-tests.sh`, or copy/paste sections one at a time.

BASE=http://localhost:5000

echo "=================================================="
echo "APP"
echo "=================================================="

echo "--- GET / ---"
curl -s "$BASE/" | python3 -m json.tool

echo "--- GET /health ---"
curl -s "$BASE/health" | python3 -m json.tool

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

echo "--- PUT /users/<id> (ajuste <id> para o retornado no POST acima) ---"
curl -s -X PUT "$BASE/users/4" -H "Content-Type: application/json" \
  -d '{"name":"Ana Costa Silva"}' | python3 -m json.tool

echo "--- POST /login (credenciais válidas do seed; token deve ser assinado, não 'fake-jwt-token-<id>') ---"
curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -m json.tool

echo "--- POST /login (senha errada, esperado 401) ---"
curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"errada"}' | python3 -m json.tool

echo "--- DELETE /users/<id> (remove o usuário criado acima, não um do seed) ---"
curl -s -X DELETE "$BASE/users/4" | python3 -m json.tool

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
curl -s -X POST "$BASE/tasks" -H "Content-Type: application/json" \
  -d '{"title":"Nova task de teste","description":"criada via curl","status":"pending","priority":2,"user_id":1,"category_id":1,"due_date":"2026-12-01","tags":["teste","curl"]}' | python3 -m json.tool

echo "--- POST /tasks (título curto, esperado 400) ---"
curl -s -X POST "$BASE/tasks" -H "Content-Type: application/json" \
  -d '{"title":"ab"}' | python3 -m json.tool

echo "--- PUT /tasks/<id> (ajuste <id> para o retornado no POST acima) ---"
curl -s -X PUT "$BASE/tasks/11" -H "Content-Type: application/json" \
  -d '{"status":"in_progress","priority":1}' | python3 -m json.tool

echo "--- DELETE /tasks/<id> (remove a task criada acima) ---"
curl -s -X DELETE "$BASE/tasks/11" | python3 -m json.tool

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
curl -s -X POST "$BASE/categories" -H "Content-Type: application/json" \
  -d '{"name":"QA","description":"Testes","color":"#9b59b6"}' | python3 -m json.tool

echo "--- PUT /categories/<id> (ajuste <id> para o retornado no POST acima) ---"
curl -s -X PUT "$BASE/categories/5" -H "Content-Type: application/json" \
  -d '{"description":"Testes manuais e automatizados"}' | python3 -m json.tool

echo "--- DELETE /categories/<id> (remove a categoria criada acima) ---"
curl -s -X DELETE "$BASE/categories/5" | python3 -m json.tool
