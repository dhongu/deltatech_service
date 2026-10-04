# ©  2026 Terrabit
# See README.rst file on addons root folder for license details


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_service_signed_value(self):
        """Valuation of the done moves with the sign of the former stock valuation layers:
        outgoing moves are negative, incoming moves (returns) are positive.

        Odoo 19+ has no ``stock.valuation.layer``; the value is kept on ``stock.move.value``
        (``stock_account``), which in Odoo 20 is already signed (negative for outgoing moves).
        Moves that are not done or not valued count as zero.
        """
        if "value" not in self._fields:
            return 0.0
        return sum(self.filtered(lambda m: m.state == "done").mapped("value"))
