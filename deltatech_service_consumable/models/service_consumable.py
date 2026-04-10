# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import RedirectWarning
from odoo.tools.safe_eval import safe_eval


class ServiceEquipmentType(models.Model):
    _inherit = "service.equipment.type"

    consumable_item_ids = fields.One2many("service.consumable.item", "type_id", string="Consumables")


class ServiceConsumableItem(models.Model):
    _name = "service.consumable.item"
    _description = "Consumable Item"

    # transient field to hold the current equipment when rendered from equipment form
    equipment_id = fields.Many2one(
        "service.equipment",
        string="Equipment (view)",
        compute="_compute_equipment_id_view",
        store=False,
        help="Set when this consumable is rendered under an Equipment form.",
    )
    name = fields.Char(string="Name", related="product_id.name")
    type_id = fields.Many2one("service.equipment.type", string="Type", ondelete="cascade")
    product_id = fields.Many2one(
        "product.product",
        string="Consumable",
        ondelete="restrict",
        domain=[("is_storable", "=", True)],
    )
    quantity = fields.Float(
        string="Quantity", compute="_compute_quantity", digits="Product Unit of Measure", compute_sudo=True
    )
    shelf_life = fields.Float(string="Shelf Life", related="product_id.shelf_life")
    uom_shelf_life = fields.Many2one(string="Shelf Life UoM", related="product_id.uom_shelf_life")
    colors = fields.Char("HTML Colors Index", default="['#a9d70b', '#f9c802', '#ff0000']")
    max_qty = fields.Float(
        string="Quantity Max",
        digits="Product Unit of Measure",
        help="Maximum Quantity allowed",
    )

    def _compute_equipment_id_view(self):
        eq_id = self.env.context.get("equipment_id")
        equipment = self.env["service.equipment"].browse(eq_id) if eq_id else self.env["service.equipment"]
        for rec in self:
            rec.equipment_id = equipment

    def _compute_quantity(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        # todo: se pus acest tip intr-un camp din companie
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))
        if not picking_type_id:
            action = self.env.ref("stock.action_stock_config_settings").sudo()
            raise RedirectWarning(self.env._("Please define the picking type for service."), action.id, self.env._("Stock Settings"))

        equipment_id = self.env.context.get("equipment_id") or (self.equipment_id.id if self.equipment_id else False)
        pickings = self.env["stock.picking"]
        if equipment_id:
            pickings = (
                self.env["stock.picking"]
                .sudo()
                .search(
                    [
                        ("equipment_id", "=", equipment_id),
                        ("picking_type_id", "=", picking_type_id),
                        ("state", "=", "done"),
                    ]
                )
            )

        for item in self:
            if equipment_id:
                move_lines = (
                    self.env["stock.move"]
                    .sudo()
                    .search(
                        [
                            ("picking_id", "in", pickings.ids),
                            ("product_id", "=", item.product_id.id),
                        ]
                    )
                )
                move_qtys = 0.0
                for move in move_lines:
                    if move.location_dest_id.usage == "internal":
                        move_qtys += -move.product_id.shelf_life * move.product_uom_qty
                    else:
                        move_qtys += move.product_id.shelf_life * move.product_uom_qty

                eff = self.env["service.efficiency.report"]
                res = eff.read_group(
                    domain=[("product_id", "=", item.product_id.id), ("equipment_id", "=", equipment_id)],
                    fields=["equipment_id", "product_id", "location_dest_id", "usage", "shelf_life"],
                    groupby=["equipment_id", "product_id", "location_dest_id"],
                    lazy=False,
                )
                usage = next((line["usage"] for line in res), 0.0)
                item.quantity = move_qtys - usage
            else:
                item.quantity = 0
