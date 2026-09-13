# Target Architecture Guidelines (Phase 3)

The refactoring target is always MVC, adapted to the detected language/framework. Do not force a specific folder layout onto every project — apply these responsibility rules to whatever layout fits the stack, and adapt (not rebuild) any layering that already exists.

## Layer responsibilities

### Models
- Own all data access (queries, ORM calls) and domain rules that belong to that data (validation invariants, derived properties like `is_overdue`, password hashing/verification).
- Never import routing/HTTP framework code. A model does not know it is being called from an HTTP request.
- Serialization methods (`to_dict`/`toJSON`) must exclude sensitive fields (password hashes, tokens) unless a caller explicitly needs the raw record for internal use — public-facing serialization always redacts them.

### Views / Routes
- Only responsible for: binding an HTTP method + path to a handler, parsing the incoming request into plain data, calling the Controller, and serializing the Controller's result into a response.
- Must not contain SQL, business rules, or duplicated domain logic — if a route needs to compute something domain-specific, it calls a Model/Service method instead of reimplementing it.
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
- If routes contain duplicated business logic (AP-06), move the shared rule into the existing Model/Service and have every route call it — do not introduce a new Controller layer if the project's routes already play that role cleanly once the duplication is removed.
- If a `services/` folder exists but is dead code (AP-10), either wire it into the appropriate route/controller or remove it — never leave it both present and unused.

## Non-negotiable output constraints

- Every original endpoint (method + path) must still exist and behave the same after the refactor.
- No endpoint may change its response shape except to redact a previously-leaked sensitive field (AP-04) — that is an intentional, expected difference.
- The composition root/entry point must still be a single obvious place to start the app (`app.py`, `app.js`, etc.).
