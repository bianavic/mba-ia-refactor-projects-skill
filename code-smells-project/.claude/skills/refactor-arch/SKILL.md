---
name: refactor-arch
description: Audits any backend codebase for MVC/SOLID architecture violations, security flaws, and code smells, then refactors it into a clean MVC structure. Use when asked to analyze, audit, or refactor a project's architecture — technology-agnostic, works with Python/Flask, Node.js/Express, or any other backend stack.
---

# Refactor Arch

Automated architectural audit and refactoring for legacy backend projects. This skill inspects a codebase, classifies its problems by severity, produces an audit report, and — once the user confirms — restructures the project into MVC (Model-View-Controller) without breaking it.

The skill is technology-agnostic: it must work correctly on any language/framework by detecting the stack at runtime rather than assuming Python, Flask, Node.js, or any specific tooling.

## Reference files

Load these on demand, only when the current phase needs them — do not read all of them upfront.

| File | Load during | Contains |
|---|---|---|
| [references/project-analysis.md](references/project-analysis.md) | Phase 1 | Heuristics to detect language, framework, database, and current architecture |
| [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Phase 2 | Anti-pattern signals, severity classification, deprecated API detection |
| [references/audit-report-template.md](references/audit-report-template.md) | Phase 2 | Exact audit report format to produce |
| [references/architecture-guidelines.md](references/architecture-guidelines.md) | Phase 3 | Target MVC layer rules and responsibilities |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | Phase 3 | Before/after transformation patterns per anti-pattern |

## Severity scale

Used to classify every finding in Phase 2. Full detection signals per severity live in `references/anti-patterns-catalog.md`.

- **CRITICAL** — severe architecture or security failures that break correctness or expose sensitive data (hardcoded credentials, SQL injection, secrets leaked via API responses) or fully violate separation of concerns (a "God Class" holding database access, business logic, and routing together).
- **HIGH** — strong MVC/SOLID violations that make testing and maintenance very hard (heavy business logic trapped in controllers/routes, tight coupling without dependency injection, mutable global state used application-wide).
- **MEDIUM** — standardization problems, duplicated code, or moderate performance bottlenecks (N+1 queries, missing pagination, misused middleware, missing route validation).
- **LOW** — readability improvements, poor naming, or magic numbers/values scattered through the code.

## Workflow

Run the three phases below **in order**, in a single invocation, pausing only where instructed. Never skip the confirmation gate between Phase 2 and Phase 3.

### Phase 1 — Analysis

Goal: understand the codebase before judging it.

1. Read `references/project-analysis.md` and apply its heuristics to this project.
2. Detect: primary language, framework(s) and version, dependencies, database/storage technology, application domain (what the API is for), and current architecture (monolithic single file, partial layering, etc.).
3. Count and list the source files you analyzed (exclude tests, migrations, virtual envs, `node_modules`, `.git`, and other generated/vendor directories).
4. Print a summary in this exact shape before moving on:

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

### Phase 2 — Audit

Goal: cross-reference the code against the anti-pattern catalog and produce a report — never modify files in this phase.

1. Read `references/anti-patterns-catalog.md` and `references/audit-report-template.md`.
2. Systematically scan every source file identified in Phase 1 for each cataloged anti-pattern, including deprecated/obsolete API usage.
3. For every finding, record: severity, a short title, exact file path and line number(s), a description, and its concrete impact. Do not report a finding without a real file/line reference — re-check the file if you are unsure.
4. Find at least 5 findings total, including at least 1 CRITICAL or HIGH, at least 2 MEDIUM, and at least 2 LOW. If the codebase does not surface enough on the first pass, look again before concluding there is nothing else — do not pad the report with fabricated or trivial findings to hit the count.
5. Sort findings by severity (CRITICAL → HIGH → MEDIUM → LOW) and render the report using the exact structure in `references/audit-report-template.md`.
6. Print the full report, then **stop and explicitly ask the user to confirm before proceeding to Phase 3**. Do not touch any file until the user responds affirmatively (e.g. "y", "yes", "proceed"). If the user declines or asks for changes, address their feedback and re-present the report instead of continuing.

### Phase 3 — Refactoring

Goal: restructure the project into MVC and prove it still works. Only start after explicit user confirmation from Phase 2.

1. Read `references/architecture-guidelines.md` and `references/refactoring-playbook.md`.
2. Design a target MVC directory layout appropriate for the detected stack (see architecture guidelines) — adapt to what already exists rather than forcing a generic template. A project with partial layering (e.g. existing `models/`, `routes/` folders) needs targeted fixes, not a full rebuild from scratch.
3. Apply the transformation pattern from the playbook that matches each confirmed finding: extract configuration out of hardcoded values, split God Classes into Models/Controllers, parameterize SQL queries, centralize error handling, deduplicate business logic into shared model/service methods, add pagination, replace `print`/`console.log` with structured logging, etc.
4. Keep all original endpoints and behavior intact — this is a structural refactor, not a feature change.
5. Validate the result:
   - The application boots without errors.
   - Every original endpoint still responds (exercise them, e.g. with `curl` or the project's existing HTTP client file).
   - Re-check the codebase against the catalog to confirm the confirmed findings are resolved.
6. Print a completion summary in this exact shape:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the resulting directory layout>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ <N> anti-patterns resolved
================================
```

## Non-negotiable rules

- Never modify, delete, or move a file before the user has confirmed the Phase 2 report.
- Every finding must cite a real file and line range — verify by reading the file, never guess.
- Do not assume Python/Flask: detect the stack fresh for every project this skill runs against.
- Preserve existing functionality; refactoring must not change observable behavior or break any endpoint.
- If Phase 3 validation fails (boot error or broken endpoint), fix the regression before reporting completion — do not report success with known failures.
