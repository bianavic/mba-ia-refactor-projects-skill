```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project (Loja API)
Stack:   Python / Flask 3.1.1
Files:   16 analyzed | ~962 lines of code

Manual, targeted re-audit — not a full from-scratch Phase 1-3 skill run. Triggered by writing
`code-smells-project/api-tests.http` (manual endpoint coverage for all routes) and hitting two
behavior bugs its edge-case/sad-path sections were designed to surface, neither of which
`manual-tests.sh` exercises and neither of which appears in `audit-project-1.md`, `-part2.md`,
or `-part3.md`. Round 3's Phase 3 (commit `83bfaa3`) and its validation
(`evidence/logs/code-smells-project-round3-validation.txt`) are not in question here — nothing
below revisits or contradicts them; these are two new findings in code untouched by round 3.

The 2 findings below undershoot the template's 5-finding minimum bar for a first-time Phase 2
pass. Per the template's own rule ("never invent a finding to fill a slot"), no filler was
added — this is a narrow, test-driven re-audit of two specific behaviors, not a full re-scan of
the project.

## Summary
CRITICAL: 0 | HIGH: 1 | MEDIUM: 1 | LOW: 0

## Findings

### [HIGH] Order Status Update Reports Success for Non-Existent Orders
File: models/order_model.py:102-107 (atualizar_status); controllers/order_controller.py:62-79
Description: `atualizar_status()` runs `UPDATE pedidos SET status = ? WHERE id = ?` and
unconditionally returns `True` — it never inspects `cursor.rowcount` (or re-selects the row) to
confirm a row actually matched. `order_controller.atualizar_status` always responds
`{"sucesso": True, "mensagem": "Status atualizado"}`, 200, regardless.
Impact: `PUT /pedidos/99999/status` reports the update as successful when zero rows were
touched — a client cannot distinguish "status changed" from "no such order." The two
unconditional log lines right after the call ("Preparar envio" / "Devolver estoque") fire even
when nothing was updated, so anything downstream that trusts those logs acts on an order that
was never touched. This is the same class of bug flagged HIGH in `ecommerce-api-legacy`'s round
3 (`audit-project-2-part3.md`, "Cascade delete swallows errors") — a mutation that never checks
whether it actually mutated anything.
Recommendation: check `cursor.rowcount` after the `UPDATE` (or `SELECT` the order first) and
have `atualizar_status()` return whether a row was affected; `order_controller.atualizar_status`
should translate a no-op into 404. No AP-xx in the current catalog covers "mutation success
reported without checking whether a row matched" precisely — `audit-project-2-part3.md` cited
AP-06 for the equivalent bug in `ecommerce-api-legacy`, but AP-06 is about duplicated logic, not
this. Same catalog gap noted in `audit-project-2-part4.md`'s follow-up note; not force-fitting
an AP-xx here either.
Status: New — never raised in `audit-project-1.md`, `-part2.md`, or `-part3.md`; found by
writing `api-tests.http`'s sad-path case for `PUT /pedidos/<id>/status` on a non-existent order,
not by re-reading the source.

### [MEDIUM] Non-Numeric Pagination/Filter Parameters Crash with 500 Instead of 400
File: utils/pagination.py:7-8 (parse_pagination, root cause); called from
controllers/product_controller.py:13 (listar) and :108 (buscar),
controllers/order_controller.py:46 (listar_por_usuario) and :55 (listar_todos),
controllers/user_controller.py:13 (listar); also controllers/product_controller.py:110-113
(`preco_min`/`preco_max` `float()` conversion inside `buscar`)
Description: `parse_pagination()` calls `int(request.args.get("page", DEFAULT_PAGE))` /
`int(request.args.get("per_page", DEFAULT_PER_PAGE))` with no `try/except`; `buscar()` does the
same with `float(preco_min)`/`float(preco_max)`. A non-numeric value (`?page=abc`,
`?preco_min=abc`) raises `ValueError`, which the generic `except Exception as e: return
jsonify({"erro": str(e)}), 500` wrapping every one of these five handlers turns into a 500 with
the raw Python exception message in the response body, instead of a 400 telling the caller the
parameter is malformed.
Impact: a client typo in a query parameter is reported as a server error, not a client error —
the wrong half of the 4xx/5xx contract — and the response leaks an internal exception string
(`invalid literal for int() with base 10: 'abc'`) to the caller. Affects every paginated or
price-filterable endpoint in the project: product listing/search, order listing (both the
all-orders and per-user variants), and user listing.
Recommendation: validate/convert `page`, `per_page`, `preco_min`, `preco_max` explicitly (e.g. a
guarded conversion inside `parse_pagination()` and in `buscar()`) and return 400 with a clear
message on failure, instead of letting the conversion exception fall through to the generic
`except Exception` handler. No current AP-xx covers "unvalidated type coercion surfaces as
500" — AP-09 is about pagination being absent, a different problem: this project already
paginates, it just doesn't validate the parameters it parses.
Status: New — never raised in `audit-project-1.md`, `-part2.md`, or `-part3.md`; found via
`api-tests.http`'s edge-case section, not by re-reading the source.

================================
Total: 2 findings
================================

Follow-up (not part of the Phase 2 output format, kept here since it motivated this report):
this is the second report in a row (after `audit-project-2-part4.md`'s missing-auth finding) to
hit a real bug with no matching catalog entry. Two more candidate gaps, not yet added to
`references/anti-patterns-catalog.md`/`refactoring-playbook.md` in any of the three project
copies: (1) a mutation (UPDATE/DELETE) that never checks whether it affected a row and reports
success anyway, and (2) request-parameter type coercion (`int()`/`float()` on query params) with
no guard, surfacing as 500 instead of 400. Both were found by writing exhaustive `.http` test
files, not by re-reading source against the existing catalog — the same mechanism gap AP-16 and
AP-17 were added to close. Not adding AP-18/AP-19 in this report; left for a deliberate catalog
update, same as AP-17 was.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
