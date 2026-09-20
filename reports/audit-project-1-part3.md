```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project (Loja API)
Stack:   Python / Flask 3.1.1
Files:   16 analyzed | ~931 lines of code

## Resolved since audit-project-1-part2.md
"Admin Controller Bypasses the Model Layer" (HIGH) is resolved: `models/admin_model.py` now
exposes `reset_database()`/`executar_query()`, and `controllers/admin_controller.py` calls only
those, matching every other controller's convention.
"Pagination Parsing Duplicated Across Three Controllers" (HIGH) is resolved: `utils/pagination.py`
now provides one `parse_pagination()` helper, used identically by product_controller,
order_controller, and user_controller.
"N+1 Query Pattern When Creating an Order" (MEDIUM) is resolved: `models/order_model.py:62-65`
now fetches all `produto_id`s in a single `WHERE id IN (...)` query before the validation loop.
"Missing Pagination on Product Search Endpoint" (MEDIUM) is resolved: `models/product_model.py`'s
`buscar()` now accepts `page`/`per_page` and applies `LIMIT ? OFFSET ?` (lines 100-102), and
`controllers/product_controller.py:101` passes them through via `parse_pagination()`.
"Magic Discount Thresholds Hardcoded in Sales Report" (LOW) is resolved: the tiers/rates now live
in `config/settings.py` as `FAIXAS_DESCONTO_FATURAMENTO`, consumed by `order_model.relatorio_vendas()`.

Still open (reappeared, partially fixed):
- "Admin Query Endpoint Still Executes Arbitrary Client-Supplied SQL" — `executar_query()` now
  rejects any statement that doesn't start with `SELECT` (models/admin_model.py:17-18), closing
  off destructive writes, but it still passes a raw client-supplied string straight into
  `cursor.execute(query)` with zero parameterization or table/column allow-list. Carried into
  this report's CRITICAL finding below rather than counted as new.
- "`id` Parameter Shadows Python Builtin" — fully fixed in `product_controller`/product routes
  (now `produto_id` everywhere), but the same pattern is still present in
  `controllers/user_controller.py:20` (`buscar_por_id(id)`) and `routes/routes.py:29`
  (`/usuarios/<int:id>`), which the previous report's finding did not cover. Carried into this
  report's LOW finding below.

## Summary
CRITICAL: 1 | HIGH: 0 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] Admin Query Endpoint Still Executes Unparameterized Client-Supplied SQL
File: models/admin_model.py:16-24; controllers/admin_controller.py:16-28
Description: `executar_query()` restricts the client-supplied `sql` string to ones starting with `SELECT`, but still executes that string verbatim via `cursor.execute(query)` with no parameterization, no column/table allow-list, and no limit on which tables or columns can be read.
Impact: any caller holding a valid `X-Admin-Token` can run `SELECT senha FROM usuarios` or `SELECT * FROM sqlite_master` to dump password hashes or the full schema in one request — the write-side risk is closed, but arbitrary read/exfiltration of any table (including fields the rest of the API deliberately hides, like `senha`) remains live.
Recommendation: AP-01 — remove the raw-SQL endpoint entirely and replace it with specific, parameterized admin read operations (e.g. named report functions); a client-supplied SQL string should never reach `cursor.execute`, even read-only and even behind authentication. See RP-01.

### [MEDIUM] Missing Pagination on Per-User Order History Endpoint
File: models/order_model.py:51-55 (get_por_usuario); controllers/order_controller.py:44-49 (listar_por_usuario)
Description: `GET /pedidos/usuario/<usuario_id>` calls `get_por_usuario()`, which runs `SELECT * FROM pedidos WHERE usuario_id = ?` with no `LIMIT`/`OFFSET`, unlike `GET /pedidos` (`listar_todos`), which already paginates via the same file's `get_todos()`.
Impact: a long-lived customer's full order history — and every hydrated line item in it — is returned in one response with no bound, growing unbounded with account age.
Recommendation: AP-09 — accept `page`/`per_page` via the existing `parse_pagination()` helper and translate to `LIMIT ? OFFSET ?`, mirroring `get_todos()`.

### [MEDIUM] Required-Field Validation Duplicated Between Create and Update
File: controllers/product_controller.py:37-39 (criar) and 65-67 (atualizar)
Description: both handlers implement the identical `for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")): if campo not in dados: return jsonify(...)` block inline instead of calling one shared helper.
Impact: the two copies already agree today, but any future change to the required-field list or its messaging must be remembered in both places or the two endpoints will silently disagree about what's mandatory.
Recommendation: AP-06 — extract a small `_validar_campos_obrigatorios(dados)` helper (in the controller or `models/product_model.py`) and call it from both `criar` and `atualizar`.

### [LOW] `id` Parameter Shadows Python Builtin in User Controller
File: controllers/user_controller.py:20-27 (buscar_por_id); routes/routes.py:29
Description: `buscar_por_id(id)` names its parameter `id`, shadowing Python's built-in `id()` for the function's scope, while the equivalent product/order handlers use `produto_id`/`pedido_id`/`usuario_id`.
Impact: purely a readability/consistency issue today, but it's a landmine for anyone who later needs `id()` inside this function, and it's now the only inconsistent spot in the codebase after the product controller was already fixed.
Recommendation: AP-15 — rename the parameter to `usuario_id` in both the route definition and the controller function, matching every other handler.

### [LOW] Magic Length Thresholds in Product Name Validation
File: models/product_model.py:23-26 (_validar_campos)
Description: the minimum (`2`) and maximum (`200`) product name lengths are literal numbers embedded directly in the validation function, the same pattern already fixed elsewhere in this file (`PRODUTO_CATEGORIAS_VALIDAS` lives in `config/settings.py`) and in `order_model.py` (`FAIXAS_DESCONTO_FATURAMENTO`).
Impact: changing the allowed name-length range requires a source edit and redeploy instead of a configuration change, inconsistent with how every other business rule in this file is now sourced.
Recommendation: AP-13 — move `NOME_PRODUTO_MIN_LEN`/`NOME_PRODUTO_MAX_LEN` into `config/settings.py` alongside `PRODUTO_CATEGORIAS_VALIDAS`.

================================
Total: 5 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
