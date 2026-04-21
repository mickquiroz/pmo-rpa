---
description: Build the Frontend UI for dynamic phase management (Create, Edit Details, Delete) inside the Manage Phases modal.
---

1. **Frontend UI: Add Phase Creation Form**
   - Modify `./frontend/index.html`:
     - Inside the `#managePhasesModal` body, just above the table, add a new section: `<div id="create-phase-container" class="card p-3 mb-3 bg-light">...</div>`.
     - Inside it, create a small inline form (or grid) to add a new phase: `phase_name`, `weight_percentage` (number), `start_date` (date), `estimated_end_date` (date), and a "Añadir Fase" button.
     - Add a `<th>Peso (%)</th>` to the phases table header.

2. **Frontend Logic: Phase Rendering & Editing**
   - Modify `./frontend/app.js` -> `openManagePhases(projectId)`:
     - Store the current `projectId` in a global variable (e.g., `currentManageProjectId`) so the new form knows where to add the phase.
     - Hide the `#create-phase-container` if `currentUserRole === 'Developer'`.
     - When rendering the rows (`phases.forEach`):
       - Make `phase_name` an `<input type="text">` (disabled for Developer).
       - Add a column for `weight_percentage` as an `<input type="number" min="0" max="100">` (disabled for Developer).
       - Add a "Eliminar" button in the Actions column (hidden for Developer).

3. **Frontend Logic: API Integration**
   - Modify `./frontend/app.js`:
     - **Delete Phase:** Create `async function deletePhase(phaseId)`. Call `DELETE /api/v1/phases/{phaseId}`. On success, call `openManagePhases(currentManageProjectId)` to refresh the modal table, and `fetchProjects()` to update the main progress bar.
     - **Create Phase:** Create an event listener for the new phase form. Call `POST /api/v1/phases` with the payload `{ project_id, phase_name, weight_percentage, start_date, estimated_end_date }`. On success, refresh the modal and main table.
     - **Update Phase:** Update the existing `updatePhase(phaseId, btnElement)` function. If Admin/PMO, also read the new name and weight inputs, and call `PUT /api/v1/phases/{phaseId}/details`.

4. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(ui): add dynamic phase management interface (CRUD)"`