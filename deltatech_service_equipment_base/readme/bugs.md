# Identified bugs

Reviewed: 2026-10-01
Target version: Odoo 20.0
Scope: Static review and isolated method checks. Full database integration tests have not been run.

## [P2] Meter-reading wizard defaults to the server startup date

**Status:** Open — documented, not fixed.

**Location:** `wizard/enter_readings.py:12`. Line numbers refer to the reviewed source and may change.

### Cause

The field declaration calls fields.Date.today() immediately, passing a fixed date as the default rather than a callable.

### Impact

After a worker remains running past midnight, new reading wizards can keep the previous date, which affects consumption periods and validation against future readings.

### Reproduction

Load the model on one day, keep the worker running, then open a new meter-reading wizard the next day. Its default remains the date evaluated when the model was loaded.

### Recommended correction

Use a callable default such as fields.Date.context_today or fields.Date.today, without invoking it in the declaration.

### Validation

The field default expression was inspected. No overnight live-worker test was performed.

## [P2] A collector crashes when a child meter has no readings

**Status:** Open — documented, not fixed.

**Location:** `models/service_meter.py:123–140`. Line numbers refer to the reviewed source.

### Cause

The collector branch accesses child_meter.meter_reading_ids[0] without checking whether a child has any readings. A newly configured counter can validly have an empty reading history.

### Impact

Reading or recomputing the collector total raises IndexError, blocking configuration or display of a collector containing a new child.

### Reproduction

Create a counter with no readings and a collector that includes it. Recompute the collector total.

### Recommended correction

Define the contribution of a child without readings explicitly, for example its start value or zero according to the intended rule, and avoid indexing an empty recordset.

### Validation

Confirmed with real ORM meters and categories: computation raised IndexError. The failed operation ran in a savepoint; the audit transaction was rolled back.

## [P1] Collector totals are not recomputed when child readings change

**Status:** Open — documented, not fixed.

**Location:** `models/service_meter.py:123–140`. Line numbers refer to the reviewed source.

### Cause

The stored total compute depends on its own meter_reading_ids and meter_ids, but not on the reading histories or values of the linked child meters.

### Impact

A collector retains an outdated total after a child reading is edited, added or removed, affecting consumers of the stored aggregate and its fallback estimate.

### Reproduction

Create a child with latest value 10 and link it to a collector. Read total 10, change the child reading to 20, and read the collector again. It remains 10; manually recomputing produces 20.

### Recommended correction

Declare dependencies on child reading membership and relevant values/dates, or aggregate a correctly dependent child total. Define which date represents the aggregate.

### Validation

Confirmed with real ORM records: before 10, after child update 10, manual recompute 20. Audit records were rolled back.

## [P2] Removing the final reading leaves the old last-reading date

**Status:** Open — documented, not fixed.

**Location:** `models/service_meter.py:123–140`. Line numbers refer to the reviewed source.

### Cause

last_reading_date is assigned only when a counter has readings. The empty-history branch clears last_meter_reading_id and resets total, but never assigns a false date.

### Impact

A meter with no readings still appears to have been read on the former last date, misleading overdue-reading filters and screens.

### Reproduction

Create one reading dated 2026-03-01, read the meter last date, then delete the reading and recompute. last_meter_reading_id is empty but last_reading_date remains 2026-03-01.

### Recommended correction

Assign every computed field on every branch, clearing last_reading_date for an empty counter and defining an explicit date policy for collectors.

### Validation

Confirmed with real ORM records: zero remaining readings, empty last reading, retained date 2026-03-01 even after manual recomputation. Audit records were rolled back.

## [P1] Standalone base installation leaves reading differences stale after deletion

**Status:** Open — documented, not fixed.

**Location:** `models/service_meter.py:265–318`. Line numbers refer to the reviewed source.

### Cause

The base module propagates differences during computation and date writes but has no unlink hook to rebuild the chain after removing an intermediate reading. The optional deltatech_service_equipment addon provides a normal unlink repair, so this finding is restricted to installations using the base without that extension.

### Impact

Removing a reading in a standalone base installation loses part of the period consumption because the next reading retains its old predecessor and delta.

### Reproduction

With only the base installed, create readings 100,150,200 on three consecutive days. Delete the middle reading. The final difference stays 50 instead of becoming 100.

### Recommended correction

Make chain maintenance part of the base reading model on deletion; coordinate with the optional extension to avoid duplicate work and preserve its billed-reading restrictions.

### Validation

Confirmed with real ORM records and deltatech_service_equipment not installed: actual final difference 50, expected 100. Source review confirms that the optional extension repairs normal deletions, so full-suite normal deletion is not claimed to fail. Audit records were rolled back.

## Additional integration validation

On 2026-10-01 the existing equipment-base suite completed 12 tests with zero failures and zero errors in test20_bug_audit_20261001. Separate ORM reproductions confirmed the four meter findings above; all reproduction records were rolled back.
