# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## CONSUMABLE-001 — P2: Equipment usage is converted with the old factor convention

- **Status:** Open.
- **Location:** `models/service_efficiency_report.py`, `get_usage()`, lines 125–126.
- **Trigger:** Compute usage when the selected report unit differs from the meter unit.
- **Actual behavior:** The conversion divides by the source factor and multiplies by the target factor, reversing the Odoo 19 quantity conversion.
- **Example:** An isolated execution with 2 dozen of meter usage and a target unit of one piece produced 0.1667 instead of 24.
- **Impact:** Usage and efficiency figures are incorrect for different units of measure.
- **Evidence:** Executed the existing `get_usage()` method with mocked meters and compared the result with the local Odoo 19 conversion formula.
- **Suggested fix:** Delegate conversion to `_compute_quantity()` with the appropriate rounding.
- **Validation needed:** Check related units in both directions and retain the same-unit baseline.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
