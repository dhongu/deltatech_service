## 20.0.1.1.10 (2026-10-10)

- Service efficiency report: a global company restriction limits the rows to the user's
  active companies. The report reuses the `stock.picking.report` SQL view under another
  model, so the company restriction of that report did not apply and a user saw the figures
  of every company (CONSUMABLE-003).
- Service efficiency report: the model is declared as a SQL view (`_auto = False`) and does
  not get log-access fields without a column in the view (CONSUMABLE-004).
- Port of 19.0.1.1.10 (dhongu/deltatech_service#130). Adapted for 20.0: the 19.0 `ir.rule`
  became a global row (no group) in `security/ir.access.csv`.

## 20.0.1.1.9 (2026-10-04)

- Validating a delivery linked to a service agreement added the move value to the
  agreement costs on every call, also when the backorder wizard was returned (before
  the transfer was done) or when the transfer was already done. The cost is now added
  only for transfers completed by the call, with
  `stock.move._get_service_signed_value()` (deliveries negative, returns positive, as
  expected by `compute_percent()`); "Recompute costs" uses the same value
  (CONSUMABLE-002). Port of 19.0.1.1.9 (dhongu/deltatech_service#104); on 20.0 the
  removed `stock_valuation_layer_ids` was already replaced by the (signed) `stock.move.value`,
  and the tests use `ir.config_parameter.set_str()` instead of the removed `set_param()`.

## 20.0.1.1.8 (2026-10-01)

- Efficiency report: meter usage is converted to the report unit with `_compute_quantity()`
  (Odoo 19+ factor convention); 2 dozen now give 24 units instead of 0.1667.

## 20.0.1.1.7 (2026-09-30)

- Own module icon in the flat style of the other modules.
