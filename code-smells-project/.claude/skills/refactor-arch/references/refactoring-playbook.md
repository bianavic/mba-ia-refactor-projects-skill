# Refactoring Playbook (Phase 3)

Concrete transformation for each anti-pattern in `anti-patterns-catalog.md`. Each pattern is language-illustrated with Python and/or Node.js — apply the same principle in whatever language Phase 1 detected, even if neither example matches exactly.

## RP-01 — Parameterize SQL queries (fixes AP-01)

**Before (Python):**
```python
cur.execute("SELECT * FROM users WHERE id = " + str(user_id))
```
**After (Python):**
```python
cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**Before (Node.js):**
```js
db.run(`INSERT INTO users (name, email) VALUES ('${name}', '${email}')`);
```
**After (Node.js):**
```js
db.run("INSERT INTO users (name, email) VALUES (?, ?)", [name, email]);
```

## RP-02 — Extract configuration from hardcoded secrets (fixes AP-02)

**Before (Python):**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**After (Python):**
```python
# config/settings.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

**Before (Node.js):**
```js
const config = { paymentGatewayKey: "pk_live_1234567890abcdef" };
```
**After (Node.js):**
```js
// config/index.js
require("dotenv").config();
module.exports = { paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY };
```
Also remove the leaked value from any response body (see RP-09) and rotate the exposed secret outside of source control.

## RP-03 — Break up a God Class (fixes AP-05)

**Before:** one class/file creates the DB connection, defines every route, and runs the "business logic" inline (e.g. `AppManager` handling schema, checkout, and reporting together).

**After:** split by responsibility —
```python
# models/order_model.py — data access + domain rules
class OrderModel:
    def create(self, user_id, course_id): ...

# controllers/checkout_controller.py — orchestration only
class CheckoutController:
    def checkout(self, payload):
        order = self.order_model.create(payload["user_id"], payload["course_id"])
        return order

# routes/routes.py — thin binding
@app.post("/api/checkout")
def checkout():
    return checkout_controller.checkout(request.json)
```
Apply the equivalent split for Node/Express: `models/orderModel.js`, `controllers/checkoutController.js`, `routes/index.js`.

## RP-04 — Centralize duplicated business logic (fixes AP-06)

**Before:** the same "is overdue" check is re-written inline in 4 different routes.

**After:**
```python
# models/task.py
class Task:
    def is_overdue(self):
        return self.due_date < datetime.now() and self.status not in ("done", "cancelled")

# every route now calls the single method
if task.is_overdue(): ...
```
Delete the duplicated inline copies once every caller uses the shared method.

## RP-05 — Remove global mutable state (fixes AP-07)

**Before (Node.js):**
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
```
**After (Node.js):**
```js
// a request-scoped or properly managed cache (e.g. an injected cache service,
// or a real cache backend) instead of a shared module-level object mutated
// from concurrent request handlers
class CacheService {
  constructor() { this.store = new Map(); }
  set(key, data) { this.store.set(key, data); }
}
```

## RP-06 — Fix N+1 queries (fixes AP-08)

**Before (Python):**
```python
for pedido in pedidos:
    itens = cur.execute("SELECT * FROM itens WHERE pedido_id = ?", (pedido["id"],)).fetchall()
```
**After (Python):**
```python
ids = [p["id"] for p in pedidos]
itens = cur.execute(
    f"SELECT * FROM itens WHERE pedido_id IN ({','.join('?' * len(ids))})", ids
).fetchall()
# then group `itens` by pedido_id in memory
```

**Before (Node.js):** nested `db.all(...)` inside a `.forEach` per course, per enrollment.
**After (Node.js):** a single query joining `courses`, `enrollments`, `users`, and `payments`, or batched `IN (...)` queries per level, aggregated in memory before responding.

## RP-07 — Add pagination (fixes AP-09)

**Before:**
```python
@app.get("/produtos")
def listar_produtos():
    return jsonify(cur.execute("SELECT * FROM produtos").fetchall())
