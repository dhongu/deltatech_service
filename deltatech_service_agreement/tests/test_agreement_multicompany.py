# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAgreementMultiCompany(AccountTestInvoicingCommon):
    """AGREEMENT-001 (billing currency/company) and AGREEMENT-006 (agreement line company rules)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # setup data as superuser; the checks below run with dedicated users
        cls.env = cls.env(su=True)
        # 1 USD = 2 EUR (rates of company A)
        cls.eur = cls.setup_other_currency("EUR")
        cls.company_a = cls.env.company
        cls.company_b_data = cls.setup_other_company(name="Service Company B", currency_id=cls.eur.id)
        cls.company_b = cls.company_b_data["company"]
        cls.journal_a = cls.company_data["default_journal_sale"]
        cls.journal_b = cls.company_b_data["default_journal_sale"]

        cls.service_product = cls.env["product.product"].create(
            {
                "name": "Service fee",
                "type": "service",
                "taxes_id": [
                    (6, 0, (cls.company_data["default_tax_sale"] | cls.company_b_data["default_tax_sale"]).ids)
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Service customer"})
        cls.cycle = cls.env["service.cycle"].create({"name": "Monthly", "value": 1, "unit": "month"})
        cls.env["service.date.range"].generate_date_range()
        cls.period = cls.env["service.date.range"].search([], limit=1)

        # default company A, also allowed in company B
        cls.billing_user = new_test_user(
            cls.env,
            login="service_billing_user",
            groups="base.group_user,account.group_account_invoice,deltatech_service_base.group_service_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a | cls.company_b).ids)],
        )
        cls.service_user_a = new_test_user(
            cls.env,
            login="service_user_a",
            groups="base.group_user,deltatech_service_base.group_service_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.service_manager_a = new_test_user(
            cls.env,
            login="service_manager_a",
            groups="base.group_user,deltatech_service_base.group_service_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )

        cls.agreement_a = cls._create_agreement(cls.company_a, cls.company_a.currency_id, 100.0)
        cls.agreement_b = cls._create_agreement(cls.company_b, cls.eur, 100.0)

    @classmethod
    def _create_agreement(cls, company, currency, price):
        return (
            cls.env["service.agreement"]
            .with_company(company)
            .create(
                {
                    "name": f"Agreement {company.name}",
                    "partner_id": cls.partner.id,
                    "company_id": company.id,
                    "currency_id": currency.id,
                    "cycle_id": cls.cycle.id,
                    "agreement_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": cls.service_product.id,
                                "quantity": 1,
                                "price_unit": price,
                                "currency_id": currency.id,
                                "uom_id": cls.service_product.uom_id.id,
                            },
                        )
                    ],
                }
            )
        )

    def _create_consumption(self, agreement):
        line = agreement.agreement_line
        return (
            self.env["service.consumption"]
            .with_company(agreement.company_id)
            .create(
                {
                    "partner_id": agreement.partner_id.id,
                    "service_period_id": self.period.id,
                    "agreement_id": agreement.id,
                    "agreement_line_id": line.id,
                    "product_id": line.product_id.id,
                    "quantity": 1,
                    "price_unit": line.price_unit,
                    "currency_id": line.currency_id.id,
                    "date_invoice": fields.Date.today(),
                }
            )
        )

    def _bill(self, consumption, company, journal):
        wizard = (
            self.env["service.billing"]
            .with_user(self.billing_user)
            .with_company(company)
            .with_context(active_ids=consumption.ids)
            .create({"company_id": company.id, "journal_id": journal.id})
        )
        self.assertEqual(wizard.consumption_ids, consumption)
        action = wizard.do_billing()
        return self.env["account.move"].search(action["domain"])

    # ------------------------------------------------------------------
    # AGREEMENT-001
    # ------------------------------------------------------------------

    def test_billing_other_company_keeps_its_currency(self):
        """EUR consumption of company B, billed by a user whose default company is A (USD)."""
        consumption = self._create_consumption(self.agreement_b)
        invoice = self._bill(consumption, self.company_b, self.journal_b)

        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.company_id, self.company_b)
        self.assertEqual(invoice.currency_id, self.eur)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 100.0)
        self.assertEqual(invoice.amount_untaxed, 100.0)
        self.assertEqual(invoice.invoice_line_ids.account_id.company_ids, self.company_b)
        self.assertEqual(invoice.invoice_line_ids.tax_ids, self.company_b_data["default_tax_sale"])
        # revenues are stored in the currency of the consumption company (EUR)
        self.assertEqual(consumption.revenues, 100.0)

    def test_billing_foreign_currency_journal(self):
        """USD consumption of company A billed on a EUR journal: the price is converted to EUR."""
        journal_eur = self.journal_a.copy({"name": "Sales EUR", "code": "SEUR", "currency_id": self.eur.id})
        consumption = self._create_consumption(self.agreement_a)
        invoice = self._bill(consumption, self.company_a, journal_eur)

        self.assertEqual(invoice.currency_id, self.eur)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 200.0)
        self.assertEqual(invoice.amount_untaxed_signed, 100.0)
        self.assertEqual(consumption.revenues, 100.0)

    def test_billing_rejects_consumption_of_other_company(self):
        consumption = self._create_consumption(self.agreement_a)
        wizard = (
            self.env["service.billing"]
            .with_user(self.billing_user)
            .with_context(allowed_company_ids=[self.company_b.id, self.company_a.id])
            .create(
                {
                    "company_id": self.company_b.id,
                    "journal_id": self.journal_b.id,
                    "consumption_ids": [(6, 0, consumption.ids)],
                }
            )
        )
        with self.assertRaises(UserError):
            wizard.do_billing()
        self.assertEqual(consumption.state, "draft")
        self.assertFalse(consumption.invoice_id)

    # ------------------------------------------------------------------
    # AGREEMENT-006
    # ------------------------------------------------------------------

    def test_line_of_other_company_not_readable(self):
        line_b = self.agreement_b.agreement_line
        Line = self.env["service.agreement.line"].with_user(self.service_user_a)
        self.assertFalse(Line.search([("id", "=", line_b.id)]))
        self.assertEqual(
            Line.search([("id", "in", (line_b | self.agreement_a.agreement_line).ids)]), self.agreement_a.agreement_line
        )
        with self.assertRaises(AccessError):
            line_b.with_user(self.service_user_a).read(["price_unit", "quantity"])

    def test_line_of_other_company_not_writable(self):
        line_b = self.agreement_b.agreement_line
        with self.assertRaises(AccessError):
            line_b.with_user(self.service_user_a).write({"price_unit": 1.0})
        self.assertEqual(line_b.price_unit, 100.0)

    def test_line_cannot_be_moved_to_other_company_agreement(self):
        line_a = self.agreement_a.agreement_line
        with self.assertRaises(AccessError):
            line_a.with_user(self.service_user_a).write({"agreement_id": self.agreement_b.id})
        self.assertEqual(line_a.agreement_id, self.agreement_a)

    def test_line_cannot_be_created_on_other_company_agreement(self):
        Line = self.env["service.agreement.line"].with_user(self.service_manager_a)
        with self.assertRaises(AccessError):
            Line.create(
                {
                    "agreement_id": self.agreement_b.id,
                    "product_id": self.service_product.id,
                    "price_unit": 1.0,
                    "currency_id": self.eur.id,
                }
            )
        line = Line.create(
            {
                "agreement_id": self.agreement_a.id,
                "product_id": self.service_product.id,
                "price_unit": 1.0,
                "currency_id": self.company_a.currency_id.id,
            }
        )
        self.assertEqual(line.company_id, self.company_a)
