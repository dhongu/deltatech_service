# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    service_location_id = fields.Many2one("service.location", string="Functional Location")
    service_equipment_id = fields.Many2one("service.equipment", string="Service Equipment")
    part_ids = fields.One2many("project.task.part", "task_id", string="Parts", copy=True)

    @api.onchange("service_location_id")
    def _onchange_service_location_id(self):
        if self.service_location_id and self.service_location_id.partner_id:
            self.partner_id = self.service_location_id.partner_id

    @api.onchange("service_equipment_id")
    def _onchange_service_equipment_id(self):
        if self.service_equipment_id:
            if self.service_equipment_id.service_location_id:
                self.service_location_id = self.service_equipment_id.service_location_id
            if self.service_equipment_id.partner_id:
                self.partner_id = self.service_equipment_id.partner_id

            part_list = []
            for equipment_part in self.service_equipment_id.part_ids:
                part_list.append(
                    (
                        0,
                        0,
                        {
                            "part_id": equipment_part.part_id.id,
                            "quantity": equipment_part.quantity,
                            "sequence": equipment_part.sequence,
                            "note": equipment_part.note,
                        },
                    )
                )
            self.part_ids = part_list


class ProjectTaskPart(models.Model):
    _name = "project.task.part"
    _description = "Project Task Part"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    part_id = fields.Many2one("service.part", string="Part", required=True)
    quantity = fields.Float(string="Quantity", default=1.0)
    note = fields.Text(string="Note")
    is_ok = fields.Boolean(string="Is OK")
