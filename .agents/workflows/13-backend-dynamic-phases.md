---
description: Build CRUD endpoints for project phases to support dynamic project types (Web, AI, custom RPA).
---

1. **Backend: Add Phase Deletion (DELETE)**
   - Modify `./api/main.py`:
     - Create endpoint `DELETE /api/v1/phases/{phase_id}`.
     - Protect with `Depends(get_current_user)`.
     - Logic: Only allow if `current_user["role"]` is 'Admin' or 'PMO'. If 'Developer', raise 403.
     - Delete the phase from SQLite.
     - Return a success message.

2. **Backend: Add Phase Creation (POST)**
   - Modify `./api/main.py`:
     - Create schema `PhaseCreate`: `project_id` (int), `phase_name` (str), `weight_percentage` (int), `start_date` (str), `estimated_end_date` (str).
     - Create endpoint `POST /api/v1/phases`.
     - Protect with `Depends(get_current_user)` (Admin/PMO only).
     - Validate that the new `weight_percentage` plus the sum of existing weights for that project does not exceed 100%. (Optional but good practice, or just let the PMO manage it).
     - Insert into `Phases` with `status = 'Pending'`.
     - Return the created phase.

3. **Backend: Add Phase Details Update (PUT)**
   - Modify `./api/main.py`:
     - Create schema `PhaseDetailsUpdate`: `phase_name` (str), `weight_percentage` (int).
     - Create endpoint `PUT /api/v1/phases/{phase_id}/details`.
     - Protect with `Depends(get_current_user)` (Admin/PMO only).
     - Update name and weight in SQLite.

4. **Backend: Update Project Creation Logic**
   - Modify `POST /api/v1/projects` in `./api/main.py`:
     - Instead of hardcoding the 4 RPA phases, just create the project and return it with 0 phases (0% progress). The PMO will add custom phases from the UI later. 
     - *Alternative for MVP*: Keep the 4 default phases as a "template", but now that we have the DELETE endpoint, the PMO can just delete them and add their own. Let's keep the template insertion so we don't break existing tests, but now they are editable.

5. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(api): add CRUD endpoints for dynamic project phases"`