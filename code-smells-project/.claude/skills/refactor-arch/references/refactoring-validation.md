# Refactoring Validation (Phase 3)

`api-test.sh` proves behavior (the external contract); `arch-check.sh` proves structure (AP-06,
AP-22, AP-23), which endpoint tests cannot see — a route that queries the database and one that
delegates to a Controller answer identically. Every check needs its own evidence; a check that
could not run is a gap, never a pass.

## Contents
- 1. Validation order
- 2. api-test.sh: contract, helpers, the nine test sections (T0–T8), database access, auth, re-runs, derivation
- 3. arch-check.sh: exit codes, layout rules, configuration, new patterns
- 4. Per-finding checks
- 5. Anti-tautology
- 6. Validation log and sanitization
- 7. Future improvements and origin words
- 8. Completion box evidence
- 9. Troubleshooting

## 1. Validation order

1. The application boots without errors.
2. Generate or update `api-test.sh` (section 2) and run it from the project's directory. Record the
   exact `TOTAL`/failure/skip counts and the coverage line. Exit 1 or 2 blocks completion.
3. **Close every approved plan line completely.** Walk the report finding by finding and, inside
   each, location by location: the fix is applied at every `file:line` it cites (or where that code
   moved), and every item the plan line names is done everywhere in the new code — "statuses →
   config" also covers a status literal inside an SQL string. A missing part of an approved fix is
   **unfinished work, not a Future improvement**; only lines marked `left open` may stay open. The
   option approved in Phase 2 already authorizes every answer change it implies (a 400, 404, 401).
   For AP-12 lines, the installed version (lockfile or freeze) is at or above the first fixed
   version recorded in Phase 2 and no call listed as deprecated remains.
4. **Re-scan the code Phase 3 wrote** against the catalog — a fix can create a finding. A new
   finding that breaks nothing goes to *Future improvements* and is counted in the `Findings:`
   evidence line — unless it has the `AP-xx` of an approved plan line: then that line is
   unfinished work.
5. Run `arch-check.sh` (section 3). Exit 1 or 2 blocks completion; never infer the result from the
   diff.
6. Run the per-finding checks (section 4) and the anti-tautology runs (section 5).
7. Save the validation log (section 6) and write *Future improvements* (section 7).

## 2. api-test.sh

### Script contract

- Lives at `<project>/api-test.sh`, executable, comments in the project's own language; never
  translate domain vocabulary (tables, fields, routes).
- `set -uo pipefail`, never `-e` — one failing check must not hide the others.
- `BASE="${BASE_URL:-http://<host>:<port>}"`, host and port detected from the code.
- A banner (project, base URL, timestamp) and a footer with `TOTAL`, failures and skipped.
- **Exit codes:** `0` all passed, `1` a check failed, `2` nothing was tested — the application was
  unreachable at preflight or the database failed the isolation gate. Exit 2 is never a pass.
- A **coverage line** in the footer: `<N> endpoints inventoried / <N> exercised`. When the numbers
  differ, fix the inventory or the script before using the run as evidence. List the endpoints in a
  comment at the top — one line per endpoint and the section that exercises it.
- Every original method + path stays in the inventory, also when an approved fix changed its status
  (200 → 401/403, 500 → 400): asserting the corrected answer exercises it. A skipped endpoint is not
  exercised.
- Assert the absence of a sensitive field without printing its value; redact output (section 6).

### Helpers

Dependency-light: `curl` plus the JSON parser the Phase 1 tooling check confirmed (`python3 -c` or
`node -e`), not `jq`.

| Helper | Role |
|---|---|
| `json <key>...` | read a field from a JSON body on stdin |
| `check <status> <desc> <curl args...>` | assert the status; capture status and body in one `curl -sS -w $'\n%{http_code}'`; print the start of the body |
| `check_equal <expected> <actual> <desc>` | assert a value |
| `deny <pattern> <desc> <curl args...>` | assert something is *absent* from a body (a secret, a hash) |
| `check_db <expected> <desc> <sql>` | assert a value straight in the database |
| `skip <desc> <reason>` | count and print a check that could not run — a gap, never a pass |

