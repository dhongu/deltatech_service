# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant (RO) și pentru readme/USAGE.md (EN), plus GIF-ul demo.
# Fluxul: tipurile de categorie -> categoria de produs cu tip și clasă -> lista echipamentelor cu
# coloanele Tip / Clasă categorie -> echipamentele grupate pe tipul categoriei.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_category_group_equipment,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=/deltatech_category_group_equipment:TestCategoryGroupEquipmentScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# afișează coloanele opționale Tip / Clasă categorie din lista echipamentelor
SHOW_OPTIONAL_COLUMNS = """
(async () => {
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    document.querySelector('.o_optional_columns_dropdown_toggle').click();
    await wait(500);
    const show = ['category_group_type', 'category_group_class'];
    // coloanele opționale goale în demo ar trunchia antetele modulului
    const hide = ['address_id', 'emplacement', 'agreement_id', 'last_reading', 'next_reading', 'installation_date',
                  'service_location_id', 'type_id', 'model_id', 'manufacturer_id', 'serial_id'];
    for (const name of [...show, ...hide]) {
        const input = document.querySelector(`.o-dropdown--menu input[name='${name}']`);
        if (input && input.checked !== show.includes(name)) { input.click(); await wait(300); }
    }
    document.querySelector('.o_list_view .o_list_table').click();
    await wait(400);
})()
"""

