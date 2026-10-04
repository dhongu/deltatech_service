# ©  2026 Terrabit
# See README.rst file on addons root folder for license details


from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAgreementDeliveryCosts(TransactionCase):
    """CONSUMABLE-002: validating a delivery linked to a service agreement adds the
    move valuation (stock.move.value) to the agreement costs, once."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.env["ir.config_parameter"].sudo().set_str("service.picking_type_for_service", cls.picking_type_out.id)
        cls.partner = cls.env["res.partner"].create({"name": "Test Agreement Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Toner", "is_storable": True, "standard_price": 10.0}
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_location, 100.0)
        cycle = cls.env["service.cycle"].create({"name": "Test Cycle", "value": 1, "unit": "month"})
        cls.agreement = cls.env["service.agreement"].create(
            {"name": "Test Agreement Costs", "partner_id": cls.partner.id, "cycle_id": cycle.id}
        )
        cls.equipment = cls.env["service.equipment"].create(
            {"name": "Test Equipment Costs", "agreement_id": cls.agreement.id}
        )

    def _delivery(self, quantity, done_quantity=None):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "partner_id": self.partner.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "agreement_id": self.agreement.id,
                "equipment_id": self.equipment.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": quantity,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity = quantity if done_quantity is None else done_quantity
        picking.move_ids.picked = True
        return picking

    def test_validate_updates_costs(self):
        picking = self._delivery(3.0)
        self.assertIs(picking.button_validate(), True)
        self.assertEqual(picking.state, "done")
        self.assertEqual(self.agreement.total_costs, -30.0)
        self.assertEqual(self.equipment.total_costs, -30.0)

    def test_repeated_validation_is_not_counted_twice(self):
        picking = self._delivery(3.0)
        picking.button_validate()
        picking.button_validate()
        self.assertEqual(self.agreement.total_costs, -30.0)

    def test_backorder_wizard_counts_after_completion(self):
        picking = self._delivery(3.0, done_quantity=2.0)
        action = picking.button_validate()
        self.assertIsInstance(action, dict)
        self.assertNotEqual(picking.state, "done")
        self.assertEqual(self.agreement.total_costs, 0.0)
        wizard = Form(self.env[action["res_model"]].with_context(**action["context"])).save()
        wizard.process()
        self.assertEqual(picking.state, "done")
        self.assertEqual(self.agreement.total_costs, -20.0)

    def test_compute_costs_matches_validation(self):
        self._delivery(3.0).button_validate()
        self._delivery(2.0).button_validate()
        self.assertEqual(self.agreement.total_costs, -50.0)
        self.agreement.total_costs = 0.0
        self.agreement.compute_costs()
        self.assertEqual(self.agreement.total_costs, -50.0)
