Obsolete compatibility module, hidden on Odoo Apps. It has no code, data or views of its own: installing it only installs *Services Agreement* (`deltatech_service_agreement`), which in turn brings *Services Base* (`deltatech_service_base`).

It is kept so that existing databases and projects that still list `deltatech_service` in their dependencies keep working after an upgrade. New projects should depend on `deltatech_service_agreement` directly.
