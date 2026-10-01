# Identified bugs

Reviewed: 2026-10-01

Target version: Odoo 20.0

Scope: Source review and real ORM reproductions in a separate audit database; outbound HTTP was mocked.

## [P1] Adding distributed value discards the original quantity contribution

**Status:** Open — documented, not fixed.

**Location:** `wizard/service_distribution.py:74–84`. Line numbers refer to the reviewed source.

### Cause

In value mode with add_values enabled, the allocated value is added to cons.price_unit and quantity is reset to 1. The previous quantity times price_unit is not preserved.

### Impact

Adding a positive amount can reduce the consumption value to be billed instead of increasing it.

### Reproduction

Create one consumption with quantity 3 and price 10: total 30. Distribute amount 5 in value mode with add_values=True. The result is quantity 1, price 15, total 15 instead of 35.

### Recommended correction

Preserve the original line value when allocating an additional amount. If quantity is intentionally normalized to 1, use old quantity times old unit price plus the allocation; otherwise adjust unit price using the preserved quantity.

### Validation

Confirmed with real service.consumption and service.distribution records: actual total 15, expected 35. Audit records were rolled back.

## [P2] Appending a reference fails when the existing reference is empty

**Status:** Open — documented, not fixed.

**Location:** `wizard/service_distribution.py:79–84; models/service_consumption.py:13`. Line numbers refer to the reviewed source.

### Cause

Consumption name is an optional Char and can be False. When the wizard reference is nonempty, the code evaluates cons.name + self.reference without normalizing the missing value.

### Impact

Value distribution fails with an uncaught TypeError for an otherwise valid consumption, preventing the operation.

### Reproduction

Leave the consumption reference empty, enter Extra in the distribution wizard reference, and apply value distribution with add_values enabled.

### Recommended correction

Normalize the existing reference to an empty string before concatenating and define a separator policy for nonempty references.

### Validation

Confirmed with real ORM records: the method raised TypeError, unsupported operand types bool and str. Audit records were rolled back.

## Existing test suite

The selected IAP server, line-counter and service-agreement suites ran together on 2026-10-01 in test20_bug_audit_20261001: 35 tests completed with zero failures and zero errors. The additional reproductions above demonstrate cases outside those assertions. All reproduction records were rolled back.
