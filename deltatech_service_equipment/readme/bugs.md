# Identified bugs

Reviewed: 2026-10-01
Target version: Odoo 20.0
Scope: Initial static review. Full database integration tests have not been run.

## [P1] Incorrect unit conversion when generating meter consumption

**Status:** Fixed in 20.0.1.1.15 — the conversion now uses `uom.uom._compute_quantity()` (without rounding, as before) from the meter unit to the agreement line unit; when the line has no unit, the product unit is used, since the invoice line falls back to it. Covered by `tests/test_consumption_uom.py` (both directions, line without unit, same unit).

**Location:** `models/service_agreement.py:164–166` (`after_create_consumption()`). Line numbers refer to the reviewed source and may change.

### Cause

The conversion divides by the source unit factor and multiplies by the destination factor. Odoo 20 uses the opposite formula: quantity * source.factor / destination.factor.

### Impact

When the meter and agreement line use different units, the generated consumption quantity is incorrect and can produce an incorrect invoice.

### Reproduction

Use a meter unit with factor 12 and an agreement unit with factor 1. Generate consumption for a reading difference of 2. The current formula returns 0.1667 instead of 24.

### Recommended correction

Replace the manual factor calculation with from_uom._compute_quantity(reading.difference, to_uom), choosing rounding appropriate to consumption billing.

### Validation

The field units and conversion semantics were checked against the local Odoo 20 core. The actual core UoM conversion method was executed in isolation: 2 units with factor 12 convert to 24 units with factor 1.
