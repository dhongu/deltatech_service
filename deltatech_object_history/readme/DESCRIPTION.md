Chatter messages mix with automatic notifications and are sometimes cleaned up. This module keeps a separate history of internal notes (`object.history`) attached to Odoo documents.

- **History button**: Partners, invoices / journal entries and stock transfers get a *History* button with the number of rows, for users of the *Object history admin* group. It opens the rows of that document.
- **History rows**: Each row has a title, a formatted description, a *Related partner*, the linked document and its name, the author and the date, plus its own chatter. *Open Document* goes back to the original record.
- **Add from Action**: On a partner form, *Actions → Add history* adds a row for that partner.
- **History list**: *Contacts → History → History lines* lists all rows, with the filters *Partners*, *Moves* and *Transfers* and grouping by partner or by document type.
- **Kept rows**: No user can delete history rows; *Object history admin* can only archive them.

Rows are visible only to users who can read their document; rows of deleted documents stay visible to *Object history admin*. A row takes the company of its document; for a document shared between companies (e.g. a partner without a company) it takes the user's current company. Rows added with *Add history* do not fill *Related partner* and *Parent name*. *Deltatech Object History for Service* (`deltatech_object_history_service`) adds the same history to service agreements and equipment.
