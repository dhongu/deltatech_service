## 18.0.2.0.10 (2026-09-24)

- Posting, cancelling or deleting an invoice or a payment no longer fails with an
  access error on *Service consumption* for users who have accounting rights but
  no service rights. The linked consumptions and agreements are now updated with
  elevated rights, still limited to the moves being processed. This also fixes the
  register-payment wizard, which deletes the draft payment move.
