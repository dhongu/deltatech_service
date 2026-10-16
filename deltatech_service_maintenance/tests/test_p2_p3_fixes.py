# ©  2026 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form, tagged

from .common import TestServiceBase


@tagged("post_install", "-at_install")
class TestServiceP2P3Fixes(TestServiceBase):
    def setUp(self):
        super().setUp()
        self.picking_type = self.env.ref("stock.picking_type_out")
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("service.picking_type_for_service", self.picking_type.id)
        set_param("service.picking_type_for_warranty", self.picking_type.id)
        self.uom_dozen = self.env.ref("uom.product_uom_dozen")

    # SERVICE-007
    def test_warranty_total_follows_line_edits(self):
        warranty = self.env["service.warranty"].create(
            {
                "type": "warranty",
                "partner_id": self.partner.id,
                "item_ids": [(0, 0, {"product_id": self.product.id, "quantity": 2.0, "price_unit": 5.0})],
            }
        )
        self.assertEqual(warranty.total_amount, 10.0)
        warranty.item_ids.quantity = 3.0
        self.assertEqual(warranty.total_amount, 15.0)
        warranty.item_ids.price_unit = 7.0
        self.assertEqual(warranty.total_amount, 21.0)
        warranty.item_ids = [(0, 0, {"product_id": self.product.id, "quantity": 1.0, "price_unit": 4.0})]
        self.assertEqual(warranty.total_amount, 25.0)
        warranty.item_ids[0].unlink()
        self.assertEqual(warranty.total_amount, 4.0)

    # SERVICE-009
    def _check_dozen_delivery(self, action):
        picking = Form(self.env["stock.picking"].with_context(**action["context"])).save()
        self.assertRecordValues(
            picking.move_ids,
            [{"product_id": self.product.id, "product_uom": self.product.uom_id.id, "product_uom_qty": 12.0}],
        )

    def _item(self):
        return [(0, 0, {"product_id": self.product.id, "quantity": 1.0, "product_uom": self.uom_dozen.id})]

    def test_delivery_from_notification_converts_uom(self):
        notification = self.env["service.notification"].create(
            {"partner_id": self.partner.id, "item_ids": self._item()}
        )
        self._check_dozen_delivery(notification.new_delivery_button())

    def test_transfer_from_notification_converts_uom(self):
        notification = self.env["service.notification"].create(
            {"partner_id": self.partner.id, "item_ids": self._item()}
        )
        action = notification.new_transfer_button()
        values = action["context"]["default_move_ids"][0][2]
        self.assertEqual(values["product_uom"], self.product.uom_id.id)
        self.assertEqual(values["product_uom_qty"], 12.0)

    def test_order_from_notification_keeps_uom(self):
        notification = self.env["service.notification"].create(
            {"partner_id": self.partner.id, "item_ids": self._item()}
        )
        action = notification.action_order()
        self.assertEqual(action["context"]["default_component_ids"][0][2]["product_uom"], self.uom_dozen.id)

    def test_delivery_from_order_converts_uom(self):
        order = self.env["service.order"].create(
            {
                "partner_id": self.partner.id,
                "type_id": self.env["service.order.type"].create({"name": "Test Order Type"}).id,
                "component_ids": self._item(),
            }
        )
        self._check_dozen_delivery(order.new_delivery_button())

    def test_delivery_from_warranty_converts_uom(self):
        warranty = self.env["service.warranty"].create(
            {"type": "warranty", "partner_id": self.partner.id, "item_ids": self._item()}
        )
        self._check_dozen_delivery(warranty.new_delivery_button())

    def test_delivery_without_item_uom_uses_product_uom(self):
        notification = self.env["service.notification"].create(
            {"partner_id": self.partner.id, "item_ids": [(0, 0, {"product_id": self.product.id, "quantity": 2.0})]}
        )
        values = notification.new_delivery_button()["context"]["default_move_ids"][0][2]
        self.assertEqual(values["product_uom"], self.product.uom_id.id)
        self.assertEqual(values["product_uom_qty"], 2.0)

    # SERVICE-010
    def test_new_notification_from_picking_context(self):
        notification = self.env["service.notification"].create(
            {"partner_id": self.partner.id, "item_ids": self._item()}
        )
        picking = Form(self.env["stock.picking"].with_context(**notification.new_delivery_button()["context"])).save()
        action = picking.new_notification()
        self.assertNotIn("sale_order_id", action["context"])
        item = action["context"]["default_item_ids"][0][2]
        self.assertEqual(item["product_uom"], self.product.uom_id.id)
        self.assertEqual(item["quantity"], 12.0)

    # SERVICE-011
    def test_company_user_uses_current_company(self):
        company_b = self.env["res.company"].create({"name": "Service Company B"})
        user_b = self.env["res.users"].create(
            {
                "name": "Technician B",
                "login": "technician_b_service",
                "company_id": company_b.id,
                "company_ids": [(6, 0, company_b.ids)],
            }
        )
        user_b.partner_id.parent_id = company_b.partner_id
        self.env.user.company_ids = [(4, company_b.id)]
        notification = self.env["service.notification"].with_company(company_b)
        users_name, _dummy = notification.company_user([], [])
        self.assertIn((user_b.id, user_b.display_name), users_name)
