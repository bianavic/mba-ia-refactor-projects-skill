```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project (Loja API)
Stack:   Python / Flask 3.1.1
Files:   14 analyzed | ~896 lines of code

## Resolved since audit-project-1.md
All CRITICAL findings except one are resolved: queries are now parameterized everywhere
(models/order_model.py, models/product_model.py, models/user_model.py use `?` placeholders);
SECRET_KEY/DB_PATH/HOST/PORT are env-driven via config/settings.py with DEBUG defaulting to
false, and GET /health no longer echoes secret_key/debug; passwords are hashed with
werkzeug.security.generate_password_hash/check_password_hash and models/user_model.py's
_to_dict() excludes the `senha` field everywhere (list, detail, login).
Also resolved: the "Business Logic Duplicated" HIGH finding (order-item hydration is now one
shared `_hydrate_pedidos()` in models/order_model.py; product field validation is one shared
`_validar_campos()` in models/product_model.py used by both criar and atualizar); the "Global
Mutable Database Connection" HIGH finding (models/db.py now uses flask.g + teardown_appcontext
instead of a module-level global); the N+1 query pattern in order listing (get_todos/
get_por_usuario now use `_hydrate_pedidos()`'s single `WHERE id IN (...)` query instead of a
per-item lookup); print-based logging (the whole codebase now uses the `logging` module); and
the unused imports (database.py's unused `os`, models.py's unused `sqlite3` — both files no
longer exist in this form, and no unused imports were found in the current codebase).

Still open (reappeared, partially fixed):
- "Unauthenticated Arbitrary SQL Execution Endpoint" — POST /admin/query is now gated behind
  `requer_admin` (middlewares/auth.py), fixing the "unauthenticated" half, but it still accepts
  and executes a raw client-supplied SQL string with zero parameterization or restriction,
  which the original recommendation explicitly said never to expose over HTTP. Carried into
  this report's CRITICAL finding below rather than counted as new.
- "Routes Bypass Controller/Model Layers Entirely" — reset_database/executar_query moved out of
  app.py into controllers/admin_controller.py, but that controller still calls
  `models.db.get_db()` and raw cursor methods itself instead of delegating to a model, unlike
  every other controller in the project. Carried into this report's HIGH finding below.
- "Missing Pagination on List Endpoints" — GET /produtos, /usuarios, and /pedidos are now
  paginated, but the newer GET /produtos/busca endpoint (added since the last audit) returns
  the entire filtered result set unpaginated. Carried into this report's MEDIUM findings below.
- "Hardcoded Configuration / Magic Values" — product categories, order statuses, DB path, and
  host/port all moved into config/settings.py, but the sales-report discount tiers/rates are a
  new instance of the same pattern the previous audit didn't cover. Carried into this report's
  LOW findings below.

## Summary
CRITICAL: 1 | HIGH: 2 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] Admin Query Endpoint Still Executes Arbitrary Client-Supplied SQL
File: controllers/admin_controller.py:22-39
Description: `executar_query()` takes a raw `sql` string straight from the JSON request body and passes it directly to `cursor.execute(query)` with no parameterization, no statement allow-list, and no restriction beyond branching on whether it starts with `SELECT`.
Impact: any caller holding a valid `X-Admin-Token` (e.g. leaked, guessed, or obtained via a separate compromise) can run arbitrary SQL — `DROP TABLE`, bulk exfiltration, or destructive writes — against the live database in one request.
Recommendation: AP-01 — remove the raw-SQL endpoint and replace it with specific, parameterized admin operations; a client-supplied SQL string should never reach `cursor.execute` even behind authentication. See RP-01.

### [HIGH] Admin Controller Bypasses the Model Layer, Touching Persistence Directly
File: controllers/admin_controller.py:1-39 (reset_database, executar_query)
Description: this controller imports `models.db.get_db` directly and issues raw `cursor.execute`/`commit()` calls itself, unlike order_controller, product_controller, user_controller, and system_controller, all of which only ever call a `*_model` function and never touch `models.db`.
Impact: the admin endpoints cannot be unit-tested without a live database and sit outside the Controller→Model convention the rest of the app follows, making them the one place a future change to the persistence layer (e.g. switching drivers, adding a query-logging wrapper) would be silently missed.
Recommendation: AP-16 — add `models/admin_model.py` exposing `reset_database()`/`run_query()`-style functions and have the controller call those, matching every other domain. See RP-14.

### [HIGH] Pagination Parsing Duplicated Across Three Controllers
File: controllers/product_controller.py:11-14 (_paginacao); controllers/order_controller.py:53-54; controllers/user_controller.py:13-14
Description: the same `page = int(request.args.get("page", DEFAULT_PAGE))` / `per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))` logic is implemented three separate times instead of being shared — only product_controller even extracted it into a local helper.
Impact: the copies have already diverged in form (helper vs. inline); a future rule (e.g. clamping `per_page` to a max, rejecting non-numeric input) must be remembered in three places or the endpoints will silently disagree on pagination behavior.
Recommendation: AP-06 — extract one shared pagination helper (e.g. a small `utils/pagination.py`) and call it from all three controllers. See RP-04.

### [MEDIUM] N+1 Query Pattern When Creating an Order
File: models/order_model.py:57-71 (criar)
Description: `criar()` loops over the submitted `itens` and issues one `SELECT * FROM produtos WHERE id = ?` per item to validate stock/price, instead of a single `WHERE id IN (...)` query — the same pattern `_hydrate_pedidos()` already uses two functions above in the same file.
Impact: placing an order with M distinct products costs M sequential product lookups instead of one, growing linearly with basket size.
Recommendation: AP-08 — fetch all `produto_id`s in one `IN (...)` query before the loop, mirroring `_hydrate_pedidos()`. See RP-06.

### [MEDIUM] Missing Pagination on Product Search Endpoint
File: models/product_model.py:80-101 (buscar); controllers/product_controller.py:101-116 (buscar)
Description: `/produtos/busca` builds a dynamic filter query (name/description/category/price range) but returns every matching row with no `limit`/`offset`, unlike `/produtos` (listar), which already paginates via the same model file's `get_todos()`.
Impact: a broad or empty search term returns the entire product table in a single response; cost grows unbounded with catalog size.
Recommendation: AP-09 — accept `page`/`per_page` and translate to `LIMIT ? OFFSET ?` the same way `get_todos()` already does. See RP-07.

### [LOW] Magic Discount Thresholds Hardcoded in Sales Report
File: models/order_model.py:122-128 (relatorio_vendas)
Description: the discount tiers (`10000`, `5000`, `1000` revenue thresholds) and their rates (`0.1`, `0.05`, `0.02`) are literal numbers embedded directly in the function body.
Impact: changing a discount tier or rate requires a source edit and redeploy instead of a configuration change, same as the categories/statuses that were already centralized in config/settings.py.
Recommendation: AP-13 — move these thresholds/rates into config/settings.py alongside `PRODUTO_CATEGORIAS_VALIDAS`/`PEDIDO_STATUS_VALIDOS`. See RP-10.

### [LOW] `id` Parameter Shadows Python Builtin
File: controllers/product_controller.py:28, 63, 90 (buscar_por_id, atualizar, deletar); routes/routes.py:17, 19, 20 (`<int:id>`)
Description: three handlers name their parameter `id`, shadowing Python's built-in `id()` function for the scope of each function, while every other resource in the codebase uses a descriptive name (`usuario_id`, `pedido_id`).
Impact: purely a readability/consistency issue today, but it's a landmine for anyone who later needs `id()` inside these functions, and it's inconsistent with the naming convention used everywhere else in the project.
Recommendation: AP-15 — rename the parameter to `produto_id` in both the route definitions and the controller functions. See RP-11.

================================
Total: 7 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
