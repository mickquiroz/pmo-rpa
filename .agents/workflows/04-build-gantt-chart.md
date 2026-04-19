---
description: Integrate Frappe Gantt to visualize project phases and update Phase schema to support start/end dates.
---

1. **Update Database Schema for Gantt Support**
   - Modify `./scripts/init_db.py`:
     - In `DDL_PHASES`, add `start_date` (TEXT) and `estimated_end_date` (TEXT).
     - Update the `SEED_PHASES_TEMPLATE` to include dummy dates for the seed project phases.
   - Run the script to recreate the database (Note: this drops current data, which is fine for local MVP).

2. **Update Pydantic Models**
   - Modify `./api/main.py`:
     - Update `PhaseResponse` to include `start_date: str` and `estimated_end_date: str`.

3. **Frontend: Include Gantt Library**
   - Modify `./frontend/index.html`:
     - Add Frappe Gantt CSS (via CDN) in `<head>`.
     - Add Frappe Gantt JS (via CDN) before the `app.js` script tag.
     - Add a Bootstrap Modal structure at the bottom of the body. Inside the modal body, place `<div id="gantt-target"></div>`.

4. **Frontend: JavaScript Logic**
   - Modify `./frontend/app.js`:
     - Make project rows clickable in `renderProjects`. When clicked, trigger a new function `showProjectGantt(projectId, projectName)`.
     - In `showProjectGantt`:
       1. Fetch phases from `/api/v1/projects/${projectId}/phases`.
       2. Map the phases data into the array format required by Frappe Gantt: `{ id, name, start, end, progress, dependencies }`. 
          - *Progress*: 100 if Completed, 50 if In Progress, 0 if Pending.
       3. Initialize `new Gantt('#gantt-target', tasks, { ...options })`.
       4. Show the Bootstrap Modal.

5. **Verify Feature**
   - Ensure clicking a project row opens the modal with a rendering Gantt chart for its phases.

6. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(gantt): update phase schema and integrate frappe-gantt visualization"`