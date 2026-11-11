Servicing equipment at customer sites needs a register of what is installed where and how much it is used. This module keeps that register.

- **Equipment records**: Each equipment has a status and a stock serial number, with a *Tracking* button to its stock moves.
- **Functional locations**: Choosing a location on an equipment fills in the customer, contact and responsible user.
- **Meters and readings**: Collector meters total several counters. Readings keep the previous value and the difference, updated when a reading is edited.
- **Estimated values**: *Compute Estimated* fits a trend line to the readings not marked *Estimated* and forecasts today's value.
- **Type templates**: Choosing an equipment type copies its parts, checks and measurements into empty lists; *Load Operations from Template* replaces them.

It depends on *Services Base* (`deltatech_service_base`) and Inventory; *Services Equipment* and *Services Maintenance* build on it. Service *Users* edit equipment and readings; *Managers* configure types. An equipment cannot have two meters with the same unit of measure.
