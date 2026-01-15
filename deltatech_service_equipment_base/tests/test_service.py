# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestService(TransactionCase):
    def setUp(self):
        super().setUp()
        self.meter_category = self.env["service.meter.category"].create(
            {
                "name": "Test Meter Category",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        self.equipment_type = self.env["service.equipment.type"].create(
            {
                "name": "Test Equipment Type",
            }
        )
        self.equipment_model = self.env["service.equipment.model"].create(
            {
                "name": "Test Equipment Model",
            }
        )

    def test_create_equipment(self):
        equipment = Form(self.env["service.equipment"])
        equipment.name = "Test Equipment"
        equipment.type_id = self.equipment_type
        equipment.model_id = self.equipment_model
        equipment = equipment.save()

        meter = Form(self.env["service.meter"])
        meter.name = "Test Meter"
        meter.meter_categ_id = self.meter_category
        meter.equipment_id = equipment
        meter = meter.save()

        meter_reading = Form(self.env["service.meter.reading"])
        meter_reading.meter_id = meter
        meter_reading.counter_value = 100
        meter_reading.date = "2020-01-01"
        meter_reading.save()

        meter_reading = Form(self.env["service.meter.reading"])
        meter_reading.meter_id = meter
        meter_reading.counter_value = 200
        meter_reading.date = "2020-01-02"
        meter_reading.save()

        wizard_enter_readings = Form(self.env["service.enter.reading"].with_context(active_ids=[equipment.id]))
        wizard_enter_readings.date = "2020-01-03"
        wizard_enter_readings = wizard_enter_readings.save()
        wizard_enter_readings.do_enter()

        meter.calc_forecast_coef()
        meter.recheck_value()

    def test_equipment_parts(self):
        part1 = self.env["service.part"].create({"name": "Test Part 1"})
        part2 = self.env["service.part"].create({"name": "Test Part 2"})
        self.env["service.part.template"].create(
            {
                "name": "Test Part Template 1",
                "part_id": part1.id,
                "equipment_type_id": self.equipment_type.id,
                "sequence": 20,
            }
        )
        self.env["service.part.template"].create(
            {
                "name": "Test Part Template 2",
                "part_id": part2.id,
                "equipment_type_id": self.equipment_type.id,
                "sequence": 10,
                "note": "Test Note 2",
            }
        )

        equipment_form = Form(self.env["service.equipment"])
        equipment_form.name = "Test Equipment with Parts"
        equipment_form.type_id = self.equipment_type
        equipment = equipment_form.save()

        self.assertEqual(len(equipment.part_ids), 2, "Two parts should have been generated")
        # Ordering is by sequence, id. So sequence 10 should be first.
        self.assertEqual(equipment.part_ids[0].part_id, part2, "The first part should be part 2 (sequence 10)")
        self.assertEqual(equipment.part_ids[1].part_id, part1, "The second part should be part 1 (sequence 20)")
        self.assertEqual(equipment.part_ids[0].sequence, 10)
        self.assertEqual(equipment.part_ids[1].sequence, 20)
        self.assertEqual(equipment.part_ids[0].note, "Test Note 2")

    def test_equipment_checks_measurements(self):
        check1 = self.env["service.check"].create({"name": "Test Check 1"})
        self.env["service.check.template"].create(
            {
                "check_id": check1.id,
                "equipment_type_id": self.equipment_type.id,
                "sequence": 10,
                "note": "Test Check Note",
            }
        )

        uom_unit = self.env.ref("uom.product_uom_unit")
        meas1 = self.env["service.measurement"].create({"name": "Test Meas 1", "uom_id": uom_unit.id})
        self.env["service.measurement.template"].create(
            {
                "measurement_id": meas1.id,
                "equipment_type_id": self.equipment_type.id,
                "sequence": 10,
                "note": "Test Meas Note",
            }
        )

        equipment_form = Form(self.env["service.equipment"])
        equipment_form.name = "Test Equipment Checks"
        equipment_form.type_id = self.equipment_type
        equipment = equipment_form.save()

        self.assertEqual(len(equipment.check_ids), 1)
        self.assertEqual(equipment.check_ids[0].check_id, check1)
        self.assertEqual(equipment.check_ids[0].note, "Test Check Note")

        self.assertEqual(len(equipment.measurement_ids), 1)
        self.assertEqual(equipment.measurement_ids[0].measurement_id, meas1)
        self.assertEqual(equipment.measurement_ids[0].uom_id, uom_unit)

    def test_create_location(self):
        location = Form(self.env["service.location"])
        location.name = "Test Location"
        location = location.save()
