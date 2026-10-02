# ©  2026 Terrabit
# See README.rst file on addons root folder for license details


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_service_signed_value(self):
        """Valuation of the done moves with the sign of the former stock valuation layers:
        outgoing moves are negative, incoming moves (returns) are positive.

        Odoo 19 removed ``stock.valuation.layer``; the value is kept on ``stock.move.value``
        (``stock_account``) and is always positive, the direction being given by
        ``is_out`` / ``is_in``. Moves that are not valued count as zero.
        """
        if "value" not in self._fields:
            return 0.0
        total = 0.0
        for move in self.filtered(lambda m: m.state == "done"):
            if move.is_out:
                total -= move.value
            elif move.is_in:
                total += move.value
        return total
