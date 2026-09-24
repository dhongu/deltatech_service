# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Echipamente în contract: instalare, citiri și facturare pe
# consum" — generate în timpul testelor, în limba RO, pe compania „Demo Service Imprimante SRL".
#
# Seed: multifuncționalul MF-0231 e instalat la Tipografia Nord SRL (sediul din Suceava) la începutul
# lunii de acum două luni, cu indexul 12.000, și adăugat într-un contract de închiriere cu plată pe
# pagină (0,05 lei / pagină). Citirile de la sfârșitul ultimelor două luni sunt 14.850 și 17.600.
# Pregătirea facturării pe luna trecută adună toate citirile nefacturate (5.600 pagini), iar
# facturarea produce factura în ciornă. Al doilea multifuncțional, MF-0232, e încă disponibil în
# depozit și servește la capturile de instalare.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_service_equipment,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_service_equipment:TestServiceEquipmentFlowScreenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Apasă în antetul formularului butonul al cărui text se potrivește.
JS_CLICK_HEADER = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    [...document.querySelectorAll('.o_form_statusbar button, .o_statusbar_buttons button')]
        .find((b) => %(match)s.test(b.textContent)).click();
    await sleep(3000);
}
"""

# Bifează toate rândurile listei și apasă butonul din antetul ei.
JS_LIST_HEADER = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    document.querySelector('thead .o_list_record_selector input').click();
    await sleep(1200);
    [...document.querySelectorAll('.o_control_panel button, .o_list_buttons button')]
        .find((b) => %(match)s.test(b.textContent)).click();
    await sleep(3000);
}
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestServiceEquipmentFlowScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_service_equipment"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Service Imprimante SRL")
        env = cls.env
        company = cls.company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        (admin | env.user).tz = "Europe/Bucharest"
        for xmlid in ("deltatech_service_base.group_service_manager", "account.group_account_invoice"):
            group = env.ref(xmlid)
            (admin | env.user).group_ids = [Command.link(group.id)]
        env.flush_all()
        env["product.template"].sudo().search([]).active = False

        ron = env.ref("base.RON")
        today = fields.Date.today()
        cls.install_date = today.replace(day=1) - relativedelta(months=2)
        month_1_end = cls.install_date + relativedelta(months=1, days=-1)
        month_2_end = cls.install_date + relativedelta(months=2, days=-1)

        Partner = env["res.partner"]
        cls.customer = Partner.create(
            {"name": "Tipografia Nord SRL", "is_company": True, "city": "Suceava", "vat": "RO18547290"}
        )
        cls.address = Partner.create(
            {"name": "Sediu Suceava", "parent_id": cls.customer.id, "type": "delivery", "street": "Str. Mărășești 12"}
        )
        reader = Partner.create({"name": "Victor Ilie"})

        unit = env.ref("uom.product_uom_unit")
        uom_page = env["uom.uom"].create({"name": "Pagini", "relative_factor": 1.0, "relative_uom_id": unit.id})
        cls.meter_categ = env["service.meter.category"].create(
            {"name": "Copii A4 alb-negru", "uom_id": uom_page.id, "bill_uom_id": uom_page.id, "type": "counter"}
        )
        cls.service = env["product.product"].create(
            {
                "name": "Pagină A4 alb-negru",
                "type": "service",
                "uom_id": uom_page.id,
                "list_price": 0.05,
                "taxes_id": [Command.set(cls.company_data["default_tax_sale"].ids)],
                # închirierea cu plată pe pagină e prestare de servicii: 704
                "property_account_income_id": env["account.account"]
                .search([("code", "=like", "704%"), ("company_ids", "in", company.ids)], limit=1)
                .id,
            }
        )
        cls.eq_categ = env["service.equipment.category"].create(
            {
                "name": "Multifuncționale",
                "template_meter_ids": [
                    Command.create(
                        {"product_id": cls.service.id, "meter_categ_id": cls.meter_categ.id, "currency_id": ron.id}
                    )
                ],
            }
        )
        cls.eq_type = env["service.equipment.type"].create(
            {"name": "Multifuncțional A4 mono", "category_id": cls.eq_categ.id}
        )
        cls.agreement_type = env["service.agreement.type"].create(
            {
                "name": "Service cu plată pe pagină",
                "journal_id": cls.company_data["default_journal_sale"].id,
                "readings_required": True,
            }
        )
        manufacturer = Partner.create({"name": "Canon", "is_company": True})
        model = env["service.equipment.model"].create({"name": "imageRUNNER 1643i"})
        salesman = (
            env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Elena Marin",
                    "login": "elena.marin",
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                }
            )
        )

        # secvența echipamentelor e a companiei principale: aici numele se dau explicit
        def equipment(name, serial):
            return env["service.equipment"].create(
                {
                    "name": name,
                    "type_id": cls.eq_type.id,
                    "model_id": model.id,
                    "manufacturer_id": manufacturer.id,
                    "serial_no": serial,
                }
            )

        cls.equipment = equipment("MF-0231", "XNJ01842")
        cls.equipment_2 = equipment("MF-0232", "XNJ01857")
        cls.equipment.create_meters_button()
        cls.meter = cls.equipment.meter_ids
        # indexul de la punerea în funcțiune: fără el, prima factură ar lua tot indexul
        cls.meter.start_value = 12000

        # operațiile scriu istoricul și etichetele în limba utilizatorului
        env = cls.env = env(context=dict(env.context, lang="ro_RO"))
        Operation = env["service.equi.operation"]
        ctx = {"active_id": cls.equipment.id, "active_ids": cls.equipment.ids}
        install = Operation.with_context(default_state="ins", **ctx).create(
            {
                "partner_id": cls.customer.id,
                "address_id": cls.address.id,
                "emplacement": "Etaj 1, birou DTP",
                "date": cls.install_date,
                "read_by": reader.id,
            }
        )
        install.items.write({"counter_value": 12000})
        install.do_operation()
        # contractul se creează întâi (Contracte → Nou), apoi echipamentul se adaugă în el
        cls.agreement = env["service.agreement"].create(
            {
                "partner_id": cls.customer.id,
                "cycle_id": env.ref("deltatech_service_agreement.cycle_monthly").id,
                "date_agreement": cls.install_date,
                "type_id": cls.agreement_type.id,
                "billing_automation": "manual",
                "user_id": salesman.id,
            }
        )
        add = Operation.with_context(default_state="add", **ctx).create(
            {
                "partner_id": cls.customer.id,
                "address_id": cls.address.id,
                "agreement_id": cls.agreement.id,
                "date": cls.install_date,
                "read_by": reader.id,
            }
        )
        # asistentul propune 0: se introduce indexul curent
        add.items.write({"counter_value": 12000})
        add.do_operation()
        # instalarea și adăugarea scriu data de azi; o aducem la data reală, după ambele operații
        cls.equipment.installation_date = cls.install_date
        cls.agreement.agreement_line.write({"price_unit": 0.05, "currency_id": ron.id})

        Reading = env["service.meter.reading"]
        for day, value in ((month_1_end, 14850), (month_2_end, 17600)):
            Reading.create(
                {
                    "meter_id": cls.meter.id,
                    "equipment_id": cls.equipment.id,
                    "date": day,
                    "counter_value": value,
                    "read_by": reader.id,
                }
            )
        cls.equipment.update_meter_status()
        cls.agreement.contract_open()
        cls.agreement.meter_reading_status = True

        cls.period = env["service.date.range"].create(
            {
                "name": month_2_end.strftime("%m/%Y"),
                "date_start": month_2_end.replace(day=1),
                "date_end": month_2_end,
            }
        )
        env.flush_all()

        cls.act_equipment = env.ref("deltatech_service_equipment_base.action_service_equipment")
        cls.act_categ = env.ref("deltatech_service_equipment_base.action_service_equipment_category")
        cls.act_meter_categ = env.ref("deltatech_service_equipment_base.action_service_meter_category")
        cls.act_agreement = env.ref("deltatech_service_agreement.action_service_agreement")
        cls.act_agreement_type = env.ref("deltatech_service_agreement.action_service_agreement_type")
        cls.act_consumption = env.ref("deltatech_service_agreement.action_service_consumption")
        cls.act_history = env.ref("deltatech_service_equipment.service_history_action")

    def _form(self, action, record, name, **extra):
        shot = {
            "url": f"action={action.id}&id={record.id}&model={record._name}&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "settle": 2500,
        }
        shot.update(extra)
        return shot

    def _capture(self, shots):
        self.env.flush_all()
        self.capture_screenshots(shots)
        self.env.invalidate_all()

    def test_capture_fise(self):
        self._capture(
            [
                self._form(self.act_categ, self.eq_categ, "01_categorie_sabloane_contoare.png"),
                self._form(self.act_meter_categ, self.meter_categ, "02_categorie_contor.png"),
                self._form(self.act_agreement_type, self.agreement_type, "03_tip_contract.png"),
                self._form(
                    self.act_equipment,
                    self.equipment_2,
                    "04_echipament_disponibil.png",
                    highlight=[".o_statusbar_buttons"],
                ),
            ]
        )
        # contoarele echipamentului disponibil, ca asistentul de instalare să ceară indexul
        self.equipment_2.create_meters_button()
        self._capture(
            [
                self._form(
                    self.act_equipment,
                    self.equipment_2,
                    "05_instalare.png",
                    eval=JS_CLICK_HEADER % {"match": "/^\\s*(Instalare|Install)\\s*$/"},
                    eval_wait=1500,
                ),
                self._form(self.act_equipment, self.equipment, "06_echipament_instalat.png"),
                self._form(self.act_agreement, self.agreement, "07_contract.png"),
                {
                    "url": f"action={self.act_agreement.id}&view_type=list",
                    "name": "08_pregatire_facturare.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                    "eval": JS_LIST_HEADER % {"match": "/Pregătire facturare|Billing Preparation/"},
                    "eval_wait": 1500,
                },
            ]
        )

        # pregătirea facturării pe luna trecută: consumul vine din citirile nefacturate
        preparation = (
            self.env["service.billing.preparation"]
            .with_context(active_ids=self.agreement.ids)
            .create({"service_period_id": self.period.id})
        )
        preparation.do_billing_preparation()
        consumptions = self.env["service.consumption"].search([("agreement_id", "=", self.agreement.id)])
        # factura se datează la data ultimei citiri incluse (sfârșitul perioadei)
        self.env["service.change.invoice.date"].with_context(active_ids=consumptions.ids).create(
            {"date_invoice": self.period.date_end}
        ).do_change()
        self._capture(
            [
                {
                    "url": f"action={self.act_consumption.id}&view_type=list",
                    "name": "09_consumuri.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
            ]
        )

        billing = (
            self.env["service.billing"]
            .with_context(active_ids=consumptions.ids)
            .create({"journal_id": self.company_data["default_journal_sale"].id})
        )
        billing.do_billing()
        invoice = consumptions.invoice_id[:1]
        self._capture(
            [
                self._form(
                    self.env.ref("account.action_move_out_invoice_type"),
                    invoice,
                    "10_factura.png",
                    highlight=["button[name='generate_excel_meters_report']"],
                ),
                {
                    "url": f"action={self.act_history.id}&view_type=list",
                    "name": "11_istoric.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
            ]
        )
