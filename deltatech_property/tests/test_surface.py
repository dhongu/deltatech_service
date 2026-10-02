# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBuildingSurface(TransactionCase):
    """PROPERTY-001: the building area fields are computed by existing methods."""

    def test_surface_by_room_usage(self):
        building = self.env["property.building"].create(
            {
                "name": "Test Building",
                "room_ids": [
                    Command.create({"name": "1", "usage": "office", "surface": 20.0}),
                    Command.create({"name": "2", "usage": "office", "surface": 15.0}),
                    Command.create({"name": "3", "usage": "kitchen", "surface": 8.0}),
                    Command.create({"name": "4", "usage": "balcony", "surface": 4.0}),
                ],
            }
        )
        self.assertRecordValues(
            building,
            [{"surface_office": 35.0, "surface_kitchen": 8.0, "surface_bedroom": 0.0, "surface_garage": 0.0}],
        )
        building.room_ids.filtered(lambda r: r.name == "3").write({"usage": "garage", "surface": 10.0})
        self.assertRecordValues(building, [{"surface_kitchen": 0.0, "surface_garage": 10.0}])

    def test_every_usage_field_is_assigned(self):
        usages = [
            key
            for key, _label in self.env["property.room"]._fields["usage"].selection
            if f"surface_{key}" in self.env["property.building"]._fields
        ]
        self.assertEqual(len(usages), 17)
        building = self.env["property.building"].create(
            {
                "name": "Test Building All",
                "room_ids": [
                    Command.create({"name": str(index), "usage": usage, "surface": index + 1.0})
                    for index, usage in enumerate(usages)
                ],
            }
        )
        for index, usage in enumerate(usages):
            self.assertEqual(building[f"surface_{usage}"], index + 1.0, usage)

    def test_surface_totals(self):
        building = self.env["property.building"].create(
            {
                "name": "Test Building Totals",
                "surface_cleaned_adm": 100.0,
                "surface_cleaned_ind": 50.0,
                "surface_cleaned_ext": 25.0,
                "surface_derating_int": 70.0,
                "surface_derating_ext": 30.0,
            }
        )
        self.assertRecordValues(building, [{"surface_cleaned_tot": 175.0, "surface_derating": 100.0}])
        building.surface_cleaned_ext = 5.0
        self.assertEqual(building.surface_cleaned_tot, 155.0)

    def test_batch_buildings_keep_their_own_rooms(self):
        buildings = self.env["property.building"].create(
            [
                {"name": "B1", "room_ids": [Command.create({"name": "1", "usage": "office", "surface": 5.0})]},
                {"name": "B2", "room_ids": [Command.create({"name": "1", "usage": "office", "surface": 7.0})]},
            ]
        )
        self.assertEqual(buildings.mapped("surface_office"), [5.0, 7.0])
