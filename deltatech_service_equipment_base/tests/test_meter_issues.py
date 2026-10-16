# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from freezegun import freeze_time

from odoo import fields
from odoo.tests import Form, new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMeterIssues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom = cls.env.ref("uom.product_uom_unit")
        cls.counter_categ = cls.env["service.meter.category"].create(
            {"name": "Counter", "uom_id": cls.uom.id, "type": "counter"}
        )
        cls.collector_categ = cls.env["service.meter.category"].create(
            {"name": "Collector", "uom_id": cls.uom.id, "type": "collector"}
        )
        cls.equipment_type = cls.env["service.equipment.type"].create({"name": "Type"})
        cls.equipment_model = cls.env["service.equipment.model"].create({"name": "Model"})
        cls.equipment = cls._create_equipment("EQ-1")

    @classmethod
    def _create_equipment(cls, name):
        return cls.env["service.equipment"].create(
            {"name": name, "type_id": cls.equipment_type.id, "model_id": cls.equipment_model.id}
        )

    @classmethod
    def _create_meter(cls, equipment, categ):
        return cls.env["service.meter"].create(
            {"meter_categ_id": categ.id, "equipment_id": equipment.id, "uom_id": cls.uom.id}
        )

    def _read(self, meter, value, date):
        return self.env["service.meter.reading"].create(
            {
                "meter_id": meter.id,
                "equipment_id": meter.equipment_id.id,
                "counter_value": value,
                "date": date,
            }
        )

    # METER-001 (#170)
    def test_same_day_readings_keep_creation_order(self):
        meter = self._create_meter(self.equipment, self.counter_categ)
        first = self._read(meter, 100, "2024-01-10")
        second = self._read(meter, 120, "2024-01-10")
        third = self._read(meter, 150, "2024-01-10")
        self.assertEqual(first.previous_counter_value, 0)
        self.assertEqual(second.previous_counter_value, 100)
        self.assertEqual(second.difference, 20)
        self.assertEqual(third.previous_counter_value, 120)

        # recompute the earlier reading: it must not take a later same-day reading as predecessor
        first.write({"date": "2024-01-10"})
        self.env.add_to_compute(first._fields["previous_counter_value"], first)
        first.flush_recordset()
        self.assertEqual(first.previous_counter_value, 0)
        self.assertEqual(first.difference, 100)
        self.assertEqual(second.previous_counter_value, 100)
        self.assertEqual(second.difference, 20)
        self.assertEqual(third.difference, 30)

        # editing the earlier reading updates its same-day successor
        first.counter_value = 110
        first.flush_recordset()
        self.assertEqual(second.previous_counter_value, 110)
        self.assertEqual(second.difference, 10)
        self.assertEqual(meter.get_counter_value("2024-01-01", "2024-02-01"), 150)

    # METER-001 (#170): deleting a reading re-chains the next one
    def test_unlink_reading_updates_next_reading(self):
        meter = self._create_meter(self.equipment, self.counter_categ)
        self._read(meter, 100, "2024-01-10")
        middle = self._read(meter, 120, "2024-01-20")
        same_day = self._read(meter, 130, "2024-01-20")
        last = self._read(meter, 150, "2024-01-30")
        same_day.unlink()
        self.assertEqual(last.previous_counter_value, 120)
        self.assertEqual(last.difference, 30)
        middle.unlink()
        self.assertEqual(last.previous_counter_value, 100)
        self.assertEqual(last.difference, 50)
        self.assertEqual(meter.get_counter_value("2024-01-01", "2024-02-01"), 150)

    # METER-002 (#171)
    def test_collector_with_unread_counter(self):
        counter_read = self._create_meter(self.equipment, self.counter_categ)
        counter_unread = self._create_meter(self._create_equipment("EQ-2"), self.counter_categ)
        self._read(counter_read, 40, "2024-01-10")
        collector = self.env["service.meter"].create(
            {
                "meter_categ_id": self.collector_categ.id,
                "equipment_id": self._create_equipment("EQ-3").id,
                "uom_id": self.uom.id,
                "meter_ids": [(6, 0, [counter_read.id, counter_unread.id])],
            }
        )
        self.assertEqual(collector.total_counter_value, 40)

    # METER-003 (#172)
    def test_collector_total_follows_child_readings(self):
        counter = self._create_meter(self.equipment, self.counter_categ)
        reading = self._read(counter, 40, "2024-01-10")
        collector = self.env["service.meter"].create(
            {
                "meter_categ_id": self.collector_categ.id,
                "equipment_id": self._create_equipment("EQ-4").id,
                "uom_id": self.uom.id,
                "meter_ids": [(6, 0, counter.ids)],
            }
        )
        self.assertEqual(collector.total_counter_value, 40)

        later = self._read(counter, 70, "2024-01-20")
        self.assertEqual(collector.total_counter_value, 70)

        later.counter_value = 90
        self.assertEqual(collector.total_counter_value, 90)

        later.unlink()
        self.assertEqual(collector.total_counter_value, 40)

        reading.counter_value = 45
        self.assertEqual(collector.total_counter_value, 45)

    # METER-004 (#173)
    def test_wizard_default_date_is_not_frozen(self):
        self.assertTrue(callable(self.env["service.enter.reading"]._fields["date"].default))
        with freeze_time("2031-05-17 10:00:00"):
            wizard = Form(self.env["service.enter.reading"].with_context(active_ids=[]))
            self.assertEqual(wizard.date, fields.Date.to_date("2031-05-17"))

    # METER-005 (#174)
    def test_service_user_reads_equipment_operations(self):
        part = self.env["service.part"].create({"name": "Part"})
        check = self.env["service.check"].create({"name": "Check"})
        measurement = self.env["service.measurement"].create({"name": "Measurement"})
        self.equipment_type.write(
            {
                "part_template_ids": [(0, 0, {"part_id": part.id})],
                "check_template_ids": [(0, 0, {"check_id": check.id})],
                "measurement_template_ids": [(0, 0, {"measurement_id": measurement.id})],
            }
        )
        self.equipment.write(
            {
                "part_ids": [(0, 0, {"part_id": part.id})],
                "check_ids": [(0, 0, {"check_id": check.id})],
                "measurement_ids": [(0, 0, {"measurement_id": measurement.id})],
            }
        )
        user = new_test_user(
            self.env, login="service_user_174", groups="base.group_user,deltatech_service_base.group_service_user"
        )
        equipment = self.equipment.with_user(user)
        self.assertEqual(equipment.model_id.name, "Model")
        self.assertEqual(equipment.part_ids.part_id.name, "Part")
        self.assertEqual(equipment.check_ids.check_id.name, "Check")
        self.assertEqual(equipment.measurement_ids.measurement_id.name, "Measurement")
        self.assertEqual(equipment.type_id.part_template_ids.part_id, part)
        self.assertEqual(equipment.type_id.check_template_ids.check_id, check)
        self.assertEqual(equipment.type_id.measurement_template_ids.measurement_id, measurement)
        # the maintenance workflow ticks the lines on the equipment form
        equipment.part_ids.is_ok = True
        equipment.check_ids.is_ok = True
        equipment.measurement_ids.value = 3.5

        # any internal user can read the equipment model (public ACL pointed at the type)
        internal = new_test_user(self.env, login="internal_174", groups="base.group_user")
        self.assertEqual(self.equipment.with_user(internal).model_id.name, "Model")
