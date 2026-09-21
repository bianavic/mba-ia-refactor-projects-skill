#!/usr/bin/env bash
# Suite de testes manuais do code-smells-project (Loja API).
# Pré-requisito: python app.py (servidor em :5000, schema + seed criados automaticamente no boot:
#   10 produtos, e usuarios admin@loja.com/admin123, joao@email.com/123456, maria@email.com/senha123)
# Rode o arquivo inteiro com `bash manual-tests.sh`, ou copie/cole seções uma de cada vez.

BASE=http://localhost:5000

echo "=================================================="
echo "APP"
echo "=================================================="

echo "--- GET / ---"
curl -s "$BASE/" | python3 -m json.tool

echo "--- GET /health (não deve conter secret_key/debug no corpo) ---"
curl -s "$BASE/health" | python3 -m json.tool

echo "=================================================="
echo "PRODUTOS"
echo "=================================================="

echo "--- GET /produtos ---"
curl -s "$BASE/produtos" | python3 -m json.tool

echo "--- GET /produtos?page=1&per_page=5 (paginação) ---"
curl -s "$BASE/produtos?page=1&per_page=5" | python3 -m json.tool

echo "--- GET /produtos/busca?q=notebook ---"
curl -s "$BASE/produtos/busca?q=notebook" | python3 -m json.tool

echo "--- GET /produtos/busca?categoria=informatica&preco_min=100&preco_max=1000 ---"
curl -s "$BASE/produtos/busca?categoria=informatica&preco_min=100&preco_max=1000" | python3 -m json.tool

echo "--- GET /produtos/1 ---"
curl -s "$BASE/produtos/1" | python3 -m json.tool

echo "--- GET /produtos/9999 (esperado 404) ---"
curl -s "$BASE/produtos/9999" | python3 -m json.tool

echo "--- POST /produtos (cria produto novo, guarde o id retornado) ---"
curl -s -X POST "$BASE/produtos" -H "Content-Type: application/json" \
  -d '{"nome":"Produto Teste","descricao":"criado via curl","preco":49.90,"estoque":100,"categoria":"geral"}' | python3 -m json.tool

echo "--- POST /produtos (categoria inválida, esperado 400) ---"
curl -s -X POST "$BASE/produtos" -H "Content-Type: application/json" \
  -d '{"nome":"Invalido","preco":10,"estoque":1,"categoria":"inexistente"}' | python3 -m json.tool

echo "--- POST /produtos (preço negativo, esperado 400) ---"
curl -s -X POST "$BASE/produtos" -H "Content-Type: application/json" \
  -d '{"nome":"Preco Negativo","preco":-10,"estoque":1,"categoria":"geral"}' | python3 -m json.tool

echo "--- PUT /produtos/<id> (ajuste <id> para o retornado no POST acima) ---"
curl -s -X PUT "$BASE/produtos/11" -H "Content-Type: application/json" \
  -d '{"nome":"Produto Teste Atualizado","descricao":"atualizado via curl","preco":59.90,"estoque":80,"categoria":"geral"}' | python3 -m json.tool

echo "--- DELETE /produtos/<id> (remove o produto criado acima) ---"
curl -s -X DELETE "$BASE/produtos/11" | python3 -m json.tool

echo "=================================================="
echo "USUARIOS"
echo "=================================================="

echo "--- GET /usuarios (senha/hash não deve aparecer em nenhum item) ---"
curl -s "$BASE/usuarios" | python3 -m json.tool

echo "--- GET /usuarios/1 ---"
curl -s "$BASE/usuarios/1" | python3 -m json.tool

echo "--- GET /usuarios/9999 (esperado 404) ---"
curl -s "$BASE/usuarios/9999" | python3 -m json.tool

echo "--- POST /usuarios (cria usuário novo, guarde o id retornado) ---"
curl -s -X POST "$BASE/usuarios" -H "Content-Type: application/json" \
  -d '{"nome":"Usuario Teste","email":"teste@ex.com","senha":"123456"}' | python3 -m json.tool

echo "--- POST /usuarios (campo obrigatório faltando, esperado 400) ---"
curl -s -X POST "$BASE/usuarios" -H "Content-Type: application/json" \
  -d '{"nome":"Sem Email"}' | python3 -m json.tool

