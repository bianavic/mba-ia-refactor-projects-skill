# Audit Report Template (Phase 2)

Run the Phase 2 architecture audit and produce a report for every execution. Save the report to `reports/` and print it to the terminal in the exact format below.

## Report format

Render the Phase 2 output using exactly this structure. Keep the box-drawn headers (`====`) as shown — they make phase boundaries easy to spot in the terminal. This structure applies identically whether it's the project's first Phase 2 report or a re-run.

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

## Report persistence and history

Naming convention:

- First report for a project: `reports/audit-project-<N>.md`
- Re-run for the same project: `reports/audit-project-<N>-part<M>.md`, where `<M>` starts at 2 for the second audit and increments sequentially, continuing the existing numbering rather than starting a new sequence

Example: `reports/audit-project-7.md`, `reports/audit-project-7-part2.md`, `reports/audit-project-7-part3.md`.

Never overwrite an existing report. Each file is an immutable snapshot of one Phase 2 execution, saved regardless of whether it's the first audit or a re-run. Before saving, inspect `reports/` to determine the next available filename.

Handling re-runs: review the previous report(s) first. Confirm resolution of every finding from the previous part before treating it as closed — a finding that reappears, even partially (e.g. a fix that addressed the letter of the recommendation but not its intent), is not new; note it as still open.

Consolidated summary: when a project has more than one part and someone needs a single view for action planning, build a separate deliverable by merging all parts chronologically, marking each finding's status (resolved / still open / duplicate-of-earlier-round), then closing with one deduplicated count of only the currently open, unique findings. This is the number that drives the next Phase 3 run, not the raw sum of findings across every part.

## Execution order

1. Complete the architecture audit.
2. Determine the next available report filename (see "Report persistence and history" above).
3. Save the complete report to that file.
4. Print the complete report to the terminal, exactly as formatted above.
5. Stop. Ask the user the literal question: `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`
6. Wait for an affirmative reply before starting Phase 3. Do not proceed automatically.

## Rules for filling the template

- **Order:** findings must be sorted CRITICAL → HIGH → MEDIUM → LOW. Within the same severity, keep the order you discovered them.
- **File/line:** always a real, verifiable path and line range from the actual project files. If one finding spans multiple locations (e.g. duplicated logic), list every location (`file.py:50-60` + 3 more routes) rather than picking just one.
- **Description vs. Impact:** description is what the code does; impact is why that matters (what an attacker/user/operator experiences as a result). Don't merge them into one vague sentence.
- **Recommendation:** must reference the anti-pattern catalog ID (`AP-xx`) and/or the playbook pattern ID (`RP-xx`) that Phase 3 will apply — this is what lets Phase 3 execute mechanically off the report instead of re-deriving fixes from scratch.
- **Minimum bar:** at least 5 findings total, with at least 1 CRITICAL or HIGH, at least 2 MEDIUM, and at least 2 LOW. If the real count is short in a category, look harder before finalizing — never invent a finding to fill a slot.
- **Final line:** must match the literal template line exactly — `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`.