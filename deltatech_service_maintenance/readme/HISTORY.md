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
