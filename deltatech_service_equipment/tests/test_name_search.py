# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEquipmentNameSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Copier NS", "type": "consu", "is_storable": True, "tracking": "serial"}
        )
        Lot = cls.env["stock.lot"]
        Equipment = cls.env["service.equipment"]
        cls.lot_a = Lot.create({"name": "SNX-ALPHA-001", "product_id": cls.product.id})
        cls.lot_b = Lot.create({"name": "SNX-ALPHA-002", "product_id": cls.product.id})
        cls.partner_a = cls.env["res.partner"].create({"name": "NS Partner A"})
        cls.partner_b = cls.env["res.partner"].create({"name": "NS Partner B"})
        # the name matches the serial too, so a naive concatenation returns it twice
        cls.eq_a = Equipment.create(
            {"name": "EQ SNX-ALPHA-001", "serial_id": cls.lot_a.id, "partner_id": cls.partner_a.id}
        )
        cls.eq_b = Equipment.create(
            {
                "name": "EQ-NS-B",
                "serial_id": cls.lot_b.id,
                "ean_code": "5941234567890",
                "partner_id": cls.partner_b.id,
            }
        )

    def _ids(self, result):
        return [rec_id for rec_id, _name in result]

    def test_search_by_serial_and_ean(self):
        Equipment = self.env["service.equipment"]
        self.assertEqual(self._ids(Equipment.name_search("SNX-ALPHA-002")), [self.eq_b.id])
        self.assertEqual(self._ids(Equipment.name_search("594123456")), [self.eq_b.id])
        self.assertEqual(Equipment.search([("display_name", "ilike", "SNX-ALPHA-002")]), self.eq_b)

    def test_domain_respected(self):
        res = self.env["service.equipment"].name_search("SNX-ALPHA", domain=[("partner_id", "=", self.partner_a.id)])
        self.assertEqual(self._ids(res), [self.eq_a.id])

    def test_no_duplicates_and_limit(self):
        Equipment = self.env["service.equipment"]
        ids = self._ids(Equipment.name_search("SNX-ALPHA-001"))
        self.assertEqual(ids, [self.eq_a.id])
        ids = self._ids(Equipment.name_search("SNX-ALPHA", limit=1))
        self.assertEqual(len(ids), 1)
        ids = self._ids(Equipment.name_search("SNX-ALPHA"))
        self.assertEqual(sorted(ids), sorted([self.eq_a.id, self.eq_b.id]))

    def test_short_value_searches_name_only(self):
        res = self.env["service.equipment"].name_search("SNX")
        self.assertEqual(self._ids(res), [self.eq_a.id])
