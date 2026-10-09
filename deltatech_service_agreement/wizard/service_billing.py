# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, format_date


class ServiceBilling(models.TransientModel):
    _name = "service.billing"
    _description = "Service Billing"

    journal_id = fields.Many2one(
        "account.journal",
        "Journal",
        required=True,
        domain="[('type', '=',  'sale' ), ('company_id', '=', company_id)]",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    # facturile pot fi facute grupat dupa partner sau dupa contract
    group_invoice = fields.Selection(
        [
            ("partner", "Group by partner"),
            ("agreement", "Group by agreement"),
            ("agreement_line", "Split by agreement line"),
        ],
        string="Group invoice",
        default="agreement",
    )

    # indica daca liniile din facura sunt insumate dupa servicu

    group_service = fields.Boolean(string="Group by service", default=False)

    consumption_ids = fields.Many2many(
        "service.consumption",
        "service_billing_consumption",
        "billing_id",
        "consumption_id",
        string="Consumptions",
        domain=[("invoice_id", "=", False)],
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)
        if "company_id" not in defaults:
            defaults.update({"company_id": self.env.company.id})
        domain = [("state", "=", "draft"), ("company_id", "=", defaults["company_id"])]
        if active_ids:
            domain += [("id", "in", active_ids)]

        res = self.env["service.consumption"].search(domain)
        for cons in res:
            if cons.agreement_id.type_id.journal_id:
                defaults["journal_id"] = cons.agreement_id.type_id.journal_id.id
        defaults["consumption_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    @api.model
    def _get_billed_quantity(self, cons):
        """Cantitatea facturata pentru un consum, aceeasi pe linia facturii si in invoiced_qty.

        O corectie (cantitate negativa) se factureaza integral, fara cantitatea gratuita;
        un consum obisnuit se factureaza peste cantitatea gratuita, niciodata sub zero
        (un ciclu gratuit apare pe factura cu cantitate 0, nu ca o corectie).
        """
        if cons.quantity < 0:
            return cons.quantity
        return max(cons.quantity - cons.agreement_line_id.quantity_free, 0.0)

    @api.model
    def _find_corrected_invoice(self, cons):
        """Factura initiala corectata de un consum negativ.

        Ultimul consum pozitiv facturat pe aceeasi linie de contract, dintr-o perioada
        anterioara perioadei corectiei, cu factura de client postata. Gol daca nu exista.
        """
        Consumption = self.env["service.consumption"]
        if cons.quantity >= 0 or not cons.agreement_line_id:
            return self.env["account.move"]
        domain = [
            ("agreement_line_id", "=", cons.agreement_line_id.id),
            ("id", "!=", cons.id),
            ("state", "=", "done"),
            ("quantity", ">", 0),
            ("invoice_id.state", "=", "posted"),
            ("invoice_id.move_type", "=", "out_invoice"),
        ]
        if cons.service_period_id:
            domain.append(("service_period_id.date_start", "<", cons.service_period_id.date_start))
        previous = Consumption.search(domain)
        if not previous:
            return self.env["account.move"]
        previous = previous.sorted(lambda c: (c.service_period_id.date_start or fields.Date.today(), c.id))
        return previous[-1].invoice_id

    @api.model
    def _get_corrections_without_invoice(self, consumptions):
        """Consumurile negative pentru care nu se gaseste factura initiala."""
        return consumptions.filtered(lambda c: c.quantity < 0 and not self._find_corrected_invoice(c))

    def add_invoice_line(self, cons, pre_invoice, price_unit, name, key):
        # nu mai exista get_invoice_line_account  in V14
        # account_id = self.env["account.move.line"].get_invoice_line_account(
        #     "out_invoice", cons.product_id, "", self.env.user.company_id
        # )

        # contul si taxele se iau pentru compania facturii, nu pentru compania implicita a utilizatorului
        company = self.company_id
        accounts = cons.product_id.product_tmpl_id.with_company(company).get_product_accounts()
        account_id = accounts["income"]
        taxes = cons.product_id.taxes_id._filter_taxes_by_company(company)

        invoice_line = {
            "product_id": cons.product_id.id,
            "quantity": self._get_billed_quantity(cons),
            "price_unit": price_unit,
            "product_uom_id": cons.agreement_line_id.uom_id.id,
            "name": name,
            # todo: de determinat contul
            "account_id": account_id.id,
            "tax_ids": [(6, 0, taxes.ids)],
            "agreement_line_id": cons.agreement_line_id.id,
            # "analytic_account_id": cons.analytic_account_id.id,  # nu mai e in 16.0
        }

        # corectie: referinta la factura initiala (art. 319 alin. (20) lit. r) CF) si
        # taxele liniei din factura initiala (cota operatiunii de baza)
        corrected_invoice = self.env["account.move"]
        warning = False
        if cons.quantity < 0:
            corrected_invoice = self._find_corrected_invoice(cons)
            if not corrected_invoice:
                raise UserError(
                    self.env._(
                        "The correction of product %(product)s on agreement %(agreement)s cannot be invoiced: "
                        "no posted invoice was found for an earlier consumption of this agreement line.",
                        product=cons.product_id.display_name,
                        agreement=cons.agreement_id.name,
                    )
                )
            invoice_line["name"] = "{} - {}".format(
                name,
                self.env._(
                    "Correction of invoice %(invoice)s from %(date)s",
                    invoice=corrected_invoice.name,
                    date=format_date(self.env, corrected_invoice.invoice_date),
                ),
            )
            original_lines = corrected_invoice.invoice_line_ids.filtered(
                lambda line: line.product_id == cons.product_id
            )
            same_agreement_line = original_lines.filtered(lambda line: line.agreement_line_id == cons.agreement_line_id)
            original_line = (same_agreement_line or original_lines)[:1]
            if original_line:
                invoice_line["tax_ids"] = [(6, 0, original_line.tax_ids.ids)]
            else:
                warning = self.env._(
                    "The line of product %(product)s was not found on the corrected invoice %(invoice)s: "
                    "check that the correction uses the VAT rate of the original operation.",
                    product=cons.product_id.display_name,
                    invoice=corrected_invoice.name,
                )

        if pre_invoice[cons.date_invoice].get(key, False):
            pre_invoice[cons.date_invoice][key]["corrected_invoices"] |= corrected_invoice
            if warning:
                pre_invoice[cons.date_invoice][key]["warnings"].append(warning)
            is_prod = False
            if (
                (self.group_service and cons.agreement_id.invoice_mode != "detail")
                or cons.agreement_id.invoice_mode == "service"
            ) and not corrected_invoice:
                for line in pre_invoice[cons.date_invoice][key]["lines"]:
                    if (
                        line["product_id"] == cons.product_id.id
                        and line["quantity"] >= 0
                        and float_compare(
                            line["price_unit"],
                            invoice_line["price_unit"],
                            precision_digits=2,
                        )
                        == 0
                    ):
                        line["quantity"] += invoice_line["quantity"]
                        is_prod = True
                        break
            if not is_prod:
                pre_invoice[cons.date_invoice][key]["lines"].append(invoice_line)
            pre_invoice[cons.date_invoice][key]["cons"] += cons
            pre_invoice[cons.date_invoice][key]["agreement_ids"] |= cons.agreement_id
        else:
            pre_invoice[cons.date_invoice][key] = {
                "lines": [invoice_line],
                "cons": cons,
                "partner_id": cons.partner_id.id,
                "corrected_invoices": corrected_invoice,
                "warnings": [warning] if warning else [],
                # todo: dterminare cont
                # 'account_id':cons.partner_id.property_account_receivable.id,
            }

            pre_invoice[cons.date_invoice][key]["agreement_ids"] = cons.agreement_id

    def _get_invoice_currency(self):
        """Moneda facturii: moneda jurnalului, altfel moneda companiei de facturare."""
        self.ensure_one()
        return self.journal_id.currency_id or self.company_id.currency_id

    def _check_consumption_company(self):
        self.ensure_one()
        other_company = self.consumption_ids.filtered(lambda c: c.company_id and c.company_id != self.company_id)
        if other_company:
            raise UserError(
                self.env._(
                    "Consumptions of company %(other)s cannot be invoiced in company %(company)s.",
                    other=", ".join(other_company.company_id.mapped("name")),
                    company=self.company_id.name,
                )
            )

    def do_billing_step1(self, pre_invoice):
        company = self.company_id
        to_currency = self._get_invoice_currency()
        for cons in self.consumption_ids:
            # convertire pret in moneda facturii, la cursul companiei de facturare
            date = cons.date_invoice or fields.Date.context_today(self)
            price_unit = cons.currency_id._convert(cons.price_unit, to_currency, company, date)
            name = cons.product_id.name

            if cons.name and (cons.agreement_id.invoice_mode == "detail" or not self.group_service):
                name += cons.name

            # if self.group_invoice == "partner":
            key = cons.partner_id.id

            if self.group_invoice == "agreement" or cons.agreement_id.invoice_mode == "detail":
                key = cons.agreement_id.id

            if self.group_invoice == "agreement_line":
                key = cons.agreement_line_id.id

            if cons.quantity > cons.agreement_line_id.quantity_free or cons.quantity < 0 or cons.with_free_cycle:
                self.add_invoice_line(cons, pre_invoice, price_unit, name, key)
                cons.write(
                    {
                        "state": "done",
                        "invoiced_qty": self._get_billed_quantity(cons),
                    }
                )
            else:  # cons.quantity < cons.agreement_line_id.quantity_free:
                cons.write({"state": "none"})

    def do_billing(self):
        self._check_consumption_company()
        pre_invoice = {}  # lista de facuri
        agreements = self.env["service.agreement"]

        for cons in self.consumption_ids:
            pre_invoice[cons.date_invoice] = {}
            agreements |= cons.agreement_id

        self.do_billing_step1(pre_invoice)

        for cons in self.consumption_ids.filtered(lambda r: r.state == "none"):
            if self.group_invoice == "agreement" or cons.agreement_id.invoice_mode == "detail":
                key = cons.agreement_id.id
            else:
                key = cons.partner_id.id
            if pre_invoice[cons.date_invoice].get(key, False):
                # daca a fost generata o factura atunci leg si consumul de facura pentru a aparea in centralizator
                pre_invoice[cons.date_invoice][key]["cons"] += cons

        if not pre_invoice:
            raise UserError(self.env._("No condition for create a new invoice"))

        service_invoices = self.env["account.move"]

        for date_invoice in pre_invoice:
            for key in pre_invoice[date_invoice]:
                comment = self.env._("According to agreement ")
                payment_term_id = False
                for agreement in pre_invoice[date_invoice][key]["agreement_ids"]:
                    comment += self.env._("%(agreement_name)s from %(agreement_date)s \n") % {
                        "agreement_name": agreement.name or "____",
                        "agreement_date": agreement.date_agreement or "____",
                    }
                if len(pre_invoice[date_invoice][key]["agreement_ids"]) > 1:
                    payment_term_id = False
                    user_id = False
                else:
                    for agreement in pre_invoice[date_invoice][key]["agreement_ids"]:
                        payment_term_id = (
                            agreement.payment_term_id.id or agreement.partner_id.property_payment_term_id.id
                        )
                        user_id = agreement.user_id.id
                lines = pre_invoice[date_invoice][key]["lines"]
                # corectiile negative nu se mai taie: daca valoarea neta e negativa,
                # documentul devine nota de credit (cantitati cu semn inversat), altfel
                # corectia ramane linie negativa pe factura
                move_type = "out_invoice"
                net_amount = sum(line["quantity"] * line["price_unit"] for line in lines)
                if float_compare(net_amount, 0.0, precision_digits=2) < 0:
                    move_type = "out_refund"
                    for line in lines:
                        line["quantity"] = -line["quantity"]
                invoice_value = {
                    # 'name': _('Invoice'),
                    "partner_id": pre_invoice[date_invoice][key]["partner_id"],
                    "journal_id": self.journal_id.id,
                    "company_id": self.company_id.id,
                    "currency_id": self._get_invoice_currency().id,
                    "invoice_date": date_invoice,
                    "invoice_payment_term_id": payment_term_id,
                    # todo: de determinat contul
                    # 'account_id': pre_invoice[date_invoice][key]['account_id'],
                    "move_type": move_type,
                    "state": "draft",
                    "invoice_line_ids": [(0, 0, x) for x in lines],
                    "narration": comment,
                    "invoice_user_id": user_id,
                    # 'agreement_id':pre_invoice[key]['agreement_id'],
                }
                corrected_invoices = pre_invoice[date_invoice][key]["corrected_invoices"]
                if corrected_invoices:
                    invoice_value["ref"] = ", ".join(corrected_invoices.mapped("name"))
                    if move_type == "out_refund" and len(corrected_invoices) == 1:
                        invoice_value["reversed_entry_id"] = corrected_invoices.id
                invoice_id = self.env["account.move"].create(invoice_value)
                for warning in pre_invoice[date_invoice][key]["warnings"]:
                    invoice_id.message_post(body=warning)
                # todo: de determinat care e butonul de calcul tva
                # invoice_id.button_compute(True)
                pre_invoice[date_invoice][key]["cons"].write({"invoice_id": invoice_id.id})
                service_invoices |= invoice_id

        agreements.compute_totals()
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_service_agreement.action_service_invoice")
        action["domain"] = [("id", "in", service_invoices.ids)]
        return action
