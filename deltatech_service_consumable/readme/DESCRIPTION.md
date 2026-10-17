Track the consumables of the equipment under a service agreement: what was delivered,
how much is left and what the deliveries cost.

**Consumables per equipment**

- Define the consumables of each equipment type (storable products), with the maximum
  quantity allowed.
- The equipment form shows its consumables as gauges: the quantity left is the delivered
  quantity multiplied by the product shelf life (for example the pages of a toner),
  minus the usage read from the equipment meter in the same unit.
- Deliveries for service are prepared from the equipment, with its consumables, address
  and agreement; the delivered products are listed on the equipment.
- A check reports the consumables whose quantity would exceed the allowed maximum.

**Total cost**

- Each validated delivery for service adds its stock value to the cost of the agreement
  (returns reduce it) and refreshes the totals of the equipment.
- The agreement shows the total cost and the cost as a percentage of the invoiced amount,
  recomputed when an invoice is posted; "Recompute costs" rebuilds the total from the
  deliveries.

**Service efficiency report**

- `service.efficiency.report` puts the consumables delivered per equipment and agreement
  next to the usage read from the equipment meters, for a period; it is limited to the
  user's active companies.

The delivery operation type for service is set in the stock settings.
