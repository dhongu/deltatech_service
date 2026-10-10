## 20.0.2.0.15 (2026-10-10)

- **Fixed** (AGREEMENT-005): the billing cron created the preparation wizard without the period it had
  found and then read a `consumption_ids` key that the preparation never returned, so automatic billing
  failed before any invoice. The cron now passes the period, company and agreements explicitly, collects
  the consumptions generated for all agreements (manual preparation also kept only the last agreement's
  consumptions in its result) and bills them per company and sale journal. Without exactly one service
  period for the current month the cron logs a warning and does nothing.
- **Fixed** (AGREEMENT-009): negative consumptions (corrections of a previous period) were capped at the
  positive quantity of the same product on the new invoice, so a lone correction became 0 while the
  consumption was still marked as billed, and the stored billed quantity differed from the invoice line.
  Corrections are now billed in full and the billed quantity is the same on the line and on the
  consumption. **Behavior change**: when the net value is negative a credit note is created instead of an
  invoice; a partial correction stays a negative line on the invoice.
  Each correction now references the invoice it corrects: the line label says "Correction of
  invoice <number> from <date>", the document reference lists the corrected invoices, and a credit note
  correcting a single invoice is linked to it. The correction line uses the taxes of the original invoice
  line (VAT rate of the original operation); if that line cannot be identified, a warning is posted in the
  document chatter. A correction without a posted original invoice is refused in manual billing and its
  agreement is skipped (with a log entry) by automatic billing.
- Port of 19.0.2.0.16 (dhongu/deltatech_service#126). Adapted for 20.0: the correction text is written
  in the invoice line `label` (on 20.0 `name` holds only the extra description).

## 20.0.2.0.14 (2026-10-09)

- Apps Store banner (banner.json).

## 20.0.2.0.13 (2026-10-04)

- Service billing converted consumption prices into the currency of the user's
  default company, even when the invoice was issued for another company. A EUR 100
  consumption of a EUR company, billed by a user whose default company uses RON,
  became a 500 line on the EUR invoice. Prices are now converted into the invoice
  currency (journal currency, otherwise the billing company currency) at the rates
  of the billing company. The invoice currency is set explicitly, and income account
  and taxes are taken for the billing company. Consumptions of another company are
  rejected. **Amounts change** for users whose default company differs from the
  billing company and for journals in a foreign currency (AGREEMENT-001).
- Stored consumption revenues are now in the currency of the consumption company,
  not in the currency of the default company of the user who triggered the
  computation. The upgrade recomputes the revenues of invoiced consumptions, so
  revenue figures change for multi-company / multi-currency databases (AGREEMENT-001).
- Agreement lines had no company restriction: any internal user could read, and any
  service user could modify, lines of agreements of other companies. Lines now follow
  the multi-company restriction of their agreement. Creating a line on an agreement, or
  moving a line to another agreement, requires write access on that agreement
  (AGREEMENT-006).
- Port of 19.0.2.0.13 (dhongu/deltatech_service#106). Adapted for 20.0: the
  multi-company record rule became a global row in `security/ir.access.csv` and the
  post-migration script runs from `migrations/20.0.2.0.13`.

## 20.0.2.0.12 (2026-09-30)

- Own module icon in the flat style of the other modules.

## 19.0.2.0.11 (2026-09-24)

- Posting, cancelling or deleting an invoice or a payment no longer fails with an
  access error on *Service consumption* for users who have accounting rights but
  no service rights. The linked consumptions and agreements are now updated with
  elevated rights, still limited to the moves being processed. This also fixes the
  register-payment wizard, which deletes the draft payment move.

## 19.0.2.0.10 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
