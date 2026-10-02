# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

PROPERTY_MODELS = [
    "property.land",
    "property.building",
    "property.room",
    "property.features",
    "building.history",
    "room.usage",
    "property.acquisition",
    "property.land.categ",
    "property.building.categ",
    "property.building.purpose",
    "property.region",
    "property.room.usage",
]


@tagged("post_install", "-at_install")
class TestPropertySecurity(TransactionCase):
    """PROPERTY-004: property models are restricted to internal users of the right company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Property Company B"})
        cls.building = cls.env["property.building"].create(
            {
                "name": "Building A",
                "company_id": cls.company_a.id,
                "room_ids": [Command.create({"name": "R1", "surface": 10.0})],
            }
        )
        cls.room = cls.building.room_ids
        cls.history = cls.env["building.history"].create({"building_id": cls.building.id, "note": "tenant"})
        cls.features = cls.env["property.features"].create({"building_id": cls.building.id, "number": 1})
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Property Portal",
                "login": "property_portal",
                "group_ids": [Command.set([cls.env.ref("base.group_portal").id])],
            }
        )
        cls.public_user = cls.env.ref("base.public_user")
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Property Internal",
                "login": "property_internal",
                "company_id": cls.company_a.id,
                "company_ids": [Command.set([cls.company_a.id])],
                "group_ids": [Command.set([cls.env.ref("base.group_user").id])],
            }
        )
        cls.manager_a = cls.env["res.users"].create(
            {
                "name": "Property Manager A",
                "login": "property_manager_a",
                "company_id": cls.company_a.id,
                "company_ids": [Command.set([cls.company_a.id])],
                "group_ids": [Command.set([cls.env.ref("maintenance.group_equipment_manager").id])],
            }
        )
        cls.manager_b = cls.env["res.users"].create(
            {
                "name": "Property Manager B",
                "login": "property_manager_b",
                "company_id": cls.company_b.id,
                "company_ids": [Command.set([cls.company_b.id])],
                "group_ids": [
                    Command.set(
                        [cls.env.ref("base.group_user").id, cls.env.ref("maintenance.group_equipment_manager").id]
                    )
                ],
            }
        )

    def test_public_and_portal_have_no_access(self):
        for user in (self.public_user, self.portal_user):
            for model in PROPERTY_MODELS:
                for operation in ("read", "write", "create", "unlink"):
                    with self.subTest(user=user.login, model=model, operation=operation):
                        self.assertFalse(
                            self.env[model].with_user(user).has_access(operation),
                            f"{user.login} must not have {operation} access on {model}",
                        )
            with self.assertRaises(AccessError):
                self.room.with_user(user).read(["name"])
            with self.assertRaises(AccessError):
                self.history.with_user(user).write({"note": "changed"})

    def test_internal_user_keeps_access(self):
        user = self.internal_user
        for model in PROPERTY_MODELS:
            for operation in ("read", "write", "create", "unlink"):
                with self.subTest(model=model, operation=operation):
                    self.assertTrue(self.env[model].with_user(user).has_access(operation))
        # like maintenance equipment, a simple user works on the buildings he follows
        self.building.base_equipment_id.message_subscribe(partner_ids=user.partner_id.ids)
        building = self.building.with_user(user)
        self.assertEqual(building.name, "Building A")
        self.assertEqual(building.room_ids, self.room)
        room = self.env["property.room"].with_user(user).create({"name": "R2", "building_id": building.id})
        room.write({"surface": 12.0})
        history = self.env["building.history"].with_user(user).create({"building_id": building.id, "note": "new"})
        history.unlink()
        self.assertEqual(self.features.with_user(user).number, 1)
        usage = self.env["property.room.usage"].with_user(user).create({"name": "Office"})
        usage.unlink()
        self.assertIn(room, building.room_ids)

    def test_internal_user_not_follower_sees_no_child_records(self):
        user = self.internal_user
        for record in (self.room, self.history, self.features):
            with self.subTest(model=record._name):
                self.assertFalse(record.with_user(user).search([("id", "=", record.id)]))
                with self.assertRaises(AccessError):
                    record.with_user(user).read(["building_id"])

    def test_equipment_manager_full_access(self):
        user = self.manager_a
        building = self.building.with_user(user)
        self.assertEqual(building.room_ids, self.room)
        self.assertEqual(self.history.with_user(user).note, "tenant")
        new_building = (
            self.env["property.building"]
            .with_user(user)
            .create({"name": "Building A2", "room_ids": [Command.create({"name": "A2-1"})]})
        )
        new_building.room_ids.write({"surface": 5.0})
        self.env["property.features"].with_user(user).create({"building_id": new_building.id, "number": 2}).unlink()

    def test_other_company_cannot_access(self):
        user = self.manager_b
        for record in (self.building, self.room, self.history, self.features):
            with self.subTest(model=record._name):
                self.assertFalse(record.with_user(user).search([("id", "=", record.id)]))
                with self.assertRaises(AccessError):
                    record.with_user(user).read(["building_id" if record._name != "property.building" else "name"])
        # a building of its own company is still fully manageable
        building_b = self.env["property.building"].with_user(user).create({"name": "Building B"})
        room_b = self.env["property.room"].with_user(user).create({"name": "B1", "building_id": building_b.id})
        self.assertEqual(building_b.company_id, self.company_b)
        self.assertTrue(room_b.with_user(user).read(["name"]))
