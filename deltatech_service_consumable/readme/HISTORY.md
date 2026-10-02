## 19.0.1.1.9 (2026-10-02)

- Validating a delivery linked to a service agreement crashed with `AttributeError` on the
  removed `stock_valuation_layer_ids` field (Odoo 19 has no stock valuation layers). The
  agreement cost now uses the move valuation (`stock.move.value`) with the former sign
  (deliveries negative, returns positive), only for transfers completed by the call: a
  backorder wizard or a repeated validation no longer adds the cost twice. "Recompute
  costs" uses the same signed value (CONSUMABLE-002).

## 19.0.1.1.8 (2026-10-01)

- Efficiency report: meter usage is converted to the report unit with `_compute_quantity()`
  (Odoo 19 factor convention); 2 dozen now give 24 units instead of 0.1667.

## 19.0.1.1.7 (2026-09-30)

- Own module icon in the flat style of the other modules.
