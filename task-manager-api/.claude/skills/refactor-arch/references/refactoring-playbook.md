# Refactoring Playbook (Phase 3)

Practical guide to converting anti-patterns into sustainable solutions. Each pattern includes the
problem it fixes, the strategy, and before/after code — in Python, in JavaScript (Node/Express),
or both, and the parts that are easy to get wrong. Snippets use placeholder names — translate the
idea into the detected stack and the project's own names.

An RP keeps inputs and outputs identical unless the variant chosen changes what an endpoint
answers. Such a variant is a `[CONTRACT_CHANGE]` plan line (`SKILL.md`, *Plan format*), applied only
as the user chose in Phase 2:
- **Always:** RP-09 (removes a leaked field), RP-16, RP-19 and RP-20.
- **When the variant does:** RP-04 when the copies had already diverged; RP-07 when the default
  page size cuts today's full list; RP-11 when a 500 stops carrying the exception text; RP-12 when
  the upgrade crosses a major version that changes an answer; RP-18 when deletion starts de-linking
  or removing related rows.

## Contents
| RP | Transformation | Fixes |
|---|---|---|
| RP-01 | Parameterize queries | AP-01 |
| RP-02 | Secrets and settings to configuration | AP-02 |
| RP-03 | Break up a God Class | AP-06 |
| RP-04 | Centralize duplicated business logic | AP-07 |
| RP-05 | Remove global mutable state | AP-08 |
| RP-06 | Fix N+1 queries | AP-09 |
| RP-07 | Add pagination | AP-10 |
| RP-08 | Replace print/console logging | AP-13 |
| RP-09 | Hash passwords, stop serializing sensitive fields | AP-03, AP-04 |
| RP-10 | Wire up or delete dead code | AP-11 |
| RP-11 | Centralize error handling | AP-06, AP-21 |
| RP-12 | Replace deprecated APIs, upgrade vulnerable versions | AP-12 |
| RP-13 | Remove unused imports and inline configuration | AP-14, AP-15 |
| RP-14 | Move persistence out of routes | AP-06 |
| RP-15 | Apply one naming convention | AP-16 |
| RP-16 | Enforce authentication and authorization | AP-05, AP-17 |
| RP-17 | Keep personal data out of logs | AP-18 |
| RP-18 | Erase a data subject completely | AP-19 |
| RP-19 | Take arbitrary execution off the request path | AP-20 |
| RP-20 | Validate input at the boundary | AP-21 |
| RP-21 | Extract a Service for multi-model use cases | AP-22 |
| RP-22 | Group supporting modules by role | AP-23 |

## RP-01 — Parameterize queries

```python
cur.execute("SELECT * FROM <table> WHERE id = " + str(id))       # before
cur.execute("SELECT * FROM <table> WHERE id = ?", (id,))          # after
```
Dynamic filters append placeholder fragments and grow the params list together. Identifiers that
cannot be bound (sort column, table name) are checked against an allowlist.

## RP-02 — Secrets and settings to configuration

```python
app.config["SECRET_KEY"] = "<literal>"                            # before
SECRET_KEY = os.environ["SECRET_KEY"]                             # after, in the config module
```
```js
const config = { apiKey: "<literal>" };                           // before
const config = { apiKey: process.env.<SECRET_NAME> };              // after, in the config module
```
- Debug off unless enabled by env; remove every secret from response bodies; ship a
  `.env.example` without real values.
- Tell the user a leaked secret must be rotated — deleting it from the code does not un-leak it.
- Seed/fixture credentials are secrets too (even when hashed on insert): read them from env or
  generate a random one on first seed. Cover every seed location the finding cites.

## RP-03 — Break up a God Class

```python
# before: app.py — connection, routes and rules together
@app.post("/<resources>")
def create():
    db.execute("INSERT ..."); ...

# after
# routes/<entity>_routes.py      → parse request, call controller, serialize
# controllers/<entity>_controller.py → flow and validation
# models/<entity>_model.py       → data access and domain rules
```
```js
// before: one class — schema, seed, routes and rules together
class <App>Manager { setupRoutes(app) { app.post("/<resources>", (req, res) => { this.db.run("INSERT ..."); }); } }

// after
// routes/<entity>Routes.js          → method + path → controller
// controllers/<entity>Controller.js → flow and validation
// models/<entity>Model.js           → data access and domain rules
```
Move one domain at a time and re-run `api-test.sh` between moves.

