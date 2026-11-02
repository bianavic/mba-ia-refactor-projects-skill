# Anti-Pattern Catalog (Phase 2)

Scan every Phase 1 source file against every entry. Each entry has a stable ID (`AP-xx`), a
severity, detection signals, the impact and the playbook fix (`RP-xx`). IDs are identifiers, not an
order: sort findings by severity, never by ID.

## Contents
- Draft validation — run before rendering the report
- CRITICAL: AP-01 SQL injection · AP-02 hardcoded secrets · AP-03 broken hashing · AP-04 data leaked via serialization · AP-05 missing auth · AP-17 privilege escalation via signup · AP-20 arbitrary query/code execution
- HIGH: AP-06 God Class · AP-07 duplicated business logic · AP-08 global mutable state · AP-22 layer leakage / missing or unwired controller layer / orchestration outside a Service
- MEDIUM: AP-23 supporting modules loose at the root · AP-09 N+1 · AP-10 no pagination · AP-11 dead layer · AP-12 deprecated APIs and vulnerable versions · AP-18 personal data in logs · AP-19 incomplete data-subject rights · AP-21 missing input validation / raw exception leakage
- LOW: AP-13 print logging · AP-14 magic values · AP-15 unused imports · AP-16 inconsistent naming

## Draft validation — run before rendering the report

When a check fails, fix the draft and re-run the checks; do not stop to ask.

- **Evidence:** every finding cites a real `file:line` confirmed by opening the file (a grep hit is
  a lead, not a citation) and lists every location it spans. Do not invent lines for unavailable code.
- **Sweep before closing:** once a signal is found, search for the same signal across every
  Phase 1 source file and every inventoried endpoint before writing `File:`; another occurrence
  of that signal is a location of the same finding, not a new one.
- **Severity:** matches the scale; security findings are rated on what an attacker can actually
  reach. Never inflate to fill a slot or soften to shorten the report.
- **Description vs. Impact:** Description says what the code does; Impact says what it costs
  someone (attacker, user, operator). If they collapse into one sentence, the finding is unfinished.
- **Traceability:** every finding names its `AP-xx` and the `RP-xx` Phase 3 will apply.
- **No double-counting:** symptoms of one root cause are one finding; two different defects in the
  same function stay separate.
- **Absent requirements:** a grep never fires on an absence — ask once per audit: can a user be
  **deleted**? Can their data be **exported**? Is there any **retention limit**? Is a privileged role
  **obtainable** by the person it restricts (AP-17)? Report an absence only when the domain implies
  the requirement, and cite the file where it would belong.
- **AP-22/AP-23 leads confirmed:** every line `arch-check.sh` listed was opened and confirmed.
- **AP-12 ran in full:** both halves below, for the runtime and every imported dependency.
- **Negative results:** every entry scanned without a finding goes to `Checked, no findings`.
- **Arithmetic:** recompute `## Summary` and `Total:` by counting the rendered blocks.

## CRITICAL

### AP-01 — SQL injection / unsafe query construction
- **Signals:** a query string built by concatenation, f-strings/template literals or `%` formatting with request-controlled values instead of bound parameters or a query builder.
- **Impact:** arbitrary read/write/delete through any client-controlled field (id, search term, email).
- **Fix:** RP-01.

### AP-02 — Hardcoded secrets and credentials
- **Signals:** literal values for `SECRET_KEY`, `API_KEY`, `PASSWORD`, `TOKEN` and the like, or matching known key formats (`sk_…`, `pk_live_…`); debug mode left on; seed/fixture accounts with literal passwords (a seeded admin especially); any of these echoed in a response (a `/health` or config endpoint).
- **Impact:** secrets in source control and/or on the network; session/token integrity or payment processing compromised immediately.
- **Fix:** RP-02.

