# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Services Base",
    "summary": "Manage Services Base",
    "version": "20.0.2.0.6",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Agreement",
    "depends": ["product", "account"],
    "license": "OPL-1",
    "data": [
        "security/service_security.xml",
        "data/data.xml",
        "views/service_cycle_view.xml",
        "views/service_date_range_view.xml",
        "security/ir.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "application": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