## RP-04 — Centralize duplicated business logic

```python
# before: the rule copied by hand in N route handlers
if item.due < now() and item.status != "<done>": ...

# after: one owner, the Model of the entity; every handler calls it
class <Entity>(db.Model):
    def is_overdue(self):
        return self.due < now() and self.status != "<done>"

if item.is_overdue(): ...
```
When the Model already has the rule, the fix is only replacing each copy with the call. A rule
spanning several entities goes to a Service (RP-21) instead.
If the copies had already diverged, keeping one behavior changes the other endpoint's answer —
that choice is a Phase 2 decision, never a silent one.

## RP-05 — Remove global mutable state

```python
_conn = sqlite3.connect(path, check_same_thread=False)            # before: shared by all threads
def get_db():                                                     # after: per request
    if "db" not in g: g.db = sqlite3.connect(path)
    return g.db
@app.teardown_appcontext                                          # close it when the context ends
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None: db.close()
```
```js
// before: module state shared by every request, unbounded, exported by value
let cache = {};                                                    // one entry per user, never evicted
let total = 0;                                                     // importers get a copy; never updated
module.exports = { cache, total };

// after: what is read gets an owner with a lifecycle, created at the composition root and injected
function createCache({ maxEntries }) {                             // in its own module
    const entries = new Map();
    return {
        get: key => entries.get(key),
        set(key, value) {
            if (entries.size >= maxEntries) entries.delete(entries.keys().next().value);
            entries.set(key, value);
        },
    };
}
const cache = createCache({ maxEntries: config.CACHE_MAX_ENTRIES }); // app.js
const <useCase>Service = create<UseCase>Service({ cache });
// `total`, which nothing reads, is deleted; when needed it is computed from the database
```
```js
// a shared connection that needs serialized transactions: the queue is owned by the connection module
let queue = Promise.resolve();
function transaction(work) {
    const result = queue.then(() => runInTransaction(work));
    queue = result.catch(() => {}); return result;
}
```
State that must be shared gets an owner with a defined lifecycle, created at the composition root
and injected. State nothing reads is dead code (RP-10): delete it.

## RP-06 — Fix N+1 queries

```python
for o in orders: o["items"] = q("SELECT ... WHERE order_id = ?", o["id"])       # before: 1 + N
items = q(f"SELECT ... WHERE order_id IN ({marks})", ids)                       # after: 2, grouped in memory
```
```js
parents.forEach(p => db.all("SELECT ... WHERE <parent>_id = ?", [p.id], cb));          // before: 1 + N
if (ids.length === 0) return [];                                                       // after: IN () is invalid SQL
const rows = await all(`SELECT ... WHERE <parent>_id IN (${ids.map(() => "?").join(",")})`, ids);  // 2 queries, grouped in a Map
```
With an ORM, use its eager loading (SQLAlchemy: `select(<Parent>).options(selectinload(<Parent>.<children>))`).
Guard the empty list first: `IN ()` is invalid SQL. The response shape stays identical.

## RP-07 — Add pagination

```python
rows = q("SELECT * FROM <table>")                                 # before
rows = q("SELECT * FROM <table> ORDER BY id LIMIT ? OFFSET ?", (per_page, (page - 1) * per_page))  # after
```
```js
db.all("SELECT * FROM <table>", [], cb);                           // before
db.all("SELECT * FROM <table> ORDER BY id LIMIT ? OFFSET ?", [limit, offset]);  // after
```
Bounded page size; invalid values answer 400. If clients expect the full list, the default keeps
today's answer — otherwise it is a contract change decided in Phase 2.

## RP-08 — Replace print/console logging

```python
print("ERROR: " + str(e))                                         # before
logger.error("Failed to <action>", exc_info=e)                    # after, module-level logger
```
```js
console.log(`<message> ${value}`);                                 // before
logger.info(`<message> ${value}`);                                 // after, one logger module with levels
```
Every new log call is also checked against RP-17.

## RP-09 — Hash passwords, stop serializing sensitive fields

