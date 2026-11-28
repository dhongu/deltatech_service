# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant (RO) și pentru readme/USAGE.md (EN), plus GIF-ul demo.
# Fluxul: contractul de service cu butonul de istoric -> rândurile contractului -> echipamentul
# cu butonul de istoric -> un rând al echipamentului -> filtrele Contracte / Echipamente.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_object_history_service,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=/deltatech_object_history_service:TestObjectHistoryServiceScreenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestObjectHistoryServiceScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_object_history_service"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.env = cls.env(su=True)
        cls.prepare_ro_company(name="Demo Service Imprimante SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id, "tz": "Europe/Bucharest"})
        admin.partner_id.name = "Andrei Popescu"
        manager = env.ref("deltatech_service_base.group_service_manager")
        admin.group_ids = [Command.link(manager.id)]
        env.flush_all()

        cls.partner = env["res.partner"].create(
            {"name": "Tipografia Nord SRL", "is_company": True, "city": "Suceava", "country_id": env.ref("base.ro").id}
        )
        journal = env["account.journal"].search([("type", "=", "sale"), ("company_id", "=", company.id)], limit=1)
        agreement_type = env["service.agreement.type"].create(
            {"name": "Închiriere echipamente", "journal_id": journal.id}
        )
        service = env["product.product"].create({"name": "Pagină alb-negru", "type": "service", "list_price": 0.05})
        cls.agreement = env["service.agreement"].create(
            {
                "name": "AG/00007",
                "partner_id": cls.partner.id,
                "user_id": admin.id,
                "company_id": company.id,
                "currency_id": company.currency_id.id,
                "type_id": agreement_type.id,
                "cycle_id": env.ref("deltatech_service_agreement.cycle_monthly").id,
                "description": "Închiriere multifuncționale, facturare la pagină",
                "date_agreement": fields.Date.today() - relativedelta(months=3),
                "agreement_line": [
                    Command.create(
                        {
                            "product_id": service.id,
                            "quantity": 1,
                            "price_unit": 0.05,
                            "uom_id": service.uom_id.id,
                            "currency_id": company.currency_id.id,
                        }
                    )
                ],
            }
        )
        cls.agreement.contract_open()
        cls.equipment = env["service.equipment"].create({"name": "MF-0231", "serial_no": "XNJ01842"})

        History = env["object.history"].with_user(admin)

        def history(record, name, description):
            return History.create(
                {
                    "name": name,
                    "description": description,
                    "res_model": record._name,
                    "res_id": record.id,
                    "object_name": record.name,
                    "partner_id": cls.partner.id,
                }
            )

        history(
            cls.agreement,
            "Prelungire contract discutată",
            "<p>Clientul dorește prelungirea cu 12 luni și un al doilea multifuncțional din martie.</p>",
        )
        history(
            cls.agreement,
            "Preț pagină renegociat",
            "<p>De la 1 ale lunii viitoare, pagina alb-negru scade la 0,045 lei. Se emite act adițional.</p>",
        )
        cls.history_equipment = history(
            cls.equipment,
            "Blocaj hârtie repetat",
            "<p>Al treilea blocaj în tava 2 luna aceasta. Tehnicianul recomandă înlocuirea rolelor de alimentare.</p>",
        )
        env.flush_all()

    def _ref(self, xmlid):
        return self.env.ref(xmlid).id

    def _agreement_url(self):
        act = self._ref("deltatech_service_agreement.action_service_agreement")
        menu = self._ref("deltatech_service_agreement.menu_service_agreement")
        return f"id={self.agreement.id}&action={act}&menu_id={menu}&model=service.agreement&view_type=form"

    def _equipment_url(self):
        act = self._ref("deltatech_service_equipment_base.action_service_equipment")
        menu = self._ref("deltatech_service_equipment_base.menu_service_equipment")
        return f"id={self.equipment.id}&action={act}&menu_id={menu}&model=service.equipment&view_type=form"

    def _shots(self):
        act_history = self._ref("deltatech_object_history.action_object_history")
        menu_history = self._ref("deltatech_object_history.menu_object_history_line")
        return [
            {
                "url": self._agreement_url(),
                "name": "01_contract_buton_istoric.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='open_history']"],
            },
            {
                "url": self._agreement_url(),
                "name": "02_istoric_contract.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='open_history']",
                "wait_after": ".o_list_view",
            },
            {
                "url": self._equipment_url(),
                "name": "03_echipament_buton_istoric.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='open_history']"],
            },
            {
                "url": f"id={self.history_equipment.id}&action={act_history}&menu_id={menu_history}"
                f"&model=object.history&view_type=form",
                "name": "04_rand_istoric_echipament.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='res_model']", "div[name='object_name']"],
            },
            {
                "url": f"action={act_history}&menu_id={menu_history}&model=object.history&view_type=list",
                "name": "05_filtre_contracte_echipamente.png",
                "wait": ".o_list_view",
                "click_btn": ".o_searchview_dropdown_toggler",
                "wait_after": ".o_filter_menu",
                "highlight": [
                    ".o_filter_menu .o-dropdown-item:has-text('Contracte'), "
                    ".o_filter_menu .o-dropdown-item:has-text('Agreements')",
                    ".o_filter_menu .o-dropdown-item:has-text('Echipamente'), "
                    ".o_filter_menu .o-dropdown-item:has-text('Equipments')",
                ],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")

    # --- GIF demo -------------------------------------------------------------------------------

    def _gif_steps(self):
        return [
            {"goto": self._agreement_url()},
            {
                "caption": {
                    "ro_RO": "Contractul de service are propriul istoric de notițe",
                    "en_US": "The service agreement has its own history of notes",
                },
                "move": "button[name='open_history']",
                "hold": 2200,
            },
            {"click": "button[name='open_history']", "wait_after": ".o_list_view", "hold": 2500},
            {"goto": self._equipment_url()},
            {
                "caption": {
                    "ro_RO": "La fel și echipamentul",
                    "en_US": "So does the equipment",
                },
                "move": "button[name='open_history']",
                "hold": 2200,
            },
            {"click": "button[name='open_history']", "wait_after": ".o_list_view", "hold": 2500},
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # EN -> static/description/en/demo.gif (limba paginii de Apps)
        # viewport lat: la 1120 px butoanele contractului trec în „Mai mult” și butonul de istoric se ascunde
        self.capture_gif(self._gif_steps(), lang="en_US", viewport=(1600, 820))
