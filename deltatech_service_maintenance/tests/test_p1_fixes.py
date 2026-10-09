# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from .common import TestServiceBase


@tagged("post_install", "-at_install")
class TestServiceOrderBatchCreate(TestServiceBase):
    """SERVICE-002: creating several service orders in one call creates all of them."""

    def setUp(self):
        super().setUp()
        self.order_type = self.env["service.order.type"].create({"name": "Batch Order Type"})

    def test_batch_create_returns_all_orders(self):
        orders = self.env["service.order"].create(
            [
                {"partner_id": self.partner.id, "type_id": self.order_type.id, "description": "A"},
                {"partner_id": self.partner.id, "type_id": self.order_type.id, "description": "B"},
                {"partner_id": self.partner.id, "type_id": self.order_type.id, "name": "MANUAL-REF"},
            ]
        )
        self.assertEqual(len(orders), 3)
        self.assertEqual(orders.mapped("description")[:2], ["A", "B"])
        self.assertEqual(orders[2].name, "MANUAL-REF")
        self.assertNotIn(self.env._("New"), orders[:2].mapped("name"))
        self.assertEqual(len(set(orders.mapped("name"))), 3)

    def test_single_and_empty_create(self):
        order = self.env["service.order"].create({"partner_id": self.partner.id, "type_id": self.order_type.id})
        self.assertEqual(len(order), 1)
        self.assertFalse(self.env["service.order"].create([]))


@tagged("post_install", "-at_install")
class TestWarrantyApprovalRights(TestServiceBase):
    """SERVICE-006: the approval right is enforced by the server, not only by the button."""

    def setUp(self):
        super().setUp()
        self.warranty_user = new_test_user(
            self.env, login="svc_warranty_user", groups="base.group_user,deltatech_service_base.group_warranty_user"
        )
        self.warranty_approver = new_test_user(
            self.env,
            login="svc_warranty_approver",
            groups="base.group_user,deltatech_service_base.group_warranty_user,"
            "deltatech_service_base.group_warranty_approve",
        )
        self.warranty_manager = new_test_user(
            self.env,
            login="svc_warranty_manager",
            groups="base.group_user,deltatech_service_base.group_warranty_manager",
        )
        self.warranty = self.env["service.warranty"].create({"type": "warranty", "partner_id": self.partner.id})
        self.warranty.state = "approval_requested"

    def test_plain_user_cannot_approve(self):
        with self.assertRaises(AccessError):
            self.warranty.with_user(self.warranty_user).approve()
        self.assertEqual(self.warranty.state, "approval_requested")

    def test_approver_can_approve(self):
        self.warranty.with_user(self.warranty_approver).approve()
        self.assertEqual(self.warranty.state, "approved")

    def test_manager_can_approve(self):
        self.warranty.with_user(self.warranty_manager).approve()
        self.assertEqual(self.warranty.state, "approved")

    def test_sudo_is_not_blocked(self):
        self.warranty.with_user(self.warranty_user).sudo().approve()
        self.assertEqual(self.warranty.state, "approved")

    def test_invalid_or_repeated_transition(self):
        self.warranty.with_user(self.warranty_approver).approve()
        with self.assertRaises(UserError):
            self.warranty.with_user(self.warranty_approver).approve()
        draft = self.env["service.warranty"].create({"type": "warranty", "partner_id": self.partner.id})
        with self.assertRaises(UserError):
            draft.with_user(self.warranty_manager).approve()


@tagged("post_install", "-at_install")
class TestNotificationEquipmentDetection(TestServiceBase):
    """SERVICE-008: equipment detection works without the optional equipment extension fields."""

    def _without_optional_fields(self):
        fields_map = dict(self.env["service.equipment"]._fields)
        fields_map.pop("ean_code", None)
        fields_map.pop("agreement_id", None)
        return patch.object(type(self.env["service.equipment"]), "_fields", fields_map)

    def test_detection_by_contact_without_optional_fields(self):
        contact = self.env["res.partner"].create({"name": "Equipment Contact"})
        self.equipment.write({"contact_id": contact.id, "technician_user_id": self.env.user.id})
        self.equipment.sudo().partner_id = self.partner
        with self._without_optional_fields():
            notification = self.env["service.notification"].create(
                {"contact_id": contact.id, "description": "printer 5940000000001 jammed"}
            )
        self.assertEqual(notification.equipment_id, self.equipment)
        self.assertEqual(notification.partner_id, self.partner)

    def test_description_without_optional_fields(self):
        with self._without_optional_fields():
            notification = self.env["service.notification"].create(
                {"partner_id": self.partner.id, "description": "printer 5940000000001 jammed"}
            )
        self.assertFalse(notification.equipment_id)

    def test_detection_by_ean_with_optional_fields(self):
        if "ean_code" not in self.env["service.equipment"]._fields:
            self.skipTest("deltatech_service_equipment is not installed")
        self.equipment.ean_code = "5940000000002"
        notification = self.env["service.notification"].create(
            {"partner_id": self.partner.id, "description": "printer 5940000000002 jammed"}
        )
        self.assertEqual(notification.equipment_id, self.equipment)