On failure, print the endpoint, the expected value and the actual value.

### The nine test sections (T0–T8)

Run them in this order; anything destructive goes last. They are labeled `T0`–`T8` so they are
never confused with the numbered sections of this file.

**T0. Preflight.** Check the application answers (`/health` or the closest equivalent); `exit 2`
with a boot hint if not. Run the isolation gate before any request that writes. Then log in and
capture tokens and ids at runtime — never a literal token.

**T1. Happy path.** One call per inventoried endpoint, 2xx expected, asserting body *values*, not
only status or shape. A 200 carrying a wrong value must fail.

**T2. Sad paths.** Per endpoint, the failures its code handles: missing field, wrong type, malformed
JSON → 400; unknown id → 404; duplicate unique value → 409; bad credentials → 401; value outside an
allowed set → 400. Assert status and error body. **500 is never an expected status** — a 500 on bad
input is a finding, not a test to enshrine.

**T3. Permission boundaries.** A matrix of endpoint × caller (anonymous, owner, another user, admin),
asserting both allow and deny. Where a resource's existence is itself sensitive (sequential ids),
"someone else's" answers the same as "does not exist". With no enforcement, write the matrix anyway
with the current statuses — each wrongly open cell is a documented finding. Derive each cell's owner
with RP-16's owner rule and record the resolver in the inventory.

**T4. Edge cases.** min−1 / min / max / max+1, zero and negative quantities, `page=0`, non-numeric
and oversized page sizes, unicode, overlong strings, bad dates, empty string vs. absent field.
Repeat mutations: second PUT, duplicate POST, delete twice (then 404).

**T5. Empty states.** An empty collection answers `200` with `[]`; a report over no data answers
zeros, not `null` or 500; a filter matching nothing answers an empty result. Reach it without
destroying data (filter by an impossible value, or use a resource the script just created).

**T6. Persistence and integrity.**
- Every write is followed by a separate read confirming the value, and by a check of any documented
  side effect (stock restored on cancel, cascade on delete).
- At the database, where reachable: row counts before/after; a unique constraint rejected by the
  database itself; no orphaned rows after a delete (`... WHERE fk NOT IN (SELECT id FROM parent)`);
  no plaintext secret in a column (compare length, not a hash prefix).
- Atomicity: a request that fails halfway leaves no partial row or side effect.

**T7. Privacy.** Required when the project stores personal data.
- `deny` password/hash/token fields in every response that serializes a user.
- Where the application log is reachable, assert a known email or card number does not appear in
  it after the flow that would write it; otherwise `skip` with the reason.
- Card numbers appear only masked.

**T8. Destructive operations.** Test the 401/403 boundary freely; exercise the destructive path
itself only at the very end. Prove erasure here: create a disposable user with dependent rows,
delete it, then assert nothing points at its id — over HTTP and with `check_db` — including
audit/event tables (no rows for that id, or rows kept with the id nulled, as RP-18 chose).

### Database access

| Situation | Strategy |
|---|---|
| File database the shell can open (SQLite file, a local server with a CLI client) | `check_db` directly; read the path/URL from the env var the app uses |
| In-memory database, or one the shell cannot reach | `skip` with the reason plus the closest HTTP substitute (a list or report endpoint) — or make the path configurable so a throwaway file can be used |

**Isolation gate (mandatory).** The suite writes and deletes data, so it runs only against a
disposable database. In T0, before the first write, classify the target from the same env
var or config the application reads:

| Target | Passes the gate when |
|---|---|
| `temp-file` | a file database under a `mktemp -d` directory or the system temp directory |
| `in-memory` | SQLite `:memory:` or an equivalent that disappears with the process |
| `test-db` | a database created for this run, or whose name ends in `test` |
| `container` | a database in a container started for this run |

Anything else — the project's default database file, a shared development or production URL, a
target the script cannot classify, or one it cannot prove the application also uses — prints
`DB target: not isolated — <reason>` and exits 2 before any write. On a pass, print only the class
(`DB target: temp-file`), never the path, URL or credentials. To pass, boot the application against
a throwaway database; never weaken or bypass the gate. A missing host command is a `skip`, not a
database failure.

