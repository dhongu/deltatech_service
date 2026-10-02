# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## HISTORY-001 — P1: Document history is readable across unauthorized companies and parent documents

- **Status:** Open.
- **Location:** `security/ir.model.access.csv`; `models/object_history.py`; manifest security data.
- **Trigger:** An ordinary internal user searches or reads `object.history` records belonging to another company or a document that the user cannot read.
- **Actual behavior:** `base.group_user` has read access to every history row. No record rule restricts `company_id`, and the model does not check read access to the referenced `res_model` / `res_id`.
- **Impact:** History descriptions and parent names can disclose accounting, stock or service information outside the user's authorized scope. Restricting the parent document does not restrict this separate model.
- **Evidence:** Read the complete module source and security CSV. The manifest loads group definitions and access rights, but no history record rules; the history model has no parent-access enforcement.
- **Suggested fix:** Apply company isolation and enforce the parent document's access rules when exposing its history; handle missing or deleted parents explicitly.
- **Validation needed:** Database tests with two companies and a user denied access to a parent document, including direct RPC searches and reads.

## Review limitations

Source inspection only. No database-backed access tests were executed in this pass.
