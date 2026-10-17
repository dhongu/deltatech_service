# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMaintenanceAgreement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Client Test"})
        cls.address = cls.env["res.partner"].create({"name": "Address Test", "parent_id": cls.partner.id})
        cycle = cls.env["service.cycle"].create({"name": "Test Cycle", "value": 1, "unit": "month"})
        journal = cls.env["account.journal"].create({"name": "Test Sales", "type": "sale", "code": "TSA"})
        cls.agreement_type = cls.env["service.agreement.type"].create(
            {"name": "Test Type", "journal_id": journal.id, "permits_pickings": True}
        )
        cls.agreement = cls.env["service.agreement"].create(
            {
                "name": "CTR-TEST",
                "partner_id": cls.partner.id,
                "cycle_id": cycle.id,
                "type_id": cls.agreement_type.id,
            }
        )
        cls.equipment = cls.env["service.equipment"].create(
            {
                "name": "Test Equipment",
                "partner_id": cls.partner.id,
                "agreement_id": cls.agreement.id,
                "address_id": cls.address.id,
            }
        )

    def test_equipment_context_default(self):
        context = self.equipment.get_context_default()
        self.assertEqual(context["default_agreement_id"], self.agreement.id)
        self.assertEqual(context["default_address_id"], self.address.id)
        self.assertEqual(context["default_equipment_id"], self.equipment.id)

    def test_notification_agreement(self):
        notification = self.env["service.notification"].create(
            {"partner_id": self.partner.id, "equipment_id": self.equipment.id}
        )
        self.assertEqual(notification.agreement_id, self.agreement)
        self.assertTrue(notification.can_create_delivery)
        self.assertEqual(notification.get_context_default()["default_agreement_id"], self.agreement.id)

    def test_notification_without_equipment(self):
        notification = self.env["service.notification"].create({"partner_id": self.partner.id})
        self.assertFalse(notification.agreement_id)
        self.assertFalse(notification.can_create_delivery)

    def test_order_agreement(self):
        order = self.env["service.order"].create(
            {
                "partner_id": self.partner.id,
                "type_id": self.env["service.order.type"].create({"name": "Test Order Type"}).id,
                "agreement_id": self.agreement.id,
            }
        )
        self.assertEqual(order.agreement_id, self.agreement)
