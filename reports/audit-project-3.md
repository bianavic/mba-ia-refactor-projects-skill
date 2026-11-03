================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.11.15 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLite)
Files:   15 analyzed | ~1160 lines of code

## Summary
CRITICAL: 7 | HIGH: 3 | MEDIUM: 8 | LOW: 4

## Findings

### [CRITICAL] Hardcoded secret key, SMTP password, debug server on 0.0.0.0 and seeded literal passwords
File: app.py:13, app.py:34, services/notification_service.py:9-10, seed.py:19, seed.py:26, seed.py:33
Description: `SECRET_KEY` is the literal `'super-secret-key-123'`, the notification service holds the SMTP account and password `'senha123'`, the app runs with `debug=True` bound to `0.0.0.0`, and the seed creates an admin with password `'1234'` and two users with `'abcd'` and `'pass'`.
Impact: Anyone with a copy of the repository holds the signing key and the mail account; the Werkzeug debugger is reachable from the network on any error page (interactive code execution behind a PIN); the seeded admin's password is public, so whoever reaches a seeded deployment logs in as admin. Removing the values from the code does not un-leak them.
Recommendation: Read the secret key, debug flag, SMTP settings and seed passwords from the environment through one config module, ship a `.env.example` without values, and rotate the leaked key/password — see RP-02 (AP-02).

### [CRITICAL] Passwords hashed with unsalted MD5
File: models/user.py:27-32
Description: `set_password` stores `hashlib.md5(pwd).hexdigest()` and `check_password` compares the same digest — a fast, unsalted hash.
Impact: Any leak of the `users` table (or of the API responses below) yields passwords recoverable with precomputed tables in seconds; equal passwords share one hash. This is the users' credential data, readable by whoever obtains the database file for as long as it is kept (LGPD art. 46 security duty).
Recommendation: Use Werkzeug's salted `generate_password_hash`/`check_password_hash`; existing MD5 rows are migrated as chosen in Phase 2 (rehash on next login or forced reset) — see RP-09 (AP-03).

### [CRITICAL] Password hash returned by every user response, including login
File: models/user.py:21, routes/user_routes.py:33, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209
Description: `User.to_dict()` includes the `password` column, and `GET /users/<id>`, `POST /users`, `PUT /users/<id>` and `POST /login` return it as-is.
Impact: Any anonymous caller downloads the MD5 hash of any user by iterating ids, and cracks it offline — every account, the seeded admin included, is one request plus a lookup away.
Recommendation: Build each response from an explicit field list that never contains the hash — see RP-09 (AP-04).

### [CRITICAL] No authentication or authorization on any route; login issues a forgeable token nothing checks
File: routes/user_routes.py:210, routes/task_routes.py:85, routes/task_routes.py:156, routes/task_routes.py:225, routes/user_routes.py:10, routes/user_routes.py:27, routes/user_routes.py:42, routes/user_routes.py:92, routes/user_routes.py:134, routes/user_routes.py:153, routes/report_routes.py:12, routes/report_routes.py:103, routes/report_routes.py:167, routes/report_routes.py:190, routes/report_routes.py:211
Description: No route has an auth construct (a project-wide search for auth, token, session, role and permission finds only the login and the unused `User.is_admin`); `POST /login` returns `'fake-jwt-token-' + id`, a predictable string that no route ever verifies.
Impact: Any anonymous caller creates, edits and deletes tasks, users and categories, changes any user's password, email, role or active flag, deletes any user with all their tasks, and reads every report.
Recommendation: Issue a signed, expiring token at login and apply the access level confirmed per route in the Phase 2 access table — see RP-16 (AP-05).

### [CRITICAL] Other people's names and emails served to anonymous callers
File: routes/user_routes.py:15-23, routes/user_routes.py:33, routes/report_routes.py:62-65, routes/report_routes.py:138-142, routes/task_routes.py:41-48
Description: `GET /users` lists the name and full email of every user, `GET /users/<id>` and `GET /reports/user/<id>` return any user's name and full email, `GET /reports/summary` lists every user's name with their productivity, and `GET /tasks` adds each assignee's name.
Impact: Any anonymous caller harvests the whole user base's names and emails and per-person productivity figures — personal data of third parties beyond what each caller needs, readable by anyone for as long as the API runs (LGPD art. 6 III, minimization).
Recommendation: Restrict the routes per the access table and mask other people's identifiers in every response, full email only to its subject, as chosen in Phase 2 — see RP-09 (AP-04), combined with RP-16.

