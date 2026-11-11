Technicians who service customer equipment need a checklist per visit and a record of the result. This module ties tasks to equipment, loads its operations as a checklist, and prints a service report.

- **Location and equipment**: Tasks get *Functional Location* and *Service Equipment* fields. The equipment list follows the location, and the customer is filled in from either.
- **Checklist from equipment**: Choosing the equipment copies its parts, checks and measurements into the task, replacing existing lines. Technicians tick *Is OK* or *Not Applicable* and enter values and notes; the lists do not allow adding rows.
- **Maintenance types**: Equipment lines and equipment-type templates can be tagged with *Maintenance Types*. A task with a type loads only matching and untagged lines, and new sub-tasks inherit it.
- **Service report**: A PDF printed from a task shows each line's status (*OK*, *Not OK*, *N/A*) or value. Each sub-task with an equipment follows on its own page.
- **Equipment history**: The *Tasks*, *Parts*, *Checks* and *Measurements* buttons on the equipment form show counts and open the related records.
- **Team follows assignees**: The *Team* field lists the employees of the assigned users and updates with them; employees without a user are kept.

The module depends on *Services Equipment Base* (`deltatech_service_equipment_base`), Project and Employees. Lines follow the access rights of their task. The checklist loads only when the equipment is chosen in the form, not on import.
