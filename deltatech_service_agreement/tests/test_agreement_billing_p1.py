# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class AgreementBillingCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(su=True)
        cls.journal = cls.company_data["default_journal_sale"]
        cls.agreement_type = cls.env["service.agreement.type"].create(
            {"name": "Automatic billing", "journal_id": cls.journal.id}
        )
        cls.service_product = cls.env["product.product"].create(
            {
                "name": "Service fee",
                "type": "service",
                "taxes_id": [(6, 0, cls.company_data["default_tax_sale"].ids)],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Service customer"})
        cls.cycle = cls.env["service.cycle"].create({"name": "Monthly", "value": 1, "unit": "month"})
        cls.today = fields.Date.context_today(cls.env["service.agreement"])
        cls.period = cls._current_period()

    @classmethod
    def _current_period(cls):
        date_start = cls.today + relativedelta(day=1)
        date_end = date_start + relativedelta(months=1, days=-1)
        Period = cls.env["service.date.range"]
        period = Period.search([("date_start", "=", date_start), ("date_end", "=", date_end)])
        if not period:
            period = Period.create({"name": f"P1 {date_start:%Y/%m}", "date_start": date_start, "date_end": date_end})
        return period[:1]

    @classmethod
    def _create_agreement(cls, name, price=100.0, quantity=1.0, quantity_free=0.0, automation="manual"):
        agreement = cls.env["service.agreement"].create(
            {
                "name": name,
                "partner_id": cls.partner.id,
                "company_id": cls.env.company.id,
                "type_id": cls.agreement_type.id,
                "cycle_id": cls.cycle.id,
                "billing_automation": automation,
                "agreement_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.service_product.id,
                            "quantity": quantity,
                            "quantity_free": quantity_free,
                            "price_unit": price,
                            "currency_id": cls.env.company.currency_id.id,
                            "uom_id": cls.service_product.uom_id.id,
                        },
                    )
                ],
            }
        )
        agreement.contract_open()
        if "meter_reading_status" in agreement._fields:
            # cu deltatech_service_equipment instalat, facturarea automata cere citirile
            # contoarelor marcate ca facute (get_agreements_auto_billing)
            agreement.meter_reading_status = True
        return agreement


@tagged("post_install", "-at_install")
class TestAgreementAutoBilling(AgreementBillingCommon):
    """AGREEMENT-005: facturarea automata trece prin pregatire pana la factura."""

    def _auto_agreement(self, name):
        agreement = self._create_agreement(name, automation="auto")
        # contractul e scadent azi
        agreement.next_date_invoice = self.today
        return agreement

    def test_cron_prepares_and_invoices_every_due_agreement(self):
        first = self._auto_agreement("AUTO-1")
        second = self._auto_agreement("AUTO-2")
        self.env["service.agreement"].make_billing_automation()
        for agreement in first | second:
            consumption = self.env["service.consumption"].search([("agreement_id", "=", agreement.id)])
            self.assertEqual(len(consumption), 1, agreement.name)
            self.assertEqual(consumption.service_period_id, self.period)
            self.assertEqual(consumption.state, "done")
            self.assertTrue(consumption.invoice_id, agreement.name)
            self.assertEqual(consumption.invoice_id.journal_id, self.journal)
            self.assertEqual(consumption.invoice_id.amount_untaxed, 100.0)

    def test_cron_ignores_user_default_period_and_runs_twice_safely(self):
        """Perioada vine explicit din cron, nu din valorile implicite ale utilizatorului."""
        other_period = self.env["service.date.range"].create(
            {
                "name": "P1 other",
                "date_start": self.period.date_start + relativedelta(years=-5),
                "date_end": self.period.date_end + relativedelta(years=-5),
            }
        )
        self.env["ir.default"].set(
            "service.billing.preparation", "service_period_id", other_period.id, user_id=self.env.uid
        )
        agreement = self._auto_agreement("AUTO-3")
        self.env["service.agreement"].make_billing_automation()
        self.env["service.agreement"].make_billing_automation()
        consumption = self.env["service.consumption"].search([("agreement_id", "=", agreement.id)])
        self.assertEqual(len(consumption), 1)
        self.assertEqual(consumption.service_period_id, self.period)
        self.assertTrue(consumption.invoice_id)

    def test_cron_without_unique_period_does_nothing(self):
        agreement = self._auto_agreement("AUTO-4")
        self.period.active = False
        self.env["service.agreement"].make_billing_automation()
        self.assertFalse(self.env["service.consumption"].search([("agreement_id", "=", agreement.id)]))


