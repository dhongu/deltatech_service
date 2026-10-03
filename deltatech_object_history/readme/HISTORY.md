## 19.0.0.0.4 (2026-10-03)

- Every internal user could search and read all history rows, including those of
  other companies and of documents they are not allowed to see. History rows now
  follow a multi-company record rule, and a row attached to a document is visible
  only to users who can read that document (search, count and direct reads alike).
  History of a deleted document, or of a model that is no longer installed, is
  visible only to *Object history admin* users.
- A new history row takes the company of its document when the document has one,
  instead of the active company.

## 19.0.0.0.3 (2026-09-30)

- Own module icon in the flat style of the other modules.

## 19.0.0.0.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