### [CRITICAL] flask-cors 4.0.0 sends `Access-Control-Allow-Private-Network: true` on every route
File: requirements.txt:3, app.py:15
Description: The pinned flask-cors 4.0.0 is affected by GHSA-hxwh-jpp2-84pm / CVE-2024-6221 (private-network header enabled by default, fixed in 4.0.2), and `CORS(app)` with default options is exactly the vulnerable path; the same pin also carries CVE-2024-1681 (log injection at debug level, fixed 4.0.1) and CVE-2024-6844, CVE-2024-6866, CVE-2024-6839 (path-matching flaws, fixed 6.0.0), which this code's single default resource and log level do not reach.
Impact: Any public web page a user opens can make their browser call this API on a private network or `localhost` and read the answers — with the routes currently open, the full user list, hashes and reports leave the network through the victim's browser.
Recommendation: Upgrade flask-cors; the release fixing every advisory (6.0.x) crosses two majors, so the target version is a Phase 2 decision — see RP-12 (AP-12).

### [CRITICAL] Exception text with the password hash and email, and user names, written to the log
File: routes/user_routes.py:83, routes/user_routes.py:89, services/notification_service.py:21
Description: `create_user` prints `Usuário criado: <id> - <name>` and, on a failed insert, `str(e)` — SQLAlchemy's exception text carries the statement parameters, i.e. the new user's name, email and password hash (confirmed by reproducing a unique-email violation); the notification service prints the recipient email.
Impact: Whoever reads stdout, the log shipper or log storage gets names, emails and, on any failed signup (two concurrent signups with the same email suffice), a password hash — retained as long as the logs, outside the database's access control.
Recommendation: Log ids and outcomes only, never exception text or names, through a logger; logs already written must be purged by the operator — see RP-17 (AP-18).

### [HIGH] Route files hold persistence and business rules
File: routes/task_routes.py:11-299, routes/user_routes.py:10-211, routes/report_routes.py:12-223
Description: Every handler queries the ORM, commits and rolls back the session, and applies the domain rules (validation, overdue computation, statistics, cascading deletion) inline — `arch-check.sh` lists 76 persistence calls across the three route files.
Impact: No rule can be tested without an HTTP request and a database; a change in one endpoint's rule (status set, overdue) must be repeated by hand in every handler that copied it.
Recommendation: Move queries to the models and the request flow to controllers — see RP-14, RP-03, RP-11 (AP-06).

### [HIGH] No controller layer; routes import models directly and orchestrate several models
File: routes/task_routes.py:3-5, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:11-63, routes/user_routes.py:3-4, routes/user_routes.py:134-151, routes/report_routes.py:3-5, routes/report_routes.py:12-101, routes/report_routes.py:103-155, routes/report_routes.py:157-165
Description: There is no `controllers/` directory; each route file imports `Task`, `User` and `Category` directly, and handlers decide multi-model use cases — task create/update check `User` and `Category`, user deletion deletes the user's `Task` rows, the reports aggregate `Task` per `User` and `Category`.
Impact: A use case cannot be tested or reused without its neighbouring models and the HTTP layer; a change to one entity's model breaks handlers of another resource.
Recommendation: Add one controller per route file and extract a Service for each multi-model use case (task assignment checks, user erasure, reports) — see RP-21 (AP-22).

### [HIGH] Overdue rule, task serialization, statistics and validation copied across handlers
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-37, routes/report_routes.py:132-135, models/task.py:50-60, routes/task_routes.py:17-28, routes/task_routes.py:275-279, routes/report_routes.py:19-22, routes/task_routes.py:296, routes/report_routes.py:67, routes/report_routes.py:151, routes/task_routes.py:92-144, routes/task_routes.py:166-213, utils/helpers.py:57-108, routes/user_routes.py:61, routes/user_routes.py:106, utils/helpers.py:19-23
Description: The overdue rule is re-implemented in six handlers while `Task.is_overdue()` already holds it; `GET /tasks` rebuilds `Task.to_dict()` field by field; per-status counts and completion rate are computed separately in `/tasks/stats` and both reports; task validation is written twice (create and update) plus a third unused copy in `process_task_data`; the email regex is repeated beside the unused `validate_email`.
Impact: The copies diverge the moment one is fixed — a new status or a change to "overdue" silently answers differently across endpoints.
Recommendation: One owner per rule: `Task.is_overdue()`/`to_dict()` on the model, one task validator shared by create and update, one statistics function — see RP-04 (AP-07).

