================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.11.15 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 8 | HIGH: 3 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] SQL injection in every data-access function
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:149-150, models.py:155, models.py:157-161, models.py:163-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299
Description: Every query is built by string concatenation with request values (nome, descricao, categoria, email, senha, search term `q`, status, ids from the body) instead of bound parameters; `login_usuario` concatenates email and password straight into the WHERE clause.
Impact: Any anonymous caller can read, change or delete any table. `POST /login` with email `' OR 1=1 --` logs in as the first user (the seeded admin) without a password, and `GET /produtos/busca?q=` can dump `usuarios` including passwords.
Recommendation: AP-01 → parameterize every query, including the dynamic filters of `buscar_produtos` (see RP-01).

### [CRITICAL] Arbitrary SQL execution endpoint
File: app.py:59-78
Description: `POST /admin/query` passes the `sql` field of the request body to `cursor.execute` as the whole statement and commits anything that is not a SELECT, with no authentication.
Impact: Whoever reaches the port owns the database: reads every password, drops tables, rewrites orders. Parameterization cannot fix it, and authentication would only narrow who can do it.
Recommendation: AP-20 → take the capability off the request path while keeping the route (see RP-19, with RP-16).

### [CRITICAL] Hardcoded secrets, debug mode on, and secrets echoed by /health
File: app.py:7-8, app.py:88, controllers.py:285-289, database.py:75-79
Description: `SECRET_KEY` is a literal in source, and `DEBUG=True` plus `app.run(debug=True)` is bound to `0.0.0.0`. `GET /health` returns the secret key, the debug flag, the DB path and the environment name to anyone. The seed creates an `admin` account with the literal password `admin123` (plus two customers with literal passwords).
Impact: The signing key is in git and on the wire, so anything signed with it can be forged. The Werkzeug debugger is exposed on every interface. Anyone who reads the repo can log in as the seeded admin.
Recommendation: AP-02 → move the secret, debug flag and seed credentials to environment configuration, and remove the secrets from the /health body (see RP-02). Rotate the leaked key and the admin password: deleting them from the code does not un-leak them.

### [CRITICAL] Passwords stored and compared in plaintext
File: models.py:105-131, database.py:75-83
Description: `criar_usuario` inserts the password exactly as typed, the seed inserts literal passwords, and `login_usuario` compares the plaintext in SQL.
Impact: Anyone who reads the database (through AP-01, AP-20, a backup or a log) gets every user's real password, which is often reused on other services (personal data under LGPD art. 46 / GDPR art. 32).
Recommendation: AP-03 → salted hashing with werkzeug's `generate_password_hash`/`check_password_hash`, and migrate the plaintext rows already stored (see RP-09).

### [CRITICAL] Password field serialized in user responses
File: models.py:79-86, models.py:95-102, controllers.py:128-144
Description: `get_todos_usuarios` and `get_usuario_por_id` copy the `senha` column into the dict that `GET /usuarios` and `GET /usuarios/<id>` return.
Impact: One anonymous GET returns every user's password.
Recommendation: AP-04 (credentials) → build user responses from an explicit field list that never includes `senha` (see RP-09).

