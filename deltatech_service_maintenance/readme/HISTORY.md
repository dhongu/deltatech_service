## 19.0.1.2.7 (2026-10-10)

- Writing *Approved* directly in the warranty status (RPC, import) is refused to the users
  who may not approve: the same right as the *Approve* button (SERVICE-012). The other
  states and the managers' clickable status bar are unchanged.

## 19.0.1.2.6 (2026-10-09)

- Creating several service orders in one call (import, batch create) kept only the
  last one; all orders are now created and returned (SERVICE-002).
- Approving a warranty is checked on the server: only the warranty Approval or
  Manager groups may approve, and only warranties waiting for approval
  (SERVICE-006).
- Creating a notification no longer fails when the optional equipment extension
  (EAN code, service agreement on the equipment) is not installed; the equipment is
  still detected from the contact and the customer is taken from the equipment
  (SERVICE-008).

## 19.0.1.2.5 (2026-10-02)

- "New quotation" on notifications and service orders crashed on the removed
  `product_id_change()` and `route_id` of the sale line. The lines are prepared from the
  Odoo 19 computed fields (`product_uom_id`, `tax_ids`, `route_ids`, price and
  description); without an address on the document the delivery address is taken from
  the customer instead of failing on save (SERVICE-003).
- Validating a warranty delivery crashed on the removed `stock_valuation_layer_ids`
  field. The warranty item unit cost is now the delivered value (`stock.move.value`)
  divided by the delivered quantity, in the item unit, and is written only when the
  transfer is completed (SERVICE-004).

## 19.0.1.2.4 (2026-10-01)

- The delivery buttons on service notifications, service orders and warranties
  fill the new picking with the products again: the lines are passed through
  `move_ids` (`move_ids_without_package` no longer exists in Odoo 19) and
  without the removed stock move `name` field (SERVICE-001).

## 19.0.1.2.3 (2026-09-30)

- Own module icon in the flat style of the other modules.

## 19.0.1.2.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