### Auth

Authenticate after preflight, on every run — tokens signed with a per-process key die on restart.
If the project issues a token nothing verifies, capture it anyway and show the answer is the same
with and without it. With no authentication, the T3 matrix documents that every caller gets
the same answer.

### Re-runnability

- Discover ids from list/creation responses; hardcode seed ids only when the database is rebuilt
  on every boot.
- Unique fields get a run-unique value (`$(date +%s)`, `$$`).
- Tests that consume a finite resource (stock, a quota) create their own. If the suite can only run
  once per reset, say so in its header comment.

### Derivation

1. Inventory routes by reading the code — method, path, auth rule, ownership rule. Never from the
   README or memory.
2. Detect boot command, port and seed step; put them in the header comment and in `BASE`.
3. Detect the auth flow and the database access strategy.
4. Run the delegation and smoke check (section 4, Per-finding checks) and a read-only health request.
5. Write the test sections T0–T8 with the shared helpers.
6. Run it. A failure caused by the script (wrong field name, wrong id) is fixed in the script; one
   caused by the application is fixed in the application.

## 3. arch-check.sh

`bash ${CLAUDE_SKILL_DIR}/scripts/arch-check.sh <project-dir>` — read-only; call it with `bash`.
Read its exit code from the command alone (`bash … >out; echo $?`), not after a pipe. Record the
detected extensions, route-file count, model/controller counts, active overrides and every `note:`
line in the validation evidence.

| Exit | Meaning | Action |
|---|---|---|
| 0 | No violation in AP-06, AP-22 or AP-23 | Record the counts; a pass needs a route-file count and a controller-file count above 0 |
| 1 | Violations, listed as `rule file:line` | AP-06: move the call into a Controller/Service (RP-14). AP-22: extract a Service (RP-21). AP-23: group the file by role (RP-22). Re-run |
| 2 | No route file or no source found | **Not a pass** — configure the checker, re-run |

### Layout rules

| Rule | Signal (line-based heuristic, confirm by opening the file) | Fix |
|---|---|---|
| AP-22 a | A model file imports another model file (model = in a model dir or named like one **and** holding a persistence call) | RP-21 |
| AP-22 b | A model file imports HTTP/routing code | RP-21, RP-11 |
| AP-22 c | One top-level controller function calls **≥ 2** model modules (`<model>.<fn>(`) — py, js, mjs, ts, rb, php | RP-21 |
| AP-22 d | Routes exist but no controller file defines a function, or no model file holds persistence calls | RP-14, RP-21 |
| AP-22 e | A route file imports no controller | RP-14 |
| AP-22 f | A route file imports a model or service module directly | RP-14 |
| AP-22 g | A controller file no route file imports (unwired) | RP-10, RP-14 |
| AP-23 | A source file at the project root that is not an entry point, a standalone script (a seed), a `*.config.*`/`*.conf.*`/`*.setup.*` file or a test — py, js, mjs, ts, rb, php | RP-22 |

