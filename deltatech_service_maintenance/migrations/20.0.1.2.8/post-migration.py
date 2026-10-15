# © 2026 Terrabit
import uuid


def migrate(cr, version):
    # Up to 20.0.1.2.7 the token default was computed once per server start, so
    # many service orders share the same portal token: give each its own.
    cr.execute("SELECT id FROM service_order")
    for (order_id,) in cr.fetchall():
        cr.execute("UPDATE service_order SET access_token = %s WHERE id = %s", (str(uuid.uuid4()), order_id))
