from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProjectTask(TransactionCase):
    def setUp(self):
        super().setUp()
        self.equipment_type = self.env["service.equipment.type"].create({"name": "Test Type"})
        self.part1 = self.env["service.part"].create({"name": "Part 1"})
        self.env["service.part.template"].create(
            {"part_id": self.part1.id, "equipment_type_id": self.equipment_type.id, "sequence": 10, "note": "Note 1"}
        )

        self.equipment = self.env["service.equipment"].create(
            {
                "name": "Test Equipment",
                "type_id": self.equipment_type.id,
            }
        )
        # Trigger onchange on equipment to populate equipment parts
        self.equipment.onchange_type_id()

    def test_task_parts_generation(self):
        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task"
        task_form.service_equipment_id = self.equipment
        task = task_form.save()

        self.assertEqual(len(task.part_ids), 1, "Task should have one part")
        self.assertEqual(task.part_ids[0].part_id, self.part1)
        self.assertEqual(task.part_ids[0].sequence, 10)
        self.assertEqual(task.part_ids[0].note, "Note 1")