```python
cur.execute("INSERT ... VALUES (?, ?)", (email, pw))               # before: stored as typed
cur.execute("... WHERE email = ? AND password = ?", (email, pw))  # before: plaintext compare

from werkzeug.security import generate_password_hash, check_password_hash
cur.execute("INSERT ... VALUES (?, ?)", (email, generate_password_hash(pw)))   # after: salted hash on write
row = find_by_email(email); ok = row and check_password_hash(row["password"], pw)   # after: verify
```
```js
const hash = Buffer.from(pw).toString("base64");                  // before: encoding, not hashing
const scrypt = util.promisify(crypto.scrypt);                      // after: scrypt is callback-based
const salt = crypto.randomBytes(16);                               // random, >= 16 bytes, per password
const stored = `scrypt$${salt.toString("hex")}$${(await scrypt(pw, salt, 64)).toString("hex")}`;
crypto.timingSafeEqual(await scrypt(pw, salt, expected.length), expected);  // verify: same length, constant time
```
- Existing rows hold plaintext or old hashes: migrate them (at boot or on next successful login)
  or document a forced reset — say which.
- Each response is built from an explicit field list for its audience: secrets never; card data
  masked; other people's identifiers masked (full only to their subject), other personal data
  removed or the endpoint restricted, as chosen in Phase 2.

## RP-10 — Wire up or delete dead code

```python
# before: services/<feature>_service.py — implemented, imported by nothing

# after (wire): the use case that owns the action calls it. A model plus an external system is a
# Service (RP-21), so the call goes there, not into the controller
def create(data):                                                  # services/<entity>_service.py
    row = <entity>_model.insert(data)
    <feature>_service.notify(row)
    return row

# after (delete): remove the module, its imports and its settings; no answer changes
```
Wire a module only when its feature is clearly intended (a notification service matching an
existing action) — confirmed in Phase 2 if it changes behavior. Otherwise delete it.

## RP-11 — Centralize error handling

```python
except Exception as e: return jsonify({"<error>": str(e)}), 500   # before, in every handler

class AppError(Exception):                                         # after: errors/, typed errors
    status = 500
    def __init__(self, message): super().__init__(message); self.message = message
class NotFound(AppError): status = 404
class ValidationError(AppError): status = 400
class Forbidden(AppError): status = 403

@app.errorhandler(AppError)                                        # registered once, by the composition root
def app_error(e): return jsonify({"<error>": e.message}), e.status

@app.errorhandler(Exception)
def unexpected(e):
    if isinstance(e, HTTPException): return e                      # keep 404/405 as they are
    logger.exception("Unhandled error")
    return jsonify({"<error>": "<generic message>"}), 500
```
```js
if (err) return res.status(500).send("<error>");                   // before, in every callback
const asyncHandler = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);  // after (Express 4)
router.post("/<resources>", asyncHandler(<entity>Controller.create));
app.use((err, req, res, next) => {                                 // registered last; must keep 4 args
    if (res.headersSent) return next(err);
    if (err instanceof AppError) return res.status(err.status).json(err.body);
    logger.error(err.stack); res.status(500).json({ <error>: "<generic message>" });
});
```
Express 5 forwards rejected promises from async handlers on its own; `asyncHandler` is needed only on 4.x.
Handlers raise typed errors (not found, validation) mapped to their status in one place. Keep the
error key and the messages the API already returns for known cases.

## RP-12 — Replace deprecated APIs, upgrade vulnerable versions

```python
<deprecated call>(...)                                            # before
<replacement documented for the installed version>(...)           # after
```
```text
<package>==<old version>                  # before, requirements.txt
<package>==<fixed version>                # after
```
```bash
pip install -r requirements.txt           # in the project's venv
pip-audit -r requirements.txt             # confirm no advisory remains for the new version
```
```json
"<package>": "^<old version>"
```
```bash
npm install <package>@^<fixed version>    # rewrites package.json and package-lock.json together
npm audit                                 # confirm no advisory remains for the new version
```
- Upgrade first, then replace: confirm each replacement in the docs/changelog of the version
  now installed — replacements differ across major versions — and that it returns an
  equivalent value (timezone-aware vs. naive datetimes compare differently).
- A vulnerable or end-of-life version: bump the pin to a release fixing every advisory found —
  latest patch of the current line when that suffices. Crossing a major version is its own Phase 2
  decision (read its migration notes). Install the new versions before booting; `api-test.sh`
  must pass on them.

## RP-13 — Remove unused imports and inline configuration

