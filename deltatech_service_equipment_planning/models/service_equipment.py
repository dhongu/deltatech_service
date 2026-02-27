# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    resource_id = fields.Many2one("resource.resource", string="Resource", readonly=True)

    def generate_resource_for_equipment(self):
        if not self.resource_id:
            self.resource_id = self.env["resource.resource"].create(
                {
                    "name": self.name,
                    "resource_type": "material",
                }
            )

    def action_view_planning(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "project_forecast.project_forecast_action_schedule_by_employee"
        )
        action["context"] = {
            "search_default_resource_id": self.resource_id.id,
        }
        action["domain"] = [("resource_id", "=", self.resource_id.id), ("resource_id", "!=", False)]
        return action