### AP-03 — Broken, fake or absent password hashing
- **Signals:** passwords stored in plaintext, hashed with an unsalted fast digest (`md5`, `sha1`), or "hashed" with a reversible or truncated encoding (e.g. a repeated base64 prefix) instead of a vetted password-hashing function (bcrypt, argon2, scrypt, the framework's helper).
- **Impact:** stored credentials are readable or trivially crackable — equivalent to plaintext.
- **Fix:** RP-09.

### AP-04 — Sensitive data leaked via serialization
- **Signals:** a response (serializer, `to_dict`, raw row, `SELECT *` returned as-is — lists, details, login, errors) carries a field its caller does not need. Three variants, checked separately:
    - **Credentials and secrets** — password or hash, token, API/gateway key, session id.
    - **Payment card data** — full PAN, CVV or expiry unmasked (last 4 digits is the masked form, not a finding).
    - **Other people's personal data** — name, email, national ID, phone, address or birth date of subjects other than the caller, from an endpoint that does not need them. An identifier (email, national ID, phone) returned in full to anyone but its subject is this variant even behind auth (LGPD art. 6 III, minimization); the masked form (`<x>***@<domain>`) is not a finding.
- **Severity:** CRITICAL for credentials and card data. Other people's personal data: CRITICAL when anonymous callers reach it, HIGH when any authenticated account does.
- **Not AP-05:** AP-05 is the missing guard, AP-04 the payload; when both apply to a route, report both.
- **Impact:** every client receives secrets or other people's data — offline attacks on hashes, card fraud, bulk harvesting of personal data.
- **Fix:** RP-09.

### AP-05 — Missing authentication/authorization on sensitive endpoints
- **Signals:** a mutating route (`POST`/`PUT`/`DELETE`) or one whose path/name signals restricted access (`/admin`, `/internal`, reports, user deletion) with no auth construct in its own handler chain (middleware/decorator, header/session/token check), confirmed by a project-wide search (`auth`, `token`, `session`, `role`, `permission`). Softer variant: a login issues a token/session that nothing ever verifies; or an action on an existing account authorized by an identifier alone (email, id) while the credential sent with it is ignored. Check every route's own chain — a protected sibling proves nothing.
- **Impact:** any caller reads, modifies or deletes data through the endpoint. Destructive or sensitive endpoints make this CRITICAL regardless of the surrounding architecture.
- **Fix:** RP-16.

### AP-17 — Privilege escalation via self-service registration
- **Signals:** a public signup reads a privilege field (`role`, `tipo`, `is_admin`, `permissions`, `group`) from the body and persists it, validating only that the *value* is allowed, not that the *caller* may assign it — and an authorization guard reads that field back. Also: an update endpoint that lets a user raise their own privilege.
- **Detection order:** invisible while the project has no auth at all (nothing to bypass). Re-check after Phase 3 adds authorization — RP-16 can create it.
- **Impact:** every authorization guard is bypassable with one anonymous request.
- **Fix:** RP-16.

### AP-20 — Arbitrary query/code execution endpoint
- **Signals:** a request-controlled string handed to an interpreter as the whole statement — `execute(body["sql"])`, `db.raw(req.query.q)`, `eval`/`exec`, a shell command built from the request. A fixed statement with request values is AP-01, not this.
- **Separate finding:** parameterization cannot fix it and authentication only narrows who uses it; report it even when AP-05 is reported for the same route.
- **Impact:** whoever reaches the endpoint owns the database (or the host) and bypasses every model invariant.
- **Fix:** RP-19.

## HIGH

### AP-06 — God Class / no architectural separation
- **Signals:** one file or class holds connection/schema setup, routes and business rules with no intermediate layer; routes or controllers running queries; domain rules inside SQL-access functions; one per-domain module (`services/`, `helpers/`, `managers/`) that validates the request, runs the queries and decides the response — layers renamed, not separated.
- **Detection:** `arch-check.sh` scans route files only; controllers running queries are confirmed by reading each controller.
- **Impact:** nothing can be tested in isolation; a change in one domain risks every other.
- **Severity:** HIGH. CRITICAL when separation of responsibilities is violated completely: one file or class merges DB access, business rules and routing, **or** the separation is only nominal — the file that registers routes (or a controller) opens connections / runs raw SQL itself, bypassing the data layer that exists elsewhere. Routes that call model or ORM methods (e.g. `Task.query.get(id)`) are not this escalation; rule logic in those routes is AP-22 (HIGH).
- **Fix:** RP-03, RP-14, RP-11.

### AP-07 — Business logic duplicated across controllers/routes
- **Signals:** the same rule (validation, status/date computation, derived field, row serialization) re-implemented in several handlers instead of one shared method.
- **Impact:** copies diverge the moment only one is fixed.
- **Fix:** RP-04.

### AP-08 — Global mutable state
- **Signals:** module-level mutable objects (cache dict, counter, shared DB connection) written or used by concurrent request handlers without synchronization or a defined lifecycle.
- **Impact:** state leaks between requests and users and grows without bound; behavior depends on request history, and becomes a race condition in multi-threaded runtimes.
- **Fix:** RP-05.

### AP-22 — Layer leakage: orchestration outside a Service
- **Signals (any one):** a model imports another model; a model imports HTTP/routing code; one
  controller function uses **≥ 2 models** or a model plus an external system (so it decides the
  use case, not only the response); a model raises response-level errors; routes exist but the
  controller layer is missing, empty or unwired (a route file importing no controller, a route
  importing a model/service directly, a controller no route imports). Detection: the layout
  section of `arch-check.sh`, then read each cited function.
- **Not AP-06:** AP-06 is persistence or rules trapped in routes/one file; AP-22 is layers that exist
  but reach into each other. When both apply to a function, report both.
- **Impact:** a use case cannot be tested without its neighbours, and a change to one entity's
  model breaks another's; the same flow is copied when a second entry point appears.
- **Fix:** RP-21.

## MEDIUM

### AP-23 — Supporting modules loose at the project root
- **Signals:** source files at the project root other than the entry point, standalone scripts
  (a seed), its config-tool files and tests — e.g. authentication, error handling, settings, security helpers, database setup —
  or layer files (`controllers`, `models`) at the root instead of in role directories. Detection:
  the AP-23 lines of `arch-check.sh`. Go, Java, Kotlin and C# are not checked (package code at
  the root is their idiom).
