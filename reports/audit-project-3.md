```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 4 | HIGH: 2 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Password Hashes Returned in API Responses
File: models/user.py:16-25 (used by routes/user_routes.py:33, 85-86, 129, 209)
Description: User.to_dict() includes the raw `password` field (the hash), and every route that serializes a user via to_dict() — GET /users/<id>, POST /users, PUT /users/<id>, and POST /login — returns it verbatim to the client.
Impact: Any API consumer (including unauthenticated ones for public-shaped responses) receives every user's password hash, enabling offline cracking without needing a separate breach.
Recommendation: Strip `password` from serialization; add a `to_public_dict()` that excludes it. See AP-04 / RP for serialization fix.

### [CRITICAL] Broken Password Hashing (MD5, No Salt)
File: models/user.py:27-32
Description: `set_password`/`check_password` hash credentials with unsalted `hashlib.md5`, a cryptographically broken, rainbow-table-crackable primitive.
Impact: Stored credentials are trivially reversible; a database leak instantly yields plaintext passwords for most users.
Recommendation: Replace with `werkzeug.security.generate_password_hash`/`check_password_hash` (already available via Flask). See AP-03.

### [CRITICAL] Hardcoded Secrets, SMTP Credentials, and Debug Mode Exposed on All Interfaces
File: app.py:13, app.py:34, services/notification_service.py:9-10
Description: `SECRET_KEY = 'super-secret-key-123'` is committed in source; `app.run(debug=True, host='0.0.0.0', ...)` binds the Werkzeug debugger to every network interface; `NotificationService` hardcodes a Gmail account and password (`senha123`) for SMTP.
Impact: The hardcoded SECRET_KEY undermines session/cookie signing; `debug=True` + `0.0.0.0` exposes the interactive Werkzeug debugger (remote code execution) to anyone who can reach the host; the SMTP credentials are a committed secret that grants access to a real mailbox.
Recommendation: Move all three into environment variables loaded via config (`os.environ`/`.env`), and disable `debug` in any non-local run. See AP-02.

### [CRITICAL] Fake, Forgeable Authentication Token
File: routes/user_routes.py:210
Description: POST /login returns `'fake-jwt-token-' + str(user.id)` as the auth token — a predictable string, not a signed JWT or any verifiable credential.
Impact: Anyone can forge a valid-looking token for any user id without knowing their password, fully bypassing authentication for any endpoint that later trusts this token.
Recommendation: Issue real signed tokens (e.g. `PyJWT` with the app's secret key) or a server-side session. See AP-02.

### [HIGH] Business Logic and Duplicate Computations Embedded in Route Handlers
File: routes/task_routes.py:16-59, routes/task_routes.py:71-80, routes/report_routes.py:13-101, routes/report_routes.py:104-155
Description: `get_tasks` manually rebuilds each task's dict field-by-field and recomputes the overdue check inline instead of calling `Task.to_dict()`/`Task.is_overdue()`, which already exist on the model; `get_task` calls `to_dict()` and then redundantly recomputes overdue again; both report endpoints reimplement all aggregation (status/priority counts, overdue detection, completion rates) directly in the route instead of delegating to a model/service method.
Impact: Controllers own logic that belongs to the Model/Service layer, so it can't be unit-tested independently of Flask, and every future overdue-rule or stats change has to be hunted down across N call sites instead of one.
Recommendation: Delegate to `Task.to_dict()` / `Task.is_overdue()` and extract report aggregation into a `ReportService`/model classmethod. See AP-06.

### [HIGH] Same Overdue Rule Reimplemented in 6 Locations
File: models/task.py:50-60, routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/user_routes.py:171-180, routes/report_routes.py:34-37, routes/report_routes.py:132-135
Description: The "is this task overdue" rule (`due_date < now` and `status not in (done, cancelled)`) is hand-written six separate times across models and three route files, even though `Task.is_overdue()` already implements it correctly and is never called.
Impact: The six copies can silently diverge — a fix applied to one won't reach the other five, producing inconsistent `overdue` flags between endpoints for the same task.
Recommendation: Call `Task.is_overdue()` everywhere instead of reimplementing the condition. See AP-06.

### [MEDIUM] N+1 Query Pattern in Report Endpoints
File: routes/report_routes.py:53-68, routes/report_routes.py:157-165
Description: `summary_report` loops over every user and issues a separate `Task.query.filter_by(user_id=u.id)` per iteration; `get_categories` does the same per category for `task_count`.
Impact: Query count grows linearly with the number of users/categories — a single report request can trigger dozens of extra round-trips as data grows.
Recommendation: Use a single grouped query (`db.session.query(...).group_by(...)`) or eager-loaded relationship counts instead of per-row queries. See AP-08.

### [MEDIUM] Missing Pagination on List Endpoints
File: routes/task_routes.py:11-63, routes/task_routes.py:240-271, routes/user_routes.py:10-25
Description: GET /tasks, GET /tasks/search, and GET /users all call `.query.all()`/`.all()` and return the entire table with no `limit`/`offset` or `page`/`per_page` parameters.
Impact: Response time and payload size grow unbounded with table size, and the seed data already shows no defense against this as usage grows.
Recommendation: Add `page`/`per_page` query params and use SQLAlchemy's `.paginate()`. See AP-09.

### [MEDIUM] Disconnected Service Layer
File: services/notification_service.py:1-48
Description: `NotificationService` (email notifications for task assignment/overdue) is fully implemented but never imported or instantiated anywhere in `app.py` or any route — task creation/assignment never calls it.
Impact: The folder structure implies notifications are live, but they silently never fire; anyone extending the feature will assume it works and won't notice the gap.
Recommendation: Either wire it into `create_task`/`update_task` where `user_id`/status changes, or remove it if the feature was abandoned. See AP-10.

### [MEDIUM] Deprecated `datetime.utcnow()` Usage
File: models/task.py:15-16,52; models/user.py:14; routes/task_routes.py:31,72,215,285; routes/report_routes.py:35,42,45,48,71 (18 occurrences total across the codebase)
Description: The codebase uses `datetime.datetime.utcnow()` throughout, which is deprecated in current Python versions in favor of timezone-aware `datetime.now(timezone.utc)`.
Impact: Naive (non-timezone-aware) timestamps are stored and compared, and the API will emit deprecation warnings today and hard failures on a future Python upgrade.
Recommendation: Replace with `datetime.now(timezone.utc)` consistently, and store timezone-aware columns. See AP-11.

### [LOW] Print-Based Logging Instead of Structured Logging
File: routes/task_routes.py:149,153,219,234; routes/user_routes.py:83,89,147
Description: Operational events (task/user created, updated, deleted, errors) are logged with bare `print(...)` calls instead of Python's `logging` module.
Impact: No log levels, no filtering, nothing captured by production log aggregation — errors are invisible outside of local stdout.
Recommendation: Replace with a configured `logging.getLogger(__name__)` and appropriate levels. See AP-12.

### [LOW] Unused Imports
File: app.py:7 (`os, sys, json`); routes/task_routes.py:7 (`os, sys, time`); routes/user_routes.py:6 (`json`); routes/report_routes.py:8 (`json`)
Description: These modules are imported but never referenced anywhere in their respective files.
Impact: Noise that obscures each file's real dependencies and misleads readers about what the module actually needs.
Recommendation: Remove the unused names from each import line. See AP-14.

### [LOW] Hardcoded Magic Values Duplicated Instead of Reusing Existing Constants
File: routes/task_routes.py:96-114 (title length, status list, priority range), routes/user_routes.py:61,64,71 (email regex, password length, role list) vs. utils/helpers.py:19-23,57-108,110-116
Description: `utils/helpers.py` already defines `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, plus `validate_email()` and `process_task_data()` — but every route re-hardcodes the same literals and re-implements the same validation inline instead of importing them; the helper functions are never called from anywhere.
Impact: Two independent sources of truth for the same validation rules; a change to one (e.g. widening `MAX_TITLE_LENGTH`) won't reach the routes actually enforcing it.
Recommendation: Import and use the existing constants/functions from `utils/helpers.py` in the routes; delete them if truly redundant. See AP-13 / AP-10.

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```
