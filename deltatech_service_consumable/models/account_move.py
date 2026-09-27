# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def action_post(self):
        # recompute total_percent field for agreements, if any
        res = super().action_post()
        invoice_agreements = self.env["service.agreement"]
        for invoice in self:
            if invoice.move_type == "out_invoice":
                for line in invoice.invoice_line_ids:
                    invoice_agreements |= line.sudo().agreement_line_id.agreement_id
        if invoice_agreements:
            # contabilul care postează factura nu are drept de scriere pe contract
            # (același tipar ca în deltatech_service_agreement)
            invoice_agreements.sudo().compute_percent()
        return res
