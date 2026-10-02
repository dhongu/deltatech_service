# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PROPERTY-001 — P1: Building area fields reference an absent compute method

- **Status:** Fixed in 19.0.1.0.3 — the 17 area-by-usage fields (`surface_office` ... `surface_access`) are computed by `_compute_surface_by_usage()` per building from `room_ids.usage` and `room_ids.surface`; `surface_cleaned_tot` (= administrative + industrial + external) and `surface_derating` (= internal + external) by `_compute_surface_totals()`. `surface_cleaned_adm`, `surface_cleaned_ind` and `surface_derating_int` had no documented formula and are now editable inputs. In the database the fields did not raise: they silently stayed at 0. Covered by tests in `tests/test_surface.py` (usage sums and usage change, every usage field, totals, two buildings in one batch).
- **Location:** models/property_building.py, fields using compute=_compute_all_surface.
- **Trigger:** Create or recompute building area fields such as surface_office, surface_cleaned_tot, or surface_derating.
- **Actual behavior:** Many stored fields reference _compute_all_surface, but that method is absent from the model and its declared dependency sources. Reaching that computation fails instead of assigning the areas.
- **Evidence:** Inspected all loaded property model files and searched definitions across local custom addons, Enterprise and core; no _compute_all_surface definition was found. No database installation/recomputation was run.
- **Impact:** Creating or recomputing affected building records can fail and the area breakdown cannot be calculated.
- **Suggested fix:** Implement the advertised area computation with explicit room/building dependencies, or remove/replace obsolete compute references according to the intended area model.
- **Validation needed:** Fresh installation and building creation, each room usage, industrial/administrative cleaning inputs, external surfaces, and complete assignment of every computed field.

## PROPERTY-002 — P2: Batch area computations assign the combined total to every building

- **Status:** Open.
- **Location:** models/property_building.py, _compute_cleaning_floor(), _compute_cleaning_windows(), _compute_cleaning_doors(), _compute_surface_disinsection().
- **Trigger:** Recompute two buildings together, with carpet cleaning areas of 5 and 7 respectively.
- **Actual behavior:** Methods iterate self.room_ids, which is the union of all buildings rooms, then assign the combined value to self. Odoo recordset field assignment broadcasts that value to each building.
- **Evidence:** Executed the existing floor computation against minimal records modeling recordset union and broadcast assignment: both buildings received 12 instead of 5 and 7. The other three methods have the same structure.
- **Impact:** Batch recomputation corrupts per-building surface totals and estimates based on them.
- **Suggested fix:** Iterate over each building and sum only its rooms; assign all outputs separately for each building.
- **Validation needed:** Two and three buildings in the same compute batch, empty buildings, and each floor/window/door/disinsection aggregation.

## PROPERTY-003 — P2: Cleaning-area validation is not registered as an ORM constraint

- **Status:** Open.
- **Location:** models/property_room.py, _check_cleaning_surface().
- **Trigger:** Create or edit a room whose floor cleaning area exceeds its total surface.
- **Actual behavior:** The bare @api.constrains is used without field arguments or decorator-call parentheses. It replaces the method with a decorator closure that has no _constrains metadata, so the ORM does not register it. The original body also reads cleaning_surface, a field not declared on property.room, rather than surface_cleaning_floor, and assumes a singleton.
- **Evidence:** Executed the local Odoo constrains/attrsetter implementations against the actual extracted method: the resulting class attribute had no _constrains metadata. Inspected room field declarations.
- **Impact:** The intended validation is silently absent; simply fixing the decorator would expose the invalid field reference.
- **Suggested fix:** Declare the actual validated field names, use the appropriate cleaning-area field, and iterate over records in the constraint.
- **Validation needed:** Valid/invalid floor area on create and write, batch updates, and confirmation of the desired policy for other cleaning areas.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run during the review. PROPERTY-001 was fixed on 2026-10-02 with database-backed tests.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `9ebc487`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **PROPERTY-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **PROPERTY-002 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **PROPERTY-003 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.

## PROPERTY-004 — P1: Property access rights grant public and portal users unrestricted CRUD

- **Status:** Open; reviewed 2026-10-02.
- **Location:** `security/ir.model.access.csv`; manifest security data.
- **Trigger:** A public or portal user accesses property rooms, building history, features or configuration records through ORM-backed endpoints; an internal user accesses another company's property data.
- **Actual behavior:** Eleven ACL entries have an empty group, granting read, write, create and unlink to every user. No property record rules limit company or parent access. Rooms, features and building history are independent models, so maintenance equipment permissions do not protect their records.
- **Impact:** Unauthorized disclosure and alteration of tenant history, room data and property configuration. Availability of an external write endpoint depends on the installed controllers; unrestricted model permissions themselves are present.
- **Evidence:** Full module source/security inspection. The manifest loads no record rules and the affected independent models contain no parent-access checks.
- **Suggested fix:** Restrict ACLs to designated internal property users and managers; enforce company and parent access for independent child models.
- **Validation needed:** Database-backed public, portal and cross-company read/write/delete checks, including direct ORM access and available controller paths. No such tests were executed in this pass.

## PROPERTY-005 — P2: Numeric nomenclature lookup discards the caller's domain

- **Status:** Open; reviewed 2026-10-02.
- **Location:** `models/property_config.py`, `PropertyNomenclature.name_search()`.
- **Trigger:** Search a numeric purpose code in a field restricted to the selected parent purpose.
- **Actual behavior:** The numeric branch searches only `cod`, ignoring the supplied domain and forcing `limit=1`. A purpose belonging to a different parent can be returned as a selectable suggestion.
- **Impact:** Numeric selection violates the field's configured restriction; selecting that purpose can change the building's parent purpose through its onchange.
- **Evidence:** Executed the actual extracted method with a search spy: input domain `[('parent_id', '=', 42)]`, name `1` and limit 20 produced search domain `[('cod', 'ilike', '01')]` and limit 1. The building purpose field supplies the omitted parent restriction.
- **Suggested fix:** Combine the caller's domain with the code criterion and honor its limit; retain access-aware ORM search.
- **Validation needed:** Identical numeric codes under two parents, restricted dropdown selection and nonnumeric searches. Isolated execution only; no database tests.
