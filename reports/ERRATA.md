# Errata — audit reports

Corrections to already-committed audit reports. The reports themselves are **never edited**:
each one is the frozen evidence of the "before" state of its round, and the repository's own
evidence gate (`scripts/sync-docs.sh --check`) treats a modified report as a new audit that
requires a fresh validation capture with the application running. Corrections therefore land
here, and every one of them says exactly what is wrong and what the right value is.

Nothing on this page changes a finding. Only counts are corrected.

## 2026-09-20 — round-1 finding counts in projects 1 and 3

Found during a release-coherence audit of the whole deliverable (no skill run, no code change).
Two round-1 reports declare a `LOW` count and a `Total` that do not match the findings written
out in the report itself. The missing finding is not missing from the audit — it was never
written, and the two counts were never reconciled with the rendered blocks.

| Report | Declared | Actually rendered | Correct value |
|---|---|---|---|
| [`audit-project-1.md`](audit-project-1.md) | `LOW: 4` · `Total: 13 findings` | 3 LOW blocks · 12 finding blocks | `LOW: 3` · `Total: 12 findings` |
| [`audit-project-3.md`](audit-project-3.md) | `LOW: 4` · `Total: 14 findings` | 3 LOW blocks · 13 finding blocks | `LOW: 3` · `Total: 13 findings` |

The CRITICAL, HIGH and MEDIUM counts in both reports are correct, and so is every finding they
contain. [`audit-project-2.md`](audit-project-2.md) has no discrepancy: 12 declared, 12
rendered.

How to verify: `grep -c '^### \[' reports/audit-project-1.md` returns 12, and
`grep -c '^### \[LOW\]' reports/audit-project-1.md` returns 3.

Everywhere these totals are quoted outside `reports/` — the README's round-by-round narrative
and `docs/results.md` — the corrected values are used.
