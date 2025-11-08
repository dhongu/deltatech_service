# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestServiceBase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        self.work_center = self.env["service.work.center"].create(
            {
                "name": "Test Work Order",
            }
        )

        self.location = self.env["service.location"].create(
            {
                "name": "Test Location",
                "work_center_id": self.work_center.id,
                "contact_id": self.partner.id,
            }
        )

        self.equipment = self.env["service.equipment"].create(
            {
                "name": "Test Equipment",
                "work_center_id": self.work_center.id,
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
            }
        )
        # Ensure sales use make-to-stock flow and avoid unintended purchase/MTO routes during tests
        self.product.route_ids = [(6, 0, [])]
        # Add on-hand stock so the generated delivery can be reserved
        stock_location = self.env.ref("stock.stock_location_stock")
        self.env["stock.quant"]._update_available_quantity(self.product, stock_location, 10.0)
