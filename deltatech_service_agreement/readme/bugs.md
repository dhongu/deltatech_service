# Identified bugs

Reviewed: 2026-10-01

Target version: Odoo 20.0

Scope: Source review and real ORM reproductions in a separate audit database; outbound HTTP was mocked.

## [P1] Adding distributed value discards the original quantity contribution

**Status:** Open — documented, not fixed.

**Location:** `wizard/service_distribution.py:74–84`. Line numbers refer to the reviewed source.

### Cause

In value mode with add_values enabled, the allocated value is added to cons.price_unit and quantity is reset to 1. The previous quantity times price_unit is not preserved.

### Impact

Adding a positive amount can reduce the consumption value to be billed instead of increasing it.

### Reproduction

Create one consumption with quantity 3 and price 10: total 30. Distribute amount 5 in value mode with add_values=True. The result is quantity 1, price 15, total 15 instead of 35.

### Recommended correction

Preserve the original line value when allocating an additional amount. If quantity is intentionally normalized to 1, use old quantity times old unit price plus the allocation; otherwise adjust unit price using the preserved quantity.

### Validation

Confirmed with real service.consumption and service.distribution records: actual total 15, expected 35. Audit records were rolled back.

## [P2] Appending a reference fails when the existing reference is empty

**Status:** Open — documented, not fixed.

**Location:** `wizard/service_distribution.py:79–84; models/service_consumption.py:13`. Line numbers refer to the reviewed source.

### Cause

Consumption name is an optional Char and can be False. When the wizard reference is nonempty, the code evaluates cons.name + self.reference without normalizing the missing value.

### Impact

Value distribution fails with an uncaught TypeError for an otherwise valid consumption, preventing the operation.

### Reproduction

Leave the consumption reference empty, enter Extra in the distribution wizard reference, and apply value distribution with add_values enabled.

### Recommended correction

Normalize the existing reference to an empty string before concatenating and define a separator policy for nonempty references.

### Validation

Confirmed with real ORM records: the method raised TypeError, unsupported operand types bool and str. Audit records were rolled back.

## [P1] AGREEMENT-001 — Service billing converts prices into the user default company currency

**Status:** Fixed in 20.0.2.0.13 — `do_billing_step1()` converts into the invoice currency (journal currency, otherwise billing company currency) with the billing company rates; the invoice currency is set explicitly; income account and taxes are taken for the billing company; consumptions of another company are rejected; `_compute_revenues()` converts into the consumption company currency (post-migration `migrations/20.0.2.0.13` recomputes stored revenues). Covered by `tests/test_agreement_multicompany.py` (other company in EUR, EUR journal in a USD company, cross-company rejection). Port of the 19.0 fix (dhongu/deltatech_service#106).

**Location:** `wizard/service_billing.py`, `do_billing_step1()`; `models/service_consumption.py`, `_compute_revenues()`.

### Impact

A user with default company A (RON) billing a EUR 100 consumption of company B (EUR) got a 500 line on the EUR invoice; stored revenues mixed company currencies.

## [P1] AGREEMENT-006 — Contract lines bypass the parent agreement company rules

**Status:** Fixed in 20.0.2.0.13 — global multi-company row `service_agreement_line_comp_rule` on `service.agreement.line` in `security/ir.access.csv` (on 19.0 an `ir.rule`); `create()` and `write()` with `agreement_id` require write access on the target agreement. Covered by `tests/test_agreement_multicompany.py` (search, read, write, create and reassignment across companies). Port of the 19.0 fix (dhongu/deltatech_service#106).

**Location:** `security/ir.access.csv`; `models/service_agreement.py`, `ServiceAgreementLine`.

### Impact

All internal users could read, and service users could modify, lines of agreements belonging to companies they are not allowed in.

## [P1] AGREEMENT-008 — Previously opened billing wizards can invoice the same consumption twice

**Status:** Open — reported on 19.0 (2026-10-03, dhongu/deltatech_service#106); the same code is present on 20.0.

**Location:** `wizard/service_billing.py`, `default_get()`, `do_billing_step1()`, `do_billing()`.

### Cause

Draft-state selection happens only in `default_get()`. Billing neither rejects nor skips consumptions that already have `invoice_id` or state `done`: it prepares the lines again, creates another invoice and replaces the consumption invoice reference.

### Recommended correction

Revalidate the selected consumptions at execution time and lock them so concurrent billing attempts cannot both pass; keep invoice references intact on rejection.

## [P1] AGREEMENT-009 — Negative service corrections are silently clipped and billed quantities disagree

**Status:** Open — reported on 19.0 (2026-10-03, dhongu/deltatech_service#106); the same code is present on 20.0.

**Location:** `wizard/service_billing.py`, `add_invoice_line()`, `do_billing_step1()`, `do_billing()` (negative-line loop).

### Cause

Each negative line is capped against the sum of positive quantities of the current invoice: a lone quantity -2 becomes 0, and with grouping disabled 3, -5, -5 become 3, -3, -3. The consumption is still marked done and `invoiced_qty` is recorded before clipping (and subtracts the free allowance from negative corrections).

### Recommended correction

Define correction/refund behaviour explicitly (error or credit note for net-negative invoices) and compute `invoiced_qty` from the final allocated invoice quantities.

## Existing test suite

The selected IAP server, line-counter and service-agreement suites ran together on 2026-10-01 in test20_bug_audit_20261001: 35 tests completed with zero failures and zero errors. The additional reproductions above demonstrate cases outside those assertions. All reproduction records were rolled back.
