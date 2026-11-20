# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .test_agreement_billing_p1 import AgreementBillingCommon


@tagged("post_install", "-at_install")
class TestAgreementGroupKey(AgreementBillingCommon):
    """AGREEMENT-015: cheile de grupare nu se ciocnesc intre tabele diferite."""

    def _set_sequence(self, table, next_id):
        self.env.cr.execute(f"SELECT setval('{table}_id_seq', %s, false)", (next_id,))  # noqa: S608

    def _agreement_for(self, name, partner, invoice_mode="none", quantity_free=0.0):
        agreement = self._create_agreement(name, quantity_free=quantity_free)
        agreement.write({"partner_id": partner.id, "invoice_mode": invoice_mode})
        return agreement

    def _consumption_for(self, agreement, quantity=1.0, period=None):
        line = agreement.agreement_line
        return self.env["service.consumption"].create(
            {
                "partner_id": agreement.partner_id.id,
                "service_period_id": (period or self.period).id,
                "agreement_id": agreement.id,
                "agreement_line_id": line.id,
                "product_id": line.product_id.id,
                "quantity": quantity,
                "price_unit": line.price_unit,
                "currency_id": line.currency_id.id,
                "date_invoice": self.today,
            }
        )

    def _wizard(self, consumptions, group_invoice):
        return (
            self.env["service.billing"]
            .with_context(active_ids=consumptions.ids)
            .create(
                {
                    "company_id": self.env.company.id,
                    "journal_id": self.journal.id,
                    "group_invoice": group_invoice,
                }
            )
        )

    def test_group_key_is_typed(self):
        agreement = self._agreement_for("KEY-1", self.partner)
        cons = self._consumption_for(agreement)
        wizard = self._wizard(cons, "partner")
        self.assertEqual(wizard._get_group_key(cons), ("partner", self.partner.id))
        wizard.group_invoice = "agreement"
        self.assertEqual(wizard._get_group_key(cons), ("agreement", agreement.id))
        wizard.group_invoice = "agreement_line"
        self.assertEqual(wizard._get_group_key(cons), ("agreement_line", agreement.agreement_line.id))
        agreement.invoice_mode = "detail"
        wizard.group_invoice = "partner"
        self.assertEqual(wizard._get_group_key(cons), ("agreement", agreement.id))

    def test_partner_and_detail_agreement_with_same_numeric_id_stay_apart(self):
        partner_a = self.env["res.partner"].create({"name": "Client A"})
        partner_b = self.env["res.partner"].create({"name": "Client B"})
        agreement_a = self._agreement_for("COL-A", partner_a)
        # contractul clientului B primeste ID-ul clientului A
        self._set_sequence("service_agreement", partner_a.id)
        agreement_b = self._agreement_for("COL-B", partner_b, invoice_mode="detail")
        self.assertEqual(agreement_b.id, partner_a.id)
        previous = self.env["service.date.range"].create(
            {
                "name": "GK previous",
                "date_start": self.period.date_start + relativedelta(months=-1),
                "date_end": self.period.date_start + relativedelta(days=-1),
            }
        )
        orders = ((agreement_a, agreement_b, self.period), (agreement_b, agreement_a, previous))
        for first, second, period in orders:
            cons = self._consumption_for(first, period=period) | self._consumption_for(second, period=period)
            action = self._wizard(cons, "partner").do_billing()
            moves = self.env["account.move"].search(action["domain"])
            self.assertEqual(len(moves), 2)
            self.assertEqual(moves.partner_id, partner_a | partner_b)
            for move in moves:
                self.assertEqual(len(move.invoice_line_ids), 1)

    def test_free_consumption_not_attached_to_other_agreement_line(self):
        agreement_a = self._agreement_for("FREE-A", self.partner)
        billable = self._consumption_for(agreement_a)
        # clientul C primeste ID-ul liniei facturabile
        self._set_sequence("res_partner", agreement_a.agreement_line.id)
        partner_c = self.env["res.partner"].create({"name": "Client C"})
        self.assertEqual(partner_c.id, agreement_a.agreement_line.id)
        agreement_c = self._agreement_for("FREE-C", partner_c, quantity_free=5.0)
        free = self._consumption_for(agreement_c, quantity=1.0)
        wizard = self._wizard(billable | free, "agreement_line")
        action = wizard.do_billing()
        move = self.env["account.move"].search(action["domain"])
        self.assertEqual(move.partner_id, self.partner)
        self.assertEqual(free.state, "none")
        self.assertFalse(free.invoice_id)
        self.assertEqual(billable.invoice_id, move)

    def test_foreign_partner_in_existing_group_is_refused(self):
        partner_b = self.env["res.partner"].create({"name": "Client B"})
        agreement_a = self._agreement_for("INV-A", self.partner)
        agreement_b = self._agreement_for("INV-B", partner_b)
        cons = self._consumption_for(agreement_a) | self._consumption_for(agreement_b)
        wizard = self._wizard(cons, "partner")
        # forteaza o cheie comuna, ca si cum ar exista o coliziune
        pre_invoice = {self.today: {}}
        key = ("partner", 1)
        wizard.add_invoice_line(cons[0], pre_invoice, 100.0, "x", key)
        with self.assertRaises(UserError):
            wizard.add_invoice_line(cons[1], pre_invoice, 100.0, "x", key)
