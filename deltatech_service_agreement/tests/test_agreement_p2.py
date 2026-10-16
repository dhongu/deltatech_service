# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import Form, new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from .test_agreement_billing_p1 import AgreementBillingCommon


class AgreementP2Common(AgreementBillingCommon):
    def _consumption(self, agreement, quantity, price_unit=None, line=None):
        line = line or agreement.agreement_line[:1]
        return self.env["service.consumption"].create(
            {
                "partner_id": agreement.partner_id.id,
                "service_period_id": self.period.id,
                "agreement_id": agreement.id,
                "agreement_line_id": line.id,
                "product_id": line.product_id.id,
                "quantity": quantity,
                "price_unit": line.price_unit if price_unit is None else price_unit,
                "currency_id": line.currency_id.id,
                "date_invoice": self.today,
            }
        )


@tagged("post_install", "-at_install")
class TestAgreementGroupedUom(AgreementP2Common):
    """AGREEMENT-002: gruparea pe serviciu nu aduna cantitati in unitati de masura diferite."""

    def test_group_service_keeps_lines_with_different_uom_separate(self):
        agreement = self._create_agreement("UOM-1", price=10.0)
        line_unit = agreement.agreement_line
        line_dozen = line_unit.copy({"agreement_id": agreement.id, "uom_id": self.env.ref("uom.product_uom_dozen").id})
        consumptions = self._consumption(agreement, 1, line=line_unit) | self._consumption(
            agreement, 1, line=line_dozen
        )
        wizard = (
            self.env["service.billing"]
            .with_context(active_ids=consumptions.ids)
            .create({"company_id": self.env.company.id, "journal_id": self.journal.id, "group_service": True})
        )
        move = self.env["account.move"].search(wizard.do_billing()["domain"])
        self.assertEqual(len(move.invoice_line_ids), 2)
        self.assertEqual(
            {(line.product_uom_id, line.agreement_line_id, line.quantity) for line in move.invoice_line_ids},
            {(line_unit.uom_id, line_unit, 1.0), (line_dozen.uom_id, line_dozen, 1.0)},
        )

    def test_group_service_still_merges_same_uom(self):
        agreement = self._create_agreement("UOM-2", price=10.0)
        line_unit = agreement.agreement_line
        line_other = line_unit.copy({"agreement_id": agreement.id})
        consumptions = self._consumption(agreement, 1, line=line_unit) | self._consumption(
            agreement, 2, line=line_other
        )
        wizard = (
            self.env["service.billing"]
            .with_context(active_ids=consumptions.ids)
            .create({"company_id": self.env.company.id, "journal_id": self.journal.id, "group_service": True})
        )
        move = self.env["account.move"].search(wizard.do_billing()["domain"])
        self.assertEqual(len(move.invoice_line_ids), 1)
        self.assertEqual(move.invoice_line_ids.quantity, 3.0)


@tagged("post_install", "-at_install")
class TestAgreementNextInvoiceDate(AgreementP2Common):
    """AGREEMENT-003: data urmatoarei facturi urmeaza modificarile de program."""

    def test_schedule_changes_recompute_next_date(self):
        agreement = self._create_agreement("SCHED-1")
        start = fields.Date.to_date("2026-01-10")
        agreement.date_agreement = start
        self.assertEqual(agreement.next_date_invoice, start + relativedelta(months=1))

        weekly = self.env["service.cycle"].create({"name": "Weekly", "value": 1, "unit": "week"})
        agreement.cycle_id = weekly
        self.assertEqual(agreement.next_date_invoice, start + relativedelta(weeks=1))

        weekly.value = 2
        self.assertEqual(agreement.next_date_invoice, start + relativedelta(weeks=2))

        agreement.cycle_id = self.cycle
        agreement.invoice_day = 25
        self.assertEqual(agreement.next_date_invoice, fields.Date.to_date("2026-02-25"))

        agreement.invoice_day = -1
        self.assertEqual(agreement.next_date_invoice, fields.Date.to_date("2026-02-28"))

        agreement.date_agreement = fields.Date.to_date("2026-03-05")
        self.assertEqual(agreement.next_date_invoice, fields.Date.to_date("2026-04-30"))

    def test_invoice_date_change_recomputes_next_date(self):
        agreement = self._create_agreement("SCHED-2")
        consumption = self._consumption(agreement, 1)
        wizard = (
            self.env["service.billing"]
            .with_context(active_ids=consumption.ids)
            .create({"company_id": self.env.company.id, "journal_id": self.journal.id})
        )
        move = self.env["account.move"].search(wizard.do_billing()["domain"])
        move.invoice_date = fields.Date.to_date("2026-05-10")
        move.action_post()
        self.assertEqual(agreement.last_invoice_id, move)
        self.assertEqual(agreement.next_date_invoice, fields.Date.to_date("2026-06-10"))
        move.button_draft()
        move.invoice_date = fields.Date.to_date("2026-05-20")
        self.assertEqual(agreement.last_date_invoice, fields.Date.to_date("2026-05-20"))
        self.assertEqual(agreement.next_date_invoice, fields.Date.to_date("2026-06-20"))


