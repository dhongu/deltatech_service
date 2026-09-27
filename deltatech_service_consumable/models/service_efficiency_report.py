# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.fields import Domain


class ServiceEfficiencyReport(models.Model):
    _name = "service.efficiency.report"
    _inherit = "stock.picking.report"
    _description = "ServiceEfficiencyReport"

    equipment_id = fields.Many2one("service.equipment", string="Equipment", index=True)
    agreement_id = fields.Many2one("service.agreement", string="Contract Services")
    usage = fields.Float(
        string="Usage",
        digits="Product Unit",
        readonly=True,
        compute="_compute_usage",
        store=True,
    )
    uom_usage = fields.Many2one(
        "uom.uom",
        string="Unit of Measure Usage",
        help="Unit of Measure for Usage",
        index=True,
    )
    shelf_life = fields.Float(string="Shelf Life", digits="Product Unit")

    def _select(self):
        select_str = (
            super()._select()
            + """,
                  sp.equipment_id,
                  equi.agreement_id,
                  0 as usage,
                  sum(sm.product_qty)*avg(pt.shelf_life) as shelf_life,
                  pt.uom_shelf_life as uom_usage
                """
        )
        return select_str

    def _from(self):
        from_str = (
            super()._from()
            + """

                       INNER JOIN service_equipment as equi ON  sp.equipment_id = equi.id
                    """
        )
        return from_str

    def _group_by(self):
        group_by_str = super()._group_by() + ", sp.equipment_id, equi.agreement_id, pt.uom_shelf_life"
        return group_by_str

    def _compute_usage(self):
        self.usage = 0.0

    @api.model
    def formatted_read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        # In 20.0 `read_group` are altă semnătură și întoarce tupluri; gruparea din interfață (și
        # `_compute_quantity`) trece prin `formatted_read_group`. `usage` nu se poate agrega în SQL:
        # se calculează pe fiecare grup din contorul echipamentului, ca în 19.0.
        res = super().formatted_read_group(
            domain, groupby, aggregates, having=having, offset=offset, limit=limit, order=order
        )
        usage_specs = [spec for spec in aggregates if spec.split(":")[0] == "usage"]
        if usage_specs:
            for line in res:
                usage = self._get_usage_from_domain(Domain(domain) & Domain(line.get("__extra_domain", [])))
                for spec in usage_specs:
                    line[spec] = usage
        return res

    @api.model
    def _get_usage_from_domain(self, domain):
        begin_date = "2000-01-01"
        end_date = "2999-12-31"
        product_id = False
        uom_usage = False
        equipment_id = False
        for cond in Domain(domain).iter_conditions():
            field_name, operator, value = cond.field_expr, cond.operator, cond.value
            if isinstance(value, models.BaseModel):
                value = value.id
            elif isinstance(value, list | tuple | set | frozenset):
                # `Domain` normalizează `=` în `in` pe many2one
                if len(value) != 1:
                    continue
                value = next(iter(value))
            if field_name == "date":
                if operator in (">=", ">"):
                    begin_date = value
                if operator in ("<", "<="):
                    end_date = value
            if field_name == "equipment_id":
                equipment_id = value
            if field_name == "product_id":
                product_id = value
            if field_name == "uom_usage":
                uom_usage = value
        return self.get_usage(begin_date, end_date, equipment_id, uom_usage, product_id)

    @api.model
    def get_usage(self, begin_date, end_date, equipment_id, uom_usage, product_id):
        usage = 0
        if not uom_usage and product_id:
            product = self.env["product.product"].browse(product_id)
            if product:
                uom_usage = product.uom_shelf_life.id

        if uom_usage and equipment_id:
            uom = self.env["uom.uom"].browse(uom_usage)
            meters = self.env["service.meter"].search([("equipment_id", "=", equipment_id)])
            meters = meters.filtered(lambda m: m.uom_id._has_common_reference(uom))

            if meters:
                meter_find = meters[0]
            else:
                meter_find = False

            for meter in meters:
                if meter.uom_id == uom:
                    meter_find = meter

            if meter_find:
                usage = meter_find.get_counter_value(begin_date, end_date)
                from_uom = meter_find.uom_id
                to_uom = uom
                usage = usage / from_uom.factor
                usage = usage * to_uom.factor

        return usage
