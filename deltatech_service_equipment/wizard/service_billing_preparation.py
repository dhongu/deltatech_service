# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.exceptions import UserError


class ServiceBillingPreparation(models.TransientModel):
    _inherit = "service.billing.preparation"

    def do_billing_preparation(self):
        if self.env.user.has_group("deltatech_service_equipment.force_agreement_invoice"):
            return super().do_billing_preparation()
        else:
            readings_message = ""
            for agreement in self.agreement_ids:
                if agreement.type_id.readings_required and not agreement.meter_reading_status:
                    readings_message += (
                        self.env._("The %s agreement does not have the meter readings made.\r\n") % agreement.name
                    )
            if not readings_message:
                return super().do_billing_preparation()
            else:
                raise UserError(self.env._(readings_message))
