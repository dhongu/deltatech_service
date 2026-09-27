# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import Command
from odoo.tests import Form

from odoo.addons.deltatech_service_agreement.tests.test_agreement import TestAgreement
from odoo.addons.deltatech_service_equipment_base.tests.test_service import TestService


class TestAgreementEquipment(TestAgreement, TestService):
    def setUp(self):
        super().setUp()
        self.get_str = self.env["ir.config_parameter"].sudo().get_str
        picking_type_for_service = self.get_str("service.picking_type_for_service")
        if not picking_type_for_service:
            picking_type_for_service = self.env["stock.picking.type"].create(
                {
                    "name": "Test Picking Type",
                    "code": "outgoing",
                    "sequence_code": "TEST",
                }
            )
            self.env["ir.config_parameter"].sudo().set_str(
                "service.picking_type_for_service", picking_type_for_service.id
            )

        self.consumable_item = self.env["service.consumable.item"].create(
            {
                "type_id": self.equipment_type.id,
                "product_id": self.product_ab.id,
            }
        )

        self.equipment = self.env["service.equipment"].create(
            {
                "name": "Test Equipment",
                "type_id": self.equipment_type.id,
                "model_id": self.equipment_model.id,
            }
        )
        self.meter = self.env["service.meter"].create(
            {
                "name": "Test Meter",
                "meter_categ_id": self.meter_category.id,
                "equipment_id": self.equipment.id,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

    def test_equipment(self):
        self.quantity = self.consumable_item.with_context(equipment_id=self.equipment.id).quantity
        self.equipment.new_piking_button()
        consumables = self.equipment.consumable_item_ids
        self.assertEqual(len(consumables), 1)

        self.equipment.delivered_button()
        self.equipment.picking_button()

    def test_agreement(self):
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle

        with agreement.agreement_line.new() as agreement_line:
            agreement_line.product_id = self.product_ab
            agreement_line.quantity = 1
            agreement_line.price_unit = 100
            agreement_line.equipment_id = self.equipment
            agreement_line.meter_id = self.meter

        agreement = agreement.save()
        agreement.contract_open()

        agreement.picking_button()
        agreement.compute_costs()
        agreement.compute_percent()

    def test_picking(self):
        picking_type_id = self.env["ir.config_parameter"].sudo().get_int("service.picking_type_for_service")

        picking_type_for_service = self.env["stock.picking.type"].browse(picking_type_id)

        picking = Form(self.env["stock.picking"])
        picking.partner_id = self.partner_1
        picking.picking_type_id = picking_type_for_service
        picking.equipment_id = self.equipment
        with picking.move_ids.new() as move:
            move.product_id = self.product_ab
            move.product_uom_qty = 1
            # move.product_uom_id = self.product_ab.uom_id

        picking = picking.save()
        picking.check_consumable()
        picking.action_assign()

        self.env["service.efficiency.report"].get_usage(
            "2000-01-01",
            "2999-12-31",
            self.equipment.id,
            self.product_ab.uom_id.id,
            self.product_ab.id,
        )

    def test_picking_validate_costs(self):
        # costurile consumabilelor livrate pe contract sunt negative (`stock.move.value` la ieșiri),
        # iar procentul (-1 * costuri / facturat) iese pozitiv
        picking_type_id = self.env["ir.config_parameter"].sudo().get_int("service.picking_type_for_service")
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        stock_location = warehouse.lot_stock_id
        customer_location = self.env.ref("stock.stock_location_customers")
        product = self.env["product.product"].create(
            {"name": "Toner", "is_storable": True, "standard_price": 10.0, "shelf_life": 100}
        )
        self.env["stock.quant"]._update_available_quantity(product, stock_location, 5)
        agreement = self.env["service.agreement"].create(
            {
                "name": "Test Agreement",
                "partner_id": self.partner_1.id,
                "type_id": self.agreement_type.id,
                "cycle_id": self.cycle.id,
            }
        )
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner_1.id,
                "picking_type_id": picking_type_id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
                "agreement_id": agreement.id,
                "equipment_id": self.equipment.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": 2,
                            "location_id": stock_location.id,
                            "location_dest_id": customer_location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertAlmostEqual(agreement.total_costs, -20.0)
        agreement.compute_costs()
        self.assertAlmostEqual(agreement.total_costs, -20.0)
        agreement.write({"total_invoiced": 100.0})
        agreement.compute_percent()
        self.assertAlmostEqual(agreement.total_percent, 20.0)

        self.env.flush_all()  # raportul e un view SQL
        report = self.env["service.efficiency.report"]
        groups = report.formatted_read_group(
            [("equipment_id", "=", self.equipment.id)],
            groupby=["equipment_id", "product_id"],
            aggregates=["usage:sum", "shelf_life:sum"],
        )
        self.assertEqual(len(groups), 1)
        self.assertIn("usage:sum", groups[0])
        item = self.env["service.consumable.item"].create({"type_id": self.equipment_type.id, "product_id": product.id})
        self.assertEqual(item.with_context(equipment_id=self.equipment.id).quantity, 200.0)
