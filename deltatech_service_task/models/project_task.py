# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    service_location_id = fields.Many2one("service.location", string="Functional Location")
    service_equipment_id = fields.Many2one(
        "service.equipment",
        string="Service Equipment",
        domain="[('service_location_id', '=', service_location_id)]",
    )
    equipment_type_summary = fields.Text(
        string="Equipment Type Summary",
        compute="_compute_equipment_type_summary",
    )
    part_ids = fields.One2many("project.task.part", "task_id", string="Parts", copy=True)
    check_ids = fields.One2many("project.task.check", "task_id", string="Checks", copy=True)
    measurement_ids = fields.One2many("project.task.measurement", "task_id", string="Measurements", copy=True)
    employee_ids = fields.Many2many("hr.employee", string="Team", sudo=True)
    # Filtreaza operatiunile preluate de pe echipament: se copiaza doar cele marcate cu acest tip si
    # cele nemarcate. Fara tip, se copiaza toate, ca pana acum.
    maintenance_type_id = fields.Many2one("service.maintenance.type", string="Maintenance Type")

    @api.depends("service_equipment_id.type_id", "child_ids.service_equipment_id.type_id")
    def _compute_equipment_type_summary(self):
        for task in self:
            type_counts = {}
            for t in task | task.child_ids:
                type_id = t.service_equipment_id.type_id
                if type_id:
                    type_counts[type_id.name] = type_counts.get(type_id.name, 0) + 1
            task.equipment_type_summary = "\n".join(f"{count} x {name}" for name, count in sorted(type_counts.items()))

    @api.onchange("user_ids")
    def _onchange_user_ids(self):
        self.sudo()._sync_employees_from_users()

    def _sync_employees_from_users(self):
        for record in self:
            # sudo for data access
            record_sudo = record.sudo()
            if not record_sudo.user_ids:
                employees_to_remove = record_sudo.employee_ids.filtered(lambda e: e.user_id)
                if employees_to_remove:
                    record_sudo.employee_ids -= employees_to_remove
                continue

            selected_users_employees = (
                self.env["hr.employee"].sudo().search([("user_id", "in", record_sudo.user_ids.ids)])
            )
            current_employees = record_sudo.employee_ids
            employees_to_add = selected_users_employees - current_employees
            employees_to_remove = current_employees.filtered(
                lambda e: e.user_id and e.user_id not in record_sudo.user_ids
            )

            if employees_to_add or employees_to_remove:
                record_sudo.employee_ids = (current_employees + employees_to_add) - employees_to_remove

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Subsarcina pe echipament face parte din aceeasi interventie ca lucrarea-parinte
            parent_id = vals.get("parent_id") or self.env.context.get("default_parent_id")
            if parent_id and "maintenance_type_id" not in vals:
                vals["maintenance_type_id"] = self.browse(parent_id).maintenance_type_id.id
        records = super().create(vals_list)
        for record in records:
            if "user_ids" in record._fields:
                record.sudo()._sync_employees_from_users()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "user_ids" in vals:
            self.sudo()._sync_employees_from_users()
        return res

    @api.onchange("service_location_id")
    def _onchange_service_location_id(self):
        if self.service_location_id and self.service_location_id.partner_id:
            self.partner_id = self.service_location_id.partner_id

    @api.onchange("maintenance_type_id")
    def _onchange_maintenance_type_id(self):
        """Refiltreaza operatiunile cand se schimba tipul de mentenanta pe o sarcina cu echipament.

        Doar cat timp nu s-a lucrat pe ele: o linie bifata (OK / N/A) sau o masuratoare completata ar
        fi pierdute la refacerea listei.
        """
        if not self.service_equipment_id:
            return
        lucrat = (
            any(line.is_ok or line.is_not_applicable for line in self.part_ids)
            or any(line.is_ok or line.is_not_applicable for line in self.check_ids)
            or any(line.is_not_applicable or line.value for line in self.measurement_ids)
        )
        if not lucrat:
            self._onchange_service_equipment_id()

    @api.onchange("service_equipment_id")
    def _onchange_service_equipment_id(self):
        self = self.sudo()
        if self.service_equipment_id:
            if self.service_equipment_id.service_location_id:
                self.service_location_id = self.service_equipment_id.service_location_id
            if self.service_equipment_id.partner_id:
                self.partner_id = self.service_equipment_id.partner_id

            def pentru_tipul_sarcinii(lines):
                return lines.filtered(lambda line: line._is_for_maintenance_type(self.maintenance_type_id))

            part_list = []
            for equipment_part in pentru_tipul_sarcinii(self.service_equipment_id.part_ids):
                part_list.append(
                    (
                        0,
                        0,
                        {
                            "part_id": equipment_part.part_id.id,
                            "quantity": equipment_part.quantity,
                            "sequence": equipment_part.sequence,
                            "note": equipment_part.note,
                        },
                    )
                )
            # Lista se inlocuieste, nu se completeaza: pe o sarcina salvata, operatiunile vechi (alt
            # echipament sau alt tip de mentenanta) se adunau peste cele noi
            self.part_ids = [(5, 0, 0)] + part_list

            check_list = []
            for equipment_check in pentru_tipul_sarcinii(self.service_equipment_id.check_ids):
                check_list.append(
                    (
                        0,
                        0,
                        {
                            "check_id": equipment_check.check_id.id,
                            "sequence": equipment_check.sequence,
                            "note": equipment_check.note,
                        },
                    )
                )
            self.check_ids = [(5, 0, 0)] + check_list

            measurement_list = []
            for equipment_measurement in pentru_tipul_sarcinii(self.service_equipment_id.measurement_ids):
                measurement_list.append(
                    (
                        0,
                        0,
                        {
                            "measurement_id": equipment_measurement.measurement_id.id,
                            "sequence": equipment_measurement.sequence,
                            "note": equipment_measurement.note,
                        },
                    )
                )
            self.measurement_ids = [(5, 0, 0)] + measurement_list


