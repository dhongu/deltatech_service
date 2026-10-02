# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## AGREEMENT-001 — P1: Service billing converts prices into the user default company currency

- **Status:** Open.
- **Location:** wizard/service_billing.py, do_billing_step1(); models/service_consumption.py, _compute_revenues().
- **Trigger:** A user with default company A (RON) bills a EUR 100 consumption in company B (EUR), selecting B and its sales journal in the wizard.
- **Actual behavior:** Price conversion targets env.user.company_id rather than the wizard/consumption company. At 5 RON/EUR the line price becomes 500, while the invoice is created for company B and its EUR journal. Stored consumption revenues use the same default-company conversion rather than the consumption company.
- **Evidence:** Executed the existing do_billing_step1 method extracted from its AST: company B/EUR selected, default company A/RON, EUR 100 price; conversion targeted RON/company A and produced price 500. Inspected invoice creation and stored revenue computation.
- **Impact:** Customers can be billed the wrong monetary amount when the active company differs from the user default; revenue reporting can also mix company currencies.
- **Suggested fix:** Use the billing company and an explicit invoice currency consistently for conversion, account and tax lookup, and invoice creation. Convert revenues to consumption.company_id.currency_id and declare the corresponding dependencies.
- **Validation needed:** Two companies with different currencies, user default differing from active company, explicit foreign-currency journals, and stored revenue recomputation.

## AGREEMENT-002 — P2: Grouped service invoice lines sum quantities from different units

- **Status:** Open.
- **Location:** wizard/service_billing.py, add_invoice_line().
- **Trigger:** Group consumptions for the same product and numeric unit price, with agreement lines using different units, such as one Unit and one Dozen.
- **Actual behavior:** The merge key compares only product_id and price_unit. It adds quantities directly while keeping the first line product_uom_id and agreement_line_id, without comparing or converting units.
- **Evidence:** Executed the actual method with an existing one-Unit line and a new one-Dozen consumption at the same numeric price: it produced a single quantity-2 line using the Unit UoM. The physical quantity is 13 Units; alternatively the two correctly priced unit-specific lines must remain separate.
- **Impact:** Invoice quantities and agreement attribution become incorrect, which can distort downstream reporting and consumption reconciliation even where the numeric invoice subtotal coincidentally matches.
- **Suggested fix:** Keep lines separate when units or accounting/tax/agreement attributes differ, or normalize both quantities and unit prices before merging.
- **Validation needed:** Matching units, Unit/Dozen combinations with equal and different numeric prices, and grouping across agreement lines.

## AGREEMENT-003 — P2: Billing schedule edits do not invalidate the stored next invoice date

- **Status:** Open.
- **Location:** models/service_agreement.py, _compute_next_date_invoice().
- **Trigger:** After the next invoice date is computed, change the agreement billing cycle, invoice_day, or date_agreement without changing last_invoice_id.
- **Actual behavior:** The stored computation depends only on last_invoice_id while reading date_agreement, cycle_id.get_cycle(), invoice_day, and last_invoice_id.invoice_date. Schedule edits leave the stored date unchanged; editing the existing invoice date has the same dependency gap.
- **Evidence:** Source inspection of the stored fields, dependency declaration, inputs, and all module references to the compute method. No override explicitly recomputes these dates when schedule inputs change. No database reproduction was run.
- **Impact:** Automated billing runs on the previous schedule despite changes to the contract; the displayed next date is stale.
- **Suggested fix:** Declare all mutable schedule inputs, including cycle value/unit and linked invoice date, and consistently assign the computed dates for every branch.
- **Validation needed:** Changing a monthly cycle to weekly, changing invoice day, changing initial agreement date, and editing the existing invoice date.

## AGREEMENT-004 — P2: Automatic billing permanently skips overdue agreements

- **Status:** Open.
- **Location:** models/service_agreement.py, get_agreements_auto_billing() and make_billing_automation().
- **Trigger:** An open agreement with automatic billing is due on September 30, but the scheduler first succeeds on October 1 after downtime or a failed run.
- **Actual behavior:** Selection requires next_date_invoice to equal today. The September 30 agreement is removed on October 1 and every later day; no invoice is created to advance its next date.
- **Evidence:** Executed the existing selection method with two eligible agreements due yesterday and today: only the one due today remained.
- **Impact:** A missed daily execution can stop recurring billing for an agreement until manual intervention, causing missed revenue.
- **Suggested fix:** Select due and overdue agreements and define an idempotent catch-up policy for missed billing periods; preserve duplicate-consumption safeguards.
- **Validation needed:** Scheduler downtime over one and several periods, a failed run followed by retry, and agreements already prepared or billed for the target period.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `9ebc487`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **AGREEMENT-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **AGREEMENT-002 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **AGREEMENT-003 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **AGREEMENT-004 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
