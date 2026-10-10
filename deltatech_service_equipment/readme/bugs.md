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

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `9ebc487`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **EQUIPMENT-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## EQUIPMENT-002 — P1: Equipment cost refresh still uses the removed stock valuation layer field

- **Status:** Fixed in 19.0.1.1.16 — `compute_totals()` reads the cost with the new `stock.move._get_service_signed_value()` (`models/stock_move.py`): `stock.move.value` of the done moves, negative for outgoing and positive for incoming (returns), i.e. the sign of the former valuation layers; non-valued moves count as zero. The picking search runs only when `stock.picking.equipment_id` exists (it is added by `deltatech_service_consumable`), so the refresh no longer fails on an invalid field without that module. Reproduced before the fix (`AttributeError`). Covered by tests in `tests/test_cost_refresh.py` (delivery/return signs, no deliveries, several deliveries) and, for the delivery-validation caller, `deltatech_service_consumable/tests/test_delivery_costs.py`.
- **Location:** models/service_equipment.py, compute_totals().
- **Trigger:** Refresh costs with a service picking type configured, including delivery validation that calls compute_totals().
- **Actual behavior:** The method maps move_ids.stock_valuation_layer_ids.value, but Odoo 19 stock.move has no stock_valuation_layer_ids field.
- **Impact:** Cost refresh fails and callers that run it within delivery validation roll back their transaction.
- **Evidence:** Inspected the method and local Community/Enterprise/custom definitions; no field definition remains. Odoo 19 defines value on stock.move instead. Source verification only.
- **Suggested fix:** Use the supported Odoo 19 move valuation API and verify outgoing/return signs.
- **Validation needed:** Cost refresh with zero and several deliveries, returns, and delivery-validation callers.

## EQUIPMENT-003 — P2: Batch meter creation carries categories from previous equipment

- **Status:** Open; reviewed 2026-10-02.
- **Location:** `models/service_equipment.py`, `create_meters_button()`.
- **Trigger:** Call meter creation for two equipment records with different meter templates.
- **Actual behavior:** The `categs` accumulator is initialized outside the equipment loop, so each later equipment receives the categories gathered for earlier equipment too.
- **Impact:** Extra meters are created for equipment whose type never requested them; uniqueness conflicts can roll back a larger batch.
- **Evidence:** Executed the actual extracted method with recordset union and creation spies. Equipment 1 requested category 1, equipment 2 category 2; equipment 2 received both categories 1 and 2. No database-backed batch execution.
- **Suggested fix:** Collect categories independently per equipment, and define repeat-call handling for existing meters.
- **Validation needed:** Batch of different and identical templates, existing meters, and single-record baseline.

## EQUIPMENT-004 — P2: Automatic billing skips agreements without meters unless *Readings done* is ticked

- **Status:** Fixed in 19.0.1.1.19. `get_agreements_auto_billing()` filters on `not type_id.readings_required or meter_reading_status`, the rule of the manual preparation.
- **Location:** `models/service_agreement.py`, `get_agreements_auto_billing()`.
- **Trigger:** With `deltatech_service_equipment` installed, an agreement whose type does not require meter readings is due for automatic billing.
- **Actual behavior / impact:** The override removes every agreement without `meter_reading_status`, whatever its type; the manual billing preparation checks readings only when the agreement type requires them. Agreements without meters are not billed automatically until someone ticks *Readings done*.
- **Suggested fix:** Filter only agreements whose type requires readings (same rule as the manual preparation), with a test for both cases.

## EQUIPMENT-005 — P2: *Readings done* is never cleared, so later periods are billed on old readings

- **Status:** Fixed in 19.0.1.1.19. `service.billing.do_billing()` clears `meter_reading_status` on the billed agreements whose type requires readings.
- **Location:** `models/service_agreement.py` (`meter_reading_status`), billing wizard.
- **Trigger:** Tick *Readings done* on an agreement whose type requires readings, bill it, wait for the next period.
- **Actual behavior / impact:** Nothing reset the flag after billing, so the automatic billing (and the manual preparation check) kept accepting the agreement in the following periods without new readings.
- **Suggested fix:** Clear the flag once the agreement is billed.

