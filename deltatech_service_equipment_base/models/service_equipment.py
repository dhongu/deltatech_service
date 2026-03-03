# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ServiceEquipment(models.Model):
    _name = "service.equipment"
    _description = "Service Equipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Reference", index=True, default=lambda self: self.env._("New"))
    # display_name = fields.Char(compute="_compute_display_name")
    partner_id = fields.Many2one("res.partner", string="Customer")
    contact_id = fields.Many2one(
        "res.partner",
        string="Contact Person",
        tracking=True,
        domain=[("type", "=", "contact"), ("is_company", "=", False)],
    )
    service_location_id = fields.Many2one("service.location", string="Functional Location")

    note = fields.Text(string="Notes")
    type_id = fields.Many2one("service.equipment.type", required=False, string="Type")
    model_id = fields.Many2one("service.equipment.model", required=False, string="Model")

    internal_type = fields.Selection([("equipment", "Equipment")], default="equipment")
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        ondelete="restrict",
        domain=[("is_storable", "=", True)],
    )

    serial_id = fields.Many2one("stock.lot", string="Product Serial Number", ondelete="restrict", copy=False)
    serial_no = fields.Char("Serial Number", copy=False)
    storage_place = fields.Many2one(
        "stock.location",
        string="Storage Place",
        related="serial_id.location_id",
        store=True,
        readonly=True,
    )

    vendor_id = fields.Many2one("res.partner", string="Vendor")
    manufacturer_id = fields.Many2one("res.partner", string="Manufacturer")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    technician_user_id = fields.Many2one("res.users", string="Responsible", tracking=True)

    meter_ids = fields.One2many("service.meter", "equipment_id", string="Meters", copy=True)
    part_ids = fields.One2many("service.equipment.part", "equipment_id", string="Parts", copy=True)
    check_ids = fields.One2many("service.equipment.check", "equipment_id", string="Checks", copy=True)
    measurement_ids = fields.One2many("service.equipment.measurement", "equipment_id", string="Measurements", copy=True)
    state = fields.Selection(
        [
            ("active", "Active"),
            ("defect", "Defect"),
            ("in_repair", "In Repair"),
            ("disposed", "Disposed"),
            ("reserved", "Reserved"),
            ("lost", "Lost"),
        ],
        tracking=True,
        readonly=False,
        copy=False,
    )
    property_type = fields.Selection(
        [
            ("owned", "Owned"),
            ("rented", "Rented"),
            ("borrowed", "Borrowed"),
        ],
        string="Property Type",
        tracking=True,
        copy=False,
    )
    inventory_no = fields.Char(string="Inventory Number", tracking=True, copy=False)

    def action_view_stock_move_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_line_action")
        action["domain"] = [("product_id", "in", self.product_id.id), ("lot_id", "=", self.serial_id.id)]
        return action

    @api.onchange("type_id")
    def onchange_type_id(self):
        if self.type_id:
            part_list = []
            for part_template in self.type_id.part_template_ids:
                part_list.append(
                    (
                        0,
                        0,
                        {
                            "part_id": part_template.part_id.id,
                            "quantity": 1.0,
                            "sequence": part_template.sequence,
                            "note": part_template.note,
                        },
                    )
                )
            self.part_ids = part_list

            check_list = []
            for check_template in self.type_id.check_template_ids:
                check_list.append(
                    (
                        0,
                        0,
                        {
                            "check_id": check_template.check_id.id,
                            "sequence": check_template.sequence,
                            "note": check_template.note,
                        },
                    )
                )
            self.check_ids = check_list

            measurement_list = []
            for measurement_template in self.type_id.measurement_template_ids:
                measurement_list.append(
                    (
                        0,
                        0,
                        {
                            "measurement_id": measurement_template.measurement_id.id,
                            "sequence": measurement_template.sequence,
                            "note": measurement_template.note,
                        },
                    )
                )
            self.measurement_ids = measurement_list

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", self.env._("New")) == self.env._("New") or vals.get("name") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("service.equipment") or self.env._("New")
        return super().create(vals_list)

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            domain = [("product_id", "=", self.product_id.id)]
        else:
            domain = []
        return {"domain": {"serial_id": domain}}

    @api.onchange("serial_id")
    def onchange_serial_id(self):
        if self.serial_id:
            self.serial_no = self.serial_id.name

    def _compute_display_name(self):
        for equipment in self:
            display_name = equipment.name
            if equipment.serial_id:
                display_name += " / " + equipment.serial_id.name
            equipment.display_name = display_name

    # def name_get(self):
    #     res = []
    #     for equipment in self:
    #         name = equipment.name
    #         if equipment.serial_id:
    #             name += "/" + equipment.serial_id.name
    #         res.append((equipment.id, name))
    #     return res

    def update_meter_status(self):
        pass

    # la modificarea locului functiona se aduc datele la nivel de echipament
    @api.onchange("service_location_id")
    def onchange_service_location_id(self):
        if self.service_location_id:
            self.partner_id = self.service_location_id.partner_id.id
            self.contact_id = self.service_location_id.contact_id.id
            self.technician_user_id = self.service_location_id.technician_user_id.id
