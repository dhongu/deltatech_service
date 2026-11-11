Technicians who service customer equipment need a checklist per visit and a record of the result. This module ties tasks to equipment, loads its operations as a checklist, and prints a service report.

- **Location and equipment**: Tasks get *Functional Location* and *Service Equipment* fields. The equipment list follows the location, and the customer is filled in from either.
- **Checklist from equipment**: Choosing the equipment copies its parts, checks and measurements into the task as lines. Technicians tick *Is OK* and enter values and notes; the lists do not allow adding rows.
- **Service report**: A PDF printed from a task shows each line's status (*OK* or *Not OK*) or value. Each sub-task with an equipment follows on its own page.
- **Equipment history**: The *Tasks*, *Checks* and *Measurements* buttons on the equipment form show counts and open the related records.
- **Team follows assignees**: The *Team* field lists the employees of the assigned users and updates with them; employees without a user are kept.

The module depends on *Services Equipment Base* (`deltatech_service_equipment_base`), Project and Employees. Project users and managers can read and change the lines. The checklist loads only when the equipment is chosen in the form, not on import.
