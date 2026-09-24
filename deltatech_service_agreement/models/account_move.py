# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def _get_service_consumptions(self):
        # sudo: anularea/stergerea unei facturi sau a unei plati o poate face si un utilizator
        # doar cu drepturi de contabilitate, fara acces la modulul de service;
        # consumurile sunt limitate la facturile curente, deci si la companiile lor
        return self.env["service.consumption"].sudo().search([("invoice_id", "in", self.ids)])

    def action_cancel(self):
        res = super().action_cancel()
        consumptions = self._get_service_consumptions()
        if consumptions:
            consumptions.write({"state": "draft", "invoice_id": False})
            consumptions.agreement_id.compute_totals()
        return res

    def unlink(self):
        consumptions = self._get_service_consumptions()
        if consumptions:
            consumptions.write({"state": "draft"})
            consumptions.agreement_id.compute_totals()
        return super().unlink()

    def action_post(self):
        res = super().action_post()
        # sudo: postarea o poate face si un utilizator fara drepturi pe contracte
        agreements = self.env["service.agreement"].sudo()
        for invoice in self.sudo():
            if invoice.move_type == "out_invoice":
                invoice_agreements = invoice.invoice_line_ids.agreement_line_id.agreement_id

                invoice_agreements.write({"last_invoice_id": invoice.id})
                agreements |= invoice_agreements

        agreements.compute_totals()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    agreement_line_id = fields.Many2one("service.agreement.line", string="Service Agreement Line")
    agreement_id = fields.Many2one("service.agreement", related="agreement_line_id.agreement_id", store=True)
