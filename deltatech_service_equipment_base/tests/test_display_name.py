# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEquipmentDisplayName(TransactionCase):
    def test_display_name(self):
        product = self.env["product.product"].create({"name": "Test Printer", "type": "consu", "tracking": "serial"})
        lot = self.env["stock.lot"].create({"name": "SN-0001", "product_id": product.id})
        equipment = self.env["service.equipment"].create({"name": "EQ-TEST", "serial_id": lot.id})
        bare = self.env["service.equipment"].create({"name": "EQ-BARE"})

        self.assertEqual(bare.display_name, "EQ-BARE")
        self.assertEqual(bare.with_context(formatted_display_name=True).display_name, "EQ-BARE")

        if "address_id" in equipment._fields:
            # deltatech_service_equipment overrides both forms (name/address/emplacement/serial);
            # its own test_display_name covers the dropdown form
            self.assertEqual(equipment.display_name, "EQ-TEST/SN-0001")
            return
        self.assertEqual(equipment.display_name, "EQ-TEST / SN-0001")
        formatted = equipment.with_context(formatted_display_name=True)
        self.assertEqual(formatted.display_name, "EQ-TEST\t--SN-0001--")
