---
description: Implement a UI role simulator to toggle between Admin, PMO, and Developer views, adjusting visible actions.
---

1. **Frontend: Role Simulator UI**
   - Modify `./frontend/index.html`:
     - In the Navbar, add a dropdown or select menu labeled "Ver como:" with options: "Admin", "PMO", "Developer".
     - Add a "Crear Proyecto" button (hidden by default) near the "Descargar Reporte" button.
     - Add a modal for "Crear Proyecto" with a simple form (process_name, assigned_developer_id, start_date, estimated_end_date).

2. **Frontend: Role Logic**
   - Modify `./frontend/app.js`:
     - Create a global variable `currentRole = 'PMO'`.
     - Add an event listener to the "Ver como:" dropdown to update `currentRole` and call a new function `applyRoleUI()`.
     - `applyRoleUI()` logic:
       - If `Admin` or `PMO`: Show "Crear Proyecto" button. Show "Descargar Reporte".
       - If `Developer`: Hide "Crear Proyecto". Hide "Descargar Reporte".
     - Call `applyRoleUI()` on initial load.

3. **Frontend: PMO Create Project Logic**
   - Modify `./frontend/app.js`:
     - Intercept the "Crear Proyecto" modal form submission.
     - Send a `POST` request to `/api/v1/projects`.
     - On success, close the modal, show an alert, and call `fetchProjects()` to refresh the table.

4. **Verify Feature**
   - Reload the UI. Toggle roles to verify buttons hide/show correctly. Test creating a project as PMO.

5. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(ui): add role simulator and create project modal for PMO"`