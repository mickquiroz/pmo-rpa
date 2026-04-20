---
description: Integrate JWT authentication into the frontend, replace the role simulator with a real login, and build the Admin IAM dashboard.
---

1. **Frontend: Build Login UI**
   - Modify `./frontend/index.html`:
     - Remove the "Ver como:" dropdown (the role simulator).
     - Add a "Cerrar Sesión" button in the Navbar (hidden by default).
     - Add a full-screen Bootstrap Modal for "Login" (`#loginModal`). Make it un-closable (backdrop='static', keyboard=false). Inside, add fields for `email` and `password`.
     - Add an "Administrar Usuarios" button (hidden by default) next to the "Descargar Reporte" button.
     - Add an "Admin Users Modal" (`#adminUsersModal`) containing a table to list users and a form to create a new user (Name, Email, Password, Role).

2. **Frontend: Auth Logic**
   - Modify `./frontend/app.js`:
     - Create variables `let authToken = localStorage.getItem('token');` and `let currentUserRole = localStorage.getItem('role');`.
     - Create a `checkAuth()` function running on load. If no `authToken`, show `#loginModal`.
     - Implement `handleLogin(e)`:
       - Use `URLSearchParams` to send `username` (email) and `password` to `POST /api/v1/auth/token`.
       - On success, save `access_token` to `localStorage`.
       - Decode the JWT payload (using `atob(token.split('.')[1])`) to extract the `role` and save it to `localStorage`.
       - Hide the login modal and call `applyRoleUI()` and `fetchProjects()`.
     - Implement `handleLogout()`: clear `localStorage` and reload the page.

3. **Frontend: Secure API Calls**
   - Modify `./frontend/app.js`:
     - Update all existing `fetch()` calls (fetchProjects, updatePhase, showProjectGantt, handleCreateProject) to include the header: `'Authorization': 'Bearer ' + authToken`.
     - If any fetch returns `401 Unauthorized`, trigger `handleLogout()`.

4. **Frontend: Admin IAM Logic**
   - Modify `./frontend/app.js`:
     - Update `applyRoleUI()`: Show "Administrar Usuarios" only if `currentUserRole === 'Admin'`.
     - Implement `fetchUsers()`: Calls `GET /api/v1/users` and renders them in the Admin Modal table. Add a "Dar de baja" button per row.
     - Implement `createUser(e)`: Sends data to `POST /api/v1/users`.
     - Implement `deleteUser(id)`: Sends `DELETE /api/v1/users/{id}`.

5. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(ui): integrate real JWT login and Admin IAM dashboard"`