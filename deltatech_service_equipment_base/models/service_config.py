# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ServiceMeterCategory(models.Model):
    _name = "service.meter.category"
    _description = "Service Meter Category"

    name = fields.Char(string="Category")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", required=True)
    type = fields.Selection(
        [("counter", "Counter"), ("collector", "Collector")],
        string="Type",
        default="counter",
    )


class ServiceEquipmentCategory(models.Model):
    _name = "service.equipment.category"
    _description = "Service Equipment category"

    name = fields.Char(string="Category", translate=True)


class ServiceEquipmentType(models.Model):
    _name = "service.equipment.type"
    _description = "Service Equipment Type"

    name = fields.Char(string="Type", translate=True)
    template_meter_ids = fields.One2many("service.template.meter", "type_id", string="Meters")
    category_id = fields.Many2one("service.equipment.category", string="Category")
    part_template_ids = fields.One2many("service.part.template", "equipment_type_id", string="Parts")
    check_template_ids = fields.One2many("service.check.template", "equipment_type_id", string="Checks")
    measurement_template_ids = fields.One2many(
        "service.measurement.template", "equipment_type_id", string="Measurements"
    )


class ServicePart(models.Model):
    _name = "service.part"
    _description = "Service Part"

    name = fields.Char(string="Part Name", required=True)


class ServicePartTemplate(models.Model):
    _name = "service.part.template"
    _description = "Service Part Template"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Part Name", related="part_id.name", readonly=True)
    part_id = fields.Many2one("service.part", string="Part")
    equipment_type_id = fields.Many2one("service.equipment.type", required=False, string="Type")
    note = fields.Text(string="Note")


class ServiceCheck(models.Model):
    _name = "service.check"
    _description = "Service Check"

    name = fields.Char(string="Check Name", required=True)


class ServiceCheckTemplate(models.Model):
    _name = "service.check.template"
    _description = "Service Check Template"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    check_id = fields.Many2one("service.check", string="Check")
    equipment_type_id = fields.Many2one("service.equipment.type", required=False, string="Type")
    note = fields.Text(string="Note")


class ServiceMeasurement(models.Model):
    _name = "service.measurement"
    _description = "Service Measurement"

    name = fields.Char(string="Measurement Name", required=True)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")


class ServiceMeasurementTemplate(models.Model):
    _name = "service.measurement.template"
    _description = "Service Measurement Template"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    measurement_id = fields.Many2one("service.measurement", string="Measurement")
    equipment_type_id = fields.Many2one("service.equipment.type", required=False, string="Type")
    note = fields.Text(string="Note")


class ServiceEquipmentModel(models.Model):
    _name = "service.equipment.model"
    _description = "Service Equipment Model"

    name = fields.Char(string="Model", translate=True)


class ServiceTemplateMeter(models.Model):
    _name = "service.template.meter"
    _description = "Service Template Meter"

    type_id = fields.Many2one("service.equipment.type", string="Type")
    product_id = fields.Many2one(
        "product.product",
        string="Service",
        ondelete="set null",
        domain=[("type", "=", "service")],
    )
    meter_categ_id = fields.Many2one("service.meter.category", string="Meter category")

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
