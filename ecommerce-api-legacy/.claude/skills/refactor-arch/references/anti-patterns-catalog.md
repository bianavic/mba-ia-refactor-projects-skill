# Anti-Pattern Catalog (Phase 2)

Each entry has an ID (used by `refactoring-playbook.md` to point back to the matching fix), a severity, language-agnostic detection signals, and why it matters. Scan every source file identified in Phase 1 against every entry below. A finding is only valid if you can point to a real file and line number — grep for the signals, then open the file to confirm.

Severity scale (see `SKILL.md` for the full definitions):
- **CRITICAL** — breaks correctness or security, or a God Class merges DB + business logic + routing in one place.
- **HIGH** — strong MVC/SOLID violation that hurts testability/maintainability.
- **MEDIUM** — duplication, standardization gaps, or moderate performance issues.
- **LOW** — readability/naming/magic-value issues.

## CRITICAL

### AP-01 — SQL Injection / Unsafe Query Construction
- **Signals:** query strings built via concatenation or f-strings/template literals with request-controlled values (`"SELECT * FROM x WHERE id = " + id`, `` `SELECT * FROM x WHERE id = ${id}` ``, `"...%s" % value`) instead of parameterized placeholders (`?`, `%s` with a params tuple/list, ORM query builders).
- **Impact:** arbitrary read/write/delete of data through any client-controlled field (id, search term, email).

### AP-02 — Hardcoded Secrets & Credentials
- **Signals:** literal strings assigned to variables/constants named like `SECRET_KEY`, `API_KEY`, `PASSWORD`, `TOKEN`, `dbPass`, or matching known key formats (e.g. `pk_live_...`, `sk_...`); `DEBUG=True`/`debug: true` left enabled; any of the above returned in an API response body (e.g. a `/health` or config endpoint echoing `secret_key`).
- **Impact:** secrets committed to source control and/or exposed over the network; compromises session/token integrity or payment processing immediately, not hypothetically.

### AP-03 — Broken or Fake Cryptographic Hashing
- **Signals:** password hashing implemented with a broken/obsolete primitive (bare `hashlib.md5`, `hashlib.sha1`) with no salt, or a hand-rolled "hash" that is actually reversible encoding (e.g. repeated `base64` of the input truncated to N characters) instead of a vetted password-hashing function (`bcrypt`, `argon2`, `werkzeug.security.generate_password_hash`, `scrypt`).
- **Impact:** stored credentials are trivially reversible or crackable via rainbow tables; equivalent to storing passwords in plaintext.

### AP-04 — Sensitive Data Leaked via Serialization
- **Signals:** a model's `to_dict()`/`toJSON()`/serializer includes a password/hash/token field, and that serialization is returned directly by one or more endpoints (list, detail, or login responses).
- **Impact:** every client of the API receives password hashes or secrets it never needed, enabling offline attacks even without a separate data breach.

## HIGH

### AP-05 — God Class / No Architectural Separation
- **Signals:** one file or class defines schema/connection setup, every route, and the "business logic" together, with no intermediate layer; adding a feature means editing the same file that handles unrelated domains.
- **Impact:** impossible to unit test in isolation; a change to one domain risks breaking every other domain living in the same file.

### AP-06 — Business Logic Duplicated Across Controllers/Routes
- **Signals:** the same rule (a date/status computation, a validation, a derived field) is re-implemented inline in multiple route handlers instead of calling one shared model/service method.
- **Impact:** the duplicated copies silently diverge the moment only one of them is fixed — a correctness bug waiting to happen, and a direct Controller/Model responsibility violation.

### AP-16 — Persistence/ORM Calls Inline in Routes
- **Signals:** a route/view handler reaches the persistence layer itself instead of making exactly one Controller/Service call — a query/session call (`Model.query...`, `db.session.add/commit/delete`, `Model.find/findOne/findById/create/update/destroy`, a raw SQL `execute`/`query`) or a Model finder classmethod (`Model.get_by_id(...)`, `Model.find_by_x(...)`). Report it even when the call appears only once, and even when the project already has `services/`/`controllers/` folders that other routes use.
- **Impact:** the handler cannot be tested without a live database, and holds responsibilities beyond parse → call → serialize. Because each individual call looks harmless in isolation, the violation survives any review that only looks for duplication.

