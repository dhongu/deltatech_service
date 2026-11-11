This base module gives the service modules a common menu, access groups, cycles and date ranges. It has no business function on its own.

- **Cycles**: A *Cycle* has a name, a value and a unit (*Day*, *Week*, *Month* or *Year*). The `get_cycle()` method returns its time interval.
- **Date ranges**: A *Date Range* has a name, a start date and an end date. The *Generate Date Range* action creates the monthly ranges of the current year, named like `2026/01`, skipping names that exist.
- **Menu and groups**: The module creates the *Service* menu, with *Cycle* and *Date Ranges* under *Configuration*, and the groups *Client*, *User* and *Manager* plus three *Warranty* groups.

Services Base depends on `product` and `account`. `deltatech_service_agreement` and `deltatech_service_equipment_base` depend on it. Only service managers edit cycles and date ranges.
