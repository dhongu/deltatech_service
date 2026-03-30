# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Services Task",
    "summary": "Services Task Maintenance",
    "version": "19.0.0.0.15",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Maintenance",
    "depends": ["deltatech_service_equipment_base", "project", "hr"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "report/project_task_report.xml",
        "views/project_task_views.xml",
        "views/service_equipment_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
