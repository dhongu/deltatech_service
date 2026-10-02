# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models

# room usage -> building field with the total area of the rooms of that usage
SURFACE_BY_USAGE = {
    usage: f"surface_{usage}"
    for usage in [
        "office",
        "living",
        "bedroom",
        "meeting",
        "lobby",
        "staircase",
        "kitchen",
        "sanitary",
        "laboratory",
        "it_endowments",
        "garage",
        "warehouse",
        "log_warehouse",
        "archive",
        "cloakroom",
        "premises",
        "access",
    ]
}


class PropertyBuilding(models.Model):
    _name = "property.building"
    _description = "Building"
    _inherit = "property.property"

    land_id = fields.Many2one("property.land", string="Land")

    categ_id = fields.Many2one("property.building.categ", string="Category")
    room_ids = fields.One2many("property.room", "building_id", string="Rooms")
    features_ids = fields.One2many("property.features", "building_id", string="Features")

    # administrator_id = fields.Many2one('res.partner', string="Administrator", domain=[('is_company', '=', False)])

    purpose_parent_id = fields.Many2one(
        "property.building.purpose",
        string="Purpose building",
        domain=[("parent_id", "=", False)],
    )
    purpose_id = fields.Many2one(
        "property.building.purpose",
        string="Purpose building for",
        domain="[('parent_id','=',purpose_parent_id)]",
    )

    data_pif = fields.Date(string="Data PIF")

    parking_space = fields.Integer(string="Parking Space", help="Parking Space Available")
    occupants = fields.Integer(string="Occupants")
    occupied_date = fields.Date(string="Date Occupied")
    finished = fields.Boolean()

    roof_structure = fields.Selection(
        [
            ("tile", "wood roofing structure, tile roofing"),
            ("metal", "wood structure, sheet metal cover"),
            ("asbestos", "wood structure, roofing asbestos cement"),
            ("bituminous", "terrace structure, bituminous membrane cover"),
        ],
        string="Roof Structure",
    )

    surface_built = fields.Float(string="Surface built")  # Sc
    surface_unfolded = fields.Float(string="Surface unfolded")  # Sd
    surface_terraces = fields.Float(string="Surface terraces")  # Ster

    surface_flameproof = fields.Float(string="Flameproof surface")  # Sig

    surface_useful = fields.Float(
        string="Useful surface",
        help="∑ Sbir + Scc +  Slb + Sit + Sgar + Smag + Slog + Sarh + Sves + Steh ",
        # compute="_compute_all_surface",
        store=True,
    )  # Su

    surface_common = fields.Float(
        string="Common surface",
        help="The common area of the building ∑ Ssed + Shol + Scs + Sof + Sgrs + Sacc",
        # compute="_compute_all_surface",
        store=True,
    )  # Scc

    surface_office = fields.Float(string="Surface office", compute="_compute_surface_by_usage", store=True)  # Sbir
    surface_living = fields.Float(string="Surface living", compute="_compute_surface_by_usage", store=True)  #
    surface_bedroom = fields.Float(string="Surface bedroom", compute="_compute_surface_by_usage", store=True)  #

    surface_meeting = fields.Float(string="Surface meeting", compute="_compute_surface_by_usage", store=True)  # Ssed
    surface_lobby = fields.Float(string="Surface lobby", compute="_compute_surface_by_usage", store=True)  # Shol
    surface_staircase = fields.Float(string="Surface staircase", compute="_compute_surface_by_usage", store=True)  # Scs
    surface_kitchen = fields.Float(string="Surface kitchen", compute="_compute_surface_by_usage", store=True)  # Sof
    surface_sanitary = fields.Float(string="Surface sanitary", compute="_compute_surface_by_usage", store=True)  # Sgrs

    surface_laboratory = fields.Float(
        string="Surface laboratory", compute="_compute_surface_by_usage", store=True
    )  # Slb
    surface_it_endowments = fields.Float(
        string="Surface IT endowments", compute="_compute_surface_by_usage", store=True
    )  # Sit
    surface_garage = fields.Float(string="Surface garage", compute="_compute_surface_by_usage", store=True)  # Sgar
    surface_warehouse = fields.Float(
        string="Surface warehouse", compute="_compute_surface_by_usage", store=True
    )  # Smag
    surface_log_warehouse = fields.Float(
        string="Surface logistic warehouse", compute="_compute_surface_by_usage", store=True
    )  # Slog
    surface_archive = fields.Float(string="Surface archive", compute="_compute_surface_by_usage", store=True)  # Sarh
    surface_cloakroom = fields.Float(
        string="Surface cloakroom", compute="_compute_surface_by_usage", store=True
    )  # Sves
    surface_premises = fields.Float(string="Surface premises", compute="_compute_surface_by_usage", store=True)  # Steh
    surface_access = fields.Float(string="Surface access", compute="_compute_surface_by_usage", store=True)  # Sacc

    surface_cleaned_adm = fields.Float(string="Surface cleaned administratively")  # Sca
    surface_cleaned_ind = fields.Float(string="Surface cleaned industrial")  # Sci

    surface_cleaned_ext = fields.Float(string="External surface cleaned")  # Scext
    surface_cleaned_tot = fields.Float(
        string="Total surface cleaned", compute="_compute_surface_totals", store=True
    )  # Stc = Sca + Sci + Scext

    surface_derating_ext = fields.Float(string="Surface derating external")  # Sdze
    surface_derating_int = fields.Float(string="Surface derating internal")  # Sdzi
    surface_derating = fields.Float(
        string="Total surface derating", compute="_compute_surface_totals", store=True
    )  # Sdzt = ∑ Sdzi+Sdze

    surface_disinsection = fields.Float(
        string="Area of disinsection",
        compute="_compute_surface_disinsection",
        store=True,
    )  # Sds

    surface_cleaning_carpet = fields.Float(
        string="Surface cleaning Carpet", compute="_compute_cleaning_floor", store=True
    )  # Sctextil
    surface_cleaning_linoleum = fields.Float(
        string="Surface cleaning Linoleum",
        compute="_compute_cleaning_floor",
        store=True,
    )  # Scgresie
    surface_cleaning_wood = fields.Float(
        string="Surface cleaning Wood", compute="_compute_cleaning_floor", store=True
    )  # Scpodea

    surface_cleaning_doors = fields.Float(
        string="Surface cleaning doors", compute="_compute_cleaning_doors", store=True
    )  # Scusi
    surface_cleaning_windows = fields.Float(
        string="Surface cleaning window",
        compute="_compute_cleaning_windows",
        store=True,
    )  # Scgeam

    maintenance_team_type = fields.Selection([("internal", "Internal"), ("external", "external")])
    verification_date = fields.Date()
    verification_note = fields.Char()

    history_ids = fields.One2many("building.history", "building_id")
    market_rent_value = fields.Monetary()
    reevaluation_date = fields.Date()
    reevaluation_value = fields.Monetary()
    monthly_average_winter = fields.Monetary("Monthly utilities average - winter")
    monthly_average_summer = fields.Monetary("Monthly utilities average - summer")
    furniture_at_occupation = fields.Selection([("Full", "Full"), ("Semi", "Semi"), ("None", "None")])
    martket_similar_value = fields.Monetary("Market value for similar property")

    @api.onchange("purpose_parent_id")
    def onchange_purpose_parent_id(self):
        # Odoo 19: returning a dynamic domain from an onchange is ignored;
        # the restriction is already declared on the purpose_id field.
        if self.purpose_id.parent_id != self.purpose_parent_id:
            self.purpose_id = False

    @api.onchange("purpose_id")
    def onchange_purpose_id(self):
        self.purpose_parent_id = self.purpose_id.parent_id

    @api.depends("room_ids.usage", "room_ids.surface")
    def _compute_surface_by_usage(self):
        """Area of the rooms of each usage: ``surface_<usage>`` = ∑ surface of the rooms
        whose ``usage`` is ``<usage>``."""
        for building in self:
            surfaces = dict.fromkeys(SURFACE_BY_USAGE, 0.0)
            for room in building.room_ids:
                if room.usage in surfaces:
                    surfaces[room.usage] += room.surface
            for usage, field_name in SURFACE_BY_USAGE.items():
                building[field_name] = surfaces[usage]

    @api.depends(
        "surface_cleaned_adm",
        "surface_cleaned_ind",
        "surface_cleaned_ext",
        "surface_derating_int",
        "surface_derating_ext",
    )
    def _compute_surface_totals(self):
        for building in self:
            building.surface_cleaned_tot = (
                building.surface_cleaned_adm + building.surface_cleaned_ind + building.surface_cleaned_ext
            )
            building.surface_derating = building.surface_derating_int + building.surface_derating_ext

    @api.depends("room_ids.surface_cleaning_floor", "room_ids.floor_type")
    def _compute_cleaning_floor(self):
        surface_cleaning_carpet = 0.0
        surface_cleaning_linoleum = 0.0
        surface_cleaning_wood = 0.0

        for room in self.room_ids:
            if room.floor_type == "c":
                surface_cleaning_carpet += room.surface_cleaning_floor
            if room.floor_type == "l":
                surface_cleaning_linoleum += room.surface_cleaning_floor
            if room.floor_type == "w":
                surface_cleaning_wood += room.surface_cleaning_floor

        self.surface_cleaning_carpet = surface_cleaning_carpet
        self.surface_cleaning_linoleum = surface_cleaning_linoleum
        self.surface_cleaning_wood = surface_cleaning_wood

    @api.depends("room_ids.surface_cleaning_windows")
    def _compute_cleaning_windows(self):
        surface_cleaning_windows = 0.0
        for room in self.room_ids:
            surface_cleaning_windows += room.surface_cleaning_windows
        self.surface_cleaning_windows = surface_cleaning_windows

    @api.depends("room_ids.surface_cleaning_doors")
    def _compute_cleaning_doors(self):
        surface_cleaning_doors = 0.0
        for room in self.room_ids:
            surface_cleaning_doors += room.surface_cleaning_doors
        self.surface_cleaning_doors = surface_cleaning_doors

    @api.depends("room_ids.surface_disinsection")
    def _compute_surface_disinsection(self):
        surface_disinsection = 0.0
        for room in self.room_ids:
            surface_disinsection += room.surface_disinsection
        self.surface_disinsection = surface_disinsection


class PropertyFeatures(models.Model):
    _name = "property.features"
    _description = "Features"

    building_id = fields.Many2one("property.building", string="Building", required=True)
    categ = fields.Selection(
        [
            ("E", "Extinguishers"),
            ("H", "Hydrants"),
            ("M", "Medical kits"),
            ("A", "Air conditioning equipment"),
            ("D", "Deflector"),
            ("W", "Water dispensers"),
            ("L", "Lightning discharger"),
            ("G", "Grounding socket "),
            ("S", "Signage"),
        ],
        string="Features",
    )

    number = fields.Integer()
    observation = fields.Char()


class BuildingHistory(models.Model):
    _name = "building.history"
    _description = "Building History"

    building_id = fields.Many2one("property.building", string="Building", required=True, ondelete="cascade")
    tenant_id = fields.Many2one("res.partner", string="Tenant")
    from_date = fields.Date(string="From date")
    to_date = fields.Date(string="To date")
    note = fields.Char()
