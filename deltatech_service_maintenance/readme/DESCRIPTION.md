Corrective and preventive service for the equipment and locations of your customers,
from the first request to the handover report.

**Notifications** (`service.notification`)

- Register a service request for an equipment or a service location, with customer,
  contact, address, responsible, work center, priority, subject and notes.
- Category of the request: defect finding, delivery, transfer or sale; external or
  internal type.
- Flow: New, Assigned, In Progress, Done, with the assignment, start and completion dates
  recorded automatically.
- Lines with the requested products and the planned operations; the stock availability
  of each product is shown on the line.
- From a notification: create the service order, a delivery, an internal transfer or a
  sale order, all linked back to the notification.

**Service orders** (`service.order`)

- Order type with its category, **Corrective** or **Preventive**, and the options for
  travel, delivery and sale.
- Flow: Draft, Acknowledge, On the way, In Progress, Work Done, Completed, with Rejected
  and Cancel; travel, start and completion dates.
- Operations (with duration and the linked service product), components (the parts used,
  with stock availability), reason, operating parameters of the equipment after the
  intervention and the customer signature.
- Deliveries and sale orders created from the order and linked to it.

**Warranties and reconditioning** (`service.warranty`)

- Warranty or recondition files for an equipment, with the customer, the products used
  and the total amount.
- Flow: New, Assigned, In Progress, Approval requested, Approved, Done; the approval and
  the validation of the warranty deliveries are reserved to the warranty approval group.
- The delivered products update the warranty lines with their actual cost.
- Clarifications status and links to the delivery, the sale order and the invoice.

**Reports**

- Service Order, Handover report and Minutes of receipt, printed from the service order.
- Notification, printed from the notification.

**Configuration**

- Work centers with stock location, operation type, sale and transfer routes and cost
  per hour; the stock location can also be set on the service location.
- Notification types, order types, order reasons, operations and operating parameters.
