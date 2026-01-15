from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProjectTask(TransactionCase):
    def setUp(self):
        super().setUp()
        self.equipment_type = self.env["service.equipment.type"].create({"name": "Test Type"})
        self.part1 = self.env["service.part"].create({"name": "Part 1"})
        self.check1 = self.env["service.check"].create({"name": "Check 1"})
        self.meas1 = self.env["service.measurement"].create({"name": "Meas 1"})

        self.env["service.part.template"].create(
            {"part_id": self.part1.id, "equipment_type_id": self.equipment_type.id}
        )
        self.env["service.check.template"].create(
            {"check_id": self.check1.id, "equipment_type_id": self.equipment_type.id}
        )
        self.env["service.measurement.template"].create(
            {"measurement_id": self.meas1.id, "equipment_type_id": self.equipment_type.id}
        )

        self.equipment = self.env["service.equipment"].create({"name": "Test Equipment", "type_id": self.equipment_type.id})
        # Trigger onchange manually or assume it worked (in tests create doesn't trigger onchange unless via Form)
        # Using Form for equipment to trigger onchange_type_id
        equipment_form = Form(self.env["service.equipment"])
        equipment_form.name = "Test Equipment Form"
        equipment_form.type_id = self.equipment_type
        self.equipment = equipment_form.save()

    def test_task_population(self):
        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task"
        task_form.service_equipment_id = self.equipment
        task = task_form.save()

        self.assertEqual(len(task.part_ids), 1)
        self.assertEqual(len(task.check_ids), 1)
        self.assertEqual(len(task.measurement_ids), 1)
        self.assertEqual(task.part_ids[0].part_id, self.part1)
        self.assertEqual(task.check_ids[0].check_id, self.check1)
        self.assertEqual(task.measurement_ids[0].measurement_id, self.meas1)
