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