echo "--- POST /login (credenciais válidas do seed) ---"
curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","senha":"123456"}' | python3 -m json.tool

echo "--- POST /login (senha errada, esperado 401) ---"
curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","senha":"errada"}' | python3 -m json.tool

echo "--- POST /login (tentativa de SQL injection no login, não deve autenticar) ---"
curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR '1'='1\",\"senha\":\"' OR '1'='1\"}" | python3 -m json.tool

echo "=================================================="
echo "PEDIDOS"
echo "=================================================="

echo "--- POST /pedidos (cria pedido novo com produtos 1 e 2, guarde o id retornado) ---"
curl -s -X POST "$BASE/pedidos" -H "Content-Type: application/json" \
  -d '{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":1},{"produto_id":2,"quantidade":2}]}' | python3 -m json.tool

echo "--- POST /pedidos (produto inexistente, esperado erro de negócio) ---"
curl -s -X POST "$BASE/pedidos" -H "Content-Type: application/json" \
  -d '{"usuario_id":2,"itens":[{"produto_id":9999,"quantidade":1}]}' | python3 -m json.tool

echo "--- POST /pedidos (estoque insuficiente, esperado erro de negócio) ---"
curl -s -X POST "$BASE/pedidos" -H "Content-Type: application/json" \
  -d '{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":999999}]}' | python3 -m json.tool

echo "--- GET /pedidos (paginado) ---"
curl -s "$BASE/pedidos?page=1&per_page=5" | python3 -m json.tool

echo "--- GET /pedidos/usuario/2 ---"
curl -s "$BASE/pedidos/usuario/2" | python3 -m json.tool

echo "--- PUT /pedidos/<id>/status (ajuste <id> para o pedido criado acima) ---"
curl -s -X PUT "$BASE/pedidos/1/status" -H "Content-Type: application/json" \
  -d '{"status":"aprovado"}' | python3 -m json.tool

echo "--- PUT /pedidos/<id>/status (status inválido, esperado 400) ---"
curl -s -X PUT "$BASE/pedidos/1/status" -H "Content-Type: application/json" \
  -d '{"status":"status-invalido"}' | python3 -m json.tool

echo "=================================================="
echo "RELATORIOS"
echo "=================================================="

echo "--- GET /relatorios/vendas ---"
curl -s "$BASE/relatorios/vendas" | python3 -m json.tool

echo "=================================================="
echo "ADMIN (desabilitado por padrão - sem ADMIN_TOKEN no ambiente)"
echo "=================================================="

echo "--- POST /admin/query sem ADMIN_TOKEN (esperado 403, endpoints desabilitados) ---"
curl -s -X POST "$BASE/admin/query" -H "Content-Type: application/json" \
  -d '{"tabela":"produtos"}' | python3 -m json.tool

echo "--- POST /admin/reset-db sem ADMIN_TOKEN (esperado 403) ---"
curl -s -X POST "$BASE/admin/reset-db" | python3 -m json.tool

echo "--- (opcional) com ADMIN_TOKEN definido no servidor (export ADMIN_TOKEN=algum-token antes de subir o app): ---"
echo "--- POST /admin/query sem header (esperado 401, token ausente) ---"
curl -s -X POST "$BASE/admin/query" -H "Content-Type: application/json" \
  -d '{"tabela":"produtos"}' | python3 -m json.tool

echo "--- POST /admin/query com header correto (ajuste <ADMIN_TOKEN> para o valor real; tabela só aceita nomes da allow-list) ---"
curl -s -X POST "$BASE/admin/query" -H "Content-Type: application/json" -H "X-Admin-Token: <ADMIN_TOKEN>" \
  -d '{"tabela":"produtos"}' | python3 -m json.tool

echo "--- POST /admin/query com tabela inválida (esperado 400, nunca executa SQL arbitrário) ---"
curl -s -X POST "$BASE/admin/query" -H "Content-Type: application/json" -H "X-Admin-Token: <ADMIN_TOKEN>" \
  -d '{"tabela":"sqlite_master"}' | python3 -m json.tool