```
**After:**
```python
@app.get("/produtos")
def listar_produtos():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    offset = (page - 1) * per_page
    rows = cur.execute("SELECT * FROM produtos LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
    return jsonify(rows)
```

## RP-08 — Replace print/console logging (fixes AP-12)

**Before (Python):** `print(f"Erro ao criar pedido: {e}")`
**After (Python):**
```python
import logging
logger = logging.getLogger(__name__)
logger.error("Erro ao criar pedido", exc_info=e)
```

**Before (Node.js):** `console.log("Processando cartão", cc)`
**After (Node.js):**
```js
const logger = require("./logger"); // pino/winston instance
logger.info({ action: "process_payment" }, "Processing payment");
```
Never log secrets/PII (card numbers, keys) even at debug level.

## RP-09 — Fix password hashing and stop leaking it (fixes AP-03, AP-04)

**Before (Python, MD5):**
```python
def set_password(self, raw):
    self.password = hashlib.md5(raw.encode()).hexdigest()

def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```
**After (Python):**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password_hash = generate_password_hash(raw)

def check_password(self, raw):
    return check_password_hash(self.password_hash, raw)

def to_dict(self):
    return {"id": self.id, "email": self.email}  # hash never serialized
```

**Before (Node.js, fake base64 "hash"):**
```js
function badCrypto(pwd) {
  let hash = "";
  for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString("base64").substring(0, 2);
  return hash.substring(0, 10);
}
```
**After (Node.js):**
```js
const bcrypt = require("bcrypt");
const hash = await bcrypt.hash(pwd, 12);
const isValid = await bcrypt.compare(pwd, hash);
```

## RP-10 — Wire up or remove dead code layers (fixes AP-10)

**Before:** `services/notification_service.py` defines `NotificationService.send_task_assigned_email(...)`, never imported anywhere.
**After:** either
```python
# controllers/task_controller.py
def assign_task(self, task_id, user_id):
    task = self.task_model.assign(task_id, user_id)
    self.notification_service.send_task_assigned_email(task)  # now actually called
    return task
```
or, if the feature is genuinely out of scope, delete the dead module rather than leaving unreachable code behind.

## RP-11 — Centralize error handling (supports AP-05/AP-06 cleanup)

**Before:** every route has its own ad hoc `try/except`/`try/catch` with inconsistent status codes.
**After (Flask):**
```python
@app.errorhandler(Exception)
def handle_error(e):
    logger.error("Unhandled error", exc_info=e)
    return jsonify({"error": "internal_error"}), 500
```
**After (Express):**
```js
app.use((err, req, res, next) => {
  logger.error(err);
  res.status(500).json({ error: "internal_error" });
});
```

## RP-12 — Replace deprecated APIs (fixes AP-11)

**Before (Python):** `datetime.datetime.utcnow()`
**After (Python):** `datetime.datetime.now(datetime.timezone.utc)`

**Before (Node.js):** `new Buffer(data)` / `crypto.createCipher(alg, pwd)`
**After (Node.js):** `Buffer.from(data)` / `crypto.createCipheriv(alg, key, iv)`

Always confirm the replacement against the installed version's own docs/changelog before applying it — deprecation replacements can differ across major versions.

## RP-13 — Clean up unused imports and inline config (fixes AP-13, AP-14)

- Delete imports with no remaining reference in the file.
- Move inline literal lists that represent configuration (valid categories, limits) into the config module or a database-backed table, and read them from there.

## RP-14 — Move persistence out of routes (fixes AP-16)

**Before (Flask):** the route talks to the ORM itself.
```python
# routes/task_routes.py
@bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)      # persistence inside the route
    if not task:
        return jsonify({"error": "task not found"}), 404
    db.session.delete(task)
    db.session.commit()
    return "", 204
```

**After:** query and commit move one layer down; the route only parses, calls once, and serializes.
```python
# controllers/task_controller.py
def delete_task(task_id):
    task = task_model.get(task_id)
    if not task:
        raise NotFound("task not found")   # handled by the central error handler (RP-11)
    task_model.delete(task)

# routes/task_routes.py
@bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_controller.delete_task(task_id)
    return "", 204
```

Same shape in Node/Express: `router.delete('/tasks/:id', taskController.remove)`, with the `Task.findByPk`/`destroy` calls living in the controller or model.

If a `services/` module already exists for that domain, put the function there instead of creating `controllers/`. What is never acceptable is leaving the call in the route because "the project is already layered" — and a Model finder called straight from the route (`Task.get_by_id(...)`) is the same violation: the route must make exactly one Controller/Service call.

## RP-15 — Apply one naming/language convention (fixes AP-15)

**Before:** identifiers in two languages inside the same layer, with no rule for which goes where.
```python
# routes/product_routes.py
def listar_produtos():
    product_list = Produto.query.all()          # "product_list" here, "produtos" three lines below
    return jsonify([p.to_dict() for p in product_list])
```

**After:** adopt the convention already dominant in the project and apply it consistently to the code it owns.
```python
# routes/product_routes.py
def listar_produtos():
    produtos = produto_controller.listar()
    return jsonify(produtos)
```

**Scope limit — this one is deliberately narrow.** Rename only what is internal: local variables, helper functions, private methods. Route paths, request/response field names, and database column names are part of the contract the refactor promised not to change (see `architecture-guidelines.md`, *Non-negotiable output constraints*), so leave them exactly as they are even when they do not match the chosen convention. Same for user-facing message strings: they stay in the language the API already answers in. If a name can only be fixed by changing a response field, it is not an AP-15 fix — report it and leave it.

## RP-16 — Add authentication/authorization enforcement (fixes AP-17)

**Before (Flask):** a login endpoint issues a token, but nothing ever reads it back; every route trusts any caller.
```python
# routes/user_routes.py
@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(email=request.json['email']).first()
    if not user or not user.check_password(request.json['password']):
        return jsonify({'error': 'invalid credentials'}), 401
    token = serializer.dumps(user.id)   # issued...
    return jsonify({'token': token})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    User.query.get(user_id).delete()    # ...and never checked again, by this or any other route
    return '', 204
```
**After (Flask):** a guard reads the token back and every sensitive route requires it.
```python
# middlewares/auth.py
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
        try:
            user_id = serializer.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
        except (BadSignature, SignatureExpired):
            abort(401, description='Credenciais inválidas')
        user = db.session.get(User, user_id)
        if not user or not user.active:
            abort(401 if not user else 403)
        g.current_user = user
        return view(*args, **kwargs)
    return wrapper

# routes/user_routes.py
@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    ...
```

**Before (Node.js/Express):** every route is public, including one whose path says otherwise.
```js
router.get('/api/admin/financial-report', reportController.financialReport);
router.delete('/api/users/:id', userController.deleteUser);
```
**After (Node.js/Express):**
```js
const requireAuth = require('../middlewares/requireAuth'); // verifies a session/JWT, sets req.user
const requireRole = require('../middlewares/requireRole');

router.get('/api/admin/financial-report', requireAuth, requireRole('admin'), reportController.financialReport);
router.delete('/api/users/:id', requireAuth, userController.deleteUser);
```

**Scope limit — this one changes observable behavior, unlike every other pattern in this playbook.** Every other RP here is a refactor: same inputs, same outputs, different internal structure. Wiring enforcement onto a previously-open endpoint is not — a caller that worked yesterday gets a 401/403 today, which is exactly the kind of silent breaking change Phase 2's confirmation gate exists to prevent. Report the AP-17 finding in Phase 2 like any other, but do not apply this specific fix automatically just because the user answered "y" to the generic "proceed with refactoring" question — call out *this* change by name and get explicit confirmation of it before writing the guard and adding it to routes. If the project has no notion of accounts/roles at all (no `users` table, no login endpoint, nothing to build a guard on top of), do not invent an auth system from scratch — report the gap and stop; that is a product decision, not a mechanical refactor.

---

Every finding reported in Phase 2 must map to one of the RP-xx patterns above (or a project-specific variant following the same before/after principle) before Phase 3 starts making changes.
