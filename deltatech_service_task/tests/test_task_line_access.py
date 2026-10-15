# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTaskLineAccess(TransactionCase):
    """TASK-001: parts / checks / measurements follow the access of their task."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Task Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Task Company B"})
        cls.user = new_test_user(
            cls.env,
            login="task_line_user_a",
            groups="base.group_user,project.group_project_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.part = cls.env["service.part"].create({"name": "Filter"})
        cls.check = cls.env["service.check"].create({"name": "Pressure"})
        cls.measurement = cls.env["service.measurement"].create({"name": "Temperature"})

        Project = cls.env["project.project"]
        cls.project_a = Project.create(
            {"name": "Open A", "company_id": cls.company_a.id, "privacy_visibility": "employees"}
        )
        cls.project_b = Project.create(
            {"name": "Open B", "company_id": cls.company_b.id, "privacy_visibility": "employees"}
        )
        cls.project_private = Project.create(
            {"name": "Private A", "company_id": cls.company_a.id, "privacy_visibility": "followers"}
        )
        cls.task_a = cls._create_task(cls.project_a)
        cls.task_b = cls._create_task(cls.project_b)
        cls.task_private = cls._create_task(cls.project_private)

    @classmethod
    def _create_task(cls, project):
        return cls.env["project.task"].create(
            {
                "name": f"Task {project.name}",
                "project_id": project.id,
                "company_id": project.company_id.id,
                "part_ids": [(0, 0, {"part_id": cls.part.id, "note": "secret note"})],
                "check_ids": [(0, 0, {"check_id": cls.check.id})],
                "measurement_ids": [(0, 0, {"measurement_id": cls.measurement.id, "value": 42})],
            }
        )

    def _lines(self, task):
        return {
            "project.task.part": task.part_ids,
            "project.task.check": task.check_ids,
            "project.task.measurement": task.measurement_ids,
        }

    def test_search_only_lines_of_readable_tasks(self):
        for model in ("project.task.part", "project.task.check", "project.task.measurement"):
            all_lines = (
                self._lines(self.task_a)[model]
                | self._lines(self.task_b)[model]
                | self._lines(self.task_private)[model]
            )
            found = self.env[model].with_user(self.user).search([("id", "in", all_lines.ids)])
            self.assertEqual(found, self._lines(self.task_a)[model], model)
            self.assertEqual(self.env[model].with_user(self.user).search_count([("id", "in", all_lines.ids)]), 1, model)

    def test_read_write_unlink_other_company(self):
        self._assert_lines_locked(self.task_b)

    def test_read_write_unlink_private_project(self):
        self._assert_lines_locked(self.task_private)

    def _assert_lines_locked(self, task):
        for model, lines in self._lines(task).items():
            lines_as_user = lines.with_user(self.user)
            with self.assertRaises(AccessError, msg=model):
                lines_as_user.read(["note"])
            with self.assertRaises(AccessError, msg=model):
                lines_as_user.write({"note": "changed"})
            with self.assertRaises(AccessError, msg=model):
                lines_as_user.unlink()
            self.assertTrue(lines.exists(), model)
            self.assertNotEqual(lines.note, "changed", model)

    def test_create_and_move_to_forbidden_task(self):
        Part = self.env["project.task.part"].with_user(self.user)
        with self.assertRaises(AccessError):
            Part.create({"task_id": self.task_b.id, "part_id": self.part.id})
        with self.assertRaises(AccessError):
            Part.create({"task_id": self.task_private.id, "part_id": self.part.id})
        own_line = self.task_a.part_ids.with_user(self.user)
        with self.assertRaises(AccessError):
            own_line.write({"task_id": self.task_b.id})
        self.assertEqual(self.task_a.part_ids.task_id, self.task_a)

    def test_lines_of_accessible_task_still_editable(self):
        lines = self._lines(self.task_a)
        for model, line in lines.items():
            line_as_user = line.with_user(self.user)
            line_as_user.read(["note"])
            line_as_user.write({"note": "ok"})
            self.assertEqual(line.note, "ok", model)
        new_part = (
            self.env["project.task.part"]
            .with_user(self.user)
            .create({"task_id": self.task_a.id, "part_id": self.part.id})
        )
        new_part.unlink()
        # editing through the task form (one2many commands) keeps working
        self.task_a.with_user(self.user).write({"part_ids": [(5, 0, 0), (0, 0, {"part_id": self.part.id})]})
        self.assertEqual(len(self.task_a.part_ids), 1)
