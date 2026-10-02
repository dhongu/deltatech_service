# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## CONSUMABLE-001 — P2: Equipment usage is converted with the old factor convention

- **Status:** Fixed in 19.0.1.1.8 — `get_usage()` now converts with `meter.uom_id._compute_quantity(usage, uom, round=False)` (no rounding to the target unit, so the report keeps the exact figure); covered by `tests/test_efficiency_report.py` (dozen → unit, unit → dozen, same unit). Priority P2 confirmed.
- **Location:** `models/service_efficiency_report.py`, `get_usage()`, lines 125–126.
- **Trigger:** Compute usage when the selected report unit differs from the meter unit.
- **Actual behavior:** The conversion divides by the source factor and multiplies by the target factor, reversing the Odoo 19 quantity conversion.
- **Example:** An isolated execution with 2 dozen of meter usage and a target unit of one piece produced 0.1667 instead of 24.
- **Impact:** Usage and efficiency figures are incorrect for different units of measure.
- **Evidence:** Executed the existing `get_usage()` method with mocked meters and compared the result with the local Odoo 19 conversion formula.
- **Suggested fix:** Delegate conversion to `_compute_quantity()` with the appropriate rounding.
- **Validation needed:** Check related units in both directions and retain the same-unit baseline.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run during the review. CONSUMABLE-001 was fixed on 2026-10-01 with database-backed regression tests.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `9ebc487`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **CONSUMABLE-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## CONSUMABLE-002 — P1: Validating agreement deliveries accesses a removed valuation field

- **Status:** Open; reviewed 2026-10-02.
- **Location:** `models/stock_picking.py`, `button_validate()`.
- **Trigger:** Validate a picking with `agreement_id` set.
- **Actual behavior:** After calling the parent validator, the override reads `picking.move_ids.stock_valuation_layer_ids`. Odoo 19 no longer defines this field on `stock.move`; valuation is represented by the new move-level `value` field.
- **Impact:** Validation raises `AttributeError` and rolls back the transaction instead of completing the delivery and updating contract costs. The reference is also reached when the parent returns a validation wizard.
- **Evidence:** Inspected the override and local Odoo 19 stock/accounting models; no definition of `stock_valuation_layer_ids` exists in the Community, Enterprise or custom addon trees. This module's separate `compute_costs()` already reads move `value`.
- **Suggested fix:** Use the Odoo 19 valuation API, update costs only after successful completion, and avoid double counting on repeated validation.
- **Validation needed:** Agreement delivery validation with immediate completion and wizard paths, returns and repeated calls on completed transfers. No database-backed validation was executed in this pass.
