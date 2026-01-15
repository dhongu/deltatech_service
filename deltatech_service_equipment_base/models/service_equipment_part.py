# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ServiceEquipmentPart(models.Model):
    _name = "service.equipment.part"
    _description = "Service Equipment Part"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    equipment_id = fields.Many2one("service.equipment", string="Equipment", required=True, ondelete="cascade")
    part_id = fields.Many2one("service.part", string="Part", required=True)
    quantity = fields.Float(string="Quantity", default=1.0)
    note = fields.Text(string="Note")
    is_ok = fields.Boolean(string="Is OK")


class ServiceEquipmentCheck(models.Model):
    _name = "service.equipment.check"
    _description = "Service Equipment Check"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    equipment_id = fields.Many2one("service.equipment", string="Equipment", required=True, ondelete="cascade")
    check_id = fields.Many2one("service.check", string="Check", required=True)
    note = fields.Text(string="Note")
    is_ok = fields.Boolean(string="Is OK")


class ServiceEquipmentMeasurement(models.Model):
    _name = "service.equipment.measurement"
    _description = "Service Equipment Measurement"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    equipment_id = fields.Many2one("service.equipment", string="Equipment", required=True, ondelete="cascade")
    measurement_id = fields.Many2one("service.measurement", string="Measurement", required=True)
    value = fields.Float(string="Value")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", related="measurement_id.uom_id", readonly=True)
    note = fields.Text(string="Note")