```python
if status not in ["<a>", "<b>", "<c>"]: ...                       # before
if status not in config.STATUSES: ...                             # after
```
```js
const status = value.startsWith("<x>") ? "<A>" : "<B>";             // before
const status = value.startsWith(config.<PREFIX>) ? config.<STATUS>.a : config.<STATUS>.b;  // after
```
Then search for **each moved value on its own**, not only the list it came from — the same value
reappears as a lone literal elsewhere, typically inside SQL (`WHERE status = '<a>'`) or a schema
default. Bind it as a parameter from config. A value in config and still hardcoded elsewhere has
two sources of truth: not fixed.

## RP-14 — Move persistence out of routes

```python
@bp.delete("/<resources>/<int:id>")                               # before
def remove(id):
    db.execute("DELETE FROM <table> WHERE id = ?", (id,)); db.commit()
    return "", 204

@bp.delete("/<resources>/<int:id>")                               # after
def remove(id):
    return <entity>_controller.remove(id)   # controller returns ("", 204); NotFound → RP-11 handler
```
```js
app.delete("/<resources>/:id", (req, res) => { db.run("DELETE FROM <table> WHERE id = ?", [req.params.id], cb); });  // before
router.delete("/<resources>/:id", asyncHandler(<entity>Controller.remove));   // after: 404 via RP-11
```
Every query, ORM call, commit and model finder leaves the route: the query goes to the Model, the
request flow (validation, status, response shape) to a Controller — a new one when none exists.
A Service is added only where RP-21 requires it, never as a substitute for the Controller.

## RP-15 — Apply one naming convention

```python
# before: sibling modules name the same operation two ways
def listar_<entidades>(): ...                                     # <entidade>_controller.py
def get_all_<outras_entidades>(): ...                             # <outra_entidade>_controller.py

# after: the dominant convention, applied to every sibling
def listar_<outras_entidades>(): ...
```
English pattern words with domain nouns in the project's language, applied uniformly, are not a
finding (AP-16): never translate domain nouns to "fix" them.
```js
let u = req.body.<field>; let c = req.body.<other_field>;              // before: cryptic locals
const { <field>, <other_field> } = req.body;                          // after: body names are contract
<useCase>Service.run({ <descriptiveName>: <field> });                 // internal names descriptive
```
Internal names only. Route paths, request/response fields, columns and user-facing messages are
contract — report a name that could only be fixed by changing one of them instead of changing it.

## RP-16 — Enforce authentication and authorization

Every route's access level (`public | authenticated | owner-or-admin | admin`) is a Phase 2 decision confirmed in the Phase 2 access table. Routes the user did not confirm are not guarded or opened by this RP.

**Owner rule.** For an owner-or-admin operation, resolve the resource's owner first
(`resource id → persisted owner identity`, one resolver per resource type) and compare that owner
with the caller — never an object id with a caller id. Name the resolver in the plan. Verify every
mutating operation with four callers — owner, another user, admin, anonymous — on a resource whose
id differs from its owner's id.

```python
@bp.delete("/<resources>/<int:id>")                               # before: open
@bp.delete("/<resources>/<int:id>")                               # after
@require_role("<admin>")
```
```js
router.get("/<resources>", handler);                               // before: open
router.get("/<resources>", requireRole("<admin>"), asyncHandler(handler));  // after
```
- Build on the mechanism the project has (a login that issues a token, a session). If the project
  has no accounts at all, do not invent an auth system — report the gap.
- Missing/invalid credentials → 401; authenticated but not allowed → 403.
- A privilege field the guard reads is writable only by an administrator; public signup assigns
  the default role and ignores it in the body (AP-17). Re-check AP-17 afterwards.

## RP-17 — Keep personal data out of logs

```python
logger.info("Login failed: %s", email)                            # before
logger.info("Login failed: %s", mask_email(email))                # after: one masking helper
```
```js
logger.info(`<message> ${email}`);                                 // before
logger.info(`<message> ${maskEmail(email)}`);                      // after: one masking helper
```
Name the fields logged — never a whole body or model object; check `except` blocks and error
middleware too.

## RP-18 — Erase a data subject completely

```sql
-- before: DELETE FROM <users> WHERE id = ?   (orders, audit rows still point at the id)
-- after, one transaction:
UPDATE <orders> SET <user_id> = NULL WHERE <user_id> = ?;   -- kept for accounting, de-linked
DELETE FROM <sessions> WHERE <user_id> = ?;                 -- exists only to serve the user
DELETE FROM <users> WHERE id = ?;
```
```python
with transaction():                                               # after: de-link, then delete
    <related>_model.unlink_user(user_id)
    user_model.delete(user_id)
```
```js
await db.transaction(async () => {                                 // after: de-link, then delete
    await <related>Model.unlinkUser(id); await userModel.deleteById(id);
});
```
List every table and in-memory structure holding the id (including ids inside free text) before
writing it. Unknown id → 404.
Export: an owner/admin GET returning the subject's rows from those same tables. Retention: a configurable
age after which personal fields are de-linked the same way.

