# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    service_location_id = fields.Many2one("service.location", string="Functional Location")
    service_equipment_id = fields.Many2one("service.equipment", string="Service Equipment")
    part_ids = fields.One2many("project.task.part", "task_id", string="Parts", copy=True)
    check_ids = fields.One2many("project.task.check", "task_id", string="Checks", copy=True)
    measurement_ids = fields.One2many("project.task.measurement", "task_id", string="Measurements", copy=True)

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

            check_list = []
            for equipment_check in self.service_equipment_id.check_ids:
                check_list.append(
                    (
                        0,
                        0,
                        {
                            "check_id": equipment_check.check_id.id,
                            "sequence": equipment_check.sequence,
                            "note": equipment_check.note,
                        },
                    )
                )
            self.check_ids = check_list

            measurement_list = []
            for equipment_measurement in self.service_equipment_id.measurement_ids:
                measurement_list.append(
                    (
                        0,
                        0,
                        {
                            "measurement_id": equipment_measurement.measurement_id.id,
                            "sequence": equipment_measurement.sequence,
                            "note": equipment_measurement.note,
                        },
                    )
                )
            self.measurement_ids = measurement_list


class ProjectTaskPart(models.Model):
    _name = "project.task.part"
    _description = "Project Task Part"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", related="task_id.service_equipment_id", store=True)
    part_id = fields.Many2one("service.part", string="Part", required=True)
    quantity = fields.Float(string="Quantity", default=1.0)
    note = fields.Text(string="Note")
    is_ok = fields.Boolean(string="Is OK")


class ProjectTaskCheck(models.Model):
    _name = "project.task.check"
    _description = "Project Task Check"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", related="task_id.service_equipment_id", store=True)
    check_id = fields.Many2one("service.check", string="Check", required=True)
    note = fields.Text(string="Note")
    is_ok = fields.Boolean(string="Is OK")


class ProjectTaskMeasurement(models.Model):
    _name = "project.task.measurement"
    _description = "Project Task Measurement"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", related="task_id.service_equipment_id", store=True)
    measurement_id = fields.Many2one("service.measurement", string="Measurement", required=True)
    value = fields.Float(string="Value")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", related="measurement_id.uom_id", readonly=True)
    note = fields.Text(string="Note")
    date_measurement = fields.Datetime(related="task_id.create_date", store=True, string="Data Măsurătorii")
