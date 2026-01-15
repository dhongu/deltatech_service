# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools import float_utils
from math import radians, cos, sin, asin, sqrt


class ProjectTask(models.Model):
    _inherit = "project.task"

    travel_start_latitude = fields.Float(string="Travel Start Latitude", digits=(10, 7))
    travel_start_longitude = fields.Float(string="Travel Start Longitude", digits=(10, 7))
    travel_stop_latitude = fields.Float(string="Travel Stop Latitude", digits=(10, 7))
    travel_stop_longitude = fields.Float(string="Travel Stop Longitude", digits=(10, 7))

    is_traveling = fields.Boolean(string="Is Traveling")
    travel_timer_start = fields.Datetime(string="Travel Timer Start")
    travel_distance = fields.Float(string="Travel Distance (km)", digits=(16, 2))
    travel_time = fields.Float(string="Travel Time (hours)")

    def action_timer_start(self):
        if self.is_traveling:
            # We use the stop coordinates saved by JS if available
            coords = {
                "lat": self.travel_stop_latitude,
                "lng": self.travel_stop_longitude
            }
            # If GPS didn't provide coords, action_travel_stop will use the functional location
            self.action_travel_stop(coords=coords)
        return super().action_timer_start()

    def action_travel_start(self, coords=None):
        if self.timer_start:
            # Note: action_timer_stop might return an action (wizard)
            # We don't handle the wizard here, but it will stop the timer if it can.
            self.action_timer_stop()
        self.ensure_one()
        if coords is None:
            coords = {}
        lat = coords.get("lat", 0.0)
        lng = coords.get("lng", 0.0)

        # Fallback to company headquarters coordinates if GPS not available
        if not lat or not lng:
            company_partner = self.env.company.partner_id
            if company_partner.partner_latitude or company_partner.partner_longitude:
                lat = company_partner.partner_latitude
                lng = company_partner.partner_longitude

        self.write({
            "is_traveling": True,
            "travel_timer_start": fields.Datetime.now(),
            "travel_start_latitude": lat,
            "travel_start_longitude": lng,
            "travel_stop_latitude": 0.0,
            "travel_stop_longitude": 0.0,
        })
        # Check distance to service location
        dest_lat = self.service_location_id.address_id.partner_latitude
        dest_lng = self.service_location_id.address_id.partner_longitude

        distance_msg = ""
        if dest_lat and dest_lng:
            distance = self._calculate_distance_google(lat, lng, dest_lat, dest_lng)
            if not distance:
                distance = self._calculate_distance(lat, lng, dest_lat, dest_lng)
            distance_msg = f" Distance to destination: {distance:.2f} km."

        self.message_post(
            body=f"Travel started manually.{distance_msg} Coordinates: {lat}, {lng}"
        )

    def action_travel_stop(self, coords=None):
        self.ensure_one()
        if coords is None:
            coords = {}
        lat = coords.get("lat", 0.0)
        lng = coords.get("lng", 0.0)

        # Fallback to service location address coordinates if GPS not available
        if not lat or not lng:
            dest_lat = self.service_location_id.address_id.partner_latitude
            dest_lng = self.service_location_id.address_id.partner_longitude
            if dest_lat or dest_lng:
                lat = dest_lat
                lng = dest_lng

        start_lat = self.travel_start_latitude
        start_lng = self.travel_start_longitude

        distance = self._calculate_distance_google(start_lat, start_lng, lat, lng)
        if not distance:
            distance = self._calculate_distance(start_lat, start_lng, lat, lng)

        duration = 0.0
        if self.travel_timer_start:
            diff = fields.Datetime.now() - self.travel_timer_start
            duration = diff.total_seconds() / 3600.0

        self.write({
            "travel_stop_latitude": lat,
            "travel_stop_longitude": lng,
            "travel_distance": distance,
            "travel_time": duration,
            "is_traveling": False,
        })
        self._sync_travel_to_sale_order()
        self.message_post(
            body=f"Travel ended manually. Distance traveled: {distance:.2f} km. Duration: {duration:.2f} hours. Stop coordinates: {lat}, {lng}"
        )

    def _calculate_distance_google(self, lat1, lon1, lat2, lon2):
        try:
            import googlemaps

            api_key = self.env["ir.config_parameter"].sudo().get_param("google_api_key", False)
            if api_key:
                client = googlemaps.Client(api_key)
                start_coords = (lat1, lon1)
                end_coords = (lat2, lon2)
                matrix = client.distance_matrix([start_coords], [end_coords])
                if matrix["rows"][0]["elements"][0]["status"] == "OK":
                    distance_km = matrix["rows"][0]["elements"][0]["distance"]["value"] / 1000.00
                    return distance_km
        except Exception as e:
            from logging import getLogger

            _logger = getLogger(__name__)
            _logger.error("Error in computing distance via Google Maps: %s", e)
        return False

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        # Haversine formula
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    def _sync_travel_to_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            return

        if self.sale_order_id.state not in ["draft", "sent"]:
            return

        get_param = self.env["ir.config_parameter"].sudo().get_param
        dist_prod_id = int(get_param("deltatech_project_task_travel.travel_distance_product_id", 0))
        time_prod_id = int(get_param("deltatech_project_task_travel.travel_time_product_id", 0))

        if dist_prod_id and self.travel_distance > 0:
            self._upsert_sale_order_line(dist_prod_id, self.travel_distance)

        if time_prod_id and self.travel_time > 0:
            self._upsert_sale_order_line(time_prod_id, self.travel_time)

    def action_sync_travel(self):
        self._sync_travel_to_sale_order()

    def _upsert_sale_order_line(self, product_id, quantity):
        self.ensure_one()
        # Find if there is an existing line for this product linked to this task
        sale_line = self.sale_order_id.order_line.filtered(lambda l: l.product_id.id == product_id and l.task_id == self)
        if sale_line:
            sale_line.product_uom_qty = quantity
        else:
            self.env["sale.order.line"].create(
                {
                    "order_id": self.sale_order_id.id,
                    "product_id": product_id,
                    "product_uom_qty": quantity,
                    "task_id": self.id,
                }
            )

