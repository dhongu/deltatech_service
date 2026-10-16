# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import Command, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    notification_id = fields.Many2one("service.notification", string="Notification", readonly=True)
    service_order_id = fields.Many2one("service.order", string="Service Order", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        notification_id = self.env.context.get("notification_id", False)
        for vals in vals_list:
            if notification_id:
                vals["notification_id"] = notification_id

        res = super().create(vals_list)
        notification_id = self.env.context.get("notification_id", False)
        if notification_id and res:
            notification = self.env["service.notification"].browse(notification_id)
            notification.write({"sale_order_id": res[0].id})
        return res

    def new_notification(self):
        self.ensure_one()
        context = {
            "default_category": "sale",
            "default_partner_id": self.partner_id.id,
            # "default_address_id": self.partner_shipping_id.id,
        }

        if self.order_line:
            context["default_item_ids"] = []

            for item in self.order_line:
                value = {}
                value["product_id"] = item.product_id.id
                value["quantity"] = item.product_uom_qty
                context["default_item_ids"] += [(0, 0, value)]

        context["sale_order_id"] = self.id
        return {
            "name": self.env._("Notification"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "service.notification",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def _prepare_service_line_values(self, order, product, quantity, name=None, route=None):
        """Values of a quotation line generated from a service document.

        Odoo 19 removed ``product_id_change()``: description, price, unit and taxes are
        computed fields of the sale line, read here from a new line of the given order.
        """
        values = {"product_id": product.id, "product_uom_qty": quantity}
        if name:
            values["name"] = name
        if route:
            values["route_ids"] = [Command.set(route.ids)]
        line = self.new(dict(values, order_id=order.id))
        for field_name in ["name", "price_unit", "product_uom_id", "tax_ids"]:
            if field_name not in values:
                values[field_name] = line._fields[field_name].convert_to_write(line[field_name], line)
        return values
