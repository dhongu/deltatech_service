# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEfficiencyReportCompany(TransactionCase):
    """CONSUMABLE-003: the efficiency report must follow the user's active companies"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Efficiency Company B"})
        cls.product = cls.env["product.product"].create(
            {"name": "Efficiency Toner", "type": "consu", "is_storable": True, "standard_price": 10.0}
        )
        cls.equipment = cls.env["service.equipment"].create({"name": "Efficiency Equipment"})
        cls.picking_a = cls._create_done_delivery(cls.company_a)
        cls.picking_b = cls._create_done_delivery(cls.company_b)
        cls.pickings = cls.picking_a | cls.picking_b
        cls.env.flush_all()

        groups = "stock.group_stock_manager"
        cls.user_a = new_test_user(
            cls.env,
            login="efficiency_user_a",
            groups=groups,
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.user_ab = new_test_user(
            cls.env,
            login="efficiency_user_ab",
            groups=groups,
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a | cls.company_b).ids)],
        )

    @classmethod
    def _create_done_delivery(cls, company):
        env = cls.env(context=dict(cls.env.context, allowed_company_ids=company.ids))
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        customers = env.ref("stock.stock_location_customers")
        env["stock.quant"]._update_available_quantity(cls.product, warehouse.lot_stock_id, 10.0)
        picking = env["stock.picking"].create(
            {
                "picking_type_id": warehouse.out_type_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": customers.id,
                "equipment_id": cls.equipment.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 2.0,
                            "location_id": warehouse.lot_stock_id.id,
                            "location_dest_id": customers.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.write({"quantity": 2.0, "picked": True})
        picking.button_validate()
        return picking

    def _report_companies(self, user, companies):
        report = self.env["service.efficiency.report"].with_user(user).with_context(allowed_company_ids=companies.ids)
        rows = report.search([("picking_id", "in", self.pickings.ids)])
        return rows.mapped("company_id")

    def test_deliveries_in_report_for_both_companies(self):
        self.assertEqual(self.picking_a.state, "done")
        self.assertEqual(self.picking_b.state, "done")
        rows = self.env["service.efficiency.report"].sudo().search([("picking_id", "in", self.pickings.ids)])
        self.assertEqual(rows.mapped("company_id"), self.company_a | self.company_b)

    def test_single_company_user_sees_only_own_company(self):
        self.assertEqual(self._report_companies(self.user_a, self.company_a), self.company_a)

    def test_multi_company_user_sees_active_companies(self):
        both = self.company_a | self.company_b
        self.assertEqual(self._report_companies(self.user_ab, both), both)
        # after switching to company A only, company B rows are hidden
        self.assertEqual(self._report_companies(self.user_ab, self.company_a), self.company_a)

    def test_full_read_of_report_rows(self):
        """CONSUMABLE-004: no log-access fields without a column in the SQL view"""
        report = self.env["service.efficiency.report"]
        for fname in ("create_uid", "create_date", "write_uid", "write_date"):
            self.assertNotIn(fname, report._fields)
        rows = report.search([])
        self.assertTrue(rows)
        rows.invalidate_recordset()
        values = rows.read()
        self.assertEqual(len(values), len(rows))
        self.assertTrue(rows.mapped("company_id"))