### AP-07 — Global Mutable State
- **Signals:** module-level mutable variables (a plain object/dict used as a cache, a counter) that are written to from multiple request handlers with no synchronization.
- **Impact:** race conditions and non-deterministic behavior under concurrent requests; also usually indicates a caching/aggregation concern that belongs in a dedicated layer.

## MEDIUM

### AP-08 — N+1 Query Pattern
- **Signals:** a loop (`for`, `.forEach`, nested callbacks) that issues one query per iteration to fetch related rows, instead of a join, a single `WHERE id IN (...)`, or eager loading.
- **Impact:** query count grows linearly (or multiplicatively, when nested) with result size; a single list endpoint can trigger dozens of round-trips.

### AP-09 — Missing Pagination on List Endpoints
- **Signals:** a list/report endpoint queries and returns an entire table with no `limit`/`offset`, `page`/`per_page`, or cursor parameters.
- **Impact:** response time and payload size degrade linearly with table growth; combines badly with AP-08.

### AP-10 — Dead / Disconnected Code Layer
- **Signals:** a module, class, or service (often named `*_service`, `*Manager`) that is fully implemented but never imported or called from any route/controller.
- **Impact:** misleads anyone reading the folder structure into believing the feature is live; indicates an incomplete integration and rotting code.

### AP-11 — Deprecated API Usage
- **Signals:** calls to APIs the detected framework/language version has flagged deprecated. Check the manifest version from Phase 1 against the framework's changelog/deprecation notices. Common examples to check for:
  - Python: `datetime.datetime.utcnow()` (deprecated favor `datetime.now(timezone.utc)`), `imp` module (favor `importlib`), `flask.ext.*` imports (favor direct `flask_<ext>` imports), `distutils` (removed in 3.12).
  - Node.js: `new Buffer(...)` (favor `Buffer.from`/`Buffer.alloc`), `crypto.createCipher`/`createDecipher` (favor `createCipheriv`/`createDecipheriv`), callback-only `fs` calls where the codebase otherwise uses promises, bundled `body-parser` usage when the installed Express version already ships `express.json()`.
  - Any dependency pinned to a major version whose changelog marks currently-used functions as removed/deprecated.
- **Impact:** deprecated APIs are removed without notice in future upgrades, and often have a safer/faster modern replacement already.

## LOW

### AP-12 — Print/Console-Based Logging
- **Signals:** `print(...)` (Python) or `console.log(...)` (Node) used for operational logging instead of the standard logging module (`logging`) or a structured logger (`winston`, `pino`).
- **Impact:** no log levels, no structured fields, no rotation — unusable in production and impossible to filter by severity.

### AP-13 — Hardcoded Configuration / Magic Values
- **Signals:** inline literal lists/values that represent configuration (valid categories, limits, endpoints) embedded directly inside a function instead of a config module, environment variable, or database-backed table.
- **Impact:** every change requires a source edit and redeploy instead of a configuration change.

### AP-14 — Unused Imports
- **Signals:** imported modules/names never referenced anywhere else in the file.
- **Impact:** noise that obscures a file's real dependencies and slightly increases load time.

### AP-15 — Inconsistent Language/Naming Conventions
- **Signals:** identifiers in one language (typically English) mixed with user-facing strings/comments in another, with no single convention applied consistently.
- **Impact:** a maintainability/standardization issue rather than a functional one, but it slows down onboarding and code review.

---

This catalog has 16 entries across all four severities — well above the minimum of 8 — and always includes at least one CRITICAL/HIGH, several MEDIUM, and several LOW so any project audited against it can satisfy the required finding distribution, provided the underlying code actually exhibits the pattern.