### [MEDIUM] Database setup module loose at the project root
File: database.py:1-3
Description: The SQLAlchemy instance lives in a root-level `database.py` instead of a role directory.
Impact: The root does not show which layer the file belongs to, and each new cross-cutting module (config, errors, auth) would land beside it.
Recommendation: Move it to `database/` and update every import — see RP-22 (AP-23).

### [MEDIUM] N+1 queries in task listing, user listing and reports
File: routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:53-56, routes/report_routes.py:161-163
Description: `GET /tasks` runs one `User` and one `Category` lookup per task, `GET /users` lazy-loads `u.tasks` per user, `/reports/summary` queries tasks per user and `GET /categories` counts tasks per category.
Impact: Query count grows linearly with the number of tasks, users and categories; listings slow down as data grows.
Recommendation: Eager-load the relationships or group counts in one query, response shape unchanged — see RP-06 (AP-09).

### [MEDIUM] List endpoints return whole tables with no pagination
File: routes/task_routes.py:14, routes/task_routes.py:266, routes/user_routes.py:12, routes/user_routes.py:35, routes/user_routes.py:159, routes/report_routes.py:159
Description: `GET /tasks`, `GET /tasks/search`, `GET /users`, `GET /users/<id>` (its task list), `GET /users/<id>/tasks` and `GET /categories` load and return every row with no limit/offset or page parameters.
Impact: Response time and payload grow with the tables; one request can return the entire dataset.
Recommendation: Add bounded `page`/`per_page` parameters, default as chosen in Phase 2 — see RP-07 (AP-10).

### [MEDIUM] Notification service, helpers and model methods implemented but never used
File: services/notification_service.py:1-48, utils/helpers.py:9-108, models/task.py:38-60, models/user.py:34-38, routes/report_routes.py:7
Description: `NotificationService` is imported nowhere; every function in `utils/helpers.py` is unused (`report_routes` imports `format_date` and `calculate_percentage` and calls neither); `Task.validate_status`, `validate_priority`, `is_overdue` and `User.is_admin` are never called.
Impact: Readers believe task-assignment emails and the shared validators are live while the routes run their own copies; the dead code rots and carries a hardcoded SMTP password.
Recommendation: Wire what duplicates live logic (`is_overdue`, `calculate_percentage`, `validate_email`), and delete or wire the notification service as chosen in Phase 2 — see RP-10 (AP-11).

### [MEDIUM] Flask 3.0.0 pin, Python 3.11.15 runtime and three unimported pins carry advisories
File: requirements.txt:1, requirements.txt:4-6
Description: Flask 3.0.0 is affected by CVE-2026-27205 (missing `Vary: Cookie`, fixed 3.1.3); the interpreter in use, 3.11.15, predates the 3.11.18 security release (CVE-2026-115557 ssl CA, CVE-2026-114583 tarfile, expat, cookiejar); marshmallow 3.20.1 (CVE-2025-68480), requests 2.31.0 (CVE-2024-35195, CVE-2024-47081, CVE-2026-25645) and python-dotenv 1.0.0 (CVE-2026-28684) are pinned although no module imports them.
Impact: None is reachable through this code today (no session use, no tarfile/XML/cookiejar use, three packages never imported), but every install ships known-vulnerable code into the environment and a future import inherits the flaws.
Recommendation: Bump Flask to 3.1.3 (same major), drop or bump the unimported pins, and decide in Phase 2 how the runtime is handled — see RP-12 (AP-12).

### [MEDIUM] Deprecated `Query.get()` used for every lookup by id
File: routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213
Description: Every id lookup calls `Model.query.get(id)`, which SQLAlchemy 2.x marks legacy and deprecated (`LegacyAPIWarning`, "available as Session.get() (deprecated since: 2.0)", reproduced on the installed 2.1.3).
Impact: Each lookup emits a deprecation warning today and breaks when the legacy Query API is removed.
Recommendation: Replace with `db.session.get(Model, id)` inside the models — see RP-12 (AP-12).

