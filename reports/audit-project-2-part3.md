```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript / Node.js 26 + Express 4.22.1, sqlite3 6.0.1
Files:   17 analyzed | ~391 lines of code

## Resolved since audit-project-2-part2.md
Nothing. `audit-project-2-part2.md` ends at the Phase 2 gate ("Proceed with refactoring
(Phase 3)? [y/n]") with no recorded answer, and `git log -- ecommerce-api-legacy` shows no
refactor commit after it — the last code change to this project is
`f5c6fca refactor(ecommerce-api-legacy): restructure into MVC and resolve critical/high findings`,
which is the Phase 3 of round 1. All 8 findings from part2 were re-verified against the
current source and all 8 are still open, unchanged, at the same lines. They are carried into
this report verbatim in substance (re-verified line references), not counted as new.

Carried forward from audit-project-2-part2.md, all still open and unchanged:
- CRITICAL "Hardcoded fallback password" — `FALLBACK_PASSWORD = '123456'` still at
  src/models/userModel.js:4, still applied at :16; checkoutController.js:12 still does not
  require `pwd`.
- HIGH "Duplicated ad hoc error handling" — the six per-call try/catch blocks and the
  unguarded `await auditLogModel.create(...)` are all still present.
- HIGH "Global mutable, unbounded, write-only cache" — `cacheService.get` is still called
  from nowhere in `src/` (verified by project-wide grep); the only reference is the write at
  checkoutController.js:59.
- MEDIUM "Dead configuration fields" — `dbUser`, `dbPass`, `smtpUser` still read in
  config/index.js:4-5,7 and still referenced nowhere else in `src/`.
- MEDIUM "Pagination present but unbounded" — reportController.js:8 still floors `per_page`
  without capping it.
- LOW "Inconsistent language/naming conventions" — unchanged; per RP-15's scope limit this
  one is expected to stay documented rather than fixed.
- LOW "Inconsistent response-format conventions" — unchanged.
- LOW "Pagination default hardcoded outside the config module" — reportController.js:4
  unchanged.

This round adds 8 new findings, all in code that already existed but was not surfaced by the
previous two passes: they concern transactional integrity, the controller/service boundary,
error swallowing in the model layer, request validation, and process bootstrap.

## Summary
CRITICAL: 1 | HIGH: 5 | MEDIUM: 5 | LOW: 5

## Findings

### [CRITICAL] Hardcoded fallback password provisions real accounts with a known credential
File: src/models/userModel.js:4,16 (root cause: src/controllers/checkoutController.js:10-14)
Description: `userModel.create()` hashes `FALLBACK_PASSWORD = '123456'` whenever `rawPassword` is falsy, and `checkoutController.checkout()` validates only `name`, `email`, `courseId` and `cardNumber` (line 12) — `pwd` is never required — so any checkout that omits `pwd` silently creates a real account secured by a password hardcoded in source.
Impact: every account created that way is protected by a credential anyone reading the repository already knows; it becomes a direct account-takeover vector the moment any authentication endpoint exists.
Recommendation: AP-02 / RP-02 — require `rawPassword` explicitly and reject the checkout with 400 when it is missing, or generate a random one-time password delivered out-of-band; never default silently to a fixed literal.
Status: Still open (third consecutive round, code unchanged).

### [HIGH] Checkout performs a multi-step money-moving write with no transaction or compensation
File: src/controllers/checkoutController.js:42-56 (charge at :42, enrollment insert at :47, payment insert at :53)
Description: The checkout charges the card first (`paymentGatewayService.charge`), then inserts the enrollment, then inserts the payment row — three sequential writes with no transaction (`BEGIN`/`COMMIT`) and no rollback or compensating action on any of the three failure branches, each of which just returns a 500.
Impact: a failure at :47 leaves the customer charged with no enrollment and no payment record — money taken, nothing delivered, and no trace in the `payments` table to reconcile against. A failure at :53 leaves an enrollment the finance report will never attribute revenue to, because the report sums only rows with `payment_status = 'PAID'` (reportController.js:36). Both states are silent and unrecoverable without manual DB surgery.
Recommendation: AP-05 / RP-01 — move the whole sequence into a `checkoutService` that owns a single transaction boundary (`db.serialize` + `BEGIN`/`COMMIT`/`ROLLBACK`) and only charges once the persistence side is known to succeed, or records a reversal when it does not.
Status: New — the sequence existed in `AppManager.js` too, but the previous two reports scoped the checkout findings to secrets, hashing and logging and never examined write ordering.

### [HIGH] Business orchestration and aggregation live in controllers instead of a service layer
File: src/controllers/checkoutController.js:9-62; src/controllers/reportController.js:28-43
Description: `checkoutController.checkout()` directly orchestrates five models (course lookup, user find-or-create, gateway charge, enrollment insert, payment insert, audit log, cache write) — that is the entire domain workflow, not HTTP concerns. `reportController.financialReport()` likewise computes the domain aggregation in the handler: it groups enrollment rows by course into a `Map` (:28-32) and derives revenue by summing only `PAID` rows (:36). The `services/` folder exists but holds only a fake payment gateway and the cache — no domain service.
Impact: neither the checkout workflow nor the revenue rule can be unit-tested without Express `req`/`res` objects and a live SQLite handle; the "revenue counts only PAID payments" rule is invisible to anyone reading the model layer and will be re-implemented differently the first time a second report or an invoice endpoint needs it.
Recommendation: AP-05 / AP-06 / RP-01 — extract `services/checkoutService.js` and `services/reportService.js`; controllers keep only parse → one service call → serialize.
Status: New — this is a direct consequence of round 1's Phase 3, which split `AppManager.js` into controllers and models but created no domain service layer; not raised in either previous report.

### [HIGH] Duplicated, ad hoc error handling bypasses the centralized handler — and one path is unguarded
File: src/controllers/checkoutController.js:17-21,25-29,35-39,46-50,52-56,58; src/controllers/reportController.js:12-16,22-26; src/controllers/userController.js:6-10; src/middlewares/errorHandler.js:1-8
Description: Every model call in every controller carries its own try/catch mapping to a hand-written response (`res.status(500).send('Erro DB')`, `'Erro Matrícula'`, `'Erro Pagamento'`, `'Erro ao deletar usuário'`), even though `app.js:14` already registers a centralized `errorHandler`. `checkoutController.js:58` (`await auditLogModel.create(...)`) has no guard at all — Express 4 does not forward a rejected promise from an async handler to `next(err)`, so a failure there reaches neither pattern and the request hangs.
Impact: nine near-identical error blocks that have already drifted (plain text here, JSON there, different messages for the same class of failure), plus one unhandled rejection that can hang a client connection; the centralized handler that exists to solve exactly this is dead weight for every route.
Recommendation: AP-06 / RP-11 — wrap handlers in an async-error adapter (or `next(err)`), delete the per-call try/catch boilerplate, and let `errorHandler` own the single response shape.
Status: Still open (unchanged since audit-project-2-part2.md).

### [HIGH] Cascade delete swallows errors and reports success for users that do not exist
File: src/models/userModel.js:26-40 (unguarded `db.run` at :29-32 and :33); src/controllers/userController.js:3-13
Description: `deleteCascade()` issues three statements inside `db.serialize`, but only the last one (`DELETE FROM users`) passes an error callback — the `DELETE FROM payments` (:29-32) and `DELETE FROM enrollments` (:33) calls have no callback, so their errors are dropped on the floor and the promise still resolves. The function also never inspects `this.changes`, so deleting a non-existent id resolves normally and `userController` replies 200 with "Usuário e seus registros associados (matrículas e pagamentos) foram deletados."
Impact: a partial cascade failure is indistinguishable from success — the caller is told enrollments and payments were removed while they are still in the database, which is precisely the orphaned-records corruption the round-1 HIGH finding was supposed to close. `DELETE /api/users/9999` likewise reports a deletion that never happened, so no client can tell a real delete from a no-op.
Recommendation: AP-06 / RP-11 — give every statement in the cascade an error callback (or promisify `db.run` once and `await` each step inside a transaction), check `this.changes` on the user delete, and return 404 when no row matched.
Status: New — round 1's fix introduced `deleteCascade` and both previous reports treated the orphaned-records finding as resolved on the strength of the statements being present, without checking their error handling.

### [HIGH] Global mutable, unbounded, write-only cache
File: src/services/cacheService.js:1-15; written at src/controllers/checkoutController.js:59
Description: `cacheService` is a module-level singleton `Map` mutated from every checkout request with no eviction, TTL or size bound. A project-wide grep confirms `cacheService.get` is called from nowhere — every write is permanent and never read back.
Impact: memory grows without bound as `last_checkout_<userId>` keys accumulate (one per user who ever checks out), and the shared `Map` is mutated from concurrent handlers with no synchronization — a real leak that delivers zero functional benefit today.
Recommendation: AP-07 / RP-05 — wire the cache into an actual read path or delete it; if kept, back it with a bounded/TTL cache instead of a plain module-level `Map`.
Status: Still open (unchanged since audit-project-2-part2.md).

### [MEDIUM] No request validation layer — route parameters are never validated
File: src/routes/index.js:8-10; src/controllers/checkoutController.js:10-14; src/controllers/userController.js:4
Description: The three routes register handlers directly with no validation middleware. `checkout` performs a bare truthiness check on four fields (:12) — `c_id` is passed to the query as-is with no numeric check, and `card` is passed to `maskCard()` with no type or length check. `deleteUser` takes `req.params.id` and hands it straight to the model with no validation at all.
Impact: a non-string `card` (e.g. `{"card": 123}`) reaches `cardNumber.slice()` in paymentGatewayService.js:7 and throws a TypeError inside an unguarded async handler; a non-numeric `c_id` silently matches nothing and returns 404 instead of 400, so clients cannot distinguish a malformed request from a missing course.
Recommendation: AP-09 / RP-07 — add a validation middleware (or a per-route schema) that coerces and rejects malformed input at the boundary before the controller runs.
Status: New — not raised in either previous report.

### [MEDIUM] Dead configuration fields (DB/SMTP credentials never consumed)
File: src/config/index.js:4-5,7 (`dbUser`, `dbPass`, `smtpUser`); sourced from .env.example:1-2,4
Description: `config/index.js` reads `DB_USER`, `DB_PASS` and `SMTP_USER` into the exported config object, but none of the three is referenced anywhere else in `src/`. The app talks to an in-memory SQLite database that needs no credentials and never sends email.
Impact: misleads anyone reading `config/` or `.env.example` into believing external DB auth and SMTP are wired up; if these are ever given real values they become live credentials with no code path consuming them.
Recommendation: AP-10 / RP-10 — delete the three fields and their `.env` entries, or wire them into a real DB/SMTP client if that integration is actually planned.
Status: Still open (unchanged since audit-project-2-part2.md).

### [MEDIUM] Pagination present but unbounded
File: src/controllers/reportController.js:7-9
Description: `per_page` is read from the query string and floored at 1 via `Math.max(...)`, but never capped — a client can pass `per_page=999999999` and receive every course plus every joined enrollment/payment row in one response.
Impact: defeats the pagination that is already implemented; a single request can still force the full-table scan and payload size the mechanism exists to prevent.
Recommendation: AP-09 / RP-07 — clamp `per_page` to a sane maximum (e.g. `Math.min(perPage, 100)`) in addition to the existing floor.
Status: Still open (unchanged since audit-project-2-part2.md).

### [MEDIUM] Password verification is implemented but unreachable — and broken if it were reached
File: src/utils/crypto.js:11-17
Description: `verifyPassword()` is exported but called from nowhere in `src/`; there is no login or authentication route at all, so the hashing half of the pair (`hashPassword`) writes credentials that nothing ever reads. The function is also latently broken: `crypto.timingSafeEqual` throws `RangeError` when its two buffers differ in length, so any stored hash whose length does not match `KEY_LENGTH` would raise instead of returning `false`.
Impact: a reader of `utils/crypto.js` reasonably concludes authentication exists; it does not. The bug would only surface the day someone wires the function up, at which point it fails on malformed input instead of rejecting it cleanly.
Recommendation: AP-10 / RP-10 — either add the authentication route this function implies, or remove it; if kept, compare lengths before `timingSafeEqual` and return `false` on mismatch.
Status: New — not raised in either previous report.

### [MEDIUM] The app binds the port at import time, so it cannot be loaded without starting a server
File: src/app.js:8-20 (`initSchema()` at :11, `app.listen(...)` at :16, `module.exports = app` at :20)
Description: `app.js` builds the Express app, runs `initSchema()`, and calls `app.listen()` as module side effects, then exports the app. Because `listen` has already fired by the time the export is visible, `require('./src/app')` always opens a socket on `config.port` and seeds the schema.
Impact: the export exists for tests but is unusable by them — any test or tooling that imports the app binds port 3000 and fails on `EADDRINUSE` when a server is already running (a real constraint here: CLAUDE.md notes projects 1 and 3 already contend for a single port). It also makes the schema bootstrap impossible to control from a test.
Recommendation: AP-05 / RP-01 — split app construction (`app.js`, exports the configured app, no side effects) from the process bootstrap (`server.js`, calls `initSchema()` and `listen`), and point `package.json` `main`/`start` at the latter.
Status: New — not raised in either previous report.

### [LOW] Inconsistent language/naming conventions
File: src/controllers/checkoutController.js:10,13,20,22,28,38,49,55; src/controllers/reportController.js:15,25; src/controllers/userController.js:9,12
Description: User-facing strings are Portuguese ('Curso não encontrado', 'Erro DB', 'Pagamento recusado', ...) while all identifiers are English, and the checkout request body uses abbreviated field names (`usr`, `eml`, `pwd`, `c_id`, `card`) that are immediately destructured into descriptive internal names (`name`, `email`, `courseId`, `cardNumber`).
Impact: slows onboarding and code review; the destructuring at :10 is the only place the two vocabularies are reconciled.
Recommendation: AP-15 / RP-15 — pick one convention for new and internal code. Per RP-15's scope limit the existing request field names and message strings are part of the API contract and should be documented, not silently renamed.
Status: Still open (expected to stay documented rather than fixed).

### [LOW] Inconsistent response-format conventions
File: src/controllers/checkoutController.js:13,20,22,28,38,49,55,61; src/controllers/userController.js:9,12; src/controllers/reportController.js:18,45 (JSON-only, for contrast)
Description: Responses mix plain-text bodies (`res.status(400).send('Bad Request')`, `res.send('Usuário e seus registros...')`) with JSON bodies across the same route layer, and the single JSON success payload mixes snake_case (`enrollment_id`) with the camelCase used everywhere else in the code.
Impact: clients cannot rely on one content type or one casing convention and must special-case per endpoint.
Recommendation: AP-15 / RP-15 — standardize on JSON with one casing convention going forward; the existing `enrollment_id` field is part of the contract and must be documented, not silently renamed.
Status: Still open (unchanged since audit-project-2-part2.md).

### [LOW] Pagination default hardcoded outside the config module
File: src/controllers/reportController.js:4
Description: `DEFAULT_PAGE_SIZE = 20` is declared in the controller instead of `src/config/index.js`, which already centralizes the app's other tunables (`port`, `logLevel`).
Impact: changing the default page size means editing a controller, and the value cannot be overridden per environment the way `PORT` and `LOG_LEVEL` already are.
Recommendation: AP-13 / RP-13 — move `DEFAULT_PAGE_SIZE` into `config/index.js` as an env-overridable value and import it.
Status: Still open (unchanged since audit-project-2-part2.md).

### [LOW] Unknown routes bypass the JSON error contract
File: src/app.js:13-14; src/routes/index.js:8-10
Description: `app.use(routes)` is followed directly by `app.use(errorHandler)` with no catch-all 404 middleware in between. A request to an unregistered path falls through to Express's built-in final handler, which returns an HTML body (`<pre>Cannot GET /api/nope</pre>`), never reaching `errorHandler`.
Impact: the API answers unknown paths with HTML while every handled error answers with JSON, so a client parsing responses as JSON breaks on exactly the case (a typo'd or removed endpoint) where a clear machine-readable error matters most.
Recommendation: AP-06 / RP-11 — register a catch-all 404 middleware after the router that produces the same JSON error shape as `errorHandler`.
Status: New — not raised in either previous report.

### [LOW] Stale boilerplate metadata contradicts the project's actual identity
File: package.json:2-4 (`"name": "desafio-arquitetura-ia-boilerplate"`, `"description": "Boilerplate com código legado para refatoração"`); src/app.js:17 (`Frankenstein LMS rodando na porta ...`)
Description: The package is still named and described as the pre-refactor boilerplate, the boot log still calls the service "Frankenstein LMS" — a name from the legacy state that appears nowhere else — and `scripts` contains only `start`, with no `test` entry despite `manual-tests.sh` and `arch-check.sh` living at the project root.
Impact: the package manifest and the first line of every boot log describe a codebase that no longer exists, and the two validation scripts are undiscoverable through `npm run`.
Recommendation: AP-13 / RP-13 — set an accurate `name`/`description`, source the service name in the boot log from config, and expose the existing scripts via `npm test` / `npm run arch-check`.
Status: New — not raised in either previous report.

================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
