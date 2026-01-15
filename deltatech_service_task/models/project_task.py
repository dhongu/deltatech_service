# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    service_location_id = fields.Many2one(
        "service.location", string="Functional Location", domain="[('partner_id', '=', partner_id)]"
    )
    service_equipment_id = fields.Many2one(
        "service.equipment", string="Service Equipment", domain="[('service_location_id', '=', service_location_id)]"
    )

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
