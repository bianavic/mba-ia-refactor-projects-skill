================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 26.13.0) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 7 | HIGH: 3 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Hardcoded credentials, live payment key and seeded account password
File: src/utils.js:2-5, src/AppManager.js:18
Description: The config object holds literal production-looking secrets — database user/password (`senha_super_secreta_prod_123`), a live payment gateway key (`pk_live_…`) and the SMTP user — and the boot seed inserts a user with the literal password `123`.
Impact: Anyone with read access to the repository (or any copy of it) holds the database password and the payment gateway key; the seeded account's password is public. Removing them from the code does not un-leak them.
Recommendation: Read every secret and the seed password from the environment through one config module, ship a `.env.example` without real values, and rotate the leaked key/password — see RP-02 (AP-02).

### [CRITICAL] Fake password hashing (truncated repeated base64)
File: src/utils.js:17-23, src/AppManager.js:18, src/AppManager.js:68-69
Description: `badCrypto` repeats the first 2 base64 characters of the password and keeps 10 characters, so the stored "hash" is a reversible function of the first 1–2 password bytes; the seeded user is stored in plaintext (`'123'`).
Impact: Every stored password is equivalent to plaintext — any two passwords starting with the same two characters collide and the original prefix is recovered by base64-decoding; a database leak exposes reusable credentials of every customer (LGPD art. 46 security duty).
Recommendation: Replace with salted `crypto.scrypt` (random 16-byte salt, constant-time verify) and hash the seed password on insert; existing in-memory rows are re-seeded at boot, so no migration is needed — see RP-09 (AP-03).

### [CRITICAL] Full card number and payment gateway key written to the log
File: src/AppManager.js:45
Description: Each checkout logs `Processando cartão ${cc} na chave ${config.paymentGatewayKey}` — the full PAN sent by the client and the live gateway key, in clear text on stdout.
Impact: Everyone with access to the process output, log shipper or log storage reads every customer's full card number and the gateway key, retained for as long as the logs are kept — a PCI-DSS violation (req. 3.3/3.4) outside the database's access control.
Recommendation: Log only the checkout outcome with a masked card (last 4 digits) and never the key; logs already written cannot be fixed in code and must be purged by the operator — see RP-17 (AP-18).

### [CRITICAL] No authentication on the admin report, user deletion and checkout for existing accounts
File: src/AppManager.js:80, src/AppManager.js:131, src/AppManager.js:40, src/AppManager.js:74
Description: `GET /api/admin/financial-report` and `DELETE /api/users/:id` have no auth construct (a project-wide search finds no auth, token, session or role code); checkout for an existing email enrolls that account on the email alone, ignoring the `pwd` sent with it.
Impact: Any anonymous caller reads the full revenue report, deletes any user by id, and enrolls/charges any existing customer by knowing their email.
Recommendation: Apply the access level confirmed per route in the Phase 2 access table — see RP-16 (AP-05).

### [CRITICAL] Financial report exposes students' names to anonymous callers
File: src/AppManager.js:104, src/AppManager.js:112-115
Description: The report returns the name of every enrolled student with the amount they paid, and its query also fetches each student's email although the response never uses it.
Impact: Any anonymous caller harvests the list of customers and what each one paid — personal and financial behaviour data of third parties, beyond what a revenue report needs (LGPD art. 6 III, minimization).
Recommendation: Build the report rows from an explicit field list chosen in Phase 2 and stop selecting the email — see RP-09 (AP-04); combined with the RP-16 guard.

### [CRITICAL] God Class: AppManager mixes schema, seed, routing, business rules and raw SQL
File: src/AppManager.js:1-141
Description: One class opens the database connection, creates the schema, seeds data, registers every route, applies the payment and enrollment rules and runs 20 raw SQL calls inside nested route callbacks.
Impact: No rule can be tested without an HTTP request and a live database; any change to one flow (checkout, report, deletion) risks the others.
Recommendation: Split into config, database, models, services, controllers and routes — see RP-03, RP-14, RP-11 (AP-06).

