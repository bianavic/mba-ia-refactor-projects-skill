```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project (Loja API)
Stack:   Python / Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 2 | LOW: 4

## Findings

### [CRITICAL] SQL Injection via String-Concatenated Queries
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140-166, 174-192, 206-224, 279-281, 291-297
Description: Nearly every query in `models.py` is built by concatenating raw request-controlled values (ids, names, search terms, emails, passwords) directly into SQL strings instead of using `?` placeholders — e.g. `"SELECT * FROM produtos WHERE id = " + str(id)` (line 28), `"...WHERE email = '" + email + "' AND senha = '" + senha + "'"` (lines 109-111), and the free-text search term at lines 291-297.
Impact: Any client can read, modify, or delete arbitrary rows, or bypass login entirely with a classic `' OR '1'='1` payload against the login query — full data-layer compromise through nearly every endpoint.
Recommendation: Parameterize every query with `?` placeholders and pass values as a tuple to `cursor.execute`. See AP-01 / RP-01.

### [CRITICAL] Unauthenticated Arbitrary SQL Execution Endpoint
File: app.py:59-78
Description: `POST /admin/query` takes a raw `sql` string from the request body and executes it directly against the database with no authentication, authorization, or validation of any kind; `POST /admin/reset-db` (lines 47-57) similarly wipes all four tables with no auth check.
Impact: Any anonymous caller can run arbitrary SQL (including `DROP TABLE`, mass exfiltration, or destructive writes) or wipe the entire database on demand — this is a live remote-code-execution-equivalent surface, not a theoretical one.
Recommendation: Delete these debug endpoints entirely before production, or gate them behind real authentication/authorization; never expose raw SQL execution over HTTP. See AP-01 / RP-01.

### [CRITICAL] Hardcoded Secret Key, Debug Mode, and Secret Leaked via API Response
File: app.py:7-8, 88; controllers.py:285-289
Description: `SECRET_KEY` is a hardcoded literal (app.py:7), `DEBUG`/`debug=True` is enabled (app.py:8, 88), and `health_check()` echoes the live `secret_key` and `debug` flag straight into the JSON response body (controllers.py:288-289) while also mislabeling the environment as `"ambiente": "producao"`.
Impact: The session-signing secret is committed to source control and additionally broadcast to any caller of `/health`, letting an attacker forge signed sessions/tokens; Flask's debug mode also exposes an interactive debugger/stack traces on error.
Recommendation: Move the secret to an environment variable, disable debug in production, and strip all secret/debug fields from any response body. See AP-02 / RP-02.

### [CRITICAL] Plaintext Password Storage and Leakage
File: models.py:72-103, 105-120, 122-131; controllers.py:128-144
Description: Passwords (`senha`) are stored in plain text on creation (models.py:122-131) and compared in plain text on login (models.py:105-111) — there is no hashing at all. `get_todos_usuarios()` and `get_usuario_por_id()` (models.py:72-103) include the raw `senha` field in every returned user dict, and `listar_usuarios`/`buscar_usuario` (controllers.py:128-144) return those dicts straight to the client.
Impact: Every list/detail call on `/usuarios` leaks every user's plaintext password over the network; a single response body is equivalent to a full credential breach.
Recommendation: Hash passwords with `werkzeug.security.generate_password_hash`/`check_password_hash` (or bcrypt/argon2) and exclude the password field from all serialized output. See AP-03 & AP-04 / RP-03.

### [HIGH] Routes Bypass Controller/Model Layers Entirely
File: app.py:47-78
Description: `reset_database()` and `executar_query()` are defined directly in `app.py` and talk to the database (`get_db()`, raw cursor calls) without going through `controllers.py` or `models.py` at all, unlike every other route in the file.
Impact: Two endpoints live entirely outside the project's own layering convention, making them impossible to test or secure consistently with the rest of the API, and setting a precedent for further layer bypassing as the app grows.
Recommendation: Move any legitimate admin operations into `models.py`/`controllers.py` following the existing pattern (or remove them, see the CRITICAL finding above). See AP-05 / RP-04.

### [HIGH] Business Logic Duplicated Across Functions
File: models.py:171-201 vs. 203-233; controllers.py:43-50 vs. 87-90
Description: `get_pedidos_usuario` and `get_todos_pedidos` (models.py) reimplement the identical item/product-name-fetching loop instead of sharing one helper; `criar_produto` and `atualizar_produto` (controllers.py) reimplement the same "preço/estoque não pode ser negativo" validation independently.
Impact: A fix or rule change (e.g. new validation rule, a change to how order items are joined) must be applied in every copy or the copies silently diverge — already showing signs of drift (only `criar_produto` validates name length/category, `atualizar_produto` does not).
Recommendation: Extract one shared model method for order-item hydration and one shared validation function for product fields. See AP-06 / RP-05.

### [HIGH] Global Mutable Database Connection
File: database.py:4, 8-9
Description: `db_connection` is a module-level global, lazily initialized and mutated via the `global` keyword inside `get_db()`, then reused across every request handler.
Impact: Under Flask's threaded dev server (or any multi-worker deployment), concurrent requests share one `sqlite3` connection object with no locking, risking race conditions and corrupted reads/writes as load increases.
Recommendation: Use Flask's app/request context (`flask.g` + `teardown_appcontext`) or a connection pool instead of a bare module global. See AP-07 / RP-06.

### [MEDIUM] N+1 Query Pattern When Loading Orders
File: models.py:187-199, 219-231
Description: Both `get_pedidos_usuario` and `get_todos_pedidos` loop over each order's items and, inside that loop, run a separate query per item to fetch the product name (`cursor3.execute("SELECT nome FROM produtos WHERE id = " + ...)`), instead of a single join or `WHERE id IN (...)`.
Impact: Listing N orders with M items each costs roughly N + N*M queries — response time degrades linearly with catalog activity, and this pattern is duplicated (see the HIGH duplication finding above).
Recommendation: Replace the nested per-item queries with one `JOIN` across `pedidos`, `itens_pedido`, and `produtos`. See AP-08 / RP-07.

### [MEDIUM] Missing Pagination on List Endpoints
File: controllers.py:5-12, 128-134, 229-235
Description: `listar_produtos`, `listar_usuarios`, and `listar_todos_pedidos` all fetch and return the entire table with no `limit`/`offset` or `page` parameters.
Impact: Response payload size and query cost grow unbounded with table size; combined with the N+1 finding above, `listar_todos_pedidos` is the worst-case compounding of both issues.
Recommendation: Add `page`/`per_page` query params and translate them to `LIMIT`/`OFFSET` in the corresponding model queries. See AP-09 / RP-08.

### [LOW] Print-Based Logging Instead of a Logging Framework
File: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 161, 179, 182, 208-210, 248, 250
Description: Operational events (server start, DB reset, errors, "emails/SMS/push sent") are logged via bare `print(...)` calls instead of Python's `logging` module.
Impact: No log levels, no timestamps, no way to filter or ship these to a log aggregator — effectively unusable once deployed beyond a local terminal.
Recommendation: Replace all `print` calls with a configured `logging` logger. See AP-12 / RP-09.

### [LOW] Hardcoded Configuration / Magic Values
File: controllers.py:52, 242; database.py:5; app.py:88
Description: The valid product categories list (controllers.py:52), the valid order-status list (controllers.py:242), the SQLite file path (database.py:5), and the server host/port (app.py:88) are all literal values embedded inline rather than sourced from configuration.
Impact: Changing a category, adding a status, or moving the DB file/port requires a source edit and redeploy instead of a config change.
Recommendation: Move these into a config module or environment variables. See AP-13 / RP-10.

### [LOW] Unused Imports
File: database.py:2; models.py:2
Description: `database.py` imports `os` and `models.py` imports `sqlite3`, but neither name is referenced anywhere else in its file.
Impact: Minor noise that misrepresents each file's actual dependencies to a reader.
Recommendation: Remove both unused imports. See AP-14 / RP-11.

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```
