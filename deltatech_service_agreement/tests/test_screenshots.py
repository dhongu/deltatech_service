# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant (RO) și pentru readme/USAGE.md (EN), plus GIF-ul demo.
# Fluxul: contract în derulare -> pregătire facturare (consumuri) -> corecții pe consumuri ->
# facturare -> facturi și situația contractului.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_service_agreement,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestServiceAgreementScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_service_agreement"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        # tooling-ul de capturi trăiește în suita deltatech și poate lipsi din CI-ul acestui repo
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.env = cls.env(su=True)
        cls.prepare_ro_company(name="Servicii IT Demo SRL")
        env = cls.env
        company = env.company
        env.ref("base.user_admin").write(
            {"company_ids": [(4, company.id)], "company_id": company.id, "lang": "ro_RO", "tz": "Europe/Bucharest"}
        )
        cls.journal = env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", company.id)], limit=1
        )
        # agentul de vânzări apare pe capturi: un nume potrivit pentru un manual
        env.ref("base.user_admin").partner_id.name = "Andrei Popescu"
        cls.journal.service_invoice = True
        cls.agreement_type = env["service.agreement.type"].create(
            {"name": "Abonamente servicii IT", "journal_id": cls.journal.id}
        )
        cls.group = env["service.agreement.group"].create({"name": "Mentenanță"})
        Product = env["product.product"]
        cls.product_maint = Product.create(
            {"name": "Mentenanță aplicație", "type": "service", "list_price": 1200.0, "taxes_id": [Command.clear()]}
        )
        cls.product_support = Product.create(
            {"name": "Suport tehnic (ore)", "type": "service", "list_price": 150.0, "taxes_id": [Command.clear()]}
        )
        # serviciile se înregistrează pe 704 „Venituri din servicii prestate”, nu pe 707 (mărfuri)
        income_704 = env["account.account"].search(
            [("code", "=", "704000"), ("company_ids", "in", company.id)], limit=1
        )
        assert income_704, "Contul 704000 lipsește: capturile s-ar genera cu contul 707"
        (cls.product_maint | cls.product_support).write({"property_account_income_id": income_704.id})
        vat = env["account.tax"].search(
            [
                ("type_tax_use", "=", "sale"),
                ("amount_type", "=", "percent"),
                ("company_id", "=", company.id),
                ("amount", "=", 21),
            ],
            limit=1,
        )
        if vat:
            (cls.product_maint | cls.product_support).write({"taxes_id": [Command.set(vat.ids)]})
        cls.cycle = env.ref("deltatech_service_agreement.cycle_monthly")
        Partner = env["res.partner"]
        cls.partner_1 = Partner.create({"name": "Ferma Verde SRL", "is_company": True, "country_id": env.ref("base.ro").id})
        cls.partner_2 = Partner.create({"name": "Transport Rapid SRL", "is_company": True, "country_id": env.ref("base.ro").id})
        cls.partner_3 = Partner.create({"name": "Atelier Mecanic SRL", "is_company": True, "country_id": env.ref("base.ro").id})
        today = fields.Date.today()
        start = today + relativedelta(day=1)
        end = start + relativedelta(months=1, days=-1)
        cls.period = env["service.date.range"].search([("date_start", "=", start), ("date_end", "=", end)], limit=1)
        if not cls.period:
            cls.period = env["service.date.range"].create(
                {"name": f"{start:%Y/%m}", "date_start": start, "date_end": end}
            )
        ron = env.ref("base.RON")

        def agreement(name, partner, lines, state="open", description=False, date=None):
            record = env["service.agreement"].create(
                {
                    "name": name,
                    "user_id": env.ref("base.user_admin").id,
                    "partner_id": partner.id,
                    "payment_term_id": env.ref("account.account_payment_term_30days").id,
                    "description": description,
                    "company_id": company.id,
                    "type_id": cls.agreement_type.id,
                    "group_id": cls.group.id,
                    "cycle_id": cls.cycle.id,
                    "currency_id": ron.id,
                    "invoice_day": -1,
                    "date_agreement": date or (today - relativedelta(months=1)),
                    "agreement_line": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "quantity": qty,
                                "price_unit": price,
                                "currency_id": ron.id,
                                "uom_id": product.uom_id.id,
                            }
                        )
                        for product, qty, price in lines
                    ],
                }
            )
            if state == "open":
                record.contract_open()
            return record

        cls.agr_1 = agreement(
            "AG/00001",
            cls.partner_1,
            [(cls.product_maint, 1, 1200.0), (cls.product_support, 10, 150.0)],
            description="Mentenanță și suport aplicație de gestiune",
        )
        cls.agr_2 = agreement("AG/00002", cls.partner_2, [(cls.product_maint, 1, 1200.0)], description="Mentenanță aplicație flotă")
        cls.agr_3 = agreement(
            "AG/00003",
            cls.partner_3,
            [(cls.product_support, 4, 150.0)],
            state="draft",
            description="Suport tehnic la cerere",
            date=today,
        )
        # contract nou, nesalvat încă ca „în derulare”: îl arătăm în ciornă
        env.flush_all()

    # --- pași de flux executați în baza seedată -------------------------------------------------

    def _prepare(self):
        """Pregătirea facturării pe contractele în derulare: creează consumurile perioadei."""
        agreements = self.agr_1 | self.agr_2
        preparation = self.env["service.billing.preparation"].create(
            {
                "service_period_id": self.period.id,
                "company_id": self.env.company.id,
                "agreement_ids": [Command.set(agreements.ids)],
            }
        )
        preparation.do_billing_preparation()
        return self.env["service.consumption"].search([("agreement_id", "in", agreements.ids)])

    def _bill(self, consumptions, lang="ro_RO"):
        # textul din factură (ex. „Conform contractului”) se traduce în limba utilizatorului
        billing = self.env["service.billing"].with_context(lang=lang).create(
            {
                "company_id": self.env.company.id,
                "journal_id": self.journal.id,
                "consumption_ids": [Command.set(consumptions.ids)],
            }
        )
        action = billing.do_billing()
        invoices = self.env["account.move"].search(action["domain"])
        return invoices

    def _menu(self, xmlid):
        return self.env.ref(f"deltatech_service_agreement.{xmlid}").id

    def _action(self, xmlid):
        return self.env.ref(f"deltatech_service_agreement.{xmlid}").id

    def _shots_before(self):
        act_agr = self._action("action_service_agreement")
        menu_agr = self._menu("menu_service_agreement")
        act_type = self._action("action_service_agreement_type")
        menu_type = self._menu("menu_service_agreement_type")
        act_prep = self._action("action_service_billing_preparation")
        return [
            {
                "url": f"action={act_agr}&menu_id={menu_agr}&model=service.agreement&view_type=list",
                "name": "01_lista_contracte.png",
                "wait": ".o_list_view",
                "highlight": ["th[data-name='state']", "th[data-name='next_date_invoice'], th[data-name='last_date_invoice']"],
            },
            {
                "url": f"id={self.agr_3.id}&action={act_agr}&menu_id={menu_agr}&model=service.agreement&view_type=form",
                "name": "02_contract_nou.png",
                "wait": ".o_form_view",
                "highlight": [
                    "div[name='partner_id']",
                    "div[name='cycle_id']",
                    "div[name='invoice_day']",
                    "button[name='contract_open']",
                ],
                "full": True,
            },
            {
                "url": f"id={self.agr_1.id}&action={act_agr}&menu_id={menu_agr}&model=service.agreement&view_type=form",
                "name": "03_contract_in_derulare.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='contract_close']", "div[name='next_date_invoice']"],
                "full": True,
            },
            {
                "url": f"action={act_type}&menu_id={menu_type}&model=service.agreement.type&view_type=list",
                "name": "04_tip_contract.png",
                "wait": ".o_list_view",
            },
            {
                "url": f"id={self.journal.id}&model=account.journal&view_type=form",
                "name": "05_jurnal_facturi_servicii.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='service_invoice']"],
            },
            {
                "url": f"action={act_prep}&menu_id={self._menu('menu_service_agr')}",
                "name": "06_pregatire_facturare.png",
                "wait": ".modal .o_form_view",
                "click_btn": ".modal div[name='service_period_id'] input",
                "wait_after": ".o-autocomplete--dropdown-menu",
                "highlight": ["div[name='service_period_id']", ".modal-footer button.btn-primary"],
            },
        ]

    def _shots_consumptions(self, consumptions):
        act_cons = self._action("action_service_consumption")
        menu_cons = self._menu("menu_service_consumption")
        ids = ",".join(map(str, consumptions.ids))
        act_price = self._action("action_service_price_change")
        act_dist = self._action("action_service_distribution")
        act_date = self._action("action_service_change_invoice_date")
        first = consumptions.filtered(lambda c: c.product_id == self.product_support)[:1]
        return [
            {
                "url": f"action={act_cons}&menu_id={menu_cons}&model=service.consumption&view_type=list",
                "name": "07_consumuri_pregatite.png",
                "wait": ".o_list_view",
                "highlight": ["tbody tr:first-child td[name='quantity']", "tbody tr:first-child td[name='price_unit']"],
            },
            {
                "url": f"action={act_price}&active_id={first.id}&active_ids={first.id}&model=service.consumption",
                "name": "08_modificare_pret.png",
                "wait": ".modal .o_form_view",
                "highlight": ["div[name='price_unit']", "div[name='reference']"],
            },
            {
                "url": f"action={act_dist}&active_id={first.id}&active_ids={first.id}&model=service.consumption",
                "name": "09_distributie.png",
                "wait": ".modal .o_form_view",
                "highlight": ["div[name='type']", "div[name='mode']", "div[name='quantity']"],
            },
            {
                "url": f"action={act_date}&active_id={ids.split(',')[0]}&active_ids={ids}&model=service.consumption",
                "name": "10_schimbare_data.png",
                "wait": ".modal .o_form_view",
                "eval": "document.activeElement && document.activeElement.blur(); document.querySelector('.modal-title').click()",
                "highlight": ["div[name='date_invoice']"],
            },
            {
                "url": (
                    f"action={self._action('action_service_billing')}&active_ids={ids}"
                    f"&menu_id={self._menu('menu_service_billing')}"
                ),
                "name": "11_facturare.png",
                "wait": ".modal .o_form_view",
                "highlight": ["div[name='journal_id']", "div[name='group_invoice']"],
            },
        ]

    def _shots_invoices(self, invoice):
        act_inv = self._action("action_service_invoice")
        menu_inv = self._menu("menu_service_invoice")
        act_agr = self._action("action_service_agreement")
        return [
            {
                "url": f"action={act_inv}&menu_id={menu_inv}&model=account.move&view_type=list",
                "name": "12_facturi_generate.png",
                "wait": ".o_list_view",
            },
            {
                "url": f"id={invoice.id}&action={act_inv}&model=account.move&view_type=form",
                "name": "13_factura_servicii.png",
                "wait": ".o_form_view",
                "highlight": ["div.o-form-buttonbox button:last-child"],
                "full": True,
            },
            {
                "url": f"id={self.agr_1.id}&action={act_agr}&model=service.agreement&view_type=form",
                "name": "14_contract_dupa_facturare.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='last_invoice_id']", "div[name='next_date_invoice']", "button[name='show_invoices']"],
                "full": True,
            },
        ]

    def _capture_flow(self, lang):
        kwargs = {"lang": lang} if lang != "ro_RO" else {}
        self.capture_screenshots(self._shots_before(), **kwargs)
        consumptions = self._prepare()
        self.capture_screenshots(self._shots_consumptions(consumptions), **kwargs)
        invoices = self._bill(consumptions, lang)
        invoice = invoices.filtered(lambda m: m.partner_id == self.partner_1)[:1] or invoices[:1]
        invoice.action_post()
        self.capture_screenshots(self._shots_invoices(invoice), **kwargs)
        # nota contabilă a facturii postate (liniile Dr/Cr)
        self.capture_screenshots([self.account_move_shot(invoice, "15_nota_contabila.png")], **kwargs)

    def test_capture_fise(self):
        self._capture_flow("ro_RO")

    def test_capture_usage(self):
        self._capture_flow("en_US")

    # --- GIF demo -------------------------------------------------------------------------------

    def _gif_steps(self):
        act_agr = self._action("action_service_agreement")
        menu_agr = self._menu("menu_service_agreement")
        act_prep = self._action("action_service_billing_preparation")
        act_bill = self._action("action_service_billing")
        menu_bill = self._menu("menu_service_billing")
        return [
            {
                "goto": f"id={self.agr_1.id}&action={act_agr}&menu_id={menu_agr}&model=service.agreement&view_type=form",
            },
            {
                "caption": {
                    "ro_RO": "Contractul stabilește serviciile și ciclul de facturare",
                    "en_US": "The agreement sets the services and the billing cycle",
                },
                "move": "div[name='cycle_id']",
                "hold": 2500,
            },
            {
                "goto": f"action={act_prep}&menu_id={self._menu('menu_service_agr')}",
                "wait": ".modal .o_form_view",
                "caption": {
                    "ro_RO": "La finalul perioadei se pregătesc consumurile",
                    "en_US": "At the end of the period the consumptions are prepared",
                },
                "hold": 2000,
            },
            {
                "click": ".modal div[name='service_period_id'] input",
                "wait_after": ".o-autocomplete--dropdown-menu",
            },
            {"click": ".o-autocomplete--dropdown-item:first-child", "hold": 800},
            {"click": ".modal-footer button.btn-primary", "wait_after": ".o_list_view", "hold": 2500},
            {
                "goto": f"action={act_bill}&menu_id={menu_bill}",
                "wait": ".modal .o_form_view",
                "caption": {
                    "ro_RO": "Apoi se verifică consumurile și se facturează",
                    "en_US": "Then the consumptions are checked and invoiced",
                },
                "hold": 2500,
            },
            {"click": ".modal-footer button.btn-primary", "wait_after": ".o_list_view", "hold": 3000},
            {
                "caption": {
                    "ro_RO": "Facturile pentru client sunt gata",
                    "en_US": "The customer invoices are ready",
                },
                "hold": 3000,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # RO -> static/description/demo.gif; fiecare limbă într-un test propriu, ca pregătirea
        # facturării să pornească de la o bază fără consumuri
        self.capture_gif(self._gif_steps(), lang="ro_RO")

    def test_capture_gif_en(self):
        # EN -> static/description/en/demo.gif
        self.capture_gif(self._gif_steps(), lang="en_US")
