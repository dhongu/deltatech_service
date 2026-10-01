# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## EQUIPMENT-001 — P1: Meter consumption uses the inverse Odoo 19 conversion ratio

- **Status:** Fixed in 19.0.1.1.15 — the conversion now uses `uom.uom._compute_quantity()` (without rounding, as before) from the meter unit to the agreement line unit; when the line has no unit, the product unit is used, since the invoice line falls back to it. Covered by `tests/test_consumption_uom.py` (both directions, line without unit, same unit).
- **Location:** `models/service_agreement.py`, `after_create_consumption()`, lines 164–166.
- **Trigger:** Generate contract consumption from readings whose meter unit differs from the agreement line unit.
- **Actual behavior:** The code divides by the source factor and multiplies by the target factor. Odoo 19 quantity conversion multiplies by the source factor and divides by the target factor.
- **Example:** For a reading difference of 2 dozen and a target unit of one piece, the current formula yields 2 / 12 = 0.1667 pieces instead of 24.
- **Impact:** Incorrect consumption quantities feed contract invoicing.
- **Evidence:** Compared the exact source expressions with local `uom.uom._compute_quantity()` and the Odoo 19 factor definition.
- **Suggested fix:** Use the supported `_compute_quantity()` API with the intended rounding.
- **Validation needed:** Generate consumption with different but related source and target units, in both conversion directions.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. EQUIPMENT-001 was fixed and verified with database-backed tests on 2026-10-01.