Limits, printed as `note:` lines and never counted as a pass: languages without function
segmentation (Java, Kotlin, Go, C#) leave AP-22 c and AP-23 unverified — read the code for them.
Aliased imports and methods inside classes are not seen: when the layer is class-based, read each
controller method.

### Configuration

Export the variables or put them in `.arch-check.conf` at the project root:

| Variable | Use when |
|---|---|
| `ROUTE_DIRS` | Routes live in a directory the defaults miss (`transport`, `presentation`) |
| `ROUTE_FILE_GLOBS` | Route files have unusual names (`*_api.rb`, `*Resource.java`) |
| `EXTRA_PATTERN` | The stack has a persistence idiom the checker does not know |
| `EXCLUDE_PATTERN` | A documented, reviewed exception must be ignored |
| `MODEL_DIRS`, `CONTROLLER_DIRS` | Models/controllers live in a directory the defaults miss (`domain`, `usecases`) |
| `LAYOUT_ROOT_ALLOW` | A root file the framework requires (`settings.py`; `next.config.js` is already allowed) |
| `LAYOUT_EXCLUDE` | A documented, reviewed AP-22/AP-23 exception (regex on the printed line) |

By default a route file sits under `routes`, `views`, `urls`, `handlers`, `endpoints`, `resources`,
`web`, `http`, `delivery` or `api`; has `route`, `router`, `urls`, `handler`, `endpoint` or
`resource` in its name; or declares a route in its content (a monolith with routes in
`app.py`/`app.js` needs no configuration). Middlewares are excluded.

### A persistence idiom the checker misses

1. Read how the model layer calls its persistence library.
2. Match the call shape: method on a handle (`db.x(...)`), static/class method (`Model.x(...)`) or
   free function (`FindX(...)`).
3. Inject one such call into a route file of a throwaway copy and confirm the pattern fires — a
   pattern that never fired is untested.
4. Pass it via `EXTRA_PATTERN` and record it so the check is reproducible.

## 4. Per-finding checks

Before counting a finding as resolved, run a check that could have failed (a code search or an
HTTP/DB call):
- One check per cited location or atomic signal (each literal, each call) — never one composite
  pattern: a search for `"<a>", "<b>", "<c>"` misses a lone `'<a>'` inside an SQL string.
- One check per defect the finding's Description and Impact name: each symptom (an invalid value
  that reached the database, an unchecked reference) gets an HTTP/DB check that failed before the fix.
- Before trusting zero hits, confirm the pattern matches the offending line as the report quotes
  it: `printf '%s\n' "<quoted line>" | grep -E '<pattern>'`.
- AP-22: no AP-22 line **and** each Service is imported by a controller; a Service nothing imports
  is AP-11.
- AP-23: no AP-23 line **and** the entry point boots.
- Authorization findings: the four-caller check of RP-16's owner rule.
- **Delegation and smoke check:** for every new wrapper, controller or Service, the symbol it calls
  resolves to the lower layer (not to itself) and its caller imports it; then a minimal boot/import
  of the application, so recursion, circular imports and registration errors are not mistaken for
  database or authorization failures.
- Lines marked `left open` are not checked; they go to *Future improvements*.

## 5. Anti-tautology

A check that passed on its first run has not yet shown it can fail. In a **throwaway copy** of the
refactored project (`cp -R` into `mktemp -d`) — never the working tree — inject each defect, run
the check against the copy (boot it on another port for `api-test.sh`) and expect exit 1 naming it:

| Injected defect | Expected |
|---|---|
| A persistence call in one route file | `arch-check.sh` names AP-06 |
| A model importing a sibling model, or a controller function calling a second model | `arch-check.sh` names AP-22 |
| A supporting file (`helpers.<ext>`) at the project root | `arch-check.sh` names AP-23 |
| The controller directory emptied | `arch-check.sh` names AP-22 |
| One fix reverted (a secret back in a response, a guard removed) | `api-test.sh` fails the matching check |

Report each injected defect and the check that caught it. Report skipped checks next to passes and
failures — "50 checks, 0 failures" and "50 checks, 0 failures, 2 skipped" are different claims. A
check no real defect could make fail is not a check: make it specific or remove it.

## 6. Validation log and sanitization

One file per project, `<repo root>/evidence/logs/<project dir>-validation.txt`, overwritten on each
run: the `Domain:` line copied verbatim from the Phase 1 box, the `AP-12:` lines recorded in Phase 2
(one per component, with the version now installed and the state after the fix), the boot output,
and the full `api-test.sh` output with its exit code. Everything else (`arch-check.sh`,
anti-tautology, per-finding checks) goes in the validation evidence under the completion box.

**Sanitization** — the single rule for every persisted output (this log, `api-test.sh` previews,
environment diagnostics): redact passwords, API keys, bearer tokens, cookies, authorization
headers, payment-card numbers and email addresses as `<REDACTED>`; record only status codes,
counts, paths and non-sensitive assertions. Never redirect a shell with inherited secrets into the
file.

