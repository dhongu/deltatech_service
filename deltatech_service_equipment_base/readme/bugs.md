# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## METER-001 — P2: A reading can select a later same-day reading as its predecessor

- **Status:** Open.
- **Location:** models/service_meter.py, ServiceMeterReading._compute_previous_counter_value() and _compute_difference().
- **Trigger:** Store readings A=100 and B=120 for the same meter on the same date, with A created first, then recompute A previous value.
- **Actual behavior:** The predecessor query accepts date <= current date and excludes only the current ID, ordering by date desc/id desc. It can select B as A predecessor and produce -20. Successor updates only consider date > current date, so same-day chains are not consistently updated.
- **Evidence:** Executed the existing predecessor compute with a search returning the later same-day row, as allowed by its captured domain: A previous value became 120 and its difference -20. Inspected the successor query. This is not a database reading-chain test.
- **Impact:** Consumption for same-day reading sequences can be negative or inconsistent, affecting reports and billing based on differences.
- **Suggested fix:** Define a strict reading order using date and ID (or timestamps), query only earlier records, and update successors with the same ordering. Alternatively explicitly prohibit multiple readings per meter/date if that is the business rule.
- **Validation needed:** Two and three same-day readings, modifying an earlier reading, backdated insertion, deletion, and consumption totals across the date range.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `9ebc487`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **METER-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.

## METER-002 — P2: Collector totals crash when a child meter has no readings

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_meter.py, _compute_last_meter_reading().
- **Trigger:** Add a counter without readings to a collector meter.
- **Actual behavior:** The collector branch indexes child_meter.meter_reading_ids[0] without checking whether any reading exists.
- **Impact:** Creating or reading the collector fails instead of showing an initial total.
- **Evidence:** Executed the actual extracted compute with a collector containing an unread counter: IndexError: list index out of range. No database execution.
- **Suggested fix:** Handle unread counters explicitly, using the agreed initial-value policy.
- **Validation needed:** Collector with zero, one and several read/unread child meters.

## METER-003 — P2: Stored collector totals are not recomputed when child readings change

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_meter.py, _compute_last_meter_reading() dependencies.
- **Trigger:** Create, edit or delete a reading on a counter already linked to a collector.
- **Actual behavior:** The stored total depends on its own meter_reading_ids and the meter_ids relation, but no dependency reaches child readings or child totals. The collector total is read from child_meter.meter_reading_ids[0].
- **Impact:** Collector totals can remain stale while counter totals change, until its relation is edited or recomputation is forced.
- **Evidence:** Inspected the full service meter implementation and equipment update_meter_status extension; neither invalidates the collector when a child reading changes. Source evidence only.
- **Suggested fix:** Declare dependencies on the child values and reading order, and compute all outputs consistently.
- **Validation needed:** Separate transactions for child reading create/write/unlink and a collector relation left unchanged.

## METER-004 — P2: The reading wizard freezes its default date when the module is loaded

- **Status:** Open; reviewed 2026-10-02.
- **Location:** wizard/enter_readings.py, ServiceEnterReading.date.
- **Trigger:** Open a new reading wizard after the server has remained running across midnight.
- **Actual behavior:** The field declares default=fields.Date.today(), evaluating a date once during class definition rather than passing a callable.
- **Impact:** New readings default to the server startup/import date and can be saved under the wrong day.
- **Evidence:** Inspected the field default expression; it is an evaluated date, and default_get does not replace it. No long-running database test.
- **Suggested fix:** Use a callable contextual date default.
- **Validation needed:** Wizards created on different dates in the same server process and with user time zones.

## METER-005 — P2: Ordinary service users cannot read equipment models and operation definitions

- **Status:** Open; reviewed 2026-10-02.
- **Location:** security/ir.model.access.csv; equipment and configuration views.
- **Trigger:** A service user without the service manager group opens an equipment containing model or operation data.
- **Actual behavior:** The public equipment-model ACL points to model_service_equipment_type instead of model_service_equipment_model. Correct model access exists only for managers; parts, checks, measurements and their equipment lines likewise have manager-only ACLs despite appearing in the ordinary equipment form.
- **Impact:** Nonmanager service users cannot read the related equipment data needed by the form and maintenance workflow.
- **Evidence:** Read all ACL entries and views; searched service-suite access CSVs for additional grants. The model grant is misdirected, and operation models have no ordinary user read grant. No database-backed UI test.
- **Suggested fix:** Grant intended read permissions to service users on referenced models and lines, preserving appropriate parent/company isolation.
- **Validation needed:** Equipment form for a service user with model, parts, checks and measurements; a project task user with copied operations.