@tagged("post_install", "-at_install")
class TestAgreementOverdueAutoBilling(AgreementP2Common):
    """AGREEMENT-004: contractele restante raman in facturarea automata."""

    def test_overdue_agreement_is_selected(self):
        overdue = self._create_agreement("OVERDUE-1", automation="auto")
        due = self._create_agreement("DUE-1", automation="auto")
        future = self._create_agreement("FUTURE-1", automation="auto")
        overdue.next_date_invoice = self.today - relativedelta(days=1)
        due.next_date_invoice = self.today
        future.next_date_invoice = self.today + relativedelta(days=1)
        selected = self.env["service.agreement"].get_agreements_auto_billing()
        self.assertIn(overdue, selected)
        self.assertIn(due, selected)
        self.assertNotIn(future, selected)

    def test_overdue_agreement_is_billed_once(self):
        overdue = self._create_agreement("OVERDUE-2", automation="auto")
        overdue.next_date_invoice = self.today - relativedelta(days=1)
        self.env["service.agreement"].make_billing_automation()
        self.env["service.agreement"].make_billing_automation()
        consumption = self.env["service.consumption"].search([("agreement_id", "=", overdue.id)])
        self.assertEqual(len(consumption), 1)
        self.assertTrue(consumption.invoice_id)


@tagged("post_install", "-at_install")
class TestAgreementDistribution(AgreementP2Common):
    """AGREEMENT-007: adaugarea unei valori pastreaza valoarea existenta (cantitate x pret)."""

    def _distribute(self, consumptions, amount):
        wizard = (
            self.env["service.distribution"]
            .with_context(active_ids=consumptions.ids)
            .create(
                {
                    "product_id": self.service_product.id,
                    "quantity": 1,
                    "amount": amount,
                    "type": "val",
                    "add_values": True,
                    "reference": False,
                }
            )
        )
        wizard.do_distribution()

    def test_add_amount_keeps_existing_value(self):
        agreement = self._create_agreement("DIST-1", price=10.0)
        consumption = self._consumption(agreement, 3, price_unit=10.0)
        consumption.name = "C"
        self._distribute(consumption, 12.0)
        self.assertEqual(consumption.quantity * consumption.price_unit, 42.0)

    def test_add_amount_zero_quantity(self):
        agreement = self._create_agreement("DIST-2", price=10.0)
        consumption = self._consumption(agreement, 0, price_unit=10.0)
        consumption.name = "C"
        self._distribute(consumption, 12.0)
        self.assertEqual(consumption.quantity * consumption.price_unit, 12.0)


@tagged("post_install", "-at_install")
class TestAgreementActiveCompany(AccountTestInvoicingCommon):
    """AGREEMENT-010 / AGREEMENT-011: wizard-urile folosesc compania activa, nu compania implicita a utilizatorului."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(su=True)
        # 1 USD = 2 EUR
        cls.eur = cls.setup_other_currency("EUR")
        cls.company_a = cls.env.company
        cls.company_b = cls.setup_other_company(name="Service Company B P2", currency_id=cls.eur.id)["company"]
        cls.user = new_test_user(
            cls.env,
            login="service_p2_user",
            groups="base.group_user,account.group_account_invoice,product.group_product_manager,deltatech_service_base.group_service_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a | cls.company_b).ids)],
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Service P2", "type": "service", "list_price": 100.0, "company_id": cls.company_b.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Service customer P2"})
        cls.cycle = cls.env["service.cycle"].create({"name": "Monthly P2", "value": 1, "unit": "month"})
        cls.agreement_b = (
            cls.env["service.agreement"]
            .with_company(cls.company_b)
            .create(
                {
                    "name": "Agreement B P2",
                    "partner_id": cls.partner.id,
                    "company_id": cls.company_b.id,
                    "currency_id": cls.eur.id,
                    "cycle_id": cls.cycle.id,
                }
            )
        )
        cls.agreement_b.contract_open()

    def _env_b(self):
        return self.env(user=self.user, context={"allowed_company_ids": [self.company_b.id, self.company_a.id]})

    def test_price_change_uses_product_company_currency(self):
        env = self._env_b()
        Wizard = env["service.price.change"]
        self.assertEqual(Wizard._default_currency(), self.eur)
        with Form(Wizard) as form:
            form.product_id = self.product.with_env(env)
            self.assertEqual(form.currency_id, self.eur)
            # list_price e in moneda companiei produsului (EUR), fara conversie
            self.assertEqual(form.price_unit, 100.0)

    def test_price_change_writes_list_price_in_product_currency(self):
        env = self._env_b()
        consumption = (
            self.env["service.consumption"]
            .with_company(self.company_b)
            .create(
                {
                    "partner_id": self.partner.id,
                    "service_period_id": self._period().id,
                    "agreement_id": self.agreement_b.id,
                    "product_id": self.product.id,
                    "quantity": 1,
                    "price_unit": 100.0,
                    "currency_id": self.eur.id,
                }
            )
        )
        wizard = (
            env["service.price.change"]
            .with_context(active_ids=consumption.ids)
            .create({"product_id": self.product.id, "price_unit": 150.0, "currency_id": self.eur.id})
        )
        wizard.do_price_change()
        self.assertEqual(consumption.price_unit, 150.0)
        self.assertEqual(self.product.list_price, 150.0)

    def test_billing_preparation_default_uses_active_company(self):
        defaults = self._env_b()["service.billing.preparation"].default_get(["agreement_ids"])
        self.assertEqual(defaults["company_id"], self.company_b.id)
        self.assertIn(self.agreement_b.id, defaults["agreement_ids"][0][2])

    def _period(self):
        today = fields.Date.today()
        date_start = today + relativedelta(day=1)
        date_end = date_start + relativedelta(months=1, days=-1)
        Period = self.env["service.date.range"]
        period = Period.search([("date_start", "=", date_start), ("date_end", "=", date_end)], limit=1)
        return period or Period.create({"name": "P2 period", "date_start": date_start, "date_end": date_end})
