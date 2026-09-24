# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAgreement(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner", "property_account_position_id": False})
        self.product_ab = self.env["product.product"].create(
            {
                "name": "Test Product",
                "company_id": self.env.company.id,
                "taxes_id": [
                    (6, 0, self.env["account.tax"].search([("company_id", "=", self.env.company.id)], limit=2).ids)
                ],
            }
        )

        self.journal = self.env["account.journal"].create(
            {
                "name": "Test Journal",
                "type": "sale",
                "code": "TEST",
                "service_invoice": True,
            }
        )

        self.agreement_type = self.env["service.agreement.type"].create(
            {
                "name": "Test Agreement Type",
                "journal_id": self.journal.id,
            }
        )
        self.cycle = self.env["service.cycle"].create(
            {
                "name": "Test Cycle",
                "value": 1,
                "unit": "month",
            }
        )
        self.env["service.date.range"].generate_date_range()
        self.date_range = self.env["service.date.range"].search([], limit=1)

    def _create_agreement_invoice(self):
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle

        with agreement.agreement_line.new() as agreement_line:
            agreement_line.product_id = self.product_ab
            agreement_line.quantity = 1
            agreement_line.price_unit = 100

        agreement = agreement.save()
        agreement.contract_open()

        wizard = Form(self.env["service.billing.preparation"].with_context(active_ids=[agreement.id]))
        wizard.service_period_id = self.date_range
        wizard = wizard.save()
        action = wizard.do_billing_preparation()

        consumptions = self.env["service.consumption"].search(action["domain"])

        wizard = Form(self.env["service.distribution"].with_context(active_ids=consumptions.ids))
        wizard.quantity = 10
        wizard = wizard.save()
        wizard.do_distribution()

        wizard = Form(self.env["service.price.change"].with_context(active_ids=consumptions.ids))
        wizard.price_unit = 5
        wizard = wizard.save()
        wizard.do_price_change()

        wizard = Form(self.env["service.billing"].with_context(active_ids=consumptions.ids))
        wizard = wizard.save()
        action = wizard.do_billing()

        invoices = self.env["account.move"].search(action["domain"])
        return agreement, consumptions, invoices

    def _create_accountant(self):
        # utilizator doar cu drepturi de facturare, fara drepturi pe modulul de service
        return self.env["res.users"].create(
            {
                "name": "Test Accountant",
                "login": "test_service_accountant",
                "company_id": self.env.company.id,
                "company_ids": [(6, 0, self.env.company.ids)],
                "group_ids": [(6, 0, [self.env.ref("account.group_account_invoice").id])],
            }
        )

    def test_agreement(self):
        agreement, consumptions, invoices = self._create_agreement_invoice()
        invoices.action_post()
        self.assertIn(agreement.last_invoice_id, invoices)

    def test_accountant_post_invoice(self):
        agreement, consumptions, invoices = self._create_agreement_invoice()
        accountant = self._create_accountant()
        invoices.with_user(accountant).action_post()
        self.assertEqual(invoices.mapped("state"), ["posted"] * len(invoices))
        self.assertIn(agreement.last_invoice_id, invoices)

    def test_accountant_unlink_invoice(self):
        agreement, consumptions, invoices = self._create_agreement_invoice()
        self.assertTrue(consumptions.invoice_id)
        accountant = self._create_accountant()
        invoices.with_user(accountant).unlink()
        self.assertFalse(invoices.exists())
        self.assertEqual(set(consumptions.mapped("state")), {"draft"})

    def test_accountant_unlink_unrelated_move(self):
        # plata / nota contabila fara legatura cu service: nu trebuie sa ceara drepturi pe consumuri
        accountant = self._create_accountant()
        move = (
            self.env["account.move"]
            .with_user(accountant)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner_1.id,
                    "invoice_line_ids": [(0, 0, {"name": "Line", "quantity": 1, "price_unit": 10})],
                }
            )
        )
        move.unlink()
        self.assertFalse(move.exists())
