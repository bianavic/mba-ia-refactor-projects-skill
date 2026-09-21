```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript / Node.js 26 + Express 4.22.1, sqlite3 6.0.1
Files:   24 analyzed | ~475 lines of code

## Resolved since audit-project-2-part3.md
Manual, targeted re-audit — not a full from-scratch Phase 1-3 skill run. Triggered by writing
`ecommerce-api-legacy/api-tests.http` (manual endpoint/DB tests) and noticing the app has no
authentication layer at all, a gap none of the first three rounds raised. Before registering
that finding, every item from `audit-project-2-part3.md` was re-verified against the current
source, since `git log -- ecommerce-api-legacy` shows a refactor commit
(`4ddb14e refactor(ecommerce-api-legacy): resolve round-3 findings and add internal checks`)
landed after `-part3.md` was written, with no audit report ever confirming what it fixed.

14 of the 16 round-3 findings are now resolved:
- CRITICAL "Hardcoded fallback password" — `FALLBACK_PASSWORD` is gone from `userModel.js`;
  `validators.js:25` now rejects checkout when `pwd` is missing (`if (!usr || !eml || !pwd || ...)`).
- HIGH "Checkout has no transaction" — `checkoutService.persistEnrollmentAndPayment` now wraps
  the enrollment + payment writes in `withTransaction` (BEGIN/COMMIT/ROLLBACK).
- HIGH "Business logic in controllers" — `services/checkoutService.js`, `services/reportService.js`
  and `services/userService.js` now hold the domain logic; controllers only parse → call → serialize.
- HIGH "Duplicated ad hoc error handling" — every route is wrapped in `asyncHandler`
  (`middlewares/asyncHandler.js`), errors are thrown as `AppError` (`errors/AppError.js`) and
  handled once in `middlewares/errorHandler.js`; no controller has a try/catch left. The
  previously-unguarded `auditLogModel.create(...)` call now has its own `.catch()`.
- HIGH "Cascade delete swallows errors" — `userModel.deleteCascade` now runs inside
  `withTransaction` using the promisified `run()` wrapper (every statement rejects on error) and
  returns `{ changes }`, which `userService.deleteUser` checks to throw 404 on a no-op delete.
- HIGH "Global mutable, unbounded, write-only cache" — removed entirely; no `cache` reference
  remains anywhere in `src/`.
- MEDIUM "No request validation layer" — `middlewares/validators.js` now validates all three routes.
- MEDIUM "Dead configuration fields" — `dbUser`/`dbPass`/`smtpUser` are gone from `config/index.js`.
- MEDIUM "Pagination present but unbounded" — `validators.js:48` now caps `per_page` with
  `Math.min(..., config.maxPageSize)`.
- MEDIUM "Password verification unreachable/broken" — the dead `verifyPassword` function was
  removed from `utils/crypto.js`; only `hashPassword` remains.
- MEDIUM "App binds port at import time" — `app.js` now only builds and exports the app;
  `server.js` owns `initSchema()` + `listen()`.
- LOW "Pagination default hardcoded outside config" — `DEFAULT_PAGE_SIZE` now lives in
  `config/index.js` as `defaultPageSize`.
- LOW "Unknown routes bypass the JSON error contract" — `middlewares/notFoundHandler.js` now
  returns `{ error: 'not_found' }` before the request would otherwise fall through to Express's
  default HTML handler.
- LOW "Stale boilerplate metadata" — `package.json` name/description now describe this project
  (not the "Frankenstein LMS" boilerplate), and `npm test` / `npm run arch-check` are wired up.

2 of the 16 remain open, unchanged, both deliberately (see their Status lines below).

The 3 findings below (1 new, 2 carried forward) undershoot the template's 5-finding minimum bar
for a first-time Phase 2 pass. Per the template's own rule ("never invent a finding to fill a
slot"), no filler was added — a re-audit of a project that already resolved 14 of 16 prior
findings legitimately has little left to report beyond the one new gap this round exists to
document.

## Summary
CRITICAL: 1 | HIGH: 0 | MEDIUM: 0 | LOW: 2

## Findings

### [CRITICAL] No authentication or authorization on any endpoint
File: src/routes/index.js:10-12 (root cause: absence — no auth middleware exists anywhere in
src/middlewares/ or elsewhere in the project)
Description: All three routes are registered with only body/param validators in the middleware
chain (`validateCheckout`, `validateReportQuery`, `validateUserId`) — none carries any check of
who is calling. `GET /api/admin/financial-report` exposes the full revenue and per-student
payment breakdown to anyone, unauthenticated, despite the `/admin` path segment implying
privileged access. `DELETE /api/users/:id` permanently removes any user and cascades to their
enrollments and payments for anyone who can guess or enumerate a small integer id — no session,
API key, or token of any kind is checked. A project-wide search (`grep -rni "auth\|token\|role\|
permission\|credential" src/`) returns zero matches.
Impact: any unauthenticated caller can read the company's full financial/revenue data broken
down by student, and can destroy any customer's account and purchase history irreversibly (the
delete is cascading and has no confirmation, soft-delete, or audit trail linking the action back
to a caller identity — `auditLogModel` only records "Checkout curso X por Y", nothing for
deletes). This is a direct, unauthenticated data-exposure and destructive-action vulnerability,
not a hardening gap.
Recommendation: add an authentication middleware (API key or session/JWT verification) applied
at minimum to `/api/admin/financial-report` and `DELETE /api/users/:id`; the naming
(`/api/admin/...`) already documents the intent, only the enforcement is missing. No existing
AP-xx/RP-xx pair actually matches this — AP-02 (hardcoded secrets) and AP-06 (duplicated business
logic) are both adjacent but neither is "an endpoint has no caller-identity check", so this
report does not cite either. See the follow-up note below for the proposed new catalog/playbook
entries.
Status: New — never raised in `audit-project-2.md`, `-part2.md`, or `-part3.md`. See the
follow-up note below for why.

