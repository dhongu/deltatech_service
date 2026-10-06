# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAgreementDisplayName(TransactionCase):
    def test_display_name(self):
        partner = self.env["res.partner"].create({"name": "Client Test"})
        cycle = self.env["service.cycle"].create({"name": "Test Cycle", "value": 1, "unit": "month"})
        agreement = self.env["service.agreement"].create(
            {"name": "CTR-TEST", "partner_id": partner.id, "cycle_id": cycle.id, "date_agreement": "2026-03-15"}
        )
        date_format = self.env["res.lang"]._get_data(code=self.env.user.lang).date_format
        date_str = fields.Date.to_date("2026-03-15").strftime(date_format)

        self.assertEqual(agreement.display_name, f"CTR-TEST / {date_str}")
        self.assertEqual(
            agreement.with_context(formatted_display_name=True).display_name,
            f"CTR-TEST\t--Client Test · {date_str}--",
        )

        agreement.date_agreement = False
        self.assertEqual(agreement.display_name, "CTR-TEST")
        self.assertEqual(agreement.with_context(formatted_display_name=True).display_name, "CTR-TEST\t--Client Test--")
