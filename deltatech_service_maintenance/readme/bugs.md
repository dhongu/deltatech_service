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

## SERVICE-002 — P1: Batch service order creation drops all entries except the last

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_order.py, create().
- **Trigger:** Create two or more service orders in one ORM call.
- **Actual behavior:** The override loops over vals_list but calls super().create(vals), passing only the last dictionary.
- **Impact:** Earlier orders are silently omitted and the returned record count violates the multi-create contract.
- **Evidence:** Executed the actual method in a minimal superclass harness: inputs named A and B passed only B to the superclass.
- **Suggested fix:** Pass the complete vals_list after preparing every entry.
- **Validation needed:** Single, empty and multi-record creation, including imports and copied orders.

## SERVICE-003 — P1: Generating new quotations uses removed sale line APIs

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_notification.py and models/service_order.py, new_sale_order_button().
- **Trigger:** Generate a new quotation from a notification or service order containing components or operations.
- **Actual behavior:** Both methods call line.product_id_change(), absent from Odoo 19 sale.order.line. Their subsequent field conversion also accesses old product_uom and tax_id names instead of product_uom_id and tax_ids.
- **Impact:** Quotation generation raises before returning the populated form.
- **Evidence:** Searched Community, Enterprise and custom method definitions: no product_id_change remains. Verified current sale line UoM/tax declarations in local core.
- **Suggested fix:** Use current computed sale line fields and a supported preparation path.
- **Validation needed:** New quotation with components, operations, taxes and nondefault units; existing quotation updates.

## SERVICE-004 — P1: Warranty delivery validation accesses removed valuation layers

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/stock.py, StockPicking.button_validate().
- **Trigger:** An authorized approver validates a picking linked to a warranty with stock moves.
- **Actual behavior:** After parent validation the method iterates move.stock_valuation_layer_ids, a field absent in Odoo 19.
- **Impact:** The transaction raises and rolls back instead of finishing the delivery and updating warranty costs.
- **Evidence:** Inspected the handler and searched all local stock field definitions; stock.move uses move-level value in Odoo 19. The authorization guard does not prevent the later API failure.
- **Suggested fix:** Use the supported valuation API and update costs only when completion succeeds, with correct signs and split quantities.
- **Validation needed:** Authorized warranty and recondition delivery validation, wizard paths, returns and partial deliveries.

## SERVICE-005 — P2: Internal transfer actions still populate the obsolete picking move relation

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_notification.py, new_transfer_button().
- **Trigger:** Create an internal transfer from a notification with products.
- **Actual behavior:** The action uses default_move_lines while Odoo 19 stock.picking uses move_ids. The delivery actions were updated, but this separate transfer path was left behind.
- **Impact:** The internal transfer opens without the requested moves.
- **Evidence:** Compared transfer context with local picking fields and the corrected delivery action. No compatibility move_lines relation exists on stock.picking.
- **Suggested fix:** Populate default_move_ids with current stock move values.
- **Validation needed:** Open and save an internal transfer containing one and several notification items.

## SERVICE-006 — P1: Warranty approval permissions are enforced only by button visibility

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_warranty.py, approve(); views/service_warranty_view.xml.
- **Trigger:** A warranty user without the approval or manager group invokes approve through RPC.
- **Actual behavior:** The button is restricted to approval/manager groups, but the public method simply assigns state=approved. Warranty users have write ACLs and no corresponding server-side approval check.
- **Impact:** Users can bypass the intended approval role and approve their own warranty requests.
- **Evidence:** Inspected view group restrictions and model ACLs; executed the actual extracted approve method, which assigns approved without consulting user groups. No database RPC test.
- **Suggested fix:** Enforce authorized approval groups and allowed source states in the server-side method.
- **Validation needed:** Ordinary warranty user denied, approver and manager allowed, and invalid/repeated transitions.

## SERVICE-007 — P2: Stored warranty totals do not follow line quantity and cost edits

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_warranty.py, _compute_total_amount().
- **Trigger:** Change quantity or price_unit on an existing warranty item without adding/removing items.
- **Actual behavior:** The stored total depends only on item_ids, while summing the nonstored amount derived from line price and quantity; neither input nor item_ids.amount appears in the dependency declaration.
- **Impact:** Warranty totals remain stale when costs or quantities change, including cost writes from delivery validation after its API issue is corrected.
- **Evidence:** Inspected complete item and warranty compute declarations; no override explicitly refreshes the stored total on line edits. Source evidence only.
- **Suggested fix:** Declare the complete line dependencies and recompute on price and quantity changes.
- **Validation needed:** Edit existing item quantity and price, compare total after a new transaction, and check adding/removing items.

## SERVICE-008 — P1: Notification equipment detection requires fields outside the declared dependencies

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_notification.py, create(); __manifest__.py.
- **Trigger:** Install maintenance with its declared dependencies, then create a notification with description keywords or a uniquely matched equipment contact.
- **Actual behavior:** The create override searches equipment ean_code and reads equipment.agreement_id, but both fields are supplied by optional deltatech_service_equipment, absent from the maintenance dependency closure. Base equipment defines neither field.
- **Impact:** Notification creation fails in a valid minimal installation with an invalid search field or AttributeError.
- **Evidence:** Compared loaded base equipment definitions, extension field providers and the full maintenance manifest. Maintenance otherwise depends on equipment_base and sale/stock addons.
- **Suggested fix:** Use the base equipment APIs for the independent module, guard optional integration, or explicitly declare the required extension dependency.
- **Validation needed:** Fresh installation with only declared dependencies, contact detection and description keyword detection, then with optional equipment agreement integration.

## SERVICE-009 — P2: Delivery preparation changes the unit without converting the source quantity

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_notification.py, models/service_order.py and models/service_warranty.py, new_delivery_button().
- **Trigger:** Set a source component/item to quantity 1 in Dozen for a product stocked in Unit, then create its delivery.
- **Actual behavior:** All three actions copy item.quantity unchanged but force the stock move product_uom to the product base UoM, ignoring item.product_uom.
- **Impact:** The requested one dozen is prepared as one unit, causing incorrect material delivery quantities.
- **Evidence:** Inspected editable item UoM fields and each action dictionary: quantities are copied directly and every product_uom is product_id.uom_id. No database-backed delivery test.
- **Suggested fix:** Preserve a valid source UoM or convert its quantity into the chosen move UoM.
- **Validation needed:** Unit/Dozen source lines in each of the three document types and a same-unit baseline.