### [CRITICAL] express@4.22.1 ships a body-parser with an unauthenticated process-crash advisory
File: package.json:10, package-lock.json:228, package-lock.json:641, src/app.js:6
Description: The locked express@4.22.1 resolves body-parser@1.20.4 (GHSA-27r3-jxmh-p828, high, fixed in 1.20.9), path-to-regexp@0.1.12 (GHSA-37ch-88jc-xwx2, fixed 0.1.13), proxy-addr@2.0.7 (GHSA-jqcg-44mw-7w3h, fixed 2.0.8) and qs@6.14.2 (GHSA-x5fp-wj9c-mxmx, GHSA-4mjr-xmp4-gh2g, fixed 6.16.0); `express.json()` with default options is exactly the vulnerable body-parser path.
Impact: One anonymous request with a compressed body plus trailing bytes terminates the process, taking the API down for every user (the path-to-regexp, proxy-addr and qs advisories are not reachable with this code's routes and settings).
Recommendation: Upgrade to express@4.22.3 (same major; it requires body-parser ~1.20.5, path-to-regexp ~0.1.13, qs ~6.16.0) and refresh the lockfile so every transitive fix is installed — see RP-12 (AP-12).

### [HIGH] Global mutable cache and revenue counter shared by all requests
File: src/utils.js:9-15, src/utils.js:25, src/AppManager.js:59
Description: A module-level `globalCache` object receives one `last_checkout_<userId>` entry per checkout, is never read and never evicted; `totalRevenue` is a module-level counter exported by value.
Impact: Memory grows with every checkout for the process lifetime, and the cache keeps a per-user purchase record that survives the user's deletion.
Recommendation: Remove the unread cache and the dead counter (no reader exists) — see RP-05 (AP-08).

### [HIGH] Checkout and report orchestrate many tables inside the route, with no controller or service layer
File: src/AppManager.js:28-78, src/AppManager.js:80-129
Description: The checkout handler reads courses and users, creates users, enrollments, payments and audit logs and calls the payment decision, all in one route callback; the report handler joins four tables by hand; no controller or model file exists (arch-check: controllers:0, models:0), and the three inserts of a checkout run without a transaction.
Impact: The checkout use case cannot be tested or reused without HTTP, and a failure between inserts leaves an enrollment without a payment.
Recommendation: Extract a CheckoutService and a ReportService over per-table models, called from controllers, with the checkout writes in one transaction — see RP-21 (AP-22).

### [HIGH] Missing input validation lets one request crash the process
File: src/AppManager.js:29-35, src/AppManager.js:46, src/AppManager.js:68, src/AppManager.js:93, src/AppManager.js:132-136
Description: Checkout checks only truthiness, so `"card": 4111222233334444` (a number) reaches `cc.startsWith` inside a sqlite callback and throws outside Express's error handling; `pwd` is optional and defaults to `"123456"`; `c_id`/email are not type-checked; the report reads `enrollments.length` without checking `err`; `DELETE /api/users/:id` ignores the error and answers success for any id, existing or not.
Impact: A single anonymous request kills the server for every user; accounts are created with a well-known password; a delete of a non-existent id reports success.
Recommendation: Validate types at the boundary and route errors through one error handler (400/404 instead of a crash) — see RP-20 with RP-11 (AP-21).

### [MEDIUM] N+1 queries in the financial report
File: src/AppManager.js:83, src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106
Description: The report runs one query for courses, then one per course for enrollments, then two per enrollment (user, payment).
Impact: Query count is 1 + C + 2E, so the report slows linearly with every sale.
Recommendation: One JOIN over courses, enrollments, users and payments, grouped in the service — see RP-06 (AP-09).

### [MEDIUM] Financial report has no pagination
File: src/AppManager.js:80-83
Description: The report loads every course and every enrollment in one response with no limit/offset.
Impact: Response time and payload grow with the whole sales history.
Recommendation: Add bounded `limit`/`offset` over courses, keeping today's full answer as the default if chosen in Phase 2 — see RP-07 (AP-10).

### [MEDIUM] User deletion leaves enrollments, payments, audit logs and cache entries behind; no export or retention
File: src/AppManager.js:131-137, src/AppManager.js:57, src/utils.js:14
Description: `DELETE /api/users/:id` removes only the `users` row, not in a transaction; enrollments and payments keep the `user_id`, audit logs keep it inside free text (`Checkout curso <cid> por <userId>`) and the cache keeps `last_checkout_<userId>` — the response even admits it; there is no export path and no retention limit.
Impact: The subject stays identifiable after being told they were removed (LGPD art. 18 VI / GDPR art. 17); no data portability (LGPD art. 18 V / GDPR art. 20) and personal data kept indefinitely (LGPD art. 16 / GDPR art. 5(1)(e)).
Recommendation: Delete or de-link every row holding the id in one transaction as chosen in Phase 2, 404 on unknown id — see RP-18 (AP-19).

### [MEDIUM] Config, cache and crypto helpers loose in a catch-all utils module at the source root
File: src/utils.js:1-25
Description: `src/utils.js` sits beside the entry point and mixes application settings, a global cache and the password-hashing helper with no role directory (arch-check did not list it; confirmed by reading the file).
Impact: The layout does not say where configuration or security code lives; every new helper lands in the same grab-bag.
Recommendation: Move settings to `config/`, hashing to a security helper, and drop the cache — see RP-22 (AP-23).

### [MEDIUM] sqlite3@5.1.7 pulls vulnerable install-time dependencies; fix only in 6.x, repository unmaintained
File: package.json:11, package-lock.json:2021
Description: npm audit reports sqlite3 5.0.0–5.1.7 as high through node-gyp/tar/cacache/make-fetch-happen (e.g. tar GHSA-34x7-hfp2-rc4v); the only fixed release is 6.0.1 (major), and v6.0.0's notes mark the repository unmaintained.
Impact: The advisories hit `npm install` (tarball extraction/build on developer and CI machines), not the running API; staying on 5.x keeps them, and the package line no longer gets fixes.
Recommendation: Phase 2 decision — upgrade across the major to 6.0.1 or leave open — see RP-12 (AP-12).

### [LOW] console.log used as the application logger
File: src/app.js:13, src/utils.js:13, src/AppManager.js:45
Description: Startup, cache writes and payments are logged with `console.log`, without levels.
Impact: Errors cannot be separated from noise or filtered by level.
Recommendation: One logger module with levels — see RP-08 (AP-13).

### [LOW] Magic values for port, payment status, card rule, active flag and default password
File: src/utils.js:6, src/AppManager.js:13, src/AppManager.js:19, src/AppManager.js:21, src/AppManager.js:37, src/AppManager.js:46, src/AppManager.js:48, src/AppManager.js:68, src/AppManager.js:108
Description: Port `3000`, statuses `'PAID'`/`'DENIED'`, the "approved if it starts with 4" card rule, `active = 1` and the default password `"123456"` are inline literals repeated across SQL and code.
Impact: Changing a status or the payment rule needs edits in several places that drift apart.
Recommendation: Named constants and env-driven port in the config module — see RP-13 (AP-14).

### [LOW] Unused import and dead export
File: src/AppManager.js:2, src/utils.js:25
Description: `totalRevenue` is imported into AppManager and never referenced; `utils.js` exports it with no reader.
Impact: Readers assume revenue is tracked in memory when it is not.
Recommendation: Remove the import and the export — see RP-13 (AP-15).

### [LOW] Cryptic and inconsistent names
File: src/AppManager.js:4, src/AppManager.js:29-33, src/utils.js:12, src/utils.js:17
Description: Handler variables are single letters or abbreviations (`u`, `e`, `p`, `cid`, `cc`), the class name `AppManager` names no role, and helpers are named after their flaw (`badCrypto`, `logAndCache`).
Impact: Names cannot be predicted from roles, slowing review of payment and identity code.
Recommendation: Role-based names (`checkoutController`, `hashPassword`, `courseModel`), keeping the request fields `usr/eml/pwd/c_id/card` as the API contract — see RP-15 (AP-16).

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
