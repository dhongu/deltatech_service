# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    history_count = fields.Integer(compute="_compute_history_number")

    def open_history(self):
        self.ensure_one()
        res = {
            "res_model": "object.history",
            "target": "current",
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "name": self.env._("History"),
            "domain": [["res_id", "=", self.id], ["res_model", "=", "res.partner"]],
            "context": {"default_res_id": self.id, "default_res_model": "res.partner"},
        }
        return res

    def _compute_history_number(self):
        for partner in self:
            histories = self.env["object.history"].search(
                [("res_id", "=", partner.id), ("res_model", "=", "res.partner")]
            )
            if histories:
                partner.history_count = len(histories)
            else:
                partner.history_count = False
