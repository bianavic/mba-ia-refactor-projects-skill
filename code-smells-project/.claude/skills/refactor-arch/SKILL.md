---
name: refactor-arch
description: Audits a backend HTTP API for MVC/SOLID violations, security flaws, deprecated APIs, vulnerable dependency versions, anti-patterns and code smells; writes a severity-ranked report with exact file and line; and, after explicit confirmation, refactors the project into MVC and proves it still works. Use when the user runs /refactor-arch. Not for one-off edits, frontends, or projects without an HTTP backend.
disable-model-invocation: true
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/arch-check.sh *) Bash(bash ${CLAUDE_SKILL_DIR}/scripts/completion-box.sh *)
metadata:
  version: 3.0.0
---

# Refactor Arch

Audit a backend HTTP API, save a ranked report, and — after the user confirms — restructure it into
MVC and prove it still works. Detect the stack at runtime; an unsupported stack or missing tooling
is a reported gap, never a pass.

## Reference files

Load each file only when its phase needs it.

| File | Phase | Contains |
|---|---|---|
| [references/project-analysis.md](references/project-analysis.md) | 1 | Detecting language, framework, database, architecture, files and endpoints |
| [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md) | 2 | Anti-pattern signals and severity; the AP-12 gate |
| [references/audit-report-template.md](references/audit-report-template.md) | 2 | Exact audit report format |
| [references/architecture-guidelines.md](references/architecture-guidelines.md) | 3 | Target MVC layer rules and the placement decision table |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | 3 | Before/after patterns per anti-pattern (RP-xx) |
| [references/refactoring-validation.md](references/refactoring-validation.md) | 3 | `api-test.sh`, `arch-check.sh`, per-finding checks, anti-tautology, validation log, completion evidence, troubleshooting |

Run the bundled scripts, do not read them: `bash ${CLAUDE_SKILL_DIR}/scripts/arch-check.sh <project-dir>` and, at the end of Phase 3, `bash ${CLAUDE_SKILL_DIR}/scripts/completion-box.sh <project-dir>`.

## Severity scale

- **CRITICAL** — breaks correctness or exposes sensitive data (hardcoded credentials, SQL injection, secrets in responses), lets a caller grant themselves a privileged role, or a "God Class" that completely breaks separation of responsibilities (data access, business logic and routing in one place, or routing code running raw SQL past a nominal data layer — see AP-06).
- **HIGH** — strong MVC/SOLID violations that make testing and maintenance very hard (business logic trapped in routes, tight coupling, application-wide mutable state).
- **MEDIUM** — standardization problems, duplication, moderate performance issues (N+1, missing pagination, missing validation), mishandled personal data short of exposing a credential or payment card data.
- **LOW** — readability, naming, scattered magic values.

## Workflow

Run the three phases in order, in one invocation. Copy this checklist into your first message and
tick it as you go:

```
refactor-arch progress:
- [ ] Phase 1: analysis box printed
- [ ] Phase 2: report saved to reports/ (test -s) and printed
- [ ] Phase 2: every open decision answered, plan printed, literal [y/n] asked — answer was y
- [ ] Phase 3: layout table printed before any code
- [ ] Phase 3: every non-left-open plan line applied at every cited location
- [ ] Phase 3: api-test.sh and arch-check.sh exit 0; anti-tautology proven
- [ ] Phase 3: validation log saved; Future improvements in the project README
- [ ] Phase 3: completion box, validation evidence and Future improvements printed
```

### Phase 1 — Analysis

1. Apply `references/project-analysis.md`: language, framework and version, dependencies, database, domain, architecture, source files and lines, endpoint inventory.
2. Check with `command -v` the tooling Phase 3 needs: `bash`, `curl`, a JSON parser (`python3` or `node`), and the database CLI when `check_db` will be used.
3. Print this box — the challenge's fixed template: no field added, removed or reworded:

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

   `Domain:` names what the application is for in the user's terms, not its tech stack. Under the box print `Lines: ~<LOC>`, `Endpoints: <N> — <METHOD /path, ...>` and `Tooling: ok` or `Tooling: missing <tool> — <what it blocks>`.

### Phase 2 — Audit

Modify no file except the report.

1. Scan every Phase 1 source file against every entry of `references/anti-patterns-catalog.md`, and run its draft validation. AP-12 (deprecated APIs and vulnerable versions) is a gate: run it as the catalog prescribes; a `BLOCKED` component (every lookup source failed) is never reported as `clean` — it becomes an open decision (see *Open decisions*).
2. Run `bash ${CLAUDE_SKILL_DIR}/scripts/arch-check.sh <project-dir>` for the AP-06/AP-22/AP-23 leads and confirm each by opening the file; read the code its `note:` lines could not verify.
3. If the first pass looks short, re-read the catalog against the source inventory. Never pad the report with fabricated or trivial findings.
4. Render the report in the exact format of `references/audit-report-template.md`, save it to `<repo root>/reports/audit-project-<N>.md`, and confirm with `test -s` and that its last non-empty line is the literal question: `grep -v '^[[:space:]]*$' <report> | tail -n 1` prints exactly `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`; otherwise fix the file and re-check.
5. Print the report and its path (without the final question line), then the `Checked, no findings` list.
6. Ask every open decision, then print the refactoring plan (see *Open decisions* and *Plan format* below).
7. Only then ask the literal question, word for word:

   ```
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```

   If the user declines or asks for changes, address the feedback and re-present the plan.