### [LOW] Inconsistent language/naming conventions
File: src/controllers/checkoutController.js (calls into validators.js:23, still `usr`/`eml`/
`pwd`/`c_id`/`card`); user-facing strings still Portuguese ('Curso não encontrado', 'Pagamento
recusado', ...) mixed with English identifiers throughout
Description: Unchanged from `-part3.md` — same abbreviated request field names, same
Portuguese/English mix in strings.
Impact: unchanged — slows onboarding/review; no new impact.
Recommendation: AP-15/RP-15 — unchanged. Per RP-15's scope limit, request field names and
user-facing strings are the API contract and are correctly left alone by Phase 3.
Status: Still open (fourth consecutive round) — deliberately not fixed, as designed.

### [LOW] Inconsistent response-format conventions
File: src/controllers/userController.js:5 (`res.send(plain text)`) vs. src/controllers/
checkoutController.js:5 (`res.status(200).json(result)`) and reportController.js (JSON); src/
middlewares/errorHandler.js:17 (`res.status(err.status).send(err.message)` for AppError, but
`res.status(500).json({ error: 'internal_error' })` at :27 for unexpected errors) and
notFoundHandler.js:9 (`res.status(404).json(...)`) for unmatched routes
Description: The mix persists in the current code: the delete-user success response and every
`AppError`-driven error response are plain text, while checkout/report successes and the two
"infrastructure" error paths (500, 404) are JSON. `errorHandler.js`'s own comment states this was
kept intentionally ("o formato das respostas de erro é contrato e não mudou").
Impact: unchanged — API consumers still cannot rely on one content type across the three routes'
success and error paths.
Recommendation: AP-15/RP-15 — unchanged; standardize on JSON going forward without silently
renaming the existing `enrollment_id` field.
Status: Still open (fourth consecutive round) — deliberately preserved per RP-15's contract-
preservation scope; the underlying inconsistency itself is unchanged, not newly discovered.

================================
Total: 3 findings (1 new, 2 carried forward unchanged and deliberately unfixed)
================================

Follow-up (not part of the Phase 2 output format, kept here since it motivated this report):
neither `references/anti-patterns-catalog.md` nor `references/refactoring-playbook.md` has an
entry for "missing authentication/authorization" in any of the three project copies of the skill
— confirmed by `grep -rni "auth"` returning zero matches in both files. That is the mechanism gap
that let this CRITICAL finding go undetected for three rounds: every other finding in this report
traces to a cataloged AP-xx with a matching RP-xx fix; this one has neither. Next AP id available
across all three copies: AP-17. Should be added (catalog entry + matching playbook pattern)
before the next Phase 2 run on any of the three projects, since code-smells-project and
task-manager-api have never been audited specifically for this either.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```