### [MEDIUM] No retention limit on users' personal data
File: models/user.py:5-14
Description: Users' names and emails are kept forever — including deactivated accounts (`active = False`) — and nothing records when an account was deactivated or ages its data out; deletion (`DELETE /users/<id>`) and the subject's own data (`GET /users/<id>`) exist.
Impact: Personal data of people who left stays identifiable indefinitely, with no limit an operator can configure (LGPD art. 16 / GDPR art. 5(1)(e) storage limitation).
Recommendation: A retention policy needs a period and a deactivation timestamp — decide in Phase 2 whether to add a configurable retention that de-links aged accounts or leave it open — see RP-18 (AP-19).

### [MEDIUM] Request fields used without type checks; bad input answers 500
File: routes/task_routes.py:96, routes/task_routes.py:113, routes/task_routes.py:167, routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/user_routes.py:61, routes/user_routes.py:103, routes/user_routes.py:106, routes/user_routes.py:115, routes/user_routes.py:125, routes/report_routes.py:173-180, routes/report_routes.py:196-202
Description: `priority` compared as a number without a type check (`"high"` → `TypeError`), `len()` on a non-string title or password, `int()` on `?priority=`/`?user_id=` in search, `re.match` on a non-string email, `active` stored with any value, user and category updates accepting an empty name, `PUT /categories/<id>` with no body crashing on `'name' in None`, and `color` never validated (`is_valid_color` is unused).
Impact: Client mistakes are reported as server failures (Flask's HTML 500 page), and invalid values (empty names, non-boolean `active`, 20-character colors) are stored.
Recommendation: One validator per resource shared by create and update raising typed errors mapped to 400 in one place, keeping the API's error key and messages — see RP-20 with RP-11 (AP-21).

### [LOW] print used for operational logging
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39-41
Description: Creation, update, deletion and error events are written with `print`.
Impact: No levels or fields — errors cannot be filtered from routine events or routed to monitoring.
Recommendation: A module-level `logging` logger per module — see RP-08 (AP-13).

### [LOW] Statuses, roles, limits and defaults hardcoded across files
File: app.py:11, app.py:34, routes/task_routes.py:32, routes/task_routes.py:73, routes/task_routes.py:96-104, routes/task_routes.py:110, routes/task_routes.py:113, routes/task_routes.py:177, routes/task_routes.py:182, routes/task_routes.py:276-279, routes/task_routes.py:286, routes/user_routes.py:64, routes/user_routes.py:71, routes/user_routes.py:115, routes/user_routes.py:120, routes/user_routes.py:173, routes/report_routes.py:19-28, routes/report_routes.py:36, routes/report_routes.py:45, routes/report_routes.py:49, routes/report_routes.py:60, routes/report_routes.py:120-129, routes/report_routes.py:134, routes/report_routes.py:180, models/task.py:11-12, models/task.py:39, models/task.py:46, models/task.py:53, models/user.py:12, models/user.py:35, models/category.py:10, utils/helpers.py:64, utils/helpers.py:75, utils/helpers.py:84, utils/helpers.py:110-116
Description: The status list, each status literal, the roles, priority bounds, title and password lengths, the default color and priority, the 7-day window, the "high priority" threshold, the database URI and the port are inline literals repeated across routes, models and helpers — `utils/helpers.py` even declares the constants and nobody uses them.
Impact: Adding a status or changing a limit needs edits in a dozen places, and the copies already differ in where they live.
Recommendation: One config module for the domain constants and settings, every literal replaced by it — see RP-13 (AP-14).

### [LOW] Unused imports
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7
Description: `os`, `sys`, `json`, `time`, `hashlib`, `math`, `format_date` and `calculate_percentage` are imported and never referenced in these files.
Impact: The files' real dependencies are obscured; `hashlib` in the user routes suggests hashing happens there.
Recommendation: Remove them — see RP-13 (AP-15).

### [LOW] Category CRUD lives in the reports blueprint; cryptic local names
File: routes/report_routes.py:157-223, routes/report_routes.py:24-28, routes/task_routes.py:16, routes/user_routes.py:14
Description: `/categories` routes are declared in `report_routes.py` under `report_bp`, so the file name does not predict its role, and handlers use `p1`…`p5`, `t`, `u`, `c`, `cat` for domain objects.
Impact: Nobody finds category handling by its name, and short locals slow review of the statistics code.
Recommendation: Give categories their own route/controller files (paths unchanged) and descriptive internal names — see RP-15 (AP-16).

================================
Total: 22 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
