# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## AGREEMENT-001 — P1: Service billing converts prices into the user default company currency

- **Status:** Fixed in 19.0.2.0.13 — `do_billing_step1()` converts into the invoice currency (journal currency, otherwise billing company currency) with the billing company rates; the invoice currency is set explicitly; income account and taxes are taken for the billing company; consumptions of another company are rejected; `_compute_revenues()` converts into the consumption company currency (post-migration recomputes stored revenues). Covered by tests in `tests/test_agreement_multicompany.py` (other company in EUR, EUR journal in a USD company, cross-company rejection).
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

## AGREEMENT-005 — P1: Automatic billing cannot pass the preparation wizard contract

- **Status:** Open; reviewed 2026-10-02.
- **Location:** models/service_agreement.py, make_billing_automation(); wizard/service_billing_preparation.py.
- **Trigger:** Run the billing cron for an eligible agreement without consumption in the current period.
- **Actual behavior:** The cron finds service_period but creates the preparation wizard with no service_period_id, a required field with no default. Even if a user default supplies the period, the next step reads res["consumption_ids"], while preparation returns only an action dictionary without that key.
- **Impact:** Automatic billing fails before invoice creation; finding the period does not pass it into the wizard.
- **Evidence:** Inspected the complete preparation and automation implementations and their equipment extension. No period default is provided by the code, and the returned dictionary has no consumption_ids entry. No database cron execution.
- **Suggested fix:** Pass an explicit unique period and company, obtain the created consumptions through a defined method result, and provide the billing journal explicitly.
- **Validation needed:** Cron with ordinary defaults and a user-provided period default, missing/duplicate periods and generated consumptions.

## AGREEMENT-006 — P1: Contract lines bypass the parent agreement company rules

- **Status:** Fixed in 19.0.2.0.13 — global multi-company record rule on `service.agreement.line` (`security/service_security.xml`); `create()` and `write()` with `agreement_id` require write access on the target agreement. Covered by tests in `tests/test_agreement_multicompany.py` (search, read, write, create and reassignment across companies).
- **Location:** security/service_security.xml; security/ir.model.access.csv; models/service_agreement.py.
- **Trigger:** An internal user directly reads contract lines belonging to an unauthorized company, or a service user modifies such a line.
- **Actual behavior:** All internal users have line read access and service users have line write access. Company rules cover service.agreement and service.consumption, but not the independent service.agreement.line model. It contains no parent-access enforcement.
- **Impact:** Contract product, quantity and pricing information can be exposed, and writable line values changed across company boundaries.
- **Evidence:** Read the full line model and security data; the stored company_id does not have an accompanying record rule. Parent record rules do not transfer through a Many2one. No database access tests.
- **Suggested fix:** Apply company isolation and parent agreement permissions to line read/write/create/reassignment.
- **Validation needed:** Direct searches and writes on lines of another company with the parent agreement inaccessible.

## AGREEMENT-007 — P2: Adding a distributed amount discards the existing quantity multiplier

- **Status:** Open; reviewed 2026-10-02.
- **Location:** wizard/service_distribution.py, do_distribution().
- **Trigger:** Distribute an amount of 12 with Add to existing enabled onto a consumption with quantity 3 and unit price 10.
- **Actual behavior:** The value branch adds 12 to the old unit price and then sets quantity to 1. It preserves 10 instead of the existing amount 30.
- **Impact:** The resulting consumption amount becomes 22 instead of 42, reducing the amount billed and misrepresenting an additive distribution.
- **Evidence:** Executed the actual extracted method with a write spy: quantity 3, price 10 and added amount 12 became quantity 1, price 22. No database execution.
- **Suggested fix:** Preserve the existing total quantity * price_unit before adding the distributed amount, or retain quantities with an explicitly defined allocation policy.
- **Validation needed:** Quantity 0, 1 and 3, several consumptions, negative adjustments and replacing rather than adding an amount.

## AGREEMENT-008 — P1: Previously opened billing wizards can invoice the same consumption twice

- **Status:** Open; reviewed 2026-10-03.
- **Location:** wizard/service_billing.py, default_get(), do_billing_step1(), do_billing().
- **Trigger:** Open two billing wizards for the same draft consumption, apply the first, then apply the second. A repeated RPC invocation on the original wizard follows the same path.
- **Actual behavior:** Draft-state selection happens only in default_get. Billing neither rejects nor skips consumptions that already have invoice_id or state done. It prepares the lines again, creates another invoice, and replaces the consumption invoice reference, leaving the first invoice in place.
- **Impact:** The same service can be charged twice, while the consumption reference exposes only the most recently created invoice.
- **Evidence:** Executed the actual do_billing_step1 method extracted from its AST with a synthetic consumption. After the first call set state done, assigned invoice_id=99 and called the method again: it prepared quantity 3 twice. Inspected the complete invoice creation path, consumption model and account-move hooks; no reuse guard exists. Invoice creation itself was not executed against a database.
- **Suggested fix:** Revalidate the selected consumptions at execution time and enforce an atomic claim or lock so concurrent billing attempts cannot both pass. Keep invoice references intact on rejection.
- **Validation needed:** Two pre-opened wizards applied sequentially, repeated calls and simultaneous transactions; assert one invoice and one stable consumption reference.

