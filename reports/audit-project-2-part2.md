```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript / Node.js + Express 4.18.2, sqlite3 6.0.1
Files:   17 analyzed | ~391 lines of code

## Resolved since audit-project-2.md
All 4 CRITICAL findings from the previous part are resolved: the God Class (`AppManager.js`)
is now split into controllers/models/services/routes; secrets (`dbPass`, `paymentGatewayKey`)
are sourced from `process.env` via config/index.js with no literal values in source; passwords
are hashed with `crypto.scryptSync` + per-user salt (utils/crypto.js) instead of the reversible
base64 `badCrypto()`; and the payment gateway service now masks the card number before logging
(`maskCard()` in services/paymentGatewayService.js) instead of logging it in plaintext.
Also resolved: the orphaned-records-on-delete HIGH finding (userModel.deleteCascade removes
payments and enrollments before the user row); the N+1 query MEDIUM finding (enrollmentModel.
findDetailsByCourseIds now issues one batched `WHERE course_id IN (...)` query); console-based
logging (logger.js is used everywhere via `logger.info`/`logger.error`); and the unused
`totalRevenue` import (no unused imports found anywhere in the current codebase).

Still open (reappeared, partially fixed):
- "Global Mutable State Used as a Cache" — `globalCache` (a plain object) is now wrapped in a
  `CacheService` class (services/cacheService.js), matching RP-05's own "after" example almost
  verbatim, but the underlying problem the finding described is unchanged: it's still a
  module-level singleton `Map` mutated from every checkout request with no TTL, eviction, or
  synchronization. It has also gotten strictly worse on one axis — a project-wide search shows
  `cacheService.get` is never called anywhere, so it is now purely write-only. Carried into this
  report's HIGH findings below rather than counted as new.
- "Missing Pagination on List/Report Endpoints" — the financial report now accepts `page`/
  `per_page` and applies `LIMIT`/`OFFSET` (reportController.js:7-9), but `per_page` is floored
  at 1 and never capped, so a client can still force the full table (and all joined rows) in one
  request. Carried into this report's MEDIUM findings below.
- "Hardcoded Magic Default Password" — unchanged: `FALLBACK_PASSWORD = '123456'`
  (src/models/userModel.js:4) is still substituted whenever `rawPassword` is falsy, and
  checkoutController.js:12 still never requires `pwd`. Re-classified CRITICAL/AP-02 in this
  report (was LOW/AP-13 previously) — on closer reading this is a hardcoded credential that
  determines a real account's password, matching AP-02's "literal strings assigned to
  variables/constants named like ... PASSWORD" signal directly, not just a generic magic value.
  Carried into this report's CRITICAL findings below.
- "Inconsistent Language/Naming Conventions" — unchanged: Portuguese user-facing strings
  ('Curso não encontrado', 'Erro DB', 'Pagamento recusado', ...) are still mixed with English
  identifiers throughout, and the request body still uses abbreviated field names (`usr`, `eml`,
  `pwd`, `c_id`, `card`) at checkoutController.js:10. Per RP-15's scope limit these are
  response/request-contract strings and field names, so — same as last time — this is reported
  but not expected to be fixed by Phase 3. Carried into this report's LOW findings below.

## Summary
CRITICAL: 1 | HIGH: 2 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] Hardcoded fallback password provisions real accounts with a known credential
File: src/models/userModel.js:4,16 (root cause: src/controllers/checkoutController.js:10-14)
Description: `userModel.create()` hashes `FALLBACK_PASSWORD = '123456'` whenever `rawPassword` is falsy. `checkoutController.checkout()` only requires `name`, `email`, `courseId`, and `cardNumber` (line 12) — `pwd` is never validated — so any checkout request that omits `pwd` silently creates a brand-new user account secured by a password that's hardcoded in source.
Impact: every account created this way is protected by a password anyone reading (or guessing) the code already knows — a direct account-takeover vector the moment any login/auth endpoint is added.
Recommendation: AP-02 / RP-02 — require `rawPassword` explicitly and reject the checkout (400) if missing, or generate a random one-time password delivered out-of-band; never default silently to a fixed value.
Status: Still open (reappeared, unchanged code) — see "Resolved since audit-project-2.md" above for the severity reclassification.

### [HIGH] Duplicated, ad hoc error handling bypasses the existing centralized handler — and one path isn't guarded at all
File: src/controllers/checkoutController.js:17-21,25-29,35-39,46-50,52-56,58; src/controllers/reportController.js:12-16,22-26; src/controllers/userController.js:6-10; src/middlewares/errorHandler.js:1-8
Description: Every model call in every controller is wrapped in its own try/catch that manually maps to a response (`res.status(500).send('Erro DB')`, `'Erro Matrícula'`, `'Erro Pagamento'`, etc.), even though `app.js` already registers a centralized `errorHandler` middleware for exactly this purpose. Worse, `checkoutController.js:58` (`await auditLogModel.create(...)`) has no try/catch at all — in Express 4 a rejected promise inside an async handler is not forwarded to `next(err)` automatically, so a DB failure at that specific line reaches neither the ad hoc pattern used everywhere else nor the centralized handler; the request simply hangs.
Impact: five near-identical error-to-response blocks per controller multiply maintenance cost and have already drifted (plain text vs JSON, inconsistent messages), and the one unguarded `await` is an unhandled-rejection risk that can hang a client connection or crash the process depending on the Node version's unhandled-rejection policy.
Recommendation: AP-06 / RP-11 — let model/service errors propagate (`next(err)` or an async-error wrapper around every handler) and centralize the response shape in the existing `errorHandler` middleware; delete the per-call try/catch boilerplate.
Status: New — this controller-per-domain split (and the centralized `errorHandler` it left unused) did not exist in this form in `AppManager.js`; not present in audit-project-2.md.

### [HIGH] Global mutable, unbounded, write-only cache
File: src/services/cacheService.js:1-15; written at src/controllers/checkoutController.js:59
Description: `cacheService` is a singleton `Map` mutated from every checkout request with no eviction, TTL, or size bound. A project-wide search confirms `cacheService.get` is never called anywhere — every write is permanent and never read back.
Impact: memory grows without bound as `last_checkout_<userId>` keys accumulate forever (one per user who ever checks out), and the shared `Map` is mutated from concurrent request handlers with no synchronization — a real production memory leak that delivers zero functional benefit today.
Recommendation: AP-07 / RP-05 — either wire the cache into an actual read path or delete it; if kept, back it with a bounded/TTL cache instead of a plain module-level `Map`.
Status: Still open (reappeared, partially fixed) — see "Resolved since audit-project-2.md" above.

### [MEDIUM] Dead configuration fields (DB/SMTP credentials never consumed)
File: src/config/index.js:4-5,7 (dbUser, dbPass, smtpUser); sourced from .env.example:1-2,4
Description: `config/index.js` reads `DB_USER`, `DB_PASS`, and `SMTP_USER` into the exported config object, but a project-wide search shows none of the three is referenced anywhere else in `src/`. The app talks to an in-memory SQLite database that needs no credentials and never sends email.
Impact: misleads anyone reading `config/`/`.env.example` into believing external DB auth and SMTP are wired up; if these ever are given real values, they become live credentials with no code path consuming them.
Recommendation: AP-10 / RP-10 — delete the three unused fields (and their `.env` entries) or wire them into a real DB/SMTP client if that integration is actually planned.
Status: New — the config module itself (and its unused fields) is a product of the Phase 3 refactor; audit-project-2.md's `dbPass` finding was about a literal hardcoded secret in `utils.js`, a different problem, now resolved.

### [MEDIUM] Pagination present but unbounded
File: src/controllers/reportController.js:7-9
Description: `per_page` is read from the query string and floored at 1 via `Math.max(...)`, but never capped — a client can pass `per_page=999999999` and receive every course (plus every joined enrollment/payment row) in a single response.
Impact: defeats the purpose of the pagination that's already implemented; a single request can still force the full-table scan and payload size the pagination mechanism exists to prevent.
Recommendation: AP-09 / RP-07 — clamp `per_page` to a sane maximum (e.g. `Math.min(perPage, 100)`) in addition to the existing floor.
Status: Still open (reappeared, partially fixed) — see "Resolved since audit-project-2.md" above.

### [LOW] Inconsistent language/naming conventions
File: src/controllers/checkoutController.js:10,13,20,22,28,38,49,55 (request-field abbreviations and Portuguese user-facing strings); src/controllers/reportController.js:15,25; src/controllers/userController.js:9,12
Description: User-facing error strings are in Portuguese ('Curso não encontrado', 'Erro DB', 'Pagamento recusado', ...) while all code identifiers are in English, and the checkout request body still uses abbreviated field names (`usr`, `eml`, `pwd`, `c_id`, `card`) instead of the descriptive names used internally (`name`, `email`, `courseId`, `cardNumber`).
Impact: slows onboarding and code review; the same ambiguity flagged last time remains unresolved.
Recommendation: AP-15 / RP-15 — pick one convention for new/internal code going forward. Per RP-15's scope limit, the existing request field names and user-facing message strings are part of the API contract and were correctly left unchanged by Phase 3 — this finding is expected to stay open/documented rather than be fixed.
Status: Still open (reappeared, unchanged) — see "Resolved since audit-project-2.md" above.

### [LOW] Inconsistent response-format conventions
File: src/controllers/checkoutController.js:13,20,22,28,38,49,55,61; src/controllers/userController.js:9,12; src/controllers/reportController.js (JSON-only, for contrast)
Description: Responses mix plain-text bodies (`res.status(400).send('Bad Request')`, `res.send('Usuário e seus registros...')`) with JSON bodies (`res.json(...)`) across the same route layer, and the one JSON success payload that exists mixes snake_case (`enrollment_id`) with the camelCase used everywhere else in the JS code (`courseId`, `userId`, `enrollmentId`).
Impact: API consumers can't rely on a single content-type or casing convention, forcing per-endpoint special-casing on the client.
Recommendation: AP-15 / RP-15 — standardize on JSON responses with one casing convention going forward; per RP-15's scope limit, the existing `enrollment_id` response field is part of the API contract and must be documented, not silently renamed.
Status: New — a distinct observation from the naming-conventions finding above (response shape, not identifiers); not raised in audit-project-2.md.

### [LOW] Pagination default hardcoded outside the config module
File: src/controllers/reportController.js:4
Description: `DEFAULT_PAGE_SIZE = 20` is declared directly in the controller instead of living in `src/config/index.js`, which already centralizes the app's other tunables (`port`, `logLevel`).
Impact: changing the default page size requires editing a controller file instead of one central config source, and the value can't be overridden per-environment the way `PORT`/`LOG_LEVEL` already are.
Recommendation: AP-13 / RP-13 — move `DEFAULT_PAGE_SIZE` into `config/index.js` (env-overridable) and import it from there.
Status: New — this controller (and its constant) is a product of the Phase 3 refactor; not present in audit-project-2.md.

================================
Total: 8 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
