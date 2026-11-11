Deltatech Category Group tags product categories with a type and a class. This module carries the same two groupings over to service equipment, so each equipment shows the type and class of its product's category.

- **Category type**: Each equipment gets a read-only *Category type*, stored on the equipment and taken from the category of its *Product*.
- **Category class**: Each equipment also gets a read-only *Category class*, taken from the same product category.
- **List columns**: The equipment list offers both fields as optional columns, hidden by default.

The module depends on *Services Equipment* (`deltatech_service_equipment`) and *Deltatech Category Group* (`deltatech_category_group`), which defines the types and classes. It changes only the list view of equipment, adds no menus or security rules, and no other module depends on it.
