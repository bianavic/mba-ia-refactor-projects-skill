#!/usr/bin/env bash
# Manual test suite for ecommerce-api-legacy (Frankenstein LMS).
# Prereq: npm install && npm start  (server on :3000)
# DB é em memória (sqlite ':memory:') e reseta a cada restart do processo, já
# seedada com: user id=1 (leonan@fullcycle.com.br), course id=1 "Clean Architecture" (997.00),
# course id=2 "Docker" (497.00), 1 matrícula/pagamento do user 1 no curso 1.
# Regra do gateway fake: cartão iniciando em "4" => PAID; qualquer outro prefixo => DENIED.
#
# IMPORTANTE: reinicie o servidor (Ctrl+C e `npm start` de novo) antes de rodar
# este script, e não rode duas vezes seguidas sem reiniciar. Os ids de
# enrollment/user e os valores do financial-report dependem do estado
# acumulado no banco em memória — qualquer checkout manual ou execução
# anterior deste script na mesma instância do servidor desloca os ids
# esperados (ex.: DELETE /api/users/3 deixaria de apontar para o usuário
# "Joao" criado no checkout recusado abaixo) e polui o relatório financeiro
# com dados de execuções passadas.
#
# Run whole file with `bash manual-tests.sh`, or copy/paste sections one at a time.

BASE=http://localhost:3000

echo "=================================================="
echo "CHECKOUT"
echo "=================================================="

echo "--- POST /api/checkout (sucesso - cartão começando em 4, cria usuário novo) ---"
curl -s -X POST "$BASE/api/checkout" -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
echo
echo "  -> conferir no terminal do servidor: o log de 'Processing payment' deve mostrar o cartão mascarado, nunca em texto plano"

echo "--- POST /api/checkout (pagamento recusado - cartão não começa em 4) ---"
curl -s -X POST "$BASE/api/checkout" -H "Content-Type: application/json" \
  -d '{"usr":"Joao","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
echo

echo "--- POST /api/checkout (usuário já existente - reutiliza o cadastro pelo email) ---"
curl -s -X POST "$BASE/api/checkout" -H "Content-Type: application/json" \
  -d '{"usr":"Leonan","eml":"leonan@fullcycle.com.br","pwd":"123","c_id":2,"card":"4222222233334444"}'
echo

echo "--- POST /api/checkout (curso inexistente, esperado 404) ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/api/checkout" -H "Content-Type: application/json" \
  -d '{"usr":"Ana","eml":"ana@teste.com","pwd":"123","c_id":9999,"card":"4111222233334444"}'

echo "--- POST /api/checkout (campo obrigatório faltando, esperado 400) ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/api/checkout" -H "Content-Type: application/json" \
  -d '{"usr":"SemCartao","eml":"semcartao@teste.com","c_id":1}'

echo "=================================================="
echo "FINANCIAL REPORT"
echo "=================================================="

echo "--- GET /api/admin/financial-report ---"
curl -s "$BASE/api/admin/financial-report" | python3 -m json.tool

echo "--- GET /api/admin/financial-report?page=1&per_page=1 (paginação) ---"
curl -s "$BASE/api/admin/financial-report?page=1&per_page=1" | python3 -m json.tool

echo "=================================================="
echo "USERS"
echo "=================================================="

echo "--- DELETE /api/users/3 (remove o usuário 'Joao', criado no checkout recusado acima; cascade em matrículas/pagamentos) ---"
curl -s -X DELETE "$BASE/api/users/3"
echo

echo "--- DELETE /api/users/9999 (id inexistente) ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X DELETE "$BASE/api/users/9999"
