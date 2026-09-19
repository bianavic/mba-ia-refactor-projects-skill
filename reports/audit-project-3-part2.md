```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   19 analyzed | ~1063 lines of code

## Resolved since audit-project-3.md
All 4 CRITICAL findings from the previous part are resolved: passwords are hashed with
werkzeug.security (not MD5) and never serialized in to_dict(); SECRET_KEY/DB URL/host/port
are env-driven via config/settings.py with DEBUG defaulting to false; /login now issues a
signed itsdangerous token instead of a fake string; services/notification_service.py (with
hardcoded SMTP creds) no longer exists.
Also resolved: the "manual dict rebuild" and "overdue rule reimplemented 6x" HIGH findings
(all call sites now use Task.to_dict()/Task.is_overdue()); the report-endpoint N+1 (now
grouped queries in services/report_service.py); the disconnected service layer; deprecated
datetime.utcnow() (utils/helpers.py:utc_now() now uses datetime.now(timezone.utc)); the
print-based logging in routes (now logging.getLogger everywhere); the unused os/sys/json
imports; and the routes re-hardcoding VALID_STATUSES/VALID_ROLES/title-length/password-length
instead of importing them (routes now import all of these from utils/helpers.py).

Still open (reappeared, partially fixed): the "Missing Pagination" finding is only half
resolved — GET /tasks and GET /tasks/search were fixed, but GET /users was not touched and
still returns the full table unpaginated. Carried into this report's MEDIUM findings below
rather than counted as new.

> **Correction (2026-09-19):** the "GET /users was not touched" claim above, and the
> "Missing pagination on list endpoints" finding below, were already inaccurate for `GET
> /users` at the time this report was written — `controllers/user_controller.py:22-23`
> (`list_users`) already paginates via `User.query.paginate(page=page, per_page=per_page,
> ...)`, and `routes/user_routes.py:9-10` already reads `page`/`per_page` from the query
> string. The rest of this report is left as originally written; only `GET /users`
> pagination should be treated as resolved, not open. `GET /categories`
> (services/report_service.py:139-148) is unaffected by this correction and remains open.

## Summary
CRITICAL: 0 | HIGH: 2 | MEDIUM: 2 | LOW: 3

## Findings

### [HIGH] Routes call the ORM directly instead of delegating to a Controller/Service
File: routes/task_routes.py:24-219 (get_tasks, get_task, create_task, update_task, delete_task, search_tasks)
File: routes/user_routes.py:23-214 (get_users, get_user, create_user, update_user, delete_user, get_user_tasks, login)
File: routes/report_routes.py:15-95 (summary_report, user_report, get_categories, create_category, update_category, delete_category)
Description: Almost every route handler in the project reaches persistence itself — `Task.query...`, `User.query...`, `Category.query...`, `db.session.add/commit/delete` — instead of making a single call into a Controller/Service and serializing the result. `Task.get_statistics()` in models/task.py is the one exception that already delegates correctly.
Impact: No route can be unit-tested without a live database; each handler mixes request parsing, validation, persistence, and serialization, so a schema or query change forces edits across every route file instead of one layer.
Recommendation: See AP-16 / RP-14 for extracting Controller/Service methods per resource (Task, User, Category) — every route becomes parse → one call → serialize.
Status: New — not present in audit-project-3.md (that run predates this catalog entry being checked); the underlying pattern already existed in the prior codebase too.

### [HIGH] Validation and normalization logic duplicated across route handlers
File: routes/task_routes.py:60-64 & 132-135 (title length), 74-75 & 142-144 (status), 77-78 & 146-149 (priority), 98-102 & 165-172 (due_date parsing), 104-108 & 174-178 (tags normalization)
File: routes/report_routes.py:37-38 vs. 65-71 (missing-body guard present in create_category, silently absent in update_category)
Description: `create_task`/`update_task` reimplement identical title/status/priority/due-date/tags rules inline instead of calling one shared Task validation method, and the "reject empty JSON body" check that every other write endpoint performs is missing entirely from `update_category`.
Impact: The copies have already begun to diverge — `update_category` will raise an unhandled `TypeError` on an empty body where every sibling endpoint returns a clean 400. Any future rule change (e.g. title length) must be remembered in multiple places or handlers silently disagree.
Recommendation: See AP-06 / RP-04 — centralize validation into Task/Category model or service methods shared by create and update paths.
Status: New — a different duplication than the two AP-06 findings in audit-project-3.md (overdue-rule reimplementation, manual dict rebuilding), both of which are resolved.

### [MEDIUM] N+1 / per-row persistence operations in loops
File: routes/user_routes.py:24-38 (`get_users` — `len(u.tasks)` per user triggers one lazy-load query per user)
File: routes/user_routes.py:154-156 (`delete_user` — loops over a user's tasks issuing one `db.session.delete()` per task instead of a single bulk delete)
Description: Both spots issue one persistence operation per loop iteration instead of a single set-based query/operation.
Impact: Response time for `GET /users` degrades linearly with user count; `DELETE /users/<id>` issues N+1 delete statements instead of one bulk delete, extending the request and the transaction under load.
Recommendation: See AP-08 / RP-06 — use a single aggregate query (or joinedload, as `get_tasks` already does) for `get_users`, and `Task.query.filter_by(user_id=user_id).delete()` for the cascade delete.
Status: New locations — audit-project-3.md's N+1 finding was about routes/report_routes.py (summary_report, get_categories), which is now resolved via grouped queries in report_service.py.

### [MEDIUM] Missing pagination on list endpoints
File: routes/user_routes.py:23-38 (`GET /users` returns `User.query.all()`)
File: routes/report_routes.py:29-31 → services/report_service.py:139-148 (`GET /categories` returns `Category.query.all()`)
Description: Both endpoints return the entire table with no `page`/`per_page` or limit/offset parameters, unlike `GET /tasks` which already paginates.
Impact: Response size and latency grow unbounded with table size; combined with the N+1 above, `GET /users` is the most expensive endpoint in the API today.
Recommendation: See AP-09 / RP-07 — apply the same `.paginate(page=..., per_page=...)` pattern already used in `get_tasks`.
Status: ~~Still open (reappeared) for GET /users~~ — see "Correction (2026-09-19)" above:
this was already resolved when this report was written (`controllers/user_controller.py`
paginates `GET /users`). GET /tasks and GET /tasks/search from the original old finding are
also resolved. GET /categories is a new location, not in the old report, and remains open.

### [LOW] print()-based logging instead of the standard logging module
File: utils/helpers.py:32-36 (`log_action`)
Description: Every other module in the app uses `logging` (`logger.info`, `logger.error`), but `log_action` uses raw `print()` — and is never called from anywhere in the codebase.
Impact: If ever wired up, this path bypasses log levels/handlers/formatting entirely; today it's just dead code adding noise to the utils module.
Recommendation: See AP-12 / RP-08 — delete `log_action` (dead) or reimplement it on top of the existing `logging` setup if the feature is actually needed.
Status: New location — audit-project-3.md's print-logging finding was about routes/task_routes.py and routes/user_routes.py, both of which now use logging correctly; this is a separate, previously-unreported dead helper.

### [LOW] Magic default values duplicated instead of using existing constants
File: models/category.py:10 & routes/report_routes.py:47 (`'#000000'` hardcoded twice)
File: models/task.py:11 & routes/task_routes.py:68 (`3` hardcoded twice)
File: utils/helpers.py:52-53 (`DEFAULT_PRIORITY`, `DEFAULT_COLOR` defined but never referenced anywhere)
Description: `utils/helpers.py` already centralizes these two defaults as constants, but the model column defaults and the route fallback values both hardcode the literal instead of importing them.
Impact: A future change to the default priority or color requires remembering to edit it in two unrelated files instead of one constant.
Recommendation: See AP-13 / RP-13 — import and use `DEFAULT_PRIORITY`/`DEFAULT_COLOR` in models/task.py, models/category.py, routes/task_routes.py, and routes/report_routes.py.
Status: New — audit-project-3.md's magic-values finding was about title-length/status/priority-range/email-regex/password-length/role-list constants, which are now correctly imported and used everywhere; this is a different pair of literals (defaults) that stayed hardcoded.

### [LOW] Inconsistent language: Portuguese user-facing/log strings mixed with English code
File: routes/task_routes.py:37,45,54,58,61,64,75,78,83,88,102,113,117-118,125,133,135,143,148,155,162,170,184,188-189,196,201,205-206
File: routes/user_routes.py:45,60,68,70,72,75,78,82,85,100-101,108,112,119,123,128,133,144-145,152,161,165-166,173,196-197,200,203,206
File: seed.py:1 (module docstring), 94-97 (print output)
Description: All identifiers, function/variable names, and code structure are in English, but every user-facing error message, log message, and the seed script's docstring/output are in Portuguese, with no documented convention for which language applies where.
Impact: Slows onboarding for non-Portuguese-speaking contributors and complicates any future API consumer that needs to branch on error message content; a mixed-language codebase is also harder to keep consistent in code review.
Recommendation: See AP-15 / RP-15 — pick one convention (e.g. English internally, Portuguese only in an i18n-ready message layer) and apply it consistently. Per RP-15's scope limit, user-facing message strings must stay in the language the API already answers in, so this finding is reported but intentionally left unresolved in Phase 3 to avoid changing response shape.
Status: New — not raised in audit-project-3.md.

================================
Total: 7 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```
