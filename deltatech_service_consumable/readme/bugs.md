# Identified bugs

Reviewed: 2026-10-01
Target version: Odoo 20.0
Scope: Initial static review. Full database integration tests have not been run.

## [P2] Incorrect usage conversion in the efficiency report

**Status:** Fixed in 20.0.1.1.8 — `get_usage()` now converts with `meter.uom_id._compute_quantity(usage, uom, round=False)` (no rounding to the target unit, so the report keeps the exact figure); covered by `tests/test_efficiency_report.py` (dozen → unit, unit → dozen, same unit). Priority P2 confirmed.

**Location:** `models/service_efficiency_report.py:132–133` (`get_usage()`). Line numbers refer to the reviewed source and may change.

### Cause

Usage is divided by the meter unit factor and multiplied by the report unit factor. This reverses the Odoo 20 conversion formula.

### Impact

The efficiency report receives an incorrect usage value when the selected meter unit differs from the requested usage unit.

### Reproduction

Use a meter with unit factor 12, a requested usage unit with factor 1, and a counter difference of 2. get_usage() computes 0.1667 instead of 24.

### Recommended correction

Replace the manual conversion with from_uom._compute_quantity(usage, to_uom), choosing rounding appropriate to the report.

### Validation

The field units and conversion semantics were checked against the local Odoo 20 core. The actual core UoM conversion method was executed in isolation: 2 units with factor 12 convert to 24 units with factor 1.
