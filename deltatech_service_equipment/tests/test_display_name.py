# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEquipmentDisplayNameFull(TransactionCase):
    def test_display_name(self):
        product = self.env["product.product"].create({"name": "Test Printer", "type": "consu", "tracking": "serial"})
        lot = self.env["stock.lot"].create({"name": "SN-0002", "product_id": product.id})
        address = self.env["res.partner"].create({"name": "Sediu Test"})
        equipment = self.env["service.equipment"].create(
            {"name": "EQ-FULL", "serial_id": lot.id, "address_id": address.id, "emplacement": "Etaj 2"}
        )
        partial = self.env["service.equipment"].create({"name": "EQ-PART", "emplacement": "Hol"})
        bare = self.env["service.equipment"].create({"name": "EQ-BARE"})

        self.assertEqual(equipment.display_name, "EQ-FULL/Sediu Test/Etaj 2/SN-0002")
        self.assertEqual(partial.display_name, "EQ-PART/Hol")
        self.assertEqual(bare.display_name, "EQ-BARE")

        ctx = {"formatted_display_name": True}
        self.assertEqual(
            equipment.with_context(**ctx).display_name, "EQ-FULL\t--Sediu Test · Etaj 2 · SN-0002--"
        )
        self.assertEqual(partial.with_context(**ctx).display_name, "EQ-PART\t--Hol--")
        self.assertEqual(bare.with_context(**ctx).display_name, "EQ-BARE")