### [CRITICAL] Other users' personal data returned to anonymous callers
File: models.py:72-103, controllers.py:128-144, app.py:18-19
Description: `GET /usuarios` lists every user's name and full email, and `GET /usuarios/<id>` returns any user's name and email, to callers who are not that user.
Impact: Anyone on the network can harvest the full customer list (names and emails) in one request, for as long as the accounts exist (LGPD art. 6 III minimization; GDPR art. 5(1)(c)).
Recommendation: AP-04 (other people's personal data) → restrict the routes and mask identifiers for anyone other than their subject (see RP-09, RP-16). Data already stored is unchanged; only what is exposed changes.

### [CRITICAL] No authentication or authorization on any route
File: app.py:14-16, app.py:18-19, app.py:23-28, app.py:47-57, app.py:59-78
Description: No route has any auth check: product create/update/delete, user listing, order listing per user, order status change, the sales report, `/admin/reset-db` and `/admin/query` are all open. `POST /login` validates credentials but issues no token or session, so nothing can be verified afterwards.
Impact: Any caller can wipe the whole database (`POST /admin/reset-db`), change prices and stock, approve or cancel any order, read any customer's order history and read the revenue report.
Recommendation: AP-05 → have login issue a signed token and guard each route at the access level confirmed in Phase 2 (see RP-16). Re-check AP-17 afterwards.

### [CRITICAL] Routing code runs raw SQL past the data layer
File: app.py:47-78, controllers.py:264-274
Description: `app.py` registers the routes and also opens the connection and runs `DELETE`s and arbitrary statements itself. `health_check` in the controller runs `SELECT COUNT(*)` queries directly, although `models.py` exists as the data layer.
Impact: The separation is only nominal. Persistence changes have to be hunted through routes and controllers, and none of these flows can be tested without a real database.
Recommendation: AP-06 → move every query into models, give the admin and health flows controllers, and make `app.py` the composition root only (see RP-03, RP-14, RP-11).

### [HIGH] Duplicated validation and serialization that have already diverged
File: controllers.py:26-54, controllers.py:66-90, models.py:12-21, models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:178-199, models.py:211-231
Description: Product validation is copied into create and update. The update copy dropped the name-length and category checks, so `PUT /produtos/<id>` accepts a 1-character name or any category. The product, user and order row-to-dict serializers are each copied 2–3 times.
Impact: A rule fixed in one place stays broken in the other. The update path already stores data that create would reject.
Recommendation: AP-07 → one product validator shared by create and update, and one serializer per entity (see RP-04, RP-20).

### [HIGH] Single global database connection shared by all threads
File: database.py:4-11
Description: A module-level `db_connection` is opened once with `check_same_thread=False` and shared by every request thread of Flask's threaded server, with no lock and no teardown.
Impact: Concurrent requests share one cursor and transaction state: one request's commit or failure leaks into another's, and order creation (read stock → insert → decrement) can interleave and oversell.
Recommendation: AP-08 → one connection per request on `flask.g`, closed at app-context teardown (see RP-05).

### [HIGH] Multi-entity use case and external notifications outside a Service
File: models.py:133-169, controllers.py:188-220, controllers.py:237-255
Description: `models.criar_pedido` checks stock in `produtos`, inserts into `pedidos` and `itens_pedido` and decrements stock, so one model function spans three entities. The controllers decide side effects ("send email/SMS/push", "approved/cancelled" notifications) next to the response.
Impact: Order creation cannot be tested or reused without products, items and the notification channel. A second entry point (job, admin tool) would copy the whole flow.
Recommendation: AP-22 → an order Service that calls the product and order models in one transaction and owns the notifications (see RP-21).

### [MEDIUM] Supporting modules loose at the project root
File: controllers.py:1, models.py:1, database.py:1
Description: The controller, model and database modules live as single files at the project root next to the entry point instead of in role directories.
Impact: The layout does not show the layers, and every new module lands in the root.
Recommendation: AP-23 → group them in `controllers/`, `models/`, `database/` (and the new `routes/`, `services/`, `config/`, `errors/`, `middleware/`, `utils/`) (see RP-22).

### [MEDIUM] N+1 queries when listing orders and creating orders
File: models.py:187-199, models.py:219-231, models.py:139-141, models.py:154-156
Description: For each order, the listing runs one query for its items and then one per item for the product name (1 + N + N·M). Order creation queries each product twice, once in the stock-check loop and again in the insert loop.
Impact: `GET /pedidos` grows multiplicatively with orders × items and gets slower with every sale.
Recommendation: AP-09 → load items and product names with `IN (...)`/JOIN and group in memory; read each product once (see RP-06).

### [MEDIUM] List endpoints return whole tables without pagination
File: models.py:4-8, models.py:72-76, models.py:171-175, models.py:203-207, models.py:285-300
Description: `GET /produtos`, `/produtos/busca`, `/usuarios`, `/pedidos` and `/pedidos/usuario/<id>` return every matching row, with no limit/offset.
Impact: Response time and payload grow with the tables. One request can pull the whole catalog or every order.
Recommendation: AP-10 → `page`/`per_page` with a bounded size (see RP-07).

### [MEDIUM] Pinned dependencies with known advisories
File: requirements.txt:1-2
Description: `flask==3.1.1` is affected by GHSA-68rp-wp8r-4726 / CVE-2026-27205 (missing `Vary: Cookie`, fixed in 3.1.3). `flask-cors==5.0.1` is affected by GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4 and GHSA-8vgw-p6qm-5gr7 (case-sensitivity and regex path-matching flaws in CORS rules, fixed only in 6.0.0, a major version). The runtime has no project pin. The installed interpreter 3.11.15 is on the security-only 3.11 line (EOL 2027-10-31) and behind 3.11.18, whose 3.11.16–3.11.18 releases fix CVEs in ssl, tarfile, webbrowser and Expat, none of which this code calls.
Impact: The app ships known flaws. The Flask cookie flaw becomes reachable as soon as a session is used, and the CORS matching flaws apply to the `CORS(app)` policy covering every route.
Recommendation: AP-12 → bump Flask to 3.1.3 and decide on flask-cors 6.0.x (major); upgrade the interpreter to 3.11.18 (see RP-12).

### [MEDIUM] Personal data written to logs
File: controllers.py:161, controllers.py:179, controllers.py:182
Description: User creation and both login outcomes print the user's full email address to stdout.
Impact: Emails end up in log storage that is kept longer and is less access-controlled than the database. Failed logins also record which addresses were tried (LGPD art. 46 / GDPR art. 32).
Recommendation: AP-18 → log the user id or a masked email through one masking helper (see RP-17). Logs already written keep the full addresses until rotated.

### [MEDIUM] No erasure, export or retention for user personal data
File: app.py:18-21, models.py:72-131
Description: The domain stores names, emails and passwords of customers, but no path deletes a user or exports their data. Orders reference `usuario_id` with no de-link strategy, and no retention limit exists.
Impact: A customer who asks to be removed or to receive their data cannot be served, and their personal data is kept indefinitely (LGPD art. 18 II/V/VI, art. 16; GDPR art. 15, 17, 20, 5(1)(e)).
Recommendation: AP-19 → erasure that de-links orders and deletes the user in one transaction, plus an export; retention needs a policy (see RP-18).

### [MEDIUM] Missing input validation and raw exception text in 500 responses
File: controllers.py:10-12, controllers.py:21-22, controllers.py:43-50, controllers.py:60-62, controllers.py:87-90, controllers.py:95-96, controllers.py:108-109, controllers.py:118-121, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:169-171, controllers.py:185-186, controllers.py:195-203, controllers.py:218-220, controllers.py:226-227, controllers.py:234-235, controllers.py:239-240, controllers.py:254-255, controllers.py:261-262, controllers.py:291-292, app.py:61-62, app.py:77-78
Description: Types are never checked (`preco: "abc"` or `preco_min=abc` raises a TypeError/ValueError → 500), and a missing JSON body on `/login`, `/pedidos/<id>/status` and `/admin/query` crashes on `None.get` → 500. In orders, `usuario_id` is never checked to exist, item fields are unchecked (KeyError → 500), and a negative `quantidade` is accepted, which lowers the total and *increases* stock. Every handler returns `str(e)` to the client.
Impact: Client mistakes look like server failures, orders can point at users that do not exist, stock and revenue can be manipulated with negative quantities, and internal errors (SQL text, column names) are disclosed to any caller.
Recommendation: AP-21 → validate at the boundary with typed 400s and one central error handler with a generic 500 (see RP-20, RP-11).

### [LOW] print used for operational logging
File: controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250, app.py:56, app.py:83-86
Description: All operational and error output uses `print`.
Impact: No levels, timestamps or filtering, so errors can't be told apart from noise.
Recommendation: AP-13 → module-level `logging` loggers (see RP-08).

### [LOW] Hardcoded configuration and magic values
File: controllers.py:52, controllers.py:242, controllers.py:247-250, models.py:122, models.py:150, models.py:247, models.py:250, models.py:253, models.py:256-262, database.py:5, database.py:32, database.py:40, app.py:36, app.py:85, app.py:88, controllers.py:285-287
Description: The valid categories, order statuses (repeated as lone literals in SQL and the schema default), default user type, discount thresholds/rates, DB path, port, version and environment name are inline literals.
Impact: Changing a status, category or rate needs edits in several files, and the copies drift apart.
Recommendation: AP-14 → one config module, with values bound as parameters where they appear in SQL (see RP-13).

### [LOW] Unused imports
File: models.py:2, database.py:2
Description: `import sqlite3` in models.py and `import os` in database.py are never used.
Impact: They hide the modules' real dependencies.
Recommendation: AP-15 → remove them (see RP-13).

### [LOW] Inconsistent naming for the same operations
File: models.py:4, models.py:24, models.py:72, models.py:89, models.py:105, models.py:171, models.py:203, controllers.py:5, controllers.py:14, controllers.py:111
Description: Models mix English `get_` verbs (`get_todos_produtos`, `get_produto_por_id`, `get_pedidos_usuario`) with Portuguese verbs (`criar_`, `buscar_`, `deletar_`). The controllers use `listar_`/`buscar_` for the same reads, and `buscar_produto` (by id) sits next to `buscar_produtos` (search).
Impact: You can't predict a function's name from its role, which slows review and causes mistakes.
Recommendation: AP-16 → apply one convention to internal names only (`listar_`, `obter_..._por_id`, `buscar_` for search) (see RP-15).

================================
Total: 22 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
