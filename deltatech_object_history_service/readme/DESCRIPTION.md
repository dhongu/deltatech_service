Notes on service agreements and equipment often need to stay apart from the chatter. This bridge module lets *Object History* notes be kept on both.

- **History button**: A *History* button with a count appears on the agreement and equipment forms, for users of the *Object history admin* group. It opens the history rows of that record.
- **Prefilled rows**: A new row opened from the button is attached to the record, and its *Parent name* takes the record's name.
- **New filters**: The history search gets *Agreements* and *Equipments* filters.

The module depends on *Object History* (`deltatech_object_history`), *Services Agreement* (`deltatech_service_agreement`) and *Services Equipment* (`deltatech_service_equipment`). Rows are visible only to users who can read their agreement or equipment. The form requires a *Related partner*, which is not prefilled.
