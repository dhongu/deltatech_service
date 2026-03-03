# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    task_count = fields.Integer(compute="_compute_task_history")
    part_history_count = fields.Integer(compute="_compute_task_history")
    check_history_count = fields.Integer(compute="_compute_task_history")
    measurement_history_count = fields.Integer(compute="_compute_task_history")

    def _compute_task_history(self):
        for equipment in self:
            equipment.task_count = self.env["project.task"].search_count([("service_equipment_id", "=", equipment.id)])
            equipment.part_history_count = self.env["project.task.part"].search_count(
                [("equipment_id", "=", equipment.id)]
            )
            equipment.check_history_count = self.env["project.task.check"].search_count(
                [("equipment_id", "=", equipment.id)]
            )
            equipment.measurement_history_count = self.env["project.task.measurement"].search_count(
                [("equipment_id", "=", equipment.id)]
            )

    def action_view_task_history(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_all_task")
        action["domain"] = [("service_equipment_id", "=", self.id)]
        action["context"] = {"default_service_equipment_id": self.id}
        return action

    def action_view_part_history(self):
        self.ensure_one()
        return {
            "name": self.env._("Part History"),
            "type": "ir.actions.act_window",
            "res_model": "project.task.part",
            "view_mode": "list,form",
            "domain": [("equipment_id", "=", self.id)],
            "context": {"default_equipment_id": self.id},
        }

    def action_view_check_history(self):
        self.ensure_one()
        return {
            "name": self.env._("Check History"),
            "type": "ir.actions.act_window",
            "res_model": "project.task.check",
            "view_mode": "list,form",
            "domain": [("equipment_id", "=", self.id)],
            "context": {"default_equipment_id": self.id},
        }

    def action_view_measurement_history(self):
        self.ensure_one()
        return {
            "name": self.env._("Measurement History"),
            "type": "ir.actions.act_window",
            "res_model": "project.task.measurement",
            "view_mode": "list,form",
            "domain": [("equipment_id", "=", self.id)],
            "context": {"default_equipment_id": self.id},
        }
