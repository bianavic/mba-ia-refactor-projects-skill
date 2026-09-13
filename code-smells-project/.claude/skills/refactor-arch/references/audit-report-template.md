# Audit Report Template (Phase 2)

Render the Phase 2 output using exactly this structure. Keep the box-drawn headers (`====`) as shown — they make phase boundaries easy to spot in the terminal.

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

## Rules for filling the template

- **Order:** findings must be sorted CRITICAL → HIGH → MEDIUM → LOW. Within the same severity, keep the order you discovered them.
- **File/line:** always a real, verifiable path and line range from the actual project files. If one finding spans multiple locations (e.g. duplicated logic), list every location (`file.py:50-60` + 3 more routes) rather than picking just one.
- **Description vs. Impact:** description is what the code does; impact is why that matters (what an attacker/user/operator experiences as a result). Don't merge them into one vague sentence.
- **Recommendation:** must reference the anti-pattern catalog ID (`AP-xx`) and/or the playbook pattern ID (`RP-xx`) that Phase 3 will apply — this is what lets Phase 3 execute mechanically off the report instead of re-deriving fixes from scratch.
- **Minimum bar:** at least 5 findings total, with at least 1 CRITICAL or HIGH, at least 2 MEDIUM, and at least 2 LOW. If the real count is short in a category, look harder before finalizing — never invent a finding to fill a slot.
- **The final line is mandatory and literal.** After printing the report, stop. Do not proceed to Phase 3 until the user responds affirmatively in a follow-up message.
