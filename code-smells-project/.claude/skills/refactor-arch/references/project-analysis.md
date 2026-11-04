# Project Analysis (Phase 1)

Fingerprint the project fresh on every run — including a re-run on a project that already has a
report. Never copy a value from a previous report or assume a stack.

## Contents
- Phase 1 output
- 1. Stack
- 2. Domain detection
- 3. Architecture
- 4. Ambiguous or missing signals
- 5. Source files and lines
- 6. Endpoint inventory

## Phase 1 output

Print this box at the end of Phase 1; each field comes from the section named after it.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <detected language>
Framework:     <detected framework + version>
Dependencies:  <key dependencies>
Domain:        <what this application does>
Architecture:  <current architectural state, one line>
Source files:  <N> files analyzed
DB tables:     <tables/collections found, if any>
================================
```

This is the challenge's fixed template, the same as in `SKILL.md`. How to fill each field:
- `Language`: the language and its runtime version. `Framework`: the framework and its version.
  `Dependencies`: imported dependencies other than the framework, comma-separated. `DB tables`:
  the tables and where they live (`file`, `external server` or `in-memory`). All from section 1.
- `Domain`: `<Domain> API (<resource>, <resource>, …)`, from section 2.
- `Architecture`: `<bucket> — <one clause on the deviation>`, from section 3.
- `Source files`: the file count from section 5. The line count goes in `Lines:`, under the box.

## 1. Stack

- **Language, framework, database:** from the manifests (`requirements.txt`, `pyproject.toml`,
  `package.json`, `go.mod`, `pom.xml`…) confirmed against the imports of the application code —
  the entry point and the modules it loads (the database driver usually lives in a data-access
  module, not in the entry point). A manifest entry alone is not enough. When signals conflict
  (test fixtures, dev-only tooling), the application code wins. Record each conclusion as
  `detected`, `confirmed` or `unverified`, with the file and line that supports it.
- **Versions:** record the exact version of the runtime and of every dependency actually imported
  (the pin, or the lockfile/installed version when the manifest gives a range or nothing — say
  which). Runtime: the project's pin (`.python-version`, `.nvmrc`, `engines`, `go` directive…) or,
  when there is none, the installed interpreter (`python3 --version`, `node --version`) — say
  which. Phase 2 checks these versions (AP-12). List only what the code imports, not the whole
  manifest.
- **Storage:** enumerate tables/collections from the schema (`CREATE TABLE`, ORM models, Mongoose
  schemas), and note whether the database is a file, an external server or in-memory (seeded on
  boot) — Phase 3 validation depends on it.

## 2. Domain detection

Read route paths and handler names, then model/table names, then any README. Summarize in the
user's terms in one line (`<Domain> API (<resource>, <resource>, …)`), never the tech stack.

## 3. Architecture

Classify into the closest bucket, adding one clause for any deviation:
- **Monolithic** — one file/class mixes routing, business rules and raw data access (a God
  Class/Module), or the code is split only by file at the project root, with no layer directories,
  while responsibilities still mix (routes or controllers running queries, rules beside data access).
- **Partial layering** — `models/`, `routes/`, `services/`… exist but responsibilities leak across
  them (a route runs queries, a `services/` module nothing imports).
- **Layered / MVC-like** — separation already holds; little to fix.

Open the entry point and every file that declares routes: inline SQL/ORM calls and business rules
there are the deciding signal, not the file count.

Also record, for Phase 2 and the Phase 3 layout table: the source files at the project root and the
role each plays (entry point, config, auth, errors, security, database, layer file), and which
layer directories already exist (`routes/`, `controllers/`, `services/`, `models/`, `middleware/`
or `middlewares/`, `utils/`, …), keeping the name the project uses.

## 4. Ambiguous or missing signals

Phase 1 has no confirmation gate — resolve these yourself and keep going:
- No recognizable language: check shebangs, Dockerfile `FROM`, CI config; otherwise write
  `undetermined — <why>`.
- Framework not recognized: record the import verbatim, or `no framework — stdlib HTTP server`.
- No domain evidence: say so in `Domain:` instead of inferring from the folder name.

## 5. Source files and lines

The count comes from a reproducible command, so the `Source files:` and `Lines:` lines of Phase 1 and the
`Files:` line of the report header carry the same two numbers (file count and line count):

```bash
git ls-files --cached --others --exclude-standard -- \
  '*.py' '*.js' '*.mjs' '*.ts' '*.go' '*.java' '*.kt' '*.rb' '*.php' '*.cs' \
  | <drop non-application files> | xargs wc -l
```

Drop tests, migrations, virtual envs, `node_modules`, `dist`/`build`, generated files and
`.claude/`; say what you dropped. Application code stays even when nothing imports it (an unused
service, a seed script): unimported code is itself the AP-11 signal, and a seed can hold AP-02
credentials. Outside git, use `find ... -print0` with the same exclusions and a null-safe line
counter. Report `<N>` exactly and `~<LOC>` as the `wc -l` total rounded to the nearest 10
(780 → `~780`). Phase 2 scans exactly this list.

## 6. Endpoint inventory

List every endpoint as `METHOD /path`, read from the framework's route declarations (decorators,
`add_url_rule`, `app.get`/`router.post`, `urlpatterns`…):
- one entry per method when a route accepts several;
- the path as declared, with its parameters (`/<resource>/<int:id>`, `/<resource>/:id`);
- prefixes applied at registration (`url_prefix=`, `app.use('/api', router)`) included.

The inventory feeds the domain summary, the Phase 2 security review (which routes mutate data or
look administrative) and the coverage line of `api-test.sh` in Phase 3.
