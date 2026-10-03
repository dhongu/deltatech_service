# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Recompute stored revenues in the currency of the consumption company (AGREEMENT-001).

    They were converted to the currency of the default company of the user who triggered the computation.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    consumptions = env["service.consumption"].search([("invoiced_qty", "!=", 0)])
    env.add_to_compute(consumptions._fields["revenues"], consumptions)
    env.flush_all()