@tagged("post_install", "-at_install")
class TestAgreementNegativeCorrections(AgreementBillingCommon):
    """AGREEMENT-009: corectiile negative nu se taie, cantitatile facturate concorda,
    iar documentul face referire la factura corectata (art. 319 alin. (20) lit. r) CF)."""

    def _period(self, months_back):
        """O corectie vine dintr-o perioada ulterioara facturii initiale (unicitate pe linie si perioada)."""
        if not months_back:
            return self.period
        name = f"P1 correction -{months_back}"
        Period = self.env["service.date.range"]
        period = Period.search([("name", "=", name)])
        if period:
            return period
        date_start = self.period.date_start + relativedelta(months=-months_back)
        return Period.create(
            {"name": name, "date_start": date_start, "date_end": date_start + relativedelta(months=1, days=-1)}
        )

    def _consumption(self, agreement, quantity, months_back=0):
        line = agreement.agreement_line
        return self.env["service.consumption"].create(
            {
                "partner_id": agreement.partner_id.id,
                "service_period_id": self._period(months_back).id,
                "agreement_id": agreement.id,
                "agreement_line_id": line.id,
                "product_id": line.product_id.id,
                "quantity": quantity,
                "price_unit": line.price_unit,
                "currency_id": line.currency_id.id,
                "date_invoice": self.today,
            }
        )

    def _bill(self, consumptions, group_service=False):
        wizard = (
            self.env["service.billing"]
            .with_context(active_ids=consumptions.ids)
            .create({"company_id": self.env.company.id, "journal_id": self.journal.id, "group_service": group_service})
        )
        action = wizard.do_billing()
        return self.env["account.move"].search(action["domain"])

    def _original_invoice(self, agreement, quantity=10, months_back=3):
        """Factura initiala, postata, a unei perioade anterioare corectiei."""
        move = self._bill(self._consumption(agreement, quantity, months_back=months_back))
        move.action_post()
        return move

    def _assert_references(self, move, original):
        self.assertEqual(move.ref, original.name)
        corrections = move.invoice_line_ids.filtered(lambda line: "Correction of invoice" in (line.name or ""))
        self.assertTrue(corrections)
        for line in corrections:
            self.assertIn(original.name, line.name)
            self.assertIn(fields.Date.to_string(original.invoice_date)[:4], line.name)

    def test_lone_negative_correction_becomes_credit_note(self):
        agreement = self._create_agreement("NEG-1")
        original = self._original_invoice(agreement)
        consumption = self._consumption(agreement, -2, months_back=1)
        move = self._bill(consumption)
        self.assertEqual(move.move_type, "out_refund")
        self.assertEqual(move.invoice_line_ids.quantity, 2)
        self.assertEqual(move.amount_untaxed, 200.0)
        self.assertEqual(consumption.invoiced_qty, -2)
        self.assertEqual(consumption.revenues, -200.0)
        self._assert_references(move, original)
        self.assertEqual(move.reversed_entry_id, original)

    def test_several_negative_lines_are_not_clipped(self):
        agreement = self._create_agreement("NEG-2")
        original = self._original_invoice(agreement)
        consumptions = (
            self._consumption(agreement, 3)
            | self._consumption(agreement, -5, months_back=1)
            | self._consumption(agreement, -5, months_back=2)
        )
        move = self._bill(consumptions)
        # net 3 - 5 - 5 = -7 -> nota de credit de 700
        self.assertEqual(move.move_type, "out_refund")
        self.assertEqual(sorted(move.invoice_line_ids.mapped("quantity")), [-3.0, 5.0, 5.0])
        self.assertEqual(move.amount_untaxed, 700.0)
        self.assertEqual(sorted(consumptions.mapped("invoiced_qty")), [-5.0, -5.0, 3.0])
        self.assertEqual(sum(consumptions.mapped("revenues")), -700.0)
        self._assert_references(move, original)
        self.assertEqual(move.reversed_entry_id, original)

    def test_partial_correction_stays_negative_line_on_invoice(self):
        agreement = self._create_agreement("NEG-3")
        original = self._original_invoice(agreement)
        consumptions = self._consumption(agreement, 5) | self._consumption(agreement, -2, months_back=1)
        move = self._bill(consumptions, group_service=True)
        # corectia nu se contopeste cu linia pozitiva, chiar si cu gruparea pe serviciu
        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(sorted(move.invoice_line_ids.mapped("quantity")), [-2.0, 5.0])
        self.assertEqual(move.amount_untaxed, 300.0)
        self.assertEqual(sum(consumptions.mapped("invoiced_qty")), 3.0)
        self._assert_references(move, original)
        self.assertFalse(move.reversed_entry_id)

    def test_negative_correction_ignores_free_quantity(self):
        agreement = self._create_agreement("NEG-4", quantity_free=1.0)
        self._original_invoice(agreement)
        consumptions = self._consumption(agreement, 4) | self._consumption(agreement, -2, months_back=1)
        move = self._bill(consumptions)
        # 4 - 1 gratuit = 3 facturat; corectia -2 integral
        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(sorted(move.invoice_line_ids.mapped("quantity")), [-2.0, 3.0])
        self.assertEqual(sorted(consumptions.mapped("invoiced_qty")), [-2.0, 3.0])
        self.assertEqual(sum(move.invoice_line_ids.mapped("quantity")), sum(consumptions.mapped("invoiced_qty")))

    def test_correction_without_original_invoice_is_refused(self):
        agreement = self._create_agreement("NEG-5")
        consumption = self._consumption(agreement, -2, months_back=1)
        with self.assertRaisesRegex(UserError, "NEG-5"):
            self._bill(consumption)

    def test_correction_of_draft_invoice_is_refused(self):
        """Doar o factura initiala postata poate fi corectata."""
        agreement = self._create_agreement("NEG-6")
        self._bill(self._consumption(agreement, 10, months_back=3))
        consumption = self._consumption(agreement, -2, months_back=1)
        with self.assertRaises(UserError):
            self._bill(consumption)

    def test_correction_uses_vat_rate_of_original_invoice(self):
        base_tax = self.company_data["default_tax_sale"]
        tax_19 = base_tax.copy({"name": "VAT 19% P1", "amount": 19.0})
        tax_21 = base_tax.copy({"name": "VAT 21% P1", "amount": 21.0})
        self.service_product.taxes_id = tax_19
        agreement = self._create_agreement("NEG-7")
        original = self._original_invoice(agreement)
        self.assertEqual(original.invoice_line_ids.tax_ids, tax_19)
        # cota s-a schimbat intre timp
        self.service_product.taxes_id = tax_21
        consumptions = self._consumption(agreement, 5) | self._consumption(agreement, -2, months_back=1)
        move = self._bill(consumptions)
        correction = move.invoice_line_ids.filtered(lambda line: line.quantity < 0)
        regular = move.invoice_line_ids.filtered(lambda line: line.quantity > 0)
        self.assertEqual(correction.tax_ids, tax_19)
        self.assertEqual(regular.tax_ids, tax_21)


@tagged("post_install", "-at_install")
class TestAgreementAutoBillingCorrections(AgreementBillingCommon):
    """Facturarea automata sare contractul cu o corectie fara factura initiala."""

    def test_cron_skips_agreement_with_unreferenced_correction(self):
        good = self._create_agreement("AUTO-OK", automation="auto")
        bad = self._create_agreement("AUTO-NEG", quantity=-1.0, automation="auto")
        (good | bad).write({"next_date_invoice": self.today})
        self.env["service.agreement"].make_billing_automation()
        good_consumption = self.env["service.consumption"].search([("agreement_id", "=", good.id)])
        bad_consumption = self.env["service.consumption"].search([("agreement_id", "=", bad.id)])
        self.assertTrue(good_consumption.invoice_id)
        self.assertEqual(len(bad_consumption), 1)
        self.assertFalse(bad_consumption.invoice_id)
        self.assertEqual(bad_consumption.state, "draft")