# grupează lista după „Tip categorie” din panoul de filtre (eticheta depinde de limbă)
GROUP_BY_TYPE = """
(async () => {
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    document.querySelector('.o_searchview_dropdown_toggler').click();
    await wait(600);
    const items = [...document.querySelectorAll('.o_group_by_menu .o-dropdown-item')];
    const item = items.find((el) => /^\\s*(Tip categorie|Category Type)\\s*$/.test(el.textContent));
    if (item) { item.click(); await wait(800); }
    document.querySelector('.o_searchview_dropdown_toggler').click();
    await wait(400);
    document.querySelectorAll('.o_group_header').forEach((h) => h.click());
    await wait(800);
})()
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestCategoryGroupEquipmentScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_category_group_equipment"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
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
        admin.group_ids = [
            Command.link(env.ref("deltatech_service_base.group_service_manager").id),
            Command.link(env.ref("deltatech_category_group.category_group_manager").id),
        ]
        env.flush_all()

        Type = env["category.group.type"]
        cls.type_mf = Type.create({"name": "Multifuncționale", "sequence": 1})
        cls.type_printer = Type.create({"name": "Imprimante", "sequence": 2})
        cls.type_scanner = Type.create({"name": "Scanere", "sequence": 3})
        Class = env["category.group.class"]
        cls.class_rent = Class.create({"name": "Închiriere", "sequence": 1})
        cls.class_sale = Class.create({"name": "Vânzare", "sequence": 2})

        Categ = env["product.category"]
        cls.categ_mf = Categ.create(
            {
                "name": "Multifuncționale A3 închiriate",
                "category_group_type": cls.type_mf.id,
                "category_group_class": cls.class_rent.id,
            }
        )
        categ_printer = Categ.create(
            {
                "name": "Imprimante laser vândute",
                "category_group_type": cls.type_printer.id,
                "category_group_class": cls.class_sale.id,
            }
        )
        Product = env["product.product"]
        mf = Product.create({"name": "Konica Minolta bizhub C300i", "type": "consu", "categ_id": cls.categ_mf.id})
        printer = Product.create({"name": "HP LaserJet M507dn", "type": "consu", "categ_id": categ_printer.id})

        Partner = env["res.partner"]
        ro = env.ref("base.ro").id
        tipografia = Partner.create(
            {"name": "Tipografia Nord SRL", "is_company": True, "city": "Suceava", "country_id": ro}
        )
        birouri = Partner.create({"name": "Birouri Centrale SA", "is_company": True, "city": "Iași", "country_id": ro})
        # mărfurile se țin pe 371, nu pe 301 (materii prime) implicit în planul RO
        stock_371 = env["account.account"].search([("code", "=", "371000"), ("company_ids", "in", company.id)], limit=1)
        if stock_371:
            (cls.categ_mf | categ_printer).write({"property_stock_valuation_account_id": stock_371.id})
        Equipment = env["service.equipment"]
        for name, serial, product, partner in (
            ("MF-0231", "XNJ01842", mf, tipografia),
            ("MF-0232", "XNJ01857", mf, tipografia),
            ("MF-0240", "XNJ02210", mf, birouri),
            ("PR-0115", "PHB4K2201", printer, birouri),
            ("PR-0116", "PHB4K2207", printer, birouri),
        ):
            Equipment.create({"name": name, "serial_no": serial, "product_id": product.id, "partner_id": partner.id})
        env.flush_all()

    def _ref(self, xmlid):
        return self.env.ref(xmlid).id

    def _equipment_list_url(self):
        act = self._ref("deltatech_service_equipment_base.action_service_equipment")
        menu = self._ref("deltatech_service_equipment_base.menu_service_equipment")
        return f"action={act}&menu_id={menu}&model=service.equipment&view_type=list"

    def _shots(self):
        act_type = self._ref("deltatech_category_group.action_category_type")
        menu_type = self._ref("deltatech_category_group.menu_category_type")
        act_categ = self._ref("product.product_category_action_form")
        menu_categ = self._ref("stock.menu_product_category_config_stock")
        return [
            {
                "url": f"action={act_type}&menu_id={menu_type}&model=category.group.type&view_type=list",
                "name": "01_tipuri_categorie.png",
                "wait": ".o_list_view",
            },
            {
                "url": f"id={self.categ_mf.id}&action={act_categ}&menu_id={menu_categ}&model=product.category&view_type=form",
                "name": "02_categorie_produs.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='category_group_type']", "div[name='category_group_class']"],
            },
            {
                "url": self._equipment_list_url(),
                "name": "03_echipamente_tip_clasa.png",
                "wait": ".o_list_view",
                "eval": SHOW_OPTIONAL_COLUMNS,
                "eval_wait": 1200,
                "highlight": ["th[data-name='category_group_type']", "th[data-name='category_group_class']"],
            },
            {
                "url": self._equipment_list_url(),
                "name": "04_echipamente_grupate_tip.png",
                "wait": ".o_list_view",
                "eval": GROUP_BY_TYPE,
                "eval_wait": 1500,
                "highlight": [".o_searchview_facet"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")

    # --- GIF demo -------------------------------------------------------------------------------

    def _gif_steps(self):
        act_categ = self._ref("product.product_category_action_form")
        return [
            {
                "goto": f"id={self.categ_mf.id}&action={act_categ}"
                f"&menu_id={self._ref('stock.menu_product_category_config_stock')}&model=product.category&view_type=form"
            },
            {
                "caption": {
                    "ro_RO": "Categoria de produs are un tip și o clasă",
                    "en_US": "The product category has a type and a class",
                },
                "move": "div[name='category_group_type']",
                "hold": 2500,
            },
            {
                "goto": self._equipment_list_url(),
                "wait": ".o_list_view",
                "caption": {
                    "ro_RO": "Echipamentele le preiau din produsul lor",
                    "en_US": "Equipment takes them from its product",
                },
                "eval": SHOW_OPTIONAL_COLUMNS,
                "hold": 2500,
            },
            {
                "caption": {
                    "ro_RO": "Lista se poate grupa pe tipul sau clasa categoriei",
                    "en_US": "The list can be grouped by category type or class",
                },
                "eval": GROUP_BY_TYPE,
                "hold": 3000,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # EN -> static/description/en/demo.gif (limba paginii de Apps)
        self.capture_gif(self._gif_steps(), lang="en_US", viewport=(1400, 760))
