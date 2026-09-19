# Verification Recipes (Phase 3, step 6)

How to prove AP-16 mechanically on **any** stack: no route/view file may reach persistence
directly. Endpoint tests cannot establish this — a route that queries the database itself and
one that delegates to a Controller/Service return byte-identical HTTP responses. Verification
must read the code.

Two ways to run the check, in order of preference:

1. **The project already ships one** (a script named like `arch-check`, an ArchUnit test, a
   lint rule, a custom ESLint/ruff/`go vet` check). Run it. Do not replace it.
2. **Otherwise, run the bundled checker**: `scripts/arch-check.sh <project-dir>`. It detects the
   languages present, selects the route/view files, and greps them for the signals below.

Never substitute "I read the diff and it looked clean" for either one.

## Interpreting the result

| Exit | Meaning | What to do |
|---|---|---|
| 0 | PASS — no inline persistence call in any route file | Phase 3 may be reported complete |
| 1 | FAIL — file:line list of violations | Move each call into a Controller/Service, re-run |
| 2 | INCONCLUSIVE — no route file identified, or no sources found | **Not a pass.** Configure the check (below) and re-run |

Exit 2 is the trap: a project whose routing layer the checker cannot find produces zero hits,
which looks like success. Treat "0 route files checked" as a failure to verify.

## Configuring the checker

Export the variables, or drop a `.arch-check.conf` shell file at the project root:

| Variable | Use when |
|---|---|
| `ROUTE_DIRS` | The routing layer lives in a directory the defaults miss (`transport`, `adapters`, `presentation`) |
| `ROUTE_FILE_GLOBS` | Route files are named unusually (`*_api.rb`, `*Resource.java`) |
| `EXTRA_PATTERN` | The stack has a persistence idiom not covered below |
| `EXCLUDE_PATTERN` | A documented, reviewed exception must be ignored |

Defaults: route files are those under a directory named `routes`, `views`, `urls`, `handlers`,
`endpoints`, `resources`, `web`, `http`, `delivery` or `api`, **or** whose filename contains
`route`, `router`, `urls`, `handler`, `endpoint` or `resource`. Middlewares, interceptors and
filters are excluded — they are a cross-cutting layer, not routing. Controllers and services are
excluded by design: they are the layer the calls are supposed to move *into*.

## Persistence signals per stack

### Python
- SQLAlchemy session: `db.session.add/commit/delete/merge/flush`, `session.execute/scalars`
- Query attribute: `Model.query...`
- Django ORM: `Model.objects...`
- Raw driver: `cursor.execute/executemany/fetchone/fetchall`, `conn.execute`
- Model finder classmethods: `Model.get_by_id(...)`, `Model.find_by_email(...)`

### JavaScript / TypeScript
- ORM statics: `Model.find/findOne/findById/findByPk/findMany/create/update/destroy/save/delete/aggregate(...)`
- Prisma: `prisma.<model>.…`
- Raw driver: `db.run/all/get/prepare`, `pool.query`, `knex(...)`, `connection.execute`

### Go
Go is where receiver-based patterns fail. Persistence is idiomatically exposed as **package-level
functions**, so `Model.Find(...)` never appears and a checker written for Python/Node reports a
false PASS on a genuinely violating file. Look for:
- Verb-first free functions: `FindOneUser(...)`, `FindManyArticle(...)`, `SaveOne(...)`,
  `DeleteArticleModel(...)`, `UpdateContextUserModel(...)`
- Functions returning a model: `GetArticleUserModel(...)`, any `Get…Model(...)`
- `database/sql` / GORM handles: `db.Query/QueryRow/Exec`, `db.Find/First/Where/Create/Save/Preload/Model/Raw`
- Connection accessors: `GetDB()`, `common.GetDB()`

The general lesson, applicable beyond Go: **first determine whether the stack exposes persistence
as methods on an object or as free functions**, then write the pattern for that shape. Rust, Elixir
and idiomatic Node service modules have the same free-function property.

### Java / Kotlin
- `entityManager.…`, `em.createQuery(...)`, `jdbcTemplate.…`, `sessionFactory.…`
- Spring Data: `<x>Repository.save/findAll/findById/findByX/delete/count(...)` called from a
  `@RestController` method body
- JPA lifecycle: `.persist(...)`, `.merge(...)`, `.flush(...)`

### Ruby
- ActiveRecord: `Model.find/find_by/where/create/update/destroy/all/first/pluck`
- `ActiveRecord::Base.connection.execute(...)`

### PHP
- Laravel: `DB::table/select/insert/update/delete/raw(...)`, Eloquent `Model::find/where/create/all(...)`
- PDO: `->prepare(...)`, `->query(...)`, `->fetchAll(...)`

### C#
- EF Core: `context.Set<T>()`, `.SaveChanges/SaveChangesAsync`, `.Add/Remove/Update/Find/FindAsync`

### Any stack
- Raw SQL literals inside a route file: `SELECT … FROM`, `INSERT INTO`, `DELETE FROM`, `UPDATE … SET`

## Deriving patterns for an unknown stack

1. From Phase 1, take the detected persistence library and read how the project's **model layer**
   calls it — those calls are exactly what must not appear in a route file.
2. Decide the call shape: method on a handle (`db.x(...)`), static/class method (`Model.x(...)`),
   or free function (`FindX(...)`). Write the regex for that shape, not for a shape borrowed from
   another language.
3. Grep one known-bad route file (before refactoring) and confirm the pattern hits it. A pattern
   that never fires on pre-refactor code is not evidence of a clean codebase — it is an untested
   pattern.
4. Pass it via `EXTRA_PATTERN` and record it in the audit report so the check is reproducible.

Step 3 is not optional. Validate the detector against a known violation before trusting a PASS.
