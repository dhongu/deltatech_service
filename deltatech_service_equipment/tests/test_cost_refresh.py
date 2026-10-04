# ©  2026 Terrabit
# See README.rst file on addons root folder for license details


from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEquipmentCostRefresh(TransactionCase):
    """EQUIPMENT-002: the cost refresh reads the move valuation
    (stock.move.value) instead of the removed stock valuation layers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.product = cls.env["product.product"].create(
            {"name": "Test Toner", "is_storable": True, "standard_price": 10.0}
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_location, 100.0)
        cls.equipment = cls.env["service.equipment"].create({"name": "Test Equipment Cost"})
        cls.env["ir.config_parameter"].sudo().set_str("service.picking_type_for_service", cls.picking_type_out.id)

    def _done_picking(self, picking_type, location, location_dest, quantity, **extra):
        picking = self.env["stock.picking"].create(
            dict(
                picking_type_id=picking_type.id,
                location_id=location.id,
                location_dest_id=location_dest.id,
                move_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": quantity,
                            "location_id": location.id,
                            "location_dest_id": location_dest.id,
                        },
                    )
                ],
                **extra,
            )
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity = quantity
        picking.move_ids.picked = True
        picking._action_done()
        self.assertEqual(picking.state, "done")
        return picking

    def test_signed_value_of_moves(self):
        if "value" not in self.env["stock.move"]._fields:
            self.skipTest("stock.move.value is provided by stock_account")
        delivery = self._done_picking(self.picking_type_out, self.stock_location, self.customer_location, 3.0)
        receipt = self._done_picking(self.picking_type_in, self.customer_location, self.stock_location, 1.0)
        # Odoo 20: `stock.move.value` is already negative for outgoing moves
        self.assertEqual(delivery.move_ids.value, -30.0)
        self.assertEqual(delivery.move_ids._get_service_signed_value(), -30.0)
        self.assertEqual(receipt.move_ids._get_service_signed_value(), 10.0)
        self.assertEqual((delivery | receipt).move_ids._get_service_signed_value(), -20.0)
        self.assertEqual(self.env["stock.move"]._get_service_signed_value(), 0.0)

    def test_compute_totals_without_deliveries(self):
        self.equipment.total_costs = 5.0
        self.equipment.compute_totals()
        self.assertEqual(self.equipment.total_costs, 0.0)

    def test_compute_totals_with_deliveries(self):
        if "equipment_id" not in self.env["stock.picking"]._fields:
            self.skipTest("stock.picking.equipment_id is provided by deltatech_service_consumable")
        extra = {"equipment_id": self.equipment.id}
        self._done_picking(self.picking_type_out, self.stock_location, self.customer_location, 3.0, **extra)
        self._done_picking(self.picking_type_out, self.stock_location, self.customer_location, 2.0, **extra)
        self.equipment.compute_totals()
        self.assertEqual(self.equipment.total_costs, -50.0)
