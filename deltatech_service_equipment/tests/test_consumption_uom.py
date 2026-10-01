# ©  2026 Terrabit
# See README.rst file on addons root folder for license details


from odoo.tests import Form

from odoo.addons.deltatech_service_agreement.tests.test_agreement import TestAgreement
from odoo.addons.deltatech_service_equipment_base.tests.test_service import TestService


class TestConsumptionUom(TestAgreement, TestService):
    """Consumption generated from meter readings is converted from the meter unit
    to the agreement line unit like uom.uom._compute_quantity() does."""

    def setUp(self):
        super().setUp()
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.uom_dozen = self.env.ref("uom.product_uom_dozen")
        self.equipment = self.env["service.equipment"].create(
            {
                "name": "Test Equipment UoM",
                "type_id": self.equipment_type.id,
                "model_id": self.equipment_model.id,
            }
        )

    def _get_consumption(self, meter_uom, line_uom):
        meter = self.env["service.meter"].create(
            {
                "name": "Test Meter UoM",
                "meter_categ_id": self.meter_category.id,
                "equipment_id": self.equipment.id,
                "uom_id": meter_uom.id,
            }
        )
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement UoM"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle
        agreement.date_agreement = self.date_range.date_start
        agreement.meter_reading_status = True
        with agreement.agreement_line.new() as agreement_line:
            agreement_line.product_id = self.product_ab
            agreement_line.quantity = 1
            agreement_line.price_unit = 100
            agreement_line.equipment_id = self.equipment
            agreement_line.meter_id = meter
        agreement = agreement.save()
        agreement.agreement_line.uom_id = line_uom
        agreement.contract_open()
        agreement.service_equipment()

        for value, date in ((24, self.date_range.date_start), (48, self.date_range.date_end)):
            reading = Form(self.env["service.meter.reading"])
            reading.meter_id = meter
            reading.counter_value = value
            reading.date = date
            reading.save()
        difference = sum(meter.meter_reading_ids.mapped("difference"))
        self.assertTrue(difference)

        wizard = Form(self.env["service.billing.preparation"].with_context(active_ids=[agreement.id]))
        wizard.service_period_id = self.date_range
        wizard = wizard.save()
        action = wizard.do_billing_preparation()
        consumption = self.env["service.consumption"].search(action["domain"])
        self.assertEqual(len(consumption), 1)
        return consumption, difference

    def test_meter_dozen_line_unit(self):
        consumption, difference = self._get_consumption(self.uom_dozen, self.uom_unit)
        self.assertAlmostEqual(consumption.quantity, difference * 12)

    def test_meter_unit_line_dozen(self):
        consumption, difference = self._get_consumption(self.uom_unit, self.uom_dozen)
        self.assertAlmostEqual(consumption.quantity, difference / 12)

    def test_meter_dozen_line_without_uom(self):
        # without a unit on the agreement line the invoice uses the product unit
        self.assertEqual(self.product_ab.uom_id, self.uom_unit)
        consumption, difference = self._get_consumption(self.uom_dozen, self.env["uom.uom"])
        self.assertAlmostEqual(consumption.quantity, difference * 12)

    def test_same_uom(self):
        consumption, difference = self._get_consumption(self.uom_dozen, self.uom_dozen)
        self.assertAlmostEqual(consumption.quantity, difference)
