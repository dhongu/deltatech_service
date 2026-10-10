# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class ServiceBilling(models.TransientModel):
    _inherit = "service.billing"

    def do_billing(self):
        # read before billing: the wizard consumptions are limited to the ones not yet invoiced
        agreements = self.consumption_ids.agreement_id
        action = super().do_billing()
        # the readings ticked as done cover the billed period only: the next period needs
        # new readings before it can be billed again
        agreements.filtered(lambda a: a.type_id.readings_required and a.meter_reading_status).write(
            {"meter_reading_status": False}
        )
        return action
