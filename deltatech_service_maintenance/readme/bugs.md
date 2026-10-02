# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SERVICE-001 — P1: Delivery actions do not populate their stock moves

- **Status:** Fixed in 19.0.1.2.4. The three delivery actions now pass the lines as `default_move_ids` and no longer send `name`; the picking description is computed from the product by Odoo. Covered by `tests/test_delivery.py` (one test per source document: the delivery is saved and its moves carry the product, quantity and operation type).
- **Location:** `models/service_notification.py`, lines 394–406; `models/service_order.py`, lines 265–277; `models/service_warranty.py`, lines 185–197.
- **Trigger:** Create a delivery from a service notification, service order, or warranty containing products/components.
- **Actual behavior:** The action context supplies product lines through `default_move_ids_without_package`. Odoo 19's picking form uses `move_ids`, so these defaults do not populate the current relation.
- **Expected behavior:** The new delivery contains the products and quantities from the source service document.
- **Impact:** The delivery opens without the intended product lines. Additionally, the prepared move values contain `name`, which has also been removed from the Odoo 19 stock move model; simply renaming the context key is insufficient.
- **Evidence:** Local Odoo 19 model declarations and inspection of all three delivery actions; no custom compatibility relation was found.
- **Suggested fix:** Use `default_move_ids` and migrate the stock move values to supported Odoo 19 fields, including the picking description where necessary.
- **Validation needed:** Open and save a populated delivery from each of the three source document types.

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. SERVICE-001 was reproduced and fixed with database-backed tests on 2026-10-01.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `9ebc487`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **SERVICE-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
