Equipment billed by use, such as printers charged per page, is invoiced on meter reading differences. This module links machines, meters and contracts and bases billing on the readings.

- **Installation and removal**: The *Install*, *Add to Agreement* and *Remove from Agreement* buttons open wizards that record readings, set the *Status* and log it in *History Equipment/Agreement*. Adding creates contract lines from meter templates; removal prepares the chosen *Period*'s consumption and deactivates the equipment's lines.
- **Billing from readings**: The *Billing Preparation* wizard sets each metered line's consumption quantity to the summed differences of readings not yet in a consumption, from the later of the agreement and installation dates to the period end. A reading in a consumption cannot be deleted.
- **Readings control**: For agreement types with *Requires readings for billing*, billing preparation refuses contracts without *Readings done*, unless the user is in *Can bill without meter readings*; scheduled billing skips them, and billing clears the tick.
- **Invoice annex**: The *Export meters XLS* button on a customer invoice downloads the billed meters with equipment, serial, previous and read values.
- **Equipment from serials**: A new serial number of a product whose category has *Equipment type required* creates the equipment.

It builds on *Services Agreement* and *Services Equipment Base*. Service managers run the operations; service users enter readings.
