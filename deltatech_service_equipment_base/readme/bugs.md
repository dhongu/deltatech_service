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
