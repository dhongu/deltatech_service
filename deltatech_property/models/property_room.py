# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

selection_level = [("p", "P"), ("m", "M"), ("s", "S")] + [(str(num), str(num)) for num in range(1, 30)]


class PropertyRoom(models.Model):
    _name = "property.room"
    _description = "Room"

    name = fields.Char(string="Number")
    building_id = fields.Many2one("property.building", string="Building", required=True)

    level = fields.Selection(selection_level)

    height = fields.Float()
    perimeter = fields.Float()
    surface_disinsection = fields.Float(
        string="Area of disinsection",
        compute="_compute_surface_disinsection",
        store=True,
    )

    surface = fields.Float("Surface area")
    surface_cleaning_floor = fields.Float(string="Surface cleaning floor")
    surface_cleaning_doors = fields.Float(string="Surface cleaning doors")
    surface_cleaning_windows = fields.Float(string="Surface cleaning window")

    floor_type = fields.Selection([("c", "Carpet"), ("l", "Linoleum"), ("w", "Wood")])

    usage = fields.Selection(
        [
            ("office", "Office"),
            ("meeting", "Meeting room"),
            ("kitchen", "Kitchen"),
            ("laboratory", "Laboratory"),
            ("garage", "Garage"),
            ("archive", "Archive"),
            ("warehouse", "Warehouse"),
            ("log_warehouse", "Logistics warehouse"),
            ("it_endowments", "IT endowments (Ranks, Hall Servers)"),
            (
                "premises",
                "Technical premises (thermal, air conditioning, post-transformer)",
            ),
            ("cloakroom", "Cloakroom"),
            ("sanitary", "Sanitary group"),
            ("access", "Access ways"),
            ("lobby", "Lobby"),
            ("staircase", "Staircase"),
            ("living", "Living Room"),
            ("bedroom", "Bedroom"),
            ("balcony", "Balcony"),
        ],
        string="Room usage",
        help="The purpose of using the room",
        default="bedroom",
    )
    usage_id = fields.Many2one("room.usage", string="Room usage type", help="The purpose of using the room")

    rented_room = fields.Boolean()
    tenant_id = fields.Many2one("res.partner", string="Tenant")

    last_maintenance = fields.Date()
    technical_condition = fields.Selection(
        [("0", "Missing"), ("1", "Unsatisfactory"), ("3", "good"), ("5", "very good")],
        aggregator="avg",
    )

    @api.depends("surface", "height", "perimeter")
    def _compute_surface_disinsection(self):
        for room in self:
            room.surface_disinsection = 2 * room.surface + room.height * room.perimeter

    @api.constrains("surface_cleaning_floor", "surface")
    def _check_cleaning_surface(self):
        for room in self:
            if float_compare(room.surface_cleaning_floor, room.surface, precision_digits=2) > 0:
                raise ValidationError(
                    self.env._(
                        "The floor cleaning area of room %(room)s cannot be greater than its surface area.",
                        room=room.display_name,
                    )
                )


class RoomUsage(models.Model):
    _name = "room.usage"
    _description = "Room usage"

    name = fields.Char(string="Usage")
