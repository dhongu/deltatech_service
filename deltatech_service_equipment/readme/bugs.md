# Identified bugs

Reviewed: 2026-10-01  
Target version: Odoo 20.0  
Scope: Initial static review. Full database integration tests have not been run.

## [P1] Incorrect unit conversion when generating meter consumption

**Status:** Open — documented, not fixed.

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
