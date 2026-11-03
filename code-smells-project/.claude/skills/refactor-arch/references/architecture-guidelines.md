# Target Architecture Guidelines (Phase 3)

The target is always MVC, laid out in the detected stack's idiom. Apply these responsibility rules
to whatever layout fits; adapt existing layering instead of rebuilding it.

## Contents
- Layer responsibilities
- Placement decision table
- Code written during Phase 3
- Partially-layered projects

## Layer responsibilities

### Models
- Own all data access (queries, ORM calls) and the domain rules of that data (invariants,
  derived properties, password hashing/verification).
- Never import routing/HTTP code — a model does not know it is called from a request.
- Public serialization never includes sensitive fields (hashes, tokens).

### Views / Routes
- Bind method + path to a handler, parse the request into plain data, call one Controller
  function, serialize its result. Nothing else — a route never calls a Model or Service directly.
- No SQL, ORM/query calls, model finders, business rules or duplicated domain logic — no exception
  for small or already-organized projects.
- No ad hoc per-route error handling; errors go to the central handler.

### Controllers
- Orchestrate: validate input, call **one** Service or **one** Model, decide status and response shape.
  Needing a second model or an external system means the call belongs in a Service.
- Application flow, not domain rules — a rule needed by several controllers lives on the Model of
  its entity, or on a Service when it spans entities or an external system.
- Thin enough to unit test without the HTTP server.

### Supporting layers
- **Config:** every secret, path, flag and domain constant, sourced from env where it is deployment
  config — never a literal in application code.
- **Services:** use cases that span several models or talk to external systems (email,
  notifications, payments). Mandatory when a criterion in "Placement decision table" holds.
  A service must be wired into a Controller; an unwired one is AP-11.
- **Central error handling:** one place turning exceptions into consistent responses.
- **Composition root:** one obvious entry point (`app.py`, `app.js`…) that wires config, DB, routes
  and error handling and starts the app — no business logic.

## Placement decision table

Apply to every function or block of code, not to whole files: a file that mixes layers is split,
each part going to the row it matches. First matching row wins; the row is the justification printed
in the Phase 3 layout table (`file → layer → criterion`, one row per resulting file).

| Criterion (checkable in the code) | Destination |
|---|---|
| Binds method + path, reads the request, calls one function, serializes the result | Route |
| Validates input, calls **one** Service or **one** Model, decides the success status and response shape; failures are raised as typed errors, never turned into responses here | Controller |
| A use case that reads or writes **≥ 2 models** or calls an external system | **Service** (`<entity>_service`, one per use-case group) |
| Queries/ORM calls of one entity, its invariants and derived values (even when several controllers use them), password hashing | Model |
| A model needs data of another entity | The Service calls both models; models never import each other |
| Reads env/constants: secrets, paths, flags, statuses, categories, rates, limits | Config |
| Wraps a route before the handler (authentication, authorization, rate limit, request parsing) | Middleware |
| Exception types and the code turning them into responses | Errors (central handler) |
| Stateless helpers with no domain meaning (hashing, masking, formatting) | Utils |
| Connection, schema, migrations, seed data the app loads itself | Database/infrastructure module (a standalone seed script run by hand may stay at the root) |
| Wires config, database, middleware, routes, error handling and starts the app | Composition root (the entry point) |

Rules the table implies:
- **Root holds only the entry point, manifests, standalone scripts (a seed), tool config files and
  tests** (`AP-23`, the same exemptions as `arch-check.sh`). Every other source file lives in a
  directory named for its role: the MVC layers — `models/`, `routes/` (or `views/`), `controllers/`
  — plus `services/` when the table requires one and the supporting `config/`, `middlewares/`,
  `errors/`, `utils/`, `database/`, adapting to names the project already uses.
- **A model imports no other model and no HTTP/routing code** (`AP-22`).
- **A controller function calls at most one model**; a second model, or an external system, makes
  it a Service call.
- **In a tightly coupled monolith, decouple before moving.** First break every model→model import
  by moving the cross-entity call into the Service that will own it (RP-21), one use case at a
  time; only then move files into their role directories (RP-22). Moving files first carries the
  coupling into the new layout and forces a second pass. Re-run `api-test.sh` after each step.
- A Service raises typed errors, never HTTP responses; it does not import routing code.
- A project with one entity and no external call needs no Service: the table decides, not the
  project size. State "no row matched Service" in the layout table when that is the case.

## Code written during Phase 3

- One module per responsibility and per domain — not one `models` file for every entity. Name
  them in the stack's file-naming idiom, keeping the domain noun in the project's language:
  `produto_model.py`, `produto_controller.py` in Python; `produto.model.js` or `produtoModel.js` in
  Node — whichever the project already uses, applied to every file.
- Dependencies follow one call flow; a layer never imports a layer above it. Within a layer, a
  Model never imports another Model, and a Service may call another Service only when no import
  cycle results (a circular import breaks boot):

  ```
  Request → [Middleware: auth, parsing] → Route (View) → Controller → Service* → Model → DB
  Error raised in any layer → Errors (central handler) → Response
  Composition root: wires config, database, middleware, routes, error handling.
  Config: read only by the composition root / config module and injected; no other layer reads the environment.
  * only when the placement table requires one (RP-21)
  ```
  A controller layer exists whenever routes exist: every route file calls controllers, and every
  controller is called by a route file. Persistence moved into a Service while the route still
  holds the request flow is layers renamed, not separated.
- Authorization follows the owner rule of RP-16.
- Create a controller file with its functions before editing the route that will call it. After
  moving code, run the delegation and smoke check (`references/phase3-validation.md` → 4).
- Keep the project's language, naming and response keys; never translate domain nouns.
- Validation errors name the field and expected shape; 500s never carry exception text.
- Logging goes through the stack's logger and never writes personal data.
- Behavior is proven by `api-test.sh` and structure by `arch-check.sh`; an existing unit-test
  suite is kept passing but replaces neither.

## Partially-layered projects

- Keep existing folder names; fix responsibilities inside them.
- A route with any direct ORM/query call is a violation however small: the query moves to the
  Model, the request flow (validation, authorization, status and response shape) to a Controller —
  a new `controllers/` module when none exists (RP-14). A `services/` module keeps only what the
  Services rule allows; it never becomes a domain's controller or data-access layer.
- Duplicated rules move into the Model of their entity, or into a Service when they span entities
  (RP-04); when the Model already has the rule, the copies are replaced by calls to it.
- Supporting modules already grouped (`utils/`, `middlewares/`) are kept; loose ones join them (RP-22).
- A dead `services/` module is wired or removed (RP-10); one wired for only some routes of a module
  is extended to all of them — no half-migrated files.
