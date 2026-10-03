# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestObjectHistoryAccess(TransactionCase):
    """HISTORY-001: history follows the company rules and the access to its parent document."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "History Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "History Company B"})
        cls.user = new_test_user(
            cls.env,
            login="history_user_a",
            groups="base.group_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.manager = new_test_user(
            cls.env,
            login="history_manager_a",
            groups="base.group_user,deltatech_object_history.group_history_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.partner_a = cls.env["res.partner"].create({"name": "Partner A", "company_id": cls.company_a.id})
        cls.partner_b = cls.env["res.partner"].create({"name": "Partner B", "company_id": cls.company_b.id})
        History = cls.env["object.history"]
        cls.history_a = History.create(
            {"name": "Visible", "res_model": "res.partner", "res_id": cls.partner_a.id, "company_id": cls.company_a.id}
        )
        # same company as the user, but attached to a document the user cannot read
        cls.history_hidden_parent = History.create(
            {"name": "Hidden parent", "res_model": "res.partner", "res_id": cls.partner_b.id, "company_id": cls.company_a.id}
        )
        # no parent document, other company
        cls.history_b = History.create({"name": "Other company", "company_id": cls.company_b.id})
        # no parent document, user company
        cls.history_free = History.create({"name": "Free note", "company_id": cls.company_a.id})

    def _search_as(self, user):
        return self.env["object.history"].with_user(user).search(
            [("id", "in", (self.history_a | self.history_hidden_parent | self.history_b | self.history_free).ids)]
        )

    def test_search_filters_company_and_parent(self):
        found = self._search_as(self.user)
        self.assertEqual(found, self.history_a | self.history_free)
        self.assertEqual(
            self.env["object.history"].with_user(self.user).search_count([("res_model", "=", "res.partner")]),
            len(self.env["object.history"].with_user(self.user).search([("res_model", "=", "res.partner")])),
        )

    def test_read_other_company_history_raises(self):
        with self.assertRaises(AccessError):
            self.history_b.with_user(self.user).read(["name", "description"])

    def test_read_history_of_unreadable_parent_raises(self):
        with self.assertRaises(AccessError):
            self.history_hidden_parent.with_user(self.user).read(["name", "description", "object_name"])
        self.assertFalse(self.history_hidden_parent.with_user(self.user).has_access("read"))
        self.assertTrue(self.history_a.with_user(self.user).has_access("read"))

    def test_history_count_on_parent(self):
        self.assertEqual(self.partner_a.with_user(self.user).history_count, 1)

    def test_deleted_parent_visible_only_to_manager(self):
        partner = self.env["res.partner"].create({"name": "Deleted partner", "company_id": self.company_a.id})
        orphan = self.env["object.history"].create(
            {"name": "Orphan", "res_model": "res.partner", "res_id": partner.id, "company_id": self.company_a.id}
        )
        partner.unlink()
        self.assertFalse(self.env["object.history"].with_user(self.user).search([("id", "=", orphan.id)]))
        with self.assertRaises(AccessError):
            orphan.with_user(self.user).read(["name"])
        self.assertEqual(self.env["object.history"].with_user(self.manager).search([("id", "=", orphan.id)]), orphan)
        orphan.with_user(self.manager).read(["name"])
        # the manager is still bound to the parent access and to the company rule
        self.assertEqual(self._search_as(self.manager), self.history_a | self.history_free)

    def test_create_takes_company_of_parent(self):
        history = (
            self.env["object.history"]
            .with_company(self.company_a)
            .create({"name": "From B", "res_model": "res.partner", "res_id": self.partner_b.id})
        )
        self.assertEqual(history.company_id, self.company_b)