class ProjectTaskPart(models.Model):
    _name = "project.task.part"
    _description = "Project Task Part"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", related="task_id.service_equipment_id", store=True)
    part_id = fields.Many2one("service.part", string="Part", required=True)
    quantity = fields.Float(string="Quantity", default=1.0)
    note = fields.Text(string="Note")
    is_ok = fields.Boolean(string="Is OK")
    is_not_applicable = fields.Boolean(
        string="Not Applicable",
        help="The operation does not apply to this equipment or configuration. It is excluded "
        "from the follow-up flow: no deviation is reported for it, regardless of the note.",
    )


class ProjectTaskCheck(models.Model):
    _name = "project.task.check"
    _description = "Project Task Check"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", related="task_id.service_equipment_id", store=True)
    check_id = fields.Many2one("service.check", string="Check", required=True)
    note = fields.Text(string="Note")
    is_ok = fields.Boolean(string="Is OK")
    is_not_applicable = fields.Boolean(
        string="Not Applicable",
        help="The check does not apply to this equipment or configuration. It is excluded "
        "from the follow-up flow: no deviation is reported for it, regardless of the note.",
    )


class ProjectTaskMeasurement(models.Model):
    _name = "project.task.measurement"
    _description = "Project Task Measurement"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", related="task_id.service_equipment_id", store=True)
    measurement_id = fields.Many2one("service.measurement", string="Measurement", required=True)
    value = fields.Float(string="Value")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", related="measurement_id.uom_id", readonly=True)
    note = fields.Text(string="Note")
    # Masuratorile nu au conformitate (is_ok), doar valoare si nota. Bifa exista si aici pentru
    # masuratorile care nu au putut fi efectuate: fara ea, singurul mod de a le semnala ar fi o nota,
    # iar nota trimite observatia mai departe ca abatere.
    is_not_applicable = fields.Boolean(
        string="Not Applicable",
        help="The measurement could not be taken or does not apply to this equipment. It is "
        "excluded from the follow-up flow: no deviation is reported for it, regardless of the note.",
    )
    date_measurement = fields.Datetime(related="task_id.create_date", store=True, string="Data Măsurătorii")
