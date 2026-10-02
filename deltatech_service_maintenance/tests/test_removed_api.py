# ©  2026 Terrabit
# See README.rst file on addons root folder for license details


from odoo import Command
from odoo.tests import Form, tagged

from .common import TestServiceBase


@tagged("post_install", "-at_install")
class TestServiceQuotation(TestServiceBase):
    """SERVICE-003: new quotations are prepared without the removed sale line APIs
    (product_id_change, product_uom, tax_id, route_id)."""

    def setUp(self):
        super().setUp()
        self.uom_dozen = self.env.ref("uom.product_uom_dozen")
        self.tax = self.env["account.tax"].create({"name": "Test VAT 21", "amount": 21.0, "type_tax_use": "sale"})
        self.component = self.env["product.product"].create(
            {
                "name": "Test Component",
                "type": "consu",
                "list_price": 50.0,
                "uom_id": self.uom_dozen.id,
                "taxes_id": [Command.set(self.tax.ids)],
            }
        )
        self.service_product = self.env["product.product"].create(
            {"name": "Test Labour", "type": "service", "list_price": 80.0, "taxes_id": [Command.set(self.tax.ids)]}
        )
        self.operation = self.env["service.operation"].create(
            {"name": "Test Repair", "duration": 2.0, "product_id": self.service_product.id}
        )
        self.route = self.env["stock.route"].create({"name": "Test Service Route", "sale_selectable": True})
        self.work_center.sale_route_id = self.route

    def _check_quotation(self, action, component_qty):
        self.assertEqual(action["res_model"], "sale.order")
        lines = action["context"]["default_order_line"]
        self.assertEqual(len(lines), 2)
        component_vals = lines[0][2]
        self.assertEqual(component_vals["product_uom_id"], self.uom_dozen.id)
        self.assertEqual(component_vals["price_unit"], 50.0)
        self.assertEqual(component_vals["tax_ids"], [Command.set(self.tax.ids)])
        self.assertEqual(component_vals["route_ids"], [Command.set(self.route.ids)])
        operation_vals = lines[1][2]
        self.assertEqual(operation_vals["name"], "Test Repair")
        self.assertEqual(operation_vals["price_unit"], 80.0)

        # the route is in the context values above; the sale line form shows it only to
        # the "Multi-Step Routes" group, so the form simulation does not keep it
        order = Form(self.env["sale.order"].with_context(**action["context"])).save()
        self.assertRecordValues(
            order.order_line,
            [
                {
                    "product_id": self.component.id,
                    "product_uom_qty": component_qty,
                    "product_uom_id": self.uom_dozen.id,
                    "price_unit": 50.0,
                    "tax_ids": self.tax.ids,
                },
                {
                    "product_id": self.service_product.id,
                    "product_uom_qty": 2.0,
                    "product_uom_id": self.service_product.uom_id.id,
                    "price_unit": 80.0,
                    "tax_ids": self.tax.ids,
                },
            ],
        )
        self.assertEqual(order.order_line[1].name, "Test Repair")
        return order

    def test_quotation_from_notification(self):
        notification = self.env["service.notification"].create(
            {
                "partner_id": self.partner.id,
                "work_center_id": self.work_center.id,
                "item_ids": [Command.create({"product_id": self.component.id, "quantity": 3.0})],
                "operation_ids": [Command.create({"operation_id": self.operation.id, "duration": 2.0})],
            }
        )
        order = self._check_quotation(notification.new_sale_order_button(), 3.0)
        self.assertEqual(order.notification_id, notification)

    def test_quotation_from_order(self):
        service_order = self.env["service.order"].create(
            {
                "partner_id": self.partner.id,
                "work_center_id": self.work_center.id,
                "type_id": self.env["service.order.type"].create({"name": "Test Order Type"}).id,
                "component_ids": [Command.create({"product_id": self.component.id, "quantity": 3.0})],
                "operation_ids": [Command.create({"operation_id": self.operation.id, "duration": 2.0})],
            }
        )
        order = self._check_quotation(service_order.new_sale_order_button(), 3.0)
        self.assertEqual(order.service_order_id, service_order)

        # existing quotation: changed quantities are written, new components are added
        other = self.env["product.product"].create({"name": "Test Other Component", "type": "consu"})
        service_order.component_ids[0].quantity = 5.0
        service_order.component_ids = [Command.create({"product_id": other.id, "quantity": 1.0})]
        action = service_order.new_sale_order_button()
        self.assertEqual(action["res_id"], order.id)
        self.assertEqual(order.order_line.filtered(lambda li: li.product_id == self.component).product_uom_qty, 5.0)
        new_line = order.order_line.filtered(lambda li: li.product_id == other)
        self.assertRecordValues(new_line, [{"product_uom_qty": 1.0, "route_ids": self.route.ids, "state": "draft"}])


@tagged("post_install", "-at_install")
class TestWarrantyDeliveryCosts(TestServiceBase):
    """SERVICE-004: validating a warranty delivery writes the unit cost from the
    Odoo 19 move valuation (stock.move.value) instead of the removed valuation layers."""

    def setUp(self):
        super().setUp()
        self.picking_type = self.env.ref("stock.picking_type_out")
        self.env["ir.config_parameter"].sudo().set_param("service.picking_type_for_warranty", self.picking_type.id)
        self.product.standard_price = 10.0
        self.env.user.group_ids |= self.env.ref("deltatech_service_base.group_warranty_approve")
        self.warranty = self.env["service.warranty"].create(
            {
                "type": "warranty",
                "partner_id": self.partner.id,
                "item_ids": [Command.create({"product_id": self.product.id, "quantity": 3.0, "price_unit": 1.0})],
            }
        )
        action = self.warranty.new_delivery_button()
        self.picking = Form(self.env["stock.picking"].with_context(**action["context"])).save()
        self.picking.action_confirm()
        self.picking.action_assign()

    def test_validate_writes_unit_cost(self):
        self.assertIs(self.picking.button_validate(), True)
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.picking.move_ids.value, 30.0)
        self.assertEqual(self.warranty.item_ids.price_unit, 10.0)

    def test_backorder_wizard_writes_cost_after_completion(self):
        self.picking.move_ids.quantity = 2.0
        action = self.picking.button_validate()
        self.assertIsInstance(action, dict)
        self.assertEqual(self.warranty.item_ids.price_unit, 1.0)
        Form(self.env[action["res_model"]].with_context(**action["context"])).save().process()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.warranty.item_ids.price_unit, 10.0)

    def test_unit_cost_in_item_unit(self):
        self.warranty.item_ids.product_uom = self.env.ref("uom.product_uom_dozen")
        self.picking.button_validate()
        self.assertAlmostEqual(self.warranty.item_ids.price_unit, 120.0)
