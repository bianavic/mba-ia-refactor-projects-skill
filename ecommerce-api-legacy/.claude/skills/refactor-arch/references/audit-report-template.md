# Audit Report Template (Phase 2)

## Contents
- Where the report is saved
- Report format (fixed)
- Checked, no findings (printed after the report)
- The data-protection lens
- Re-runs

## Where the report is saved

`<repo root>/reports/audit-project-<N>.md`, with the repo root from `git rev-parse --show-toplevel`
— never a project-local `reports/`. `<N>` is fixed by the challenge, not by run order:
`1` = `code-smells-project`, `2` = `ecommerce-api-legacy`, `3` = `task-manager-api`. For any other
project, read the `Project:` line of every existing report and take the next free number. If this
project already has a report, that file is updated instead (see "Re-runs").

## Report format (fixed)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project name>
Stack:   <language + framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <Short title>
File: <relative/path.ext>:<line>-<line>
Description: <one or two sentences on what the code actually does wrong>
Impact: <concrete consequence — what breaks, what leaks, what degrades>
Recommendation: <one line pointing at the fix; name the refactoring-playbook pattern id, e.g. "See RP-01">

### [<SEVERITY>] <Short title>
File: ...
Description: ...
Impact: ...
Recommendation: ...

[... one block per finding ...]

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- The headers, section names and the per-finding fields never change — not for a new
  severity, a new category, or between runs — so a report can be diffed against its previous version.
- `Files:` carries the same two numbers as Phase 1 (file count and line count).
- `File:` lists every location a finding spans (`a.py:50-60, b.py:12`), never just the first.
- Findings sorted CRITICAL → HIGH → MEDIUM → LOW; discovery order within a severity.
- `Recommendation:` names the `AP-xx` and/or `RP-xx`.
- The saved file ends with the literal question line; in the terminal it is asked only after the
  refactoring plan.

## Checked, no findings (printed after the report)

Not part of the report, but mandatory: without it "checked and clean" and "never checked" read the
same. One line per catalog entry scanned without a finding, plus always one `AP-12:` line per
component — also when AP-12 produced a finding — for the runtime, the framework and every imported
dependency. Also one
`Absent:` line answering each absent-requirement question of the catalog
(`deleted: yes — <file:line> | no — reported AP-xx | n/a — <why>`):

```
AP-12: <component>@<version> | <not applicable|clean|finding|BLOCKED> | <latest release; advisories <n> or none; support/EOL status; deprecated calls found> | <source URL or command> | <YYYY-MM-DD>
```

One component per line, fields separated by ` | `, so the lines can be counted and checked with
`grep '^AP-12:'`. Illustrative shape only (a fictitious package — every value comes from the lookup):
`AP-12: example-lib@1.2.0 | finding | latest 1.4.1; advisories 1 (fixed in 1.3.2); supported;
no deprecated calls | pip-audit; <registry URL> | <YYYY-MM-DD>`. A lookup that could
not run is `BLOCKED`, with the failed sources in the detail field — never `clean`.

## The data-protection lens

Not a field — a question for `Impact:` and `Recommendation:` when a finding touches **personal
data** (name, email, national ID, phone, address, birth date, an IP or behavioural data tied to a
person — LGPD art. 5 I / GDPR art. 4) or **payment card data** (PCI-DSS):
- `Impact:` says who can read the data and for how long, not only what an attacker could do.
- `Recommendation:` also answers what happens to data already written, and on erasure (RP-17, RP-18).

The lens never changes severity by itself, and most findings (N+1, dead layers, naming) have no
regime — do not stretch one to fit.

## Re-runs

The same file for every Phase 2 run on a project — never a `-partM` file, never a rename:
1. Read the existing report, then re-audit the project fully.
2. Keep every finding still open, unchanged, in place — including one fixed only partially.
3. Drop findings Phase 3 has fixed (a fixed finding is removed, not marked resolved).
4. Insert new findings at their severity position, never appended at the end.
5. Recompute `## Summary` and `Total:` and save over the same file.

An error unrelated to a re-run (wrong count, typo) is fixed directly in the file.
