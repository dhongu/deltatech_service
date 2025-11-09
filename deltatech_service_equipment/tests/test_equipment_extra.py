# © 2025 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.deltatech_service_agreement.tests.test_agreement import TestAgreement
from odoo.addons.deltatech_service_equipment_base.tests.test_service import TestService


class TestEquipmentExtra(TestAgreement, TestService):
    def setUp(self):
        super().setUp()
        # Minimal equipment + meter setup reused across tests
        self.equipment = self.env["service.equipment"].create(
            {
                "name": "EQ-Extra",
                "type_id": self.equipment_type.id,
                "model_id": self.equipment_model.id,
            }
        )
        self.meter = self.env["service.meter"].create(
            {
                "name": "MT-Extra",
                "meter_categ_id": self.meter_category.id,
                "equipment_id": self.equipment.id,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

    def _create_draft_agreement_with_line(self, add_meter=False):
        agreement = Form(self.env["service.agreement"])
        # Avoid fixed name to prevent unique constraint collisions across tests
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle
        with agreement.agreement_line.new() as agreement_line:
            agreement_line.product_id = self.product_ab
            agreement_line.quantity = 1
            agreement_line.price_unit = 100
            agreement_line.equipment_id = self.equipment
            if add_meter:
                agreement_line.meter_id = self.meter
        agreement = agreement.save()
        return agreement

    # def test_uninstall_requires_billing(self):
    #     # Prepare an agreement with equipment + meter line, but no billed consumption yet
    #     agreement = self._create_draft_agreement_with_line(add_meter=True)
    #     # Link equipment to agreement explicitly for button logic/labels
    #     self.equipment.agreement_id = agreement
    #
    #     # Seed a last meter reading so the wizard has a reference to compare against
    #     self.env["service.meter.reading"].create(
    #         {
    #             "meter_id": self.meter.id,
    #             "equipment_id": self.equipment.id,
    #             "counter_value": 5,
    #             "date": self.env["service.date.range"]._fields["date_start"].today(self.env.user),
    #         }
    #     )
    #
    #     # Open uninstall wizard with active_ids so delegated items are populated
    #     wiz = Form(
    #         self.env["service.equi.operation"].with_context(
    #             active_id=self.equipment.id, active_ids=[self.equipment.id], default_state="rem"
    #         )
    #     )
    #     wiz.service_period_id = self.date_range
    #     # partner_id and address_id are defaulted from equipment by default_get; avoid writing invisible fields in Form
    #     wiz = wiz.save()
    #     # Force a mismatch with the last reading so can_remove evaluates to False
    #     wiz.items[0].counter_value = self.meter.last_meter_reading_id.counter_value + 1
    #     with self.assertRaises(UserError):
    #         wiz.do_operation()

    def test_install_creates_history_and_updates_equipment(self):
        # Install equipment to a partner/location -> creates service.history and updates fields
        wiz = Form(self.env["service.equi.operation"].with_context(active_id=self.equipment.id, default_state="ins"))
        wiz.partner_id = self.partner_1
        wiz.address_id = self.partner_1
        wiz.emplacement = "Hala A"
        wiz = wiz.save()
        wiz.do_operation()

        # Equipment fields updated
        self.equipment.invalidate_recordset()
        self.assertEqual(self.equipment.partner_id, self.partner_1)
        self.assertEqual(self.equipment.address_id, self.partner_1)
        self.assertEqual(self.equipment.emplacement, "Hala A")
        self.assertEqual(self.equipment.state, "installed")
        self.assertTrue(self.equipment.installation_date)

        # History entry created
        history = self.env["service.history"].search(
            [("equipment_id", "=", self.equipment.id), ("name", "=", "Installation")], limit=1
        )
        self.assertTrue(history, "Installation history should be created")
        self.assertIn("Meters:", history.description)

    def test_readings_status_updates(self):
        # Create a current reading -> status should become 'done' after update_meter_status
        reading = Form(self.env["service.meter.reading"])
        reading.meter_id = self.meter
        reading.counter_value = 10
        reading.date = self.env["service.date.range"]._fields["date_start"].today(self.env.user)
        reading.save()

        # Force recompute via helper method
        self.equipment.update_meter_status()
        self.assertEqual(self.equipment.readings_status, "done")

    def test_remove_from_agreement_button_behaviour(self):
        # Draft agreement -> button should clear link and deactivate line
        agreement = self._create_draft_agreement_with_line(add_meter=False)
        self.equipment.agreement_id = agreement
        # Ensure at least one line exists with this equipment
        line = self.env["service.agreement.line"].search(
            [("agreement_id", "=", agreement.id), ("equipment_id", "=", self.equipment.id)], limit=1
        )
        self.assertTrue(line)
        self.equipment.remove_from_agreement_button()
        self.assertFalse(self.equipment.agreement_id)
        line.invalidate_recordset()
        self.assertFalse(line.active)
        self.assertEqual(line.quantity, 0)

        # Non-draft agreement -> should raise
        agreement_nd = self._create_draft_agreement_with_line(add_meter=False)
        agreement_nd.contract_open()
        self.equipment.agreement_id = agreement_nd
        with self.assertRaises(UserError):
            self.equipment.remove_from_agreement_button()

    def test_name_search_and_display_name(self):
        # EAN search path requires pattern length > 3
        self.equipment.ean_code = "1234567890"
        res = self.env["service.equipment"].name_search("3456")
        ids = [r[0] for r in res]
        self.assertIn(self.equipment.id, ids)
        # Display name is computed
        self.equipment._compute_display_name()
        self.assertTrue(self.equipment.display_name)
