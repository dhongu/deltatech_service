Internal Category Groups tags product categories with a type and a class. This module carries the same two groupings over to service equipment, so equipment can be grouped the way its product is.

- **Type and class**: Each equipment gets a read-only *Category type* and *Category class*, taken from the category of its *Product*.
- **List columns**: The equipment list offers both fields as optional columns, hidden by default.
- **Search and grouping**: The equipment search accepts both fields and adds the group-by filters *Category Type* and *Category Class*.

The module depends on *Services Equipment* (`deltatech_service_equipment`) and *Internal Category Groups* (`deltatech_category_group`), which defines the types and classes. It changes only the list and search views of equipment, adds no menus or security rules, and no other module depends on it.
