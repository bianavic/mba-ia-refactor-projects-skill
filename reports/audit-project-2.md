```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript / Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 2 | MEDIUM: 2 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Secrets & Credentials
File: src/utils.js:2-6
Description: `dbPass` ("senha_super_secreta_prod_123") and `paymentGatewayKey` ("pk_live_1234567890abcdef" — a live payment gateway key) are literal strings committed directly in source.
Impact: Production database credentials and a live payment-processor key are exposed to anyone with repo access, and shipped inside version control history permanently.
Recommendation: Move all secrets to environment variables loaded via `.env`/process env, never committed. See AP-02.

### [CRITICAL] Fake/Reversible Password Hashing
File: src/utils.js:17-23 (defined), used at src/AppManager.js:68
Description: `badCrypto()` "hashes" a password by repeating base64 encoding of the input and truncating to 10 characters — base64 is a reversible encoding, not a one-way hash, and truncation makes it collide constantly.
Impact: Every stored user password is trivially recoverable; equivalent to storing plaintext passwords. A single leaked `pass` column compromises all accounts (and likely reused passwords elsewhere).
Recommendation: Replace with a vetted password-hashing function (bcrypt/argon2) with per-user salt. See AP-03, RP-03.

### [CRITICAL] Payment Card Number Logged in Plaintext
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` writes the full raw credit card number and the live payment gateway secret key to stdout on every checkout.
Impact: Card numbers and the payment gateway key land in log files/aggregators (often shipped to third-party log services), a direct PCI-DSS violation and a serious data-exposure risk independent of any breach.
Recommendation: Never log PAN/secrets; mask card numbers and route logging through a structured logger with redaction. See AP-02, AP-12.

### [CRITICAL] God Class — DB, Routing, and Business Logic Merged
File: src/AppManager.js:1-142
Description: A single `AppManager` class owns the DB connection/schema (`initDb`), every HTTP route (`setupRoutes`), and all checkout/reporting business logic, with no Model/Controller/Service separation.
Impact: Impossible to unit test checkout logic without spinning up Express and SQLite together; any change to one domain (e.g. reporting) risks breaking unrelated domains (e.g. checkout) living in the same file/class.
Recommendation: Split into Models (data access), Controllers (HTTP I/O), and Services (business rules). See AP-05, RP-01.

## HIGH

### [HIGH] Orphaned Records on User Deletion — No Referential Integrity
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` removes the user row only, with no cascading cleanup of `enrollments`/`payments`; the response literally admits the data is left inconsistent ("mas as matrículas e pagamentos ficaram sujos no banco").
Impact: Financial and enrollment reports silently reference deleted users, corrupting `financial-report` output and any future audit; the bug is undocumented outside a hardcoded response string.
Recommendation: Move deletion into a Model/Service method that handles cascading rules explicitly (soft-delete or cascading delete). See AP-05, AP-06.

### [HIGH] Global Mutable State Used as a Cache
File: src/utils.js:9, 12-15; written from src/AppManager.js:59
Description: `globalCache` is a module-level plain object written to from the checkout request handler (`logAndCache`) with no synchronization or scoping per request.
Impact: Concurrent checkout requests race on the same object; state leaks across unrelated requests/users and grows unbounded with no eviction.
Recommendation: Replace with a proper per-request or externally managed cache (Redis, or remove if unnecessary). See AP-07.

## MEDIUM

### [MEDIUM] N+1 Query Pattern in Financial Report
File: src/AppManager.js:80-129
Description: `/api/admin/financial-report` queries all courses, then for each course queries its enrollments, then for each enrollment issues two more separate queries (user, payment) — fully nested per-row round-trips instead of joins.
Impact: Query count grows multiplicatively with courses × enrollments; with real data volumes this endpoint becomes a many-hundred-query request and a primary latency/DB-load source.
Recommendation: Replace nested callbacks with SQL joins or batched `WHERE id IN (...)` queries. See AP-08, RP-05.

### [MEDIUM] Missing Pagination on List/Report Endpoints
File: src/AppManager.js:83 (`SELECT * FROM courses`, feeding the full report)
Description: The financial report endpoint loads and returns the entire `courses` table (and transitively all enrollments/payments) with no `limit`/`offset` or page parameters.
Impact: Response size and latency grow linearly with catalog size; there is no way for a client to request a bounded page of results.
Recommendation: Add `limit`/`offset` (or cursor) query parameters and enforce a default page size. See AP-09.

## LOW

### [LOW] Console-Based Logging Instead of Structured Logger
File: src/app.js:13; src/AppManager.js:45; src/utils.js:13
Description: Operational logging uses raw `console.log` calls scattered across files instead of a structured logger with levels.
Impact: No log levels, no structured fields/rotation, and no way to filter by severity in production — unusable for real operations and (combined with the finding above) actively dangerous.
Recommendation: Adopt a structured logger (e.g. `pino`/`winston`) with configurable levels. See AP-12.

### [LOW] Unused Import: `totalRevenue`
File: src/AppManager.js:2; declared/exported at src/utils.js:10, 25
Description: `totalRevenue` is imported into `AppManager.js` but never referenced anywhere in the file; it is also never incremented anywhere in `utils.js`.
Impact: Dead code that misleads readers into thinking revenue is tracked/aggregated somewhere centrally, when it is not.
Recommendation: Remove the unused import and the dead variable, or wire it up if the aggregate was intended. See AP-14.

### [LOW] Hardcoded Magic Default Password
File: src/AppManager.js:68
Description: `badCrypto(p || "123456")` silently substitutes a fixed literal password whenever the client omits one, instead of validating that a password is required.
Impact: Any checkout that creates a new user without a `pwd` field gets an account with the same guessable default password ("123456") for every such user.
Recommendation: Require the field explicitly and reject the request if missing, rather than defaulting to a magic value. See AP-13.

### [LOW] Inconsistent Language/Naming Conventions
File: src/AppManager.js:35,38,41,48,51,55,70,84,135 (Portuguese user-facing strings) mixed with English identifiers throughout (`checkout`, `AppManager`, `financial-report`); request fields abbreviated inconsistently (`usr`, `eml`, `pwd`, `c_id`, `card`)
Description: User-facing error strings are in Portuguese while all code identifiers, route paths, and field names are in English, with no single naming convention applied to request body keys.
Impact: Slows onboarding and code review; ambiguous field names (`u`, `e`, `p`, `cid`, `cc`) inside handlers make the checkout logic harder to follow than necessary.
Recommendation: Pick one language for user-facing strings and consistent, descriptive names for request fields. See AP-15.

================================
Total: 12 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```
