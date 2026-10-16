## 19.0.1.2.9 (2026-10-16)

- The warranty *Total amount* follows the edits of the quantity and the unit price of
  its lines, not only the added or removed lines (SERVICE-007).
- The delivery and the transfer prepared from a notification, a service order or a
  warranty convert the line quantity into the product unit: one dozen is delivered as
  12 units, no longer as one unit. The service order created from a notification keeps
  the unit of the notification line (SERVICE-009).
- "New notification" from a transfer keeps the unit of measure of the moves and no longer
  passes the transfer as a sale order in the context; the commented-out button was
  removed from the transfer form (SERVICE-010).
- The technician grouping helper of notifications lists the users of the current
  company instead of the user's default company (SERVICE-011).

## 19.0.1.2.8 (2026-10-16)

- Each service order gets its own portal access token: the default was computed once
  per server start, so the orders created until a restart shared the same token. The
  upgrade gives every existing order a new token.
- The linked service order of a notification is no longer searched while the
  notification is still being created (no more "Domains don't support NewId" warning).
- "New transfer" on notifications fills the internal transfer with the products again:
  the lines are passed through `move_ids` (SERVICE-005).
- "New notification" from a transfer and the technician grouping helper no longer use
  the removed `move_lines` and `name_get()` (SERVICE-010, SERVICE-011).

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
