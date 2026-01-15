# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Task Travel",
    "summary": "Project Task Travel Management",
    "version": "19.0.0.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Maintenance",
    "depends": ["deltatech_service_equipment_base", "project", "hr_timesheet"],
    "license": "OPL-1",
    "data": [
        "views/project_task_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "deltatech_project_task_travel/static/src/components/project_task_timer/project_task_timer.js",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
