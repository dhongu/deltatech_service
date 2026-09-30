# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ServiceMaintenanceType(models.Model):
    """Tipul de mentenanta al unei interventii: de exemplu primavara, toamna, intermediara.

    Separat de tipul de interventie (corectiva / preventiva), care decide forma raportului: tipurile de
    mentenanta produc acelasi proces verbal si difera doar prin operatiunile care se executa. Lista e
    gestionata de utilizator si se poate extinde oricand.
    """

    _name = "service.maintenance.type"
    _description = "Maintenance Type"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer()


MAINTENANCE_TYPES_HELP = (
    "Maintenance types in which this operation is performed. Leave empty if it is performed in all of them."
)


class MaintenanceTypesMixin(models.AbstractModel):
    """Marcajul operatiunii pe tipuri de mentenanta: pe sablonul tipului de echipament si pe liniile
    echipamentului. Nemarcat = valabil la toate tipurile, deci un tip nou nu cere remarcarea
    nomenclatorului."""

    _name = "service.maintenance.types.mixin"
    _description = "Maintenance Types Applicability"

    maintenance_type_ids = fields.Many2many(
        "service.maintenance.type", string="Maintenance Types", help=MAINTENANCE_TYPES_HELP
    )

    def _is_for_maintenance_type(self, maintenance_type):
        """Operatiunea se executa la tipul de mentenanta dat (fara tip pe sarcina = toate)."""
        self.ensure_one()
        return not maintenance_type or not self.maintenance_type_ids or maintenance_type in self.maintenance_type_ids


class ServicePartTemplate(models.Model):
    _name = "service.part.template"
    _inherit = ["service.part.template", "service.maintenance.types.mixin"]

    maintenance_type_ids = fields.Many2many(relation="service_part_template_maint_type_rel")


class ServiceCheckTemplate(models.Model):
    _name = "service.check.template"
    _inherit = ["service.check.template", "service.maintenance.types.mixin"]

    maintenance_type_ids = fields.Many2many(relation="service_check_template_maint_type_rel")


class ServiceMeasurementTemplate(models.Model):
    _name = "service.measurement.template"
    _inherit = ["service.measurement.template", "service.maintenance.types.mixin"]

    maintenance_type_ids = fields.Many2many(relation="service_measurement_template_maint_type_rel")


class ServiceEquipmentPart(models.Model):
    _name = "service.equipment.part"
    _inherit = ["service.equipment.part", "service.maintenance.types.mixin"]

    maintenance_type_ids = fields.Many2many(relation="service_equipment_part_maint_type_rel")


class ServiceEquipmentCheck(models.Model):
    _name = "service.equipment.check"
    _inherit = ["service.equipment.check", "service.maintenance.types.mixin"]

    maintenance_type_ids = fields.Many2many(relation="service_equipment_check_maint_type_rel")


class ServiceEquipmentMeasurement(models.Model):
    _name = "service.equipment.measurement"
    _inherit = ["service.equipment.measurement", "service.maintenance.types.mixin"]

    maintenance_type_ids = fields.Many2many(relation="service_equipment_measurement_maint_type_rel")
