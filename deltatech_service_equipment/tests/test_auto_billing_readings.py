# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.deltatech_service_agreement.tests.test_agreement_billing_p1 import AgreementBillingCommon


@tagged("post_install", "-at_install")
class TestAutoBillingReadings(AgreementBillingCommon):
    """EQUIPMENT-004 / EQUIPMENT-005: readings required only by the agreement type, reset after billing."""

    def _auto_agreement(self, name, readings_required, readings_done):
        agreement = self._create_agreement(name, automation="auto")
        agreement.type_id = self.env["service.agreement.type"].create(
            {"name": f"Type {name}", "journal_id": self.journal.id, "readings_required": readings_required}
        )
        agreement.meter_reading_status = readings_done
        agreement.next_date_invoice = self.today
        return agreement

    def _invoiced(self, agreement):
        consumption = self.env["service.consumption"].search([("agreement_id", "=", agreement.id)])
        return bool(consumption.invoice_id)

    def test_type_without_readings_is_billed(self):
        agreement = self._auto_agreement("NO-METER", readings_required=False, readings_done=False)
        self.assertIn(agreement, self.env["service.agreement"].get_agreements_auto_billing())
        self.env["service.agreement"].make_billing_automation()
        self.assertTrue(self._invoiced(agreement))

    def test_type_with_readings_waits_for_them(self):
        agreement = self._auto_agreement("METER-PENDING", readings_required=True, readings_done=False)
        self.assertNotIn(agreement, self.env["service.agreement"].get_agreements_auto_billing())
        self.env["service.agreement"].make_billing_automation()
        self.assertFalse(self._invoiced(agreement))

    def test_readings_done_are_reset_after_billing(self):
        agreement = self._auto_agreement("METER-DONE", readings_required=True, readings_done=True)
        self.env["service.agreement"].make_billing_automation()
        self.assertTrue(self._invoiced(agreement))
        self.assertFalse(agreement.meter_reading_status)
        # a type without required readings keeps its flag
        other = self._auto_agreement("NO-METER-FLAG", readings_required=False, readings_done=True)
        self.env["service.agreement"].make_billing_automation()
        self.assertTrue(other.meter_reading_status)
