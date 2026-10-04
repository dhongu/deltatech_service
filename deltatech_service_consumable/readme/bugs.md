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

## [P1] CONSUMABLE-002 — Validating agreement deliveries counted the cost before completion or twice

**Status:** Fixed in 20.0.1.1.9 — `button_validate()` adds `stock.move._get_service_signed_value()` (from `deltatech_service_equipment` 20.0.1.1.16: the signed `stock.move.value` of the done moves, negative for outgoing and positive for incoming moves, as expected by `compute_percent()`) only for the pickings completed by the call, so the backorder wizard path counts after completion and a repeated call on a done transfer adds nothing. `compute_costs()` uses the same helper. Covered by `tests/test_delivery_costs.py` (direct validation, repeated validation, backorder wizard, recompute equal to the accumulated cost). Port of the 19.0 fix (dhongu/deltatech_service#104).

**Location:** `models/stock_picking.py`, `button_validate()`; `models/service_agreement.py`, `compute_costs()`.

### Cause

On 19.0 the override read the removed `stock_valuation_layer_ids` field (`AttributeError`); the 20.0 migration had already replaced it with `stock.move.value`. On both versions the cost was added for every picking in `self`, also when `super().button_validate()` returned a wizard (picking not done yet) or the picking was already done.

### Impact

A backorder wizard or a repeated validation added the cost of a transfer to the agreement before completion or more than once, distorting `compute_percent()`.
