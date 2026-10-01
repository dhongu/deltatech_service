# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form

from .common import TestServiceBase


class TestServiceDelivery(TestServiceBase):
    def setUp(self):
        super().setUp()
        self.picking_type = self.env.ref("stock.picking_type_out")
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("service.picking_type_for_service", self.picking_type.id)
        set_param("service.picking_type_for_warranty", self.picking_type.id)

    def _save_delivery(self, action):
        picking = Form(self.env["stock.picking"].with_context(**action["context"])).save()
        self.assertRecordValues(
            picking.move_ids,
            [{"product_id": self.product.id, "product_uom_qty": 3.0, "picking_type_id": self.picking_type.id}],
        )
        return picking

    def test_delivery_from_notification(self):
        notification = self.env["service.notification"].create(
            {
                "partner_id": self.partner.id,
                "item_ids": [(0, 0, {"product_id": self.product.id, "quantity": 3.0})],
            }
        )
        self._save_delivery(notification.new_delivery_button())

    def test_delivery_from_order(self):
        order = self.env["service.order"].create(
            {
                "partner_id": self.partner.id,
                "type_id": self.env["service.order.type"].create({"name": "Test Order Type"}).id,
                "component_ids": [(0, 0, {"product_id": self.product.id, "quantity": 3.0})],
            }
        )
        self._save_delivery(order.new_delivery_button())

    def test_delivery_from_warranty(self):
        warranty = self.env["service.warranty"].create(
            {
                "type": "warranty",
                "partner_id": self.partner.id,
                "item_ids": [(0, 0, {"product_id": self.product.id, "quantity": 3.0})],
            }
        )
        picking = self._save_delivery(warranty.new_delivery_button())
        self.assertEqual(picking.warranty_id, warranty)
