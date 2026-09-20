```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   22 analyzed | ~1178 lines of code

## Resolved since audit-project-3-part2.md
Both HIGH findings of the previous part are resolved. AP-16: no route file touches
persistence any more — `routes/task_routes.py`, `routes/user_routes.py` and
`routes/report_routes.py` now only parse the request, make one call into
`controllers/task_controller.py`, `controllers/user_controller.py` or
`services/report_service.py`, and serialize the result (confirmed mechanically by
`./arch-check.sh`). The validation duplication is gone too: `create_task`/`update_task`
share `_validate_title/_validate_status/_validate_priority/_resolve_user/_resolve_category/
_apply_due_date` (controllers/task_controller.py:15-52), and `update_category` now has the
empty-body guard it was missing (services/report_service.py:194-195).
Also resolved: the N+1 pair in `get_users` (one grouped count query,
controllers/user_controller.py:26-30) and `delete_user` (single bulk delete,
controllers/user_controller.py:156); `GET /categories` pagination
(services/report_service.py:149); the `print()`-based `log_action` helper (deleted from
utils/helpers.py); and the hardcoded `'#000000'` / `3` defaults, which now come from
`DEFAULT_COLOR` (models/category.py:10) and `DEFAULT_PRIORITY` (models/task.py:22).

Still open, deliberately: the [LOW] "Inconsistent language" finding from part 2 (Portuguese
user-facing strings inside an English codebase) is unchanged and is not re-listed below.
Per RP-15's scope limit it stays unresolved on purpose — rewriting the messages would change
the response bodies the API already returns.

## Summary
CRITICAL: 0 | HIGH: 3 | MEDIUM: 4 | LOW: 4

## Findings

### [HIGH] No application factory — the entry point wires and creates the schema at import time
File: app.py:16-26 (module-level `app`, config, CORS, `db.init_app`, blueprint registration)
File: app.py:29-36 (`/health` and `/` defined in the entry point instead of a routes module)
File: app.py:39-40 (`with app.app_context(): db.create_all()` runs on import, not on startup)
File: tests/conftest.py:11-18 (a second Flask app, with its own duplicated config, exists only to avoid importing app.py)
File: seed.py:2 (`from app import app, db` — importing the seeder creates the schema as a side effect)
Description: The application object is a module-level global built at import time, and importing it also opens the configured database and issues `create_all()`. There is no factory function that takes a config and returns a configured app, so no caller can construct the app with different settings.
Impact: Any import of `app.py` — a test, the seeder, a management script — silently creates/touches the real database named by `DATABASE_URL`. The test suite had to work around this by hand-building its own Flask app, which duplicates `config/settings.py` and will drift from it; a config change (e.g. a new `SQLALCHEMY_ENGINE_OPTIONS`) is applied to production but not to tests, so tests stop exercising the real configuration.
Recommendation: See AP-05 / RP-03 — extract `create_app(config_object=Config)` that registers extensions, blueprints and error handlers, move `/health` and `/` into a routes module, move `db.create_all()` behind the `__main__` guard (or into the seeder), and rebuild `tests/conftest.py` on top of the factory.

### [HIGH] Task-status aggregation implemented three separate times
File: models/task.py:102-118 (`Task.get_statistics` — four `filter_by(status=...).count()` calls + overdue + completion_rate)
File: services/report_service.py:21-24 and 33-43 (`build_summary_report` — the same four status counts re-queried, overdue recomputed by iterating the whole table)
File: services/report_service.py:113-121 (`build_user_report` — the same four statuses counted a third time, as an `if/elif` chain in Python)
Description: `GET /tasks/stats`, `GET /reports/summary` and `GET /reports/user/<id>` each compute "how many tasks per status, how many overdue, what completion rate" with their own implementation — one via ORM counts on the model, one via ORM counts in the service, one by looping in Python.
Impact: The three copies have already diverged: `get_statistics` returns `completion_rate` over all tasks, `build_summary_report` returns no overall completion rate at all, and `build_user_report` derives its counts from objects already in memory. None of them is driven by `VALID_STATUSES` (utils/helpers.py:38), so adding a fifth status silently gives three different wrong answers on three endpoints instead of failing in one place.
Recommendation: See AP-06 / RP-04 — one `Task.status_breakdown(query=None)` classmethod that both the model-level stats and both report functions call, iterating `VALID_STATUSES` rather than naming each status.

### [HIGH] Login issues a token that nothing ever verifies; every write endpoint is anonymous
File: controllers/user_controller.py:18-19 (`_login_serializer`), 202-207 (`dumps` — the only serializer call in the project; there is no matching `loads`/`max_age` anywhere)
File: routes/user_routes.py:26-35 (`PUT /users/<id>`, `DELETE /users/<id>` — no authentication)
File: routes/task_routes.py:20-35 (`POST`/`PUT`/`DELETE /tasks` — no authentication)
File: routes/report_routes.py:25-40 (`POST`/`PUT`/`DELETE /categories` — no authentication)
File: config/settings.py:10 (`SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()` — a fresh per-process key whenever the variable is unset)
Description: `POST /login` checks the password and returns a signed `itsdangerous` token, but no code path ever reads a token back: there is no `loads`, no auth decorator, no `before_request` hook. The security layer stops at the login response. The `SECRET_KEY` fallback compounds it — with the variable unset, every process (and every gunicorn worker) signs with a different key, so a token is not even verifiable by the process next door.
Impact: Any anonymous client can promote a user to `admin` (`PUT /users/<id>` with `{"role": "admin"}`) or delete users, tasks and categories. The login endpoint gives the misleading impression that the API is protected, which is how an unauthenticated API reaches production.
Recommendation: See AP-10 / RP-10 — either wire the token into a `before_request`/decorator that calls `loads(..., max_age=...)` and enforce it on the write endpoints, or remove the token from the login response so the API does not advertise protection it does not have. **Not resolved in this Phase 3:** both directions change observable behavior (new 401s, or a changed login payload), which Phase 3 is not allowed to do. It needs an explicit product decision; the `SECRET_KEY` fallback is fixed as part of it only when that decision is made, since making it fail-fast today would break boot for anyone relying on the current default.

### [MEDIUM] Whole-table loads in the aggregation paths
File: models/task.py:108 (`sum(1 for t in cls.query.all() if t.is_overdue())`)
File: services/report_service.py:35 (`for t in Task.query.all()` — hydrates every task to build the overdue list)
File: services/report_service.py:60 (`for u in User.query.all()` — hydrates every user for the productivity block)
Description: After the counts were correctly turned into grouped queries in the previous round, three paths still pull entire tables into Python: the overdue computation runs `is_overdue()` per row in application code, and the per-user productivity loop iterates all users.
Impact: `GET /tasks/stats` and `GET /reports/summary` allocate one ORM object per row in the database on every request, with no limit — memory and latency grow linearly with table size and the endpoints get slower exactly as the dataset becomes worth reporting on.
Recommendation: See AP-08 / RP-06 — express "overdue" as a SQL predicate (`due_date < now AND status NOT IN ('done','cancelled')`) and count it with a single query; select only the columns the productivity block needs instead of full `User` entities.

### [MEDIUM] Request parameters are used without type validation, turning bad input into 500s
File: routes/task_routes.py:44-49 → models/task.py:95 (`int(priority)`) and models/task.py:97 (`int(user_id)`)
File: controllers/task_controller.py:86-87 → models/task.py:54-55 (`MIN_PRIORITY <= p <= MAX_PRIORITY` on an unconverted value)
File: middlewares/error_handler.py:14-17 (the generic handler that turns the resulting exception into 500)
Description: `GET /tasks/search` forwards `priority` and `user_id` to the model as raw strings and `Task.search` calls `int()` on them, so `?priority=abc` raises `ValueError`. `POST /tasks` with `{"priority": "2"}` reaches `Task.validate_priority` with a string, and `1 <= "2"` raises `TypeError`. Both are caught by the catch-all handler. `page`/`per_page` are the counter-example: the routes already coerce them with `type=int`.
Impact: Client mistakes are reported as `500 {"error": "Erro interno"}` instead of `400`, so a caller cannot tell a bad parameter from a server outage, and every occurrence writes a full stack trace to the error log as if it were an incident.
Recommendation: See AP-06 / RP-04 — coerce query parameters at the route boundary the same way `page`/`per_page` already are, and make `Task.validate_priority` reject non-integers instead of comparing them.

### [MEDIUM] Nested collections are returned unpaginated
File: controllers/user_controller.py:54-55 (`get_user` embeds every task of the user in the detail response)
File: controllers/user_controller.py:166-179 + routes/user_routes.py:38-40 (`GET /users/<id>/tasks` accepts no `page`/`per_page`)
File: services/report_service.py:34-43 (`GET /reports/summary` embeds an unbounded `overdue.tasks` list)
Description: `GET /tasks`, `GET /tasks/search`, `GET /users` and `GET /categories` all paginate, but the collections nested inside a user detail, the per-user task listing, and the overdue block of the summary report return every matching row.
Impact: The payload of `GET /users/<id>` and `GET /users/<id>/tasks` grows without bound for an active user, and `GET /reports/summary` grows with the backlog of overdue tasks — the case where the report is most needed is the case where it is slowest.
Recommendation: See AP-09 / RP-07 — apply the `.paginate(page=..., per_page=...)` pattern already used by `list_tasks`, and cap the embedded overdue list (or paginate it) in the summary report.

### [MEDIUM] CORS is opened to every origin and is the only setting not driven by configuration
File: app.py:19 (`CORS(app)`)
File: config/settings.py:9-15 (every other setting — secret, database, debug, host, port — reads from the environment)
Description: `CORS(app)` with no arguments sends `Access-Control-Allow-Origin: *` for every route, including the unauthenticated write endpoints. It is hardcoded in the entry point while the rest of the configuration was already extracted into `Config`.
Impact: The allowed origin list cannot be tightened for production without editing and redeploying source, which is exactly the coupling `config/settings.py` exists to remove; combined with the unauthenticated writes above, any page in any browser can call the write endpoints directly.
Recommendation: See AP-13 / RP-02 — add `CORS_ORIGINS` to `Config` (defaulting to `*` so current behavior is preserved) and pass it to `CORS(app, origins=...)`.

### [LOW] Dead helper functions and a dead model method
File: utils/helpers.py:9-12 (`format_date`), 21-24 (`sanitize_string`), 27-29 (`generate_id`), 32-35 (`is_valid_color`)
File: models/user.py:32-36 (`is_admin`)
Description: Five functions have zero call sites anywhere in the project (verified by grep across all `*.py` outside the skill copy). `is_admin` also spells `if x: return True else: return False` instead of returning the comparison, and hardcodes `'admin'` although `VALID_ROLES` exists.
Impact: `utils/helpers.py` reads as a utility library that the application depends on when in fact only `utc_now` and `calculate_percentage` are live; `is_admin` suggests a role check exists somewhere, reinforcing the false impression of an authorization layer (see the HIGH finding above).
Recommendation: See AP-10 / RP-10 — delete the four unused helpers; keep `is_admin` only if the authorization decision above wires it up, and then write it as `return self.role == 'admin'`.

### [LOW] Status literals hardcoded instead of using VALID_STATUSES
File: models/task.py:21 (`default='pending'`), 79 (`('done', 'cancelled')`), 104-107 (four literals)
File: controllers/task_controller.py:83 (`data.get('status', 'pending')`)
File: services/report_service.py:21-24, 48, 55, 114-120
File: models/user.py:33 (`'admin'`, while `VALID_ROLES` is defined at utils/helpers.py:39)
Description: `utils/helpers.py:38` centralizes the status vocabulary and the validation path imports it, but every default, filter and branch elsewhere re-spells the literal. This is the same class of finding as the `DEFAULT_COLOR`/`DEFAULT_PRIORITY` pair resolved last round, on a different set of values.
Impact: The status vocabulary now lives in eleven places instead of one; renaming or adding a status requires finding every literal by hand, and a missed one fails silently as a count that is always zero.
Recommendation: See AP-13 / RP-13 — expose the statuses as named constants (e.g. `STATUS_PENDING`, `CLOSED_STATUSES`) derived from `VALID_STATUSES` and import them wherever a status is written today.

### [LOW] requirements.txt does not match what the code imports
File: requirements.txt:4 (`marshmallow==3.20.1`), requirements.txt:5 (`requests==2.31.0`) — neither is imported anywhere
File: models/user.py:3, middlewares/error_handler.py:4 (`werkzeug`) and controllers/user_controller.py:5 (`itsdangerous`) — imported directly, declared nowhere
Description: Two pinned dependencies are unused (`marshmallow` appears only inside a seed string, seed.py:76), while two packages the code imports directly are present only as transitive dependencies of `flask==3.0.0`.
Impact: The unused pins keep two packages in every install and in the CVE surface for no benefit; the undeclared ones break the moment Flask changes its dependency set, and the failure is an `ImportError` at boot rather than a resolution error at install.
Recommendation: See AP-14 / RP-13 — drop `marshmallow` and `requests`, add `werkzeug` and `itsdangerous` with the versions Flask 3.0.0 already resolves.

### [LOW] `get_user_tasks` builds its response by deleting keys from another serializer's output
File: controllers/user_controller.py:174-177 (`for field in ('user_id', 'category_id', 'updated_at', 'tags'): del task_data[field]`)
Description: The endpoint calls `Task.to_dict()` and then removes four keys from the resulting dict instead of asking the model for the projection it wants.
Impact: The subtraction is coupled to `to_dict`'s exact key set — the day a field is renamed or dropped there, this endpoint raises `KeyError` and returns 500 while every other task endpoint keeps working. It also means `GET /tasks` and `GET /users/<id>/tasks` return two different shapes for the same resource with nothing documenting the difference.
Recommendation: See AP-06 / RP-04 — give `Task.to_dict(fields=None)` an explicit field selection (or a second named serializer) and have the endpoint request the shape it wants instead of removing what it does not.

================================
Total: 11 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

> **Adendo (2026-09-20) — a decisão pendente foi tomada:** o usuário determinou que o
> finding [HIGH] "Login issues a token that nothing ever verifies" fosse resolvido, e ele
> **está resolvido** desde esta data. O escopo aprovado: leituras (`GET`) seguem públicas;
> toda escrita exige `Authorization: Bearer <token>`; `PUT`/`DELETE /users/<id>` exigem ser
> o próprio usuário ou admin; `PUT`/`DELETE /tasks/<id>` exigem ser o dono da task ou admin;
> escrita em `/categories` exige role `admin`/`manager`; cadastro anônimo só cria role `user`.
> Implementação em `services/token_service.py` (emissão/leitura), `services/authorization.py`
> (regras, sem acoplamento HTTP) e `middlewares/auth.py` (guard que recarrega o usuário do
> banco a cada request). `SECRET_KEY` passou a não ter default: o boot aborta fora de
> desenvolvimento. Evidência: `evidence/logs/task-manager-api-round4-validation.txt`.
> O corpo do relatório acima é preservado como o snapshot da Fase 2 que o originou.
