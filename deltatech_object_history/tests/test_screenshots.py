# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant (RO) și pentru readme/USAGE.md (EN), plus GIF-ul demo.
# Fluxul: partenerul cu butonul „Istoric” -> adăugare rând de istoric din meniul Acțiuni ->
# rândurile partenerului -> un rând deschis -> istoricul unei facturi -> lista generală.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_object_history,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=/deltatech_object_history:TestObjectHistoryScreenshots --stop-after-init
import unittest

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# deschide „Adaugă istoric” din meniul Acțiuni al formularului (eticheta depinde de limbă)
OPEN_ADD_HISTORY = """
(() => {
    const items = [...document.querySelectorAll('.o-dropdown-item, .dropdown-item')];
    const item = items.find((el) => /Adaugă istoric|Add history/.test(el.textContent));
    if (item) { item.click(); }
})()
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestObjectHistoryScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_object_history"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.env = cls.env(su=True)
        cls.prepare_ro_company(name="Demo Distribuție SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id, "tz": "Europe/Bucharest"})
        # autorul rândurilor de istoric apare pe capturi: un nume potrivit pentru un manual
        admin.partner_id.name = "Andrei Popescu"
        env.flush_all()

        Partner = env["res.partner"]
        cls.partner = Partner.create(
            {
                "name": "Ferma Verde SRL",
                "is_company": True,
                "city": "Iași",
                "country_id": env.ref("base.ro").id,
                "email": "office@fermaverde.example",
                "phone": "+40 232 555 010",
                "website": "https://fermaverde.example",
            }
        )
        product = env["product.product"].create({"name": "Furaje concentrate (sac 40 kg)", "list_price": 180.0})
        # vânzare de mărfuri pe 707, cu TVA 21%
        income_707 = env["account.account"].search(
            [("code", "=", "707000"), ("company_ids", "in", company.id)], limit=1
        )
        vat = env["account.tax"].search(
            [
                ("type_tax_use", "=", "sale"),
                ("amount_type", "=", "percent"),
                ("company_id", "=", company.id),
                ("amount", "=", 21),
            ],
            limit=1,
        )
        product.write({"property_account_income_id": income_707.id, "taxes_id": [Command.set(vat.ids)]})
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [Command.create({"product_id": product.id, "quantity": 20, "price_unit": 180.0})],
            }
        )
        cls.invoice.action_post()

        # rândurile sunt scrise de un utilizator real, nu de OdooBot
        History = env["object.history"].with_user(admin)

        def history(record, name, description, partner=None):
            return History.create(
                {
                    "name": name,
                    "description": description,
                    "res_model": record._name,
                    "res_id": record.id,
                    "object_name": record.name,
                    "partner_id": (partner or cls.partner).id,
                }
            )

        history(
            cls.partner,
            "Condiții de livrare negociate",
            "<p>Livrare săptămânală, marțea, la depozitul din Iași. Plata la 30 de zile.</p>",
        )
        cls.history_partner = history(
            cls.partner,
            "Reclamație ambalaj deteriorat",
            "<p>Clientul a semnalat doi saci rupți la livrarea din 12 ale lunii. "
            "S-a convenit înlocuirea lor la următoarea livrare.</p>",
        )
        cls.history_invoice = history(
            cls.invoice,
            "Scadență amânată",
            "<p>Directorul financiar a aprobat amânarea scadenței cu 15 zile, la cererea clientului.</p>",
        )
        env.flush_all()

    def _ref(self, xmlid):
        return self.env.ref(xmlid).id

    def _shots(self):
        act_partner = self._ref("contacts.action_contacts")
        menu_contacts = self._ref("contacts.menu_contacts")
        act_history = self._ref("deltatech_object_history.action_object_history")
        menu_history = self._ref("deltatech_object_history.menu_object_history_line")
        partner_url = (
            f"id={self.partner.id}&action={act_partner}&menu_id={menu_contacts}&model=res.partner&view_type=form"
        )
        return [
            {
                "url": partner_url,
                "name": "01_partener_buton_istoric.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='open_history']"],
            },
            {
                "url": partner_url,
                "name": "02_adaugare_istoric.png",
                "wait": ".o_form_view",
                "click_btn": ".o_cp_action_menus button",
                "wait_after": ".o-dropdown--menu",
                "eval": OPEN_ADD_HISTORY,
                "eval_wait": 2500,
                "highlight": [
                    ".modal div[name='name']",
                    ".modal div[name='description']",
                    ".modal button[name='add_history']",
                ],
            },
            {
                "url": partner_url,
                "name": "03_istoric_partener.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='open_history']",
                "wait_after": ".o_list_view",
            },
            {
                "url": f"id={self.history_partner.id}&action={act_history}&menu_id={menu_history}"
                f"&model=object.history&view_type=form",
                "name": "04_rand_istoric.png",
                "wait": ".o_form_view",
                "highlight": [
                    "div[name='partner_id']",
                    "div[name='object_name']",
                    ".o_inner_group button[name='action_open_document']",
                ],
            },
            {
                "url": f"id={self.invoice.id}&action={self._ref('account.action_move_out_invoice_type')}"
                f"&menu_id={self._ref('account.menu_finance')}&model=account.move&view_type=form",
                "name": "05_factura_istoric.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='open_history']"],
            },
            {
                "url": f"action={act_history}&menu_id={menu_history}&model=object.history&view_type=list",
                "name": "06_lista_istoric.png",
                "wait": ".o_list_view",
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")

    # --- GIF demo -------------------------------------------------------------------------------

    def _gif_steps(self):
        act_partner = self._ref("contacts.action_contacts")
        menu_contacts = self._ref("contacts.menu_contacts")
        return [
            {
                "goto": f"id={self.partner.id}&action={act_partner}&menu_id={menu_contacts}"
                f"&model=res.partner&view_type=form",
            },
            {
                "caption": {
                    "ro_RO": "Butonul Istoric arată notițele păstrate pentru partener",
                    "en_US": "The History button shows the notes kept for the partner",
                },
                "move": "button[name='open_history']",
                "hold": 2200,
            },
            {"click": "button[name='open_history']", "wait_after": ".o_list_view", "hold": 2200},
            {
                "caption": {
                    "ro_RO": "Fiecare rând are titlu, partener asociat, documentul legat și descriere",
                    "en_US": "Each row has a title, a related partner, the linked document and a description",
                },
                "click": ".o_data_row:first-child td[name='name']",
                "wait_after": ".o_form_view",
                "hold": 2500,
            },
            {
                "caption": {
                    "ro_RO": "Deschide duce înapoi la înregistrarea de origine",
                    "en_US": "Open goes back to the original record",
                },
                "move": ".o_inner_group button[name='action_open_document']",
                "hold": 2500,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # EN -> static/description/en/demo.gif (limba paginii de Apps)
        # viewport mai lat decât cel implicit, ca lista de istoric să încapă mai bine
        self.capture_gif(self._gif_steps(), lang="en_US", viewport=(1500, 800))
