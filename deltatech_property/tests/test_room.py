# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRoom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.building = cls.env["property.building"].create({"name": "Test Building Room"})

    def test_cleaning_floor_constraint(self):
        """PROPERTY-003: the floor cleaning area cannot exceed the room surface."""
        Room = self.env["property.room"]
        room = Room.create(
            {"name": "1", "building_id": self.building.id, "surface": 10.0, "surface_cleaning_floor": 10.0}
        )
        with self.assertRaises(ValidationError):
            Room.create({"name": "2", "building_id": self.building.id, "surface": 10.0, "surface_cleaning_floor": 12.0})
        with self.assertRaises(ValidationError):
            room.surface_cleaning_floor = 11.0
        with self.assertRaises(ValidationError):
            room.surface = 5.0
        other = Room.create(
            {"name": "3", "building_id": self.building.id, "surface": 20.0, "surface_cleaning_floor": 2.0}
        )
        with self.assertRaises(ValidationError):
            (room | other).write({"surface_cleaning_floor": 15.0})
        (room | other).write({"surface_cleaning_floor": 8.0})
        self.assertEqual((room | other).mapped("surface_cleaning_floor"), [8.0, 8.0])

    def test_numeric_name_search_keeps_domain(self):
        """PROPERTY-005: a numeric code search honours the caller's domain and limit."""
        Purpose = self.env["property.building.purpose"]
        parent_a = Purpose.create({"name": "Test parent A", "cod": "TA"})
        parent_b = Purpose.create({"name": "Test parent B", "cod": "TB"})
        child_a = Purpose.create({"name": "Test child A", "cod": "9901", "parent_id": parent_a.id})
        child_b = Purpose.create({"name": "Test child B", "cod": "9901", "parent_id": parent_b.id})
        child_b2 = Purpose.create({"name": "Test child B2", "cod": "9902", "parent_id": parent_b.id})

        result = Purpose.name_search("9901", domain=[("parent_id", "=", parent_b.id)], limit=20)
        self.assertEqual([res[0] for res in result], [child_b.id])

        result = Purpose.name_search("990", domain=[("parent_id", "=", parent_b.id)], limit=20)
        self.assertEqual({res[0] for res in result}, {child_b.id, child_b2.id})

        result = Purpose.name_search("990", domain=[("parent_id", "in", (parent_a | parent_b).ids)], limit=2)
        self.assertEqual(len(result), 2)

        result = Purpose.name_search("9901", limit=20)
        self.assertTrue({child_a.id, child_b.id} <= {res[0] for res in result})

        # non-numeric searches keep the standard behaviour
        result = Purpose.name_search("Test child B", domain=[("parent_id", "=", parent_b.id)], limit=20)
        self.assertEqual({res[0] for res in result}, {child_b.id, child_b2.id})

    def test_room_usage_fields_have_distinct_labels(self):
        """PROPERTY-006: the selection and the many2one usage fields have distinct labels."""
        fields = self.env["property.room"]._fields
        self.assertNotEqual(fields["usage"].string, fields["usage_id"].string)
