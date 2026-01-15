# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


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
