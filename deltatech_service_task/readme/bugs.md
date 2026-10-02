# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## TASK-001 — P1: Task operation lines bypass the parent task's access restrictions

- **Status:** Open.
- **Location:** `security/ir.model.access.csv`; `models/project_task.py`.
- **Trigger:** A project user directly searches, reads, writes or deletes `project.task.part`, `project.task.check` or `project.task.measurement` rows for a task outside their authorized companies or private projects.
- **Actual behavior:** The three independent models grant project users full CRUD access, with no record rules and no enforcement of parent task access. A Many2one to a restricted task does not transfer its record rules to these models.
- **Impact:** Users can disclose maintenance notes and measurements, change conformity results, or remove intervention evidence even when the parent task is inaccessible.
- **Evidence:** Full module source and security CSV inspection; compared with Odoo 19 project's company and task visibility rules, which apply to `project.task` only. No rule for these three line models was found in the service suite.
- **Suggested fix:** Enforce the parent task's read and modification permissions on all line operations, including record creation and reassignment.
- **Validation needed:** Database tests for direct RPC operations against another company's task and a restricted private project's task. No database-backed access tests were executed in this pass.
