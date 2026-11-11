Servicing equipment at customer sites needs a register of what is installed where and how much it is used. This module keeps that register.

- **Equipment records**: Each equipment has an automatic *Reference*, a type, model and manufacturer, and can link a product and a stock serial number.
- **Functional locations**: Choosing a location on an equipment fills in the customer, contact and responsible user.
- **Meters and readings**: A collector meter groups several counters. Readings keep the previous value and the difference, updated when readings are edited.
- **Estimated values**: *Compute Estimated* fits a trend line to the readings not marked *Estimated* and forecasts today's value.
- **Type templates**: Choosing an equipment type copies the parts, checks and measurements of its templates.

It depends on *Services Base* (`deltatech_service_base`) and Inventory; *Services Equipment* and *Deltatech Services Maintenance* build on it. Service users edit equipment and readings; service managers configure types. An equipment cannot have two meters with the same unit of measure.