- **Impact:** the layout does not show which layer a file belongs to; every new cross-cutting
  module lands in the root and the root stops being a map of the architecture.
- **Fix:** RP-22.

### AP-09 — N+1 queries
- **Signals:** a loop issuing one query per iteration for related rows instead of a join, `IN (...)` or eager loading.
- **Impact:** query count grows linearly (or multiplicatively when nested) with result size.
- **Fix:** RP-06.

### AP-10 — Missing pagination on list endpoints
- **Signals:** a list/report endpoint returns a whole table with no limit/offset, page or cursor parameters.
- **Impact:** response time and payload grow with the table.
- **Fix:** RP-07.

### AP-11 — Dead / disconnected layer
- **Signals:** a fully implemented module/service never imported or called from any route/controller.
- **Impact:** readers believe the feature is live; the code rots.
- **Fix:** RP-10.

### AP-12 — Deprecated APIs and vulnerable or end-of-life versions
Two halves, both mandatory, for the runtime, the framework and every dependency the code imports.
Never answered from memory.

1. **Deprecated calls in the version in use.** Look up what that exact version deprecates or
   removed, grep the code for those calls and recommend the documented modern equivalent.
   Illustrative shapes only: `datetime.utcnow()` → `datetime.now(timezone.utc)`,
   `Model.query.get(id)` → `session.get(Model, id)`, `new Buffer(x)` → `Buffer.from(x)`.
2. **The version itself.** The latest release, known advisories for the version in use with each
   advisory's first fixed version, and end-of-life of the release line and runtime. A version with
   an advisory or past end-of-life is a finding citing the manifest line; merely being behind the
   latest release is not.

**Sources:** official docs, changelogs and migration guides; the package registry; OSV
(`POST https://api.osv.dev/v1/query`), GitHub Advisories, `pip-audit`/`npm audit`. Context7 is
optional: it may locate official material, never the only authority; if it fails, use the others.