#### Open decisions

Ask every finding whose fix changes observable behavior, or has more than one reasonable path:

- **One decision per question.** An option says what it does for *that* finding only; a second decision carried inside it (which other routes stay public, what a default becomes) was not decided by the user.
- **Access rules route by route (RP-16).** Before the auth question, print an access table — every endpoint × `public | authenticated | owner-or-admin | admin` — with the recommendation in each row, and have the user confirm or edit it. No route is public or protected by omission.
- **Every option keeps every endpoint.** Never offer removing an endpoint or making its path answer 404. If only removal would fully fix it, say so in one line, offer the closest variant that keeps the endpoint, and name the remaining risk.
- **Each option states its residual in exact words**: what the endpoint will answer, what happens to data already stored, what stays open. Do not soften or inflate it.
- **Recommend, don't decide.** Recommendation first, then wait.
- **A question, doubt or constraint is not an answer.** Answer it, revise the options to respect it, and ask again. Proceed only on an explicit choice among the options shown.
- **AP-12:** an advisory with no fixed release, or whose only fix crosses a major version, is one question per component — never a silent pin or a skipped component. A `BLOCKED` component is also one question: name the sources that failed and offer (a) retry the lookup now or (b) proceed with it unverified as a `left open` line (`AP-12 <component>@<version> — left open — external lookup unavailable`).

#### Plan format

One line per finding, plus one per route file (below). A finding line gives the change type, the fix (`RP-xx` and the chosen option) or `left open — <reason>`, then its origin.

- **Change type:** `[CONTRACT_CHANGE]` when the fix changes what an endpoint answers — always for RP-09, RP-16, RP-19 and RP-20, and for any other variant that does; `[STRUCTURAL]` when inputs and outputs stay identical.
- **Origin:** `(you chose: "<the option label the user picked>")` or `(no answer change — no decision needed)`. A `[CONTRACT_CHANGE]` line without `you chose` is a plan error: go back and ask.
- **Every cited location:** confirm the fix reaches every `file:line` of the finding's `File:`; a location it will not reach becomes its own line (`<finding> at <file:line> — left open — <reason>`) and an open decision.
- **Every route file** gets a line naming the controller file that will receive its request flow.
- Under the plan, reprint the confirmed access table.

A `y` approves exactly this plan. It also covers what Phase 3 derives from the plan without a new
decision: the files the placement decision table produces from the approved lines (the layout
table) and the validation artifacts (`api-test.sh`, the validation log, *Future improvements*). Any
other file, or any behavior the plan does not name, needs a new question.

### Phase 3 — Refactoring

Start only after `y`.

1. Read `references/architecture-guidelines.md`, `references/refactoring-playbook.md` and `references/refactoring-validation.md`.
2. Design the target layout for the detected stack, adapting to what exists. Print the layout table before writing any code: one row per resulting file, `file → layer → criterion`, the criterion being a row of the placement decision table; an original file split across layers lists where each of its parts went; plus `route file → controller file` for every route file.
3. Apply each approved plan line with the `RP-xx` it names, in the variant chosen in Phase 2.
4. Validate, save the validation log and write *Future improvements* as `references/refactoring-validation.md` prescribes.
5. Run `bash ${CLAUDE_SKILL_DIR}/scripts/completion-box.sh <project-dir>` and paste its output verbatim. The script holds the challenge's fixed template and generates the tree; never retype, omit or reword a line. It prints nothing when a precondition fails — then Phase 3 is not complete. The template it prints:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the resulting directory layout>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

   Then print `## Validation evidence` and `## Future improvements` under the box (`references/refactoring-validation.md` → 8).

## Non-negotiable rules

1. **Detect the stack, don't assume it** — fresh for every project, never what a previous run used.
2. **Evidence over opinion.** Every finding cites a real `file:line`, confirmed by opening the file.
3. **Confirmation gate.** Before the literal `y`, the only file written is the audit report. After it, write only what the approved plan covers (its lines, the layout the placement table derives from them, and the validation artifacts — see *Plan format*); any other file or behavior needs a new question.
4. **Adapt to the starting point.** Reuse what exists and is correct instead of rewriting it.
5. **Preserve the external contract.** Every original endpoint (method + path) still exists and responds. What an endpoint answers changes only to fix a defect, only as the user decided in Phase 2, and no option removes an endpoint. Prove it with `api-test.sh`.
6. **Never report success with known failures.** Boot, `api-test.sh` and `arch-check.sh` must pass; every plan line not marked `left open` is applied in full. A `left open` line is the user's Phase 2 answer, not a failure: it is counted under `## Validation evidence` and does not change the box. The box's `✓ Zero anti-patterns remaining` therefore means every finding is resolved or `left open` by the user; the `Findings:` evidence line printed right under the box gives the counts, so the box is never shown without them.
7. **Decision traceability.** Every answer change traces to a Phase 2 question the user answered. What the skill chose on its own is never attributed to the user. When the user's words conflict with a rule here, the user's words win and the options are rebuilt.