```bash
LOG=<repo root>/evidence/logs/<project dir>-validation.txt
BOOT=$(mktemp)
<boot command> >"$BOOT" 2>&1 &            # e.g. python app.py / npm start
# ... wait until BASE_URL answers ...
{
  echo "# <project dir> — $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Domain: <the Phase 1 Domain value, verbatim>"
  echo; echo "## AP-12"; printf '%s\n' "<one AP-12: line per component>"
  echo; echo "## Boot"; cat "$BOOT"
  echo; echo "## api-test.sh"
  ./api-test.sh 2>&1; echo "api-test.sh exit code: $?"
} >"$LOG"
kill %1
test -s "$LOG"
```

The log is valid only with the `Domain:` line, one `AP-12:` line per component (none `BLOCKED`),
a boot section showing the application listening, a passing `DB target:` line, and a footer with
`TOTAL`, the coverage line and exit code 0. A log of a failing run is not evidence: fix, re-run,
overwrite.

## 7. Future improvements and origin words

A `## Future improvements` section in `<project dir>/README.md` (replace it if it exists; create the
README if there is none), one line per item:
`- <item> — <origin: left open in the plan | declined by the user | accepted by the user | noticed
during Phase 3 | outside the code> — <reason>`, or `None.` It is the same list as the one printed
under the completion box: every line left open and every problem noticed during Phase 3 that this
round did not fix. It never blocks completion. A piece of an approved fix never belongs here:
before listing an item, match it against each approved finding's `File:`, `Description:` and
`Impact:` — a match is unfinished work. An action no code change can do (rotating a leaked secret)
is `outside the code`.

**Origin words.** `declined by the user` / `accepted by the user` only when the user answered that
exact question. A gap the skill found and never asked about is `noticed during Phase 3`, worded as
*outside the approved plan* — and, when that code predates this round, *kept as in the original* —
never as "you chose". A residual is worded as the approved option states it, never stronger or
weaker.

## 8. Completion box evidence

The box is printed by `completion-box.sh <project-dir>` and pasted verbatim: always the three `✓`
lines, never retyped, omitted or reworded. It prints only when `arch-check.sh` exits 0 and the
validation log is valid (section 6: `Domain:`, `AP-12:` lines, boot section, `DB target:`, `TOTAL`,
equal coverage numbers, exit code 0); otherwise it prints nothing, lists what is missing, and Phase 3
is not complete — fix and re-run.

What the three lines assert, and what the evidence is:
- `Application boots without errors` — the boot section of the validation log.
- `All endpoints respond correctly` — `api-test.sh` exit 0 with every inventoried endpoint exercised
  **and** `arch-check.sh` exit 0.
- `Zero anti-patterns remaining` — every report finding is resolved (every cited location fixed and
  its per-finding check passing) or `left open` by an explicit Phase 2 answer. A finding with
  neither is unfinished work (section 1, step 3): no box is printed. Lines `left open` and problems
  noticed during Phase 3 are counted in `Findings:` below and listed in *Future improvements*.

Right under the box print `## Validation evidence`:

```
api-test.sh:  <N> checks, <N> failures, <N> skipped, <N>/<N> endpoints — exit <code>
arch-check:   exit <code>, <N> route file(s) checked
Findings:     <N> resolved, <N> left open, <N> noticed during Phase 3
Anti-tautology: <injected defect> → caught by <check>; ...
Report:       reports/audit-project-<N>.md
Log:          evidence/logs/<project>-validation.txt
```

Every value is the real one; `left open` equals the plan's `left open` lines; `Report:` and `Log:`
are printed only after `test -s` succeeded on that path. A check that was not run has no line —
report the gap instead. Then print the `## Future improvements` list.

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Address already in use` on boot | Another process holds the port | Boot on a free port and run `BASE_URL=http://localhost:<port> ./api-test.sh` |
| `ModuleNotFoundError` / `Cannot find module` | Dependencies not installed | `pip install -r requirements.txt` in a venv / `npm install`; never edit the code to dodge a missing package |
| `arch-check.sh` exit 2 or a `note: … not verified` line | Routes, models or controllers not recognized, or a stack without function segmentation | Set the variables of section 3 and re-run, or read the code for that rule and record the gap |
| `api-test.sh` exit 2 | App not reachable at `BASE_URL`, or `DB target: not isolated` | Boot it against a throwaway database and re-run — exit 2 means nothing was tested |
