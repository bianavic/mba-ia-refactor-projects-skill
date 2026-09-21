# Target Architecture Guidelines (Phase 3)

The refactoring target is always MVC, adapted to the detected language/framework. Do not force a specific folder layout onto every project — apply these responsibility rules to whatever layout fits the stack, and adapt (not rebuild) any layering that already exists.

## Layer responsibilities

### Models
- Own all data access (queries, ORM calls) and domain rules that belong to that data (validation invariants, derived properties like `is_overdue`, password hashing/verification).
- Never import routing/HTTP framework code. A model does not know it is being called from an HTTP request.
- Serialization methods (`to_dict`/`toJSON`) must exclude sensitive fields (password hashes, tokens) unless a caller explicitly needs the raw record for internal use — public-facing serialization always redacts them.

### Views / Routes
- Only responsible for: binding an HTTP method + path to a handler, parsing the incoming request into plain data, calling the Controller, and serializing the Controller's result into a response.
- Must not contain SQL, business rules, direct ORM/query calls, or duplicated domain logic — if a route needs something domain-specific, it calls the Controller/Service function that owns it instead of reimplementing it or reaching into the Model itself. This has no exception for partially-layered or already-organized projects (see below).
- Must not swallow errors ad hoc per-route — delegate to centralized error handling (see below).

### Controllers
- Orchestrate the flow between Routes and Models/Services: validate input shape, call the right Model/Service methods in the right order, decide the response status/shape.
- Contain application flow, not domain rules — a rule like "a task is overdue when X" belongs on the Model, not copy-pasted into every Controller that needs it.
- Should be thin enough to unit test without spinning up the HTTP server.

### Supporting layers (create only if the project needs them)
- **Config module:** centralizes all configuration (secrets, DB paths, feature flags) sourced from environment variables/`.env`, never literal values in application code.
- **Services:** optional layer for logic that spans multiple models or talks to external systems (email, notifications, payment gateways). If a service module exists, it must actually be wired into a Controller — an unconnected service is a finding (AP-10), not architecture.
- **Middlewares / centralized error handling:** one place that turns exceptions into consistent HTTP error responses, instead of try/except-per-route.
- **Entry point / composition root:** one clear file that wires config, DB, routes, and error handling together and starts the app — no business logic here.

## Stack-specific mapping

### Python / Flask
```
src/
├── config/
│   └── settings.py          # env-driven config, no hardcoded secrets
├── models/
│   ├── product_model.py
│   └── user_model.py        # data access + domain rules per entity
├── controllers/
│   ├── product_controller.py
│   └── order_controller.py  # orchestration, no raw SQL
├── routes/
│   └── routes.py            # Blueprint registration, thin handlers
├── middlewares/
│   └── error_handler.py     # Flask errorhandler(s)
└── app.py                   # composition root
```

### Node.js / Express
```
src/
├── config/
│   └── index.js             # env-driven config
├── models/
│   ├── userModel.js
│   └── courseModel.js       # DB access + domain rules
├── controllers/
│   ├── checkoutController.js
│   └── reportController.js  # orchestration, no raw SQL
├── routes/
│   └── index.js             # express.Router() wiring, thin handlers
├── middlewares/
│   └── errorHandler.js      # centralized Express error middleware
└── app.js                   # composition root
```

### Partially-layered projects (e.g. an existing `models/routes/services/utils` structure)
- Keep the existing folder names; fix responsibilities *inside* them instead of renaming everything.
- Every route handler must be reduced to: parse the request, call one Controller/Service function, serialize the result. A route that still contains a direct ORM/query call (`Model.query...`, `db.session.add/commit/delete`, or equivalent) is not "playing the Controller role cleanly" — that is always a Views/Routes violation, no matter how small or non-duplicated the query is, and this holds even when the project already has folders and no exception applies. Move such calls into the existing `services/` module if one already exists for that domain, or into a new lightweight `controllers/` module otherwise; the route may only call that function.
- If routes contain duplicated business logic (AP-06), move the shared rule into the existing Model/Service and have every route call it.
- If a `services/` folder exists but is dead code (AP-10), either wire it into the appropriate route/controller or remove it — never leave it both present and unused. If a `services/` folder is already wired for *some* routes in a module (e.g. only report reads), extend it to cover every route in that same module rather than leaving a half-migrated file.

### Verifying AP-16 mechanically (Phase 3, step 6)

Endpoint tests cannot verify this rule: a route that queries the DB directly and one that
properly delegates to a Controller/Service return exactly the same HTTP response, so functional
testing alone cannot tell them apart. Verification has to be structural — grep the route/view
files themselves and confirm there are zero direct persistence calls left:

- ORM session calls (`db.session.add/commit/delete`)
- query attributes (`Model.query...`)
- Model finders/writers (`Model.find/findById/create/update/get_by_id/find_by_x(...)`)
- driver/cursor calls (`cursor.execute`, `db.run/all/get`)
- raw SQL literals

Adapt the patterns to the detected stack — `references/verification-recipes.md` has the signals per
language, the bundled `scripts/arch-check.sh`, and the procedure for a stack not listed there. Note
especially that languages exposing persistence as free functions rather than methods (Go, Elixir,
Rust) need a different pattern shape: a receiver-based regex silently reports a clean result on a
route file that is full of violations. Any hit must be moved into a Controller/Service before
Phase 3 can be reported complete — "the project already has folders" is not an exemption (see
*Partially-layered projects* above). This check is mandatory and is never skipped, even when
every endpoint from step 5 responds correctly.

## Non-negotiable output constraints

- Every original endpoint (method + path) must still exist and behave the same after the refactor.
- No endpoint may change its response shape except to redact a previously-leaked sensitive field (AP-04) — that is an intentional, expected difference.
- The composition root/entry point must still be a single obvious place to start the app (`app.py`, `app.js`, etc.).
