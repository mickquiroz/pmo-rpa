---
description: Build the Phase Management modal to allow Developers to update phase statuses and PMOs to update phase dates.
---

1. **Frontend: Update Projects Table**
   - Modify `./frontend/index.html`:
     - Add a new column header `<th>Acciones</th>` to the projects table.
     - Add a new Modal with ID `managePhasesModal`. Inside, include a table to list phases (Columns: Fase, Fecha Inicio, Fecha Fin, Estado, Acciones).

2. **Frontend: Add Action Buttons**
   - Modify `./frontend/app.js` in `renderProjects()`:
     - Remove the `onclick` event from the `<tr>` that opens the Gantt.
     - Add a new `<td>` containing two buttons: 
       1. "Ver Gantt" (triggers `showProjectGantt(id, name)`).
       2. "Editar Fases" (triggers `openManagePhases(id)`).

3. **Frontend: Manage Phases Logic**
   - Modify `./frontend/app.js`:
     - Create `async function openManagePhases(projectId)`.
     - Fetch the phases from `/api/v1/projects/${projectId}/phases`.
     - Render the phases inside the `managePhasesModal` table.
     - **Role Logic per Row**:
       - `start_date` and `estimated_end_date` should be `<input type="date">`. Disable them if `currentRole === 'Developer'`.
       - `status` should be a `<select>` (Pending, In Progress, Completed). Disable it if `currentRole === 'PMO'`.
       - Add a "Guardar" button per row that triggers `updatePhase(phaseId)`.

4. **Frontend: Update Phase Function**
   - Modify `./frontend/app.js`:
     - Create `async function updatePhase(phaseId)`.
     - Depending on the role, gather the data:
       - If Developer: send `PATCH /api/v1/phases/{phaseId}` with the new `status`.
       - If PMO: send `PUT /api/v1/phases/{phaseId}/dates` with the new dates.
       - If Admin: allow both operations sequentially.
     - On success, alert the user, refresh the phases in the modal, and call `fetchProjects()` to update the background table progress.

5. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(ui): add phase management modal with role-based editing capabilities"`