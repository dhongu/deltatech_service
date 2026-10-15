# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMaintenanceType(TransactionCase):
    """Operatiunile preluate pe sarcina se filtreaza dupa tipul de mentenanta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "Maintenance contracts"})
        MaintenanceType = cls.env["service.maintenance.type"]
        cls.spring = MaintenanceType.create({"name": "Spring"})
        cls.autumn = MaintenanceType.create({"name": "Autumn"})

        cls.part_all = cls.env["service.part"].create({"name": "Filter (always)"})
        cls.part_spring = cls.env["service.part"].create({"name": "Nozzle (spring)"})
        cls.check_autumn = cls.env["service.check"].create({"name": "Leak test (autumn)"})
        cls.meas_all = cls.env["service.measurement"].create({"name": "Pressure (always)"})

        cls.equipment = cls.env["service.equipment"].create(
            {
                "name": "Boiler",
                "part_ids": [
                    (0, 0, {"part_id": cls.part_all.id, "sequence": 1}),
                    (
                        0,
                        0,
                        {
                            "part_id": cls.part_spring.id,
                            "sequence": 2,
                            "maintenance_type_ids": [(6, 0, cls.spring.ids)],
                        },
                    ),
                ],
                "check_ids": [
                    (0, 0, {"check_id": cls.check_autumn.id, "maintenance_type_ids": [(6, 0, cls.autumn.ids)]}),
                ],
                "measurement_ids": [(0, 0, {"measurement_id": cls.meas_all.id})],
            }
        )

    def _task_form(self, maintenance_type=None):
        task_form = Form(self.env["project.task"])
        task_form.name = "Maintenance"
        task_form.project_id = self.project
        if maintenance_type:
            task_form.maintenance_type_id = maintenance_type
        task_form.service_equipment_id = self.equipment
        return task_form

    def test_without_type_all_operations(self):
        task = self._task_form().save()
        self.assertEqual(task.part_ids.part_id, self.part_all | self.part_spring)
        self.assertEqual(task.check_ids.check_id, self.check_autumn)
        self.assertEqual(task.measurement_ids.measurement_id, self.meas_all)

    def test_type_filters_operations(self):
        task = self._task_form(self.spring).save()
        self.assertEqual(task.part_ids.part_id, self.part_all | self.part_spring)
        self.assertFalse(task.check_ids, "the autumn check is not done in spring")
        self.assertEqual(task.measurement_ids.measurement_id, self.meas_all, "unmarked = all types")

        task = self._task_form(self.autumn).save()
        self.assertEqual(task.part_ids.part_id, self.part_all)
        self.assertEqual(task.check_ids.check_id, self.check_autumn)

    def test_type_change_refilters_untouched_task(self):
        task_form = self._task_form(self.spring)
        task_form.maintenance_type_id = self.autumn
        task = task_form.save()
        # the operations are replaced, not appended
        self.assertEqual(task.part_ids.part_id, self.part_all)
        self.assertEqual(len(task.part_ids), 1)
        self.assertEqual(task.check_ids.check_id, self.check_autumn)

    def test_type_change_keeps_worked_task(self):
        task_form = self._task_form(self.spring)
        with task_form.part_ids.edit(0) as line:
            line.is_ok = True
        task_form.maintenance_type_id = self.autumn
        task = task_form.save()
        # the work already recorded is not lost
        self.assertEqual(task.part_ids.part_id, self.part_all | self.part_spring)
        self.assertTrue(task.part_ids.filtered(lambda line: line.part_id == self.part_all).is_ok)

    def test_subtask_inherits_type(self):
        parent = self._task_form(self.spring).save()
        child = self.env["project.task"].create({"name": "Sub", "parent_id": parent.id, "project_id": self.project.id})
        self.assertEqual(child.maintenance_type_id, self.spring)
        child_ctx = (
            self.env["project.task"]
            .with_context(default_parent_id=parent.id)
            .create({"name": "Sub from context", "project_id": self.project.id})
        )
        self.assertEqual(child_ctx.maintenance_type_id, self.spring)
        explicit = self.env["project.task"].create(
            {
                "name": "Sub explicit",
                "parent_id": parent.id,
                "project_id": self.project.id,
                "maintenance_type_id": self.autumn.id,
            }
        )
        self.assertEqual(explicit.maintenance_type_id, self.autumn)

    def test_equipment_type_summary(self):
        equipment_type = self.env["service.equipment.type"].create({"name": "Boiler type"})
        self.equipment.type_id = equipment_type
        parent = self.env["project.task"].create(
            {"name": "Site", "project_id": self.project.id, "service_equipment_id": self.equipment.id}
        )
        self.env["project.task"].create(
            {
                "name": "Unit",
                "parent_id": parent.id,
                "project_id": self.project.id,
                "service_equipment_id": self.equipment.id,
            }
        )
        self.assertEqual(parent.equipment_type_summary, "2 x Boiler type")

    def test_team_follows_assignees(self):
        user = self.env["res.users"].create({"name": "Technician", "login": "svc_task_technician"})
        employee = self.env["hr.employee"].create({"name": "Technician", "user_id": user.id})
        task = self.env["project.task"].create({"name": "Assigned", "user_ids": [(6, 0, user.ids)]})
        self.assertEqual(task.employee_ids, employee)
        task.user_ids = [(5, 0, 0)]
        self.assertFalse(task.employee_ids)

    def test_template_types_copied_to_equipment(self):
        """Marcajul din sablonul tipului de echipament ajunge pe liniile echipamentului."""
        Equipment = self.env["service.equipment"]
        base_hook = any(
            "_values_from_type_templates" in vars(cls)
            for cls in type(Equipment).__mro__
            if cls.__module__.startswith("odoo.addons.deltatech_service_equipment_base")
        )
        if not base_hook:
            self.skipTest("deltatech_service_equipment_base has no _values_from_type_templates hook yet")
        equipment_type = self.env["service.equipment.type"].create({"name": "Typed"})
        self.env["service.part.template"].create(
            {
                "part_id": self.part_spring.id,
                "equipment_type_id": equipment_type.id,
                "maintenance_type_ids": [(6, 0, self.spring.ids)],
            }
        )
        equipment_form = Form(Equipment)
        equipment_form.name = "From template"
        equipment_form.type_id = equipment_type
        equipment = equipment_form.save()
        self.assertEqual(equipment.part_ids.maintenance_type_ids, self.spring)