**Gate:** one `AP-12:` line per component in `Checked, no findings`
(`references/audit-report-template.md`). A component whose every applicable source failed is
`BLOCKED`: Phase 2 is incomplete — do not ask the Phase 3 question.

- **Severity:** MEDIUM. CRITICAL when the deprecation notice gives a security reason (insecure, not merely superseded) or the advisory is reachable through how this code uses the package — cite the notice or advisory.
- **Impact:** deprecated calls break on upgrade; a vulnerable or unsupported release ships known flaws that no longer get fixes.
- **Fix:** RP-12.

### AP-18 — Personal data written to logs
- **Signals:** a log call carrying email, name, national ID, phone, address, birth date, an IP tied to a person or a card number unmasked — or logging a whole request body/model object. Check `except`/`catch` blocks and error middleware too.
- **Not AP-13:** AP-13 is the medium (`print`), this is the content; a structured logger writing emails is AP-18.
- **Severity:** MEDIUM; CRITICAL when the logged value is a credential or a full card number.
- **Impact:** logs are copied, shipped and retained far longer and less carefully than the database, outside its access control.
- **Fix:** RP-17.

### AP-19 — Incomplete data-subject rights (erasure, export, retention)
- **Signals:** a user deletion that misses a place holding the user's id — audit/event tables without an FK (id inside free text), in-memory structures, rows reached only through a join — or a non-transactional deletion. The absence of any deletion path is also this finding (see "Absent requirements"). So is, when the domain holds personal data, no path to export a subject's data or no retention limit on it.
- **Impact:** the subject stays identifiable after being told they were removed; LGPD art. 18 VI / GDPR art. 17 unmet; export/retention: LGPD art. 18 II/V, art. 16 / GDPR art. 15, 20, 5(1)(e) unmet.
- **Legitimate alternative:** de-link rather than destroy rows kept for security or accounting (null the user id).
- **Fix:** RP-18.

### AP-21 — Missing input validation / raw exception leakage
- **Signals:** request fields used without presence, type or range checks, so bad input surfaces as a 500; a referenced id taken from the request never checked to exist (the row is stored pointing at nothing); an error path returning the exception text or a stack trace; validation present in one route and absent from its sibling (create validates, update does not).
- **Not AP-07:** a rule missing at the boundary is AP-21; the same rule duplicated is AP-07.
- **Severity:** MEDIUM; HIGH when one request can crash the process (an exception thrown outside the framework's error handling, e.g. inside a callback) — every user loses the service.
- **Impact:** client errors reported as server failures, internals disclosed to any caller, invalid values stored.
- **Fix:** RP-20 with RP-11.

## LOW

### AP-13 — Print/console-based logging
- **Signals:** `print(...)`/`console.log(...)` for operational logging instead of the logging module or a structured logger.
- **Impact:** no levels, fields or rotation; errors cannot be filtered from noise.
- **Fix:** RP-08.

### AP-14 — Hardcoded configuration / magic values
- **Signals:** inline literals that are configuration (valid categories, statuses, limits, rates, ports, paths) — including each member of such a list repeated alone elsewhere (a status literal inside an SQL string or a schema default). Cite every location.
- **Impact:** every change needs a source edit, and copies drift apart.
- **Fix:** RP-13.

### AP-15 — Unused imports
- **Signals:** imported modules/names never referenced in the file.
- **Impact:** obscures the file's real dependencies.
- **Fix:** RP-13.

### AP-16 — Inconsistent naming conventions
- **Signals:** no single convention applied — some domain nouns translated and others not, a role word in both languages across sibling files (`<entidade>_controller` next to `<entity>Controller`), different verbs for the same operation.
- **Not a signal:** pattern vocabulary in English plus domain vocabulary in the project's language, applied uniformly (`<entidade>_controller`, `listar_<entidades>`). Never translate domain nouns to "fix" it.
- **Impact:** names cannot be predicted from roles; slows onboarding and review.
- **Fix:** RP-15.