## AGREEMENT-009 — P1: Negative service corrections are silently clipped and billed quantities disagree

- **Status:** Open; reviewed 2026-10-03.
- **Location:** wizard/service_billing.py, add_invoice_line(), do_billing_step1(), do_billing(), especially the negative-line loop.
- **Trigger:** Bill a negative consumption correcting a previous period with no positive quantity of that product in the new invoice. Alternatively use several negative lines or a negative consumption with a free quantity allowance.
- **Actual behavior:** Each negative line is capped against the sum of positive quantities in the current invoice. A lone quantity -2 becomes zero. With grouping disabled, quantities 3, -5, -5 become 3, -3, -3 because the same allowance is reused for each negative line. The consumption is still marked done, and invoiced_qty is recorded before clipping. For quantity -2 and free allowance 1, the initial invoice line is -2 but invoiced_qty is -3, even before clipping.
- **Impact:** A correction for an earlier invoice can disappear entirely while remaining recorded as billed. Invoice quantities and stored invoiced quantities diverge, distorting revenue reporting and reconciliation. The clipping also fails to enforce its apparent aggregate limit when several corrections share a product.
- **Evidence:** Executed the unmodified negative-line loop extracted from the actual do_billing AST: [-2] became [0], and [3, -5, -5] became [3, -3, -3]. Executed the actual do_billing_step1 method with quantity -2 and free allowance 1: invoiced_qty became -3. Checked add_invoice_line's explicit negative-quantity branch and the revenue computation. No account.move database execution.
- **Suggested fix:** Define correction/refund behavior explicitly and preserve the intended adjustment amount. If net-negative invoices are unsupported, raise a clear error or create the appropriate credit note. Calculate invoiced_qty from the final allocated invoice quantities, without subtracting free allowances from negative corrections.
- **Validation needed:** Negative-only corrections, mixed positive/negative lines, multiple negative lines with grouping enabled and disabled, differing prices and units, free allowances and consistency with stored revenues.

## AGREEMENT-010 — P2: Price change wizard converts prices with the user default company

- **Status:** Open. Found on 2026-10-03 while fixing AGREEMENT-001.
- **Location:** `wizard/service_price_change.py`, `_default_currency()`, `onchange_scanned_ean()`, `do_price_change()`.
- **Trigger:** A multi-company user whose default company (`env.user.company_id`) differs from the active company or from the company of the selected consumptions, with different company currencies (e.g. default company in RON, consumptions/product in EUR), runs Change price.
- **Actual behavior:** The default wizard currency, the conversion of the product `list_price` in the onchange and the conversion back to `list_price` in `do_price_change()` all use `env.user.company_id` and its currency/rates, not the active company, the consumption company or the product company. This is the same class of error as AGREEMENT-001.
- **Evidence:** source inspection of `wizard/service_price_change.py` (four uses of `env.user.company_id`); no reproduction in a database.
- **Impact:** The proposed price and the `list_price` written back on the product are converted with the wrong currency/rates when the companies differ, so the product sale price can be changed by the exchange-rate factor.
- **Suggested fix:** Use the consumption company (or the product company, falling back to `env.company`) for the default currency and as the conversion company/target currency, consistent with the AGREEMENT-001 fix.
- **Validation needed:** Two companies with different currencies, user default company different from the active one; check the proposed price and the resulting product `list_price`.

## AGREEMENT-011 — P3: Billing preparation default falls back to the user default company

- **Status:** Open. Found on 2026-10-03 while fixing AGREEMENT-001.
- **Location:** `wizard/service_billing_preparation.py`, `ServiceBillingPreparation.default_get()` (the `deltatech_service_equipment` extension of the same wizard does not use the company).
- **Trigger:** `default_get()` called without `company_id` in the requested fields (e.g. programmatic creation of the wizard), for a user whose default company differs from the active one.
- **Actual behavior:** The fallback sets `company_id` from `env.user.company_id` instead of `env.company`, and the prefilled agreements are searched with that company, while the field default itself uses `env.company`. Same class of error as AGREEMENT-001.
- **Evidence:** source inspection of `deltatech_service_agreement/wizard/service_billing_preparation.py` and `deltatech_service_equipment/wizard/service_billing_preparation.py`; no reproduction in a database.
- **Impact:** Limited: the form requests `company_id`, so the field default (`env.company`) normally applies; only callers that omit the field get agreements of the user default company.
- **Suggested fix:** Use `self.env.company` in the fallback (or rely on the field default).
- **Validation needed:** Call `default_get()` without `company_id` with an active company different from the user default company and check the company and the prefilled agreements.

## Additional review — 2026-10-03

AGREEMENT-008 and AGREEMENT-009 were checked against local Odoo 19 source using isolated executions of actual AST-extracted code with synthetic objects. These checks confirm the method behavior, not database-backed invoice creation, concurrency or account.move validation. No fixes were applied. Existing report content and other local changes were preserved.