## RP-19 — Take arbitrary execution off the request path

```python
@bp.post("/admin/query")                                          # before
def run(): return jsonify(db.execute(request.json["sql"]).fetchall())

@bp.post("/admin/query")                                          # after: route kept, capability off
@require_role("<admin>")
def run():
    return admin_controller.run_query(g.user, request.get_json())

# controllers/admin_controller.py
def run_query(user, data):
    if not config.ADMIN_QUERY_ENABLED: raise Forbidden("<disabled>")   # → 403 via RP-11
    ...
```
Variants to offer in Phase 2, recommendation first (removing the route is never a variant — rule 5; when the user rules out the flag/allowlist, the route stays, admin-only, and the residual is named exactly): disabled by default behind an env flag
(documented with its risk in `.env.example`; when on, admin-only and logged by user id) · a fixed
allowlist of named read-only operations · leave open as accepted risk.

## RP-20 — Validate input at the boundary

```python
price = data["price"]                                             # before: "abc" → TypeError → 500
if price < 0: ...
price = data.get("price")                                         # after
if not isinstance(price, (int, float)) or price < 0:
    raise ValidationError("price must be a number >= 0")          # → 400 via RP-11
```
```js
if (!body.<field>) return res.status(400).send("<message>");       // before: 123 or "abc" pass
if (typeof body.<field> !== "string" || body.<field>.trim() === "")  // after: types checked
    throw new ValidationError("<message>");                         // → 400 via RP-11
```
One validator per resource, shared by create **and** update; if they had diverged, the stricter
rule is a Phase 2 decision. Keep the error key the API already uses.

## RP-21 — Extract a Service for multi-model use cases

```python
# before: controller decides the use case, or a model reaches into another model
def create_order(data):
    user = user_model.find(data["user_id"]); ...
    return order_model.insert(user["id"], items)

# after
# controllers/order_controller.py → validate, call one function; typed errors propagate to RP-11
def create_order(data):
    payload = validate_order(data)
    return order_service.create_order(payload)

# services/order_service.py → the use case: calls both models, owns the rule, raises typed errors
def create_order(payload):
    if not user_model.find(payload["user_id"]): raise NotFound("user")
    return order_model.insert(payload["user_id"], payload["items"])
```
```js
db.run("INSERT INTO <a> ...", p, function () { db.run("INSERT INTO <b> ...", q, cb); });  // before: nested, no transaction
const id = await db.transaction(async () => {                      // after, in <useCase>Service
    const aId = await <a>Model.create(<args>); await <b>Model.create(aId, <args>); return aId;
});
```
- One `<entity>_service` per use-case group named by the criterion that required it (≥ 2 models
  or an external system). A rule of one entity stays on its Model even when several controllers
  use it (RP-04). Models keep only their entity's queries and
  invariants; a model function that called another model becomes two model calls in the Service.
- Transactions spanning both entities open in the Service (or in a model helper it calls), never
  in the controller.
- The Service returns data or raises typed errors (RP-11); it never builds a response.
- Move one use case at a time and re-run `api-test.sh` between moves; the response stays identical.
- Wire every Service into a Controller in the same step (an unwired Service is AP-11).

## RP-22 — Group supporting modules by role

```text
# before: project root
app.py  auth.py  config.py  errors.py  error_handlers.py  security.py  database.py

# after
app.py                       # composition root
config/        settings
middleware/    auth
errors/        exceptions + handler
utils/         hashing, masking
database/      connection, schema, seed data the app loads
```
- Directory per role from the Placement decision table; reuse a directory the project already
  has (`utils/`, `middleware/`) before creating another. New names follow the stack's conventions
  (Placement decision table rules in `architecture-guidelines.md`).
- A standalone seed script run by hand may stay at the root (`arch-check.sh` exempts it).
- Update every import in the same step; a package needs its marker file where the language
  requires one (`__init__.py`).
- Names of routes, fields and messages are contract; only file locations and import paths change.
- Re-run `arch-check.sh`: no AP-23 line and the entry point still boots.
