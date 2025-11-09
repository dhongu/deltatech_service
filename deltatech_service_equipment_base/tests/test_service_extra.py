# © 2025 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import Form

from odoo.addons.deltatech_service_equipment_base.tests.test_service import TestService


class TestServiceExtra(TestService):
    def setUp(self):
        super().setUp()
        # Minimal equipment + meter to reuse in multiple tests
        self.equipment = self.env["service.equipment"].create(
            {
                "name": "EQ-Base-Extra",
                "type_id": self.equipment_type.id,
                "model_id": self.equipment_model.id,
            }
        )
        self.meter = self.env["service.meter"].create(
            {
                "name": "MT-Base-Extra",
                "meter_categ_id": self.meter_category.id,
                "equipment_id": self.equipment.id,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

    def _create_reading(self, meter, value, date):
        return self.env["service.meter.reading"].create(
            {
                "meter_id": meter.id,
                "equipment_id": meter.equipment_id.id,
                "counter_value": value,
                "date": date,
            }
        )

    def test_enter_readings_default_get_and_onchange(self):
        # create a baseline reading so total_counter_value is known
        self._create_reading(self.meter, 10, "2024-01-01")

        wiz = Form(self.env["service.enter.reading"].with_context(active_ids=[self.equipment.id]))
        # default_get should pre-fill one item for our meter with estimated value
        wiz = wiz.save()
        self.assertEqual(len(wiz.items), 1)
        item = wiz.items[0]
        # estimated_value falls back to total_counter_value when no coef -> 10
        self.assertEqual(item.counter_value, 10)

        # Changing date should recompute estimated to current forecast (still 10)
        wiz = wiz.with_context(active_ids=[self.equipment.id])
        wiz.date = "2024-02-01"
        wiz.onchange_date()
        self.assertEqual(wiz.items[0].counter_value, self.meter.with_context(date=wiz.date).estimated_value)

    def test_enter_readings_do_enter_creates_readings(self):
        self._create_reading(self.meter, 5, "2024-01-01")

        wiz = Form(self.env["service.enter.reading"].with_context(active_ids=[self.equipment.id]))
        wiz.date = "2024-01-15"
        wiz = wiz.save()
        # adjust the only item value
        wiz.items[0].counter_value = 7
        wiz.do_enter()

        readings = self.env["service.meter.reading"].search([("meter_id", "=", self.meter.id)])
        self.assertEqual(len(readings), 2)
        # verify previous_counter_value/difference computed
        prev = self.env["service.meter.reading"].search([("date", "=", "2024-01-01"), ("meter_id", "=", self.meter.id)])
        curr = self.env["service.meter.reading"].search([("date", "=", "2024-01-15"), ("meter_id", "=", self.meter.id)])
        self.assertEqual(curr.previous_counter_value, prev.counter_value)
        self.assertEqual(curr.difference, curr.counter_value - prev.counter_value)

    def test_enter_readings_compute_error_messages(self):
        # create a future reading and set total at 100
        self._create_reading(self.meter, 100, "2024-01-10")
        self._create_reading(self.meter, 120, "2024-02-10")  # future vs 2024-02-01 wizard date

        wiz = Form(self.env["service.enter.reading"].with_context(active_ids=[self.equipment.id]))
        wiz.date = "2024-02-01"
        wiz = wiz.save()
        # set a too-small value (<= total_counter_value)
        wiz.items[0].counter_value = 90
        wiz._compute_error()
        self.assertIn("has readings in the future", wiz.error)
        self.assertIn("must be greater than", wiz.error)

    def test_meter_forecast_and_getters(self):
        # create an increasing series so regression has a slope
        self._create_reading(self.meter, 10, "2024-01-01")
        self._create_reading(self.meter, 20, "2024-02-01")
        self.meter.calc_forecast_coef()
        # coefficients stored
        self.assertNotEqual(self.meter.value_a, 0.0)
        # forecast for a later date should be >= last value (monotonic trend)
        f = self.meter.get_forcast("2024-03-01")
        self.assertGreaterEqual(f, 20)
        # inverse date for a value greater than last should return a date
        fd = self.meter.get_forcast_date(25)
        self.assertTrue(fd)

    def test_recheck_value_updates_previous_and_difference(self):
        # out-of-order creates
        r2 = self._create_reading(self.meter, 20, "2024-02-01")
        r1 = self._create_reading(self.meter, 10, "2024-01-01")
        # trigger recompute
        self.meter.recheck_value()
        r1.invalidate_recordset()
        r2.invalidate_recordset()
        self.assertEqual(r1.previous_counter_value, 0.0)  # start_value default 0
        self.assertEqual(r1.difference, 10.0)
        self.assertEqual(r2.previous_counter_value, 10.0)
        self.assertEqual(r2.difference, 10.0)

    def test_meter_reading_onchange_sets_equipment(self):
        reading = Form(self.env["service.meter.reading"])  # no equipment set
        reading.meter_id = self.meter
        # Form triggers onchange automatically when setting fields
        self.assertEqual(reading.equipment_id, self.equipment)

    def test_wizard_handles_equipment_without_meters(self):
        # create separate equipment with no meters
        eq2 = self.env["service.equipment"].create(
            {
                "name": "EQ-Empty",
                "type_id": self.equipment_type.id,
                "model_id": self.equipment_model.id,
            }
        )
        wiz = Form(self.env["service.enter.reading"].with_context(active_ids=[eq2.id]))
        wiz = wiz.save()
        self.assertFalse(wiz.items)
