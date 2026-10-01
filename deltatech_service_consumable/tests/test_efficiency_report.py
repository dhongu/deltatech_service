# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import TransactionCase


class TestEfficiencyReportUsage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        meter_category = cls.env["service.meter.category"].create(
            {"name": "Test Meter Category", "uom_id": cls.uom_unit.id}
        )
        cls.equipment = cls.env["service.equipment"].create({"name": "Test Equipment"})
        cls.meter = cls.env["service.meter"].create(
            {
                "name": "Test Meter",
                "meter_categ_id": meter_category.id,
                "equipment_id": cls.equipment.id,
                "uom_id": cls.uom_unit.id,
            }
        )
        cls.report = cls.env["service.efficiency.report"]

    def _usage(self, meter_uom, counter_value, target_uom):
        self.meter.uom_id = meter_uom
        meter_class = type(self.env["service.meter"])
        with patch.object(meter_class, "get_counter_value", return_value=counter_value):
            return self.report.get_usage("2000-01-01", "2999-12-31", self.equipment.id, target_uom.id, False)

    def test_usage_dozen_to_unit(self):
        self.assertAlmostEqual(self._usage(self.uom_dozen, 2, self.uom_unit), 24)

    def test_usage_unit_to_dozen(self):
        self.assertAlmostEqual(self._usage(self.uom_unit, 24, self.uom_dozen), 2)

    def test_usage_same_uom(self):
        self.assertAlmostEqual(self._usage(self.uom_unit, 7, self.uom_unit), 7)
