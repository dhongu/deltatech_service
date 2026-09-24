# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Echipamente de service, contoare și citiri" — generate în
# timpul testelor, în limba RO, pe compania „Demo Service Imprimante SRL".
#
# Seed: firma întreține multifuncționale la clienți. Tipul „Multifuncțional A3 color" are
# șabloane de contoare, piese, verificări și măsurători. Clientul Tipografia Nord SRL are un
# loc funcțional (sediul din Suceava) cu două echipamente; primul are contor alb-negru, contor
# color și un contor colector „Total pagini", cu citiri lunare pe ultimele șase luni.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_service_equipment_base,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_service_equipment_base:TestServiceEquipmentScreenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestServiceEquipmentScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_service_equipment_base"

    @classmethod
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
        manager = env.ref("deltatech_service_base.group_service_manager")
        (admin | env.user).group_ids = [Command.link(manager.id)]
        env.flush_all()

        Partner = env["res.partner"]
        customer = Partner.create({"name": "Tipografia Nord SRL", "is_company": True, "city": "Suceava"})
        contact = Partner.create({"name": "Ana Moraru", "parent_id": customer.id, "type": "contact"})
        address = Partner.create(
            {"name": "Sediu Suceava", "parent_id": customer.id, "type": "delivery", "street": "Str. Mărășești 12"}
        )
        manufacturer = Partner.create({"name": "Konica Minolta", "is_company": True})
        technician = (
            env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Victor Ilie",
                    "login": "victor.ilie",
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                    "group_ids": [Command.set(env.ref("deltatech_service_base.group_service_user").ids)],
                }
            )
        )

        # unități distincte: un echipament nu poate avea două contoare cu aceeași unitate
        unit = env.ref("uom.product_uom_unit")
        Uom = env["uom.uom"]
        uom_bw = Uom.create({"name": "Pagini A/N", "relative_factor": 1.0, "relative_uom_id": unit.id})
        uom_color = Uom.create({"name": "Pagini color", "relative_factor": 1.0, "relative_uom_id": unit.id})
        uom_total = Uom.create({"name": "Pagini total", "relative_factor": 1.0, "relative_uom_id": unit.id})
        Categ = env["service.meter.category"]
        categ_bw = Categ.create({"name": "Copii alb-negru", "uom_id": uom_bw.id, "type": "counter"})
        categ_color = Categ.create({"name": "Copii color", "uom_id": uom_color.id, "type": "counter"})
        categ_total = Categ.create({"name": "Total pagini", "uom_id": uom_total.id, "type": "collector"})

        eq_categ = env["service.equipment.category"].create({"name": "Echipamente de imprimare"})
        parts = env["service.part"].create(
            [{"name": n} for n in ("Cartuș toner negru", "Unitate cilindru", "Role alimentare")]
        )
        checks = env["service.check"].create([{"name": n} for n in ("Curățare role", "Test pagină de probă")])
        temp_uom = Uom.create({"name": "°C", "relative_factor": 1.0, "relative_uom_id": unit.id})
        measurements = env["service.measurement"].create([{"name": "Temperatură cuptor", "uom_id": temp_uom.id}])
        service_bw = env["product.product"].create({"name": "Pagină alb-negru", "type": "service"})
        service_color = env["product.product"].create({"name": "Pagină color", "type": "service"})
        cls.eq_type = env["service.equipment.type"].create(
            {
                "name": "Multifuncțional A3 color",
                "category_id": eq_categ.id,
                "template_meter_ids": [
                    Command.create({"product_id": service_bw.id, "meter_categ_id": categ_bw.id}),
                    Command.create({"product_id": service_color.id, "meter_categ_id": categ_color.id}),
                ],
                "part_template_ids": [
                    Command.create({"part_id": p.id, "sequence": (i + 1) * 10}) for i, p in enumerate(parts)
                ],
                "check_template_ids": [
                    Command.create({"check_id": c.id, "sequence": (i + 1) * 10}) for i, c in enumerate(checks)
                ],
                "measurement_template_ids": [
                    Command.create({"measurement_id": m.id, "note": "Între 180 și 200 °C"}) for m in measurements
                ],
            }
        )
        model = env["service.equipment.model"].create({"name": "bizhub C300i"})

        cls.location = env["service.location"].create(
            {
                "name": "Sediu Suceava",
                "partner_id": customer.id,
                "contact_id": contact.id,
                "address_id": address.id,
                "technician_user_id": technician.id,
            }
        )

        def equipment(serial, inventory, localization):
            return env["service.equipment"].create(
                {
                    "partner_id": customer.id,
                    "contact_id": contact.id,
                    "service_location_id": cls.location.id,
                    "technician_user_id": technician.id,
                    "localization": localization,
                    "type_id": cls.eq_type.id,
                    "model_id": model.id,
                    "manufacturer_id": manufacturer.id,
                    "serial_no": serial,
                    "inventory_no": inventory,
                    "property_type": "rented",
                    "state": "active",
                    "part_ids": [
                        Command.create({"part_id": p.id, "sequence": (i + 1) * 10, "quantity": 1.0})
                        for i, p in enumerate(parts)
                    ],
                    "check_ids": [
                        Command.create({"check_id": c.id, "sequence": (i + 1) * 10, "is_ok": True})
                        for i, c in enumerate(checks)
                    ],
                    "measurement_ids": [
                        Command.create({"measurement_id": m.id, "value": 190.0, "note": "Între 180 și 200 °C"})
                        for m in measurements
                    ],
                }
            )

        cls.equipment = equipment("A7PU021004512", "INV-0231", "Etaj 1, birou DTP")
        cls.equipment_2 = equipment("A7PU021004733", "INV-0232", "Parter, recepție")
        cls.equipment_2.state = "in_repair"

        Meter = env["service.meter"]
        cls.meter_bw = Meter.create(
            {"equipment_id": cls.equipment.id, "meter_categ_id": categ_bw.id, "uom_id": uom_bw.id, "start_value": 12000}
        )
        cls.meter_color = Meter.create(
            {
                "equipment_id": cls.equipment.id,
                "meter_categ_id": categ_color.id,
                "uom_id": uom_color.id,
                "start_value": 4000,
            }
        )
        # citiri lunare, la sfârșitul fiecăreia din ultimele șase luni, în ordine cronologică
        month_end = fields.Date.today().replace(day=1) - relativedelta(days=1)
        dates = [month_end - relativedelta(months=5 - i, day=31) for i in range(6)]
        Reading = env["service.meter.reading"]
        values_bw = [14800, 17350, 20100, 22600, 25480, 28150]
        values_color = [4900, 5720, 6610, 7380, 8240, 9020]
        for day, bw, color in zip(dates, values_bw, values_color, strict=True):
            for meter, value in ((cls.meter_bw, bw), (cls.meter_color, color)):
                Reading.create(
                    {
                        "meter_id": meter.id,
                        "equipment_id": cls.equipment.id,
                        "date": day,
                        "counter_value": value,
                        "read_by": technician.partner_id.id,
                    }
                )
        env.flush_all()
        env.invalidate_all()
        # totalurile stocate se recalculează din citirile ordonate din bază
        meters = cls.meter_bw | cls.meter_color
        env.add_to_compute(Meter._fields["total_counter_value"], meters)
        env.add_to_compute(Meter._fields["last_reading_date"], meters)
        env.add_to_compute(Meter._fields["last_meter_reading_id"], meters)
        meters.flush_recordset()
        meters.calc_forecast_coef()
        cls.meter_total = Meter.create(
            {
                "equipment_id": cls.equipment.id,
                "meter_categ_id": categ_total.id,
                "uom_id": uom_total.id,
                "meter_ids": [Command.set(meters.ids)],
            }
        )
        env.flush_all()

        cls.act_equipment = env.ref("deltatech_service_equipment_base.action_service_equipment")
        cls.act_location = env.ref("deltatech_service_equipment_base.action_service_location")
        cls.act_meter = env.ref("deltatech_service_equipment_base.action_service_meter")
        cls.act_reading = env.ref("deltatech_service_equipment_base.action_service_meter_reading")
        cls.act_type = env.ref("deltatech_service_equipment_base.action_service_equipment_type")
        cls.act_categ = env.ref("deltatech_service_equipment_base.action_service_meter_category")

    def _form(self, action, record, name, **extra):
        shot = {
            "url": f"action={action.id}&id={record.id}&model={record._name}&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "settle": 2500,
        }
        shot.update(extra)
        return shot

    def test_capture_fise(self):
        self.env.flush_all()
        self.capture_screenshots(
            [
                {
                    "url": f"action={self.act_categ.id}&view_type=list",
                    "name": "01_categorii_contoare.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
                self._form(self.act_type, self.eq_type, "02_tip_echipament.png"),
                self._form(self.act_location, self.location, "03_loc_functional.png", click_tab="Echipamente"),
                {
                    "url": f"action={self.act_equipment.id}&view_type=list",
                    "name": "04_echipamente.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
                self._form(self.act_equipment, self.equipment, "05_echipament_contoare.png"),
                self._form(self.act_equipment, self.equipment, "06_echipament_piese.png", click_tab="Piese"),
                self._form(self.act_equipment, self.equipment, "07_echipament_verificari.png", click_tab="Verificări"),
                self._form(
                    self.act_meter,
                    self.meter_bw,
                    "08_contor_citiri.png",
                    highlight=["button[name='calc_forecast_coef']", "button[name='recheck_value']"],
                ),
                self._form(self.act_meter, self.meter_total, "09_contor_colector.png"),
                {
                    "url": f"action={self.act_reading.id}&view_type=list",
                    "name": "10_citiri_contoare.png",
                    "wait": ".o_list_view",
                    "settle": 2000,
                },
            ]
        )
