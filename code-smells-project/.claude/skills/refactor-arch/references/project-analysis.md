# Project Analysis Heuristics (Phase 1)

Use these heuristics to fingerprint a project without assuming any specific language or framework. Work top-down: identify the language first, then the framework, then the database, then the architecture.

## 1. Language detection

Look at file extensions and manifest files at the project root (ignore `.git`, `node_modules`, `venv`, `.venv`, `__pycache__`, `dist`, `build`).

| Signal | Language |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, `*.py` files | Python |
| `package.json`, `*.js`/`*.ts`/`*.mjs` files | JavaScript / TypeScript |
| `go.mod`, `*.go` files | Go |
| `pom.xml`, `build.gradle`, `*.java` files | Java |
| `Gemfile`, `*.rb` files | Ruby |
| `composer.json`, `*.php` files | PHP |

If more than one signal is present (e.g. a Python backend with a small JS build script), pick the language of the actual application/API code, not tooling scripts.

## 2. Framework and dependency detection

- **Python:** check `requirements.txt` / `pyproject.toml` for `flask`, `django`, `fastapi`, `sqlalchemy`, `flask-cors`, `flask-sqlalchemy`. Confirm with imports at the top of the entry-point file (`from flask import Flask`, `from fastapi import FastAPI`, ...).
- **Node.js:** check `package.json` `dependencies`/`devDependencies` for `express`, `koa`, `fastify`, `sqlite3`, `pg`, `mongoose`, `sequelize`. Confirm with `require(...)`/`import ... from ...` in the entry-point file.
- Record exact versions from the manifest — they are needed later to check for deprecated APIs (see `anti-patterns-catalog.md`).
- List only dependencies that are actually imported/used somewhere, not the full manifest.

## 3. Database / storage detection

- Look for driver imports/requires: `sqlite3`, `psycopg2`, `pymysql`, `pg`, `mysql2`, `mongoose`.
- Look for ORM usage: `flask_sqlalchemy`, `sequelize`, `prisma`, `typeorm`.
- Look for a schema definition (`CREATE TABLE ...` strings, SQLAlchemy model classes, Mongoose schemas) to enumerate the actual tables/collections — don't guess the domain from the folder name alone.
- Note whether the database is embedded/in-memory (e.g. `:memory:` SQLite, seeded on boot) versus a persisted external database — this affects how Phase 3 validation is performed.

## 4. Domain detection

Infer what the application actually does by reading, in this order:
1. Route/endpoint paths and their handler names (e.g. `/products`, `/orders`, `/checkout`, `/enrollments`).
2. Model/table names and their fields.
3. Any existing README or docstring.

Summarize the domain in one plain sentence (e.g. "E-commerce API — products, users, orders, order items" or "LMS — courses, enrollments, payments, checkout").

## 5. Architecture mapping

Classify the current architecture into one of these buckets:

- **Monolithic / no separation** — most logic lives in 1-4 files; a single file mixes routing, business rules, and raw database access (a God Class/God Module).
- **Partial layering** — folders like `models/`, `routes/`, `services/`, `utils/` already exist, but responsibilities leak across them (e.g. a route computes domain rules directly instead of delegating to a model/service).
- **Layered / MVC-like** — clear separation already exists between routing, business logic, and data access, with little to fix.

To classify correctly:
- Count top-level source files and directories.
- Open the entry-point file and any file that defines routes: does it also contain SQL/query logic and business rules inline? That's a strong God Class/Module signal.
- Check whether a `services/` or similar directory exists but is never imported by any route (dead layer — see the anti-pattern catalog).
- Estimate total lines of code across the files you will analyze (exclude generated/vendor code) for the Phase 1 summary.

## 6. Output

Produce, from the above, everything the Phase 1 summary in `SKILL.md` needs: language, framework + version, key dependencies, domain, one-line architecture classification, number of source files analyzed, and DB tables/collections found. Keep the list of "source files analyzed" — Phase 2 must scan exactly these files (plus anything they import that lives in the project).
