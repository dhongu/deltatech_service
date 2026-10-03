# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.fields import Domain
from odoo.tools import SQL


class ObjectHistory(models.Model):
    """
    Parallel document history
    """

    _name = "object.history"
    _description = "Object history"
    _inherit = ["mail.thread"]
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char("Name", required=True)
    object_name = fields.Char(string="Parent name")
    partner_id = fields.Many2one("res.partner", string="Related partner")
    description = fields.Html("Description")
    res_model = fields.Char(
        "Resource Model",
        readonly=True,
        index=True,
        help="The database model this history will be attached to.",
    )
    res_id = fields.Many2oneReference(
        "Resource ID",
        model_field="res_model",
        readonly=True,
        index=True,
        help="The record id this is attached to.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        change_default=True,
        default=lambda self: self.env.company,
    )

    # ------------------------------------------------------------------
    # Access: a history row is visible only if its parent document is
    # ------------------------------------------------------------------
    # The company is enforced by the global record rule. On top of it, a
    # history row attached to a document (res_model / res_id) follows the read
    # access of that document. History whose document was deleted, or whose
    # model is no longer installed, is visible only to history managers.

    def _is_history_manager(self):
        return self.env.user.has_group("deltatech_object_history.group_history_manager")

    @api.model
    def _get_parent_access_domain(self):
        """Domain that keeps the history rows whose parent document the current user can read."""
        self.env.cr.execute(
            SQL(
                "SELECT DISTINCT res_model FROM %s WHERE res_model IS NOT NULL AND res_model != ''",
                SQL.identifier(self._table),
            )
        )
        res_models = [row[0] for row in self.env.cr.fetchall()]
        is_manager = self._is_history_manager()
        domains = [Domain("res_model", "in", [False, ""])]
        for res_model in res_models:
            parent_model = self.env.get(res_model)
            if parent_model is None or parent_model._abstract:
                if is_manager:
                    domains.append(Domain("res_model", "=", res_model))
                continue
            if parent_model.browse().has_access("read"):
                parent_query = parent_model.with_context(active_test=False)._search([])
                domains.append(Domain("res_model", "=", res_model) & self._res_id_in_query_domain(parent_query))
            if is_manager:
                existing_query = parent_model.sudo().with_context(active_test=False)._search([])
                domains.append(
                    Domain("res_model", "=", res_model) & self._res_id_in_query_domain(existing_query, negate=True)
                )
        return Domain.OR(domains)

    @api.model
    def _res_id_in_query_domain(self, query, negate=False):
        def to_sql(model, alias, sql_query):
            return SQL(
                "%s %s %s",
                model._field_to_sql(alias, "res_id", sql_query),
                SQL("NOT IN") if negate else SQL("IN"),
                query.subselect(),
            )

        return Domain.custom(to_sql=to_sql)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, *, bypass_access=False, **kwargs):
        if self.env.su or bypass_access:
            return super()._search(domain, offset, limit, order, bypass_access=bypass_access, **kwargs)
        self.browse().check_access("read")
        domain = Domain(domain) & self._get_parent_access_domain()
        return super()._search(domain, offset, limit, order, **kwargs)

    def _check_access(self, operation):
        result = super()._check_access(operation)
        if not self:
            return result
        candidates = self - result[0] if result else self
        forbidden = candidates - candidates._filter_parent_access()
        if not forbidden:
            return result
        if result:
            return result[0] + forbidden, result[1]
        return forbidden, lambda: forbidden._make_parent_access_error(operation)

    def _filter_parent_access(self):
        """Return the history rows whose parent document the current user can read."""
        allowed_ids = set()
        by_model = defaultdict(lambda: defaultdict(list))
        for history in self.sudo():
            if not history.res_model:
                allowed_ids.add(history.id)
            else:
                by_model[history.res_model][history.res_id].append(history.id)
        is_manager = None
        for res_model, history_by_res_id in by_model.items():
            parent_model = self.env.get(res_model)
            if parent_model is None or parent_model._abstract:
                existing_ids, readable_ids = set(), set()
            else:
                parents = parent_model.browse(list(history_by_res_id)).sudo().exists()
                existing_ids = set(parents.ids)
                readable_ids = set(parents.with_env(self.env)._filtered_access("read").ids)
            for res_id, history_ids in history_by_res_id.items():
                if res_id in readable_ids:
                    allowed_ids.update(history_ids)
                elif res_id not in existing_ids:
                    if is_manager is None:
                        is_manager = self._is_history_manager()
                    if is_manager:
                        allowed_ids.update(history_ids)
        return self.browse([history_id for history_id in self.ids if history_id in allowed_ids])

    def _make_parent_access_error(self, operation):
        return AccessError(
            self.env._(
                "You cannot access this history (%(operation)s) because you do not have access "
                "to the document it belongs to.",
                operation=operation,
            )
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # the history belongs to the company of its document, not to the active company
            if vals.get("company_id") or not vals.get("res_model") or not vals.get("res_id"):
                continue
            parent_model = self.env.get(vals["res_model"])
            if parent_model is None or "company_id" not in parent_model._fields:
                continue
            parent = parent_model.sudo().browse(vals["res_id"]).exists()
            parent_company = parent.company_id if parent else False
            if parent_company and len(parent_company) == 1:
                vals["company_id"] = parent_company.id
        return super().create(vals_list)

    def action_open_document(self):
        """Opens the related record based on the model and ID"""
        self.ensure_one()
        return {
            "res_id": self.res_id,
            "res_model": self.res_model,
            "target": "current",
            "type": "ir.actions.act_window",
            "view_mode": "form",
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if (
            "res_model" in res
            and res["res_model"]
            and "res_id" in res
            and res["res_id"]
            and (
                res["res_model"] == "res.partner"
                or res["res_model"] == "account.move"
                or res["res_model"] == "stock.picking"
            )
        ):
            parent = self.env[res["res_model"]].browse(res["res_id"])
            if res["res_model"] == "res.partner":
                partner = self.env["res.partner"].browse(res["res_id"])
                res["partner_id"] = partner.id
            res["object_name"] = parent.name

        return res
