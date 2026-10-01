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
