# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    travel_distance_product_id = fields.Many2one(
        "product.product",
        string="Travel Distance Product",
        domain=[("type", "=", "service")],
        config_parameter="deltatech_project_task_travel.travel_distance_product_id",
    )
    travel_time_product_id = fields.Many2one(
        "product.product",
        string="Travel Time Product",
        domain=[("type", "=", "service")],
        config_parameter="deltatech_project_task_travel.travel_time_product_id",
    )
