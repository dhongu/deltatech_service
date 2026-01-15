from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
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

    def test_task_history(self):
        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task 1"
        task_form.service_equipment_id = self.equipment
        task1 = task_form.save()

        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task 2"
        task_form.service_equipment_id = self.equipment
        task2 = task_form.save()

        self.equipment._compute_task_history()
        self.assertEqual(self.equipment.task_count, 2)
        # Each task should have 1 check and 1 measurement copied from equipment
        self.assertEqual(self.equipment.check_history_count, 2)
        self.assertEqual(self.equipment.measurement_history_count, 2)

        # Check action methods
        action_task = self.equipment.action_view_task_history()
        self.assertEqual(action_task["res_model"], "project.task")

        action_check = self.equipment.action_view_check_history()
        self.assertEqual(action_check["res_model"], "project.task.check")

        action_meas = self.equipment.action_view_measurement_history()
        self.assertEqual(action_meas["res_model"], "project.task.measurement")
